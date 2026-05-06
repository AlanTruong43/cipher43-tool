# 🚀 CIPHER 43 PLATFORM — PRODUCTION DEPLOYMENT

**Complete Guide to Deploy Everything**

Status: ✅ **READY TO DEPLOY**  
Date: 2026-04-22  
Version: 1.0.0 Production

---

## 📋 What You'll Deploy

```
┌─────────────────────────────────────────────┐
│     CIPHER 43 PLATFORM (Production)         │
├─────────────────────────────────────────────┤
│ Frontend:  https://cipher43lab.com          │
│ Backend:   https://api.cipher43lab.com      │
│ Tool:      https://tool.cipher43lab.com     │
│ Extension: Installed in browser             │
└─────────────────────────────────────────────┘
```

---

## ⏱️ Timeline

| Step | Component | Platform | Time | Status |
|------|-----------|----------|------|--------|
| 1 | Backend | Railway | 10min | 📝 |
| 2 | Frontend | Vercel | 10min | 📝 |
| 3 | Local Tool | Your Server | 20min | 📝 |
| 4 | DNS Setup | Registrar | varies | 📝 |
| 5 | Testing | All | 10min | 📝 |
| **Total** | - | - | **~1 hour** | - |

---

## 🔑 Prerequisites

### 1. Accounts (Create if needed)

```
☐ Railway Account: https://railway.app
☐ Vercel Account: https://vercel.com
☐ GitHub Account: https://github.com
```

### 2. Domain

```
☐ cipher43lab.com (already owned)
☐ DNS access (at registrar)
```

### 3. Server

```
☐ Ubuntu 20.04+ server (IP: your-server-ip)
☐ SSH access
☐ Python 3.11+ installed
```

### 4. Code

```
☐ Cipher-43-lab-BE (GitHub)
☐ Cipher-43-Lab-FE (GitHub)
☐ cipher43-tool (GitHub)
```

---

## 🎬 STEP 1: Backend Deployment (Railway) — 10 minutes

### 1.1 Connect to Railway

```
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose: Cipher-43-lab-BE
6. Click "Deploy"
```

✅ **Railway connected**

### 1.2 Set Environment Variables

Railway → Project → Variables tab

**Add these variables:**

```
PORT=3000
NODE_ENV=production
FRONTEND_URL=https://cipher43lab.com
MONGO_URI=mongodb+srv://admin:Alantruong%40113@cluster0.2y3quz3.mongodb.net/cipher43?appName=Cluster0
JWT_SECRET=c1ph3r43_jwt_@cc3ss_s3cr3t_k3y_2026!xZ9
JWT_REFRESH_SECRET=c1ph3r43_jwt_r3fr3sh_s3cr3t_k3y_2026!mK7
IMAGEKIT_PUBLIC_KEY=public_k1SoxOoPzQi/vdlLrXQppiar0uc=
IMAGEKIT_PRIVATE_KEY=private_yg58RxycTYS/zXa20JRPTT7wBVg=
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/md7h2eu1h
RESEND_API_KEY=re_jkjBFMN3_MXYhF9q5ZwC8CZX5yHuH4PEU
FROM_NAME=Cipher 43 Lab
FROM_EMAIL=onboarding@resend.dev
LOCAL_TOOL_URL=https://tool.cipher43lab.com:8000
```

✅ **Variables set**

### 1.3 Configure Custom Domain

```
1. Railway → Settings → Domains
2. Click "Add Custom Domain"
3. Enter: api.cipher43lab.com
4. Railway generates CNAME record
5. Copy the CNAME value (something like: railway.app)
```

✅ **Domain configured**

### 1.4 Update DNS at Registrar

**At your domain registrar (GoDaddy, Namecheap, etc.):**

```
Add CNAME Record:
  Host: api
  Value: [CNAME from Railway]
  TTL: 3600
```

✅ **DNS updated (wait 5-15 minutes)**

### 1.5 Verify Backend

```bash
# Wait a few minutes for DNS propagation
curl https://api.cipher43lab.com

# Expected response:
# {"message":"Chào mừng đến với Backend API","version":"1.0.0","status":"running"}
```

✅ **Backend LIVE!**

---

## 🎨 STEP 2: Frontend Deployment (Vercel) — 10 minutes

### 2.1 Connect to Vercel

```
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New..." → "Project"
4. Select: Cipher-43-Lab-FE
5. Click "Import"
```

✅ **Vercel connected**

### 2.2 Set Environment Variables

Vercel → Project Settings → Environment Variables

```
VITE_BASE_URL=https://api.cipher43lab.com/
SEPAY_MERCHANT_ID=SP-TEST-TV999A94
SEPAY_SECRET_KEY=spsk_test_Bbnih6D5GaJzR7S1wxHptiub2TuWhWQK
```

✅ **Variables set**

### 2.3 Configure Custom Domain

```
1. Vercel → Settings → Domains
2. Click "Add Domain"
3. Enter: cipher43lab.com
4. Vercel shows DNS records
```

✅ **Domain info received**

### 2.4 Update DNS at Registrar

**At your domain registrar:**

**Option A - CNAME (Recommended):**
```
Add CNAME Record:
  Host: www
  Value: cname.vercel-dns.com
  TTL: 3600
```

**Option B - A Record:**
```
Add A Record:
  Host: @
  Value: [Vercel IP provided]
  TTL: 3600
```

✅ **DNS updated**

### 2.5 Verify Frontend

```bash
# Wait 5-15 minutes for DNS
curl https://cipher43lab.com

# Expected: HTML page content
```

✅ **Frontend LIVE!**

---

## 💻 STEP 3: Local Tool Deployment (Your Server) — 20 minutes

### 3.1 SSH into Server

```bash
ssh user@your-server-ip

# Or with key:
ssh -i /path/to/key.pem user@your-server-ip
```

### 3.2 Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Nginx, Certbot
sudo apt install python3 python3-pip nginx certbot python3-certbot-nginx git -y

# Verify
python3 --version    # Should be 3.11+
```

### 3.3 Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/cipher43-tool.git
sudo chown -R $USER:$USER cipher43-tool
cd cipher43-tool
```

### 3.4 Install Python Packages

```bash
pip3 install -r requirements.txt
pip3 install openpyxl uvicorn gunicorn
```

### 3.5 Configure Local Tool

```bash
# Edit config.json
nano config.json

# Content should be:
{
    "browser": "gpm",
    "be_url": "https://api.cipher43lab.com",
    "local_tool_url": "https://tool.cipher43lab.com:8000",
    "tool_token": ""
}

# Save: Ctrl+O, Enter, Ctrl+X
```

### 3.6 Test Locally

```bash
cd /opt/cipher43-tool
python3 api_server.py

# Expected:
# INFO:     Uvicorn running on http://127.0.0.1:8000

# In another terminal:
curl http://localhost:8000
# Expected: {"status":"online"}

# Press Ctrl+C to stop
```

✅ **Local test passed**

### 3.7 Setup Nginx

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/cipher43-tool
```

Paste:

```nginx
upstream cipher43_tool {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name tool.cipher43lab.com;

    location / {
        proxy_pass http://cipher43_tool;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
}
```

**Save: Ctrl+O, Enter, Ctrl+X**

### 3.8 Enable Nginx

```bash
# Enable config
sudo ln -s /etc/nginx/sites-available/cipher43-tool /etc/nginx/sites-enabled/

# Test
sudo nginx -t
# Expected: syntax is ok, test is successful

# Restart
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 3.9 Setup SSL

```bash
# Generate certificate
sudo certbot --nginx -d tool.cipher43lab.com

# Follow prompts:
# - Enter email
# - Accept terms
# - Choose: 2 (redirect HTTP to HTTPS)
```

✅ **HTTPS configured**

### 3.10 Create Systemd Service

```bash
sudo nano /etc/systemd/system/cipher43-tool.service
```

Paste:

```ini
[Unit]
Description=Cipher 43 Tool
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/cipher43-tool
ExecStart=/usr/bin/python3 /opt/cipher43-tool/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save: Ctrl+O, Enter, Ctrl+X**

### 3.11 Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable cipher43-tool
sudo systemctl start cipher43-tool

# Check status
sudo systemctl status cipher43-tool

# View logs
sudo journalctl -u cipher43-tool -f
```

✅ **Service running**

### 3.12 Update DNS

**At your registrar, add:**

```
CNAME Record:
  Host: tool
  Value: your-server-domain-or-ip
  TTL: 3600
```

Or use A record:
```
A Record:
  Host: tool
  Value: your-server-ip
  TTL: 3600
```

✅ **DNS updated**

### 3.13 Verify Local Tool

```bash
# Wait 5-15 minutes for DNS
curl https://tool.cipher43lab.com:8000

# Expected: {"status":"online"}
```

✅ **Local Tool LIVE!**

---

## 🔗 STEP 4: DNS Final Setup

### All DNS Records Needed

At your domain registrar, ensure these records exist:

```
A/CNAME Records:
  @                    → cipher43lab.com (Vercel)
  api                  → api.cipher43lab.com (Railway)
  tool                 → tool.cipher43lab.com (Your Server)
  www (optional)       → www.cipher43lab.com (cname.vercel-dns.com)
```

### Verify DNS Propagation

```bash
# Check each domain
dig cipher43lab.com
dig api.cipher43lab.com
dig tool.cipher43lab.com

# Should show IP/CNAME values
```

✅ **DNS ready**

---

## 🧪 STEP 5: Full Testing — 10 minutes

### 5.1 Test Backend

```bash
curl https://api.cipher43lab.com
# Expected: Backend response

curl https://api.cipher43lab.com/scripts
# Expected: {"scripts": [...]}
```

### 5.2 Test Frontend

```bash
# Open browser
curl https://cipher43lab.com
# Expected: HTML page content
```

### 5.3 Test Local Tool

```bash
curl https://tool.cipher43lab.com:8000
# Expected: {"status":"online"}

curl https://tool.cipher43lab.com:8000/tool-info
# Expected: Tool info
```

### 5.4 Test Full Workflow

1. **Open browser:** https://cipher43lab.com
2. **Sign up / Login**
3. **Go to Tools page**
4. **Click Get Token** → Copy token
5. **Open Extension** → Paste token
6. **Click Load** → Should show profiles
7. **Select Excel file** → `/cipher43-tool/samples/sample-profiles.xlsx`
8. **Click Run** → Should start automation

✅ **Full workflow working!**

---

## ✅ Final Verification Checklist

- [ ] Backend API responding at https://api.cipher43lab.com
- [ ] Frontend website loading at https://cipher43lab.com
- [ ] Local Tool responding at https://tool.cipher43lab.com:8000
- [ ] Can login to website
- [ ] Can generate tool token
- [ ] Can load token in extension
- [ ] Can select profiles
- [ ] Can run automation script
- [ ] DNS records all correct
- [ ] SSL certificates valid
- [ ] All services auto-restart enabled

---

## 📊 Deployment Summary

| Component | URL | Platform | Status |
|-----------|-----|----------|--------|
| Backend | https://api.cipher43lab.com | Railway | ✅ |
| Frontend | https://cipher43lab.com | Vercel | ✅ |
| Local Tool | https://tool.cipher43lab.com | Server | ✅ |
| Extension | - | Browser | ✅ |
| Database | MongoDB | Cloud | ✅ |

---

## 🎯 Production System LIVE! 🎉

Congratulations! Your Cipher 43 platform is now live!

### What's Running

✅ **Production Backend** - https://api.cipher43lab.com  
✅ **Production Frontend** - https://cipher43lab.com  
✅ **Production Local Tool** - https://tool.cipher43lab.com  
✅ **Extension** - Ready to use  
✅ **Database** - MongoDB connected  
✅ **Monitoring** - Systemd auto-restart  

### Next Steps

1. **Invite early users** to test
2. **Monitor logs** - `sudo journalctl -u cipher43-tool -f`
3. **Collect feedback**
4. **Fix issues** as they arise
5. **Scale infrastructure** as needed

### Useful Commands

```bash
# Check service status
sudo systemctl status cipher43-tool

# View logs
sudo journalctl -u cipher43-tool -f

# Restart service
sudo systemctl restart cipher43-tool

# Update code
cd /opt/cipher43-tool && git pull && sudo systemctl restart cipher43-tool
```

---

## 📞 Support

Need help?

1. Read: [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
2. Read: [LOCAL_TOOL_SERVER_SETUP.md](./LOCAL_TOOL_SERVER_SETUP.md)
3. Check logs: `sudo journalctl -u cipher43-tool -f`
4. Test APIs: `curl https://api.cipher43lab.com`

---

**Deployment Complete!** ✅

Your Cipher 43 Platform is production-ready and live!

Generated: 2026-04-22  
Version: 1.0.0 PRODUCTION  
Status: ✅ READY FOR USERS
