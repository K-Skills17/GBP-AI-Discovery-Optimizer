# 🔧 Vercel Setup - Quick Fix Guide

## ⚠️ Problem: Vercel Detects "Other" Instead of Next.js

**Quick Fix:** Tell Vercel where the frontend is!

---

## ✅ Solution 1: Configure During Import (EASIEST)

When you click "Import Project" in Vercel:

### Step 1: Select Your Repo
- Choose: `K-Skills17/GBP-AI-Discovery-Optimizer`

### Step 2: Configure Project ⚙️
**IMPORTANT:** Click **"Edit"** next to Root Directory

```
┌─────────────────────────────────────────────┐
│ Root Directory: frontend/           [Edit] │
├─────────────────────────────────────────────┤
│ Framework Preset: Next.js              [▼] │
├─────────────────────────────────────────────┤
│ Build Command: npm run build               │
├─────────────────────────────────────────────┤
│ Output Directory: .next                     │
├─────────────────────────────────────────────┤
│ Install Command: npm install               │
└─────────────────────────────────────────────┘
```

### Step 3: Deploy
Click **"Deploy"** and you're done! ✅

---

## ✅ Solution 2: Fix After Import

If you already imported and it shows "Other":

### Go to Settings
1. Open your project in Vercel
2. Click **"Settings"** (top menu)
3. Click **"General"** (left sidebar)

### Update Framework
1. Find **"Framework Preset"**
2. Click dropdown → Select **"Next.js"**
3. Click **"Save"**

### Update Root Directory
1. Find **"Root Directory"**
2. Click **"Edit"**
3. Enter: `frontend`
4. Click **"Save"**

### Redeploy
1. Go to **"Deployments"** tab
2. Click **⋯** (three dots) on latest deployment
3. Click **"Redeploy"**

---

## ✅ Solution 3: Use vercel.json (Already Added!)

I've added a `vercel.json` file to your project root that tells Vercel about your setup.

**After you push to GitHub:**
```bash
git push origin main
```

Vercel will automatically:
- ✅ Detect Next.js
- ✅ Build from frontend folder
- ✅ Deploy correctly

---

## 🎯 Correct Settings Reference

### Your Vercel settings should show:

**Framework:**
- Framework Preset: `Next.js`
- ⚠️ NOT "Other"

**Paths:**
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `.next`

**Environment Variables:**
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

---

## 🔍 How to Verify It's Working

### During Build:
Look for these messages in the deployment logs:

```
✓ Detected Next.js
✓ Installing dependencies...
✓ Building Next.js application...
✓ Compiled successfully
```

### ⚠️ If you see:
```
! No Build Command detected
! No package.json found
```
→ Your Root Directory is wrong. Set it to `frontend`

---

## 🆘 Common Issues & Fixes

### Issue 1: "No package.json found"
**Fix:** Set Root Directory to `frontend`

### Issue 2: Build succeeds but site is blank
**Fix:** Check environment variables are set:
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Issue 3: "Module not found" errors
**Fix:** 
1. Delete the deployment
2. Make sure `frontend/package.json` exists
3. Redeploy

### Issue 4: Build works locally but fails on Vercel
**Fix:** Check Node version:
- Vercel: Settings → General → Node.js Version
- Should be: 18.x or 20.x

---

## 📋 Deployment Checklist

Before deploying, verify:

- [ ] Root Directory set to `frontend`
- [ ] Framework Preset is `Next.js`
- [ ] All 3 environment variables added
- [ ] Latest code pushed to GitHub
- [ ] `frontend/package.json` exists in repo
- [ ] `frontend/next.config.js` exists in repo

---

## 🎯 Expected Result

After correct configuration:

**Build Log Should Show:**
```
> Cloning repository...
✓ Detected Next.js
> Installing dependencies...
✓ Installed
> Building...
✓ Compiled successfully
> Deploying...
✓ Deployment ready
```

**Your Site:**
- ✅ Loads the landing page
- ✅ Shows "AI Discovery Optimizer" header
- ✅ Has the audit form
- ✅ Styled with Tailwind (looks good!)

---

## 🚀 Quick Commands

If you made changes to `vercel.json`:

```bash
# In your project folder
git add vercel.json
git commit -m "Add Vercel config"
git push origin main

# Vercel auto-deploys from GitHub!
```

---

## 💡 Pro Tips

1. **Always set Root Directory first** - This is the #1 mistake
2. **Use the vercel.json file** - I've already created it for you
3. **Check the build logs** - They tell you exactly what's wrong
4. **Test locally first** - Run `npm run build` in the frontend folder

---

## ✅ Final Check

Your deployment is successful when:

1. ✅ Framework shows **"Next.js"** (not Other)
2. ✅ Build completes without errors
3. ✅ Site preview shows your landing page
4. ✅ Form works and styles load
5. ✅ No console errors in browser

---

**Need more help?** Check the full deployment guide in `EASY_DEPLOYMENT.md`

**Still stuck?** The issue is 99% likely to be:
- Root Directory not set to `frontend`
- OR environment variables missing

Fix those two and you're golden! 🎉
