"""Background daemon that keeps a Vicoa CLI machine online for remote sessions."""

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Any, Optional
from uuid import uuid4

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from vicoa.utils import get_project_path

logger = logging.getLogger(__name__)

STATE_PATH = Path.home() / ".vicoa" / "daemon_state.json"
DEFAULT_POLL_INTERVAL_SECONDS = 5
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30
REQUEST_TIMEOUT_SECONDS = 15


@dataclass
class MachineRegistration:
    machine_id: str
    display_name: Optional[str]
    hostname: Optional[str]
    platform: Optional[str]


class MachineDaemon:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
        cli_version: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.poll_interval = max(1, poll_interval)
        self.heartbeat_interval = max(5, heartbeat_interval)
        self.cli_version = cli_version
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        self.machine_id: Optional[str] = None
        self._last_heartbeat_sent: float = 0.0

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> dict[str, Any]:
        if not STATE_PATH.exists():
            return {}
        try:
            with STATE_PATH.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _save_state(self, state: dict[str, Any]) -> None:
        try:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with STATE_PATH.open("w", encoding="utf-8") as fh:
                json.dump(state, fh, indent=2)
        except Exception as exc:
            print(f"[daemon] failed to persist state: {exc}")

    # ------------------------------------------------------------------
    # REST helpers
    # ------------------------------------------------------------------
    def _post(self, path: str, payload: dict[str, Any] | None = None) -> Response:
        url = f"{self.base_url}{path}"
        return self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)

    def _patch(self, path: str, payload: dict[str, Any]) -> Response:
        url = f"{self.base_url}{path}"
        return self.session.patch(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)

    # ------------------------------------------------------------------
    # Registration & heartbeat
    # ------------------------------------------------------------------
    def register_machine(self) -> MachineRegistration:
        state = self._load_state()
        machine_id = state.get("machine_id")

        payload: dict[str, Any] = {
            "machine_id": machine_id,
            "hostname": platform.node(),
            "platform": platform.platform(),
            "display_name": state.get("display_name"),
            "metadata": {
                "cli_version": self.cli_version,
                "python_version": platform.python_version(),
                "cwd": get_project_path(),
            },
        }

        response = self._post("/api/v1/machines/register", payload)
        response.raise_for_status()
        data = response.json()

        self.machine_id = data["machine_id"]
        state["machine_id"] = self.machine_id
        state["display_name"] = data.get("display_name")
        self._save_state(state)

        print(
            f"[daemon] machine registered as {self.machine_id} (hostname={data.get('hostname')})"
        )

        return MachineRegistration(
            machine_id=data["machine_id"],
            display_name=data.get("display_name"),
            hostname=data.get("hostname"),
            platform=data.get("platform"),
        )

    def send_heartbeat(self) -> None:
        if not self.machine_id:
            return

        payload = {
            "metadata": {
                "last_pid": os.getpid(),
            }
        }
        try:
            response = self._post(
                f"/api/v1/machines/{self.machine_id}/heartbeat", payload
            )
            response.raise_for_status()
            self._last_heartbeat_sent = time.time()
        except RequestException as exc:
            logger.debug(f"Heartbeat failed (will retry): {exc}")

    # ------------------------------------------------------------------
    # Spawn handling
    # ------------------------------------------------------------------
    def poll_for_requests(self) -> Optional[dict[str, Any]]:
        if not self.machine_id:
            return None
        try:
            response = self._post(
                f"/api/v1/machines/{self.machine_id}/spawn-requests/next",
                payload={},
            )
        except Timeout:
            logger.debug("Poll request timed out (will retry)")
            return None
        except RequestException as exc:
            logger.debug(f"Failed to poll for requests (will retry): {exc}")
            return None

        if response.status_code == 204:
            return None

        if response.status_code != 200:
            print(
                f"[daemon] unexpected response polling spawn requests: {response.status_code}"
            )
            return None

        try:
            return response.json()
        except ValueError:
            print("[daemon] failed to decode spawn request payload")
            return None

    def report_request_status(
        self,
        request_id: str,
        status: str,
        *,
        agent_instance_id: str | None = None,
        message: str | None = None,
        retry_on_missing_agent: bool = False,
        retry_timeout: float = 30.0,
    ) -> bool:
        if not self.machine_id:
            return False
        if not request_id:
            print("[daemon] unable to report spawn status without request_id")
            return False

        payload = {
            "status": status,
            "agent_instance_id": agent_instance_id,
            "message": message,
        }

        deadline = time.time() + retry_timeout if retry_on_missing_agent else None

        while True:
            try:
                response = self._patch(
                    f"/api/v1/machines/{self.machine_id}/spawn-requests/{request_id}",
                    payload,
                )
            except RequestException as exc:
                print(f"[daemon] failed to report request status: {exc}")
                return False

            if response.status_code == 200:
                return True

            if retry_on_missing_agent and response.status_code == 400:
                detail: str | None = None
                try:
                    body = response.json()
                    detail = body.get("detail") if isinstance(body, dict) else None
                except ValueError:
                    detail = None

                if detail and "agent_instance_id not found" in detail:
                    if deadline is not None and time.time() < deadline:
                        time.sleep(0.5)
                        continue
                    print(
                        "[daemon] agent instance not yet available to update spawn request"
                    )
                    return False

            print(
                f"[daemon] unexpected response when reporting status: {response.status_code}"
            )
            try:
                print(f"[daemon] response body: {response.text}")
            except Exception:
                pass
            return False

    # ------------------------------------------------------------------
    # Session launching
    # ------------------------------------------------------------------
    def _build_headless_command(
        self,
        *,
        directory: str,
        agent: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        cmd = [
            sys.executable,
            "-m",
            "vicoa.cli",
            "headless",
            "--api-key",
            self.api_key,
            "--base-url",
            self.base_url,
            "--cwd",
            directory,
            "--name",
            agent.replace("_", " ").title(),
        ]
        if session_id:
            cmd.extend(["--session-id", session_id])
        permission_mode = self._extract_permission_mode(metadata)
        if permission_mode:
            cmd.extend(["--permission-mode", permission_mode])
        else:
            cmd.extend(["--permission-mode", "acceptEdits"])
        prompt = self._extract_prompt(metadata)
        if prompt:
            cmd.extend(["--prompt", prompt])
        allowed_tools = self._extract_tool_list(metadata, "allowed_tools")
        if allowed_tools:
            cmd.extend(["--allowed-tools", allowed_tools])
        disallowed_tools = self._extract_tool_list(metadata, "disallowed_tools")
        if disallowed_tools:
            cmd.extend(["--disallowed-tools", disallowed_tools])
        if agent and agent.lower() == "codex":
            cmd.extend(["--agent", "codex"])
        return cmd

    def _extract_tool_list(
        self, metadata: dict[str, Any] | None, key: str
    ) -> str | None:
        if not metadata:
            return None
        value = metadata.get(key)
        if not value:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                return ",".join(cleaned)
        return None

    def _extract_prompt(self, metadata: dict[str, Any] | None) -> str | None:
        if not metadata:
            return None
        prompt = metadata.get("prompt") or metadata.get("initial_prompt")
        if isinstance(prompt, str) and prompt.strip():
            return prompt
        return None

    def _extract_permission_mode(self, metadata: dict[str, Any] | None) -> str | None:
        if not metadata:
            return None
        value = metadata.get("permission_mode")
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        if not normalized:
            return None
        allowed_modes = {"acceptEdits", "bypassPermissions", "default", "plan"}
        if normalized in allowed_modes:
            return normalized
        lowered = normalized.lower()
        mapping = {
            "accept_edits": "acceptEdits",
            "accept-edits": "acceptEdits",
            "accept": "acceptEdits",
            "bypass": "bypassPermissions",
            "plan mode": "plan",
        }
        if lowered in mapping:
            return mapping[lowered]
        return None

    def _monitor_session_process(
        self,
        *,
        request_id: str,
        session_id: str,
        process: subprocess.Popen[bytes],
    ) -> None:
        """Monitor a running headless process and report its completion status."""
        return_code: int | None = None
        try:
            return_code = process.wait()
        except Exception as exc:
            self.report_request_status(
                request_id,
                "error",
                agent_instance_id=session_id,
                message=str(exc),
            )
            return
        if return_code == 0:
            self.report_request_status(
                request_id,
                "success",
                agent_instance_id=session_id,
                message="Session completed successfully",
            )
        else:
            self.report_request_status(
                request_id,
                "error",
                agent_instance_id=session_id,
                message=f"Headless session exited with code {return_code}",
            )

    def process_request(self, request: dict[str, Any]) -> None:
        request_id_raw = request.get("request_id")
        if not request_id_raw:
            print("[daemon] spawn request missing request_id; skipping")
            return

        request_id = str(request_id_raw)
        directory = request.get("directory")
        agent = request.get("agent", "claude code")
        metadata_raw = request.get("metadata")
        metadata = metadata_raw if isinstance(metadata_raw, dict) else None

        if not isinstance(directory, str) or not directory.strip():
            self.report_request_status(
                request_id,
                "error",
                message="Invalid directory supplied",
            )
            return

        expanded_directory = os.path.expanduser(directory.strip())
        try:
            os.makedirs(expanded_directory, exist_ok=True)
        except Exception as exc:
            self.report_request_status(
                request_id,
                "error",
                message=f"Unable to prepare directory: {exc}",
            )
            return

        env = os.environ.copy()
        env.setdefault("VICOA_API_KEY", self.api_key)
        env.setdefault("VICOA_AGENT_TYPE", agent)

        session_id = str(uuid4())
        env["VICOA_AGENT_INSTANCE_ID"] = session_id

        command = self._build_headless_command(
            directory=expanded_directory,
            agent=agent,
            session_id=session_id,
            metadata=metadata,
        )

        print(
            f"[daemon] launching headless session (request={request_id}) at {expanded_directory}"
        )

        # Send immediate heartbeat to show machine is active
        self.send_heartbeat()

        try:
            process = subprocess.Popen(
                command,
                cwd=expanded_directory,
                env=env,
            )
        except Exception as exc:
            self.report_request_status(
                request_id,
                "error",
                message=f"Failed to launch headless session: {exc}",
            )
            return

        if not self._wait_for_process_ready(process):
            exit_code = process.poll()
            self.report_request_status(
                request_id,
                "error",
                message=(
                    "Headless session failed to start"
                    if exit_code is None
                    else f"Headless process exited with code {exit_code}"
                ),
            )
            return

        started = self.report_request_status(
            request_id,
            "started",
            agent_instance_id=session_id,
            message="Session started",
            retry_on_missing_agent=True,
            retry_timeout=30.0,
        )

        if not started:
            print(
                f"[daemon] failed to mark request {request_id} as started; terminating session"
            )
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
            self.report_request_status(
                request_id,
                "error",
                message="Failed to start headless session",
            )
            return

        # Launch monitor thread so we can continue polling
        session_thread = Thread(
            target=self._monitor_session_process,
            kwargs={
                "request_id": request_id,
                "session_id": session_id,
                "process": process,
            },
            daemon=True,
        )
        session_thread.start()

        print(
            f"[daemon] session {session_id} running in background, continuing to poll for requests"
        )

    def _wait_for_process_ready(
        self,
        process: subprocess.Popen[bytes],
        *,
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if process.poll() is not None:
                return False
            time.sleep(interval)
        return True

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.register_machine()
        self.send_heartbeat()

        try:
            while True:
                now = time.time()
                if now - self._last_heartbeat_sent >= self.heartbeat_interval:
                    self.send_heartbeat()

                request = self.poll_for_requests()
                if request:
                    self.process_request(request)
                    continue

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("[daemon] shutting down")


def run_daemon(
    *,
    api_key: str,
    base_url: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    cli_version: str | None = None,
) -> None:
    daemon = MachineDaemon(
        api_key=api_key,
        base_url=base_url,
        poll_interval=poll_interval,
        heartbeat_interval=heartbeat_interval,
        cli_version=cli_version,
    )
    daemon.run()
