# 📡 LOCAL TOOL SERVER SETUP GUIDE

**Hướng dẫn setup Cipher 43 Tool trên máy server của bạn**

---

## 📋 Yêu Cầu

- **OS:** Ubuntu 20.04+ (hoặc CentOS, Debian, macOS)
- **Python:** 3.11+
- **Storage:** 2GB free space
- **Network:** Port 8000 accessible
- **Git:** Để clone repository
- **SSL:** Let's Encrypt certificate (optional nhưng recommended)

---

## 🚀 Cài Đặt Nhanh (10 phút)

### Step 1: SSH vào Server

```bash
ssh user@your-server-ip
# Hoặc nếu dùng key:
ssh -i /path/to/key.pem user@your-server-ip
```

### Step 2: Clone Repository

```bash
# Navigate đến /opt (hoặc /home/user/apps)
cd /opt

# Clone cipher43-tool
git clone https://github.com/yourusername/cipher43-tool.git
cd cipher43-tool

# Hoặc nếu là private repo
git clone https://your-token@github.com/yourusername/cipher43-tool.git
```

### Step 3: Install Dependencies

```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python + pip + Git
sudo apt install python3 python3-pip git -y

# Verify versions
python3 --version    # Should be 3.11+
pip3 --version
```

### Step 4: Install Python Packages

```bash
cd /opt/cipher43-tool

# Install from requirements.txt
pip3 install -r requirements.txt

# Additional packages for production
pip3 install openpyxl uvicorn gunicorn
```

### Step 5: Configure

```bash
# Edit config.json
nano config.json

# Update:
# {
#     "browser": "gpm",
#     "be_url": "https://api.cipher43lab.com",
#     "local_tool_url": "https://tool.cipher43lab.com:8000",
#     "tool_token": ""
# }
```

### Step 6: Test Run

```bash
cd /opt/cipher43-tool
python3 api_server.py

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# Press Ctrl+C to stop
```

Test trên terminal khác:

```bash
curl http://localhost:8000
# Expected: {"status":"online"}
```

✅ **Local Tool working locally!**

---

## 🔧 Production Setup (Nginx + HTTPS)

### Step 1: Install Nginx + Certbot

```bash
# Install Nginx
sudo apt install nginx -y

# Install Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 2: Create Nginx Config

```bash
# Create config file
sudo nano /etc/nginx/sites-available/cipher43-tool
```

Paste this:

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
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # CORS headers
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
}
```

Save: Ctrl+O, Enter, Ctrl+X

### Step 3: Enable Config

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/cipher43-tool /etc/nginx/sites-enabled/

# Test Nginx config
sudo nginx -t

# Should output: "syntax is ok" and "test is successful"

# Restart Nginx
sudo systemctl restart nginx
```

### Step 4: Setup SSL Certificate

```bash
# Generate SSL certificate with Let's Encrypt
sudo certbot --nginx -d tool.cipher43lab.com

# Follow prompts:
# 1. Enter email
# 2. Accept terms
# 3. Choose redirect option (2 = redirect HTTP to HTTPS)

# Verify certificate
sudo certbot certificates
```

Nginx config sẽ tự-update với HTTPS. ✅

### Step 5: Test HTTPS

```bash
curl https://tool.cipher43lab.com:8000
# Expected: {"status":"online"}
```

✅ **HTTPS working!**

---

## 🔄 Auto-Start Service (Systemd)

### Step 1: Create User (Optional but Recommended)

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash cipher43

# Change ownership
sudo chown -R cipher43:cipher43 /opt/cipher43-tool

# Allow user to access
sudo usermod -aG www-data cipher43
```

### Step 2: Create Systemd Service

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
StandardOutput=append:/var/log/cipher43-tool.log
StandardError=append:/var/log/cipher43-tool.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Save: Ctrl+O, Enter, Ctrl+X

### Step 3: Enable Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable cipher43-tool

# Start service
sudo systemctl start cipher43-tool

# Check status
sudo systemctl status cipher43-tool

# View logs
sudo journalctl -u cipher43-tool -f

# Or from log file
tail -f /var/log/cipher43-tool.log
```

✅ **Service will auto-restart on failure and on server reboot!**

---

## 📊 Monitoring

### Check Service Status

```bash
sudo systemctl status cipher43-tool
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u cipher43-tool -f

# Last 50 lines
sudo journalctl -u cipher43-tool -n 50

# Or file logs
tail -f /var/log/cipher43-tool.log
```

### Monitor Performance

```bash
# CPU/Memory usage
top

# Disk usage
df -h

# Network connections
netstat -tlnp | grep 8000
```

### Health Check

```bash
# Backend connectivity
curl https://api.cipher43lab.com/

# Local Tool connectivity
curl https://tool.cipher43lab.com:8000/

# Check profiles endpoint
curl https://tool.cipher43lab.com:8000/profiles
```

---

## 🔄 Updates & Maintenance

### Update Code (Pull Latest)

```bash
cd /opt/cipher43-tool
git pull origin main

# Restart service
sudo systemctl restart cipher43-tool

# Check status
sudo systemctl status cipher43-tool
```

### Update Dependencies

```bash
cd /opt/cipher43-tool

# Update pip packages
pip3 install --upgrade -r requirements.txt

# Restart
sudo systemctl restart cipher43-tool
```

### Renew SSL Certificate

```bash
# Certbot auto-renews, but you can manually run:
sudo certbot renew

# Check certificate
sudo certbot certificates
```

---

## 🛡️ Security Best Practices

### 1. Firewall Setup

```bash
# Install UFW
sudo apt install ufw -y

# Enable firewall
sudo ufw enable

# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other ports
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Check status
sudo ufw status
```

### 2. Security Updates

```bash
# Enable automatic updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades

# Check for updates
sudo apt update
sudo apt list --upgradable
```

### 3. SSH Security

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config

# Find and set:
# PermitRootLogin no
# PubkeyAuthentication yes
# PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### 4. Backup

```bash
# Backup config files
mkdir ~/backups
cp /opt/cipher43-tool/config.json ~/backups/config.json.backup
```

---

## 🚨 Troubleshooting

### ❌ Service không start

```bash
# Check status
sudo systemctl status cipher43-tool

# View detailed logs
sudo journalctl -u cipher43-tool -n 100

# Manually run để see errors
cd /opt/cipher43-tool && python3 api_server.py
```

### ❌ Port 8000 already in use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or restart service
sudo systemctl restart cipher43-tool
```

### ❌ SSL certificate error

```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# View certificate details
openssl s_client -connect tool.cipher43lab.com:443
```

### ❌ Nginx proxy not working

```bash
# Test Nginx config
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### ❌ API không connect

```bash
# Test if service is running
curl http://localhost:8000

# Check if port listening
netstat -tlnp | grep 8000

# Check firewall
sudo ufw status

# Check Nginx upstream
curl -v https://tool.cipher43lab.com:8000
```

---

## ✅ Verification Checklist

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (pip3 install -r requirements.txt)
- [ ] config.json updated with production URLs
- [ ] Nginx installed and configured
- [ ] SSL certificate installed
- [ ] Service file created and enabled
- [ ] Service running (systemctl status)
- [ ] HTTPS responding (curl https://...)
- [ ] Local Tool online
- [ ] Backend connectivity working
- [ ] Firewall configured
- [ ] Monitoring setup

---

## 🎯 Production URLs

```
Backend:   https://api.cipher43lab.com
Frontend:  https://cipher43lab.com
Local Tool: https://tool.cipher43lab.com:8000
```

---

## 📞 Support

Having issues?

1. **Check logs:** `sudo journalctl -u cipher43-tool -f`
2. **Test manually:** `python3 api_server.py`
3. **Check connectivity:** `curl https://tool.cipher43lab.com:8000`
4. **Review troubleshooting section above**

---

**Server Setup Complete!** ✅

Your Local Tool is now production-ready.

Generated: 2026-04-22  
Version: 1.0.0
