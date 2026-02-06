# 🚀 Easy Deployment Guide (No Docker Required!)

Docker is optional! Here are **simpler, faster** ways to deploy your SaaS.

---

## ⚡ RECOMMENDED: Vercel + Railway (Easiest & Free to Start)

**Why this is best:**
- ✅ 100% free tier to start
- ✅ Zero DevOps knowledge needed
- ✅ Auto-deploys from GitHub
- ✅ Takes 15 minutes total
- ✅ Production-grade infrastructure

### Total Time: 15 minutes
### Cost: $0 to start, ~$20/month in production

---

## 🎯 Step-by-Step: Vercel + Railway Deployment

### Phase 1: Prepare Your Code (5 minutes)

#### 1. Push to GitHub
```bash
cd gbp-ai-optimizer

# Initialize Git
git init
git add .
git commit -m "Initial commit - GBP AI Optimizer"

# Create GitHub repo (using GitHub CLI)
gh repo create gbp-ai-optimizer --private --source=. --remote=origin --push

# Or manually:
# 1. Go to github.com/new
# 2. Create private repo "gbp-ai-optimizer"
# 3. Follow instructions to push
```

---

### Phase 2: Deploy Frontend to Vercel (3 minutes)

#### 1. Sign up at Vercel
- Go to [vercel.com](https://vercel.com)
- Click "Sign Up"
- Choose "Continue with GitHub"

#### 2. Import Your Project
- Click "Add New..." → "Project"
- Select your `gbp-ai-optimizer` repository
- Framework Preset: **Next.js** (auto-detected)
- Root Directory: `frontend`
- Click **Deploy**

#### 3. Add Environment Variables
After deployment, go to **Project Settings** → **Environment Variables**:

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app/api/v1
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

> **Note:** You'll get the `NEXT_PUBLIC_API_URL` in Phase 3. For now, use a placeholder.

Click **Save** → **Redeploy**

✅ **Your frontend is now live!** (e.g., `https://gbp-optimizer.vercel.app`)

---

### Phase 3: Deploy Backend to Railway (7 minutes)

#### 1. Sign up at Railway
- Go to [railway.app](https://railway.app)
- Click "Login with GitHub"

#### 2. Create New Project
- Click "New Project"
- Choose "Deploy from GitHub repo"
- Select `gbp-ai-optimizer`
- Railway will detect Python

#### 3. Configure Backend Service

**Settings → General:**
- Service Name: `api`
- Root Directory: `/backend`
- Watch Paths: `/backend/**`

**Settings → Deploy:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### 4. Add Redis Database
- In your project, click "+ New"
- Select "Database" → "Add Redis"
- Railway creates it automatically

#### 5. Add Environment Variables

**Settings → Variables → Add Variables:**

```env
PROJECT_NAME=GBP AI Discovery Optimizer
DEBUG=False
API_PREFIX=/api/v1

# Supabase (from your Supabase dashboard)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...

# Redis (Railway provides this automatically)
REDIS_URL=${{Redis.REDIS_URL}}

# Your API Keys
OUTSCRAPER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Celery (same as Redis)
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}

# CORS - Add your Vercel URL
BACKEND_CORS_ORIGINS=["https://gbp-optimizer.vercel.app"]

# Limits
MAX_REVIEWS_PER_AUDIT=100
AUDIT_CACHE_HOURS=24
```

Click **Deploy**

#### 6. Add Celery Worker Service

**In the same Railway project:**
- Click "+ New" → "Empty Service"
- Name: `worker`
- Root Directory: `/backend`

**Settings → Deploy:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `celery -A app.tasks.celery_app worker --loglevel=info`

**Settings → Variables:**
- Click "Copy all from api service"
- This copies all environment variables

Click **Deploy**

#### 7. Get Your Backend URL

- Go to your `api` service
- Click **Settings** → **Networking**
- Click **Generate Domain**
- Copy the URL (e.g., `https://gbp-optimizer-production.up.railway.app`)

---

### Phase 4: Connect Frontend to Backend (2 minutes)

#### 1. Update Vercel Environment Variable
- Go to your Vercel project
- **Settings** → **Environment Variables**
- Update `NEXT_PUBLIC_API_URL`:
  ```
  NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app/api/v1
  ```

#### 2. Redeploy
- Go to **Deployments** tab
- Click ⋯ on latest deployment
- Click **Redeploy**

---

### Phase 5: Test Your Deployment (2 minutes)

#### 1. Test Backend
```bash
curl https://your-backend-url.railway.app/api/v1/health
# Should return: {"status":"healthy","service":"GBP AI Discovery Optimizer"}
```

#### 2. Test Frontend
- Visit your Vercel URL: `https://gbp-optimizer.vercel.app`
- Fill in the form with a test business
- Submit and watch it process!

#### 3. Monitor Celery Worker
- In Railway, go to your `worker` service
- Click **Deployments** → **View Logs**
- You should see: `celery@worker ready`

---

## ✅ You're Live!

**Your SaaS is now running on:**
- Frontend: `https://gbp-optimizer.vercel.app`
- Backend: `https://your-backend.railway.app`
- Database: Supabase (managed)
- Redis: Railway (managed)
- Worker: Railway Celery worker

**Monthly Cost:**
- Vercel: FREE (up to 100GB bandwidth)
- Railway: FREE ($5 credit/month, usually enough for dev)
- Supabase: FREE (up to 500MB database)

**Total: $0/month until you scale!**

---

## 🔧 Alternative Deployment Options

### Option 2: Render.com (All-in-One)

**Pros:** One platform for everything
**Cons:** Slightly slower free tier

#### Setup:
1. Go to [render.com](https://render.com)
2. "New +" → "Web Service"
3. Connect GitHub repo
4. Configure:
   - Name: `gbp-optimizer-api`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Create Redis instance: "New +" → "Redis"
7. Create Worker: "New +" → "Background Worker"
   - Start Command: `celery -A app.tasks.celery_app worker`

**For Frontend:**
- Deploy to Vercel (same as above)
- Or use Render Static Site

---

### Option 3: Fly.io (Developer-Friendly)

**Pros:** Great free tier, fast globally
**Cons:** Requires CLI tool

#### Setup:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy Backend
cd backend
fly launch --name gbp-optimizer-api
# Follow prompts, add Postgres + Redis

# Deploy Worker
fly launch --name gbp-optimizer-worker --no-deploy
# Edit fly.toml, change CMD to celery command
fly deploy
```

---

### Option 4: PythonAnywhere + Netlify (Super Simple)

**Best for:** Absolute beginners
**Pros:** Very simple UI
**Cons:** Limited scalability

#### Backend on PythonAnywhere:
1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. "Web" → "Add a new web app"
3. Choose "Manual configuration" → Python 3.10
4. Upload your `backend/` folder
5. Configure WSGI to run FastAPI
6. Use their Redis add-on

#### Frontend on Netlify:
1. Sign up at [netlify.com](https://netlify.com)
2. "Add new site" → "Import from Git"
3. Select repo
4. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/.next`

---

### Option 5: Traditional VPS (DigitalOcean, Linode)

**Best for:** Full control
**Cost:** ~$12/month minimum

#### Quick Setup:
```bash
# 1. Create Ubuntu 22.04 droplet ($12/month)
# 2. SSH into server
ssh root@your-ip

# 3. Install dependencies
apt update
apt install python3-pip nginx redis-server nodejs npm

# 4. Clone your repo
git clone https://github.com/yourusername/gbp-ai-optimizer
cd gbp-ai-optimizer

# 5. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Setup systemd services (see DEPLOYMENT.md for full config)
# 7. Setup nginx reverse proxy
# 8. Setup frontend on subdomain
```

Full guide in `DEPLOYMENT.md`

---

## 🌐 Custom Domain Setup

### After deploying, add your domain:

#### For Vercel:
1. Buy domain (Namecheap, Google Domains, etc.)
2. Vercel project → **Settings** → **Domains**
3. Add your domain: `auditoria-ai.com.br`
4. Follow DNS instructions

#### For Railway:
1. Railway project → `api` service → **Settings** → **Networking**
2. **Custom Domain** → Add: `api.auditoria-ai.com.br`
3. Update your DNS:
   ```
   Type: CNAME
   Name: api
   Value: your-project.up.railway.app
   ```

---

## 📊 Cost Comparison

| Platform | Free Tier | Paid (1K audits/month) | Notes |
|----------|-----------|------------------------|-------|
| **Vercel + Railway** | ✅ $0 | ~$20/month | RECOMMENDED |
| Render | ✅ $0 | ~$25/month | Slower cold starts |
| Fly.io | ✅ $0 | ~$15/month | Best performance |
| PythonAnywhere | ✅ $0 | ~$10/month | Limited features |
| VPS (DO/Linode) | ❌ $12+ | ~$24/month | Full control |
| AWS/GCP | ❌ Complex | $50-100/month | Overkill for MVP |

---

## 🚀 Production Optimizations

Once deployed, add these improvements:

### 1. Enable HTTPS (Automatic on all platforms)
- Vercel: Auto-SSL ✓
- Railway: Auto-SSL ✓
- Render: Auto-SSL ✓

### 2. Setup Monitoring
```bash
# Add to backend/requirements.txt
sentry-sdk[fastapi]==1.40.0

# In backend/app/main.py
import sentry_io

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### 3. Add Uptime Monitoring
- Free: [UptimeRobot](https://uptimerobot.com)
- Monitor both frontend and `/api/v1/health`

### 4. Setup Analytics
```typescript
// In frontend/app/layout.tsx
import Script from 'next/script'

// Add Google Analytics
<Script src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX" />
```

---

## 🔄 Auto-Deploy Setup (CI/CD)

### With Vercel + Railway:
**Already done!** Every `git push` auto-deploys.

To deploy:
```bash
git add .
git commit -m "Update feature X"
git push origin main
```

- Vercel rebuilds frontend automatically
- Railway rebuilds backend + worker automatically

---

## 🐛 Deployment Troubleshooting

### Frontend build fails
```bash
# Locally test the build
cd frontend
npm run build
# Fix any TypeScript errors
```

### Backend won't start
- Check Railway logs: **Deployments** → **View Logs**
- Common issue: Missing environment variable
- Verify: All env vars are set in Railway settings

### Worker not processing
- Check worker logs in Railway
- Verify: Redis URL is correct
- Test: Create audit and watch worker logs

### CORS errors
- Check `BACKEND_CORS_ORIGINS` includes your Vercel URL
- Format: `["https://your-app.vercel.app"]` (with quotes and brackets)

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Supabase database created & schema executed
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway
- [ ] Redis database added in Railway
- [ ] Worker service created in Railway
- [ ] All environment variables set
- [ ] Frontend connected to backend URL
- [ ] Test audit completed successfully
- [ ] Health check endpoint working
- [ ] Custom domain added (optional)
- [ ] SSL certificate active (auto)
- [ ] Monitoring setup (optional)

---

## 🎉 You're Live!

**No Docker needed.** Your SaaS is running on modern, managed infrastructure.

**Next steps:**
1. Test thoroughly
2. Share with beta users
3. Collect feedback
4. Start marketing!

---

**Questions?** Everything is in the docs:
- Technical issues → `README.md`
- Platform-specific → This file
- General setup → `QUICKSTART.md`

**Good luck! 🚀**
