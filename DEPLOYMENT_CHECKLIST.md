# Streamlit Cloud Deployment Checklist

## Pre-Deployment (Local Setup)

- [ ] All code is working locally
- [ ] Tested with `streamlit run app.py`
- [ ] `.env` file has your API key (for local testing)
- [ ] `.gitignore` includes `.env` and `.streamlit/secrets.toml`
- [ ] All dependencies are in `requirements.txt`
- [ ] Updated `config/settings.py` to handle Streamlit secrets ✅ (already done)

## GitHub Setup

- [ ] Create GitHub account (if you don't have one)
- [ ] Create new public repository named `LLMCouncil`
- [ ] Initialize git in your project:
  ```bash
  cd "D:\Ilkom ULM\Penelitian\LLMCouncil"
  git init
  git add .
  git commit -m "Initial commit: LLM Council application"
  ```
- [ ] Connect to GitHub remote:
  ```bash
  git remote add origin https://github.com/YOUR_USERNAME/LLMCouncil.git
  git branch -M main
  git push -u origin main
  ```

## Streamlit Cloud Setup

- [ ] Go to https://share.streamlit.io/
- [ ] Sign in with GitHub account
- [ ] Authorize Streamlit Cloud to access your repositories

## Deploy App

- [ ] Click "New app" in Streamlit Cloud
- [ ] Select repository: `YOUR_USERNAME/LLMCouncil`
- [ ] Select branch: `main`
- [ ] Main file path: `app.py`
- [ ] Choose app URL: `llm-council-yourusername` (or your preferred name)
- [ ] Click "Deploy!"

## Configure Secrets

- [ ] Wait for initial deployment (it will show errors - this is expected)
- [ ] Click "⋮" (three dots) → "Settings"
- [ ] Go to "Secrets" section
- [ ] Add your API key:
  ```toml
  OPENROUTER_API_KEY = "sk-or-v1-your-actual-key"
  ```
- [ ] Click "Save"
- [ ] App will auto-redeploy

## Verify Deployment

- [ ] Wait for deployment to complete (2-5 minutes)
- [ ] Visit your app URL: `https://your-app-name.streamlit.app`
- [ ] Check that API key is recognized (no error message)
- [ ] Test a simple brainstorming session:
  - Use Budget preset (3 models)
  - Enter a simple prompt
  - Verify it generates ideas
- [ ] Check cost tracking works
- [ ] Test download report feature

## Post-Deployment

- [ ] Share your app URL with others
- [ ] Monitor usage at https://openrouter.ai/activity
- [ ] Check Streamlit Cloud metrics in app settings
- [ ] Update README.md with your deployed URL

## Troubleshooting

### If deployment fails:

**"API key cannot be empty"**
- [ ] Verify secrets format in Streamlit Cloud settings
- [ ] Ensure no extra quotes or spaces
- [ ] Check secret name is exactly `OPENROUTER_API_KEY`

**"Module not found"**
- [ ] Check `requirements.txt` is in root directory
- [ ] Verify all packages are listed
- [ ] Push updated requirements:
  ```bash
  git add requirements.txt
  git commit -m "Update requirements"
  git push
  ```

**"File not found"**
- [ ] Verify all config files are committed:
  ```bash
  git add config/
  git commit -m "Add config files"
  git push
  ```

**App is slow or times out**
- [ ] Use Budget preset (fewer models)
- [ ] Reduce concurrent requests
- [ ] Reduce ideas per member to 2

## Optional: Custom Configuration

**For public demo (limited features):**

Add to Streamlit secrets:
```toml
DEMO_MODE = "true"
```

**Update app.py** to check demo mode and limit features.

## Success Criteria

✅ App is accessible at your URL
✅ API key is working
✅ Can generate ideas successfully
✅ Reports download correctly
✅ No errors in Streamlit Cloud logs

## Your Deployed URL

Once deployed, your app will be available at:
```
https://your-app-name.streamlit.app
```

Share it with the world! 🚀

## Estimated Time

- **GitHub setup**: 5-10 minutes
- **Streamlit Cloud setup**: 5 minutes
- **Configuration**: 5 minutes
- **Testing**: 5-10 minutes
- **Total**: 20-35 minutes

## Need Help?

See detailed guide: `DEPLOYMENT_GUIDE.md`
