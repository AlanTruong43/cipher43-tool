# 🚀 Cipher 43 Tool — Automation API

API server tự động hóa thao tác trình duyệt cho airdrop farming.
Tương thích với **mọi antidetect browser** hỗ trợ Chrome Remote Debugging Protocol.

## 🛠 Yêu cầu hệ thống
- Python 3.11+
- `pip install -r requirements.txt`
- Browser đang chạy với Remote Debugging được bật

## 📁 Cấu trúc
- `api_server.py` — FastAPI server chính
- `project/` — Chứa các script automation
- `example_code.py` — Template để tạo script mới
- `tutorial.txt` — Chuẩn code cho AI

## 🚀 Khởi chạy Server

```bash
python api_server.py
```
Server chạy tại: `http://127.0.0.1:8000`

## 📡 Cách gọi API

### GET (thông thường)
```
http://127.0.0.1:8000/execute/{tên_script}?port={debug_port}
```

**Ví dụ:**
```
http://127.0.0.1:8000/execute/twitter?port=9222
http://127.0.0.1:8000/execute/import_key_okx?port=9222&mnemonic=word1+word2&password=abc
```

### POST (dữ liệu nhạy cảm)
```
POST http://127.0.0.1:8000/execute/{tên_script}
Body: { "remote_debugging_address": "127.0.0.1:9222" }
```

## 🧠 Luồng xử lý
1. Lấy **debug port** từ antidetect browser của bạn (GPM, AdsPower, Multilogin...)
2. Gọi API với port đó
3. Server kết nối vào browser và chạy script tự động

## 📝 Thêm script mới
Tạo file `.py` trong thư mục `project/` với hàm `run(profile_data)`.
Xem `example_code.py` và `tutorial.txt` để biết cấu trúc chuẩn.
