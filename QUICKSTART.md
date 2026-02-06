# 🚀 Quick Start Guide - GBP AI Discovery Optimizer

## ⚡ 5-Minute Setup

### Step 1: Clone & Setup Database (2 min)

```bash
# 1. Navigate to project
cd gbp-ai-optimizer

# 2. Setup Supabase
# - Go to supabase.com and create a new project
# - Copy supabase_schema.sql content
# - Paste in Supabase SQL Editor and run
# - Save your credentials:
#   - Project URL
#   - anon/public key
#   - service_role/secret key
```

### Step 2: Get API Keys (2 min)

**Google Gemini:**
```
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy your key
```

**Outscraper:**
```
1. Visit: https://outscraper.com
2. Sign up (free trial available)
3. Go to Profile > API
4. Copy your API key
```

### Step 3: Backend Setup (1 min)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys:
nano .env  # or use any text editor

# Test it works
uvicorn app.main:app --reload
# Should see: "Application startup complete"
# Visit: http://localhost:8000/api/v1/docs
```

### Step 4: Frontend Setup (30 sec)

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local
nano .env.local

# Start dev server
npm run dev
# Visit: http://localhost:3000
```

### Step 5: Start Workers (30 sec)

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

## ✅ Verify Everything Works

### Test 1: Backend Health
```bash
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy","service":"GBP AI Discovery Optimizer"}
```

### Test 2: Create Test Audit
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Padaria Brasileira",
    "location": "São Paulo"
  }'
# Should return audit object with id
```

### Test 3: Frontend
1. Go to `http://localhost:3000`
2. Fill in form:
   - Business: "Padaria Brasileira"
   - Location: "São Paulo"
3. Click "Iniciar Auditoria"
4. Should redirect to results page
5. Wait ~60 seconds for processing

## 🐳 Docker Alternative (Even Easier!)

```bash
# Start everything at once
docker-compose up -d

# Check logs
docker-compose logs -f

# Access:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - Flower: http://localhost:5555
```

## 🔧 Common Issues

**"ModuleNotFoundError: No module named 'app'"**
```bash
# Make sure you're in the backend directory
cd backend
# Make sure venv is activated
source venv/bin/activate
```

**"Connection refused" when creating audit**
```bash
# Make sure backend is running
cd backend
uvicorn app.main:app --reload
```

**"Audit stuck in 'processing' status"**
```bash
# Make sure Celery worker is running
cd backend
celery -A app.tasks.celery_app worker --loglevel=info

# Check Celery logs for errors
```

**"Negócio não encontrado"**
- Outscraper might not have data for that business
- Try a well-known business: "McDonald's, São Paulo"
- Check Outscraper credits/quota

## 📊 Testing the Full Flow

Use this known business for testing:
```
Business Name: Café Girondino
Location: São Paulo
```

This should:
1. ✅ Be found by Outscraper
2. ✅ Have reviews to analyze
3. ✅ Complete in ~60 seconds
4. ✅ Generate full report with score

## 🎯 Next Steps

Once everything is working:

1. **Customize branding**: Update colors in `frontend/tailwind.config.ts`
2. **Add WhatsApp CTA**: Update number in `frontend/app/resultado/[auditId]/page.tsx`
3. **Deploy**: Follow deployment guide in README.md
4. **Get real clients**: Start marketing your tool!

## 💡 Pro Tips

- **Free tier limits**: Gemini has generous free tier, Outscraper gives 75 free requests/month
- **Cache audits**: System automatically caches audits for 24h to save API costs
- **Local development**: Use ngrok to test webhooks/payments locally

## 🆘 Need Help?

Check the full README.md for:
- Detailed architecture
- API documentation
- Deployment guides
- Troubleshooting

---

**Happy optimizing! 🚀**
