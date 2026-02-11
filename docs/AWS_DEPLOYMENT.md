# AWS RDS Production Deployment

This guide covers deploying the application to production with AWS RDS + Supabase Auth.

## Prerequisites

- AWS account with access to RDS
- Supabase account (free tier works)
- Backend deployment environment (EC2, ECS, Lambda, etc.)

## Step 1: Set Up Supabase Auth (One-time)

1. **Create Supabase Project**
   ```
   Go to https://supabase.com
   Create new project
   Wait for project to initialize (~2 minutes)
   ```

2. **Get Supabase Credentials**
   - Go to project Settings > API
   - Copy these values:
     - `Project URL` → SUPABASE_URL
     - `anon public` key → SUPABASE_ANON_KEY
   - Go to Settings > API > JWT Settings
     - Copy `JWT Secret` → SUPABASE_JWT_SECRET

3. **Configure Supabase Auth**
   - Go to Authentication > Providers
   - Enable Email auth (already enabled by default)
   - Optional: Enable OAuth providers (Google, GitHub, etc.)
   - Go to Authentication > URL Configuration
   - Add your production frontend URL to "Site URL"
   - Add your production redirect URLs

4. **Disable Supabase Database (Optional)**
   - We're using AWS RDS for the database
   - Supabase database is not needed
   - This keeps your free tier usage minimal

## Step 2: Prepare AWS RDS

### Option A: Use Existing RDS Instance

If you already have an RDS instance:

1. **Verify Connection**
   ```bash
   psql -h your-rds-endpoint.us-east-2.rds.amazonaws.com \
        -U username \
        -d clyvara_prod \
        -c "SELECT version();"
   ```

2. **Check Schemas**
   ```sql
   SELECT schema_name FROM information_schema.schemata;
   -- Should see: public, main, user_data, dashboard
   ```

### Option B: Create New RDS Instance

1. **Launch RDS Instance**
   ```
   AWS Console → RDS → Create database
   
   Engine: PostgreSQL 14 or higher
   Template: Production (or Dev/Test for staging)
   DB instance identifier: clyvara-prod
   Master username: clyvara_admin
   Master password: <generate strong password>
   
   Instance configuration:
   - Dev/Test: db.t3.micro (free tier eligible)
   - Production: db.t3.small or higher
   
   Storage:
   - General Purpose SSD (gp3)
   - 20 GB minimum
   - Enable storage autoscaling
   
   Connectivity:
   - VPC: Your existing VPC
   - Public access: No (recommended)
   - VPC security group: Create new
   
   Database authentication:
   - Password authentication
   
   Additional configuration:
   - Initial database name: clyvara_prod
   - Backup retention: 7 days (production)
   - Enable encryption at rest
   ```

2. **Configure Security Group**
   ```
   RDS → Select instance → Connectivity & security → Security groups
   
   Add inbound rule:
   - Type: PostgreSQL
   - Port: 5432
   - Source: Backend server security group or IP range
   - Description: Backend access
   ```

3. **Create Database User**
   ```bash
   # Connect as admin
   psql -h your-rds-endpoint.us-east-2.rds.amazonaws.com \
        -U clyvara_admin \
        -d clyvara_prod
   
   # Create application user
   CREATE USER clyvara_app WITH PASSWORD 'strong_app_password';
   
   # Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE clyvara_prod TO clyvara_app;
   
   # Exit and reconnect as new user to test
   \q
   ```

## Step 3: Run Migrations on RDS

1. **Configure Connection**
   ```bash
   # On your local machine or deployment server
   export DATABASE_URL="postgresql+psycopg://clyvara_app:password@your-rds-endpoint.us-east-2.rds.amazonaws.com:5432/clyvara_prod"
   ```

2. **Test Connection**
   ```bash
   cd backend
   python -c "from database import test_connection; test_connection()"
   # Should print: "Database connection successful!"
   ```

3. **Run Migrations**
   ```bash
   # From backend directory
   python create_migration.py upgrade
   ```

   Expected output:
   ```
   Applying all pending migrations...
   Creating schemas and extensions...
   ✓ Schemas and extensions ready
   INFO  [alembic.runtime.migration] Running upgrade  -> 5d3a712b3ced, initial schema
   ✓ Database upgraded successfully!
   ```

4. **Verify Schema**
   ```bash
   psql "$DATABASE_URL" -c "\dn"
   ```
   
   Should show:
   ```
   List of schemas
   Name      | Owner
   ----------+----------
   dashboard | clyvara_app
   main      | clyvara_app
   public    | postgres
   user_data | clyvara_app
   ```

## Step 4: Configure Production Environment

Create `.env` file on your backend server:

```bash
# ============================================
# PRODUCTION ENVIRONMENT
# ============================================

# Auth Mode
AUTH_MODE=supabase

# AWS RDS Database
DATABASE_URL=postgresql+psycopg://clyvara_app:password@your-rds-endpoint.us-east-2.rds.amazonaws.com:5432/clyvara_prod

# Supabase Auth (for authentication only)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# JWT Secret (backup/fallback)
JWT_SECRET=generate_random_secret_here

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# AWS S3 Storage
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-2
S3_BUCKET_NAME=clyvara-uploads

# Optional: Admin API Key
ADMIN_API_KEY=generate_random_admin_key

# Optional: Sentry for error tracking
SENTRY_DSN=your_sentry_dsn_if_using
```

## Step 5: Deploy Backend

### Option A: EC2 Deployment

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.10 python3.10-venv postgresql-client
   
   cd /opt/clyvara/backend
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r ../requirements.txt
   ```

2. **Configure Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/clyvara-backend.service
   ```
   
   ```ini
   [Unit]
   Description=Clyvara Backend API
   After=network.target
   
   [Service]
   Type=notify
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/opt/clyvara/backend
   Environment="PATH=/opt/clyvara/backend/venv/bin"
   EnvironmentFile=/opt/clyvara/backend/.env
   ExecStart=/opt/clyvara/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable clyvara-backend
   sudo systemctl start clyvara-backend
   ```

3. **Set Up Nginx Reverse Proxy**
   ```bash
   sudo apt install nginx
   sudo nano /etc/nginx/sites-available/clyvara
   ```
   
   ```nginx
   server {
       listen 80;
       server_name api.clyvara.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/clyvara /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   
   # Install SSL certificate
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d api.clyvara.com
   ```

### Option B: Docker Deployment

1. **Create Dockerfile** (if not exists)
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY backend/ .
   
   EXPOSE 8000
   
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build and Run**
   ```bash
   docker build -t clyvara-backend .
   docker run -d \
     --name clyvara-backend \
     --env-file .env \
     -p 8000:8000 \
     clyvara-backend
   ```

### Option C: AWS ECS/Fargate

See AWS ECS documentation for container deployments.

## Step 6: Deploy Frontend

1. **Update Frontend .env**
   ```bash
   VITE_API_URL=https://api.clyvara.com
   ```

2. **Build Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Deploy to S3 + CloudFront** (recommended)
   ```bash
   aws s3 sync dist/ s3://clyvara-frontend/
   aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
   ```

## Step 7: Verify Deployment

1. **Health Check**
   ```bash
   curl https://api.clyvara.com/
   # Should return: {"message":"Clyvara Backend API","status":"running"}
   ```

2. **Database Connection**
   ```bash
   curl https://api.clyvara.com/health/db
   ```

3. **Test Auth Flow**
   ```bash
   # Signup
   curl -X POST https://api.clyvara.com/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpass123",
       "username": "testuser",
       "full_name": "Test User"
     }'
   
   # Login
   curl -X POST https://api.clyvara.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpass123"
     }'
   ```

## Monitoring and Maintenance

### CloudWatch Monitoring

1. **RDS Metrics to Monitor**
   - CPUUtilization
   - DatabaseConnections
   - FreeStorageSpace
   - ReadLatency / WriteLatency
   - FreeableMemory

2. **Set Up Alarms**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name clyvara-rds-cpu \
     --alarm-description "CPU utilization exceeds 80%" \
     --metric-name CPUUtilization \
     --namespace AWS/RDS \
     --statistic Average \
     --period 300 \
     --threshold 80 \
     --comparison-operator GreaterThanThreshold \
     --evaluation-periods 2
   ```

### Backup Strategy

1. **Automated Backups** (already configured in RDS)
   - Retention: 7 days
   - Backup window: 03:00-04:00 UTC (off-peak)

2. **Manual Snapshots**
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier clyvara-prod \
     --db-snapshot-identifier clyvara-prod-manual-$(date +%Y%m%d)
   ```

### Database Maintenance

1. **Apply Migrations**
   ```bash
   # SSH into backend server
   cd /opt/clyvara/backend
   source venv/bin/activate
   python create_migration.py upgrade
   sudo systemctl restart clyvara-backend
   ```

2. **Monitor Connections**
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

3. **Vacuum Database** (automatic in RDS, but can trigger manually)
   ```sql
   VACUUM ANALYZE;
   ```

## Security Checklist

- [ ] RDS in private subnet (no public access)
- [ ] Security group restricts access to backend only
- [ ] Strong database passwords (20+ characters)
- [ ] Encryption at rest enabled
- [ ] SSL/TLS for database connections
- [ ] Environment variables not in version control
- [ ] HTTPS only for API endpoints
- [ ] CORS configured for frontend domain only
- [ ] Supabase rate limiting enabled
- [ ] CloudWatch alarms configured
- [ ] Backup retention policy set
- [ ] IAM roles with least privilege

## Troubleshooting

### Cannot Connect to RDS
```bash
# Check security group
aws rds describe-db-instances --db-instance-identifier clyvara-prod \
  --query 'DBInstances[0].VpcSecurityGroups'

# Test connection
telnet your-rds-endpoint.us-east-2.rds.amazonaws.com 5432
```

### Authentication Errors
```bash
# Verify Supabase credentials
curl -X POST https://your-project.supabase.co/auth/v1/signup \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

### Migration Failures
```bash
# Check current version
python create_migration.py current

# Rollback one version
python create_migration.py downgrade

# Re-apply
python create_migration.py upgrade
```

## Cost Optimization

### Development/Staging
- db.t3.micro (free tier eligible)
- 20 GB storage
- Single AZ
- 1-day backup retention

**Estimated cost**: $15-20/month

### Production
- db.t3.small (recommended minimum)
- 50 GB storage with autoscaling
- Multi-AZ for high availability
- 7-day backup retention

**Estimated cost**: $60-80/month

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions)
2. Configure monitoring and alerting
3. Implement database backup testing
4. Set up staging environment
5. Configure CDN for static assets
6. Implement rate limiting
7. Set up log aggregation (CloudWatch Logs)
