# Railway Deployment Guide for AI Booking Agent

## 🚀 Quick Deploy to Railway

### Prerequisites
- Railway account (free tier available)
- GitHub repository with your code
- API keys for OpenAI/Anthropic (optional)

### Step 1: Prepare Your Repository

1. **Ensure these files are in your repository:**
   - `railway.json` ✅ (created)
   - `backend/Dockerfile` ✅ (updated)
   - `backend/requirements.txt` ✅ (exists)
   - `backend/app/` (your FastAPI app) ✅

2. **Commit and push your changes:**
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

### Step 2: Deploy to Railway

1. **Go to [Railway Dashboard](https://railway.app/dashboard)**
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your repository**
5. **Railway will automatically detect the Dockerfile and deploy**

### Step 3: Configure Environment Variables

In your Railway project dashboard, go to **Variables** tab and add:

#### Required Variables:
```
API_RELOAD=false
USE_MOCK_CALENDAR=true
LOG_LEVEL=INFO
```

#### Optional Variables (for full functionality):
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
LLM_MODEL=gpt-3.5-turbo
```

#### CORS Configuration:
```
CORS_ORIGINS=https://your-frontend-url.railway.app,http://localhost:8501
```

### Step 4: Add Redis (Optional but Recommended)

1. **In Railway dashboard, click "New"**
2. **Select "Database" → "Redis"**
3. **Railway will automatically set REDIS_URL environment variable**

### Step 5: Test Your Deployment

1. **Railway will provide a URL like: `https://your-app-name.railway.app`**
2. **Test the health endpoint: `https://your-app-name.railway.app/health`**
3. **Should return: `{"message": "Booking Agent API is running!", "status": "healthy"}`**

## 🔧 Configuration Details

### Railway.json Configuration
- **Builder**: Uses Dockerfile in backend directory
- **Start Command**: Uses Railway's PORT environment variable
- **Health Check**: Monitors `/health` endpoint
- **Restart Policy**: Automatically restarts on failure

### Environment Variables
- **PORT**: Automatically set by Railway
- **API_RELOAD**: Set to false for production
- **CORS_ORIGINS**: Configure for your frontend domain

### Dockerfile Optimizations
- Uses Python 3.11 slim image
- Non-root user for security
- Proper layer caching
- Production-ready configuration

## 🚨 Important Notes

### 1. **Frontend Deployment**
- Deploy frontend separately as another Railway service
- Update `BOOKING_AGENT_API_URL` to point to your backend URL
- Update CORS_ORIGINS to include your frontend URL

### 2. **File Storage**
- Railway provides ephemeral storage
- Session files will be lost on restarts
- Consider using Redis for session storage

### 3. **Google Calendar**
- Upload credentials file to Railway
- Set `GOOGLE_CALENDAR_CREDENTIALS_FILE` path
- Or keep `USE_MOCK_CALENDAR=true` for testing

### 4. **Monitoring**
- Railway provides built-in monitoring
- Check logs in Railway dashboard
- Use `/health` and `/ready` endpoints for monitoring

## 🔍 Troubleshooting

### Common Issues:

1. **Build Fails**
   - Check requirements.txt for compatibility
   - Ensure all dependencies are listed

2. **App Won't Start**
   - Check logs in Railway dashboard
   - Verify PORT environment variable is set

3. **CORS Errors**
   - Update CORS_ORIGINS with your frontend URL
   - Ensure frontend URL is correct

4. **API Timeouts**
   - Increase `BOOKING_AGENT_API_TIMEOUT`
   - Check if external APIs are accessible

### Debug Commands:
```bash
# Check Railway logs
railway logs

# Check app status
curl https://your-app.railway.app/health

# Check environment variables
railway variables
```

## 📈 Scaling

### Railway Free Tier:
- 500 hours/month
- 512MB RAM
- Shared CPU

### Paid Plans:
- More resources available
- Custom domains
- Better performance

## 🔐 Security Considerations

1. **Environment Variables**: Never commit API keys
2. **CORS**: Restrict to your domains only
3. **HTTPS**: Railway provides automatic HTTPS
4. **Rate Limiting**: Consider adding rate limiting for production

## ✅ Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables configured
- [ ] Health check passing
- [ ] Frontend URL updated in CORS
- [ ] API keys configured (if using)
- [ ] Redis added (optional)
- [ ] Custom domain configured (optional)

Your AI Booking Agent is now ready for Railway deployment! 🎉 