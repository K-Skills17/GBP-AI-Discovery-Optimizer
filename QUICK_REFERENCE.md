# 📋 Quick Reference Card

**Print or save this for quick access!**

---

## 🚀 **I Want to Deploy WITHOUT Docker**

**Go to:** `EASY_DEPLOYMENT.md`

**Platform:** Vercel + Railway  
**Time:** 15 minutes  
**Cost:** FREE to start  
**Steps:**
1. Push to GitHub
2. Deploy to Vercel
3. Deploy to Railway
4. Done!

---

## 🐳 **I Want to Use Docker**

**Go to:** `DEPLOYMENT.md` (Docker section)

**Platform:** Docker Compose  
**Time:** 30 minutes  
**Cost:** Varies by host  
**Steps:**
1. Install Docker
2. Run `docker-compose up`
3. Deploy to cloud

---

## 💻 **I Want Full Control (VPS)**

**Go to:** `DEPLOYMENT.md` (VPS section)

**Platform:** Ubuntu VPS  
**Time:** 1-2 hours  
**Cost:** $12/month+  
**Steps:**
1. Buy VPS
2. Install dependencies
3. Configure services
4. Setup nginx + SSL

---

## 🎯 **I'm Just Starting**

**Start Here:**
1. `START_HERE.md` - Overview (5 min)
2. `PROJECT_SUMMARY.md` - What's built (10 min)
3. `QUICKSTART.md` - Run locally (15 min)
4. `CHOOSE_DEPLOYMENT.md` - Pick deployment (2 min)

---

## ⚡ **Quick Commands**

### Local Development
```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev

# Worker
celery -A app.tasks.celery_app worker --loglevel=info
```

### Deploy to Vercel (Frontend)
```bash
cd frontend
vercel --prod
```

### Deploy to Railway (Backend)
```bash
# Push to GitHub, Railway auto-deploys
git push origin main
```

---

## 🔑 **API Keys Needed**

1. **Supabase** (supabase.com)
   - Project URL
   - Anon key
   - Service key

2. **Google Gemini** (aistudio.google.com)
   - API key

3. **Outscraper** (outscraper.com)
   - API key

---

## 📊 **Cost Summary**

### Development (Local)
- **Cost:** $0
- **What:** Run on your laptop

### Production (Free Tier)
- **Vercel:** FREE
- **Railway:** FREE ($5 credit)
- **Supabase:** FREE
- **Total:** $0/month

### Production (Paid)
- **Vercel:** $20/month
- **Railway:** $20/month
- **Supabase:** $25/month
- **APIs:** $50/month
- **Total:** ~$115/month (1000 audits)

---

## 🆘 **Having Issues?**

### Frontend won't build
→ Check: `frontend/.env.local` exists with correct values

### Backend won't start
→ Check: `backend/.env` exists with all API keys

### Audit stuck processing
→ Check: Celery worker is running

### 404 errors
→ Check: `NEXT_PUBLIC_API_URL` points to correct backend

### CORS errors
→ Check: `BACKEND_CORS_ORIGINS` includes frontend URL

---

## 📁 **File Locations**

```
gbp-ai-optimizer/
├── START_HERE.md              ← Start here!
├── CHOOSE_DEPLOYMENT.md       ← Pick deployment
├── EASY_DEPLOYMENT.md         ← No Docker (recommended)
├── DEPLOYMENT.md              ← Docker/VPS options
├── QUICKSTART.md              ← Local setup
├── CHECKLIST.md               ← Verification
├── PROJECT_SUMMARY.md         ← What's built
├── README.md                  ← Full docs
│
├── backend/                   ← Python/FastAPI
│   ├── app/
│   ├── requirements.txt
│   └── .env                   ← Add your keys here
│
└── frontend/                  ← Next.js
    ├── app/
    ├── package.json
    └── .env.local             ← Add your keys here
```

---

## ✅ **Checklist for Going Live**

- [ ] Code tested locally
- [ ] All API keys obtained
- [ ] Database schema executed
- [ ] Deployment method chosen
- [ ] Frontend deployed
- [ ] Backend deployed
- [ ] Worker deployed
- [ ] Test audit completed
- [ ] Custom domain added (optional)
- [ ] Monitoring setup (optional)

---

## 🎯 **Success Metrics**

**Week 1:**
- [ ] Deployed successfully
- [ ] 3 test audits completed
- [ ] Shown to 2 people

**Week 2:**
- [ ] 5 beta users
- [ ] Feedback collected
- [ ] Improvements made

**Month 1:**
- [ ] 50 audits completed
- [ ] 3 paying clients
- [ ] Marketing started

---

## 📞 **Support Resources**

**Technical Questions:**
- README.md - Full documentation
- QUICKSTART.md - Setup help
- CHECKLIST.md - Troubleshooting

**Deployment Questions:**
- CHOOSE_DEPLOYMENT.md - Pick method
- EASY_DEPLOYMENT.md - Vercel + Railway
- DEPLOYMENT.md - Docker/VPS

**Business Questions:**
- PROJECT_SUMMARY.md - Revenue model
- START_HERE.md - Getting started

---

## 🚀 **URLs to Bookmark**

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Railway Dashboard](https://railway.app/dashboard)
- [Supabase Dashboard](https://app.supabase.com)
- [Google AI Studio](https://aistudio.google.com)
- [Outscraper Dashboard](https://app.outscraper.com)

---

**Keep this handy!** 📌

_Last updated: February 2024_
