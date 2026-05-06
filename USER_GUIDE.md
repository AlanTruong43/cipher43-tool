# 📖 Cipher 43 Tool — User Guide

**Hướng dẫn sử dụng cho người dùng cuối**

---

## 🎯 Overview

Cipher 43 Tool giúp bạn tự động hóa airdrop farming trên nhiều tài khoản (profiles) cùng lúc.

**Quy trình:**
1. ✅ Cài Tool trên máy
2. ✅ Cấu hình Antidetect Browser
3. ✅ Chuẩn bị Excel file với profile data
4. ✅ Paste Tool Token từ website
5. ✅ Click Run → Tool tự chạy

---

## 📋 Prerequisites

### Yêu cầu hệ thống
- **OS**: Windows, Mac, Linux
- **Python**: 3.11+
- **Antidetect Browser**: GPM Login hoặc GoLogin
- **Internet**: Kết nối ổn định

### Cài đặt

**Option 1: Using launcher (Recommended)**
```bash
# Tải source code từ GitHub
git clone https://github.com/your-repo/cipher43-tool.git
cd cipher43-tool

# Chạy launcher (tự động pull code, install dependencies, start server)
python launcher.py
```

**Option 2: Manual setup**
```bash
# Clone repository
git clone https://github.com/your-repo/cipher43-tool.git
cd cipher43-tool

# Cài dependencies
pip install -r requirements.txt

# Chạy server
python api_server.py
```

Server sẽ chạy tại: **http://127.0.0.1:8000**

---

## ⚙️ Configuration (Setup 1 lần)

### Step 1: Tạo/Edit `config.json`

Tạo file `config.json` trong thư mục cipher43-tool:

```json
{
  "browser": "gpm",
  "be_url": "https://cipher43lab.com"
}
```

**Tùy chọn `browser`:**
- `"gpm"` — GPM Login
- `"gologin"` — GoLogin

**`be_url`**: Địa chỉ website backend (giữ nguyên)

### Step 2: Cấu hình Antidetect Browser

Tùy theo loại antidetect, bạn có thể config Startup URL (optional, nếu muốn tự động):

**GPM Login:**
- Mở Profile Settings
- Tìm "Startup URL" hoặc "Launch URL"
- (Optional) Set: `http://127.0.0.1:8000/register?port={port}&profile_id={profile_id}`

**GoLogin:**
- Tương tự, tìm startup URL setting

---

## 📊 Chuẩn bị Excel File

### Excel Format

Tạo file Excel (.xlsx) với các cột sau. **Hàng đầu là headers**, các hàng dưới là data:

| profile_name | username | password | totp_seed | (custom columns) |
|---|---|---|---|---|
| Account_01 | email1@gmail.com | pass123 | JBSWY3DPEHPK3PXP | ... |
| Account_02 | email2@gmail.com | pass456 | JBSWY3DPEHPK3PXP | ... |

### Cột bắt buộc

| Cột | Mô tả | Ví dụ |
|---|---|---|
| **profile_name** | Tên profile trong antidetect (phải khớp chính xác) | `Account_01` |

### Cột tùy chọn (script có thể dùng)

| Cột | Mô tả | Ví dụ |
|---|---|---|
| username | Email/username | `user@gmail.com` |
| password | Mật khẩu | `SecurePass123` |
| totp_seed | 2FA seed (TOTP) — script tự gen OTP | `JBSWY3DPEHPK3PXP` |
| proxy | Proxy address (nếu cần) | `http://proxy:port` |
| (custom) | Bất kỳ cột nào khác mà script cần | ... |

**Lưu ý:**
- Hàng đầu **bắt buộc** là header row
- Bỏ qua hàng trống
- Column name không quan trọng (normalize thành lowercase_underscore)
- Script chỉ lấy cột nào nó cần

**Ví dụ Excel:**

```
profile_name,username,password,totp_seed
Account_01,user1@gmail.com,Pass123,JBSWY3DPEHPK3PXP
Account_02,user2@gmail.com,Pass456,JBSWY3DPEHPK3PXP
Account_03,user3@gmail.com,Pass789,JBSWY3DPEHPK3PXP
```

---

## 🚀 Cách sử dụng (Step-by-step)

### Workflow

**1. Mở website cipher43lab.com**
```
Đăng nhập tài khoản của bạn
```

**2. Chọn Tool bạn muốn dùng**
```
Tools → Chọn script (Twitter, OKX, v.v.)
```

**3. Copy Tool Token**
```
Nút "Get Token" → Copy token (dạng: c43_xxx...)
```

**4. Mở extension Cipher 43 trong browser**
```
Click icon extension ở top-right trình duyệt
```

**5. Paste Token vào extension**
```
Input field "Tool Token" → Paste token từ website
```

**6. Chọn Excel File**
```
Button "Choose File" → Select file Excel từ máy
```

**7. Chọn Profile (tùy chọn)**
```
Dropdown "Profile" → Chọn 1 profile hoặc "All" để chạy tất cả
```

**8. Click "Run"**
```
Button "Run" → Tool tự động:
  1. Validate token với website
  2. Đọc Excel file
  3. Với mỗi hàng (profile):
     - Lấy debug port từ antidetect
     - Start profile nếu chưa chạy
     - Chạy script automation
```

**9. Xem kết quả**
```
Extension hiển thị:
  ✅ Queued profiles: [Account_01, Account_02, ...]
  ❌ Errors: [...]
```

---

## 📱 Thay thế: Dùng antidetect startup URL (Auto-trigger)

Nếu bạn config Startup URL trong antidetect browser, khi mở profile, nó sẽ tự động:
1. Gọi `/trigger` endpoint của local tool
2. Tool tự động chạy script

**Không cần mở extension hoặc manual trigger.**

---

## 🛠️ Troubleshooting

### ❌ "Tool server không phản hồi"
**Giải pháp:**
- Kiểm tra server có chạy không: `http://127.0.0.1:8000/`
- Nếu không, chạy: `python api_server.py`
- Kiểm tra firewall/antivirus có block port 8000 không

### ❌ "Token không hợp lệ"
**Giải pháp:**
- Token hết hạn? Copy lại từ website
- Subscription hết hạn? Kiểm tra tài khoản
- Token thuộc tool khác? Dùng token đúng

### ❌ "Profile_name không tìm thấy"
**Giải pháp:**
- Kiểm tra tên profile trong Excel khớp chính xác với antidetect browser
- Excel: `Account_01`  ≠  Antidetect: `account 01`
- Kiểm tra lỗi đánh máy

### ❌ "Browser không phản hồi"
**Giải pháp:**
- Kiểm tra antidetect browser có chạy không
- Mở profile vào trước khi chạy tool
- Kiểm tra port browser: `http://127.0.0.1:9222` (hoặc port khác)

### ❌ "Excel file format không được hỗ trợ"
**Giải pháp:**
- File phải là `.xlsx` (Excel) hoặc `.csv`
- Kiểm tra không có macro hoặc file corruption
- Mở trong Excel và save lại

### ❌ "Script lỗi khi chạy"
**Giải pháp:**
- Kiểm tra Excel data đúng format (username, password, totp_seed)
- Kiểm tra browser profile đã login hay chưa
- Xem console output của tool để biết lỗi chi tiết

---

## 📊 Monitoring & Logs

### Xem logs realtime
```bash
# Terminal nơi tool chạy sẽ show:
>>> [SCRIPT_NAME] Connected to 127.0.0.1:9222
>>> [SCRIPT_NAME] Step 1: ...
>>> [SCRIPT_NAME] SUCCESS ...
```

### Logs location
```
~/.cipher43-tool/logs/  (nếu config logging)
```

---

## 🔐 Security Tips

⚠️ **Important:**

1. **Excel file chứa mật khẩu**
   - Lưu ở nơi an toàn, không share
   - Xóa sau khi dùng xong
   - Mã hóa nếu cần (Pro plan)

2. **Tool Token**
   - Copy & paste, không gửi cho ai
   - 1 token = 1 user = 1 tool
   - Revoke trong website nếu bị leak

3. **Local tool chỉ chạy localhost**
   - Không expose ra internet
   - Chỉ website (internal) gọi được

4. **2FA Seeds**
   - Giữ bí mật như password
   - Script chỉ dùng để gen OTP, không upload

---

## 🎓 Advanced Usage

### Customize Excel columns

Script có thể dùng bất kỳ cột nào trong Excel. Dev sẽ quy định cột nào cần.

Ví dụ, script Twitter có thể cần:
```
profile_name, username, password, tweet_text, hashtags
```

Thêm vào Excel:
```
Account_01, user1@gmail.com, pass123, "Hello crypto", "#airdrop #defi"
```

Script sẽ tự động:
```python
tweet_text = profile_data["tweet_text"]
hashtags = profile_data["hashtags"]
```

### Run multiple profiles
```
Excel: 100 profiles
Tool auto: Run 5 song song → chờ xong → run 5 cái tiếp
```

Tốc độ phụ thuộc vào:
- Máy bạn mạnh cỡ nào
- Script phức tạp đến mức nào
- Trung bình: 30 profiles / máy / session

---

## 📞 Support

**Gặp vấn đề?**
1. Kiểm tra Troubleshooting section
2. Xem logs từ console
3. Liên hệ support: support@cipher43lab.com

**Feedback?**
- Submit issue: GitHub issues
- Feature request: discussions

---

## 📚 Các documents liên quan

- [SETUP_GUIDE.md](./SETUP_GUIDE.md) — Dev setup
- [CLAUDE_CONTEXT.md](./CLAUDE_CONTEXT.md) — Tech context
- [README.md](./README.md) — Overview

---

**Version**: 1.0  
**Last Updated**: April 22, 2026  
**Status**: ✅ Production Ready
