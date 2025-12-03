#!/bin/bash
# Deployment Verification Script for Telethon FastAPI
# Run this after deploying to Coolify to verify everything is working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"

echo "========================================="
echo "Telethon FastAPI Deployment Verification"
echo "========================================="
echo ""
echo "Base URL: $BASE_URL"
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health" || echo "")
if [ -n "$HEALTH_RESPONSE" ]; then
    print_status 0 "Health endpoint accessible"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
    
    # Check Telethon status
    TELETHON_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"telethon_client":"[^"]*"' | cut -d'"' -f4)
    if [ "$TELETHON_STATUS" = "connected" ]; then
        print_status 0 "Telethon client is connected"
    else
        print_status 1 "Telethon client status: $TELETHON_STATUS"
        print_warning "Check TG_BOT_TOKEN environment variable or session file"
    fi
else
    print_status 1 "Health endpoint not accessible"
    echo "Error: Cannot reach $BASE_URL/health"
    exit 1
fi
echo ""

# Test 2: Authentication
echo "Test 2: Authentication"
echo "----------------------"
if [ -z "$ADMIN_PASSWORD" ]; then
    print_warning "ADMIN_PASSWORD not set, skipping authentication tests"
    print_warning "Set ADMIN_PASSWORD environment variable to test authentication"
    echo ""
else
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$ADMIN_USERNAME&password=$ADMIN_PASSWORD" || echo "")
    
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        print_status 0 "Authentication successful"
        TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        echo "Token obtained: ${TOKEN:0:20}..."
    else
        print_status 1 "Authentication failed"
        echo "$LOGIN_RESPONSE"
        print_warning "Create admin user or check credentials"
        TOKEN=""
    fi
    echo ""
fi

# Test 3: Channels Endpoint
echo "Test 3: Channels Endpoint"
echo "-------------------------"
CHANNELS_RESPONSE=$(curl -s "$BASE_URL/api/channels/" || echo "")
if [ -n "$CHANNELS_RESPONSE" ]; then
    print_status 0 "Channels endpoint accessible"
    CHANNEL_COUNT=$(echo "$CHANNELS_RESPONSE" | grep -o '\[' | wc -l)
    if [ "$CHANNEL_COUNT" -gt 0 ]; then
        NUM_CHANNELS=$(echo "$CHANNELS_RESPONSE" | grep -o '"username"' | wc -l)
        print_status 0 "Found $NUM_CHANNELS active channel(s)"
        echo "$CHANNELS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CHANNELS_RESPONSE"
    else
        print_warning "No channels configured yet"
        echo "Add channels via admin dashboard or API"
    fi
else
    print_status 1 "Channels endpoint not accessible"
fi
echo ""

# Test 4: Media Endpoint (if authenticated)
if [ -n "$TOKEN" ]; then
    echo "Test 4: Media Endpoint"
    echo "----------------------"
    MEDIA_RESPONSE=$(curl -s "$BASE_URL/api/media/pending" \
        -H "Authorization: Bearer $TOKEN" || echo "")
    
    if echo "$MEDIA_RESPONSE" | grep -q "items"; then
        print_status 0 "Media endpoint accessible"
        PENDING_COUNT=$(echo "$MEDIA_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
        if [ -n "$PENDING_COUNT" ] && [ "$PENDING_COUNT" -gt 0 ]; then
            print_status 0 "Found $PENDING_COUNT pending media file(s)"
        else
            print_warning "No pending media files"
            echo "Media will appear after channels are added and messages are pulled"
        fi
    else
        print_status 1 "Media endpoint error"
        echo "$MEDIA_RESPONSE"
    fi
    echo ""
fi

# Test 5: Database Connection
echo "Test 5: Database Connection"
echo "---------------------------"
# This is indirect - if health check works, DB is likely OK
# But we can check if we got valid JSON responses
if [ -n "$CHANNELS_RESPONSE" ] && echo "$CHANNELS_RESPONSE" | python3 -m json.tool >/dev/null 2>&1; then
    print_status 0 "Database appears to be connected (inferred from API responses)"
else
    print_warning "Cannot verify database connection"
fi
echo ""

# Summary
echo "========================================="
echo "Summary"
echo "========================================="
echo ""

if [ "$TELETHON_STATUS" = "connected" ]; then
    echo -e "${GREEN}✓ Deployment appears healthy${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Add Telegram channels via admin dashboard or API"
    echo "2. Monitor logs for media pulling activity"
    echo "3. Approve pending media files"
    echo "4. Test media download URLs"
else
    echo -e "${RED}✗ Issues detected${NC}"
    echo ""
    echo "Action required:"
    echo "1. Check application logs in Coolify"
    echo "2. Verify TG_BOT_TOKEN or session file is configured"
    echo "3. Verify TG_API_ID and TG_API_HASH are correct"
    echo "4. Check network connectivity to Telegram servers"
fi

echo ""
echo "For detailed troubleshooting, see MEDIA_PULLING_FIXES.md"
echo ""
