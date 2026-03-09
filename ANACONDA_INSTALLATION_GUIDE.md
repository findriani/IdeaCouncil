# Anaconda Fresh Installation Guide

Complete guide to install Anaconda with Python 3.11+ and set up LLM Council.

## Step 1: Uninstall Old Anaconda (Optional but Recommended)

### Windows:

1. **Using Windows Settings:**
   - Press `Win + I` to open Settings
   - Go to "Apps" → "Apps & Features"
   - Search for "Anaconda" or "Python"
   - Click "Uninstall" for each

2. **Manual Cleanup (if needed):**
   - Delete folder: `C:\Users\[YourUsername]\Anaconda3`
   - Delete folder: `C:\Users\[YourUsername]\.conda`
   - Delete folder: `C:\Users\[YourUsername]\AppData\Local\Continuum`

3. **Clean Environment Variables:**
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Go to "Advanced" → "Environment Variables"
   - Remove any paths containing "Anaconda" or old Python paths
   - Common paths to remove:
     ```
     C:\Users\[YourUsername]\Anaconda3
     C:\Users\[YourUsername]\Anaconda3\Scripts
     C:\Users\[YourUsername]\Anaconda3\Library\bin
     ```

## Step 2: Download Latest Anaconda

1. **Go to:** https://www.anaconda.com/download
2. **Download:** Anaconda for Windows (latest version)
   - Should include Python 3.11 or 3.12
   - File size: ~600-800 MB
3. **Save** the installer (e.g., `Anaconda3-2024.02-1-Windows-x86_64.exe`)

## Step 3: Install Anaconda

1. **Run the installer** (as Administrator if possible)
2. **Installation options:**
   - ✅ "Just Me (recommended)"
   - ✅ Default installation location is fine
   - ⚠️ **IMPORTANT:** Check "Add Anaconda to my PATH environment variable"
     - Yes, even though it says "not recommended"
     - This makes it easier to use from command prompt
   - ✅ "Register Anaconda as my default Python"
3. **Click "Install"** (takes 5-10 minutes)
4. **Click "Finish"**

## Step 4: Verify Installation

Open a **new** Command Prompt or PowerShell (must be new for PATH to update):

```bash
# Check Anaconda
conda --version
# Should show: conda 24.x.x

# Check Python
python --version
# Should show: Python 3.11.x or 3.12.x

# Check pip
pip --version
# Should show: pip 24.x from anaconda3...
```

All three commands should work! ✅

## Step 5: Create Environment for LLM Council (Recommended)

Creating a dedicated environment keeps things clean:

```bash
# Create new environment with Python 3.11
conda create -n llmcouncil python=3.11 -y

# Activate the environment
conda activate llmcouncil

# Verify
python --version
# Should show: Python 3.11.x
```

**Note:** You'll need to activate this environment each time:
```bash
conda activate llmcouncil
```

## Step 6: Install LLM Council Dependencies

Navigate to your project:

```bash
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"
```

Install packages:

```bash
pip install -r requirements.txt
```

This should work perfectly now! ✅

## Step 7: Set Up API Key

Create `.env` file:

```bash
copy .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

## Step 8: Verify Everything Works

```bash
# Run verification script
python verify_installation.py

# If all checks pass, run the app
streamlit run app.py
```

Your browser should open automatically to `http://localhost:8501` 🎉

## Quick Reference Commands

### Every time you want to use the app:

```bash
# 1. Activate environment (if you created one)
conda activate llmcouncil

# 2. Navigate to project
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"

# 3. Run app
streamlit run app.py
```

### To deactivate environment:

```bash
conda deactivate
```

## Troubleshooting

### "conda is not recognized"

**Fix:**
1. Close and reopen your terminal (must be NEW window)
2. If still not working, add Anaconda to PATH manually:
   - Open Environment Variables
   - Add to PATH:
     ```
     C:\Users\[YourUsername]\anaconda3
     C:\Users\[YourUsername]\anaconda3\Scripts
     C:\Users\[YourUsername]\anaconda3\Library\bin
     ```
3. Restart terminal

### "python is not recognized"

**Fix:**
1. Run: `conda activate llmcouncil`
2. Try again

### Installation fails with "Solving environment"

**Fix:**
```bash
# Update conda
conda update conda

# Try again
conda create -n llmcouncil python=3.11 -y
```

### Package installation fails

**Fix:**
```bash
# Update pip
python -m pip install --upgrade pip

# Clear cache
pip cache purge

# Install again
pip install -r requirements.txt
```

## Alternative: Use Base Environment

If you don't want a separate environment, just use the base:

```bash
# Navigate to project
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"

# Install directly
pip install -r requirements.txt

# Run app
streamlit run app.py
```

## Recommended Setup (Best Practice)

**Use a dedicated environment:**

✅ **Pros:**
- Isolated dependencies
- Can't break other projects
- Easy to recreate
- Clean uninstall

❌ **Cons:**
- Need to remember to activate
- Slightly more disk space

**Command to remember:**
```bash
conda activate llmcouncil
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"
streamlit run app.py
```

## Expected Package Versions (with Python 3.11+)

After installation, you should have:

```
streamlit: 1.31+ ✅
httpx: 0.26+ ✅
pyyaml: 6.0+ ✅
python-dotenv: 1.0+ ✅
pandas: 2.0+ ✅
scipy: 1.11+ ✅
```

## Testing Your Installation

### Quick test:

```bash
python -c "import streamlit, httpx, yaml, pandas, scipy; print('All packages imported successfully! ✅')"
```

### Full verification:

```bash
python verify_installation.py
```

Should show all ✅ PASS

## Next Steps After Installation

1. ✅ Anaconda installed with Python 3.11+
2. ✅ Environment created (optional but recommended)
3. ✅ Dependencies installed
4. ✅ API key configured in `.env`
5. ✅ Verification passed

**You're ready to run:**

```bash
streamlit run app.py
```

## Conda Cheat Sheet

```bash
# List environments
conda env list

# Create environment
conda create -n myenv python=3.11

# Activate environment
conda activate myenv

# Deactivate environment
conda deactivate

# Delete environment
conda env remove -n myenv

# Update conda
conda update conda

# Install package
conda install package_name
# OR
pip install package_name
```

## Support

- **Anaconda Docs:** https://docs.anaconda.com/
- **Conda Cheat Sheet:** https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html

## Summary

**Installation time:** 20-30 minutes total
- Uninstall old: 5 min
- Download: 5 min
- Install: 10 min
- Setup project: 10 min

**After fresh installation, run:**

```bash
conda activate llmcouncil
cd "D:\Ilkom ULM\Penelitian\LLMCouncil"
streamlit run app.py
```

Good luck with the installation! 🚀
