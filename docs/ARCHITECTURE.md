# Application Architecture

## Overview

Clyvara uses a **hybrid architecture** that separates concerns between development and production environments while keeping the frontend unchanged.

## Architecture Diagrams

### Development Environment (Local)

```
┌──────────┐
│ Frontend │ 
│ (React)  │ 
└────┬─────┘
     │ HTTP API calls
     │ /api/auth/*, /api/*
     ▼
┌──────────────────┐
│ Backend          │
│ (FastAPI)        │
│                  │
│ • Custom JWT     │
│ • Bcrypt hashing │
└────┬─────────────┘
     │
     │ SQLAlchemy ORM
     ▼
┌──────────────────┐
│ Local PostgreSQL │
│                  │
│ • Users          │
│ • Materials      │
│ • Care Plans     │
│ • All App Data   │
└──────────────────┘
```

**Key points:**
- ✅ No external dependencies
- ✅ Runs entirely offline
- ✅ Fast local development
- ✅ Full database control

### Production Environment (AWS + Supabase)

```
┌──────────┐
│ Frontend │ 
│ (React)  │ 
└────┬─────┘
     │ HTTP API calls
     │ /api/auth/*, /api/*
     ▼
┌──────────────────────────────────┐
│ Backend (FastAPI)                │
│                                  │
│ AUTH_MODE=supabase               │
│ ┌────────────────────────────┐  │
│ │ Auth Proxy                 │  │
│ │ • Routes to Supabase Auth  │  │
│ │ • Verifies Supabase JWT    │  │
│ └────┬────────────────────┬──┘  │
└──────┼────────────────────┼─────┘
       │                    │
       │                    │ SQLAlchemy ORM
       │                    ▼
       │              ┌──────────────┐
       │              │   AWS RDS    │
       │              │  PostgreSQL  │
       │              │              │
       │              │ • Users      │
       │              │ • Materials  │
       │              │ • Care Plans │
       │              │ • All Data   │
       │              └──────────────┘
       │
       │ HTTPS to Supabase
       ▼
┌──────────────────┐
│  Supabase Auth   │
│                  │
│ • User signup    │
│ • Login          │
│ • OAuth (Google) │
│ • Magic links    │
│ • JWT tokens     │
│ • Password reset │
└──────────────────┘
```

**Key points:**
- ✅ Supabase handles authentication (OAuth, magic links, etc.)
- ✅ AWS RDS stores all application data
- ✅ Backend proxies auth requests to Supabase
- ✅ Backend verifies Supabase JWT tokens
- ✅ Frontend code remains identical to development

## Why This Architecture?

### Development Benefits
- **Simplicity**: No cloud account or API keys required
- **Speed**: No network latency
- **Privacy**: All data stays local
- **Cost**: Zero external service costs
- **Debugging**: Full control over database and auth

### Production Benefits
- **Supabase Auth**: Enterprise-grade authentication
  - OAuth providers (Google, GitHub, etc.)
  - Magic links for passwordless login
  - Email verification
  - Password reset flows
  - Built-in rate limiting
  - Session management
  
- **AWS RDS**: Proven database infrastructure
  - Automatic backups
  - High availability with Multi-AZ
  - Performance Insights
  - Encryption at rest
  - Existing infrastructure integration
  - Your team already knows it

### Separation of Concerns
- **Authentication**: Supabase (best-in-class auth features)
- **Data Storage**: AWS RDS (your existing database)
- **Business Logic**: FastAPI backend (full control)
- **User Interface**: React frontend (framework agnostic)

## Data Flow

### User Signup (Production)
1. User enters email/password in frontend
2. Frontend calls `POST /api/auth/signup`
3. Backend forwards request to Supabase Auth API
4. Supabase creates user account and returns JWT
5. Backend stores user metadata in AWS RDS
6. Backend returns JWT to frontend
7. Frontend stores JWT in localStorage
8. Subsequent requests include JWT in Authorization header

### User Login (Production)
1. User enters email/password in frontend
2. Frontend calls `POST /api/auth/login`
3. Backend forwards request to Supabase Auth API
4. Supabase validates credentials and returns JWT
5. Backend optionally syncs user data to AWS RDS
6. Backend returns JWT to frontend
7. Frontend stores JWT and redirects to dashboard

### Authenticated Request (Production)
1. Frontend includes `Authorization: Bearer <jwt>` header
2. Backend extracts JWT from header
3. Backend verifies JWT using Supabase JWT secret
4. Backend extracts user_id from JWT payload
5. Backend queries AWS RDS for user data
6. Backend processes request and returns response

## Environment Configuration

### Development (.env)
```bash
AUTH_MODE=local
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/clyvara_dev
JWT_SECRET=random_secret_for_local_dev
OPENAI_API_KEY=your_openai_key
```

### Production (.env)
```bash
AUTH_MODE=supabase
DATABASE_URL=postgresql+psycopg://user:pass@rds-endpoint.us-east-2.rds.amazonaws.com:5432/clyvara_prod
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
OPENAI_API_KEY=your_openai_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-2
S3_BUCKET_NAME=clyvara-uploads
```

## Frontend Compatibility

The frontend uses a custom `authClient.js` that abstracts away the authentication backend:

```javascript
// Works in both development and production without changes
import { authClient } from './utils/authClient';

// Login
const { data, error } = await authClient.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
});

// Always calls backend API, backend handles the rest
```

## Database Schema

Both environments use the same schema:

### Schemas
- `public` - System tables (sessions, OAuth, etc.)
- `main` - Core app (users, courses, materials, care plans, learning plans)
- `user_data` - Activity tracking (chat, interactions)
- `dashboard` - Analytics and widgets

### Key Tables (main schema)
- `users` - User accounts and profiles
- `materials` - Uploaded educational materials
- `care_plans` - Anesthesia care plans
- `learning_plans` - Educational content plans
- `courses` - Course information
- `topics` - Knowledge topics
- `flashcards` - Study materials

## Migration Strategy

### Local to Production
1. Ensure AWS RDS is running and accessible
2. Set up Supabase project (auth only)
3. Update environment variables
4. Run database migrations on AWS RDS
5. Deploy backend with `AUTH_MODE=supabase`
6. Deploy frontend (no changes needed)

### Production to Local (for testing)
1. Change `AUTH_MODE=local` in backend `.env`
2. Change `DATABASE_URL` to local PostgreSQL
3. Restart backend
4. Frontend automatically adapts (calls same endpoints)

## Security Considerations

### Development
- JWT tokens signed with local secret
- Passwords hashed with bcrypt (12 rounds)
- No external network exposure required

### Production
- Supabase JWT tokens with audience verification
- HTTPS required for all API calls
- AWS RDS in private subnet (security group controlled)
- Environment variables never committed to git
- S3 for secure file storage
- Rate limiting via Supabase and API Gateway

## Technology Stack

### Frontend
- React 18
- Vite 7
- React Router 7
- Tailwind CSS

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy (ORM)
- Alembic (migrations)
- PyJWT (token verification)
- Bcrypt (password hashing)
- OpenAI API (AI features)

### Databases
- Development: PostgreSQL 12+ (local)
- Production: AWS RDS PostgreSQL (us-east-2)

### Authentication
- Development: Custom JWT
- Production: Supabase Auth

### Storage
- Development: Local filesystem
- Production: AWS S3 (us-east-2)

## Monitoring and Observability

### Development
- Console logs
- FastAPI debug mode
- PostgreSQL logs

### Production
- AWS CloudWatch (RDS metrics)
- Application logs (backend)
- Supabase Auth logs (auth events)
- Performance Insights (RDS query performance)
- S3 access logs

## Future Considerations

1. **Caching**: Add Redis for session management
2. **CDN**: CloudFront for static assets and API
3. **Load Balancing**: ELB for backend instances
4. **Queue**: SQS for async tasks
5. **Multi-region**: Add us-west-2 for DR
6. **API Gateway**: AWS API Gateway for rate limiting
7. **Secrets Manager**: AWS Secrets Manager for credentials

## Summary

This hybrid architecture provides:
- ✅ Fast local development (no cloud dependencies)
- ✅ Production-grade auth (Supabase OAuth, magic links)
- ✅ Reliable data storage (AWS RDS)
- ✅ Clean separation of concerns
- ✅ Frontend stays unchanged between environments
- ✅ Leverages best-in-class services for each concern
