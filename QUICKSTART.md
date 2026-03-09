# Quick Start Guide

Get your LLM Council up and running in 5 minutes!

## Step 1: Install Dependencies

Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

## Step 2: Set Up API Key

1. Get your OpenRouter API key from: https://openrouter.ai/keys

2. Create a `.env` file:
   - Copy `.env.example` to `.env`
   - Or create a new file named `.env`

3. Add your API key to `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

## Step 3: Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Step 4: Start Brainstorming

1. **In the sidebar:**
   - Enter your API key (if not using .env)
   - Select "Default (Recommended)" preset (5 models)
   - Keep default settings

2. **In the main area:**
   - Enter a research prompt, for example:
     ```
     I need ML research ideas for my undergraduate thesis on
     time series analysis. I have limited compute (no GPU) and
     6 months to complete the project.
     ```

3. **Click "Start Brainstorming"**
   - Wait 30-60 seconds for the council to complete
   - Review the top recommendations
   - Download the full report

4. **Optional: Refine Results**
   - Provide feedback like "Focus more on educational applications"
   - Click "Run Next Iteration"
   - Review updated recommendations

## First Time Tips

- **Use the Default preset** - It's balanced and cost-effective (~$0.35/iteration)
- **Be specific** - More details = better recommendations
- **Check your profile** - Edit `config/user_profile.yaml` to match your context
- **Monitor costs** - Check the "Cost Breakdown" tab after each iteration

## Example Session

**Prompt:**
```
Give me research ideas for applying machine learning to education,
suitable for a master's thesis
```

**Expected Output:**
- 15 diverse research ideas (3 per model × 5 models)
- Critical evaluations from all council members
- Top 5 ranked recommendations with:
  - Feasibility assessment
  - Methodology details
  - Timeline estimates
  - Next steps

**Cost:** ~$0.30-$0.40 for one iteration

## Troubleshooting

### "API key cannot be empty"
- Make sure you created the `.env` file
- Check that your API key is correct

### "Insufficient credits"
- Add credits to your OpenRouter account
- Visit: https://openrouter.ai/credits

### "Module not found"
- Reinstall dependencies: `pip install -r requirements.txt`
- Make sure you're in the project directory

### App won't start
- Check Python version: `python --version` (need 3.8+)
- Try: `python -m streamlit run app.py`

## What's Next?

1. **Customize your profile**: Edit `config/user_profile.yaml`
2. **Try different presets**: Budget (cheaper) or Premium (better quality)
3. **Iterate on results**: Provide feedback and refine
4. **Export reports**: Download markdown files from the app

## Need Help?

- Read the full [README.md](README.md)
- Check the model configurations in `config/models.yaml`
- Review example user profile in `config/user_profile.yaml`

---

**Ready to brainstorm?** Run `streamlit run app.py` and let the council help you!
