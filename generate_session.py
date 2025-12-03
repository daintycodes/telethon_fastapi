#!/usr/bin/env python3
"""
Generate Telethon User Session File

This script creates a telethon_session.session file that can be used
for user account authentication (allows pulling historical messages).

IMPORTANT: Use the EXACT same API_ID and API_HASH as in your Coolify deployment!
"""

from telethon import TelegramClient
import asyncio
import sys

# ⚠️ CRITICAL: These MUST match your Coolify environment variables EXACTLY
# Get these from your Coolify dashboard → Environment Variables
API_ID = 26694786  # Your TG_API_ID from Coolify
API_HASH = input("Enter your TG_API_HASH from Coolify: ").strip()

if not API_HASH:
    print("❌ Error: API_HASH cannot be empty!")
    sys.exit(1)

print("\n" + "="*60)
print("📱 Telethon User Session Generator")
print("="*60)
print(f"\nAPI_ID: {API_ID}")
print(f"API_HASH: {API_HASH[:10]}...")
print("\n⚠️  Make sure these match your Coolify environment variables!")
print("\nThis will prompt you for:")
print("  1. Phone number (with country code, e.g., +1234567890)")
print("  2. Verification code (sent to your Telegram app)")
print("  3. 2FA password (if you have it enabled)")
print("\n" + "="*60 + "\n")

# Create client
client = TelegramClient('telethon_session', API_ID, API_HASH)

async def main():
    try:
        print("🔄 Connecting to Telegram...")
        await client.start()
        
        print("\n✅ Session created successfully!")
        print("📄 File created: telethon_session.session")
        
        # Get user info
        me = await client.get_me()
        print(f"\n👤 Logged in as:")
        print(f"   Name: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username}" if me.username else "   Username: (none)")
        print(f"   ID: {me.id}")
        print(f"   Phone: {me.phone}")
        
        await client.disconnect()
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Next steps:")
        print("="*60)
        print("\n1. Upload 'telethon_session.session' to Coolify:")
        print("   - Go to your app → Storage/Volumes")
        print("   - Upload the file to your persistent volume")
        print("   - Make sure it's in the root of the volume")
        print("\n2. In Coolify Environment Variables:")
        print("   - REMOVE or empty: TG_BOT_TOKEN")
        print("   - KEEP: TG_API_ID and TG_API_HASH")
        print("   - OPTIONAL: Set TG_SESSION=telethon_session")
        print("\n3. Redeploy your application")
        print("\n4. Check logs - should see:")
        print("   '✅ Logged in as: YourName (ID: ...)'")
        print("   'User account detected - pulling historical media'")
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCommon issues:")
        print("  - Wrong phone number format (need country code: +1234567890)")
        print("  - Invalid verification code")
        print("  - Wrong 2FA password")
        print("  - API_ID/API_HASH don't match your Telegram app")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
