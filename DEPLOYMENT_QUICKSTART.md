# Quick Deployment Fix Guide

## 🚨 Critical Issue: Media Not Being Pulled

Your Telethon FastAPI application has been **fixed** to resolve media pulling issues. This guide will help you deploy the fixes.

---

## What Was Fixed

✅ **Connection checking** - Client now verifies connection before API calls  
✅ **Auto-reconnection** - Background task reconnects if disconnected  
✅ **Retry logic** - 3 retries with delays for transient failures  
✅ **Better error handling** - Comprehensive logging for debugging  
✅ **Health monitoring** - `/health` endpoint now shows Telethon status  
✅ **Task management** - Fixed async task creation issues  

---

## Deployment Steps (Coolify)

### 1. **Set Required Environment Variable**

The #1 reason media isn't pulled: **Missing authentication**

**Choose ONE method:**

#### Option A: Bot Token (Recommended)
```bash
TG_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```
Get from [@BotFather](https://t.me/BotFather) on Telegram

#### Option B: Session File
- Upload `telethon_session.session` to persistent volume at `/app/`

### 2. **Verify Other Environment Variables**

```bash
# Required
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
DATABASE_URL=postgresql://user:pass@host:5432/dbname
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Optional (for debugging)
LOG_LEVEL=DEBUG
```

### 3. **Redeploy in Coolify**

1. Go to your application in Coolify
2. Click **"Redeploy"** or push to main branch (if auto-deploy enabled)
3. Wait for build to complete

### 4. **Verify Deployment**

Run the verification script:

```bash
# From your local machine
BASE_URL=https://your-domain.com \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=your_password \
bash verify_deployment.sh
```

**Or manually check:**

```bash
curl https://your-domain.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "telethon_client": "connected",
  "telethon_connected": true
}
```

### 5. **Add a Channel**

Via admin dashboard at `https://your-domain.com/admin`

Or via API:
```bash
TOKEN="your_jwt_token"
curl -X POST "https://your-domain.com/api/channels/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "@channel_name"}'
```

### 6. **Monitor Logs**

In Coolify **Logs** tab, look for:

```
✅ Starting Telethon client with bot token...
✅ Telethon client connected successfully
✅ Event handlers registered
✅ Starting historical media pull from all active channels...
✅ Pulling historical media from channel: @channel_name
✅ Pulled 42 audio/PDF messages from @channel_name
```

---

## Troubleshooting

### ❌ "telethon_client": "disconnected"

**Cause:** No `TG_BOT_TOKEN` or invalid credentials

**Fix:**
1. Add `TG_BOT_TOKEN` to Coolify environment variables
2. Verify token is valid with [@BotFather](https://t.me/BotFather)
3. Redeploy

### ❌ No media being pulled

**Checklist:**
- [ ] Health check shows `"connected"`
- [ ] Channels added (`/api/channels/` returns list)
- [ ] Channels contain audio/PDF files
- [ ] Bot has access to channels (for private channels)
- [ ] Check logs for "Pulled X messages" confirmations

**Debug:**
```bash
# Check if channel is accessible
curl "https://your-domain.com/api/telegram/@channel/messages?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### ❌ Background tasks not running

**Symptoms:** Client disconnects and never reconnects

**Fix:**
1. Check logs for scheduler errors
2. Restart container in Coolify
3. Verify no memory/CPU limits being hit

---

## Quick Health Check

```bash
# 1. Is app running?
curl https://your-domain.com/health

# 2. Is Telethon connected?
curl https://your-domain.com/health | grep "connected"

# 3. Are channels added?
curl https://your-domain.com/api/channels/

# 4. Is media being pulled?
# Check logs for "Pulled X audio/PDF messages"
```

---

## Files Changed

This fix modified:
- `app/telethon_client.py` - Connection checking, retry logic
- `app/api/channels.py` - Fixed async task creation
- `app/tasks.py` - Improved reconnection
- `app/main.py` - Enhanced health check

**No database migrations needed** - just redeploy!

---

## Getting Help

1. **Check logs first** - Most issues are visible in logs
2. **Verify environment variables** - Especially `TG_BOT_TOKEN`
3. **Test health endpoint** - Shows Telethon connection status
4. **Read full guide** - See `MEDIA_PULLING_FIXES.md` for details

---

## Success Checklist

After deployment, verify:

- [x] `/health` shows `"telethon_client": "connected"`
- [x] Logs show "Telethon client connected successfully"
- [x] Can add channels via API or admin dashboard
- [x] Logs show "Pulled X audio/PDF messages from @channel"
- [x] Pending media appears in `/api/media/pending`
- [x] Can approve media and download from S3

---

**Need more details?** See `MEDIA_PULLING_FIXES.md` for comprehensive troubleshooting.
