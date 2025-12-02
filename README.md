# telethon_fastapi
telethon_fastapi for audio and pdf S3 Pipeline

## Admin UI & Auth

- Start the server and open `/admin` to access the minimal admin dashboard.
- Create a user (see next section) and login to approve media and manage channels.

## Database migrations (Alembic)

1. Install alembic in your environment: `pip install alembic`
2. Create initial migration (already included as `alembic/versions/0001_initial.py`) or autogenerate using:

```bash
alembic revision --autogenerate -m "create initial tables"
```

3. Apply migrations:

```bash
alembic upgrade head
```

## Authentication

- This project supports JWT-based authentication (`/auth/login`) and a legacy API key via `ADMIN_API_KEY`.
- Use the admin dashboard to login (OAuth2 password flow) and receive a Bearer token.
