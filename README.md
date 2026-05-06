# Cipher 43 Tool — Automation API

API server tự động hóa thao tác trình duyệt. Tích hợp với Genlogin qua **Call API callback** — mỗi khi profile mở xong, Genlogin tự gọi api_server và script chạy ngay, không cần thao tác thủ công.

## Yêu cầu

- Python 3.11+
- `pip install -r requirements.txt`
- Genlogin đang chạy tại `http://127.0.0.1:55550`

## Cấu trúc

```
cipher43-tool/
├── api_server.py        — FastAPI server chính
├── config.json          — Cấu hình local
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

Tạo file `config.json`:

```json
{
  "browser": "genlogin",
  "be_url": "https://cipher-43-lab-be-production.up.railway.app",
  "local_tool_url": "https://your-ngrok-url.ngrok-free.app",
  "tool_token": "c43_xxx",
  "genlogin_username": "your_email@gmail.com",
  "genlogin_password": "your_password"
}
```

- `tool_token` — lấy từ BE dashboard, xác định script nào sẽ chạy
- `browser` — hiện hỗ trợ: `genlogin`, `gologin`, `gpm`

## Khởi chạy

```bash
python api_server.py
```

Server chạy tại `http://127.0.0.1:8000`.

## Flow hoạt động

```
Mở profile trong Genlogin
        ↓
Genlogin tự gọi POST http://127.0.0.1:8000/callback/profile-ready
        ↓
api_server lấy debug port từ Genlogin /running
        ↓
Xác thực tool_token → lấy scriptName từ BE
        ↓
Chạy project/{scriptName}.py với profile đó
```

## Cài đặt Genlogin Call API

Trong mỗi profile settings của Genlogin → **Call API** → điền:

```
http://127.0.0.1:8000/callback/profile-ready
```

Genlogin sẽ tự POST đến đây sau khi profile mở xong.

## API Endpoints

| Endpoint | Mô tả |
|---|---|
| `GET /` | Kiểm tra server online |
| `GET /scripts` | Liệt kê scripts trong `project/` |
| `GET,POST /callback/profile-ready` | Genlogin gọi sau khi profile mở |

## Thêm script mới

Tạo file `.py` trong `project/` với hàm `run(profile_data)`:

```python
def run(profile_data):
    debug_address = profile_data["remote_debugging_address"]  # "127.0.0.1:PORT"
    profile_name  = profile_data["profile_name"]
    # ... thao tác với browser tại debug_address
```

Sau đó cập nhật `scriptName` trong BE dashboard để trỏ đến tên file mới.
