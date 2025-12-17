# Deployment Guide - Render

This guide walks you through deploying the AI Conversational Loan Agent to Render.

## Prerequisites

- GitHub account with your repository pushed
- Render account (free at render.com)
- OpenAI API key

## Step-by-Step Deployment

### 1. Ensure Code is Pushed to GitHub

```bash
cd C:\Ritika\AI-Conversational-Loan-Agent
git add .
git commit -m "Ready for production deployment"
git push origin main  # or your branch name
```

Check your GitHub repo to verify files are pushed.

### 2. Sign Up / Login to Render

- Go to [render.com](https://render.com)
- Sign up with GitHub (easiest option)
- Authorize Render to access your GitHub repositories

### 3. Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Select your `AI-Conversational-Loan-Agent` repository
3. Fill in configuration:

| Setting | Value |
|---------|-------|
| **Name** | `nexus-loan-agent` (or your preferred name) |
| **Environment** | `Docker` |
| **Region** | `Oregon` (or closest to you) |
| **Plan** | `Free` |
| **Auto-deploy** | `Yes` (redeploy on git push) |

### 4. Add Environment Variable

Before deploying, add your OpenAI API key:

1. In the Render settings page, scroll to **Environment**
2. Click **"Add Environment Variable"**
3. Add:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `sk-proj-...` (your full API key)
4. Click **"Save"**

⚠️ **CRITICAL**: Never commit your API key to GitHub. Render keeps it secure.

### 5. Deploy

Click **"Create Web Service"** and wait ~5-10 minutes for:
- Docker image build
- Tesseract-OCR installation
- Python dependencies installation
- Application startup

You can watch the logs in real-time.

### 6. Get Your URL

Once deployed, Render gives you a public URL like:
```
https://nexus-loan-agent.onrender.com
```

This is your live application!

### 7. Access the Application

Open your browser and go to:
```
https://nexus-loan-agent.onrender.com
```

Start a loan application! ✅

---

## Troubleshooting

### Deployment Fails (Docker build error)

**Check logs**: Click "Logs" in Render dashboard
**Common issues**:
- Missing `Dockerfile` or `.dockerignore` → Add them (already in repo)
- Python version incompatible → We use Python 3.11 (compatible)
- Missing dependencies → Check `backend/requirements.txt`

### Service doesn't start

**Error**: `ModuleNotFoundError: No module named 'agents'`

**Solution**: Ensure you're in correct working directory in `app.py`:
- The code already handles this with relative imports ✅

**Error**: `OPENAI_API_KEY not found`

**Solution**: Add environment variable in Render dashboard (Step 4)

### Blank page / 502 Bad Gateway

**Cause**: Service crashed or taking too long to start

**Fix**:
1. Check Render logs for errors
2. Wait longer (first deploy can take 2-3 minutes)
3. Click "Manual Deploy" to retry

### OCR not working (on Linux/Docker)

**Expected**: Tesseract-OCR is installed via Docker ✅

**If still failing**:
```bash
# Render will automatically install via Dockerfile:
RUN apt-get install -y tesseract-ocr poppler-utils
```

No action needed - already configured.

---

## Important Notes

### Cold Starts
Free tier on Render goes to sleep after 30 minutes of inactivity. First request will take ~30 seconds to wake up.

**Solution**: Upgrade to Paid tier ($7/month) for always-on service, or use Railway (pay-per-use).

### File Uploads & PDFs
All uploaded payslips and generated PDFs are stored in the container's `/app/backend/orchestrator/static/` directory.

**Important**: Docker containers are ephemeral. Files are lost when:
- Service restarts
- New deployment occurs

**Solution** (for production):
- Integrate with cloud storage (AWS S3, Google Cloud Storage)
- Use Render's persistent disk (for $7/month, 10 GB included)

### HTTPS
Render automatically provides HTTPS for your domain. ✅

### Scaling
Free tier has limits: 
- 0.5 CPU, 512 MB RAM
- Good for testing, may need upgrade for production with many concurrent users

---

## Updating Your Application

### To Deploy Changes

```bash
# Make your changes locally
cd C:\Ritika\AI-Conversational-Loan-Agent
git add .
git commit -m "Description of changes"
git push origin main
```

Render will automatically:
1. Detect the push
2. Rebuild Docker image
3. Deploy new version

No manual action needed! ✅

### To Update Environment Variables

1. Go to Render dashboard
2. Click your service
3. Click **"Environment"**
4. Edit the variable
5. Changes apply immediately (service doesn't restart)

---

## Production Checklist

Before going live:

- ✅ Dockerfile created
- ✅ `.dockerignore` created
- ✅ `render.yaml` created
- ✅ `app.py` updated for production (dynamic port, host)
- ✅ `script.js` updated for dynamic API URL
- ✅ Environment variables configured in Render
- ✅ All code pushed to GitHub
- ✅ Test end-to-end flow
- ✅ Monitor logs after first deployment

---

## Cost Analysis

| Provider | Free Tier | Paid Tier | Tesseract Support |
|----------|-----------|-----------|-------------------|
| **Render** | 0.5 CPU, 512MB | $7/mo | ✅ Docker included |
| **Railway** | $5/mo credit | Pay-per-use | ✅ Docker included |
| **Heroku** | ❌ Deprecated | $7/mo (legacy) | ⚠️ Limited |
| **PythonAnywhere** | Free | $5/mo | ❌ Not available |

**Recommendation**: Render free tier for testing, upgrade to $7/month when going production. ✅

---

## Support

- **Render Docs**: https://render.com/docs
- **Docker Docs**: https://docs.docker.com
- **Troubleshooting**: Check application logs in Render dashboard

---

## Next Steps

1. ✅ Complete the checklist above
2. ✅ Deploy to Render
3. ✅ Test all features (loan inquiry → payslip upload → KYC → approval → sanction letter)
4. ✅ Monitor logs and performance
5. ✅ Collect user feedback
6. ✅ Plan production upgrade if needed
