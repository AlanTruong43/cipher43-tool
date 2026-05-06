# 🚀 PRODUCTION DEPLOYMENT GUIDE

**Deploy Cipher 43 Platform lên Production**

- Backend: Railway → https://api.cipher43lab.com
- Frontend: Vercel → https://cipher43lab.com
- Local Tool: Server riêng

---

## 📋 Prerequisites

- [x] Railway account (https://railway.app)
- [x] Vercel account (https://vercel.com)
- [x] Domain cipher43lab.com (với quyền DNS)
- [x] Server riêng cho Local Tool (VPS/Dedicated)
- [x] MongoDB cluster (already setup)
- [x] Git repositories (GitHub)

---

## 🌐 Part 1: Backend Deployment (Railway)

### Step 1: Connect GitHub to Railway

1. Vào https://railway.app
2. Login với GitHub account
3. Click **New Project** → **Deploy from GitHub**
4. Chọn repo: `Cipher-43-lab-BE`
5. Click **Deploy**

### Step 2: Configure Environment Variables

Railway dashboard → Variables tab:

```
PORT=3000
NODE_ENV=production
FRONTEND_URL=https://cipher43lab.com
MONGO_URI=[Your MongoDB Connection String]
JWT_SECRET=[Your JWT Secret]
JWT_REFRESH_SECRET=[Your JWT Refresh Secret]
IMAGEKIT_PUBLIC_KEY=[Your ImageKit Key]
IMAGEKIT_PRIVATE_KEY=[Your ImageKit Private Key]
IMAGEKIT_URL_ENDPOINT=[Your ImageKit URL]
RESEND_API_KEY=[Your Resend API Key]
FROM_NAME=Cipher 43 Lab
FROM_EMAIL=onboarding@resend.dev
LOCAL_TOOL_URL=https://tool.cipher43lab.com:8000
```

**Hoặc:** Copy từ `.env.production` file mà tôi tạo.

### Step 3: Configure Custom Domain

1. Railway → Settings → Domains
2. Click **Generate Domain** hoặc **Add Custom Domain**
3. Nhập: `api.cipher43lab.com`
4. Railway sẽ tạo CNAME record
5. Update DNS settings ở registrar của bạn

```
CNAME: api.cipher43lab.com → [Railway generated domain]
```

### Step 4: Verify Deployment

```bash
curl https://api.cipher43lab.com
# Expected: {"message":"Chào mừng đến với Backend API",...}
```

✅ **Backend deployed!**

---

## 🎨 Part 2: Frontend Deployment (Vercel)

### Step 1: Connect GitHub to Vercel

1. Vào https://vercel.com
2. Login với GitHub account
3. Click **New Project** → **Import**
4. Chọn repo: `Cipher-43-Lab-FE`
5. Click **Import**

### Step 2: Configure Environment Variables

Vercel dashboard → Environment Variables:

```
VITE_BASE_URL=https://api.cipher43lab.com/
SEPAY_MERCHANT_ID=SP-TEST-TV999A94
SEPAY_SECRET_KEY=spsk_test_Bbnih6D5GaJzR7S1wxHptiub2TuWhWQK
```

### Step 3: Configure Custom Domain

1. Vercel → Settings → Domains
2. Click **Add Domain**
3. Nhập: `cipher43lab.com`
4. Vercel sẽ hướng dẫn update DNS
5. Update DNS settings ở registrar

```
A Record: cipher43lab.com → [Vercel IP]
```

Hoặc (recommended):
```
CNAME: www.cipher43lab.com → cname.vercel-dns.com
```

### Step 4: Verify Deployment

```bash
curl https://cipher43lab.com
# Expected: HTML page
```

✅ **Frontend deployed!**

---

## 💻 Part 3: Local Tool Deployment (Your Server)

### Prerequisites

- Ubuntu 20.04+ (hoặc OS khác)
- Python 3.11+
- pip3
- Git
- Nginx hoặc Apache (optional, for reverse proxy)
- SSL certificate (từ Let's Encrypt)

### Step 1: SSH vào Server

```bash
ssh user@your-server-ip
```

### Step 2: Clone Repository

```bash
cd /opt
git clone https://github.com/yourusername/cipher43-tool.git
cd cipher43-tool
```

### Step 3: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python + pip
sudo apt install python3 python3-pip git -y

# Install project dependencies
pip3 install -r requirements.txt

# Install openpyxl for Excel
pip3 install openpyxl
```

### Step 4: Configure Local Tool

Edit `config.json`:

```json
{
    "browser": "gpm",
    "be_url": "https://api.cipher43lab.com",
    "local_tool_url": "https://tool.cipher43lab.com:8000",
    "tool_token": ""
}
```

### Step 5: Setup Systemd Service (Auto-start)

Tạo file service:

```bash
sudo nano /etc/systemd/system/cipher43-tool.service
```

Paste:

```ini
[Unit]
Description=Cipher 43 Tool - Automation Engine
After=network.target

[Service]
Type=simple
User=cipher43
WorkingDirectory=/opt/cipher43-tool
ExecStart=/usr/bin/python3 /opt/cipher43-tool/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Lưu (Ctrl+O, Enter, Ctrl+X)

Enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cipher43-tool
sudo systemctl start cipher43-tool

# Check status
sudo systemctl status cipher43-tool
```

### Step 6: Setup Nginx Reverse Proxy (HTTPS)

```bash
sudo apt install nginx certbot python3-certbot-nginx -y

sudo nano /etc/nginx/sites-available/cipher43-tool
```

Paste:

```nginx
server {
    listen 80;
    server_name tool.cipher43lab.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/cipher43-tool /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Setup HTTPS:

```bash
sudo certbot --nginx -d tool.cipher43lab.com
```

### Step 7: Verify Local Tool

```bash
curl https://tool.cipher43lab.com:8000
# Expected: {"status":"online"}
```

✅ **Local Tool deployed!**

---

## 🧩 Extension Configuration

Update extension popup.js để pointing đúng URLs:

```javascript
const API_BASE_URL = "https://api.cipher43lab.com";
const LOCAL_TOOL_URL = "https://tool.cipher43lab.com:8000";
```

---

## 🔗 DNS Configuration Summary

Thêm vào DNS provider của bạn (GoDaddy, Namecheap, etc.):

```
A Record:
  cipher43lab.com → [Vercel IP hoặc CNAME]

CNAME Records:
  api.cipher43lab.com → [Railway CNAME]
  tool.cipher43lab.com → [Your Server IP hoặc CNAME]
  www.cipher43lab.com → cname.vercel-dns.com (optional)
```

---

## ✅ Final Verification

```bash
# Backend
curl https://api.cipher43lab.com/

# Frontend
curl https://cipher43lab.com

# Local Tool
curl https://tool.cipher43lab.com:8000

# Test login
# Vào https://cipher43lab.com → Login → Get Token → Extension → Run
```

---

## 🚨 Troubleshooting

### ❌ Backend không respond

```bash
# Check Railway logs
railway logs

# Check service status
systemctl status backend-service

# Check MongoDB connection
mongo --version
```

### ❌ Frontend DNS not resolving

```bash
# Check DNS propagation
dig cipher43lab.com
nslookup cipher43lab.com

# Wait 24-48 hours for DNS to propagate
```

### ❌ Local Tool SSL certificate error

```bash
# Renew cert
sudo certbot renew

# Check cert status
sudo certbot certificates
```

### ❌ Extension không kết nối

```bash
# Check CORS headers
curl -I https://api.cipher43lab.com

# Check Local Tool responding
curl https://tool.cipher43lab.com:8000

# Check browser console for errors (F12)
```

---

## 📊 Deployment Checklist

- [ ] Railway account created
- [ ] Vercel account created
- [ ] GitHub repos connected
- [ ] Backend deployed to Railway
- [ ] Backend API responding
- [ ] Frontend deployed to Vercel
- [ ] Frontend website loading
- [ ] Custom domains configured
- [ ] DNS records updated
- [ ] SSL certificates installed
- [ ] Local Tool installed on server
- [ ] Local Tool service running
- [ ] Extension URLs updated
- [ ] Full workflow tested

---

## 🎯 Production URLs

| Component | URL | Status |
|-----------|-----|--------|
| Backend | https://api.cipher43lab.com | ✅ |
| Frontend | https://cipher43lab.com | ✅ |
| Local Tool | https://tool.cipher43lab.com:8000 | ✅ |
| Extension | Installed in browser | ✅ |

---

## 📞 Support

Issues during deployment?
1. Check the troubleshooting section above
2. Read Railway/Vercel documentation
3. Check server logs: `journalctl -u cipher43-tool -f`
4. Contact support team

---

**Deployment Status: ✅ READY**

All systems prepared for production!

Generated: 2026-04-22
Version: 1.0.0 PRODUCTION
