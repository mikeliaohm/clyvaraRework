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

### 3. Configure backend environment variables (OpenAI)
Create a `.env` file in /backend and add your OpenAI API secret key:
```
OPENAI_API_KEY="your_secret_key_here"
```

### 4. Configure frontend environment variables (Supabase)
Create a `.env.local` file in /frontend and add your Supabase credentials:
```
VITE_SUPABASE_URL= "supabase_url_here"
VITE_SUPABASE_ANON_KEY="your_secret_key_here"
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

## 📦 AWS Services Setup

### AWS RDS (PostgreSQL on PgAdmin4)
1. Download [PgAdmin4](https://www.pgadmin.org/download/)
2. Connect to RDS:
   - Enter Hostname/Address, Port, Username from RDS (make sure to use `us-east-2` region)
   - Ask Christian for password/credentials
   - **Parameters**: 
     - First: SSL Mode → value: `require`
     - Second (Optional): Connection timeout
3. **Database Schemas**: 
   - In RDS, there are four schemas: `dashboard`, `main`, `public`, and `user_data`
   - The most frequently used ones are `main` and `user_data`

### AWS SageMaker
1. **Access**: 
   - Domain: `Clyvara_Health`
   - Project name: `Clyvara_ML`
2. **Authentication**: 
   - Christian may need to give you authentications for S3, Manager, or may need to add you as a member
3. **Datasets**: 
   - Download ednet (kt-1 to kt-4) datasets via SageMaker
4. **SAKT Model**: 
   - Run SAKT model (initial experiments are done in `Dev.ipynb`)


## 🧩 Notes
- Make sure both backend and frontend servers are running for full functionality.  
- Commit changes only from feature branches — open a PR to merge into `main`.  
- Use the `.env.example` format (if present) for consistent environment setup.


