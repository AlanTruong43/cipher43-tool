# Cipher 43 Tool — Setup Guide

## ✅ Hoàn thành

### Local Tool (Xeon)
- ✅ API Server chạy tại: http://127.0.0.1:8001
- ✅ Ngrok tunnel: https://violeta-lamprophonic-venially.ngrok-free.dev
- ✅ Config: `C:\Users\admin\Desktop\cipher43-tool\config.json`
  - Browser: genlogin
  - Credentials: cipher43 / Alantruong@113
- ✅ Git auto-pull trước mỗi run
- ✅ Excel reader
- ✅ Endpoints: `/profiles`, `/run`

### Backend (cipher43lab.com)
- ✅ ToolToken model + endpoints
- ✅ Token generation: `POST /api/tool-tokens/generate`
- ✅ Token verification: `POST /api/tool-tokens/verify`
- ✅ Tool verification: `POST /api/tools/verify-token`
- ✅ scriptName field added to Tool model

---

## 🚀 Tiếp theo cần làm (Thủ công)

### 1. Deploy Backend
```bash
cd /Users/admin/code/Cipher-43-lab-BE
git add models/ToolToken.js controllers/ToolController.js routes/tool.js models/Tool.js
git commit -m "feat: tool token system + scriptName field"
git push
```

### 2. Tạo 1 Tool test trên website

**Truy cập BE admin API hoặc database:**

```json
POST /api/tools
{
  "name": "Twitter Check",
  "slug": "twitter-check",
  "description": "Check Twitter login status",
  "scriptName": "twitter",
  "type": "free",
  "features": ["Check login status", "Visual feedback"],
  "apiLocked": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Twitter Check",
    "scriptName": "twitter",
    ...
  }
}
```

### 3. Generate Token từ website

**Login vào website → Dashboard → Tools → "Get Token"**

Hoặc gọi API direct:
```bash
curl -X POST https://cipher43lab.com/api/tool-tokens/generate \
  -H "Authorization: Bearer YOUR_USER_JWT" \
  -H "Content-Type: application/json" \
  -d '{"toolId": 1}'
```

**Response:**
```json
{
  "message": "Token generated successfully",
  "token": "c43_abc123def456...",
  "toolName": "Twitter Check",
  "expiresAt": "2027-04-22T...",
  "startupUrl": "https://cipher43lab.com/trigger?token=c43_...&port={port}"
}
```

### 4. Test API Flow

**Lấy profiles từ genlogin:**
```bash
curl "https://violeta-lamprophonic-venially.ngrok-free.dev/profiles?token=c43_abc123..."
```

**Expected Response:**
```json
{
  "profiles": [
    {"id": "prof_123", "name": "Account_01", "status": "running"},
    {"id": "prof_456", "name": "Account_02", "status": "stopped"}
  ]
}
```

**Chạy script trên multiple profiles từ Excel:**
```bash
curl -X POST https://violeta-lamprophonic-venially.ngrok-free.dev/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_token": "c43_abc123...",
    "script_name": "twitter",
    "excel_path": "C:\\Users\\admin\\Desktop\\profiles.xlsx",
    "extra_params": {}
  }'
```

**Excel file format:**
```
profile_name  | username        | password  | totp_seed
Account_01    | user1@gmail.com | pass123   | JBSWY3DPEHPK3PXP
Account_02    | user2@gmail.com | pass456   | JBSWY3DPEXX3PXP
```

---

## 📋 Checklist

- [ ] BE deployment complete
- [ ] Test Tool created (name: "Twitter Check", scriptName: "twitter")
- [ ] Token generated
- [ ] `/profiles` endpoint working
- [ ] `/run` endpoint chạy successfully
- [ ] Excel reader working
- [ ] Genlogin profiles starting automatically

---

## ❓ Nếu có lỗi

**Token verification failed:**
```
POST /api/tools/verify-token không trả về 200
```
→ Check: token valid? User premium? Tool type?

**Profile not found:**
```
Error: genlogin profile "Account_01" không tìm thấy
```
→ Check: profile name match chính xác?

**Excel reader error:**
```
Lỗi đọc Excel file
```
→ Check: file path đúng? Format columns có tên?

---

## 🔗 API Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/profiles` | GET | token | List profiles từ antidetect |
| `/run` | POST | token | Run script trên multiple profiles từ Excel |
| `/api/tool-tokens/generate` | POST | JWT | Gen token (website) |
| `/api/tool-tokens/verify` | POST | none | Verify token status (website admin) |
| `/api/tools/verify-token` | POST | none | Verify token (from local tool) |

---

Generated: 2026-04-22
