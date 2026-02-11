# Clyvara Rework
New and improved Clyvara website — Fall 2025 release.

---

## ⚙️ Setup

### 1. Create and activate a virtual environment
```bash
python -m venv <env_name>
source <env_name>/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up local database
See [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) for detailed instructions:
```bash
# Create PostgreSQL database
createdb clyvara_dev

# Copy environment example
cp .env.example .env

# Edit .env with your settings
# Required: DATABASE_URL, JWT_SECRET, OPENAI_API_KEY
```

### 4. Run database migrations
```bash
cd backend
python create_migration.py upgrade
```

### 5. Configure frontend
Create a `.env` file in /frontend:
```
VITE_API_URL=http://localhost:8000
```

---

## Development Workflow

### Create a new feature branch
```bash
git checkout -b <branch_name>
```

### Run the app locally

Run **backend** and **frontend** separately:

#### Backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
npm run dev
```

---

## 🏗️ Architecture

This application uses a **hybrid architecture**:

### Development (Local)
- **Database**: Local PostgreSQL
- **Auth**: Custom JWT authentication
- **Benefits**: No cloud dependencies, fast iteration

### Production (AWS + Supabase)
- **Database**: AWS RDS PostgreSQL (us-east-2)
- **Auth**: Supabase Auth (OAuth, magic links)
- **Storage**: AWS S3 (us-east-2)
- **Benefits**: Enterprise-grade services

**Key Feature**: Frontend code is identical in both environments. Backend handles the differences.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture diagrams.

---

## 📦 Production Services

### AWS RDS (PostgreSQL)
1. Download [PgAdmin4](https://www.pgadmin.org/download/)
2. Connect to RDS:
   - Hostname/Address from AWS Console (us-east-2 region)
   - Ask team lead for credentials
   - **SSL Mode**: `require`
3. **Database Schemas**: 
   - `main` - Core application data (users, courses, materials, care plans)
   - `user_data` - Activity tracking (chat, interactions)
   - `dashboard` - Analytics and widgets
   - `public` - System tables (sessions, OAuth)

### Supabase Auth (Production Only)
- Used for authentication in production
- Provides OAuth (Google, GitHub), magic links, password reset
- Backend proxies all auth requests
- Frontend never calls Supabase directly

### AWS S3
- **Bucket**: `clyvara-uploads` (us-east-2)
- **Purpose**: Store uploaded materials (PDFs, documents)
- **Local Development**: Files stored locally (no S3 needed)

### AWS SageMaker (ML Experiments)
1. **Access**: 
   - Domain: `Clyvara_Health`
   - Project name: `Clyvara_ML`
2. **Datasets**: 
   - ednet (kt-1 to kt-4) datasets
3. **Models**: 
   - SAKT model experiments in `Dev.ipynb`


## 🧩 Notes
- Make sure both backend and frontend servers are running for full functionality
- Commit changes only from feature branches — open a PR to merge into `main`
- See [docs/HYBRID_AUTH.md](docs/HYBRID_AUTH.md) for authentication details
- See [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) for local database setup
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete architecture overview


