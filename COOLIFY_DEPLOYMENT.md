# Coolify Deployment Guide for Telethon FastAPI

## Pre-deployment checklist

Ensure you have the following prepared:
- Postgres instance running with credentials (user, password, host, port, database name)
- MinIO instance running with credentials (endpoint, access key, secret key, bucket names)
- Telegram API credentials (API_ID and API_HASH from https://my.telegram.org)
- A strong JWT_SECRET for token signing
- (Optional) Sentry DSN for error monitoring
- (Optional) Admin API key for legacy authentication

## Step 1: Add GitHub Repository to Coolify

1. Login to Coolify dashboard
2. Click **"New Project"** → **"Create a new application"**
3. Select **"Git repository"**
4. Connect your GitHub account and select the `telethon_fastapi` repository
5. Select the `main` branch

## Step 2: Configure Docker Build Settings

1. In the application settings, under **"Build Settings"**:
   - **Docker file**: Leave as default (`Dockerfile`)
   - **Base directory**: Leave empty (root of repo)
   - Coolify will auto-detect and use the Dockerfile

2. Click **"Deploy"** to allow Coolify to build the image (first build may take 2-3 minutes)

## Step 3: Set Environment Variables in Coolify

After the initial build, navigate to **"Environment"** tab and add these variables:

### Required variables:
- `TG_API_ID`: Your Telegram API ID (integer)
- `TG_API_HASH`: Your Telegram API Hash (string)
- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/dbname`
  - Example: `postgresql://telethon:my_password@postgres.example.com:5432/telethon_db`
- `S3_ENDPOINT`: MinIO endpoint
  - Format: `http://host:port` or `https://host:port`
  - Example: `http://minio.example.com:9000`
- `S3_ACCESS_KEY`: MinIO access key
- `S3_SECRET_KEY`: MinIO secret key

### Optional variables:
- `TG_SESSION`: Telethon session name (default: `telethon_session`)
- `S3_BUCKET_AUDIO`: Audio bucket name (default: `audio`)
- `S3_BUCKET_PDF`: PDF bucket name (default: `pdf`)
- `ADMIN_API_KEY`: Legacy API key for admin endpoints (optional; use JWT token instead)
- `JWT_SECRET`: Secret for JWT signing (default: `change-this-secret` — set a strong value)
- `LOG_LEVEL`: Logging level (default: `INFO`; options: `DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `SENTRY_DSN`: Sentry error tracking (optional)
- `SENTRY_TRACES_SAMPLE_RATE`: Sentry trace sampling (default: `0.0`)

## Step 4: Configure Persistent Volumes

Navigate to **"Volumes"** tab and add these:

1. **Telethon Session Volume**:
   - **Container Path**: `/app`
   - **Volume Type**: `Named Volume`
   - **Volume Name**: `telethon_session`
   - **Size**: 1-2 GB (for session files)

2. (Optional) **Temporary Downloads Volume**:
   - **Container Path**: `/app/downloads`
   - **Volume Type**: `Named Volume`
   - **Volume Name**: `telethon_downloads`
   - **Size**: 10-50 GB (depends on expected file size)

## Step 5: Configure Networking & Ports

1. **Ports** tab:
   - **Container Port**: `8000`
   - **Public Port**: `8000` (or let Coolify auto-assign; recommended: use a reverse proxy)
   - **Protocol**: `HTTP`

2. (Optional) **Reverse Proxy**:
   - If you want HTTPS and a domain, configure Coolify's reverse proxy (or use Nginx/Traefik externally)
   - Recommended domain: `your-domain.com/api`

## Step 6: Configure Health Check

Navigate to **"Health Checks"** tab:
- **Health Check URL**: `http://localhost:8000/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

This allows Coolify to monitor app status and auto-restart if unhealthy.

## Step 7: Deploy

1. In **"General"** settings, enable **"Auto Deploy"** if you want automatic redeploy on git push
2. Click **"Deploy"** or **"Redeploy"** to start the deployment
3. Monitor the logs in **"Logs"** tab to ensure:
   - Alembic migrations run successfully (`Running Alembic migrations...`)
   - Telethon client starts (`Telethon client started...`)
   - App starts listening (`Application startup complete`)

## Step 8: Post-Deployment: Create Admin User

After the app is deployed and running, create an admin user to access the admin dashboard:

### Option A: Using Coolify Terminal

1. In Coolify, go to **"Console"** or **"Terminal"**
2. Run the following Python snippet:
```bash
python - <<'PY'
from app.database import SessionLocal
from app import crud
db = SessionLocal()
crud.create_user(db, 'admin', 'YourStrongPasswordHere', is_admin=True)
db.close()
print('Admin user created successfully!')
PY
```

### Option B: Using SSH (if you have shell access to the VPS)

```bash
docker exec telethon-fastapi python - <<'PY'
from app.database import SessionLocal
from app import crud
db = SessionLocal()
crud.create_user(db, 'admin', 'YourStrongPasswordHere', is_admin=True)
db.close()
print('Admin user created successfully!')
PY
```

## Step 9: Smoke Testing

After deployment and admin user creation, run these tests:

### Test 1: Health check
```bash
curl https://your-domain.com/health
# Expected response: {"status":"healthy"}
```

### Test 2: Login (get JWT token)
```bash
curl -X POST https://your-domain.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=YourStrongPasswordHere"
# Expected response: {"access_token":"eyJ0eXAiOiJKV1QiL...","token_type":"bearer"}
```

### Test 3: Access admin dashboard
```bash
# Open in browser
https://your-domain.com/admin
# Login with admin credentials
# You should see "Pending Media" and "Preview Telegram Channel" sections
```

### Test 4: List channels (public endpoint)
```bash
curl https://your-domain.com/api/channels/
# Expected response: [] (empty if no channels added yet)
```

### Test 5: Add a channel (admin-protected)
```bash
TOKEN="your_jwt_token_from_step2"
curl -X POST "https://your-domain.com/api/channels/?username=@testchannel" \
  -H "Authorization: Bearer $TOKEN"
# Expected response: {"id":1,"username":"@testchannel","active":true}
```

## Step 10: Troubleshooting

### Issue: App fails to start ("Telethon client failed to authenticate")
- **Cause**: Telegram session not authenticated yet or invalid credentials
- **Fix**: On first deploy, Telethon may need interactive login. Check logs for "phone number" prompt. You may need to run an interactive session to authenticate, then redeploy.

### Issue: "Failed to ensure buckets" error in logs
- **Cause**: MinIO endpoint unreachable or credentials invalid
- **Fix**: Verify `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` are correct and MinIO is accessible from the VPS

### Issue: "Database connection refused"
- **Cause**: PostgreSQL endpoint unreachable or credentials invalid
- **Fix**: Verify `DATABASE_URL` and ensure Postgres is running and accessible from the VPS

### Issue: Migrations fail on deploy
- **Cause**: Alembic migration error or DB schema mismatch
- **Fix**: Check logs for migration error message. If needed, manually run alembic revision or reset the DB.

### Issue: Admin login fails
- **Cause**: Admin user not created or wrong password
- **Fix**: Re-run the admin user creation step (Step 8)

## Step 11: Monitoring & Maintenance

### View Logs
- In Coolify, go to **"Logs"** to see real-time app output
- Monitor for errors, especially during media downloads and S3 uploads

### Monitor Resource Usage
- Check CPU, memory, and disk usage in Coolify **"Stats"** tab
- If memory usage grows, consider increasing container memory limit or optimizing media processing

### Update & Redeploy
- Push updates to the `main` branch on GitHub
- If **"Auto Deploy"** is enabled, Coolify will automatically redeploy
- Otherwise, click **"Redeploy"** in the Coolify dashboard

### Backup Data
- Regularly backup the Telethon session volume (contains authentication)
- Backup MinIO buckets if needed
- Backup PostgreSQL database

## Summary

Your Telethon FastAPI app is now deployed on Coolify with:
- ✅ Automatic migrations on startup
- ✅ Resilient S3 bucket creation with retries
- ✅ Production-ready single-worker Uvicorn
- ✅ Health checks for auto-restart
- ✅ Admin dashboard for managing channels and approving media
- ✅ JWT-based authentication
- ✅ Persistent session storage for Telethon
- ✅ Integrated logging and optional Sentry error monitoring
