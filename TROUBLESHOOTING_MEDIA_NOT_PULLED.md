# Troubleshooting: Media Not Being Pulled

## 🚨 CRITICAL: Bot Account Limitation (MOST COMMON ISSUE)

### **Telegram API Restriction for Bots**

If you see this error in logs:
```
The API access for bot users is restricted. 
The method you tried to invoke cannot be executed as a bot 
(caused by GetHistoryRequest)
```

**This is a Telegram API limitation, NOT a bug in your code!**

### **What Bots Can and Cannot Do**

✅ **Bots CAN:**
- Receive NEW messages in real-time
- Listen to channels they're added to
- Process incoming media as it arrives

❌ **Bots CANNOT:**
- Fetch historical messages from channels
- Use `client.get_messages()` to pull message history
- Access past messages via `GetHistoryRequest`

### **Solution: Switch to User Account**

To pull historical media, you MUST use a **user account session** instead of a bot token.

**Quick Fix:**
1. Generate user session (see instructions below)
2. Remove `TG_BOT_TOKEN` from Coolify
3. Upload `telethon_session.session` file
4. Redeploy

**Detailed instructions in "Scenario 5" below.**

---

## Issue: Telethon Connected but No Media Pulled

If your `/health` endpoint shows `"telethon_connected": true` but media is not being pulled from channels, follow this guide.

---

## Root Cause Analysis

The media pulling system has **3 trigger points**:

1. **Startup Pull** - Runs once when app starts (only if channels exist)
2. **New Message Handler** - Triggers when new messages arrive in real-time
3. **Manual Trigger** - Via API or admin dashboard

### Why Media Might Not Be Pulled

#### ❌ **No Channels Configured**
- Media pull only runs if there are active channels
- Check: Go to admin dashboard → Channels tab

#### ❌ **Channels Added After Startup**
- If you add channels after the app started, the initial pull already ran
- Solution: Use manual trigger or restart app

#### ❌ **Bot Doesn't Have Access to Channels**
- For private channels, the bot must be a member
- For public channels, bot needs read access

#### ❌ **Channels Don't Have Audio/PDF Files**
- System only pulls `audio/mpeg`, `audio/ogg`, and `application/pdf`
- Other file types are ignored

---

## Diagnostic Steps

### Step 1: Use the Diagnostics Dashboard

1. Login to admin dashboard: `https://your-domain.com/admin`
2. Click **🔧 Diagnostics** in sidebar
3. Review the system status:
   - ✅ Telethon: Started & Connected
   - ✅ Database: Connected
   - ✅ Active Channels: > 0
   - ✅ Total Media: Should increase after pull

### Step 2: Check Recommendations

The diagnostics page shows actionable recommendations:

- **🔴 Critical** - Must fix immediately
- **⚠️ Warning** - Should address soon
- **ℹ️ Info** - Informational
- **✅ Success** - All good

### Step 3: Manual Trigger

Click **🔄 Trigger Media Pull** button in diagnostics tab.

**Expected behavior:**
- Button shows "⏳ Pulling..."
- After 3-10 seconds: Success message
- Diagnostics refresh automatically
- Check "Total Media" count increases

### Step 4: Check Application Logs

In Coolify logs, look for:

```
✅ Starting historical media pull from all active channels...
✅ Pulling historical media from channel: @channel_name
✅ Pulled 42 audio/PDF messages from @channel_name
```

**If you see:**
```
❌ No active channels found to pull media from
```
→ Add channels first

```
❌ Cannot pull media: Telethon client is not connected
```
→ Check TG_BOT_TOKEN

```
❌ Error pulling media from @channel: [error details]
```
→ Check channel access permissions

---

## Solutions by Scenario

### Scenario 1: No Channels Configured

**Symptoms:**
- Diagnostics shows "Active Channels: 0"
- Recommendation: "No active channels configured"

**Solution:**
1. Go to **Channels** tab
2. Enter channel username (e.g., `@durov`)
3. Click **Add Channel**
4. Go back to **Diagnostics** tab
5. Click **🔄 Trigger Media Pull**

---

### Scenario 2: Channels Added After Startup

**Symptoms:**
- Channels exist but "Total Media: 0"
- No errors in logs

**Solution:**
Use manual trigger:
```bash
# Via API
curl -X POST "https://your-domain.com/api/diagnostics/trigger-pull" \
  -H "Authorization: Bearer $TOKEN"

# Or use admin dashboard Diagnostics tab
```

---

### Scenario 3: Bot Lacks Channel Access

**Symptoms:**
- Logs show: `Error pulling media from @channel: ChatAdminRequiredError` or `ChannelPrivateError`

**Solution:**

**For Public Channels:**
- Bot should have automatic read access
- Verify channel username is correct (include @)

**For Private Channels:**
1. Add bot to channel as member
2. Grant read permissions
3. Trigger manual pull

**To verify access:**
1. Go to **Preview Messages** tab
2. Enter channel username
3. Click **Preview**
4. If you see messages → Access OK
5. If error → Fix permissions

---

### Scenario 4: Channels Have No Supported Media

**Symptoms:**
- Pull completes successfully
- Logs show: `Pulled 0 audio/PDF messages from @channel`
- Total Media stays at 0

**Solution:**

Check what media types exist:
1. Go to **Preview Messages** tab
2. Enter channel username
3. Check MIME types in results

**Supported types:**
- ✅ `audio/mpeg` (MP3)
- ✅ `audio/ogg` (OGG)
- ✅ `application/pdf` (PDF)

**Not supported:**
- ❌ `video/*`
- ❌ `image/*`
- ❌ `application/zip`
- ❌ Other types

**To add support for other types:**
Edit `app/telethon_client.py` lines 160-163:
```python
if msg.file.mime_type in ["audio/mpeg", "audio/ogg"]:
    media_type = "audio"
elif msg.file.mime_type == "application/pdf":
    media_type = "pdf"
# Add more types here:
elif msg.file.mime_type == "video/mp4":
    media_type = "video"
```

---

### Scenario 5: Bot Account Cannot Pull Historical Messages (MOST COMMON)

**Symptoms:**
- Logs show: `The API access for bot users is restricted. The method you tried to invoke cannot be executed as a bot (caused by GetHistoryRequest)`
- Telethon connected successfully
- Channels configured correctly
- Total Media: 0
- Diagnostics shows: "Bot accounts cannot pull historical messages"

**Root Cause:**
Telegram API **does not allow bots** to fetch historical messages. This is a platform limitation, not a bug.

**Solution: Generate and Use User Session**

#### **Step 1: Generate User Session Locally**

Create a Python script `generate_session.py`:

```python
from telethon import TelegramClient

# Your API credentials (same as in Coolify)
API_ID = 26694786  # Your actual API_ID
API_HASH = "your_api_hash_here"  # Your actual API_HASH

# Create client
client = TelegramClient('telethon_session', API_ID, API_HASH)

async def main():
    await client.start()
    print("✅ Session created successfully!")
    print(f"Logged in as: {await client.get_me()}")
    await client.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

Run it:
```bash
pip install telethon
python generate_session.py
```

**It will prompt for:**
1. Phone number (with country code, e.g., +1234567890)
2. Verification code (sent to your Telegram app)
3. 2FA password (if enabled)

**Result:** Creates `telethon_session.session` file

#### **Step 2: Upload Session to Coolify**

**Option A: Via Coolify Persistent Storage**
1. In Coolify, go to your app → Storage
2. Create persistent volume mounted to `/app`
3. Upload `telethon_session.session` to the volume

**Option B: Via Docker Volume**
```bash
# Copy session file to Coolify server
scp telethon_session.session user@your-server:/path/to/volume/

# Or use Coolify file manager
```

#### **Step 3: Update Environment Variables**

In Coolify environment variables:
1. **Remove** `TG_BOT_TOKEN` (or leave empty)
2. **Keep** `TG_API_ID` and `TG_API_HASH`
3. **Set** `TG_SESSION=telethon_session` (default)

#### **Step 4: Redeploy**

Click "Redeploy" in Coolify

**Expected logs:**
```
INFO - Starting Telethon client with existing session...
INFO - ✅ Telethon client connected successfully
INFO - ✅ Logged in as: YourName (ID: 123456789)
INFO - User account detected - pulling historical media
INFO - Pulling historical media from channel: @channel
INFO - Pulled 150 audio/PDF messages from @channel
```

#### **Verification:**

1. Check diagnostics dashboard:
   - Started: ✅ Yes
   - Connected: ✅ Yes
   - Client Type: User (not Bot)
   - Total Media: > 0

2. Go to Pending Media tab - should show files

---

### Scenario 6: Rate Limiting

**Symptoms:**
- Logs show: `FloodWaitError: A wait of X seconds is required`

**Solution:**
- Telegram is rate limiting your account
- Wait the specified time
- Reduce pull frequency
- For bots: Switch to user account (has higher limits)

---

## API Endpoints for Diagnostics

### Get System Status
```bash
curl "https://your-domain.com/api/diagnostics/status" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "telethon": {
    "started": true,
    "connected": true,
    "is_bot": true
  },
  "database": {
    "connected": true,
    "total_channels": 3,
    "active_channels": 3,
    "total_media": 0,
    "pending_media": 0,
    "approved_media": 0
  },
  "channels": [
    {"id": 1, "username": "@channel1", "active": true}
  ],
  "recommendations": [...]
}
```

### Trigger Manual Pull
```bash
curl -X POST "https://your-domain.com/api/diagnostics/trigger-pull" \
  -H "Authorization: Bearer $TOKEN"
```

**Success Response:**
```json
{
  "success": true,
  "message": "Media pull triggered for 3 active channel(s)",
  "channels": ["@channel1", "@channel2", "@channel3"]
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "No active channels",
  "message": "No active channels configured. Add channels first."
}
```

---

## Verification Checklist

After troubleshooting, verify:

- [ ] `/health` shows `"telethon_connected": true`
- [ ] Diagnostics shows "Active Channels: > 0"
- [ ] Manual trigger returns success
- [ ] Logs show "Pulled X audio/PDF messages"
- [ ] Diagnostics shows "Total Media: > 0"
- [ ] Pending Media tab shows files
- [ ] Can approve and download media

---

## Common Mistakes

### ❌ Wrong Channel Username Format
```bash
# Wrong
channel_name
t.me/channel_name
https://t.me/channel_name

# Correct
@channel_name
```

### ❌ Expecting Immediate Results
- Media pull runs in background
- May take 10-30 seconds for large channels
- Check diagnostics after 30 seconds

### ❌ Not Checking Logs
- Logs contain detailed error messages
- Always check Coolify logs when troubleshooting

### ❌ Forgetting to Trigger After Adding Channels
- Adding channels doesn't auto-trigger pull
- Must manually trigger or restart app

---

## Advanced Debugging

### Check Database Directly

```bash
# SSH into container
docker exec -it your-container bash

# Check channels
python -c "
from app.database import SessionLocal
from app.models import Channel, MediaFile
db = SessionLocal()
channels = db.query(Channel).all()
print(f'Channels: {len(channels)}')
for c in channels:
    print(f'  {c.id}: {c.username} (active={c.active})')
"

# Check media
python -c "
from app.database import SessionLocal
from app.models import MediaFile
db = SessionLocal()
media = db.query(MediaFile).all()
print(f'Media files: {len(media)}')
for m in media[:5]:
    print(f'  {m.id}: {m.file_name} ({m.file_type}) - {m.channel_username}')
"
```

### Test Telethon Connection

```bash
docker exec -it your-container python -c "
import asyncio
from app.telethon_client import client, ensure_client_connected

async def test():
    await ensure_client_connected()
    print(f'Connected: {client.is_connected()}')
    print(f'Is bot: {await client.is_bot()}')
    
asyncio.run(test())
"
```

### Test Channel Access

```bash
docker exec -it your-container python -c "
import asyncio
from app.telethon_client import client, fetch_recent_channel_messages

async def test():
    messages = await fetch_recent_channel_messages('@channel_name', limit=5)
    print(f'Found {len(messages)} messages')
    for m in messages:
        print(f'  Message {m[\"message_id\"]}: {m[\"mime_type\"]}')
    
asyncio.run(test())
"
```

---

## Still Not Working?

If media is still not being pulled:

1. **Restart the application**
   - In Coolify, click "Restart"
   - This re-runs startup pull

2. **Check environment variables**
   ```bash
   docker exec your-container env | grep TG_
   ```
   Verify: `TG_BOT_TOKEN`, `TG_API_ID`, `TG_API_HASH`

3. **Test with a known channel**
   - Try `@durov` (Telegram founder's channel)
   - Has many media files for testing

4. **Enable debug logging**
   ```bash
   LOG_LEVEL=DEBUG
   ```
   Redeploy and check logs for detailed output

5. **Check Sentry (if configured)**
   - Errors are reported to Sentry
   - Check for exceptions

---

## Summary

**Most common fix:** Use the **🔄 Trigger Media Pull** button in the Diagnostics tab after adding channels.

**Key insight:** Media pull only runs automatically at startup. If you add channels later, you must manually trigger it.

**Prevention:** Always use the Diagnostics tab to verify system status before assuming something is broken.
