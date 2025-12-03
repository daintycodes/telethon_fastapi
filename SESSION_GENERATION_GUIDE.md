# 📱 User Session Generation Guide

## Why You Need This

**Bot accounts CANNOT pull historical messages from Telegram channels** due to API restrictions.

To pull historical media, you need a **user account session**.

---

## Prerequisites

Before starting, get these from your **Coolify dashboard**:

1. **TG_API_ID** (e.g., `26694786`)
2. **TG_API_HASH** (e.g., `abc123def456...`)

⚠️ **CRITICAL:** The session MUST be generated with the EXACT same API_ID and API_HASH as your deployment!

---

## Step-by-Step Instructions

### **Step 1: Install Telethon Locally**

On your local machine (not the server):

```bash
pip install telethon
```

### **Step 2: Run the Session Generator**

```bash
cd /path/to/telethon_fastapi
python generate_session.py
```

### **Step 3: Follow the Prompts**

The script will ask for:

1. **TG_API_HASH**: Paste from Coolify (will be hidden)
2. **Phone number**: Your Telegram phone with country code
   - Format: `+1234567890` (include the `+`)
   - Example: `+14155551234` for US number
3. **Verification code**: Check your Telegram app
   - You'll receive a code in "Telegram" official chat
   - Enter the 5-digit code
4. **2FA Password** (if enabled): Your cloud password
   - Only if you have two-factor authentication enabled
   - Skip if you don't have 2FA

### **Step 4: Verify Success**

You should see:

```
✅ Session created successfully!
📄 File created: telethon_session.session

👤 Logged in as:
   Name: John Doe
   Username: @johndoe
   ID: 123456789
   Phone: +1234567890
```

### **Step 5: Upload to Coolify**

**Option A: Via Coolify UI**
1. Go to Coolify → Your App → **Storage**
2. Find your persistent volume
3. Upload `telethon_session.session` to the volume root
4. Verify the file is there

**Option B: Via SCP (if you have SSH access)**
```bash
# Find your volume path in Coolify (usually something like):
# /var/lib/docker/volumes/coolify_xxxxx/_data

scp telethon_session.session user@your-server:/path/to/volume/
```

**Option C: Via Docker Volume**
```bash
# On your Coolify server
docker volume ls  # Find your volume name
docker run --rm -v VOLUME_NAME:/data -v $(pwd):/backup alpine cp /backup/telethon_session.session /data/
```

### **Step 6: Update Coolify Environment Variables**

In Coolify → Your App → Environment Variables:

**Remove or empty:**
- `TG_BOT_TOKEN` (leave blank or delete)

**Keep these (don't change):**
- `TG_API_ID=26694786`
- `TG_API_HASH=your_hash_here`

**Optional (if session file is in different location):**
- `TG_SESSION=/data/telethon_session` (or path to your session file)

### **Step 7: Redeploy**

Click **"Redeploy"** in Coolify.

### **Step 8: Verify in Logs**

Check application logs for:

```
✅ Starting Telethon client with existing session...
✅ Telethon client connected successfully
✅ Logged in as: YourName (ID: 123456789)
✅ User account detected - pulling historical media
✅ Pulling historical media from channel: @channel
✅ Pulled 150 audio/PDF messages from @channel
```

### **Step 9: Check Diagnostics**

Go to admin dashboard → Diagnostics tab:

**Should show:**
- Started: ✅ Yes
- Connected: ✅ Yes
- Client Type: **User** (not Bot)
- Total Media: > 0

---

## Troubleshooting

### ❌ "Invalid phone number"
- Make sure to include country code with `+`
- Format: `+1234567890` not `1234567890`

### ❌ "Phone number already in use"
- You can only have one session per phone number
- Log out from other devices or use a different number

### ❌ "Invalid code"
- Code expires in 5 minutes
- Request a new code and try again
- Make sure you're entering the code from Telegram app

### ❌ "Session file not found" (in deployment)
- Verify file was uploaded to correct volume
- Check file permissions (should be readable)
- Verify volume is mounted correctly in Coolify

### ❌ "EOFError: EOF when reading a line" (in deployment)
- Session file is invalid or from different API_ID/API_HASH
- Generate new session with EXACT same credentials
- Delete old session file and upload new one

### ❌ Still using bot after upload
- Make sure TG_BOT_TOKEN is removed/empty
- Verify session file is in correct location
- Check TG_SESSION environment variable path
- Redeploy after changes

---

## Security Notes

⚠️ **IMPORTANT:**

1. **Never commit** `telethon_session.session` to git
2. **Keep it secure** - it gives full access to your Telegram account
3. **Regenerate if compromised** - delete old session and create new one
4. **Use a dedicated account** if possible (not your personal Telegram)

---

## Session File Location

The session file should be placed in:
- **Coolify volume root** (recommended)
- Or specify custom path via `TG_SESSION` environment variable

Default paths checked:
1. `/data/telethon_session` (new default)
2. `telethon_session` (backward compatibility)
3. Custom path from `TG_SESSION` env var

---

## Comparison: Bot vs User Account

| Feature | Bot Account | User Account |
|---------|-------------|--------------|
| Pull historical messages | ❌ No | ✅ Yes |
| Receive new messages | ✅ Yes | ✅ Yes |
| Setup complexity | Easy (just token) | Medium (session file) |
| Authentication | Bot token | Phone + code |
| Rate limits | Lower | Higher |
| Access to private channels | Limited | Full (if member) |

---

## Need Help?

If you encounter issues:

1. Check the logs for specific error messages
2. Verify API_ID and API_HASH match exactly
3. Ensure session file is uploaded correctly
4. Try generating a fresh session file
5. Check Coolify volume mount configuration

---

**Last Updated:** December 3, 2024
