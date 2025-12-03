# Deployment Debugging Guide

## Current Issue: Telethon Client Not Starting

**Symptoms:**
- Diagnostics shows: Started: ❌ No, Connected: ❌ No
- Error when approving media: "The key is not registered in the system"
- 4,648 pending media files but nothing downloading

**This means the Telethon client failed to start during application startup.**

---

## Step 1: Check Container Logs

In Coolify, go to your application → **Logs** and look for these messages:

### **What to Look For:**

#### ✅ **SUCCESS - Should see:**
```
✅ Using session path from TG_SESSION: /data/telethon_session
   OR
✅ Found session file at: /data/telethon_session.session

✅ Initializing Telethon client with session: /data/telethon_session
✅ Starting Telethon client with existing session...
✅ Telethon client connected successfully
✅ Logged in as: YourName (ID: 123456789)
✅ User account detected - pulling historical media
```

#### ❌ **FAILURE - Might see:**

**Scenario A: No session file found**
```
❌ No TG_BOT_TOKEN and no session file found at /data/telethon_session.session
   Skipping Telethon client start to avoid interactive prompt
```
→ **Fix:** Upload session file to `/data/` in Coolify volume

**Scenario B: Invalid session file**
```
❌ Session file exists at /data/telethon_session.session but is invalid or incomplete
   The session may have been created with different API_ID/API_HASH
```
→ **Fix:** Regenerate session with correct credentials

**Scenario C: EOFError (old bug, should be fixed)**
```
❌ Failed to start Telethon client: EOFError: EOF when reading a line
```
→ **Fix:** Should be resolved by latest code, force rebuild

**Scenario D: Import error**
```
ModuleNotFoundError: No module named 'telethon'
```
→ **Fix:** Rebuild container (dependencies not installed)

---

## Step 2: Verify Session File Location

### **Check Coolify Volume**

1. Go to Coolify → Your App → **Storage/Volumes**
2. Find your persistent volume
3. Verify `telethon_session.session` exists in the volume
4. Check the file size (should be ~28KB, not 0 bytes)

### **Check Environment Variables**

In Coolify → Your App → **Environment Variables**, verify:

```bash
TG_API_ID=26694786
TG_API_HASH=34cea1013b192f5ded0d97c6fd9152dc
TG_SESSION=telethon_session  # OR /data/telethon_session
```

**Important:** Do NOT set `TG_BOT_TOKEN` if using user session!

---

## Step 3: Session File Validation

### **Is Your Session File Valid?**

The session file MUST be generated with the **EXACT same** API_ID and API_HASH as your deployment.

**To verify:**
1. Check what API_ID/API_HASH you used when generating the session
2. Compare with Coolify environment variables
3. If they don't match → regenerate session

### **Generate New Session**

On your local machine:

```bash
cd /home/master/telethon_fastapi/telethon_fastapi
./venv/bin/python3 generate_session.py
```

**When prompted:**
- API_HASH: `34cea1013b192f5ded0d97c6fd9152dc` (from Coolify)
- Phone: `+1234567890` (your Telegram number)
- Code: Check Telegram app
- 2FA: Your cloud password (if enabled)

**Upload the generated `telethon_session.session` to Coolify volume.**

---

## Step 4: Force Rebuild

Sometimes Docker cache causes issues. In Coolify:

1. Go to your application
2. Click **Settings** → **Advanced**
3. Enable **"Force rebuild without cache"**
4. Click **Redeploy**

---

## Step 5: Manual Restart

After fixing the session file:

1. In Coolify, click **Restart** (not just redeploy)
2. Wait for container to fully start
3. Check logs for success messages
4. Refresh diagnostics page

---

## Common Issues & Fixes

### Issue: "Session file not found"

**Possible causes:**
1. File not uploaded to volume
2. File in wrong location (not in `/data/`)
3. Volume not mounted correctly

**Fix:**
- Upload to `/data/telethon_session.session` in volume
- OR set `TG_SESSION=/your/custom/path` env var

### Issue: "Session invalid or incomplete"

**Possible causes:**
1. Generated with different API_ID/API_HASH
2. File corrupted during upload
3. Session expired or revoked

**Fix:**
- Delete old session
- Generate new one with EXACT credentials from Coolify
- Upload fresh file

### Issue: "Client started but not connected"

**Possible causes:**
1. Network issues
2. Telegram API rate limiting
3. Session revoked from another device

**Fix:**
- Check container network connectivity
- Wait a few minutes and restart
- Regenerate session if persists

---

## Expected Behavior After Fix

### **Diagnostics Page Should Show:**
- Started: ✅ Yes
- Connected: ✅ Yes
- Client Type: User (not Bot)

### **Dashboard Should Show:**
- Media being downloaded and approved
- Total Media count increasing
- Approved Media > 0

### **Logs Should Show:**
```
✅ Telethon client connected successfully
✅ Logged in as: YourName (ID: 123456789)
✅ User account detected - pulling historical media
✅ Pulling historical media from channel: @rhapsodylibrary
✅ Pulled 150 audio/PDF messages from @rhapsodylibrary
```

---

## Quick Checklist

- [ ] Session file exists in Coolify volume
- [ ] Session file size is ~28KB (not empty)
- [ ] Session generated with correct API_ID/API_HASH
- [ ] TG_BOT_TOKEN is NOT set (or empty)
- [ ] TG_API_ID and TG_API_HASH are set correctly
- [ ] Latest code deployed (commit e820ac1)
- [ ] Container logs checked for errors
- [ ] Application restarted after changes

---

## Still Not Working?

**Share the following:**
1. Container logs (first 100 lines after startup)
2. Screenshot of Coolify environment variables (hide sensitive values)
3. Screenshot of volume contents
4. Output of diagnostics page

This will help identify the exact issue!

---

**Last Updated:** December 3, 2024
