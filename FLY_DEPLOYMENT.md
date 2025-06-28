# 🚀 Fly.io Deployment Guide for AI Booking Agent

## 📋 Prerequisites

1. **Fly.io Account**: Sign up at [fly.io](https://fly.io)
2. **Fly CLI**: Install the Fly CLI tool
3. **GitHub Repository**: Your code should be in a Git repository
4. **API Keys**: OpenAI/Anthropic API keys (optional)

## 🛠️ Installation

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Windows (with Scoop)
scoop install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Login to Fly.io

```bash
fly auth login
```

## 🚀 Deploy Backend

### 1. Navigate to Project Directory

```bash
cd /path/to/your/booking-agent
```

### 2. Configure Your App

Edit `fly.toml` and update:
- `app = "your-unique-app-name"`
- `primary_region = "your-preferred-region"`

### 3. Deploy the Backend

```bash
# Deploy to Fly.io
fly deploy

# Or if you want to create a new app
fly launch
```

### 4. Set Environment Variables

```bash
# Set your API keys and configuration
fly secrets set OPENAI_API_KEY="your-openai-api-key"
fly secrets set ANTHROPIC_API_KEY="your-anthropic-api-key"
fly secrets set SMTP_HOST="your-smtp-host"
fly secrets set SMTP_USERNAME="your-smtp-username"
fly secrets set SMTP_PASSWORD="your-smtp-password"
fly secrets set FROM_EMAIL="noreply@yourdomain.com"
fly secrets set SECRET_KEY="your-secret-key"
```

### 5. Check Deployment Status

```bash
# Check app status
fly status

# View logs
fly logs

# Open the app
fly open
```

## 🌐 Deploy Frontend (Optional)

If you want to deploy the frontend separately:

### 1. Create Frontend App

```bash
cd frontend
fly launch --name your-frontend-app-name
```

### 2. Configure Frontend

Create a `fly.toml` in the frontend directory:

```toml
app = "your-frontend-app-name"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  BOOKING_AGENT_API_URL = "https://your-backend-app-name.fly.dev"

[http_service]
  internal_port = 8501
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

### 3. Deploy Frontend

```bash
fly deploy
```

## 🔧 Configuration

### Environment Variables

Set these in your Fly.io app:

```bash
# Required
PORT=8080
API_RELOAD=false
USE_MOCK_CALENDAR=true

# Optional (for production)
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
SMTP_HOST=your-smtp-host
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
FROM_EMAIL=noreply@yourdomain.com
SECRET_KEY=your-secret-key
```

### CORS Configuration

Update `backend/app/config/settings.py` with your frontend domain:

```python
CORS_ORIGINS: List[str] = [
    "https://your-frontend-app.fly.dev",
    "http://localhost:8501",  # For local development
]
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
fly logs

# Follow logs
fly logs --follow

# View specific app logs
fly logs --app your-app-name
```

### Check Health

```bash
# Check app health
fly status

# View app info
fly info
```

### Scale Your App

```bash
# Scale to 2 instances
fly scale count 2

# Scale with specific resources
fly scale vm shared-cpu-1x --memory 1024
```

## 🔒 Security

### SSL/TLS

Fly.io automatically provides SSL certificates for your domains.

### Secrets Management

```bash
# Set secrets (encrypted)
fly secrets set MY_SECRET="value"

# List secrets
fly secrets list

# Remove secrets
fly secrets unset MY_SECRET
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs
   fly logs --build
   
   # Rebuild locally
   fly deploy --local-only
   ```

2. **App Not Starting**
   ```bash
   # Check app logs
   fly logs
   
   # SSH into the app
   fly ssh console
   ```

3. **Health Check Failures**
   - Ensure `/health` endpoint exists
   - Check if app is listening on correct port
   - Verify environment variables

### Performance Optimization

```bash
# Monitor resource usage
fly status

# Scale based on usage
fly scale vm shared-cpu-2x --memory 2048

# Enable auto-scaling
fly scale count 1-5
```

## 📈 Production Checklist

- [ ] Set all required environment variables
- [ ] Configure CORS for your frontend domain
- [ ] Set up proper logging
- [ ] Configure email service
- [ ] Set up monitoring and alerts
- [ ] Test all endpoints
- [ ] Configure custom domain (optional)
- [ ] Set up database (if needed)

## 🔗 Useful Commands

```bash
# Deploy
fly deploy

# Rollback
fly deploy --image-label v1

# Destroy app
fly destroy

# List all apps
fly apps list

# View app details
fly info

# Open app in browser
fly open
```

## 📞 Support

- **Fly.io Documentation**: [fly.io/docs](https://fly.io/docs)
- **Community**: [fly.io/community](https://fly.io/community)
- **Status**: [fly.io/status](https://fly.io/status)

Your AI Booking Agent is now ready for production deployment on Fly.io! 🎉 