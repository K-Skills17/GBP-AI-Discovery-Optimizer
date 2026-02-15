# 🚀 Quick Deployment Guide

This guide shows you how to deploy your app with WhatsApp integration.

## Current Issue

✅ **What works:** Users can run audits and see results
❌ **What doesn't work:** WhatsApp notifications aren't sent

**Why?** The Evolution API (WhatsApp service) is configured for `http://localhost:8080`, which isn't deployed.

## Solution: Deploy Evolution API to Render

### Option 1: One-Click Render Deployment (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Evolution API deployment config"
   git push
   ```

2. **Deploy to Render:**
   - Go to [render.com](https://render.com)
   - Click "New" → "Blueprint"
   - Connect this repository
   - Render will read `render.yaml` and create:
     - Evolution API web service
     - PostgreSQL database

3. **Set Environment Variables in Render:**
   - `SERVER_URL`: Your Evolution API URL (e.g., `https://evolution-api-xxx.onrender.com`)
   - `AUTHENTICATION_API_KEY`: Generate with `openssl rand -hex 32`
   - Optional: `REDIS_URI` for better performance

4. **Connect WhatsApp:**
   - Once deployed, visit: `https://evolution-api-xxx.onrender.com/instance/qrcode/default`
   - Scan with WhatsApp (like WhatsApp Web)
   - Done! ✅

5. **Update Your Backend:**
   Update these env vars in your backend (Railway/Render/wherever it's deployed):
   ```env
   EVOLUTION_API_URL=https://evolution-api-xxx.onrender.com
   EVOLUTION_API_KEY=your_authentication_api_key
   EVOLUTION_INSTANCE_NAME=default
   OWNER_WHATSAPP=5511999991234
   ```

6. **Test:**
   - Run a new audit
   - User should receive WhatsApp message! 🎉

### Option 2: Manual Docker Deployment

If you prefer Docker on your own server:

```bash
# 1. Clone Evolution API
git clone https://github.com/EvolutionAPI/evolution-api
cd evolution-api

# 2. Configure
cp .env.example .env
# Edit .env with your settings

# 3. Run
docker-compose up -d

# 4. Update your backend .env
EVOLUTION_API_URL=http://your-server-ip:8080
```

## Architecture After Deployment

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Frontend  │────────▶│   Backend    │────────▶│  Evolution API  │
│  (Vercel)   │         │  (Railway)   │         │   (Render)      │
└─────────────┘         └──────────────┘         └─────────────────┘
                               │                          │
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐         ┌─────────────────┐
                        │   Supabase   │         │    WhatsApp     │
                        │  (Database)  │         │  (User's Phone) │
                        └──────────────┘         └─────────────────┘
```

## Cost Estimate

### Free Tier (Good for Testing)
- **Evolution API**: Free on Render (750 hours/month)
- **PostgreSQL**: Free Starter (256MB RAM)
- **Total**: $0/month

**Limitations:**
- Service sleeps after 15min of inactivity (wakes in ~30s)
- Limited database storage (1GB)
- Good for <100 messages/day

### Production (Recommended)
- **Evolution API**: $7/month (Starter plan)
- **PostgreSQL**: $7/month (Essential plan)
- **Optional Redis**: $10/month
- **Total**: $14-24/month

**Benefits:**
- Always on (no sleep)
- Better performance
- More storage
- Suitable for hundreds of audits/day

## Troubleshooting

### "Messages not sending"
1. Check Evolution API is deployed and running
2. Verify WhatsApp is connected (check QR code status)
3. Check backend env vars are correct
4. Test manually with curl (see EVOLUTION_API_SETUP.md)

### "QR code expired"
- QR codes expire after 30 seconds
- Generate a new one: Visit `/instance/connect/default`

### "Instance disconnected"
- Phone lost internet connection
- Phone in ultra battery saver mode
- Solution: Reconnect by scanning new QR code

## Next Steps

1. ✅ Deploy Evolution API to Render
2. ✅ Connect WhatsApp via QR code
3. ✅ Update backend environment variables
4. ✅ Test with a real audit
5. 🎉 Celebrate working WhatsApp integration!

## Need Help?

- Full setup guide: [EVOLUTION_API_SETUP.md](./EVOLUTION_API_SETUP.md)
- Evolution API docs: https://doc.evolution-api.com/
- Open an issue or contact: stephen@lkdigital.com.br
