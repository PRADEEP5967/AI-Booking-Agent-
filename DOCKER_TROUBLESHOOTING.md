# 🐳 Docker Build Troubleshooting Guide

## 🚨 Common Docker Build Issues and Solutions

### 1. **Network Connectivity Issues**

#### **Error: "context canceled" or "failed to do request"**
This usually indicates network connectivity problems when downloading Docker images.

#### **Solutions:**

##### **A. Use Alternative Base Images**
```dockerfile
# Option 1: Use Alpine (smaller, often more reliable)
FROM python:3.11-alpine

# Option 2: Use specific Debian version
FROM python:3.11-slim-bullseye

# Option 3: Use Ubuntu (larger but more stable)
FROM python:3.11-slim-ubuntu
```

##### **B. Configure Docker Registry Mirrors**
Add to `/etc/docker/daemon.json`:
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

##### **C. Use Different Docker Registry**
```bash
# Pull from alternative registry
docker pull registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim
```

### 2. **Build Context Issues**

#### **Error: "failed to copy" or "not found"**
Files not found in build context.

#### **Solutions:**

##### **A. Check .dockerignore**
Ensure `.dockerignore` doesn't exclude needed files:
```dockerignore
# Don't exclude these
!backend/
!backend/requirements.txt
!backend/app/
```

##### **B. Verify File Paths**
```bash
# Check if files exist
ls -la backend/requirements.txt
ls -la backend/app/

# Build from correct directory
docker build -t myapp .
```

### 3. **Dependency Installation Issues**

#### **Error: "pip install failed" or "package not found"**

#### **Solutions:**

##### **A. Add Retry Mechanism**
```dockerfile
RUN pip install --no-cache-dir --retries 3 --timeout 300 -r requirements.txt
```

##### **B. Use Alternative Package Index**
```dockerfile
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

##### **C. Install System Dependencies First**
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*
```

### 4. **Memory and Resource Issues**

#### **Error: "out of memory" or "killed"**

#### **Solutions:**

##### **A. Increase Docker Resources**
- Docker Desktop: Settings → Resources → Memory (increase to 4GB+)
- Docker Engine: Add to `/etc/docker/daemon.json`:
```json
{
  "default-shm-size": "2G",
  "storage-driver": "overlay2"
}
```

##### **B. Build with More Memory**
```bash
docker build --memory=4g --memory-swap=4g -t myapp .
```

### 5. **Platform-Specific Issues**

#### **Error: "exec format error" or "platform not supported"**

#### **Solutions:**

##### **A. Specify Platform**
```bash
docker build --platform linux/amd64 -t myapp .
```

##### **B. Use Multi-Platform Base**
```dockerfile
FROM --platform=linux/amd64 python:3.11-slim
```

### 6. **Railway-Specific Solutions**

#### **A. Use Railway's Build Cache**
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile",
    "buildCommand": "docker build --no-cache -t myapp ."
  }
}
```

#### **B. Alternative Railway Configuration**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r backend/requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

### 7. **Quick Fixes to Try**

#### **A. Clear Docker Cache**
```bash
docker system prune -a
docker builder prune
```

#### **B. Use Different Network**
```bash
docker build --network host -t myapp .
```

#### **C. Build with Verbose Output**
```bash
docker build --progress=plain --no-cache -t myapp .
```

### 8. **Alternative Deployment Methods**

#### **A. Use Railway's Nixpacks (No Dockerfile needed)**
Create `nixpacks.toml`:
```toml
[phases.setup]
nixPkgs = ["python311", "gcc", "postgresql"]

[phases.install]
cmds = ["pip install -r backend/requirements.txt"]

[start]
cmd = "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

#### **B. Use Railway's Python Template**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

### 9. **Testing Locally**

#### **A. Test Docker Build Locally**
```bash
# Build locally first
docker build -t booking-agent .

# Test the image
docker run -p 8000:8000 booking-agent

# Check if it works
curl http://localhost:8000/health
```

#### **B. Use Docker Compose for Testing**
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - USE_MOCK_CALENDAR=true
```

### 10. **Emergency Fallback**

If all else fails, use Railway's built-in Python support:

1. **Remove Dockerfile and railway.json**
2. **Add `runtime.txt` to backend directory:**
   ```
   python-3.11
   ```
3. **Add `Procfile` to backend directory:**
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Deploy directly to Railway**

## 🔧 Current Project Status

Your project has been updated with:
- ✅ **Enhanced Dockerfile** with better error handling
- ✅ **Alternative Dockerfile** using Alpine Linux
- ✅ **Comprehensive troubleshooting guide**
- ✅ **Multiple deployment options**

## 🚀 Next Steps

1. **Try the updated Dockerfile first**
2. **If it fails, try the alternative Alpine version**
3. **If both fail, use the Nixpacks approach**
4. **As last resort, use Railway's built-in Python support**

## 📞 Getting Help

If you continue to have issues:
1. Check Railway's status page
2. Try building locally first
3. Use the verbose build output for debugging
4. Consider using a different deployment platform temporarily

Your AI Booking Agent will be deployed successfully! 🎉 