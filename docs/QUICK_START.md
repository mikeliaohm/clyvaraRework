# Quick Start — Local Development

Minimum setup to run Clyvara locally. No cloud services required.

---

## 1. Prerequisites

| Tool | Required version |
|------|-----------------|
| Python | 3.10+ |
| Node.js | 20.19+ or 22+ |
| PostgreSQL | 12+ (with pgvector) |

### Install pgvector

The RAG pipeline requires the [pgvector](https://github.com/pgvector/pgvector) PostgreSQL extension.

**Linux (Ubuntu/Debian):**

Install PostgreSQL, build tools, and the PostgreSQL server headers for your version:

```bash
sudo apt update
sudo apt install -y postgresql postgresql-server-dev-17 build-essential git
```

If you are on PostgreSQL 16 or another version, replace `postgresql-server-dev-17`
with the matching package for your installed server version.

Build and install `pgvector` from source:

```bash
git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
cd ..
```

**macOS (Homebrew PostgreSQL):**

```bash
brew install pgvector
```

**macOS (EDB / system PostgreSQL at `/Library/PostgreSQL/`):**

If your running PostgreSQL server uses `/Library/PostgreSQL/<version>/` (check with
`psql -c "SHOW data_directory;"`), Homebrew installs pgvector to the wrong location.
Copy the files manually after `brew install pgvector`:

```bash
PG_VERSION=17  # adjust to your version

sudo cp /opt/homebrew/lib/postgresql@${PG_VERSION}/vector.dylib \
        /Library/PostgreSQL/${PG_VERSION}/lib/postgresql/

sudo cp /opt/homebrew/share/postgresql@${PG_VERSION}/extension/vector.control \
        /Library/PostgreSQL/${PG_VERSION}/share/postgresql/extension/

sudo cp /opt/homebrew/share/postgresql@${PG_VERSION}/extension/vector--*.sql \
        /Library/PostgreSQL/${PG_VERSION}/share/postgresql/extension/
```

**Verify** (after creating the database in step 5):

```bash
psql -d clyvara_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Install Node via nvm if needed:

```bash
nvm install 22
nvm use 22
```

---

## 2. Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 4. Environment variables

Create `.env` (at repo-root) before running migrations:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/clyvara_dev

# Auth: 'local' for dev (no Supabase needed), 'supabase' for production
AUTH_MODE=local

JWT_SECRET=<run: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Only needed when AUTH_MODE=supabase
SUPABASE_JWT_SECRET=

# Optional — AI features won't work without this
OPENAI_API_KEY=<your_key>

# Optional — file uploads fall back to local without this
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-2
S3_BUCKET_NAME=clyvara-uploads

# Optional — admin endpoint fallback key
ADMIN_API_KEY=local_admin_key_123
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

---

## 5. Local PostgreSQL database

```bash
# Create the database
psql postgres -c "CREATE DATABASE clyvara_dev;"
```

Then apply the schema migrations:

```bash
source .venv/bin/activate
cd backend
python create_migration.py upgrade
```

If the first migration failed before this fix, rerun `python create_migration.py upgrade`.
If your database was left in a partial state, drop and recreate `clyvara_dev` first.

---

## 6. Create accounts for testing

With `AUTH_MODE=local` the backend provides its own auth endpoints — no
external service required. Start the backend first (see step 7), then:

### Register a user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

`username` and `full_name` are auto-derived from the email if omitted.

### Log in and get a token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

The response includes `access_token`. Use it as `Authorization: Bearer <token>` on
protected endpoints.

### Grant admin role

After registering an admin account, grant the role directly in the database:

```bash
psql $DATABASE_URL -c "
  INSERT INTO public.roles (name, description)
    VALUES ('admin', 'Administrator')
    ON CONFLICT (name) DO NOTHING;
  INSERT INTO public.user_roles (user_id, role_id)
    SELECT u.id, r.id
    FROM public.users u, public.roles r
    WHERE u.email = 'admin@example.com' AND r.name = 'admin'
    ON CONFLICT DO NOTHING;
"
```

### Production auth

In production, set `AUTH_MODE=supabase` and `SUPABASE_JWT_SECRET` to your
project's JWT secret (found in the Supabase dashboard). The local
login/register routes are disabled — Supabase handles user creation and
token issuance. The backend only validates incoming JWTs.

---

## 7. Run the app

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

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |

---

## 8. Migration command reference

```bash
cd backend

python create_migration.py init          # generate initial migration from models
python create_migration.py auto "msg"    # generate migration for model changes
python create_migration.py upgrade       # apply all pending migrations
python create_migration.py downgrade     # rollback one migration
python create_migration.py history       # show migration history
python create_migration.py current       # show current version
```
