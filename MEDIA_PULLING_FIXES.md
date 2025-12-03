# Media Pulling Issues - Fixes Applied

## Summary

This document outlines the issues preventing media from being pulled from Telegram channels and the fixes that have been applied.

---

## Issues Identified & Fixed

### ✅ 1. **Telethon Client Connection Checking**
**Problem:** Functions didn't verify if the client was connected before making API calls.

**Fix Applied:**
- Added `ensure_client_connected()` function that checks connection status
- Auto-reconnects if disconnected
- All API functions now call this before making requests
- Added better logging for connection status

**Files Modified:**
- `app/telethon_client.py`

---

### ✅ 2. **Retry Logic for Telegram API Calls**
**Problem:** Transient failures (network issues, rate limits) caused media to be permanently skipped.

**Fix Applied:**
- Added 3-retry logic with 5-second delays in `pull_all_channel_media()`
- Better error messages showing retry attempts
- Continues to next channel even if one fails

**Files Modified:**
- `app/telethon_client.py`

---

### ✅ 3. **Unsafe asyncio.create_task() Usage**
**Problem:** Tasks created in sync context could be garbage collected before execution.

**Fix Applied:**
- Changed endpoints to async
- Use FastAPI's `BackgroundTasks` for proper task management
- Fallback with `asyncio.ensure_future()` to prevent garbage collection

**Files Modified:**
- `app/api/channels.py`

---

### ✅ 4. **Background Task Scheduler Improvements**
**Problem:** Scheduler called `start_client()` repeatedly but didn't properly handle reconnections.

**Fix Applied:**
- Created `check_and_reconnect_client()` function
- Checks connection status every 5 minutes
- Attempts reconnection before full restart
- Better logging for connection monitoring

**Files Modified:**
- `app/tasks.py`

---

### ✅ 5. **Health Check Enhancement**
**Problem:** `/health` endpoint didn't report Telethon client status.

**Fix Applied:**
- Health check now includes:
  - `telethon_client`: Status string (connected/disconnected/started_but_disconnected)
  - `telethon_connected`: Boolean connection status
- Allows monitoring tools to detect when media pulling is broken

**Files Modified:**
- `app/main.py`

---

### ✅ 6. **Better Error Handling & Logging**
**Problem:** Silent failures made debugging difficult.

**Fix Applied:**
- Added comprehensive logging throughout
- Connection status logged at startup
- Retry attempts logged
- Empty channel list detection
- All exceptions logged with stack traces

**Files Modified:**
- `app/telethon_client.py`
- `app/tasks.py`

---

## Deployment Checklist for Coolify

### **Critical: Verify These Environment Variables**

1. **Telegram Authentication** (choose ONE method):
   
   **Option A: Bot Token (Recommended for production)**
   ```bash
   TG_BOT_TOKEN=your_bot_token_here
   ```
   Get from [@BotFather](https://t.me/BotFather) on Telegram
   
   **Option B: User Session File**
   - Mount existing `telethon_session.session` file to `/app/` in container
   - Configure persistent volume in Coolify

2. **Required Variables:**
   ```bash
   TG_API_ID=12345678
   TG_API_HASH=your_api_hash_here
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   S3_ENDPOINT=http://minio:9000
   S3_ACCESS_KEY=minioadmin
   S3_SECRET_KEY=minioadmin
   ```

3. **Optional but Recommended:**
   ```bash
   LOG_LEVEL=DEBUG  # For troubleshooting, use INFO in production
   JWT_SECRET=your_strong_secret_here
   ```

---

## Troubleshooting Steps

### **Step 1: Check Health Endpoint**

```bash
curl https://your-domain.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "telethon_client": "connected",
  "telethon_connected": true
}
```

**If `telethon_client` is "disconnected":**
- Check logs for authentication errors
- Verify `TG_BOT_TOKEN` or session file is present
- Check `TG_API_ID` and `TG_API_HASH` are correct

---

### **Step 2: Check Application Logs**

In Coolify, go to **Logs** tab and look for:

**✅ Success indicators:**
```
Starting Telethon client with bot token...
Telethon client connected successfully
Event handlers registered
Starting historical media pull from all active channels...
Pulled X audio/PDF messages from @channel
```

**❌ Error indicators:**
```
No TG_BOT_TOKEN and no existing Telethon session file found
Telethon client failed to connect
Cannot pull media: Telethon client is not connected
Error pulling media from @channel
```

---

### **Step 3: Verify Channels Are Added**

```bash
TOKEN="your_jwt_token"
curl https://your-domain.com/api/channels/ \
  -H "Authorization: Bearer $TOKEN"
```

**If empty `[]`:**
- No channels have been added yet
- Add a channel via admin dashboard or API

---

### **Step 4: Add a Test Channel**

```bash
TOKEN="your_jwt_token"
curl -X POST "https://your-domain.com/api/channels/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "@durov"}'
```

**Check logs for:**
```
Triggered media pull for new channel: @durov
Pulling historical media from channel: @durov
Pulled X audio/PDF messages from @durov
```

---

### **Step 5: Check Pending Media**

```bash
TOKEN="your_jwt_token"
curl https://your-domain.com/api/media/pending \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** List of media files waiting for approval

**If empty:**
- Channel may not have audio/PDF files
- Check logs for errors during media pull
- Try a different channel with known media

---

### **Step 6: Test Media Preview**

```bash
TOKEN="your_jwt_token"
curl "https://your-domain.com/api/telegram/@durov/messages?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** Recent messages with file metadata

**If fails:**
- Telethon client not connected
- Channel username incorrect (must include @)
- Bot doesn't have access to channel

---

## Common Issues & Solutions

### **Issue: "No TG_BOT_TOKEN and no existing Telethon session file found"**

**Solution:**
1. Get bot token from [@BotFather](https://t.me/BotFather)
2. Add to Coolify environment variables: `TG_BOT_TOKEN=123456:ABC-DEF...`
3. Redeploy

**OR**

1. Create session file locally:
   ```python
   from telethon import TelegramClient
   client = TelegramClient('telethon_session', API_ID, API_HASH)
   client.start()  # Follow prompts
   ```
2. Upload `telethon_session.session` to Coolify volume mounted at `/app/`

---

### **Issue: "Telethon client disconnected" in health check**

**Solution:**
1. Check logs for disconnection reason
2. Verify network connectivity to Telegram servers
3. Check if bot token is valid (test with [@BotFather](https://t.me/BotFather))
4. Wait 5 minutes for auto-reconnect (scheduler will retry)
5. If persists, restart container

---

### **Issue: No media being pulled from channels**

**Checklist:**
- [ ] Telethon client connected (`/health` shows `"connected"`)
- [ ] Channels added and active (`/api/channels/` returns list)
- [ ] Channels actually contain audio/PDF files
- [ ] Bot has access to channels (if private, bot must be member)
- [ ] Check logs for "Pulled X audio/PDF messages" confirmations

**Debug:**
```bash
# Set log level to DEBUG
LOG_LEVEL=DEBUG

# Check specific channel
curl "https://your-domain.com/api/telegram/@channel/messages?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

---

### **Issue: Media pulled but not appearing in pending list**

**Possible Causes:**
1. Media already exists in database (check `message_id` uniqueness)
2. MIME type not recognized (only `audio/mpeg`, `audio/ogg`, `application/pdf`)
3. Database connection issue

**Debug:**
```bash
# Check database directly
docker exec -it your-container python -c "
from app.database import SessionLocal
from app.models import MediaFile
db = SessionLocal()
count = db.query(MediaFile).count()
print(f'Total media files: {count}')
recent = db.query(MediaFile).order_by(MediaFile.id.desc()).limit(5).all()
for m in recent:
    print(f'ID: {m.id}, Type: {m.file_type}, Approved: {m.approved}, Channel: {m.channel_username}')
"
```

---

### **Issue: Background tasks not running**

**Solution:**
1. Check scheduler is running in logs:
   ```
   Background task scheduler started (checking Telethon connection every 5 minutes)
   ```
2. Verify no errors in scheduler:
   ```
   Error checking/reconnecting Telethon client: ...
   ```
3. Restart container if scheduler crashed

---

## Performance Optimization

### **For Large Channels (10,000+ messages)**

The current implementation fetches ALL messages with `limit=None`. For very large channels:

1. **Monitor memory usage** in Coolify Stats tab
2. **Consider pagination** if memory issues occur:
   ```python
   # In pull_all_channel_media(), replace:
   messages = await client.get_messages(entity, limit=None)
   
   # With paginated approach:
   offset_id = 0
   while True:
       messages = await client.get_messages(entity, limit=100, offset_id=offset_id)
       if not messages:
           break
       # Process messages...
       offset_id = messages[-1].id
   ```

3. **Increase container memory** in Coolify if needed

---

## Monitoring Recommendations

### **1. Set up Sentry (Optional)**
```bash
SENTRY_DSN=https://your-sentry-dsn
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### **2. Monitor Health Endpoint**
Set up external monitoring (UptimeRobot, Pingdom, etc.) to check:
```
https://your-domain.com/health
```

Alert if `telethon_connected` is `false` for > 10 minutes.

### **3. Log Aggregation**
Consider forwarding logs to external service:
- Papertrail
- Logtail
- Elasticsearch

### **4. Metrics to Track**
- Media files pulled per day
- Approval rate
- Failed download attempts
- Telethon disconnection frequency

---

## Next Steps After Deployment

1. **Verify health check shows connected**
2. **Add your first channel**
3. **Check pending media appears**
4. **Approve a test media file**
5. **Verify S3 upload successful**
6. **Test download URL generation**
7. **Set up monitoring alerts**

---

## Support & Debugging

If issues persist after following this guide:

1. **Collect logs** from last 100 lines:
   ```bash
   # In Coolify logs tab, or:
   docker logs your-container --tail 100
   ```

2. **Check environment variables** are set correctly:
   ```bash
   docker exec your-container env | grep TG_
   ```

3. **Verify database connectivity**:
   ```bash
   docker exec your-container python -c "
   from app.database import engine
   engine.connect()
   print('Database connected!')
   "
   ```

4. **Test Telegram API directly**:
   ```bash
   docker exec your-container python -c "
   from app.telethon_client import client
   import asyncio
   async def test():
       await client.connect()
       print(f'Connected: {client.is_connected()}')
   asyncio.run(test())
   "
   ```

---

## Summary of Code Changes

**Files Modified:**
1. `app/telethon_client.py` - Connection checking, retry logic, better error handling
2. `app/api/channels.py` - Fixed async task creation
3. `app/tasks.py` - Improved reconnection logic
4. `app/main.py` - Enhanced health check

**No Breaking Changes:**
- All existing API endpoints remain compatible
- Database schema unchanged
- Environment variables backward compatible

**Recommended Actions:**
1. Redeploy application in Coolify
2. Verify `TG_BOT_TOKEN` is set
3. Check `/health` endpoint shows connected
4. Monitor logs for successful media pulls
5. Test adding a channel and approving media

---

**Last Updated:** December 3, 2024
