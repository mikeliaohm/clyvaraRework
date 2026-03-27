# Staging — Hooking Up External Services

This document covers what needs to be configured before the application is ready to
run in a staging or production environment. Local development requires none of these.

---

## Services required

| Service | Purpose | Status |
|---------|---------|--------|
| AWS RDS (PostgreSQL) | Primary database | Existing instance available |
| AWS S3 | File uploads (materials) | Needs bucket + IAM credentials |
| OpenAI API | Embeddings, chat, question generation | Needs API key |
| Google OAuth | Social login via fastapi-users | Not yet wired |
| Domain + TLS | HTTPS for API and frontend | Needs setup |

---

## 1. AWS RDS (PostgreSQL)

The production database already exists on AWS RDS (us-east-2).

**Steps:**

1. Confirm the RDS security group allows inbound traffic from the backend host on port 5432.
2. Point `DATABASE_URL` at the RDS endpoint:

```env
DATABASE_URL=postgresql+psycopg://<user>:<password>@<rds-endpoint>.us-east-2.rds.amazonaws.com:5432/<dbname>
```

3. Run migrations against it once:

```bash
source .venv/bin/activate
cd backend
python create_migration.py upgrade
```

---

## 2. AWS S3 (file uploads)

Used by the `/api/upload` and `/api/admin/upload-system-material` endpoints to store
uploaded PDFs and documents.

**Steps:**

1. Create an S3 bucket (e.g. `clyvara-uploads`) in `us-east-2`.
2. Create an IAM user with the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::clyvara-uploads",
        "arn:aws:s3:::clyvara-uploads/*"
      ]
    }
  ]
}
```

3. Add credentials to `.env`:

```env
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=us-east-2
S3_BUCKET_NAME=clyvara-uploads
```

---

## 3. OpenAI API

Used for:
- Generating text embeddings for RAG search (`text-embedding-3-small`)
- Chat responses (`gpt-3.5-turbo`)
- Learning plan question generation (`gpt-4o-mini`)
- Care plan AI recommendations (`gpt-4o-mini`)

**Steps:**

1. Create an API key at https://platform.openai.com
2. Add to `.env`:

```env
OPENAI_API_KEY=sk-...
```

Without this key the AI features return 503. The rest of the app (auth, profiles,
care plan CRUD, material browsing) continues to work.

---

## 4. Google OAuth (social login)

The "Continue with Google" button currently shows an alert in local mode. To wire it
up in staging/production, fastapi-users supports Google OAuth via `httpx-oauth`.

**Steps:**

1. Create OAuth credentials in Google Cloud Console:
   - Application type: Web application
   - Authorized redirect URI: `https://<api-domain>/api/fau/auth/google/callback`
   - Copy **Client ID** and **Client Secret**

2. Install the OAuth extra:

```bash
pip install "httpx-oauth[google]"
```

3. Add to `backend/fastapi_users_setup.py`:

```python
from httpx_oauth.clients.google import GoogleOAuth2

google_oauth_client = GoogleOAuth2(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
)
```

4. Register the OAuth router in `backend/main.py`:

```python
app.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        state_secret=os.getenv("JWT_SECRET"),
        redirect_url="https://<api-domain>/api/fau/auth/google/callback",
    ),
    prefix="/api/fau/auth/google",
    tags=["fastapi-users-auth"],
)
```

5. Add to `.env`:

```env
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
```

6. Update `GoogleSignInButton.jsx` to redirect to the OAuth start URL instead of
   showing the alert.

---

## 5. CORS — restrict to production domain

`backend/main.py` currently allows all localhost and private-network origins.
For staging/production add the frontend domain to the regex or use `allow_origins`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.clyvara.com"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

---

## 6. Full production `.env`

```env
# Database
DATABASE_URL=postgresql+psycopg://<user>:<pass>@<rds-endpoint>.us-east-2.rds.amazonaws.com:5432/<db>

# Auth
JWT_SECRET=<strong-random-secret>
ADMIN_API_KEY=<strong-random-key>

# AI
OPENAI_API_KEY=sk-...

# Storage
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=us-east-2
S3_BUCKET_NAME=clyvara-uploads

# Google OAuth (when wired up)
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
```

---

## 7. Deployment

### Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Recommended: run behind Nginx with TLS termination (Let's Encrypt via Certbot), or
deploy as a container to ECS/Fargate.

### Frontend

```bash
cd frontend
VITE_API_URL=https://api.clyvara.com npm run build
```

Deploy `dist/` to S3 + CloudFront or any static host.

---

## 8. Post-deployment checklist

- [ ] `GET https://<api>/health` returns `{"status":"healthy","database":"connected"}`
- [ ] User registration and login work through the frontend
- [ ] File upload stores object in S3 (verify in AWS console)
- [ ] AI chat / question generation responds correctly
- [ ] Admin role granted to at least one account via psql
- [ ] CORS allows only the frontend domain
- [ ] JWT_SECRET and ADMIN_API_KEY are strong and not committed to git
