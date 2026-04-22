# ✅ Cipher 43 Tool System — Deployment Checklist

**Status: 90% Done - Waiting on Manual Setup**

---

## 🟢 Completed (Automated)

### Local Tool (Xeon)
- ✅ API Server running: `http://127.0.0.1:8001`
- ✅ Ngrok tunnel active: `https://violeta-lamprophonic-venially.ngrok-free.dev`
- ✅ Genlogin adapter configured (cipher43 / Alantruong@113)
- ✅ Config file: `config.json`
- ✅ Endpoints: `GET /profiles`, `POST /run`
- ✅ Git auto-pull mechanism
- ✅ Excel reader with column mapping
- ✅ Token validation integration

### Backend (cipher43lab.com)
- ✅ ToolToken model created
- ✅ Token generation: `POST /api/tool-tokens/generate`
- ✅ Token verification: `POST /api/tool-tokens/verify`
- ✅ Tool verification: `POST /api/tools/verify-token`
- ✅ scriptName field added to Tool model
- ✅ Code committed and pushed to main branch

---

## 🟠 Pending - User Action Required

### Step 1: Deploy Backend Changes
**Status: ⏳ Waiting for you**

```bash
cd /path/to/Cipher-43-lab-BE
git pull  # Pull the latest changes (commit: 79a938c)
npm install  # If any new deps
npm restart  # or your deploy command
```

**Changes included in this commit:**
- models/ToolToken.js (new model)
- models/Tool.js (added scriptName field)
- controllers/ToolController.js (added verifyToolToken)
- routes/tool.js (added /verify-token route)

**Verify deployment:**
```bash
curl https://cipher43lab.com/api/tools/verify-token \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"token": "test"}'
```

Should return 401 with message (not 404).

---

### Step 2: Create a Test Tool on Backend
**Status: ⏳ Waiting for you**

**Option A: Using MongoDB direct**
```javascript
db.tools.insertOne({
  id: 1,
  name: "Twitter Check",
  slug: "twitter-check",
  description: "Check Twitter login status",
  scriptName: "twitter",
  type: "free",
  features: ["Check login status"],
  apiLocked: false,
  image: "",
  about: "",
  howItWorks: [],
  useCases: [],
  badges: [],
  idUser: []
})
```

**Option B: Using API (if you have admin access)**
```bash
curl -X POST https://cipher43lab.com/api/tools \
  -H "Authorization: Bearer YOUR_ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Twitter Check",
    "slug": "twitter-check",
    "description": "Check Twitter login status",
    "scriptName": "twitter",
    "type": "free",
    "features": ["Check login status"],
    "apiLocked": false
  }'
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Twitter Check",
    "scriptName": "twitter",
    "_id": "...",
    ...
  }
}
```

---

### Step 3: Generate Token from Website
**Status: ⏳ Waiting for you**

**Login to cipher43lab.com:**
1. Go to Dashboard / Tools section
2. Find "Twitter Check" tool
3. Click "Get Token" button
4. Copy the token (format: `c43_abc123def456...`)

**OR via API:**
```bash
curl -X POST https://cipher43lab.com/api/tool-tokens/generate \
  -H "Authorization: Bearer YOUR_USER_JWT" \
  -H "Content-Type: application/json" \
  -d '{"toolId": 1}'
```

**Expected response:**
```json
{
  "message": "Token generated successfully",
  "token": "c43_abc123def456ghi789...",
  "toolName": "Twitter Check",
  "expiresAt": "2027-04-22T10:30:45Z"
}
```

**Save this token for testing.**

---

### Step 4: Test API Endpoints

#### Test 4a: Get Profiles
**Status: ⏳ Ready to test**

```bash
TOKEN="c43_your_token_here"
curl "https://violeta-lamprophonic-venially.ngrok-free.dev/profiles?token=$TOKEN"
```

**Expected response:**
```json
{
  "profiles": [
    {
      "id": "prof_123",
      "name": "Account_01",
      "status": "running"
    },
    {
      "id": "prof_456",
      "name": "Account_02",
      "status": "stopped"
    }
  ]
}
```

**If error:**
- `401 Token invalid` → Check token is valid
- `502 Bad gateway` → Local tool not running (restart on Xeon)
- `Connection timeout` → Ngrok tunnel issue

---

#### Test 4b: Run Script on Multiple Profiles
**Status: ⏳ Ready to test**

**Create Excel file: `C:\Users\admin\Desktop\profiles.xlsx`**

| profile_name | username        | password  |
|---|---|---|
| Account_01 | user1@gmail.com | pass123 |
| Account_02 | user2@gmail.com | pass456 |

```bash
TOKEN="c43_your_token_here"

curl -X POST https://violeta-lamprophonic-venially.ngrok-free.dev/run \
  -H "Content-Type: application/json" \
  -d "{
    \"tool_token\": \"$TOKEN\",
    \"script_name\": \"twitter\",
    \"excel_path\": \"C:\\\\Users\\\\admin\\\\Desktop\\\\profiles.xlsx\",
    \"extra_params\": {}
  }"
```

**Expected response:**
```json
{
  "status": "queued",
  "script": "twitter",
  "queued_profiles": ["Account_01", "Account_02"],
  "errors": []
}
```

---

## 🔍 How to Monitor Execution

**On Xeon machine (where API server runs):**

```bash
# Monitor real-time logs
tail -f api_server_logs.txt

# Or see console output (if running in foreground)
python api_server.py
```

**Check genlogin profiles:**
- Look at genlogin app
- Verify profiles are opening and closing as scripts run

---

## ❌ Troubleshooting

### "Token not found or invalid"
✓ Solution: Regenerate token, verify it's correct

### "Premium subscription required"
✓ Solution: Tool is type:'premium', user must have premium account type

### "Profile Account_01 not found"
✓ Solution: Check genlogin has profile with exact name "Account_01"

### "404 on /verify-token"
✓ Solution: Backend not deployed, pull latest code and restart

### "502 Bad gateway from ngrok"
✓ Solution: Local tool crashed, restart `python api_server.py` on Xeon

---

## 📋 Final Checklist

- [ ] Backend code pulled and deployed
- [ ] Test Tool created in database (id: 1, scriptName: "twitter")
- [ ] Token generated and tested
- [ ] `/profiles` endpoint returns profiles
- [ ] Excel file created with test profiles
- [ ] `/run` endpoint queues scripts successfully
- [ ] Genlogin profiles open/run scripts/close automatically

---

## 🎯 After All Steps Complete

Once all manual steps are done:

✅ System is fully functional
✅ Users can:
  - Login to website
  - Get tool tokens
  - Paste token into extension or use ngrok tunnel
  - Run scripts on multiple profiles via Excel
  - Track token usage

---

## 📞 Need Help?

Check logs:
- **Local tool**: Console output from `python api_server.py`
- **Backend**: Application logs in `/var/log/` or docker logs
- **Genlogin**: App logs for profile start/stop events

Review code:
- SETUP_GUIDE.md (in cipher43-tool folder)
- API documentation (this file)

---

**Generated: 2026-04-22**
**Local Tool Tunnel: https://violeta-lamprophonic-venially.ngrok-free.dev**
**Backend: https://cipher43lab.com**
