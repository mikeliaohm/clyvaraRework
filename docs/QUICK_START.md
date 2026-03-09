# Quick Start (Local Development)

This guide covers the minimum setup for local development.

## 1. Create local environments (Python + Node)

### Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
```

### Node environment (required: Node 20.19+ or 22.12+)

Using `nvm`:

```bash
nvm install 20
nvm use 20
node -v
npm -v
```

## 2. Install dependencies (backend + frontend)

From repo root:

```bash
# backend dependencies
source .venv/bin/activate
pip install -r requirements.txt

# frontend dependencies
cd frontend
npm install
cd ..
```

## 3. Create a local database

### 3.1 Create PostgreSQL database

```bash
createdb clyvara_dev
```

or login to psql and create database directly:

```bash
psql postgres -c "CREATE DATABASE clyvara_dev;"
```

### 3.2 Configure `.env`

Update `.env` with at least:

```env
AUTH_MODE=local
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/clyvara_dev
JWT_SECRET=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">
OPENAI_API_KEY=<your_key_or_placeholder>
LOCAL_ADMIN_EMAILS=admin1@example.com
ADMIN_API_KEY=local_admin_key_123
```

### 3.3 Run migrations

```bash
source .venv/bin/activate
python backend/create_migration.py upgrade
```

## 4. Create dummy users (normal + admin workflow)

Auth is handled by **fastapi-users**. Use the register endpoint to create local accounts.
If the backend is not running yet, start it in another terminal first (`cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`).

### 4.1 Register a normal user

```bash
curl -X POST http://localhost:8000/api/fau/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@example.com",
    "password": "password123",
    "username": "normal_user",
    "full_name": "Normal User"
  }'
```

### 4.2 Log in and get a token

Login uses **form data** (OAuth2 password flow), not JSON:

```bash
curl -X POST http://localhost:8000/api/fau/auth/jwt/login \
  -F "username=user1@example.com" \
  -F "password=password123"
```

Response contains `access_token`. Use it as `Authorization: Bearer <token>` on protected endpoints.

### 4.3 Register an admin user

Register the account the same way as above, then grant the admin role directly in the database:

```bash
psql $DATABASE_URL -c "
  INSERT INTO main.roles (name, description)
    VALUES ('admin', 'Administrator')
    ON CONFLICT (name) DO NOTHING;
  INSERT INTO main.user_roles (user_id, role_id)
    SELECT u.id, r.id
    FROM main.users u, main.roles r
    WHERE u.email = 'admin1@example.com' AND r.name = 'admin'
    ON CONFLICT DO NOTHING;
"
```

Note: `ADMIN_API_KEY` remains as a temporary fallback for admin endpoints while the RBAC migration is in progress.

## 5. Run the app (backend + frontend)

### Backend

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (new terminal)

```bash
cd frontend
npm run dev
```

Local URLs:

- Backend API: `http://localhost:8000`
- Backend Docs: `http://localhost:8000/docs`
- Frontend: usually `http://localhost:5173`
