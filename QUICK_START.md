# ⚡ QUICK START — Cipher 43 Platform

**5 bước để khởi động & test hệ thống trong 10 phút**

---

## 🚀 Khởi Động Nhanh

### Bước 1: Mở 4 Terminal

```bash
# Terminal 1 - Backend
cd /Users/admin/code/Cipher-43-lab-BE && npm start

# Terminal 2 - Local Tool
cd /Users/admin/code/cipher43-tool && python3 api_server.py

# Terminal 3 - Frontend
cd /Users/admin/code/Cipher-43-Lab-FE && npm run dev

# Terminal 4 - Testing (tuỳ chọn)
# Dùng cho curl commands hoặc monitoring
```

### Bước 2: Verify Mỗi Component

```bash
# Terminal 3 (hoặc browser)
curl http://localhost:3000      # Backend ✓
curl http://127.0.0.1:8000      # Local Tool ✓
curl http://localhost:5173      # Frontend ✓
```

**Expected output:**
- Backend: `{"message":"Chào mừng..."}`
- Local Tool: `{"status":"online"}`
- Frontend: HTML page

---

### Bước 3: Load Extension

1. Mở Chrome/Brave
2. Gõ: `chrome://extensions/` (hoặc `brave://extensions/`)
3. Bật **Developer mode** (top-right)
4. Click **Load unpacked**
5. Chọn: `/Users/admin/code/cipher43-tool/extension/`

✅ Thấy icon "Cipher 43" ở top-right

---

### Bước 4: Test Login & Token

1. Vào: http://localhost:5173
2. **Sign Up** hoặc **Login**
   - Email: `test@example.com`
   - Password: Bất kỳ (8+ ký tự)
3. Vào trang **Tools**
4. Chọn 1 tool → Click **"Get Token"**
5. **Copy token** (dạng `c43_xxxxx`)

---

### Bước 5: Test Extension & Run Script

1. Click icon extension (top-right)
2. **Paste token** vào field
3. Click **"Load"** → Thấy tool name
4. **Select Excel file**: `/Users/admin/code/cipher43-tool/samples/sample-profiles.xlsx`
5. Click **"▶ Chạy"**

**Kết quả:**
- ✅ Extension: `Queued 5 profiles`
- ✅ Terminal 2 (Local Tool): Show script logs
- ✅ Browser: Profiles tự mở

---

## 📊 Tệp Cần Thiết

| Tệp | Vị trí | Mục đích |
|-----|--------|---------|
| Backend | `/Cipher-43-lab-BE` | API server |
| Local Tool | `/cipher43-tool` | Automation engine |
| Frontend | `/Cipher-43-Lab-FE` | Web UI |
| Extension | `/cipher43-tool/extension` | Browser plugin |
| Sample Excel | `/cipher43-tool/samples/sample-profiles.xlsx` | Test data |

---

## 🛠️ Commands Nhanh

```bash
# Backend
cd /Users/admin/code/Cipher-43-lab-BE && npm start

# Local Tool
cd /Users/admin/code/cipher43-tool && python3 api_server.py

# Frontend
cd /Users/admin/code/Cipher-43-Lab-FE && npm run dev

# Test Backend
curl http://localhost:3000

# Test Local Tool
curl http://127.0.0.1:8000

# Create Sample Excel
python3 /Users/admin/code/cipher43-tool/create_sample_excel.py
```

---

## ❓ FAQ

**Q: Cổng 3000/8000/5173 đã được sử dụng?**
```bash
# Tìm process
lsof -i :3000

# Kill process
kill -9 <PID>
```

**Q: Extension không kết nối?**
```
1. Verify local tool running (terminal 2)
2. Check browser console (F12)
3. Verify token valid
4. Try reload extension
```

**Q: Script không chạy?**
```
1. Check antidetect browser mở
2. Check profile_name khớp Excel vs browser
3. Read terminal 2 logs
4. Check excel format
```

**Q: Quên token?**
```
1. Vào trang Tools
2. Click tool tên
3. Copy token mới
```

---

## ✅ Checklist Hoàn Thành

- [ ] Backend chạy on :3000
- [ ] Local Tool chạy on :8000
- [ ] Frontend chạy on :5173
- [ ] Extension loaded trong browser
- [ ] Đã login với account test
- [ ] Đã copy tool token
- [ ] Đã select sample Excel file
- [ ] Đã click "Run" và thấy kết quả

---

## 🎯 Tiếp Theo

✅ **System ready!**

- Đưa cho team test
- Collect feedback
- Fix issues
- Deploy production

---

**Thời gian setup:** ~10 phút  
**Test time:** ~5 phút  
**Total:** ~15 phút

Good luck! 🚀
