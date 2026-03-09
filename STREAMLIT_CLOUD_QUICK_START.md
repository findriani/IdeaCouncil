# Streamlit Cloud - Quick Start Guide

Deploy your LLM Council app online in **20-30 minutes**! 🚀

## What You'll Need

- ✅ GitHub account (free) - https://github.com/signup
- ✅ Your OpenRouter API key
- ✅ 20-30 minutes of time

## Three Easy Steps

### 📤 Step 1: Upload to GitHub (10 minutes)

**Option A: Using the Helper Script (Easiest)**

```bash
# Windows users:
deploy_to_github.bat

# Mac/Linux users:
./deploy_to_github.sh
```

The script will guide you through:
1. Creating a GitHub repository
2. Uploading your code
3. Next steps

**Option B: Manual GitHub Upload**

1. Go to https://github.com/new
2. Create new repository:
   - Name: `LLMCouncil`
   - Visibility: **Public** (required for free tier)
   - Don't initialize with README
3. Open terminal in your project folder
4. Run these commands:

```bash
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"
git init
git add .
git commit -m "Initial commit: LLM Council"
git remote add origin https://github.com/YOUR_USERNAME/LLMCouncil.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### 🚀 Step 2: Deploy to Streamlit Cloud (5 minutes)

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Click "Sign in with GitHub"
   - Authorize Streamlit Cloud

2. **Create New App**
   - Click "New app" button
   - Fill in the form:
     ```
     Repository: YOUR_USERNAME/LLMCouncil
     Branch: main
     Main file path: app.py
     App URL: llm-council-yourusername (choose your own)
     ```
   - Click "Deploy!"

3. **Wait for Initial Deploy**
   - Takes 2-5 minutes
   - Will show errors (expected - we haven't added API key yet)

### 🔐 Step 3: Add Your API Key (5 minutes)

1. **Open App Settings**
   - Click "⋮" (three dots) in the top-right
   - Select "Settings"

2. **Add Secrets**
   - Go to "Secrets" section
   - Paste this (replace with your real key):
   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-your-actual-key-here"
   ```
   - Click "Save"

3. **Wait for Redeploy**
   - App automatically redeploys (1-2 minutes)
   - Your app is now live! 🎉

## Your App is Live!

Visit your app at:
```
https://your-app-name.streamlit.app
```

Share it with anyone! 🌐

## Testing Your Deployed App

1. Open your app URL
2. The API key should already be configured (from secrets)
3. Select "Budget" preset (for testing)
4. Enter a simple prompt:
   ```
   Give me 3 ML research ideas for undergraduate thesis
   ```
5. Click "Start Brainstorming"
6. Wait ~30 seconds
7. Review results!

## Troubleshooting

### "This app has encountered an error"

**Check the logs:**
1. Click "⋮" → "Settings" → "Logs"
2. Look for error messages

**Common fixes:**
- Verify API key in Secrets (no typos, correct format)
- Make sure all files are on GitHub
- Check requirements.txt is correct

### "API key cannot be empty"

**Fix:**
1. Go to Settings → Secrets
2. Add:
   ```toml
   OPENROUTER_API_KEY = "your-key-here"
   ```
3. No extra quotes, no spaces
4. Save and wait for redeploy

### "Module not found"

**Fix:**
1. Make sure `requirements.txt` is in your GitHub repo
2. If you just added it:
   ```bash
   git add requirements.txt
   git commit -m "Add requirements"
   git push
   ```
3. Streamlit Cloud will auto-redeploy

### App is slow

**Fix:**
- Use "Budget" preset (3 models instead of 5)
- Reduce "Ideas per Member" to 2
- Free tier has limited resources

## Updating Your App

Made changes locally? Update the deployed app:

```bash
git add .
git commit -m "Update: description of changes"
git push
```

Streamlit Cloud automatically redeploys when you push to GitHub! 🔄

## Managing Costs

⚠️ **Important:** If you make your app public with your API key:
- **YOU** pay for all usage
- Users can rack up costs quickly

**Recommended approach:**
- Let users enter their own API keys
- Or set daily spending limits on OpenRouter
- Or use demo mode (see DEPLOYMENT_GUIDE.md)

## Advanced: Custom URL

Free tier gives you:
```
https://your-app-name.streamlit.app
```

Want a custom domain?
- Requires Streamlit Cloud Teams (paid plan)
- Or use a service like Cloudflare

## Getting Help

**Resources:**
- Full guide: `DEPLOYMENT_GUIDE.md`
- Checklist: `DEPLOYMENT_CHECKLIST.md`
- Streamlit docs: https://docs.streamlit.io/streamlit-community-cloud
- OpenRouter docs: https://openrouter.ai/docs

**Common Questions:**

**Q: Is Streamlit Cloud free?**
A: Yes! Free tier includes 1 GB RAM, 1 CPU core, public apps.

**Q: Do I need a credit card?**
A: No for free tier. Yes for OpenRouter API.

**Q: Can I make my app private?**
A: Only with paid Streamlit Cloud Teams plan.

**Q: How do I delete my app?**
A: Settings → General → Delete app

**Q: Can I use my own domain?**
A: Only with paid plan.

## Success Checklist

Once deployed, verify:

- [ ] App URL is accessible
- [ ] No errors on homepage
- [ ] Can select models
- [ ] Can enter prompts
- [ ] "Start Brainstorming" works
- [ ] Ideas are generated
- [ ] Report downloads work
- [ ] Cost tracking displays

## Share Your App!

Your app is now online! Share it:

**Direct link:**
```
https://your-app-name.streamlit.app
```

**Embed in website:**
```html
<iframe
  src="https://your-app-name.streamlit.app"
  width="100%"
  height="800">
</iframe>
```

**Social media:**
```
Check out my LLM Council app!
🧠 Multi-AI research brainstorming
🚀 https://your-app-name.streamlit.app
```

## Congratulations! 🎉

You've successfully deployed your LLM Council application to the cloud!

**What's next?**
- Use it for real research brainstorming
- Share with colleagues
- Add enhancements from Karpathy's approach
- Monitor usage and costs
- Collect feedback and improve

---

**Need help?** See `DEPLOYMENT_GUIDE.md` for detailed instructions.

**Happy brainstorming!** 🚀
