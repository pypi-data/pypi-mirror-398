# mcp_client_async.py
import uuid
import time
import asyncio
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


class MCPError(Exception):
    pass


class MCPClient:
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retries: int = 1,
        proxies=None,
    ):
        """
        base_url: full MCP HTTP endpoint e.g. http://localhost:3000/mcp
        headers: extra headers (e.g. {"Authorization": "Bearer ..."})
        timeout: request timeout seconds
        retries: number of attempts for network errors
        proxies: httpx proxies dict, e.g.
            {
              "http://": "http://127.0.0.1:8080",
              "https://": "http://127.0.0.1:8080"
            }
        """
        self.base_url = base_url.rstrip("/")
        self.headers = DEFAULT_HEADERS.copy()
        if headers:
            self.headers.update(headers)

        self.timeout = timeout
        self.retries = max(1, retries)

        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(self.timeout),
            proxy=proxies,
        )

        # local session cache
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # -------------------------
    # JSON-RPC core
    # -------------------------
    async def _rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }

        last_exc: Optional[Exception] = None

        for attempt in range(self.retries):
            try:
                r = await self._client.post(self.base_url, json=payload)
                r.raise_for_status()
            except httpx.HTTPError as e:
                last_exc = e
                await asyncio.sleep(0.2 * (attempt + 1))
                continue

            try:
                data = r.json()
            except ValueError:
                raise MCPError(
                    f"Invalid JSON response (status {r.status_code}): {r.text}"
                )

            if err := data.get("error"):
                raise MCPError(
                    {
                        "code": err.get("code"),
                        "message": err.get("message"),
                        "data": err.get("data"),
                    }
                )

            return data.get("result", {})

        raise MCPError(f"Request failed after {self.retries} attempts: {last_exc}")

    # -------------------------
    # Tool wrappers
    # -------------------------

    async def call_tool_structured(
        self, tool: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        res = await self._rpc("callTool", {"tool": tool, "arguments": arguments or {}})

        if isinstance(res, dict) and "structuredContent" in res:
            return res["structuredContent"]

        return res

    async def call_tool(
        self, tool: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return await self._rpc("callTool", {"tool": tool, "arguments": arguments or {}})

    # -------------------------
    # Session helpers
    # -------------------------

    async def create_session(self, cdpUrl: str) -> str:
        result = await self.call_tool_structured("createSession", {"cdpUrl": cdpUrl})

        session_id = (
            result.get("sessionId") or result.get("session_id") or result.get("id")
        )

        if not session_id:
            raise MCPError("createSession did not return sessionId")

        self._sessions[session_id] = {"created_at": time.time()}
        return session_id

    async def close_session(self, session_id: str) -> bool:
        try:
            await self.call_tool_structured("closeSession", {"sessionId": session_id})
            self._sessions.pop(session_id, None)
            return True
        except MCPError:
            self._sessions.pop(session_id, None)
            raise

    def list_local_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    async def aclose(self):
        """Close the httpx async client"""
        await self._client.aclose()
