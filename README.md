# Cipher 43 Tool — Automation API

FastAPI server chạy trên **máy Windows local**, tự động chạy script automation khi profile Antidetect browser mở. Tích hợp qua tính năng **Call API** có sẵn trong antidetect browser — không cần Extension.

## Yêu cầu

- Python 3.11+
- `pip install -r requirements.txt`
- Antidetect browser đang chạy (GenLogin: `127.0.0.1:55550`, GPMLogin Global: `127.0.0.1:9495`)

## Cấu trúc

```
cipher43-tool/
├── api_server.py        — FastAPI server chính
├── config.json          — Cấu hình local (không commit)
├── adapters/            — Adapter cho từng antidetect browser
│   ├── base.py
│   ├── genlogin.py
│   ├── gologin.py
│   └── gpm.py
└── project/             — Script automation
    ├── encoding_fix.py  — Windows UTF-8 fix (import tự động)
    ├── twitter.py
    └── ...              — Thêm script mới tại đây
```

## Cấu hình

Tạo file `config.json` (không commit vào git):

```json
{
  "browser": "genlogin",
  "be_url": "https://cipher-43-lab-be-production.up.railway.app",
  "tool_token": "c43_xxx",
  "user_email": "your_gmail@gmail.com",
  "genlogin_username": "your_email@gmail.com",
  "genlogin_password": "your_password"
}
```

- `tool_token` — lấy từ web dashboard (nút **Lấy Token** trong trang Tool), xác định script nào sẽ chạy
- `user_email` — gmail đã đăng ký tài khoản trên web, dùng để xác minh quyền truy cập
- `browser` — hiện hỗ trợ: `genlogin`, `gologin`, `gpm`, `gpmglobal`

## Khởi chạy

```bash
python api_server.py
```

Server chạy tại `http://127.0.0.1:8000`.

## Flow hoạt động

```
User mở profile trong Antidetect browser
        ↓
Browser tự gọi POST http://127.0.0.1:8000/callback/profile-ready
        ↓
api_server query /running → lấy debug port của profile
        ↓
Xác thực tool_token + user_email → lấy scriptName từ BE
        ↓
Chạy project/{scriptName}.py với profile đó
```

Nếu browser không gửi data trong callback (payload rỗng), api_server tự fallback query endpoint `/running` để lấy tất cả profiles đang mở.

## Cài đặt Call API trong Antidetect browser

Vào settings từng profile → **Call API** → điền:

```
http://127.0.0.1:8000/callback/profile-ready
```

Browser sẽ tự POST đến đây sau khi profile mở xong.

## API Endpoints

| Endpoint | Mô tả |
|---|---|
| `GET /` | Kiểm tra server online |
| `GET /scripts` | Liệt kê scripts trong `project/` |
| `GET,POST /callback/profile-ready` | Browser gọi sau khi profile mở (GenLogin, GoLogin, GPM) |
| `POST /run-profile` | FE gọi để start profile và chạy script (GPMLogin Global) |
| `GET /status` | Trạng thái tất cả tasks đang/đã chạy |
| `GET /status/{profile_name}` | Trạng thái task của một profile |
| `GET /status/stream/{profile_name}` | SSE stream log realtime của profile |
| `DELETE /status` | Xóa các task đã hoàn thành (giữ lại `running`) |

## Thêm script mới

1. Tạo file `.py` trong `project/` với hàm `run(profile_data)`:

```python
def run(profile_data):
    debug_address = profile_data["remote_debugging_address"]  # "127.0.0.1:PORT"
    profile_name  = profile_data["profile_name"]
    # ... thao tác với browser tại debug_address
```

2. Vào web dashboard → Admin → Tool → thêm tên file (không có `.py`) vào field **scriptNames**

3. User tạo lại token trên web để chọn script mới

## Chạy persistent trên Windows (qua SSH)

Server được khởi chạy qua Windows Task Scheduler để giữ process sau khi đóng SSH:

```
Task name: cipher43-tool
Location:  C:\Users\admin\Desktop\cipher43-tool\
Bat file:  start_api_server.bat
```

Để restart: `schtasks /run /tn cipher43-tool`
