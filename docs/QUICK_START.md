# Quick Start Guide

## ✅ Migration Complete!

Your application has been successfully migrated from Supabase to local PostgreSQL.

## What's Working Now

- ✅ Local PostgreSQL database with 54 tables across 4 schemas
- ✅ Custom JWT authentication (replaces Supabase Auth)
- ✅ Database migrations with Alembic
- ✅ Test user created: `test_user` / `test_password`

## Start the Application

### 1. Start Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 2. Start Frontend
```bash
cd frontend
npm install  # First time only
npm run dev
```

Frontend will be available at the port shown in terminal (usually http://localhost:5173)

## Test Authentication

You can test the authentication with the created test user:

**Username:** `test_user`
**Password:** `test_password`

Or create a new account through the signup page.

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new account
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (requires auth)

### Testing with curl

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "test_password"}'
```

**Get User Info (use token from login):**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Database Schema

- **public** - System tables (sessions, OAuth, biometric data, etc.)
- **main** - Core app data (users, courses, materials, care plans)
- **user_data** - User activity (chat messages, interactions)
- **dashboard** - Dashboard and analytics

## Environment Variables

Required in `.env`:
```bash
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/clyvara_dev
JWT_SECRET=your_jwt_secret_here
OPENAI_API_KEY=your_openai_key_here
```

## Database Management

```bash
# Create new migration after model changes
python create_migration.py auto "description"

# Apply migrations
python create_migration.py upgrade

# Check current version
python create_migration.py current

# Migration history
python create_migration.py history
```

## What Changed

1. **Removed:** Supabase dependency
2. **Added:** Local PostgreSQL database
3. **Added:** Custom JWT authentication
4. **Added:** Alembic migrations
5. **Updated:** Frontend to use backend auth

## Documentation

- [DATABASE_SETUP.md](./DATABASE_SETUP.md) - Detailed setup guide
- [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) - Migration details
- [.env.example](./.env.example) - Environment configuration

## Troubleshooting

**Database connection failed:**
```bash
# Check PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Test connection
python -c "from database import test_connection; test_connection()"
```

**Migration errors:**
```bash
# Check current migration status
python create_migration.py current

# Re-run migrations
python create_migration.py upgrade
```

## Next Steps

1. ✅ Database is set up and running
2. ✅ Test user created
3. ✅ Authentication system working
4. → Start backend and frontend
5. → Test login with test_user
6. → Create your own account
7. → Start building!

---

Need help? Check the detailed guides in:
- DATABASE_SETUP.md
- MIGRATION_SUMMARY.md
