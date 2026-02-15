# Evolution API Setup on Render

This guide explains how to deploy the Evolution API (WhatsApp integration) on Render so your users can receive audit results via WhatsApp.

## 📱 What is Evolution API?

Evolution API is an open-source WhatsApp Business API that allows you to:
- Send and receive WhatsApp messages programmatically
- Connect via QR code (just like WhatsApp Web)
- Send text, images, and documents
- Receive webhooks for incoming messages

## 🚀 Deployment Steps

### Step 1: Deploy to Render

1. **Push this repository to GitHub** (if not already done)

2. **Connect to Render:**
   - Go to [render.com](https://render.com) and sign in
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select this repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables:**

   Before deploying, you need to set these environment variables:

   **Required:**
   - `SERVER_URL`: Your Evolution API URL (e.g., `https://evolution-api-xxx.onrender.com`)
   - `AUTHENTICATION_API_KEY`: Generate a strong random key (e.g., `openssl rand -hex 32`)
   - `REDIS_URI`: Redis connection string (optional but recommended)

   **Optional:**
   - `WEBHOOK_GLOBAL_URL`: URL to receive incoming message webhooks
   - `DATABASE_CONNECTION_URI`: Auto-filled by Render from the database

4. **Deploy:**
   - Click "Apply" to deploy
   - Wait 5-10 minutes for the deployment to complete
   - Note your Evolution API URL: `https://evolution-api-xxx.onrender.com`

### Step 2: Connect WhatsApp via QR Code

Once deployed, you need to create a WhatsApp instance and connect it:

1. **Create an Instance:**

   ```bash
   curl -X POST https://evolution-api-xxx.onrender.com/instance/create \
     -H "Content-Type: application/json" \
     -H "apikey: YOUR_AUTHENTICATION_API_KEY" \
     -d '{
       "instanceName": "default",
       "qrcode": true,
       "integration": "WHATSAPP-BAILEYS"
     }'
   ```

2. **Get the QR Code:**

   ```bash
   curl -X GET https://evolution-api-xxx.onrender.com/instance/connect/default \
     -H "apikey: YOUR_AUTHENTICATION_API_KEY"
   ```

   This will return a base64 QR code image. You can:
   - Decode it and display in a browser
   - Use the Evolution API dashboard (if enabled)
   - Or visit: `https://evolution-api-xxx.onrender.com/instance/qrcode/default`

3. **Scan the QR Code:**
   - Open WhatsApp on your phone
   - Go to Settings → Linked Devices
   - Tap "Link a Device"
   - Scan the QR code displayed

4. **Verify Connection:**

   ```bash
   curl -X GET https://evolution-api-xxx.onrender.com/instance/connectionState/default \
     -H "apikey: YOUR_AUTHENTICATION_API_KEY"
   ```

   Should return: `{"state":"open"}`

### Step 3: Update Your Backend Configuration

Update your backend `.env` file with the Evolution API details:

```env
# Evolution API (WhatsApp)
EVOLUTION_API_URL=https://evolution-api-xxx.onrender.com
EVOLUTION_API_KEY=your_authentication_api_key_here
EVOLUTION_INSTANCE_NAME=default

# Owner WhatsApp for notifications (Brazilian format)
OWNER_WHATSAPP=5511999991234
```

If you're deploying your backend to Railway, Render, or another platform, make sure to set these environment variables there as well.

### Step 4: Test the Integration

Test sending a message:

```bash
curl -X POST https://evolution-api-xxx.onrender.com/message/sendText/default \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_AUTHENTICATION_API_KEY" \
  -d '{
    "number": "5511999991234",
    "text": "Teste de mensagem do GBP AI Discovery Optimizer!"
  }'
```

If successful, you should receive the message on WhatsApp!

## 🔧 Troubleshooting

### QR Code Expires Before Scanning

The QR code expires after ~30 seconds. If you can't scan it in time:
1. Request a new QR code using the `/instance/connect` endpoint
2. Consider using the Evolution API dashboard for easier QR code scanning

### Instance Disconnects

If your WhatsApp instance disconnects:
1. Check if the phone is connected to the internet
2. Make sure the phone battery isn't in "ultra battery saver" mode
3. Reconnect by generating a new QR code

### Messages Not Sending

1. **Check Instance Status:**
   ```bash
   curl -X GET https://evolution-api-xxx.onrender.com/instance/connectionState/default \
     -H "apikey: YOUR_AUTHENTICATION_API_KEY"
   ```

2. **Check Phone Number Format:**
   - Brazilian numbers should be: `5511999991234` (country code + area code + number)
   - Your backend automatically formats numbers, but double-check

3. **Check Evolution API Logs:**
   - Go to Render dashboard
   - Click on your Evolution API service
   - View logs for errors

### Database Connection Issues

If you see database errors:
1. Make sure the PostgreSQL database is running (check Render dashboard)
2. Verify the `DATABASE_CONNECTION_URI` environment variable is set correctly
3. Check database logs in Render

## 💰 Cost Considerations

**Free Tier:**
- Render Free Tier includes:
  - Web Service: Free (with 750 hours/month)
  - PostgreSQL: Free Starter (256MB RAM, 1GB storage)
  - Evolution API should work fine on free tier for moderate usage

**Paid Plans:**
- If you need better reliability and performance:
  - Web Service: $7/month (Starter plan)
  - PostgreSQL: $7/month (Essential plan)
  - Redis (optional): $10/month

**Important:** Free tier services sleep after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up. Consider upgrading to paid plan for production use.

## 🔐 Security Best Practices

1. **Strong API Key:**
   - Generate with: `openssl rand -hex 32`
   - Never commit to git
   - Store in Render environment variables

2. **Webhook Security:**
   - If using webhooks, validate incoming requests
   - Use HTTPS only
   - Consider IP whitelisting

3. **Phone Number Validation:**
   - Already implemented in `whatsapp_service.py`
   - Validates Brazilian phone format
   - Prevents sending to invalid numbers

## 📊 Monitoring

1. **Render Dashboard:**
   - View logs in real-time
   - Monitor CPU/Memory usage
   - Check deployment status

2. **Evolution API Endpoints:**
   - `/instance/fetchInstances`: List all instances
   - `/instance/connectionState/{instance}`: Check connection
   - Health check: `GET /`

3. **Your Backend Logs:**
   - Watch for WhatsApp send errors
   - Monitor message delivery success rate

## 🔄 Keeping Evolution API Updated

Evolution API releases updates frequently. To update:

1. **Rebuild on Render:**
   - Go to Render dashboard
   - Click on your Evolution API service
   - Click "Manual Deploy" → "Clear build cache & deploy"

2. **Check for Breaking Changes:**
   - Review [Evolution API changelog](https://github.com/EvolutionAPI/evolution-api)
   - Test thoroughly after updating

## 📚 Additional Resources

- [Evolution API Documentation](https://doc.evolution-api.com/)
- [Evolution API GitHub](https://github.com/EvolutionAPI/evolution-api)
- [Render Documentation](https://render.com/docs)
- [WhatsApp Business API Limits](https://developers.facebook.com/docs/whatsapp/api/rate-limits)

## ❓ FAQ

**Q: Can I use multiple phone numbers?**
A: Yes! Create multiple instances with different names (e.g., "default", "support", "sales")

**Q: Will my WhatsApp account get banned?**
A: Evolution API uses the official WhatsApp Web protocol. As long as you:
- Don't spam
- Follow WhatsApp's terms of service
- Send reasonable volumes (<1000 messages/day)
You should be fine. For high-volume use, consider WhatsApp Business API official solution.

**Q: Can I receive messages too?**
A: Yes! Set up a webhook URL in the Evolution API config to receive incoming messages.

**Q: What happens if my phone loses internet?**
A: The Evolution API will try to reconnect automatically. If it fails, you'll need to scan the QR code again.

---

**Need Help?** Open an issue or contact stephen@lkdigital.com.br
