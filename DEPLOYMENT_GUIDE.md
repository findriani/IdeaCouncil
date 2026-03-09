# Deploying LLM Council to Streamlit Cloud

## Overview

Streamlit Cloud is a free hosting service for Streamlit apps. This guide shows you how to deploy your LLM Council application online.

## Prerequisites

1. GitHub account (free)
2. Streamlit Cloud account (free - uses GitHub login)
3. Your OpenRouter API key

## Step-by-Step Deployment

### Step 1: Create GitHub Repository

**Option A: Using GitHub Website**

1. Go to https://github.com/new
2. Create a new repository:
   - Name: `LLMCouncil` (or your preferred name)
   - Description: "Multi-LLM Research Brainstorming Council"
   - Visibility: **Public** (required for free Streamlit Cloud)
   - **Do NOT** initialize with README (you already have one)
3. Click "Create repository"

**Option B: Using Git Command Line**

```bash
# Navigate to your project
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: LLM Council application"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/LLMCouncil.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 2: Prepare for Deployment

**Create `.streamlit/config.toml` (Optional - for custom theme)**

```bash
mkdir .streamlit
```

Create file: `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
```

**Update `.gitignore` to exclude secrets:**

Make sure your `.gitignore` includes:
```
.env
.streamlit/secrets.toml
outputs/
*.log
__pycache__/
```

**Commit these changes:**

```bash
git add .streamlit/config.toml
git add .gitignore
git commit -m "Add Streamlit Cloud configuration"
git push
```

### Step 3: Sign Up for Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "Sign up" or "Sign in"
3. Sign in with your GitHub account
4. Authorize Streamlit Cloud to access your repositories

### Step 4: Deploy Your App

1. Click "New app" button
2. Fill in deployment settings:
   - **Repository**: Select `YOUR_USERNAME/LLMCouncil`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Choose a custom URL like `llm-council-yourusername`

3. Click "Deploy!"

**Initial deployment will fail** because we haven't configured the API key yet. This is expected!

### Step 5: Configure Secrets (API Key)

After deployment starts, you'll see the app settings:

1. Click on "⋮" (three dots) → "Settings"
2. Go to "Secrets" section
3. Add your secrets in TOML format:

```toml
# .streamlit/secrets.toml format

OPENROUTER_API_KEY = "sk-or-v1-your-actual-api-key-here"
```

4. Click "Save"
5. The app will automatically redeploy

### Step 6: Update Code to Use Streamlit Secrets

Update `config/settings.py` to handle both local `.env` and Streamlit Cloud secrets:

```python
# config/settings.py

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Manages application configuration."""

    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent
        self.outputs_dir = self.project_root / "outputs"

        # Ensure outputs directory exists
        self.outputs_dir.mkdir(exist_ok=True)

        # Load configurations
        self.models_config = self._load_yaml("models.yaml")
        self.user_profile = self._load_yaml("user_profile.yaml")

        # API configuration - Handle both local and Streamlit Cloud
        self.openrouter_api_key = self._get_api_key()
        self.openrouter_base_url = "https://openrouter.ai/api/v1"

        # Session defaults
        self.max_iterations = 3
        self.max_concurrent_requests = 5
        self.request_timeout = 60
        self.max_retries = 3

    def _get_api_key(self) -> str:
        """Get API key from environment or Streamlit secrets."""
        # Try environment variable first (local development)
        api_key = os.getenv("OPENROUTER_API_KEY", "")

        if api_key:
            return api_key

        # Try Streamlit secrets (cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "OPENROUTER_API_KEY" in st.secrets:
                return st.secrets["OPENROUTER_API_KEY"]
        except Exception:
            pass

        return ""

    # ... rest of the Settings class remains the same
```

**Commit and push this change:**

```bash
git add config/settings.py
git commit -m "Add support for Streamlit Cloud secrets"
git push
```

Streamlit Cloud will automatically redeploy when it detects the push.

### Step 7: Verify Deployment

1. Wait for deployment to complete (usually 2-5 minutes)
2. Your app will be available at: `https://YOUR_APP_URL.streamlit.app`
3. Test the app:
   - Check if API key is recognized
   - Try a simple brainstorming session
   - Verify all features work

## Troubleshooting

### Issue: "API key cannot be empty"

**Solution:**
1. Go to app settings → Secrets
2. Verify the secret is formatted correctly:
   ```toml
   OPENROUTER_API_KEY = "your-key-here"
   ```
3. Make sure there are no extra quotes or spaces
4. Save and wait for redeploy

### Issue: "Module not found"

**Solution:**
Make sure `requirements.txt` is in the root directory and includes all dependencies:
```bash
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Issue: "File not found" errors

**Solution:**
Check that all config files are committed:
```bash
git add config/models.yaml config/user_profile.yaml
git commit -m "Add config files"
git push
```

### Issue: App is slow or times out

**Solution:**
Streamlit Cloud has resource limits. For better performance:
1. Use Budget preset (fewer models)
2. Reduce max concurrent requests in settings
3. Consider upgrading to Streamlit Cloud Teams (paid)

### Issue: "This app has exceeded its resource limits"

**Solution:**
Streamlit Cloud free tier has limitations:
- CPU: 1 core
- Memory: 1 GB
- Concurrent users: Limited

If you hit limits:
1. Use fewer models (Budget preset)
2. Reduce ideas per member
3. Deploy to alternative platforms (see below)

## Advanced Configuration

### Custom Domain (Streamlit Cloud Teams only)

If you upgrade to Teams plan, you can use a custom domain:
1. Settings → General → Custom subdomain
2. Follow DNS configuration instructions

### Environment-Specific Settings

Update `config/settings.py` to detect environment:

```python
def is_cloud_deployment(self) -> bool:
    """Check if running on Streamlit Cloud."""
    try:
        import streamlit as st
        return hasattr(st, "secrets")
    except:
        return False
```

Use this to adjust settings:
```python
if self.is_cloud_deployment():
    # Cloud-optimized settings
    self.max_concurrent_requests = 3  # Lower for cloud
else:
    # Local development settings
    self.max_concurrent_requests = 5
```

## Alternative Deployment Options

If Streamlit Cloud doesn't work for you, consider:

### Option 1: Hugging Face Spaces

```bash
# Create account at huggingface.co
# Create new Space with Streamlit SDK
# Push your code to the Space repository
```

**Pros:** More generous free tier, GPU options
**Cons:** Requires Hugging Face account

### Option 2: Railway.app

```bash
# Connect GitHub repository
# Add OPENROUTER_API_KEY environment variable
# Deploy
```

**Pros:** Easy deployment, good free tier
**Cons:** Credit card required for free tier

### Option 3: Google Cloud Run

```bash
# Create Dockerfile
# Build and push to Google Container Registry
# Deploy to Cloud Run
```

**Pros:** Scalable, pay-per-use
**Cons:** More complex setup, requires GCP account

### Option 4: Heroku

```bash
# Create Procfile
# Add buildpacks
# Deploy to Heroku
```

**Pros:** Simple deployment
**Cons:** Free tier discontinued, now requires payment

## Best Practices for Cloud Deployment

### 1. Security

✅ **DO:**
- Use Streamlit secrets for API keys
- Keep `.env` in `.gitignore`
- Use environment-specific configurations

❌ **DON'T:**
- Commit API keys to GitHub
- Hardcode secrets in code
- Share secrets in public repositories

### 2. Performance

✅ **DO:**
- Use Budget preset for public demos
- Implement caching with `@st.cache_data`
- Optimize concurrent requests

❌ **DON'T:**
- Run Premium preset on free tier
- Allow unlimited iterations
- Skip rate limiting

### 3. Cost Management

✅ **DO:**
- Set reasonable default values
- Display cost estimates prominently
- Warn users about API costs

❌ **DON'T:**
- Let users accidentally spend $100+
- Hide cost information
- Use expensive models by default

## Monitoring Your Deployment

### Streamlit Cloud Metrics

1. Go to your app settings
2. Click "Metrics" tab
3. Monitor:
   - Active users
   - Resource usage
   - Error rates
   - Deployment history

### OpenRouter Usage

1. Go to https://openrouter.ai/activity
2. Monitor:
   - API calls
   - Token usage
   - Costs
   - Rate limits

## Updating Your Deployed App

### Method 1: Push to GitHub (Automatic)

```bash
# Make changes locally
# Commit and push
git add .
git commit -m "Update feature X"
git push

# Streamlit Cloud auto-redeploys
```

### Method 2: Manual Redeploy

1. Go to Streamlit Cloud dashboard
2. Click "⋮" → "Reboot app"
3. App will restart with latest code

## Sharing Your App

Once deployed, share your app:

**Public URL:**
```
https://your-app-name.streamlit.app
```

**Embed Options:**
- Share direct link
- Embed in iframe
- Add to portfolio/resume

**Usage Tips for Users:**
- Provide sample prompts
- Explain cost implications
- Set reasonable defaults
- Include documentation link

## Cost Estimates for Public Deployment

If you make your app public:

**Free Tier Limits:**
- Streamlit Cloud: Free (with limits)
- OpenRouter API: Pay per use

**Expected Costs:**
- **You (app owner):** $0 (Streamlit hosting is free)
- **Users:** Pay for their own API keys
- **If you provide API key:** Could be expensive! Users may rack up costs.

**Recommendation:**
Have each user provide their own OpenRouter API key in the sidebar. This way:
- You don't pay for others' usage
- Users are aware of their own costs
- More sustainable model

## Example: Public Demo Configuration

For a public demo with limited features:

```python
# app.py - Add demo mode

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    st.warning("🎮 Demo Mode: Limited to Budget preset, 1 iteration, 2 ideas per member")

    # Override settings
    config["max_iterations"] = 1
    config["ideas_per_member"] = 2

    # Force budget preset
    selected_models = ["gemini", "gpt4o_mini"]
```

Set in Streamlit secrets:
```toml
DEMO_MODE = "true"
```

## Summary

**Quick Deployment Checklist:**

1. ✅ Create GitHub repository
2. ✅ Push code to GitHub
3. ✅ Sign up for Streamlit Cloud
4. ✅ Deploy app from GitHub
5. ✅ Configure secrets (API key)
6. ✅ Update `settings.py` to use secrets
7. ✅ Test deployed app
8. ✅ Share your URL!

**Your app will be live at:**
```
https://your-app-name.streamlit.app
```

**Estimated deployment time:** 15-30 minutes

Good luck with your deployment! 🚀
