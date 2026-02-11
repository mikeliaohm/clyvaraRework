# Hybrid Authentication Architecture

This application supports a **hybrid authentication approach**:
- **Development**: Local PostgreSQL + Custom JWT authentication
- **Production**: AWS RDS PostgreSQL + Supabase Auth (backend proxies)

## Key Benefits

✅ **Frontend never changes** - always calls backend API endpoints  
✅ **No Supabase SDK on frontend** - backend handles all auth  
✅ **Easy local development** - no cloud services needed  
✅ **Production-ready** - seamless switch to Supabase  

## How It Works

### Development Mode (`AUTH_MODE=local`)

```
User → Frontend → Backend (/api/auth/login) → Local PostgreSQL
                      ↓
                Custom JWT Token
                      ↓
                  Frontend
```

**Features:**
- Local PostgreSQL database
- Custom JWT token generation
- Bcrypt password hashing
- No external dependencies

### Production Mode (`AUTH_MODE=supabase`)

```
User → Frontend → Backend (/api/auth/login) → Supabase Auth API
                      ↓                              ↓
                      ↓                        Supabase JWT
                      ↓                              ↓
                  Frontend                  Backend verifies JWT
                                                    ↓
                                              AWS RDS PostgreSQL
```

**Features:**
- AWS RDS PostgreSQL (your existing database)
- Supabase Auth (OAuth, magic links, etc.)
- Backend proxies auth requests to Supabase
- Backend stores data in AWS RDS
- Frontend remains unchanged

## Environment Configuration

### Local Development

```bash
# .env
AUTH_MODE=local
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/clyvara_dev
JWT_SECRET=your_secret_key
```

### Production/Staging

```bash
# .env
AUTH_MODE=supabase
DATABASE_URL=postgresql+psycopg://username:password@your-rds-endpoint.us-east-2.rds.amazonaws.com:5432/clyvara_prod
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
```

## API Endpoints (Unchanged)

### Frontend always calls these endpoints:

```javascript
// Login
POST /api/auth/login
Body: { email, password }
Returns: { access_token, user }

// Signup
POST /api/auth/signup
Body: { email, password, full_name, username, ... }
Returns: { access_token, user }

// Get current user
GET /api/auth/me
Headers: { Authorization: "Bearer <token>" }
Returns: { id, email, username, ... }
```

**The backend implementation changes based on `AUTH_MODE`, but the API contract remains the same.**

## Authentication Flow

### Signup Flow

**Local Mode:**
1. Frontend → `POST /api/auth/signup`
2. Backend validates data
3. Backend hashes password with bcrypt
4. Backend stores user in local PostgreSQL
5. Backend generates custom JWT
6. Returns JWT to frontend

**Supabase Mode:**
1. Frontend → `POST /api/auth/signup`
2. Backend proxies to Supabase Auth API
3. Supabase creates user + generates JWT
4. Backend stores user metadata in AWS RDS PostgreSQL
5. Returns Supabase JWT to frontend

### Login Flow

**Local Mode:**
1. Frontend → `POST /api/auth/login`
2. Backend queries local PostgreSQL
3. Backend verifies password with bcrypt
4. Backend generates custom JWT
5. Returns JWT to frontend

**Supabase Mode:**
1. Frontend → `POST /api/auth/login`
2. Backend proxies to Supabase Auth API
3. Supabase validates credentials + generates JWT
4. Backend syncs user data to AWS RDS if needed
5. Returns Supabase JWT to frontend

### Request Authentication

**Local Mode:**
```python
# Backend verifies custom JWT
payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
```

**Supabase Mode:**
```python
# Backend verifies Supabase JWT
payload = jwt.decode(
    token, 
    SUPABASE_JWT_SECRET, 
    algorithms=["HS256"],
    audience="authenticated"
)
```

## Migration Guide

### Local → Production

1. **Set up Supabase project (Auth only)**
   - Create project at https://supabase.com
   - Enable Auth in Supabase dashboard
   - Note: Supabase URL, Anon Key, JWT Secret
   - **Important**: You're only using Supabase for Auth, not the database

2. **Ensure AWS RDS is ready**
   - Verify AWS RDS PostgreSQL is running (us-east-2)
   - Ensure security group allows connections from your backend
   - Get connection credentials

3. **Run migrations on AWS RDS**
   ```bash
   # Update DATABASE_URL to AWS RDS
   DATABASE_URL=postgresql+psycopg://username:password@your-rds-endpoint.us-east-2.rds.amazonaws.com:5432/clyvara_prod
   
   # Run migrations
   cd backend
   python create_migration.py upgrade
   ```

4. **Update environment variables**
   ```bash
   AUTH_MODE=supabase
   DATABASE_URL=postgresql+psycopg://username:password@your-rds-endpoint.us-east-2.rds.amazonaws.com:5432/clyvara_prod
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=...
   SUPABASE_JWT_SECRET=...
   ```

4. **Deploy backend** - No code changes needed!

5. **Frontend deployment** - No changes needed!

### Production → Local (for testing)

1. Change environment variables:
   ```bash
   AUTH_MODE=local
   DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/clyvara_dev
   ```

2. Restart backend - that's it!

## Frontend Integration

**No changes needed!** The frontend code remains identical:

```javascript
// authClient.js already proxies through backend
const response = await fetch(`${API_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

The `AUTH_MODE` environment variable controls everything on the backend.

## Security Considerations

### Local Mode
- ✅ Bcrypt password hashing (salt rounds: 12)
- ✅ JWT tokens with expiration
- ✅ HTTP-only auth (no localStorage password storage)
- ⚠️ Manual password reset implementation needed

### Supabase Mode
- ✅ All local mode security features
- ✅ Supabase's enterprise-grade auth
- ✅ Built-in rate limiting
- ✅ Email verification, magic links
- ✅ OAuth providers (Google, GitHub, etc.)
- ✅ Automatic password reset flows

## Testing Both Modes

```bash
# Test local mode
AUTH_MODE=local python -m pytest tests/

# Test Supabase mode (requires Supabase credentials)
AUTH_MODE=supabase python -m pytest tests/
```

## Troubleshooting

### "Invalid token" errors in production

**Check:**
- `SUPABASE_JWT_SECRET` is set correctly
- Token is from Supabase, not custom JWT
- Audience claim is "authenticated"

### Login works locally but not in production

**Check:**
- `AUTH_MODE=supabase` is set
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct
- Supabase Auth is enabled in dashboard

### User not found after Supabase login

**Solution:**
- Backend automatically creates user record on first login
- Check user metadata is syncing correctly

## Future Enhancements

Potential additions to the hybrid system:
- Social OAuth in both modes
- Passwordless authentication
- Multi-factor authentication (MFA)
- Session management improvements
- Token refresh handling

## Production Deployment

For complete production deployment guide with AWS RDS + Supabase Auth:
- See [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) - Step-by-step AWS RDS setup
- See [ARCHITECTURE.md](./ARCHITECTURE.md) - Complete architecture diagrams

Quick production setup summary:
1. Set up Supabase project (auth only)
2. Configure AWS RDS PostgreSQL
3. Run migrations on AWS RDS
4. Deploy backend with `AUTH_MODE=supabase`
5. Frontend works without changes
