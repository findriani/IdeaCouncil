# LLM Council - Quick Reference Card

## 🚀 Start the App

```bash
streamlit run app.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main application - run this |
| `.env` | Your API key (create from `.env.example`) |
| `config/user_profile.yaml` | Your research profile |
| `config/models.yaml` | Model configurations |
| `README.md` | Full documentation |
| `FINAL_SUMMARY.md` | Complete overview |

## 🎯 Workflow

1. **Input** → Enter research prompt
2. **Diverge** → Models generate ideas (parallel)
3. **Criticize** → Models evaluate ideas (sequential)
4. **Converge** → Synthesis of top recommendations
5. **Iterate** → Provide feedback, run again (optional)

## 💰 Cost Estimates

| Preset | Models | Cost/Iteration | Cost/Session (3 iterations) |
|--------|--------|----------------|----------------------------|
| Budget | 3 | $0.10-$0.15 | $0.30-$0.45 |
| Default | 5 | $0.30-$0.40 | $1.00-$1.20 |
| Premium | 7 | $0.80-$1.20 | $2.50-$3.50 |

## 🔧 Configuration

### Default Models (5)
- Claude 3.5 Sonnet
- Gemini 2.0 Flash (Free)
- ChatGPT 4o
- Kimi (Moonshot)
- GLM-4 Plus

### Budget Models (3)
- Gemini (Free)
- GPT-4o Mini
- Claude Haiku

### Premium Models (7)
- All default + Claude Opus + GPT-4 Turbo

## 📊 Output

- **Ideas**: 3 per model × number of models
- **Critiques**: Each model reviews all others' ideas
- **Top Recommendations**: Top 5 ranked ideas
- **Report**: Comprehensive markdown file
- **Cost**: Detailed breakdown by phase and model

## 🛠️ Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_installation.py

# Run application
streamlit run app.py

# Run tests
pytest tests/test_basic.py -v

# Test enhancements
python -c "from core.anonymizer import IdeaAnonymizer; print('OK')"
python -c "from core.ranker import RankingAggregator; print('OK')"
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key cannot be empty" | Add key to `.env` file |
| "Insufficient credits" | Add credits at openrouter.ai/credits |
| "Module not found" | Run `pip install -r requirements.txt` |
| App won't start | Try `python -m streamlit run app.py` |

## 📖 Documentation

- `QUICKSTART.md` - 5-minute setup
- `README.md` - Full guide
- `FINAL_SUMMARY.md` - Complete overview
- `KARPATHY_DETAILED_COMPARISON.md` - Enhancements
- `INTEGRATION_GUIDE.md` - How to integrate enhancements

## ✨ New Features (Optional)

**Already Created, Ready to Integrate:**
- `core/anonymizer.py` - Blind peer review
- `core/ranker.py` - Borda count voting

**Integration Time:**
- Anonymization: 2-3 hours
- Ranking: 2-3 hours
- Both: 6-8 hours

**See:** `INTEGRATION_GUIDE.md`

## 🎓 Example Prompts

**Vague:**
```
Give me ML research ideas for my thesis
```

**Specific:**
```
I need ML research ideas for time series analysis, suitable for
undergraduate thesis, no deep learning (limited compute), must
complete in 6 months, using public datasets.
```

**With Constraints:**
```
Research ideas for educational technology using NLP. I have:
- 3 months timeline
- No funding
- Undergraduate level expertise
- Access to Google Colab
```

## 📈 Usage Tips

1. **Be Specific** - More details = better recommendations
2. **Use Default Preset** - Good balance of quality/cost
3. **Iterate** - Provide feedback to refine results
4. **Edit Profile** - Customize `config/user_profile.yaml`
5. **Monitor Costs** - Check breakdown after each iteration
6. **Download Reports** - Save markdown files for reference

## 🔑 Environment Variables

```bash
# .env file
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get your key: https://openrouter.ai/keys

## 📞 Support

- **Documentation**: See files above
- **Issues**: Check troubleshooting section
- **OpenRouter**: https://openrouter.ai/docs

---

**Ready? Run:** `streamlit run app.py` 🚀
