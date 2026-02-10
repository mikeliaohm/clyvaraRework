# Database Setup Guide

This guide will help you migrate from Supabase to a local PostgreSQL database instance.

## Overview

The application has been migrated from Supabase to use:
- **Local PostgreSQL** database for data storage
- **Custom JWT authentication** instead of Supabase Auth
- **Alembic** for database migrations

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (for frontend)

## Step 1: Install PostgreSQL

### macOS (using Homebrew)
```bash
brew install postgresql@15
brew services start postgresql@15
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

## Step 2: Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE clyvara_dev;

# Create user (optional, or use default postgres user)
CREATE USER clyvara_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE clyvara_dev TO clyvara_user;

# Exit psql
\q
```

## Step 3: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and update the following values:

```bash
# PostgreSQL Database URL
# Format: postgresql+psycopg://username:password@host:port/database
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/clyvara_dev

# JWT Secret (generate a secure random key)
# Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your_generated_jwt_secret_here

# OpenAI API Key (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: AWS S3 for file storage (leave empty to use local storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-2
S3_BUCKET_NAME=clyvara-uploads

# Optional: Admin API Key for system material uploads
ADMIN_API_KEY=your_random_secret_key_here
```

### Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Install Python Dependencies

```bash
cd backend
pip install -r ../requirements.txt
```

## Step 5: Run Database Migrations

We use Alembic for database migrations. The migration system is already set up.

### Create Initial Migration

This will generate a migration file from your SQLAlchemy models:

```bash
cd backend
python create_migration.py init
```

This creates a migration file in `backend/alembic/versions/`. Review it to ensure it looks correct.

### Apply Migrations

Apply all pending migrations to create the database schema:

```bash
python create_migration.py upgrade
```

You should see output like:
```
Applying all pending migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema
✓ Database upgraded successfully!
```

### Verify Database

Test the database connection:

```bash
cd backend
python -c "from database import test_connection; test_connection()"
```

You should see: `Database connection successful!`

## Step 6: Configure Frontend

1. Create or update `frontend/.env`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Note: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are no longer needed
# The frontend now uses the backend API for authentication
```

2. The frontend has been updated to use the custom auth client (`authClient.js`) instead of Supabase.

## Step 7: Start the Application

### Start Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Start Frontend

```bash
cd frontend
npm install  # if not already done
npm run dev
```

The frontend will be available at the port shown in the terminal (usually `http://localhost:5173`)

## Migration Commands Reference

The `create_migration.py` script provides several useful commands:

```bash
# Create initial migration from models
python create_migration.py init

# Create a new migration with auto-detected changes
python create_migration.py auto "description of changes"

# Apply all pending migrations
python create_migration.py upgrade

# Rollback one migration
python create_migration.py downgrade

# Show migration history
python create_migration.py history

# Show current migration version
python create_migration.py current
```

## Authentication Changes

### Backend Changes
- Replaced Supabase JWT verification with custom JWT auth
- Added new endpoints:
  - `POST /api/auth/signup` - Create new user account
  - `POST /api/auth/login` - Login and get JWT token
  - `GET /api/auth/me` - Get current user info

### Frontend Changes
- Created new `authClient.js` to replace `@supabase/supabase-js`
- Updated `useAuth.js` hook to use the new auth client
- Updated `supabaseClient.js` for backward compatibility

### User Model
Users are now stored in the `users` table with the following fields:
- `id` - Auto-incrementing integer (primary key)
- `username` - Unique username
- `password` - Bcrypt hashed password
- `email` - User email
- `full_name` - Full name
- `specialty` - User specialty (optional)
- `graduation_year` - Graduation year (optional)
- `institution` - Institution (optional)
- `profile_completed` - Boolean flag
- `created_at` - Timestamp

## Removing Supabase Dependencies

Once you've verified everything works with the local setup, you can optionally remove Supabase dependencies:

### Backend
The `SUPABASE_JWT_SECRET` environment variable is no longer needed. You can remove it from your `.env` file.

### Frontend
The `@supabase/supabase-js` package is still installed but no longer used. You can optionally remove it:

```bash
cd frontend
npm uninstall @supabase/supabase-js
```

Note: The `supabaseClient.js` file has been updated to use the new auth client, so existing imports will continue to work.

## Troubleshooting

### Database Connection Issues

**Error: `connection refused`**
- Ensure PostgreSQL is running: `brew services list` (macOS) or `sudo systemctl status postgresql` (Linux)
- Check that the DATABASE_URL is correct in `.env`
- Verify the database exists: `psql -l`

**Error: `authentication failed`**
- Check username/password in DATABASE_URL
- For default PostgreSQL setup, try: `postgresql+psycopg://postgres:@localhost:5432/clyvara_dev`

### Migration Issues

**Error: `target database is not up to date`**
```bash
python create_migration.py current  # Check current version
python create_migration.py upgrade  # Apply pending migrations
```

**Error: `Can't locate revision`**
```bash
# Reset migrations (WARNING: This will drop all tables!)
# Only use in development
python create_migration.py downgrade base
python create_migration.py upgrade head
```

### Authentication Issues

**Error: `Invalid token`**
- Check that JWT_SECRET is set in backend `.env`
- Clear browser localStorage and try logging in again
- Verify the backend is using the same JWT_SECRET

**Error: `User not found`**
- The user might not exist in the local database
- Create a new account using the signup endpoint

## Database Schema

The database uses three schemas:
- `public` - Default schema (sessions, etc.)
- `main` - Core application tables (users, courses, materials, etc.)
- `user_data` - User activity tracking (chat messages, interactions, sessions)
- `dashboard` - Dashboard and analytics data

All schemas and tables are created automatically when you run migrations.

## Next Steps

1. ✅ Create local PostgreSQL database
2. ✅ Configure `.env` file
3. ✅ Run migrations to create schema
4. ✅ Start backend and frontend
5. ✅ Create a new user account
6. ✅ Test authentication and features

## Support

If you encounter issues:
1. Check the logs in the backend console
2. Verify database connection with `python -c "from database import test_connection; test_connection()"`
3. Check migration status with `python create_migration.py current`
4. Review this documentation for common troubleshooting steps
