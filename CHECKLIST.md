# ✅ Setup Checklist - GBP AI Discovery Optimizer

Use this checklist to ensure you've completed all setup steps correctly.

## 🔧 Prerequisites

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Redis installed (or Docker)
- [ ] Git installed
- [ ] Code editor (VS Code recommended)

---

## 1️⃣ API Keys & Accounts

### Supabase
- [ ] Created account at supabase.com
- [ ] Created new project
- [ ] Copied Project URL
- [ ] Copied `anon/public` key
- [ ] Copied `service_role` key
- [ ] Executed `supabase_schema.sql` in SQL Editor
- [ ] Verified tables created (run SELECT query)

### Google Gemini
- [ ] Went to aistudio.google.com
- [ ] Created API key
- [ ] Saved API key securely
- [ ] Tested key works (try in AI Studio)

### Outscraper
- [ ] Created account at outscraper.com
- [ ] Signed up for free trial or purchased credits
- [ ] Copied API key from Profile > API
- [ ] Verified credits available

---

## 2️⃣ Backend Setup

- [ ] Navigated to `backend/` directory
- [ ] Created virtual environment: `python3 -m venv venv`
- [ ] Activated venv: `source venv/bin/activate`
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Copied `.env.example` to `.env`
- [ ] Updated `.env` with all API keys:
  - [ ] SUPABASE_URL
  - [ ] SUPABASE_ANON_KEY
  - [ ] SUPABASE_SERVICE_KEY
  - [ ] GEMINI_API_KEY
  - [ ] OUTSCRAPER_API_KEY
  - [ ] REDIS_URL (if using external Redis)
- [ ] Tested backend: `uvicorn app.main:app --reload`
- [ ] Visited http://localhost:8000/api/v1/docs
- [ ] Saw OpenAPI documentation

---

## 3️⃣ Frontend Setup

- [ ] Navigated to `frontend/` directory
- [ ] Installed dependencies: `npm install`
- [ ] Copied `.env.local.example` to `.env.local`
- [ ] Updated `.env.local` with:
  - [ ] NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  - [ ] NEXT_PUBLIC_SUPABASE_URL (from Supabase)
  - [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY (from Supabase)
- [ ] Started dev server: `npm run dev`
- [ ] Visited http://localhost:3000
- [ ] Saw landing page

---

## 4️⃣ Redis & Celery

- [ ] Started Redis: `redis-server` (or Docker)
- [ ] Verified Redis running: `redis-cli ping` (should return "PONG")
- [ ] In new terminal, activated backend venv
- [ ] Started Celery worker: `celery -A app.tasks.celery_app worker --loglevel=info`
- [ ] Saw worker output: "celery@hostname ready"
- [ ] No errors in worker logs

---

## 5️⃣ First Test

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Redis running on port 6379
- [ ] Celery worker running
- [ ] Went to http://localhost:3000
- [ ] Filled in form:
  - Business: "Café Girondino"
  - Location: "São Paulo"
- [ ] Clicked "Iniciar Auditoria"
- [ ] Redirected to results page
- [ ] Saw "Analisando seu perfil..." message
- [ ] After ~60 seconds, saw completed audit
- [ ] Discovery score displayed (0-100)
- [ ] Recommendations shown
- [ ] No errors in any terminal

---

## 6️⃣ Verify Components

### Backend Health
- [ ] `curl http://localhost:8000/api/v1/health`
- [ ] Returns: `{"status":"healthy","service":"GBP AI Discovery Optimizer"}`

### Create Audit via API
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"business_name":"Test","location":"São Paulo"}'
```
- [ ] Returns audit object with `id`
- [ ] Status is `pending`

### Check Audit Status
```bash
# Replace {audit_id} with actual ID from above
curl http://localhost:8000/api/v1/audits/{audit_id}
```
- [ ] Initially returns `processing`
- [ ] After processing, returns `completed`
- [ ] Has `discovery_score` field

### Celery Task Execution
- [ ] Checked Celery worker logs
- [ ] Saw: "Task app.tasks.audit_tasks.process_audit_task[...]"
- [ ] Saw: "Task ... succeeded"
- [ ] No exceptions or errors

---

## 7️⃣ Common Issues Resolved

### "ModuleNotFoundError"
- [ ] Ensured virtual environment is activated
- [ ] Ran `pip install -r requirements.txt` again

### "Connection refused"
- [ ] Verified backend is running
- [ ] Checked port 8000 is not in use by another app
- [ ] Updated `NEXT_PUBLIC_API_URL` if needed

### "Negócio não encontrado"
- [ ] Tried different business name (use McDonald's for testing)
- [ ] Verified Outscraper API key is correct
- [ ] Checked Outscraper credits available

### "Audit stuck in processing"
- [ ] Verified Celery worker is running
- [ ] Checked Celery logs for errors
- [ ] Verified Redis is running
- [ ] Checked Gemini API key is valid

### Frontend errors
- [ ] Ran `npm install` again
- [ ] Cleared `.next` folder: `rm -rf .next`
- [ ] Restarted dev server

---

## 8️⃣ Production Ready

- [ ] All tests passing
- [ ] No console errors
- [ ] Environment variables secured
- [ ] `.env` files in `.gitignore`
- [ ] Read DEPLOYMENT.md
- [ ] Chose deployment platform (Vercel + Railway recommended)
- [ ] Have custom domain ready (optional)
- [ ] Updated WhatsApp number in CTA
- [ ] Customized branding colors

---

## 9️⃣ Optional Enhancements

- [ ] Setup Sentry for error tracking
- [ ] Add Google Analytics
- [ ] Setup email notifications (SendGrid/Mailgun)
- [ ] Configure custom email domain
- [ ] Add user authentication
- [ ] Implement payment system
- [ ] Build admin dashboard
- [ ] Setup CI/CD pipeline

---

## 🎯 Success Criteria

You're ready to launch when:

✅ **All checkboxes above are checked**
✅ **Successfully completed 3+ test audits**
✅ **No errors in any logs**
✅ **All API keys working**
✅ **Frontend loads in < 2 seconds**
✅ **Audits complete in < 90 seconds**
✅ **Results page displays correctly**
✅ **Mobile responsive** (test on phone)

---

## 📞 If You're Stuck

1. **Check logs first:**
   - Backend: Terminal where uvicorn is running
   - Celery: Terminal where worker is running
   - Frontend: Browser console (F12)

2. **Common fixes:**
   - Restart all services
   - Clear Redis: `redis-cli FLUSHALL`
   - Delete `.next` folder in frontend
   - Reinstall Python packages
   - Check all env vars are set

3. **Test individual components:**
   - Backend: Visit `/api/v1/docs`
   - Celery: Check worker sees tasks
   - Database: Query Supabase dashboard
   - Redis: `redis-cli ping`

---

## 🎉 Congratulations!

When all items are checked, you have:

- ✅ A working full-stack application
- ✅ Real AI integration
- ✅ Production-ready code
- ✅ Scalable architecture
- ✅ Professional UI/UX
- ✅ Lead generation funnel

**Now go get your first 10 clients! 🚀**

---

_Last updated: February 2024_
_Questions? Check README.md or QUICKSTART.md_
