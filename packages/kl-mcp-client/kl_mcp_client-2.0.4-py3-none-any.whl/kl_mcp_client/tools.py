from functools import wraps
from typing import Any, Dict, Optional

from .client import MCPClient


def _ensure_client(func):
    """Decorator kiểm tra self.client != None trước khi gọi tool."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.client is None:
            return {
                "ok": False,
                "error": "MCP client not connected. Call connect mcp server first.",
            }
        return func(self, *args, **kwargs)

    return wrapper


class MCPTools:
    """
    Wrapper chuẩn cho Google ADK + MCP Server.
    - Tool nào trả text/html/... → dùng structuredContent
    - Tool screenshot → trả đúng content để ADK Web hiển thị image
    """

    def __init__(self):
        self.client = None

    # ======================================================
    # SESSION MANAGEMENT
    # ======================================================
    def connect_mcp(self, mcpUrl: str) -> Dict[str, Any]:
        # sid = self.client.create_session(mcpUrl)
        self.client = MCPClient(base_url=mcpUrl, headers=None, timeout=30, retries=2)
        return {"ok": True, "cdpUrl": "http://localhost:9222"}

    @_ensure_client
    def create_session(self, cdpUrl: str) -> Dict[str, Any]:
        sid = self.client.create_session(cdpUrl)
        return {"sessionId": sid}

    @_ensure_client
    def close_session(self, sessionId: str) -> Dict[str, Any]:
        ok = self.client.close_session(sessionId)
        return {"ok": bool(ok)}

    @_ensure_client
    def list_sessions(self) -> Dict[str, Any]:
        return {"sessions": self.client.list_local_sessions()}

    # ======================================================
    # NAVIGATION & DOM
    # ======================================================
    @_ensure_client
    def open_page(self, sessionId: str, url: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "openPage", {"sessionId": sessionId, "url": url}
        ).get("structuredContent", {})

    @_ensure_client
    def get_html(self, sessionId: str) -> Dict[str, Any]:
        return self.client.call_tool("getHTML", {"sessionId": sessionId}).get(
            "structuredContent", {}
        )

    @_ensure_client
    def screenshot(self, sessionId: str) -> Dict[str, Any]:
        """
        Trả về đúng phần IMAGE content:
        {
          "type": "image",
          "mimeType": "image/png",
          "data": "<base64>"
        }
        """
        full = self.client.call_tool("screenshot", {"sessionId": sessionId})
        return full["content"][0]

    @_ensure_client
    def click(self, sessionId: str, selector: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "click", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def type(self, sessionId: str, selector: str, text: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "type", {"sessionId": sessionId, "selector": selector, "text": text}
        ).get("structuredContent", {})

    @_ensure_client
    def evaluate(self, sessionId: str, expression: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "evaluate", {"sessionId": sessionId, "expression": expression}
        ).get("structuredContent", {})

    # ======================================================
    # ELEMENT UTILITIES
    # ======================================================
    @_ensure_client
    def find_element(self, sessionId: str, selector: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "findElement", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def find_all(self, sessionId: str, selector: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "findAll", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def get_bounding_box(self, sessionId: str, selector: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "getBoundingBox", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def click_bounding_box(self, sessionId: str, selector: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "clickBoundingBox", {"sessionId": sessionId, "selector": selector}
        ).get("structuredContent", {})

    @_ensure_client
    def upload_file(
        self,
        sessionId: str,
        selector: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Upload file (kể cả video lớn) vào input[type=file] theo luồng mới:
        1. Multipart upload file lên MCP server
        2. Nhận uploadId
        3. Gọi MCP tool uploadFile với uploadId

        Args:
            sessionId: MCP browser session
            selector: CSS selector, ví dụ 'input[type=file]'
            file_path: đường dẫn file local (video, pdf, doc, ...)
        """

        if not file_path:
            return {"ok": False, "error": "file_path is required"}

        # --------------------------------------------------
        # 1️⃣ Multipart upload file lên MCP server
        # --------------------------------------------------
        try:
            with open(file_path, "rb") as f:
                resp = self.client.http.post(
                    "/upload",
                    files={"file": f},
                    timeout=300,  # upload file lớn
                )
        except Exception as e:
            return {"ok": False, "error": f"upload http failed: {e}"}

        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"upload http error {resp.status_code}: {resp.text}",
            }

        data = resp.json()
        upload_id = data.get("uploadId")
        if not upload_id:
            return {"ok": False, "error": "uploadId not returned from server"}

        # --------------------------------------------------
        # 2️⃣ Gọi MCP tool uploadFile (PATH MODE)
        # --------------------------------------------------
        result = self.client.call_tool(
            "uploadFile",
            {
                "sessionId": sessionId,
                "selector": selector,
                "uploadId": upload_id,
            },
        )

        return result.get("structuredContent", {})

    @_ensure_client
    def wait_for_selector(
        self, sessionId: str, selector: str, timeoutMs: Optional[int] = None
    ) -> Dict[str, Any]:
        args = {"sessionId": sessionId, "selector": selector}
        if timeoutMs is not None:
            args["timeoutMs"] = int(timeoutMs)

        return self.client.call_tool("waitForSelector", args).get(
            "structuredContent", {}
        )

    # ======================================================
    # TAB MANAGEMENT
    # ======================================================
    @_ensure_client
    def new_tab(
        self, sessionId: str, url: Optional[str] = "about:blank"
    ) -> Dict[str, Any]:
        return self.client.call_tool(
            "newTab", {"sessionId": sessionId, "url": url}
        ).get("structuredContent", {})

    @_ensure_client
    def switch_tab(self, sessionId: str, targetId: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "switchTab", {"sessionId": sessionId, "targetId": targetId}
        ).get("structuredContent", {})

    # ======================================================
    # ADVANCED ACTIONS
    # ======================================================
    @_ensure_client
    def click_to_text(self, sessionId: str, text: str) -> dict:
        return self.client.call_tool(
            "clickToText", {"sessionId": sessionId, "text": text}
        ).get("structuredContent", {})

    @_ensure_client
    def find_element_xpath(self, sessionId: str, xpath: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "findElementByXPath", {"sessionId": sessionId, "xpath": xpath}
        ).get("structuredContent", {})

    @_ensure_client
    def find_element_by_text(self, sessionId: str, text: str) -> Dict[str, Any]:
        return self.client.call_tool(
            "findElementByText", {"sessionId": sessionId, "text": text}
        ).get("structuredContent", {})

    @_ensure_client
    def click_by_node_id(self, sessionId: str, nodeId: int) -> Dict[str, Any]:
        return self.client.call_tool(
            "clickByNodeId", {"sessionId": sessionId, "nodeId": nodeId}
        ).get("structuredContent", {})

    @_ensure_client
    def import_cookies(self, sessionId: str, cookies: dict) -> Dict[str, Any]:
        return self.client.call_tool(
            "importCookies", {"sessionId": sessionId, "cookies": cookies}
        ).get("structuredContent", {})

    @_ensure_client
    def get_dom_tree(self, sessionId, args=None):
        return self.client.call_tool(
            "getDomTree", {"sessionId": sessionId, "args": args or {}}
        )

    @_ensure_client
    def get_clickable(self, sessionId, args=None):
        return self.client.call_tool(
            "getClickable", {"sessionId": sessionId, "args": args or {}}
        )

    @_ensure_client
    def selector_map(self, sessionId, selector, args=None):
        return self.client.call_tool(
            "selectorMap",
            {"sessionId": sessionId, "selector": selector, "args": args or {}},
        )

    @_ensure_client
    def find_element_by_prompt(self, sessionId: str, prompt: str) -> Dict[str, Any]:
        """
        Gọi tool findElementByPrompt trên MCP server.
        Trả về structuredContent gồm: html, nodeId.
        """
        return self.client.call_tool(
            "findElementByPrompt", {"sessionId": sessionId, "prompt": prompt}
        ).get("structuredContent", {})

    # ======================================================
    # AI / CONTENT PARSING
    # ======================================================
    @_ensure_client
    def parse_html_by_prompt(self, html: str, prompt: str) -> Dict[str, Any]:
        """
        Parse HTML content using AI with dynamic prompt-defined structure.

        Args:
            html: Raw HTML string (client-provided)
            prompt: Instruction that defines what to extract and output structure
                    Example:
                      - "Hãy lấy nội dung bài viết, struct trả về { content }"
                      - "Hãy lấy số lượng like, share, comment, trả JSON { like, share, comment }"

        Returns:
            structuredContent (dynamic JSON defined by prompt)
        """
        return self.client.call_tool(
            "parseHTMLByPrompt",
            {
                "html": html,
                "prompt": prompt,
            },
        ).get("structuredContent", {})
