# Supabase to Local PostgreSQL Migration Summary

## What Changed

This migration removes the Supabase dependency and replaces it with a local PostgreSQL database and custom JWT authentication.

### Backend Changes

1. **New Files:**
   - `backend/auth.py` - Custom JWT authentication module
   - `backend/alembic.ini` - Alembic configuration
   - `backend/alembic/env.py` - Alembic environment
   - `backend/alembic/script.py.mako` - Migration template
   - `backend/create_migration.py` - Helper script for migrations
   - `.env.example` - Example environment configuration

2. **Modified Files:**
   - `backend/main.py`:
     - Removed Supabase JWT verification
     - Added custom JWT authentication
     - Added new auth endpoints:
       - `POST /api/auth/signup`
       - `POST /api/auth/login`
       - `GET /api/auth/me`
   - `backend/database.py` - No changes needed (already using SQLAlchemy)
   - `requirements.txt` - Added `alembic` and `bcrypt`

3. **Environment Variables:**
   - ❌ Removed: `SUPABASE_JWT_SECRET`
   - ✅ Added: `JWT_SECRET` (for custom JWT tokens)
   - ✅ Kept: `DATABASE_URL` (now points to local PostgreSQL)

### Frontend Changes

1. **New Files:**
   - `frontend/src/utils/authClient.js` - Custom authentication client

2. **Modified Files:**
   - `frontend/src/utils/supabaseClient.js` - Now exports authClient for backward compatibility
   - `frontend/src/utils/useAuth.js` - Uses authClient instead of Supabase

3. **Environment Variables:**
   - ✅ Added: `VITE_API_URL` (backend API URL)
   - ❌ No longer needed: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

### Database Changes

- **Database**: PostgreSQL (local instance)
- **Migrations**: Alembic (version-controlled migrations)
- **Schemas**:
  - `public` - Default schema
  - `main` - Core application data
  - `user_data` - User activity tracking
  - `dashboard` - Dashboard and analytics

## Authentication Flow

### Before (Supabase)
1. Frontend calls Supabase Auth API
2. Supabase returns JWT token
3. Backend verifies Supabase JWT (without signature verification)

### After (Custom Auth)
1. Frontend calls backend `/api/auth/login` or `/api/auth/signup`
2. Backend validates credentials against local database
3. Backend generates and returns custom JWT token
4. Frontend stores token in localStorage
5. Frontend sends token in Authorization header for authenticated requests

## User Data Migration

**Note:** This migration sets up a new local database. If you have existing user data in Supabase that needs to be migrated, you'll need to:

1. Export data from Supabase
2. Transform data to match local schema
3. Import into local PostgreSQL database

User passwords will need to be reset since Supabase uses different hashing.

## Benefits

1. **No External Dependencies**: No reliance on Supabase service
2. **Full Control**: Complete control over database and authentication
3. **Cost Savings**: No Supabase subscription needed
4. **Data Privacy**: All data stored locally
5. **Easier Development**: No need for Supabase credentials
6. **Migration Support**: Alembic provides version-controlled schema migrations

## Quick Start

```bash
# 1. Create database
createdb clyvara_dev

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
cd backend
python create_migration.py init
python create_migration.py upgrade

# 5. Start backend
uvicorn main:app --reload

# 6. Start frontend
cd ../frontend
npm install
npm run dev
```

## Testing the Migration

1. Create a test user:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com",
    "full_name": "Test User"
  }'
```

2. Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

3. Get user info (use token from login response):
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Files Changed Summary

### Backend
- ✅ Created: 6 new files
- ✏️ Modified: 2 files
- 📦 New dependencies: alembic, bcrypt

### Frontend
- ✅ Created: 1 new file
- ✏️ Modified: 2 files
- 📦 Dependencies: No changes (can optionally remove @supabase/supabase-js)

### Documentation
- ✅ Created: DATABASE_SETUP.md (detailed setup guide)
- ✅ Created: MIGRATION_SUMMARY.md (this file)
- ✏️ Updated: .env.example

## Next Steps

1. Review [DATABASE_SETUP.md](./DATABASE_SETUP.md) for detailed setup instructions
2. Set up local PostgreSQL database
3. Configure environment variables
4. Run database migrations
5. Test authentication endpoints
6. Update any existing code that directly uses Supabase (if any)
7. Remove Supabase credentials from production environment

## Rollback Plan

If you need to rollback to Supabase:

1. Keep the old Supabase credentials
2. Revert changes to `main.py`, `supabaseClient.js`, and `useAuth.js`
3. Update `.env` to use `SUPABASE_JWT_SECRET` instead of `JWT_SECRET`
4. Reinstall `@supabase/supabase-js` in frontend

**Note:** The database schema remains the same, so data can be migrated back if needed.
