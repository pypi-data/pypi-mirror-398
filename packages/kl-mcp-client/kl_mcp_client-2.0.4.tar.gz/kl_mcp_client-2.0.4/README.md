# 📦 kl-mcp-client

**kl-mcp-client** là SDK Python giúp giao tiếp với **MCP (Model Context Protocol) Browser Server** — một server trung gian điều khiển Chrome/Chromium qua CDP.

Thư viện này được thiết kế để:

- Điều khiển Chrome tự động: click, nhập liệu, screenshot, đọc DOM…
- Kết nối trình duyệt Chrome Remote qua CDP (Chrome DevTools Protocol)
- Tích hợp làm Web Automation Agent trong **Google ADK**
- Hoạt động độc lập như một browser automation SDK

---

# 🚀 Cài đặt

```bash
pip install kl-mcp-client
```

---

# 🧩 Thành phần của thư viện

Package gồm 2 module chính:

| File | Vai trò |
|------|---------|
| `client.py` | JSON-RPC HTTP Client giao tiếp với MCP Server |
| `tools.py`  | Wrapper cấp cao, cung cấp API tiện dụng cho các Agent & automation |

---

# ✨ Tính năng chính

### ✔ Điều khiển trình duyệt
- Mở tab, load URL  
- Click CSS selector, click bằng text, click bằng nodeId  
- Nhập text vào input  
- Screenshot (chuẩn ADK hiển thị được)

### ✔ DOM Tools nâng cao
- Find element by selector / text / XPath  
- Lấy bounding box  
- Lấy toàn bộ DOM Tree  
- Lấy danh sách clickable elements  
- Highlight elements (nếu server hỗ trợ)

### ✔ Tương tác hệ thống
- Upload file bằng base64  
- Import cookies  
- Evaluate JavaScript  

### ✔ Chrome Remote Debugging
- Tạo session từ địa chỉ:  
  `http://localhost:9222/json/version`

---

# 🧭 Cách sử dụng

## 1. Import client & tools

```python
from kl_mcp_client.client import MCPClient
from kl_mcp_client.tools import MCPTools
```

---

## 2. Tạo kết nối tới MCP Server

```python
mcp = MCPClient(
    base_url="http://localhost:3000/mcp",
    timeout=30,
    retries=2
)
tools = MCPTools(mcp)
```

---

## 3. Tạo session (Chrome Remote)

```python
session = tools.create_session("http://localhost:9222/json/version")
sid = session["sessionId"]
```

---

## 4. Mở URL

```python
tools.open_page(sid, "https://google.com")
```

---

## 5. Screenshot (hiển thị được trong ADK Web)

```python
img = tools.screenshot(sid)
print(img)
```

Trả về:

```json
{
  "type": "image",
  "mimeType": "image/png",
  "data": "<base64>"
}
```

---

## 6. Click & Type

```python
tools.click(sid, "#login")
tools.type(sid, "input[name=q]", "Hello world")
```

---

## 7. Find Elements

```python
tools.find_element(sid, "#content")
tools.find_element_by_text(sid, "Đăng nhập")
tools.find_element_xpath(sid, "//input[@type='email']")
```

---

## 8. Upload File

```python
import base64
data = base64.b64encode(open("test.pdf", "rb").read()).decode()

tools.upload_file(
    sid,
    selector="input[type=file]",
    filename="test.pdf",
    base64Data=data
)
```

---

## 9. Import Cookies

```python
tools.import_cookies(sid, [
    {"name": "token", "value": "abc", "domain": "example.com", "path": "/"}
])
```

---

## 10. Đóng session

```python
tools.close_session(sid)
```

---

# 🧪 Ví dụ đầy đủ

```python
from kl_mcp_client.client import MCPClient
from kl_mcp_client.tools import MCPTools
import base64

mcp = MCPClient("http://localhost:3000/mcp")
tools = MCPTools(mcp)

# Create session
sid = tools.create_session("http://localhost:9222/json/version")["sessionId"]

# Navigate
tools.open_page(sid, "https://google.com")

# Screenshot
img = tools.screenshot(sid)
print("Screenshot returned:", img["mimeType"])

# Search
tools.type(sid, "input[name=q]", "Hello MCP")
tools.click_to_text(sid, "Google Search")

# Close
tools.close_session(sid)
```

---

# 🏗 Kiến trúc

```
Python App / ADK Agent
          ↓
      kl-mcp-client
          ↓
   MCP Browser Server
          ↓
      Chrome / CDP
```

---

# 📘 Yêu cầu

- Python ≥ 3.8  
- MCP Server chạy sẵn (Chromedp backend)
- Chrome/Chromium với cờ:

```
chrome.exe --remote-debugging-port=9222
```

---

# 📝 License

MIT License.

---

# 📚 Liên hệ

Nếu bạn cần:

- MCP Server đầy đủ  
- Hỗ trợ tích hợp ADK Web Agent  
- Thêm tool: DOM Tree, highlight, selector map…  
