# 🚀 Deployment Guide

## Deployment Options

### Option 1: Vercel (Frontend) + Railway (Backend) [RECOMMENDED]

**Advantages:**
- Free tiers available
- Automatic deployments from Git
- Easy to scale
- Zero DevOps required

#### Frontend → Vercel

1. **Push to GitHub:**
```bash
cd gbp-ai-optimizer
git init
git add .
git commit -m "Initial commit"
gh repo create gbp-ai-optimizer --private --source=. --remote=origin --push
```

2. **Deploy to Vercel:**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

3. **Configure Environment Variables in Vercel Dashboard:**
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

#### Backend → Railway

1. **Create Railway Account:**
   - Go to railway.app
   - Sign in with GitHub

2. **Create New Project:**
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Select your repo
   - Choose `/backend` as root directory

3. **Add Redis Service:**
   - In your project, click "New"
   - Choose "Database" → "Redis"

4. **Configure Environment Variables:**
```
PROJECT_NAME=GBP AI Discovery Optimizer
DEBUG=False
API_PREFIX=/api/v1
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
SUPABASE_SERVICE_KEY=your_key
REDIS_URL=${{Redis.REDIS_URL}}
OUTSCRAPER_API_KEY=your_key
GEMINI_API_KEY=your_key
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

5. **Add Celery Worker Service:**
   - Click "New" → "Empty Service"
   - Name it "celery-worker"
   - Set start command: `celery -A app.tasks.celery_app worker --loglevel=info`
   - Use same environment variables

6. **Deploy:**
   - Railway auto-deploys on push
   - Get your backend URL: `https://your-project.railway.app`

---

### Option 2: AWS/GCP (Full Production Setup)

#### Architecture:
```
Frontend: Vercel / Cloudflare Pages
Backend: EC2 / Cloud Run
Database: Supabase (managed)
Redis: ElastiCache / Memorystore
Workers: ECS / Cloud Run Jobs
```

#### Steps for AWS:

**1. Setup Infrastructure:**
```bash
# Install AWS CLI
aws configure

# Create EC2 instance (Ubuntu 22.04)
# t3.medium recommended (2 vCPU, 4GB RAM)

# Setup ElastiCache Redis
# t3.micro for development
```

**2. Backend Deployment:**
```bash
# SSH into EC2
ssh ubuntu@your-ec2-ip

# Install dependencies
sudo apt update
sudo apt install python3-pip nginx redis-tools

# Clone repo
git clone https://github.com/yourusername/gbp-ai-optimizer
cd gbp-ai-optimizer/backend

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure systemd services
sudo nano /etc/systemd/system/gbp-api.service
```

**gbp-api.service:**
```ini
[Unit]
Description=GBP AI Optimizer API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gbp-ai-optimizer/backend
Environment="PATH=/home/ubuntu/gbp-ai-optimizer/backend/venv/bin"
EnvironmentFile=/home/ubuntu/gbp-ai-optimizer/backend/.env
ExecStart=/home/ubuntu/gbp-ai-optimizer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

**gbp-worker.service:**
```ini
[Unit]
Description=GBP AI Optimizer Celery Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gbp-ai-optimizer/backend
Environment="PATH=/home/ubuntu/gbp-ai-optimizer/backend/venv/bin"
EnvironmentFile=/home/ubuntu/gbp-ai-optimizer/backend/.env
ExecStart=/home/ubuntu/gbp-ai-optimizer/backend/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

**3. Start Services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gbp-api gbp-worker
sudo systemctl start gbp-api gbp-worker
sudo systemctl status gbp-api
```

**4. Configure Nginx:**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**5. SSL with Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

---

### Option 3: Docker + DigitalOcean App Platform

**1. Create Dockerfile for production:**

`backend/Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Create app.yaml:**
```yaml
name: gbp-ai-optimizer
services:
  - name: api
    dockerfile_path: backend/Dockerfile.prod
    github:
      repo: yourusername/gbp-ai-optimizer
      branch: main
      deploy_on_push: true
    envs:
      - key: SUPABASE_URL
        value: ${SUPABASE_URL}
      # ... add all env vars
    http_port: 8000
    
  - name: worker
    dockerfile_path: backend/Dockerfile.prod
    github:
      repo: yourusername/gbp-ai-optimizer
      branch: main
    envs:
      - key: SUPABASE_URL
        value: ${SUPABASE_URL}
    run_command: celery -A app.tasks.celery_app worker --loglevel=info
    
databases:
  - name: redis
    engine: REDIS
    version: "7"
```

**3. Deploy:**
```bash
# Install doctl
brew install doctl  # or apt-get install doctl

# Authenticate
doctl auth init

# Deploy
doctl apps create --spec app.yaml
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Enable RLS on Supabase tables
- [ ] Add rate limiting (use FastAPI limiter)
- [ ] Setup CORS properly
- [ ] Use environment variables (never commit secrets)
- [ ] Enable HTTPS only
- [ ] Setup API key rotation

### Performance
- [ ] Enable Redis caching for audits
- [ ] Setup CDN (Cloudflare)
- [ ] Configure connection pooling
- [ ] Setup Celery autoscaling
- [ ] Monitor with Sentry/Datadog

### Monitoring
```python
# Add to backend/app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

### Logging
```python
# backend/app/config.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/gbp-optimizer/app.log')
    ]
)
```

---

## Cost Estimates

### Development (Free Tier)
- **Supabase**: Free (500MB database, 2GB bandwidth)
- **Vercel**: Free (100GB bandwidth)
- **Railway**: $5/month (500 hours, 8GB RAM)
- **Gemini API**: Free tier (15 requests/min)
- **Outscraper**: Free trial (75 requests)

**Total: ~$5/month**

### Production (1000 audits/month)
- **Supabase**: $25/month (Pro plan)
- **Vercel**: $20/month (Pro plan)
- **Railway**: $20/month (scaled workers)
- **Gemini API**: ~$15/month (0.001¢/1K input tokens)
- **Outscraper**: ~$50/month (credits)

**Total: ~$130/month**

---

## Domain Setup

**1. Buy domain** (Registro.br, Namecheap, etc.)

**2. Configure DNS:**
```
Type  | Name | Value
------|------|-------
A     | @    | Vercel IP
CNAME | www  | your-app.vercel.app
CNAME | api  | your-backend.railway.app
```

**3. Add to Vercel:**
- Go to project settings
- Add custom domain
- Follow verification steps

---

## Backup Strategy

**1. Supabase Backups:**
- Automatic daily backups (Pro plan)
- Point-in-time recovery

**2. Redis Backups:**
```bash
# Configure in railway.app or AWS
# Enable AOF persistence
```

**3. Application Backups:**
```bash
# Automated via GitHub
git push origin main
```

---

## Post-Deployment

**Test Production:**
```bash
curl https://api.yourdomain.com/api/v1/health

# Create test audit
curl -X POST https://api.yourdomain.com/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"business_name":"Test","location":"São Paulo"}'
```

**Monitor:**
- Setup uptime monitoring (UptimeRobot)
- Configure error tracking (Sentry)
- Watch Celery queue length
- Monitor API usage quotas

---

🎉 **Your app is now live!**

Share it: `https://yourdomain.com`
