# 🚀 Cipher 43 Tool — Automation API

API server tự động hóa thao tác trình duyệt cho airdrop farming.
Tương thích với **mọi antidetect browser** hỗ trợ Chrome Remote Debugging Protocol.

## 🛠 Yêu cầu hệ thống
- Python 3.11+
- `pip install -r requirements.txt`
- File `config.json` (xem mục cấu hình)

## 📁 Cấu trúc

```
cipher43-tool/
├── api_server.py        — FastAPI server chính
├── config.json          — Cấu hình local (browser type, BE URL)
├── excel_reader.py      — Đọc file Excel thành list profile_data
├── git_updater.py       — git pull script mới nhất trước khi chạy
│
├── adapters/            — Adapter cho từng antidetect browser
│   ├── base.py          — Abstract class
│   ├── gpm.py           — GPM Login
│   ├── gologin.py       — GoLogin
│   └── genlogin.py      — Genlogin
│
├── project/             — Script automation (dev viết)
│   ├── twitter.py
│   └── import_key_okx.py
│
└── extension/           — Chrome Extension lấy debug port
    ├── manifest.json
    ├── background.js
    ├── popup.html
    └── popup.js
```

## ⚙️ Cấu hình

Tạo file `config.json` tại thư mục gốc:

### Cho GPM Login
```json
{
  "browser": "gpm",
  "be_url": "https://cipher43lab.com"
}
```

### Cho GoLogin (Orbital Agent)
```json
{
  "browser": "gologin",
  "be_url": "https://cipher43lab.com"
}
```

### Cho Genlogin
```json
{
  "browser": "genlogin",
  "genlogin_username": "your_email@gmail.com",
  "genlogin_password": "your_password",
  "be_url": "https://cipher43lab.com"
}
```

**Hỗ trợ browsers**: `gpm`, `gologin`, `genlogin`

## 🚀 Khởi chạy Server

```bash
python api_server.py
```
Server chạy tại: `http://127.0.0.1:8000`

## 📡 API Endpoints

### `GET /tool-info?token={tool_token}`
Validate token + trả về tên tool, scriptName, danh sách profiles.
Extension gọi sau khi user paste token.

```json
{
  "toolName": "Twitter Checker",
  "scriptName": "twitter",
  "profiles": [{ "id": "abc", "name": "Account_01" }]
}
```

### `POST /run`
Đọc Excel, lấy debug port từng profile, chạy script song song.

```json
{
  "tool_token": "c43_xxx",
  "excel_path": "C:/Users/abc/accounts.xlsx",
  "extra_params": {}
}
```

### `GET /execute/{script}?port={debug_port}` *(legacy)*
Chạy script trực tiếp với port cụ thể (không cần token).

### `GET /scripts`
Liệt kê scripts có trong `project/`.

## 🧠 Luồng xử lý (Token flow)

1. User lấy **Tool Token** từ cipher43lab.com
2. Paste vào Extension → Extension gọi `/tool-info` để validate
3. Extension đọc file Excel từ máy user
4. Click Run → Extension gọi `/run` với token + đường dẫn Excel
5. Tool xác thực token với BE, đọc Excel, lấy debug port từng profile → chạy script

## 📝 Thêm script mới
Tạo file `.py` trong `project/` với hàm `run(profile_data)`.
Xem `tutorial.txt` để biết cấu trúc chuẩn.
