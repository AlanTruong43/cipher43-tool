# 🚀 DEPLOYMENT GUIDE — Cipher 43 Platform

**Hướng dẫn khởi động toàn bộ hệ thống để đưa user sử dụng**

---

## 📋 Checklist Trước Khi Khởi Động

- ✅ Backend (Node.js 24.15.0) - chuẩn bị
- ✅ Local Tool (Python 3.14.4) - chuẩn bị
- ✅ Frontend (Vue.js) - chuẩn bị
- ✅ Extension - chuẩn bị
- ✅ Database (MongoDB) - đã connected
- ✅ Configuration - sẵn sàng

---

## 🎬 Khởi Động Hệ Thống (4 Terminals)

### Terminal 1️⃣: Backend (Node.js)

```bash
cd /Users/admin/code/Cipher-43-lab-BE
npm start
```

**Expected output:**
```
🚀 Server đang chạy tại http://localhost:3000
📝 Environment: development
🗄 MongoDB Connected: ...
```

✅ **Verify:** Truy cập http://localhost:3000 → thấy JSON response

---

### Terminal 2️⃣: Local Tool (Python)

```bash
cd /Users/admin/code/cipher43-tool
python3 api_server.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ **Verify:** Truy cập http://127.0.0.1:8000 → thấy `{"status":"online"}`

---

### Terminal 3️⃣: Frontend (Vue.js)

```bash
cd /Users/admin/code/Cipher-43-Lab-FE
npm run dev
```

**Expected output:**
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to access from network
```

✅ **Verify:** Truy cập http://localhost:5173 → thấy website

---

### Terminal 4️⃣: (Optional) Monitoring / Testing

```bash
# Xem logs, run curl commands, etc.
curl http://localhost:3000
curl http://127.0.0.1:8000
```

---

## 🔧 Extension Setup

### Step 1: Open Chrome/Brave
```
Mở antidetect browser hoặc Chrome bình thường
```

### Step 2: Load Extension
```
1. Chrome menu → More tools → Extensions
2. Toggle "Developer mode" (top-right)
3. Click "Load unpacked"
4. Select: /Users/admin/code/cipher43-tool/extension/
```

### Step 3: Verify Extension Loaded
```
Extension icon sẽ xuất hiện ở top-right
Click icon → thấy Cipher 43 Tool popup
```

---

## 🧪 Test Workflow (End-to-End)

### Test 1: Đăng Ký / Đăng Nhập

1. Truy cập http://localhost:5173
2. Click "Sign Up" hoặc "Login"
3. Tạo tài khoản test hoặc dùng existing account
4. **Lưu JWT token** (từ localStorage hoặc dev tools)

```javascript
// F12 → Console:
localStorage.getItem('token')  // Copy token này
```

### Test 2: Lấy Tool Token

1. Login xong, vào trang **Tools**
2. Chọn 1 tool (ví dụ: Twitter)
3. Click **"Get Token"** button
4. Copy token (dạng: `c43_xxxxxxxxxxxxx`)

### Test 3: Dùng Extension

1. Mở extension popup (click icon)
2. Paste tool token vào field "Tool Token"
3. Click **"Load"** button
4. Extension sẽ:
   - Validate token
   - Show tool name + script
   - List profiles từ antidetect

### Test 4: Upload Excel & Run

1. Click **"Choose File"** → Select `sample-profiles.xlsx`
2. (Optional) Chọn profile từ dropdown hoặc "All profiles"
3. Click **"▶ Chạy"** button
4. Extension sẽ:
   - Gửi request đến local tool (port 8000)
   - Automation script chạy background
   - Show status: "Queued X profiles"

### Test 5: Verify Results

1. Check **Terminal 2** (Local Tool) → log output
2. Check browser tabs → có mở profile không?
3. Check script kết quả (ví dụ: Twitter posted, OKX wallet created)

---

## 📊 File Cần Thiết

### 1. Excel Sample File
```
File: sample-profiles.xlsx
Location: /Users/admin/code/cipher43-tool/samples/

Cột:
- profile_name (required)
- username (optional)
- password (optional)
- totp_seed (optional)
- custom columns (as needed)
```

### 2. Config Files
```
Backend:    /Users/admin/code/Cipher-43-lab-BE/.env
Local Tool: /Users/admin/code/cipher43-tool/config.json
Frontend:   /Users/admin/code/Cipher-43-Lab-FE/.env
```

### 3. Environment Variables (if needed)
```bash
# Backend .env
JWT_SECRET=your_secret_key
MONGODB_URI=mongodb+srv://...
BE_URL=http://localhost:3000

# Local Tool config.json
{
  "browser": "gpm",
  "be_url": "http://localhost:3000"
}

# Frontend .env
VITE_API_URL=http://localhost:3000
```

---

## ✅ Verification Checklist

| Item | Check | Status |
|------|-------|--------|
| Backend running on :3000 | curl http://localhost:3000 | ✅ |
| Local tool running on :8000 | curl http://127.0.0.1:8000 | ✅ |
| Frontend running on :5173 | Visit in browser | ✅ |
| Extension loaded | Icon visible | ✅ |
| MongoDB connected | Check backend logs | ✅ |
| Can login | Create/login account | ✅ |
| Can generate token | Tool page → get token | ✅ |
| Can validate token | Extension load token | ✅ |
| Can run script | Extension → Run | ✅ |
| Script executes | Check logs/results | ✅ |

---

## 🚨 Troubleshooting

### ❌ Port already in use
```bash
# Find process using port
lsof -i :3000    # Backend
lsof -i :8000    # Local Tool
lsof -i :5173    # Frontend

# Kill process
kill -9 <PID>
```

### ❌ Extension not connecting to tool
```
1. Check local tool is running (terminal 2)
2. Check config.json has correct "be_url"
3. Check browser network tab for failed requests
4. Try: curl http://127.0.0.1:8000/tool-info?token=test
```

### ❌ Token validation fails
```
1. Verify token not expired
2. Check backend /verify-token endpoint working
3. Check network connectivity
4. Try generating new token
```

### ❌ Script not running
```
1. Check antidetect browser is open
2. Check profile_name in Excel matches browser
3. Check local tool logs (terminal 2)
4. Check excel file format correct
5. Try manual: curl -X POST http://127.0.0.1:8000/run ...
```

---

## 📞 Support

**Issues?**
1. Check logs từ 4 terminals
2. Read USER_GUIDE.md
3. Check QUICK_START.md
4. Contact: support@cipher43lab.com

---

## 🎯 Next Steps for User Adoption

1. **Create demo video** - show full workflow
2. **Setup production servers** - buy/configure hosting
3. **Add more tools** - more automation scripts
4. **Improve security** - rate limiting, auth enhancement
5. **Scale infrastructure** - CDN, load balancer, etc.

---

**System Status: ✅ READY FOR DEPLOYMENT**

Generated: 2026-04-22  
Version: 1.0.0
