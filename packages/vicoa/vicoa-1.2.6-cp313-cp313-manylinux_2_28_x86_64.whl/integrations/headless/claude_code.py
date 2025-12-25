#!/usr/bin/env python3
"""
Headless Claude Code Integration for Vicoa

This module provides a headless version of Claude Code that integrates with the Vicoa SDK,
allowing human users to interact with Claude through the web dashboard while Claude runs
autonomously using the Claude Agent SDK.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Union, cast, Any

from vicoa.sdk.async_client import AsyncVicoaClient
from integrations.utils import GitDiffTracker
from integrations.headless.format_tools import format_tool_use
from vicoa.utils import get_project_path

try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        AssistantMessage,
        UserMessage,
        SystemMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
        CLINotFoundError,
        ProcessError,
        PermissionMode,
        McpServerConfig,
    )
except ImportError as e:
    print(
        "Error: Claude Agent SDK not found. Please install it with: pip install claude-agent-sdk"
    )
    print(f"Import error: {e}")
    sys.exit(1)


# Control command pattern (JSON format)
CONTROL_JSON_PATTERN = re.compile(r'\{[^}]*"type"\s*:\s*"control"[^}]*\}')


def setup_logging(session_id: str, console_output: bool = True):
    """Setup logging with session-specific log file.

    Args:
        session_id: Session ID for the log file name
        console_output: Whether to also log to console (default True for standalone, False for webhook)
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create .vicoa/claude_headless directory and log file with session UUID
    vicoa_dir = Path.home() / ".vicoa"
    claude_headless_dir = vicoa_dir / "claude_headless"
    claude_headless_dir.mkdir(exist_ok=True, parents=True)

    log_file = claude_headless_dir / f"{session_id}.log"

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler (always add)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (only if requested)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.info(f"Logging to: {log_file}")

    return logger


class HeadlessClaudeRunner:
    """Headless Claude Code runner that integrates with Vicoa SDK."""

    def __init__(
        self,
        vicoa_api_key: str,
        session_id: str,
        vicoa_base_url: str = "https://api.vibecodeanywhere.com:8443",
        initial_prompt: Optional[str] = None,
        extra_args: Optional[Dict[str, Optional[str]]] = None,
        permission_mode: Optional[PermissionMode] = None,
        allowed_tools: Optional[List[str]] = None,
        disallowed_tools: Optional[List[str]] = None,
        cwd: Optional[Union[str, Path]] = None,
        console_output: bool = True,
        agent_name: str = "Claude Code",
        enable_thinking: bool = False,
    ):
        self.vicoa_api_key = vicoa_api_key
        self.vicoa_base_url = vicoa_base_url
        self.initial_prompt = initial_prompt
        self.session_id = session_id
        self.last_message_id: Optional[str] = None
        self.cwd = str(cwd) if cwd else os.getcwd()  # Store cwd before using it
        self.agent_name = agent_name  # Store the agent name/type
        self.project_path = get_project_path(self.cwd)

        # Store configuration for dynamic reconnection
        self.enable_thinking = enable_thinking
        self.permission_mode = permission_mode
        self.allowed_tools = allowed_tools
        self.disallowed_tools = disallowed_tools
        self.extra_args = extra_args

        # Setup logging for this session
        setup_logging(session_id, console_output=console_output)
        self.logger = logging.getLogger(__name__)

        # Build initial Claude options
        self.claude_options = self._build_claude_options()

        # Vicoa client and Claude client
        self.vicoa_client: Optional[AsyncVicoaClient] = None
        self.claude_client: Optional[ClaudeSDKClient] = None
        self.running = True
        self.conversation_started = False
        self.interrupt_requested = False

        # Initialize git diff tracker with our logger and working directory
        self.git_tracker = GitDiffTracker(
            enabled=True, logger=self.logger, cwd=str(self.cwd) if self.cwd else None
        )
        self.previous_git_diff = None  # Track previous diff to avoid duplicates

    def _build_claude_options(self) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions with current configuration.

        This method can be called to rebuild options when settings change.
        """
        # Create default Vicoa MCP server config
        vicoa_mcp_server = {
            "command": "vicoa",
            "args": [
                "mcp",
                "--api-key",
                self.vicoa_api_key,
                "--permission-tool",
                "--disable-tools",
                "--agent-instance-id",
                self.session_id,
            ],
        }

        # Always include default Vicoa MCP server
        default_mcp_servers = cast(
            Dict[str, McpServerConfig], {"vicoa": vicoa_mcp_server}
        )

        # Prepare environment variables for Claude Code
        claude_env: Dict[str, str] = {}
        if self.enable_thinking:
            claude_env["MAX_THINKING_TOKENS"] = "1024"
            self.logger.info(
                "Building options with thinking enabled (MAX_THINKING_TOKENS=1024)"
            )
        else:
            self.logger.info("Building options with thinking disabled")

        # Claude Agent SDK options - build kwargs conditionally
        claude_options_kwargs: Dict[str, Any] = {
            "mcp_servers": default_mcp_servers,
            "permission_mode": self.permission_mode,
            "allowed_tools": (self.allowed_tools or []) + ["mcp__vicoa__approve"],
            "permission_prompt_tool_name": "mcp__vicoa__approve",
            "disallowed_tools": self.disallowed_tools or [],
            "cwd": self.cwd,
            "extra_args": self.extra_args or {},
            # Restore Claude Code defaults (required in v0.1.0+)
            "system_prompt": {"type": "preset", "preset": "claude_code"},
            "setting_sources": ["user", "project", "local"],
        }

        # Only add env if we have environment variables
        if claude_env:
            claude_options_kwargs["env"] = claude_env

        return ClaudeAgentOptions(**claude_options_kwargs)

    async def _reconnect_claude_client(self) -> bool:
        """Disconnect and reconnect Claude client with updated options.

        Returns:
            True if reconnection successful, False otherwise
        """
        try:
            self.logger.info("Reconnecting Claude client with updated settings...")

            # Disconnect existing client if connected
            if self.claude_client:
                self.logger.info("Disconnecting existing Claude client...")
                try:
                    # Properly exit the async context manager
                    await self.claude_client.__aexit__(None, None, None)
                    self.claude_client = None
                except Exception as e:
                    self.logger.warning(f"Error during disconnect: {e}")

            # Rebuild options with current configuration
            self.claude_options = self._build_claude_options()

            # Create new client
            self.logger.info("Creating new Claude client...")
            self.claude_client = ClaudeSDKClient(options=self.claude_options)

            # Connect the new client (start the async context manager)
            self.logger.info("Connecting new Claude client...")
            await self.claude_client.__aenter__()

            self.logger.info("✅ Claude client reconnected successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to reconnect Claude client: {e}")
            return False

    async def initialize(self):
        """Initialize the Vicoa and Claude clients and create initial session."""
        self.logger.info("Initializing Vicoa client...")

        self.vicoa_client = AsyncVicoaClient(
            api_key=self.vicoa_api_key, base_url=self.vicoa_base_url
        )

        # Ensure the agent instance is registered with project metadata for the dashboard.
        try:
            registration = await self.vicoa_client.register_agent_instance(
                agent_type=self.agent_name,
                agent_instance_id=self.session_id,
                project=self.project_path,
                home_dir=str(Path.home()),
            )
            updated_session_id = registration.agent_instance_id
            if updated_session_id and updated_session_id != self.session_id:
                self.logger.info(
                    f"Session ID updated from {self.session_id} to {updated_session_id}"
                )
                self.session_id = updated_session_id
                # Rebuild Claude options with the updated session ID to ensure consistency
                self.claude_options = self._build_claude_options()
                self.logger.info(
                    "Rebuilt Claude options with updated session ID for MCP server"
                )
        except Exception as exc:  # pragma: no cover - defensive logging only
            self.logger.warning(
                "Failed to register agent instance for session %s: %s",
                self.session_id,
                exc,
            )

        # Initialize persistent Claude client
        self.logger.info("Initializing Claude Agent SDK client...")
        self.claude_client = ClaudeSDKClient(options=self.claude_options)
        await self.claude_client.__aenter__()  # Start the async context

        # Create initial session
        self.logger.info("Creating initial Vicoa session...")
        if not self.vicoa_client:
            raise RuntimeError("Vicoa client not initialized")

        # If we have an initial prompt, send it as a USER message to Vicoa
        if self.initial_prompt:
            self.logger.info("Sending initial prompt as user message to Vicoa")
            # Send agent ready message (not waiting for input since we have the prompt)
            await self.vicoa_client.send_message(
                content="Claude Code session started, waiting for your input...",
                agent_instance_id=self.session_id,
                agent_type=self.agent_name,
                requires_user_input=False,
            )

            # Send the prompt as a USER message so it shows in the dashboard
            await self.vicoa_client.send_user_message(
                agent_instance_id=self.session_id,
                content=self.initial_prompt,
            )
            # Return the prompt as the first user input
            return self.initial_prompt
        else:
            # No initial prompt, send agent message and wait for user input
            response = await self.vicoa_client.send_message(
                content="Claude Code session started, waiting for your input...",
                agent_instance_id=self.session_id,
                agent_type=self.agent_name,
                requires_user_input=True,  # Wait for user input
            )

            # Process any initial queued messages
            if response.queued_user_messages:
                # Filter out control commands from initial messages
                filtered_messages = await self._filter_control_commands(
                    response.queued_user_messages
                )
                if filtered_messages:
                    return filtered_messages[0]  # Return first non-control message
                # If all were control commands, return None to trigger wait in main loop
                self.logger.info(
                    "Initial messages were all control commands, will wait for actual input"
                )

        return None

    async def send_to_vicoa(
        self,
        content: str,
        requires_user_input: bool = False,
    ) -> Optional[str]:
        """Send a message to Vicoa and optionally wait for user response.

        Args:
            content: Message content to send
            requires_user_input: Whether to wait for user input
        """
        if not self.vicoa_client or not self.session_id:
            self.logger.error("Vicoa client not initialized")
            return None

        try:
            # Get git diff if requested, but only if it changed
            git_diff = None
            current_diff = self.git_tracker.get_diff()
            if current_diff != self.previous_git_diff:
                git_diff = current_diff
                self.previous_git_diff = current_diff
                self.logger.info(
                    f"Git diff changed, sending {len(git_diff) if git_diff else 0} chars"
                )
                if git_diff:
                    self.logger.debug(f"Git diff preview: {git_diff[:200]}...")
            else:
                self.logger.debug("Git diff unchanged, not sending")

            response = await self.vicoa_client.send_message(
                content=content,
                agent_type=self.agent_name,
                agent_instance_id=self.session_id,
                requires_user_input=requires_user_input,
                git_diff=git_diff,
                timeout_minutes=1440,  # 24 hours max wait
                poll_interval=3.0,
            )

            # Store message ID for potential user input requests
            if hasattr(response, "message_id"):
                self.last_message_id = response.message_id

            # If we asked for user input, return the first response as string
            if requires_user_input:
                if response.queued_user_messages:
                    # Filter out control commands
                    filtered_messages = await self._filter_control_commands(
                        response.queued_user_messages
                    )
                    if self.interrupt_requested and not filtered_messages:
                        self.logger.info(
                            "Interrupt command received while waiting for input"
                        )
                        return None
                    if filtered_messages:
                        # New user input should clear any previous interrupt flag
                        self.interrupt_requested = False
                        return filtered_messages[0]
                    # If all were control commands, return None to indicate no actual input
                    self.logger.info("All queued messages were control commands")
                else:
                    # No queued messages at all
                    self.logger.info("No queued messages received")
                return None

            if response.queued_user_messages:
                await self._process_control_messages(response.queued_user_messages)
                if self.interrupt_requested:
                    self.logger.info(
                        "Interrupt received from queued messages while sending update"
                    )
                    return None

            # For intermediate messages, return None (we stored the message_id above)
            return None

        except Exception as e:
            self.logger.error(f"Failed to send message to Vicoa: {e}")

        return None

    def format_message_content(self, message) -> str:
        """Format a Claude SDK message for display in Vicoa."""
        if isinstance(message, AssistantMessage):
            parts = []

            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    # Use the centralized tool formatting function
                    tool_name = block.name
                    tool_input = block.input if hasattr(block, "input") else {}
                    formatted = format_tool_use(tool_name, tool_input)
                    parts.append(formatted)

                elif isinstance(block, ToolResultBlock):
                    # Summarize tool results without overwhelming detail
                    if hasattr(block, "content") and block.content:
                        result_summary = str(block.content)[:200]
                        if len(str(block.content)) > 200:
                            result_summary += "..."
                        parts.append(f"   Result: {result_summary}")

            return "\n".join(parts) if parts else "Claude is thinking..."

        elif isinstance(message, UserMessage):
            # UserMessage should have content attribute
            content = getattr(message, "content", str(message))
            return f"User: {content}"
        elif isinstance(message, SystemMessage):
            # SystemMessage might not have content attribute, handle gracefully
            content = getattr(
                message, "content", getattr(message, "text", str(message))
            )
            return f"System: {content}"
        elif isinstance(message, ResultMessage):
            # ResultMessage also might not have content
            content = getattr(
                message,
                "content",
                getattr(message, "text", "Claude completed this task."),
            )
            return content if content != str(message) else "Claude completed this task."

        return str(message)

    def _parse_control_command(self, content: str) -> Optional[Dict[str, str]]:
        """Parse JSON control command from text.

        Expected format: {"type": "control", "setting": "permission_mode", "value": "plan"}
        Returns: {"setting": "permission_mode", "value": "plan"} or None
        """
        if not content:
            return None

        # Try to find JSON anywhere in the content
        match = CONTROL_JSON_PATTERN.search(content)
        if not match:
            return None

        # Extract the JSON string
        json_str = match.group(0)

        try:
            data = json.loads(json_str)

            # Validate structure
            if data.get("type") != "control":
                return None

            setting = data.get("setting")
            value = data.get("value")

            if setting == "interrupt":
                return {"setting": setting}

            if not setting or value is None:
                return None

            return {"setting": setting, "value": value}
        except json.JSONDecodeError:
            return None

    async def _handle_interrupt(self) -> None:
        """Handle interrupt command by stopping the current task."""

        if self.interrupt_requested:
            return

        self.interrupt_requested = True
        self.logger.info("Interrupt command received; stopping current task")

        if self.claude_client:
            try:
                await self.claude_client.interrupt()
                self.logger.info("Sent interrupt to Claude client")
            except Exception as exc:
                self.logger.error(f"Failed to interrupt Claude client: {exc}")

        await self._send_feedback_message(
            "Interrupted · What should Claude do instead?"
        )

    async def _send_feedback_message(self, content: str) -> None:
        """Send a feedback message to the web UI (non-blocking)."""
        try:
            if self.vicoa_client and self.session_id:
                await self.vicoa_client.send_message(
                    content=content,
                    agent_type=self.agent_name,
                    agent_instance_id=self.session_id,
                    requires_user_input=False,
                )
                self.logger.info(f"Sent feedback message: {content}")
        except Exception as e:
            self.logger.error(f"Failed to send feedback message: {e}")

    async def _handle_control_command(self, content: str) -> bool:
        """Handle control commands from web UI.

        Returns: True if this was a control command (even if failed), False otherwise
        """
        control = self._parse_control_command(content)
        if not control:
            return False

        setting = control["setting"]
        value = control.get("value")

        self.logger.info(
            f"Received control command: {setting}{'=' + str(value) if value is not None else ''}"
        )

        if setting == "permission_mode":
            valid_modes = ["default", "acceptEdits", "bypassPermissions", "plan"]
            if value not in valid_modes:
                await self._send_feedback_message(
                    f"Invalid permission mode '{value}'. Valid options: {', '.join(valid_modes)}"
                )
            else:
                # Use the SDK's set_permission_mode() API to change mode dynamically
                try:
                    if self.claude_client:
                        await self.claude_client.set_permission_mode(value)
                        await self._send_feedback_message(
                            f"Permission mode changed to {value}"
                        )
                        self.logger.info(
                            f"Successfully changed permission mode to: {value}"
                        )
                    else:
                        await self._send_feedback_message(
                            "Cannot change permission mode: Claude client not initialized"
                        )
                except Exception as e:
                    self.logger.error(f"Failed to change permission mode: {e}")
                    await self._send_feedback_message(
                        f"Failed to change permission mode: {str(e)}"
                    )

        elif setting == "thinking":
            # Thinking can be toggled by reconnecting the Claude client
            target_state = value == "on"

            if target_state == self.enable_thinking:
                # Already in the requested state
                state_name = "on" if target_state else "off"
                await self._send_feedback_message(f"Thinking is already {state_name}")
            else:
                # Need to change state - reconnect with new env
                self.logger.info(
                    f"Toggling thinking from {self.enable_thinking} to {target_state}"
                )

                # Update the state
                self.enable_thinking = target_state

                # Reconnect Claude client with updated environment
                success = await self._reconnect_claude_client()

                if success:
                    state_name = "on" if target_state else "off"
                    await self._send_feedback_message(f"Thinking turned {state_name}")
                    self.logger.info(f"Successfully toggled thinking to {state_name}")
                else:
                    # Rollback state on failure
                    self.enable_thinking = not target_state
                    await self._send_feedback_message(
                        "Failed to toggle thinking. Please try again or restart the session."
                    )
                    self.logger.error("Failed to toggle thinking, rolled back state")

        elif setting == "interrupt":
            await self._handle_interrupt()

        else:
            await self._send_feedback_message(f"Unknown setting '{setting}'")

        return True

    async def _process_control_messages(self, messages: List[str]) -> None:
        """Process control commands from queued messages without returning content."""

        for message in messages:
            await self._handle_control_command(message)

    async def _filter_control_commands(self, messages: List[str]) -> List[str]:
        """Filter out control commands from message list and handle them.

        Args:
            messages: List of message strings from web UI

        Returns:
            List of non-control messages to pass to Claude
        """
        filtered = []
        for msg in messages:
            if await self._handle_control_command(msg):
                # This was a control command, don't pass to Claude
                continue
            filtered.append(msg)
        return filtered

    async def run_conversation_turn(self, user_input: str) -> Optional[str]:
        """Run a single conversation turn with Claude and return next user input needed."""
        self.logger.info(
            f"Starting conversation turn with input: {user_input[:100]}..."
        )

        # Clear any previous interrupt when starting a new turn
        self.interrupt_requested = False

        if not self.claude_client:
            self.logger.error("Claude client not initialized")
            return None

        try:
            # Send the user input to the persistent Claude client
            if not self.conversation_started:
                # Just use the input directly - it already contains the full prompt
                await self.claude_client.query(user_input)
                self.conversation_started = True
            else:
                # For subsequent messages, just send the user input
                await self.claude_client.query(user_input)

            # Stream Claude's response - send everything immediately
            message_count = 0
            async for message in self.claude_client.receive_response():
                if self.interrupt_requested:
                    self.logger.info(
                        "Interrupt requested; stopping response stream immediately"
                    )
                    break

                message_count += 1
                self.logger.info(
                    f"Message #{message_count} - Type: {type(message).__name__}"
                )

                if isinstance(message, SystemMessage):
                    # Log system messages but don't send to Vicoa
                    if hasattr(message, "subtype") and message.subtype == "init":
                        self.logger.warning(
                            "Received init SystemMessage - context may have been reset"
                        )
                    self.logger.info(f"System message: {message}")
                    continue

                if isinstance(message, UserMessage):
                    # Log user messages but don't send to Vicoa (these are echoes of user input)
                    self.logger.debug(f"User message (not forwarding): {message}")
                    continue

                if isinstance(message, ResultMessage):
                    # Conversation turn is complete
                    self.logger.info("Conversation turn completed")
                    break

                # Format and send all other messages (mainly AssistantMessages) immediately
                formatted_content = self.format_message_content(message)
                if formatted_content:
                    await self.send_to_vicoa(
                        formatted_content,
                        requires_user_input=False,
                    )

                if self.interrupt_requested:
                    self.logger.info(
                        "Interrupt requested during response streaming; stopping turn"
                    )
                    break

            if self.interrupt_requested:
                self.logger.info(
                    "Skipping input request because current task was interrupted"
                )
                return None

            # After all messages are sent, request user input on the last message
            if self.last_message_id and self.vicoa_client:
                self.logger.info(
                    f"Requesting user input on last message {self.last_message_id}"
                )
                try:
                    user_responses = await self.vicoa_client.request_user_input(
                        message_id=self.last_message_id,
                        timeout_minutes=1440,
                        poll_interval=3.0,
                    )
                    if user_responses:
                        # Filter out control commands
                        filtered_responses = await self._filter_control_commands(
                            user_responses
                        )
                        if self.interrupt_requested:
                            self.logger.info(
                                "Interrupt handled while waiting for input; returning to idle"
                            )
                            return None
                        if filtered_responses:
                            return filtered_responses[0]
                        # If all messages were control commands, return None to wait for actual input
                        self.logger.info(
                            "All messages were control commands, no actual user input yet"
                        )
                        return None
                except Exception as e:
                    self.logger.error(f"Failed to request user input: {e}")

            # Fallback if no last_message_id or request failed
            next_user_input = await self.send_to_vicoa(
                "What would you like me to do next?",
                requires_user_input=True,
            )
            return next_user_input

        except CLINotFoundError:
            error_msg = "❌ Claude Code CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code"
            await self.send_to_vicoa(error_msg, requires_user_input=True)
            self.logger.error(error_msg)
            return None
        except ProcessError as e:
            error_msg = f"❌ Claude Code process error: {e}"
            await self.send_to_vicoa(error_msg, requires_user_input=True)
            self.logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"❌ Error during conversation turn: {e}"
            await self.send_to_vicoa(error_msg, requires_user_input=True)
            self.logger.error(error_msg)
            return None

        return None

    async def run(self):
        """Main run loop for the headless Claude runner."""
        try:
            # Initialize Vicoa connection
            initial_user_input = await self.initialize()

            if not initial_user_input:
                # Wait for first user input
                self.logger.info("Waiting for initial user input...")
                initial_user_input = await self.send_to_vicoa(
                    "Headless Claude is ready. What would you like me to help you with?",
                    requires_user_input=True,
                )

            if not initial_user_input:
                self.logger.error("Failed to get initial user input")
                return

            # Start with the user input
            current_input = initial_user_input

            # Main conversation loop
            while self.running:
                if not current_input:
                    # If we don't have input, wait for it
                    self.logger.debug("No current input, waiting for user message...")
                    current_input = await self.send_to_vicoa(
                        "Waiting for your input...",
                        requires_user_input=True,
                    )
                    if not current_input:
                        # Still no input after waiting, retry
                        await asyncio.sleep(1)
                        continue

                next_input = await self.run_conversation_turn(current_input)
                current_input = next_input  # Update for next iteration (can be None)

        except (KeyboardInterrupt, asyncio.CancelledError):
            self.logger.info("Received interrupt/cancel signal, shutting down...")
            self.running = False
        except Exception as e:
            self.logger.error(f"Fatal error in headless runner: {e}")
            if self.vicoa_client and self.session_id:
                await self.send_to_vicoa(
                    f"Headless Claude encountered a fatal error: {e}",
                    requires_user_input=False,
                )
        finally:
            # Clean up
            if self.claude_client:
                try:
                    await self.claude_client.__aexit__(None, None, None)
                    self.logger.info("Claude client closed")
                except Exception as e:
                    self.logger.error(f"Error closing Claude client: {e}")

            if self.vicoa_client and self.session_id:
                try:
                    await self.vicoa_client.end_session(self.session_id)
                    self.logger.info("Session ended successfully")
                except Exception as e:
                    self.logger.error(f"Error ending session: {e}")

            if self.vicoa_client:
                await self.vicoa_client.close()


def parse_list_argument(value: str) -> List[str]:
    """Parse a comma-separated list argument."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main():
    """Main entry point for headless Claude Code integration."""
    parser = argparse.ArgumentParser(
        description="Headless Claude Code integration with Vicoa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Vicoa configuration
    parser.add_argument(
        "--api-key",
        default=os.environ.get("VICOA_API_KEY"),
        help="Vicoa API key (defaults to VICOA_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.vibecodeanywhere.com:8443",
        help="Vicoa base URL",
    )

    # Claude Code configuration
    parser.add_argument(
        "--prompt",
        default="You are starting a coding session",
        help="Initial prompt to send to Claude",
    )
    parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "bypassPermissions", "default", "plan"],
        help="Permission mode for Claude Code",
    )
    parser.add_argument(
        "--allowed-tools",
        type=str,
        help="Comma-separated list of allowed tools (e.g., 'Read,Write,Bash')",
    )
    parser.add_argument(
        "--disallowed-tools", type=str, help="Comma-separated list of disallowed tools"
    )
    parser.add_argument(
        "--cwd",
        type=str,
        help="Working directory for Claude (defaults to current directory)",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=os.environ.get("VICOA_AGENT_INSTANCE_ID"),
        help="Custom session ID (defaults to VICOA_AGENT_INSTANCE_ID env var or random UUID)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=os.environ.get("VICOA_AGENT_TYPE", "Claude Code"),
        help="Name/type of the agent (defaults to VICOA_AGENT_TYPE env var or 'Claude Code')",
    )
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Enable thinking mode by setting MAX_THINKING_TOKENS=1024",
    )

    args, unknown_args = parser.parse_known_args()

    # Check if API key is provided (either via argument or environment variable)
    if not args.api_key:
        logger = logging.getLogger(__name__)
        logger.error(
            "Error: Vicoa API key is required. Provide via --api-key or set VICOA_API_KEY environment variable."
        )
        sys.exit(1)

    # Setup logging with session ID (default to random UUID if not provided)
    session_id = (
        args.session_id
        if hasattr(args, "session_id") and args.session_id
        else str(uuid.uuid4())
    )
    logger = setup_logging(session_id)

    # Parse list arguments
    allowed_tools = (
        parse_list_argument(args.allowed_tools) if args.allowed_tools else None
    )
    disallowed_tools = (
        parse_list_argument(args.disallowed_tools) if args.disallowed_tools else None
    )

    # Convert unknown arguments to extra_args dict for Claude Agent SDK
    extra_args: Dict[str, Optional[str]] = {}
    i = 0
    while i < len(unknown_args):
        arg = unknown_args[i]
        if arg.startswith("--"):
            key = arg[2:]  # Remove '--' prefix
            # Check if next argument is the value (doesn't start with '-')
            if i + 1 < len(unknown_args) and not unknown_args[i + 1].startswith("-"):
                extra_args[key] = unknown_args[i + 1]
                i += 2
            else:
                # Flag without value
                extra_args[key] = None
                i += 1
        else:
            # Skip non-flag arguments
            i += 1

    # Create and run headless Claude
    runner = HeadlessClaudeRunner(
        vicoa_api_key=args.api_key,
        session_id=session_id,
        vicoa_base_url=args.base_url,
        initial_prompt=args.prompt,
        extra_args=extra_args,
        permission_mode=args.permission_mode,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
        cwd=args.cwd,
        agent_name=args.name,
        enable_thinking=args.enable_thinking,
    )

    logger.info("Starting headless Claude Code session...")

    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Headless Claude session interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
