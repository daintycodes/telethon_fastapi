#!/usr/bin/env python3
"""
Debug the exact path resolution and client initialization logic 
that's used in the container.

This script mimics the exact same logic as telethon_client.py
to identify where the disconnect happens.
"""

import os
import logging
from telethon import TelegramClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Same values as in container
API_ID = 26694786
API_HASH = "34cea1013b192f5ded0d97c6fd9152dc"

def get_session_path():
    """EXACT same logic as in telethon_client.py"""
    env_session = os.getenv("TG_SESSION")
    if env_session:
        logger.info(f"Using session path from TG_SESSION: {env_session}")
        return env_session
    
    # Check /data first (new default)
    data_session = "/data/telethon_session"
    if os.path.exists(f"{data_session}.session"):
        logger.info(f"Found session file at: {data_session}.session")
        return data_session
    
    # Fallback to current directory
    local_session = "telethon_session"
    if os.path.exists(f"{local_session}.session"):
        logger.info(f"Found session file at: {local_session}.session")
        return local_session
    
    # Default to /data for new sessions
    logger.info(f"No existing session found, will create at: {data_session}")
    return data_session

def debug_session_resolution():
    """Debug the session path resolution"""
    print("\n" + "="*60)
    print("🔍 DEBUGGING SESSION PATH RESOLUTION")
    print("="*60)
    
    # Check environment variables
    print(f"\n📋 Environment Variables:")
    print(f"  TG_SESSION = {os.getenv('TG_SESSION', '(not set)')}")
    print(f"  TG_API_ID = {os.getenv('TG_API_ID', '(not set)')}")
    print(f"  TG_API_HASH = {os.getenv('TG_API_HASH', '(not set)')[:10]}...")
    print(f"  TELEGRAM_BOT_TOKEN = {os.getenv('TELEGRAM_BOT_TOKEN', '(not set)')}")
    print(f"  TG_BOT_TOKEN = {os.getenv('TG_BOT_TOKEN', '(not set)')}")
    
    # Check file locations
    print(f"\n📁 File System Check:")
    locations = [
        "/data/telethon_session.session",
        "/app/telethon_session.session", 
        "./telethon_session.session",
        "telethon_session.session"
    ]
    
    for location in locations:
        exists = os.path.exists(location)
        if exists:
            size = os.path.getsize(location)
            print(f"  ✅ {location} (exists, {size} bytes)")
        else:
            print(f"  ❌ {location} (not found)")
    
    # Test path resolution
    print(f"\n🎯 Session Path Resolution:")
    session_path = get_session_path()
    session_file = f"{session_path}.session"
    
    print(f"  Resolved path: {session_path}")
    print(f"  Full session file: {session_file}")
    print(f"  File exists: {os.path.exists(session_file)}")
    
    if os.path.exists(session_file):
        size = os.path.getsize(session_file)
        print(f"  File size: {size} bytes")
        
        # Check permissions
        readable = os.access(session_file, os.R_OK)
        print(f"  Readable: {readable}")
        
        # Check file type
        import stat
        st = os.stat(session_file)
        print(f"  Is regular file: {stat.S_ISREG(st.st_mode)}")
        print(f"  Permissions: {oct(st.st_mode)[-3:]}")
    
    return session_path, session_file

async def test_client_initialization():
    """Test the actual client initialization"""
    print("\n" + "="*60)
    print("🔍 DEBUGGING CLIENT INITIALIZATION")
    print("="*60)
    
    session_path, session_file = debug_session_resolution()
    
    if not os.path.exists(session_file):
        print(f"\n❌ Cannot test client - session file not found: {session_file}")
        return
    
    print(f"\n🔄 Creating TelegramClient...")
    print(f"  Session: {session_path}")
    print(f"  API_ID: {API_ID}")
    print(f"  API_HASH: {API_HASH[:10]}...")
    
    try:
        client = TelegramClient(session_path, API_ID, API_HASH)
        print(f"  ✅ Client created successfully")
        
        # Check initial connection state
        print(f"  Initial is_connected(): {client.is_connected()}")
        
        print(f"\n🔄 Attempting to connect...")
        await client.connect()
        print(f"  ✅ Connected to Telegram")
        print(f"  is_connected(): {client.is_connected()}")
        
        # Check authorization
        print(f"\n🔄 Checking authorization...")
        is_authorized = await client.is_user_authorized()
        print(f"  is_user_authorized(): {is_authorized}")
        
        if is_authorized:
            me = await client.get_me()
            print(f"\n👤 Account Info:")
            print(f"  Name: {me.first_name} {me.last_name or ''}")
            print(f"  Username: @{me.username}" if me.username else "  Username: (none)")
            print(f"  User ID: {me.id}")
            print(f"  Bot: {me.bot}")
        
        await client.disconnect()
        print(f"\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def debug_working_directory():
    """Debug current working directory and Python path"""
    print("\n" + "="*60)
    print("🔍 DEBUGGING WORKING DIRECTORY")
    print("="*60)
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {__file__}")
    print(f"Python executable: {os.sys.executable}")
    
    # List files in current directory
    print(f"\nFiles in current directory:")
    try:
        for item in sorted(os.listdir('.')):
            if os.path.isfile(item):
                size = os.path.getsize(item)
                print(f"  📄 {item} ({size} bytes)")
            else:
                print(f"  📁 {item}/")
    except Exception as e:
        print(f"  ❌ Error listing directory: {e}")

if __name__ == "__main__":
    import asyncio
    
    debug_working_directory()
    asyncio.run(test_client_initialization())
