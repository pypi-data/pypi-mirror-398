# async_tools.py
from typing import Any, Dict, Optional

from .client import MCPClient


class MCPTools:
    """
    Async wrapper cho Google ADK + MCP Server.
    - Dùng MCPClientAsync (httpx async)
    - Tất cả method đều async
    - Screenshot trả về đúng format ADK Web yêu cầu
    """

    def __init__(self, client: MCPClient):
        self.client = client

    # ======================================================
    # SESSION MANAGEMENT
    # ======================================================

    async def create_session(self, cdpUrl: str) -> Dict[str, Any]:
        sid = await self.client.create_session(cdpUrl)
        return {"sessionId": sid}

    async def close_session(self, sessionId: str) -> Dict[str, Any]:
        ok = await self.client.close_session(sessionId)
        return {"ok": bool(ok)}

    async def list_sessions(self) -> Dict[str, Any]:
        return {"sessions": self.client.list_local_sessions()}

    # ======================================================
    # NAVIGATION & DOM
    # ======================================================

    async def open_page(self, sessionId: str, url: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "openPage", {"sessionId": sessionId, "url": url}
        )
        return res.get("structuredContent", {})

    async def get_html(self, sessionId: str) -> Dict[str, Any]:
        res = await self.client.call_tool("getHTML", {"sessionId": sessionId})
        return res.get("structuredContent", {})

    async def screenshot(self, sessionId: str) -> Dict[str, Any]:
        """
        ADK Web expects this structure:
        {
            "type": "image",
            "mimeType": "image/png",
            "data": "<base64>"
        }
        """
        res = await self.client.call_tool("screenshot", {"sessionId": sessionId})
        return res["content"][0]

    async def click(self, sessionId: str, selector: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "click", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def type(self, sessionId: str, selector: str, text: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "type", {"sessionId": sessionId, "selector": selector, "text": text}
        )
        return res.get("structuredContent", {})

    async def evaluate(self, sessionId: str, expression: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "evaluate", {"sessionId": sessionId, "expression": expression}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # ELEMENT UTILITIES
    # ======================================================

    async def find_element(self, sessionId: str, selector: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "findElement", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def find_all(self, sessionId: str, selector: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "findAll", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def get_bounding_box(self, sessionId: str, selector: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "getBoundingBox", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def click_bounding_box(self, sessionId: str, selector: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "clickBoundingBox", {"sessionId": sessionId, "selector": selector}
        )
        return res.get("structuredContent", {})

    async def upload_file(
        self, sessionId: str, selector: str, filename: str, base64data: str
    ) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "uploadFile",
            {
                "sessionId": sessionId,
                "selector": selector,
                "filename": filename,
                "data": base64data,
            },
        )
        return res.get("structuredContent", {})

    async def wait_for_selector(
        self, sessionId: str, selector: str, timeoutMs: Optional[int] = None
    ) -> Dict[str, Any]:
        args = {"sessionId": sessionId, "selector": selector}
        if timeoutMs is not None:
            args["timeoutMs"] = timeoutMs

        res = await self.client.call_tool("waitForSelector", args)
        return res.get("structuredContent", {})

    # ======================================================
    # TAB MANAGEMENT
    # ======================================================

    async def new_tab(
        self, sessionId: str, url: Optional[str] = "about:blank"
    ) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "newTab", {"sessionId": sessionId, "url": url}
        )
        return res.get("structuredContent", {})

    async def switch_tab(self, sessionId: str, targetId: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "switchTab", {"sessionId": sessionId, "targetId": targetId}
        )
        return res.get("structuredContent", {})

    # ======================================================
    # ADVANCED
    # ======================================================

    async def click_to_text(self, sessionId: str, text: str) -> dict:
        res = await self.client.call_tool(
            "clickToText", {"sessionId": sessionId, "text": text}
        )
        return res.get("structuredContent", {})

    async def find_element_xpath(self, sessionId: str, xpath: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "findElementByXPath", {"sessionId": sessionId, "xpath": xpath}
        )
        return res.get("structuredContent", {})

    async def find_element_by_text(self, sessionId: str, text: str) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "findElementByText", {"sessionId": sessionId, "text": text}
        )
        return res.get("structuredContent", {})

    async def click_by_node_id(self, sessionId: str, nodeId: int) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "clickByNodeId", {"sessionId": sessionId, "nodeId": nodeId}
        )
        return res.get("structuredContent", {})

    async def import_cookies(self, sessionId: str, cookies: dict) -> Dict[str, Any]:
        res = await self.client.call_tool(
            "importCookies", {"sessionId": sessionId, "cookies": cookies}
        )
        return res.get("structuredContent", {})

    async def parse_html_by_prompt(self, html: str, prompt: str) -> Dict[str, Any]:
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
        res = await self.client.call_tool(
            "parseHTMLByPrompt",
            {
                "html": html,
                "prompt": prompt,
            },
        )
        return res.get("structuredContent", {})
