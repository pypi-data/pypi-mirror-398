from __future__ import annotations

import asyncio
import base64
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import httpx

from .auth import Authenticator
from .config import COLAB_API_URL, Config
from .exceptions import (
    AccountBlockedError,
    ExecutionTimeoutError,
    KernelNotReadyError,
    QuotaDeniedError,
    ServerAssignmentError,
    ServerNotAssignedError,
    SessionError,
    UsageQuotaExceededError,
    WebSocketError,
)
from .models import (
    AcceleratorType,
    Assignment,
    ExecutionError,
    ExecutionResult,
    KernelState,
    ProxyInfo,
    RuntimeVariant,
    Session,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

OUTCOME_ERRORS: dict[int, type[ServerAssignmentError]] = {
    1: QuotaDeniedError,
    2: UsageQuotaExceededError,
    5: AccountBlockedError,
}

OUTCOME_MESSAGES: dict[int, str] = {
    1: "Quota denied for requested variant",
    2: "Usage time quota exceeded",
    5: "Account blocked",
}


class ColabClient:
    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        self._auth = Authenticator(self._config)
        self._http = httpx.Client(timeout=self._config.http_timeout)
        self._assignment: Assignment | None = None
        self._session: Session | None = None
        self._keep_alive_thread: threading.Thread | None = None
        self._stop_keep_alive = threading.Event()

    @property
    def assignment(self) -> Assignment | None:
        return self._assignment

    @property
    def session(self) -> Session | None:
        return self._session

    @property
    def is_connected(self) -> bool:
        return self._assignment is not None

    @property
    def has_session(self) -> bool:
        return self._session is not None

    def login(self, interactive: bool = True) -> bool:
        return self._auth.login(interactive=interactive)

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._auth.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Colab-Client-Agent": "vscode",
        }

    def _get_tunnel_headers(self) -> dict[str, str]:
        headers = self._get_headers()
        headers["X-Colab-Tunnel"] = "Google"
        return headers

    def _get_proxy_headers(self) -> dict[str, str]:
        headers = self._get_headers()
        if self._assignment and self._assignment.proxy_token:
            headers["X-Colab-Runtime-Proxy-Token"] = self._assignment.proxy_token
        return headers

    def _strip_xssi(self, text: str) -> str:
        if text.startswith(")]}'\\n"):
            return text[5:]
        if text.startswith(")]}'"):
            return text[4:]
        return text

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        headers = kwargs.pop("headers", self._get_headers())
        resp = self._http.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            if self._auth.refresh():
                headers = self._get_headers()
                resp = self._http.request(method, url, headers=headers, **kwargs)

        return resp

    def list_assignments(self) -> list[dict[str, Any]]:
        url = f"{COLAB_API_URL}/tun/m/assignments"
        params = {"authuser": "0"}
        resp = self._request("GET", url, params=params)
        resp.raise_for_status()
        data = json.loads(self._strip_xssi(resp.text))
        return data.get("assignments", [])

    def get_or_create_server(
        self,
        variant: RuntimeVariant = RuntimeVariant.DEFAULT,
        accelerator: AcceleratorType = AcceleratorType.NONE,
    ) -> Assignment:
        assignments = self.list_assignments()

        if assignments:
            a = assignments[0]
            logger.info("Found existing server: %s", a["endpoint"])
            proxy_info = self.refresh_connection(a["endpoint"])
            self._assignment = Assignment(
                endpoint=a["endpoint"],
                accelerator=AcceleratorType.from_string(a.get("accelerator", "")),
                variant=RuntimeVariant.from_string(a.get("variant", variant.value)),
                proxy_info=ProxyInfo(
                    url=proxy_info.get("url", ""),
                    token=proxy_info.get("token", ""),
                ),
            )
            return self._assignment

        return self.assign_server(variant, accelerator)

    def refresh_connection(self, endpoint: str) -> dict[str, str]:
        url = f"{COLAB_API_URL}/tun/m/runtime-proxy-token"
        params = {"authuser": "0", "endpoint": endpoint, "port": "8080"}
        headers = self._get_tunnel_headers()
        resp = self._http.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return json.loads(self._strip_xssi(resp.text))

    def assign_server(
        self,
        variant: RuntimeVariant = RuntimeVariant.DEFAULT,
        accelerator: AcceleratorType = AcceleratorType.NONE,
    ) -> Assignment:
        notebook_id = str(uuid.uuid4())
        notebook_hash = notebook_id.replace("-", "_") + "." * (44 - len(notebook_id))

        url = f"{COLAB_API_URL}/tun/m/assign"
        params: dict[str, str] = {"authuser": "0", "nbh": notebook_hash}

        if variant != RuntimeVariant.DEFAULT:
            params["variant"] = variant.value
        if accelerator != AcceleratorType.NONE:
            params["accelerator"] = accelerator.value

        headers = self._get_headers()
        resp = self._http.get(url, params=params, headers=headers)

        if not resp.is_success:
            logger.error("Error response: %s - %s", resp.status_code, resp.text)
            resp.raise_for_status()

        data = json.loads(self._strip_xssi(resp.text))

        if "endpoint" in data:
            self._assignment = self._parse_assignment(data, variant)
            logger.info("Reusing existing server: %s", self._assignment.endpoint)
            return self._assignment

        xsrf_token = data.get("token")
        if not xsrf_token:
            raise ServerAssignmentError("No XSRF token received")

        headers["X-Goog-Colab-Token"] = xsrf_token
        resp = self._http.post(url, params=params, headers=headers)
        resp.raise_for_status()
        data = json.loads(self._strip_xssi(resp.text))

        outcome = data.get("outcome")
        if outcome and outcome not in (0, 4):
            error_cls = OUTCOME_ERRORS.get(outcome, ServerAssignmentError)
            message = OUTCOME_MESSAGES.get(outcome, f"Unknown outcome: {outcome}")
            raise error_cls(message)

        self._assignment = self._parse_assignment(data, variant)
        logger.info("New server assigned: %s", self._assignment.endpoint)
        return self._assignment

    def _parse_assignment(self, data: dict[str, Any], variant: RuntimeVariant) -> Assignment:
        proxy_info_data = data.get("runtimeProxyInfo", {})
        proxy_info = (
            ProxyInfo(
                url=proxy_info_data.get("url", ""),
                token=proxy_info_data.get("token", ""),
            )
            if proxy_info_data
            else None
        )

        return Assignment(
            endpoint=data["endpoint"],
            accelerator=AcceleratorType.from_string(data.get("accelerator", "")),
            variant=RuntimeVariant.from_string(data.get("variant", variant.value)),
            proxy_info=proxy_info,
        )

    def keep_alive(self) -> bool:
        if not self._assignment:
            return False

        url = f"{COLAB_API_URL}/tun/m/{self._assignment.endpoint}/keep-alive/"
        params = {"authuser": "0"}
        resp = self._http.get(url, params=params, headers=self._get_tunnel_headers())
        return resp.status_code == 200

    def start_keep_alive(self, interval: int | None = None) -> None:
        if self._keep_alive_thread and self._keep_alive_thread.is_alive():
            return

        interval = interval or self._config.keep_alive_interval
        self._stop_keep_alive.clear()

        def worker() -> None:
            while not self._stop_keep_alive.wait(interval):
                try:
                    self.keep_alive()
                except Exception:
                    pass

        self._keep_alive_thread = threading.Thread(target=worker, daemon=True)
        self._keep_alive_thread.start()
        logger.info("Keep-alive started (every %ds)", interval)

    def stop_keep_alive(self) -> None:
        self._stop_keep_alive.set()
        if self._keep_alive_thread:
            self._keep_alive_thread.join(timeout=1)
            self._keep_alive_thread = None

    def get_or_create_session(self) -> Session:
        if not self._assignment:
            raise ServerNotAssignedError("No server assigned")

        sessions = self.list_sessions()
        for session_data in sessions:
            kernel = session_data.get("kernel", {})
            state = kernel.get("execution_state", "")

            if state in ("idle", "busy"):
                self._session = Session(
                    id=session_data["id"],
                    kernel_id=kernel["id"],
                    path=session_data.get("path", ""),
                    state=KernelState(state),
                )
                logger.info("Reusing session: %s", self._session.id)
                return self._session

        return self.create_session()

    def create_session(self) -> Session:
        if not self._assignment:
            raise ServerNotAssignedError("No server assigned")

        if self._assignment.proxy_url:
            base_url = self._assignment.proxy_url.rstrip("/")
            url = f"{base_url}/api/sessions"
            headers = self._get_proxy_headers()
            params: dict[str, str] = {}
        else:
            url = f"{COLAB_API_URL}/tun/m/{self._assignment.endpoint}/api/sessions"
            headers = self._get_tunnel_headers()
            params = {"authuser": "0"}

        session_data = {
            "path": f"notebook_{uuid.uuid4().hex[:8]}.ipynb",
            "name": "",
            "type": "notebook",
            "kernel": {"name": "python3"},
        }

        resp = self._http.post(url, params=params, headers=headers, json=session_data)

        if not resp.is_success:
            logger.error("Create session error: %s - %s", resp.status_code, resp.text[:500])
            raise SessionError(f"Failed to create session: {resp.status_code}")

        data = resp.json()
        self._session = Session(
            id=data["id"],
            kernel_id=data["kernel"]["id"],
            path=data.get("path", ""),
            state=KernelState.STARTING,
        )

        logger.info("Session created: %s", self._session.id)
        self._wait_for_kernel_ready()
        return self._session

    def list_sessions(self) -> list[dict[str, Any]]:
        if not self._assignment:
            raise ServerNotAssignedError("No server assigned")

        url = f"{COLAB_API_URL}/tun/m/{self._assignment.endpoint}/api/sessions"
        params = {"authuser": "0"}
        resp = self._http.get(url, params=params, headers=self._get_tunnel_headers())
        resp.raise_for_status()
        return resp.json()

    def _wait_for_kernel_ready(self, max_wait: int | None = None) -> bool:
        if not self._assignment or not self._session:
            return False

        max_wait = max_wait or self._config.kernel_wait_timeout
        headers = self._get_proxy_headers()
        base_url = self._assignment.proxy_url

        logger.info("Waiting for kernel to be ready...")

        for i in range(max_wait // 3):
            try:
                resp = self._http.get(
                    f"{base_url}/api/kernels/{self._session.kernel_id}",
                    headers=headers,
                    timeout=5,
                )

                if resp.is_success:
                    kernel = resp.json()
                    state = kernel.get("execution_state", "unknown")
                    logger.debug("Kernel state: %s", state)

                    if state in ("idle", "busy"):
                        self._session.state = KernelState(state)
                        logger.info("Kernel is ready!")
                        return True

                    if state == "starting" and i == 5:
                        logger.info("Kernel stuck in starting, restarting...")
                        self._restart_kernel()

            except Exception as e:
                logger.debug("Check failed: %s", e)

            time.sleep(3)

        logger.warning("Kernel may not be ready after %ds", max_wait)
        return False

    def _restart_kernel(self) -> None:
        if not self._assignment or not self._session:
            return

        headers = self._get_proxy_headers()
        base_url = self._assignment.proxy_url

        resp = self._http.post(
            f"{base_url}/api/kernels/{self._session.kernel_id}/restart",
            headers=headers,
            timeout=30,
        )

        if resp.is_success:
            logger.info("Kernel restarted")
            time.sleep(5)

    def execute(self, code: str, timeout: float | None = None) -> ExecutionResult:
        return asyncio.run(self.execute_async(code, timeout))

    async def execute_async(self, code: str, timeout: float | None = None) -> ExecutionResult:
        if not self._assignment or not self._session:
            raise ServerNotAssignedError("No kernel available. Call create_session() first.")

        import websockets

        timeout = timeout or self._config.execution_timeout

        if self._assignment.proxy_url:
            base_url = self._assignment.proxy_url.rstrip("/")
            ws_base = base_url.replace("https://", "wss://").replace("http://", "ws://")
            ws_url = f"{ws_base}/api/kernels/{self._session.kernel_id}/channels?session_id={self._session.id}"
            extra_headers = {
                "X-Colab-Runtime-Proxy-Token": self._assignment.proxy_token,
                "X-Colab-Client-Agent": "vscode",
            }
        else:
            ws_url = (
                f"wss://colab.research.google.com/tun/m/{self._assignment.endpoint}"
                f"/api/kernels/{self._session.kernel_id}/channels?session_id={self._session.id}"
            )
            extra_headers = {
                "Authorization": f"Bearer {self._auth.token}",
                "X-Colab-Tunnel": "Google",
            }

        logger.debug("Connecting to WebSocket...")

        kernel_info_request = self._create_message("kernel_info_request", {})
        execute_request = self._create_message(
            "execute_request",
            {
                "code": code,
                "silent": False,
                "store_history": True,
                "user_expressions": {},
                "allow_stdin": False,
                "stop_on_error": True,
            },
        )
        msg_id = execute_request["header"]["msg_id"]

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        result_data: dict[str, Any] | None = None
        error_data: ExecutionError | None = None
        display_data: list[dict[str, Any]] = []

        try:
            async with websockets.connect(
                ws_url,
                additional_headers=extra_headers,
                ping_interval=30,
                ping_timeout=10,
            ) as ws:
                logger.debug("WebSocket connected!")

                await ws.send(json.dumps(kernel_info_request))

                for _ in range(10):
                    try:
                        msg_data = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        data = json.loads(msg_data)
                        msg_type = data.get("msg_type") or data.get("header", {}).get("msg_type")
                        if msg_type == "kernel_info_reply":
                            break
                    except asyncio.TimeoutError:
                        continue

                await ws.send(json.dumps(execute_request))
                logger.debug("Executing code...")

                start_time = time.time()
                execution_done = False

                while not execution_done and (time.time() - start_time) < timeout:
                    try:
                        msg_data = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(msg_data)
                        msg_type = data.get("msg_type") or data.get("header", {}).get("msg_type")
                        parent_msg_id = data.get("parent_header", {}).get("msg_id")

                        if parent_msg_id != msg_id:
                            continue

                        content = data.get("content", {})

                        if msg_type == "stream":
                            stream_name = content.get("name")
                            text = content.get("text", "")
                            if stream_name == "stdout":
                                stdout_parts.append(text)
                            elif stream_name == "stderr":
                                stderr_parts.append(text)

                        elif msg_type == "execute_result":
                            result_data = content.get("data", {})

                        elif msg_type == "display_data":
                            display_data.append(content.get("data", {}))

                        elif msg_type == "error":
                            error_data = ExecutionError(
                                name=content.get("ename", ""),
                                value=content.get("evalue", ""),
                                traceback=content.get("traceback", []),
                            )

                        elif msg_type == "execute_reply":
                            execution_done = True

                    except asyncio.TimeoutError:
                        continue

                if not execution_done:
                    raise ExecutionTimeoutError(f"Execution timed out after {timeout}s")

        except Exception as e:
            if not isinstance(e, ExecutionTimeoutError):
                raise WebSocketError(f"WebSocket error: {e}") from e
            raise

        return ExecutionResult(
            stdout="".join(stdout_parts),
            stderr="".join(stderr_parts),
            result=result_data,
            error=error_data,
            display_data=display_data,
        )

    def _create_message(self, msg_type: str, content: dict[str, Any]) -> dict[str, Any]:
        msg_id = uuid.uuid4().hex
        return {
            "header": {
                "msg_id": msg_id,
                "msg_type": msg_type,
                "username": "",
                "session": self._session.id if self._session else uuid.uuid4().hex,
                "date": datetime.now(timezone.utc).isoformat(),
                "version": "5.2",
            },
            "parent_header": {},
            "metadata": {},
            "content": content,
            "buffers": [],
            "channel": "shell",
        }

    def unassign_server(self) -> bool:
        if not self._assignment:
            return False

        url = f"{COLAB_API_URL}/tun/m/unassign/{self._assignment.endpoint}"
        params = {"authuser": "0"}

        resp = self._http.get(url, params=params, headers=self._get_headers())
        resp.raise_for_status()
        data = json.loads(self._strip_xssi(resp.text))

        xsrf_token = data.get("token")
        if not xsrf_token:
            return False

        headers = self._get_headers()
        headers["X-Colab-Xsrf-Token"] = xsrf_token
        resp = self._http.post(url, params=params, headers=headers)

        if resp.status_code == 200:
            self._assignment = None
            self._session = None
            logger.info("Server unassigned")
            return True

        return False

    def close(self) -> None:
        self.stop_keep_alive()
        self._http.close()

    def __enter__(self) -> ColabClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
