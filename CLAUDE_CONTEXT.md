# 🧠 CLAUDE CONTEXT — Cipher 43 Tool

> Đọc file này trước khi bắt đầu làm việc với dự án.
> Sau khi đọc xong, bạn sẽ hiểu đầy đủ về dự án mà không cần giải thích lại từ đầu.

---

## 1. 🌐 Bối cảnh sản phẩm (Product Context)

**Cipher 43 Lab** là một nền tảng web về **research + tool airdrop crypto**, gồm các tính năng:

| Tính năng | Mô tả |
|---|---|
| Cập nhật nhiệm vụ (Task) | Liên tục cập nhật task mới để farm airdrop kịp thời |
| Thông báo Premium | Tự động push notification khi có cập nhật mới (chỉ Premium) |
| Tool automation | Các tool Free & Premium tự động hóa thao tác trên trình duyệt |
| **API VIP (Multi-account)** | Tính năng mạnh nhất — Premium user gắn API vào antidetect browser để chạy automation trên nhiều tài khoản song song |

**Project `cipher43-tool` chính là phần backend của "API VIP"** — phục vụ người dùng Premium.

---

## 2. 🎯 Mục đích của project này

- Cung cấp **REST API server** để nhận lệnh từ bất kỳ antidetect browser nào
- User chỉ cần truyền **debug port** của browser đang chạy → server tự kết nối và thực thi script
- **Không phụ thuộc vào antidetect browser cụ thể nào** (GPM, AdsPower, Multilogin... đều dùng được)
- Mỗi script = một tác vụ airdrop cụ thể (import ví, tương tác Twitter, v.v.)
- Chạy trên **local machine** của người dùng Premium

---

## 3. 🏗️ Kiến trúc hệ thống

```
[Bất kỳ Antidetect Browser nào]
  (GPM / AdsPower / Multilogin / ...)
         │
         ├─► Extension [Cipher 43 Tool]
         │   └─► Lấy debug port từ browser
         │       Hiển thị trên popup
         │
         │ User copy port vào URL:
         │ http://127.0.0.1:8000/execute/{script}?port={port}
         ▼
[api_server.py] ← FastAPI Server (localhost:8000)
         │
         ├─► Kiểm tra port có sống không (socket check)
         │
         └─► Load & chạy script trong background
               [project/{script}.py]
                      │
                      └─► Kết nối vào browser qua Chrome Remote Debugging Protocol
                          Thực thi automation (DrissionPage)
```

---

## 4. 🛠️ Tech Stack

| Thành phần | Công nghệ |
|---|---|
| API Server | **FastAPI** + Uvicorn |
| Automation engine | **DrissionPage 4.0+** |
| Data Validation | Pydantic |
| Excel reader | **openpyxl** |
| HTTP client | **requests** |
| Python | 3.11+ |
| Browser port | Chrome Extension (Manifest v3) + Antidetect adapter API

---

## 5. 📁 Cấu trúc thư mục

```
cipher43-tool/
├── api_server.py              # FastAPI server chính — nhận & dispatch request
├── config.json                # Cấu hình local: browser type, be_url
├── excel_reader.py            # Đọc file Excel → list profile_data dict
├── git_updater.py             # git pull script mới nhất trước khi chạy
├── requirements.txt           # Dependencies
├── tutorial.txt               # Quy trình & chuẩn code cho AI viết script
├── rule_coding.md             # Quy tắc code
├── README.md                  # Hướng dẫn sử dụng
│
├── adapters/                  # Adapter cho từng antidetect browser
│   ├── base.py                # Abstract class: list_profiles, get_debug_address
│   ├── gpm.py                 # GPM Login adapter
│   └── gologin.py             # GoLogin adapter
│
├── extension/                 # Chrome Extension — cầu nối website ↔ tool
│   ├── manifest.json          # Permissions: tabs, storage
│   ├── background.js          # Port scanner (legacy fallback)
│   ├── popup.html             # UI: nhập token, chọn Excel, trigger run
│   ├── popup.js               # Logic: gọi /tool-info, /run
│   └── icons/                 # Icons
│
└── project/                   # Các script automation (dev viết)
    ├── twitter.py             # Tự động hóa Twitter/X
    ├── import_key_okx.py      # Import seed phrase vào ví OKX
    └── import_key_okx_stealth.py  # Bản stealth OKX dùng Raw CDP
```

---

## 6. ⚡ Cách hoạt động chi tiết

### Luồng xử lý (Token flow — luồng chính):
1. User lấy Tool Token từ cipher43lab.com
2. Paste vào Extension → Extension gọi `GET /tool-info?token=xxx`
3. Server validate token với BE, trả về `toolName`, `scriptName`, danh sách profiles
4. User chọn file Excel → Click Run → Extension gọi `POST /run`
5. Tool validate token, git pull code mới nhất, đọc Excel
6. Với mỗi hàng: lấy debug port qua antidetect adapter → chạy script

### Luồng legacy (trực tiếp bằng port):
1. User lấy debug port từ extension hoặc antidetect UI
2. Gọi `GET /execute/{script}?port=9222`
3. Server kết nối browser và chạy script

### Cấu trúc `profile_data` dict truyền vào script:
```python
{
    "remote_debugging_address": "127.0.0.1:9222",  # luôn có
    "profile_name": "Account_01",                   # từ Excel
    "username": "email@gmail.com",                  # từ Excel (nếu có)
    "password": "xxx",                              # từ Excel (nếu có)
    "totp_seed": "JBSWY3...",                       # từ Excel (nếu có)
    # + mọi cột khác trong Excel được forward vào đây
}
```

### Endpoints:
```
GET  /tool-info?token={tool_token}   — validate + trả về tool info + profiles
POST /run                            — đọc Excel + chạy script cho nhiều profile
GET  /execute/{script}?port={port}   — legacy: chạy script với port cụ thể
POST /execute/{script}               — legacy: chạy script với body JSON
GET  /scripts                        — liệt kê scripts có trong project/
GET  /profiles                       — liệt kê profiles từ antidetect
```

---

## 7. 📝 Chuẩn khi viết script mới

Mọi script trong `project/` đều phải:
- Định nghĩa hàm `def run(profile_data):` làm entry point
- Kết nối bằng DrissionPage qua debug port (không mở browser mới)
- Dùng prefix log `>>> [TÊN_SCRIPT]` để dễ trace
- Scan `page.get_tabs()` để chọn tab thực tế, bỏ qua tab extension
- Có try/except/finally đầy đủ

Chi tiết xem thêm: `tutorial.txt` và `rule_coding.md`

---

## 8. 🔄 DrissionPage — Cú pháp chuẩn

### Kết nối browser
```python
from DrissionPage import ChromiumPage, ChromiumOptions
co = ChromiumOptions().set_address("127.0.0.1:9222")
page = ChromiumPage(co)
```

### Tìm & tương tác element
```python
el = page.ele('xpath://button[@id="submit"]', timeout=10)  # None nếu không thấy
el = page.ele('css:button.submit', timeout=10)
el = page.ele('text:Xác nhận', timeout=10)
els = page.eles('xpath://input')                           # Tìm nhiều
el.click()
el.input("nội dung", clear=True)
page.run_js("arguments[0].click();", el)                   # JS click fallback
```

### Quản lý tab
```python
for tab in page.get_tabs():
    if not tab.url.startswith("chrome-extension://"):
        page.activate_tab(tab)
        break
page.new_tab("https://example.com")
```

### Điều hướng & JS
```python
page.get("https://example.com")
page.run_js("window.scrollTo(0, 500);")
result = page.run_js("return document.title;")
```

---

## 9. 🔒 Bảo mật (lưu ý)

- API **không có authentication** → chỉ dùng local/mạng nội bộ
- Dữ liệu nhạy cảm (mnemonic, password) nên truyền qua **POST body**, không qua GET query string

---

## 10. 🚀 Trạng thái dự án hiện tại

- ✅ Chạy được trên local
- ✅ Đã migrate sang **DrissionPage** (bỏ Selenium)
- ✅ **Browser-agnostic** — không phụ thuộc antidetect browser cụ thể nào
- ✅ Chrome Extension để lấy debug port
- ✅ API endpoint: `http://127.0.0.1:8000/execute/{script}?port={port}`
- 📋 Cần viết thêm scripts cho các airdrop project mới

---

## 11. 🎯 Plan hiện tại

**Sử dụng GET API call model:**
```
Extension → lấy port → user copy port → user tự thay vào URL
→ gọi http://127.0.0.1:8000/execute/{script}?port={port}
→ API kết nối browser → chạy script
```

User không cần biết code, chỉ cần:
1. Cài extension Cipher 43
2. Mở profile trong antidetect browser
3. Click popup → copy port
4. Gọi URL hoặc dùng startup script của antidetect browser

---

*File này được tạo để giúp AI (Claude) nhanh chóng hiểu context dự án khi bắt đầu conversation mới.*
*Cập nhật lần cuối: 2026-03-17*
