# GitHub Actions Setup Guide

This repository includes automated workflows for daily picks generation and model monitoring.

## 🚀 Workflows

### 1. Daily Picks Generation
**File**: `.github/workflows/daily-picks-generation.yml`  
**Schedule**: Runs at 9 AM ET (2 PM UTC) every day  
**Purpose**: Automatically generates picks for today's NCAA basketball games

**What it does**:
- Fetches live odds from The Odds API
- Runs Variant B model predictions
- Applies odds-aware filtering
- Commits picks to repository
- Creates artifacts for download

### 2. Model Testing
**File**: `.github/workflows/model-testing.yml`  
**Trigger**: On push to main or pull requests  
**Purpose**: Validates model integrity and runs unit tests

### 3. Weekly Model Check
**File**: `.github/workflows/weekly-model-check.yml`  
**Schedule**: Every Sunday at 2 AM ET  
**Purpose**: Monitors model performance and data freshness

---

## ⚙️ Setup Required

### 1. Add GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions**

Add the following secret:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `ODDS_API_KEY` | Your API key | Get from [The Odds API](https://the-odds-api.com/) |

### 2. Enable GitHub Actions

1. Go to **Settings → Actions → General**
2. Under "Workflow permissions", select:
   - ✅ **Read and write permissions**
3. Check: ✅ **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### 3. Test Manual Run

1. Go to **Actions** tab in your repository
2. Select "Daily NCAA Basketball Picks Generation"
3. Click **Run workflow** → **Run workflow**
4. Monitor the run to ensure it completes successfully

---

## 📊 Viewing Results

### In GitHub Actions UI
- Go to **Actions** tab
- Click on a workflow run
- View the **Summary** for picks preview
- Download artifacts for full CSV/JSON files

### In Repository
After successful run, picks are committed to:
```
data/ncaabb/picks/variant_b_picks_odds_aware_YYYY-MM-DD.csv
data/ncaabb/picks/variant_b_picks_odds_aware_YYYY-MM-DD.json
```

### Artifacts (90-day retention)
Each run uploads artifacts containing:
- CSV picks file
- JSON picks file
- Available for 90 days after run

---

## 🔧 Configuration

You can modify these environment variables in the workflow files:

| Variable | Default | Description |
|----------|---------|-------------|
| `VARIANT_B_MIN_EDGE` | 0.10 | Minimum edge threshold (10%) |
| `VARIANT_B_KELLY_FRACTION` | 0.25 | Kelly criterion fraction (25%) |
| `VARIANT_B_BANKROLL` | 10000 | Bankroll in dollars |

---

## 📅 Schedule Customization

To change when picks are generated, edit the cron expression in `.github/workflows/daily-picks-generation.yml`:

```yaml
schedule:
  - cron: '0 14 * * *'  # 9 AM ET (14:00 UTC)
```

**Common schedules**:
- `0 13 * * *` - 8 AM ET (1 PM UTC)
- `0 14 * * *` - 9 AM ET (2 PM UTC) - **Current**
- `0 15 * * *` - 10 AM ET (3 PM UTC)

**Cron format**: `minute hour day month weekday`

---

## 🚨 Monitoring

### Email Notifications
GitHub automatically sends email notifications on workflow failures. Configure in:
**Settings → Notifications → Actions**

### Workflow Status Badge
Add to your README.md:
```markdown
![Daily Picks](https://github.com/bgoldman22-code/NCAAMBBModel/actions/workflows/daily-picks-generation.yml/badge.svg)
```

---

## 🔐 Security Notes

1. **Never commit API keys** - Always use GitHub Secrets
2. **API quota monitoring** - The Odds API has usage limits (500 requests/month free tier)
3. **Rate limiting** - Workflow automatically handles rate limits
4. **Private repository** - Consider making repo private if using paid API keys

---

## 🐛 Troubleshooting

### "No changes to commit"
- Normal if no games scheduled for that day
- Check the workflow summary for "No Games Today" message

### "API quota exceeded"
- Check your API usage at [The Odds API Dashboard](https://the-odds-api.com/account)
- Consider upgrading plan during busy season
- Workflow will fail gracefully without breaking

### "Model file not found"
- Ensure model files are committed to repository
- Run `scripts/ncaabb/freeze_variant_b_model.py` to regenerate
- Check `models/variant_b_production/` directory exists

### "Permission denied"
- Verify "Read and write permissions" enabled in Settings → Actions
- Check branch protection rules don't block Actions commits

---

## 💡 Advanced: Netlify Integration

If you want to deploy a frontend dashboard:

1. **Create `netlify.toml`**:
```toml
[build]
  command = "echo 'No build needed'"
  publish = "data/ncaabb/picks"

[[redirects]]
  from = "/api/picks/latest"
  to = "/variant_b_picks_odds_aware_:date.json"
  status = 200
```

2. **Connect Netlify to GitHub**:
   - Go to [Netlify](https://app.netlify.com/)
   - New site from Git
   - Select this repository
   - Auto-deploys on push

3. **Access picks via URL**:
   - `https://your-site.netlify.app/variant_b_picks_odds_aware_2025-12-09.csv`

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [The Odds API Documentation](https://the-odds-api.com/liveapi/guides/v4/)
- [Cron Expression Generator](https://crontab.guru/)

---

## ✅ Quick Start Checklist

- [ ] Add `ODDS_API_KEY` secret to repository
- [ ] Enable read/write permissions for Actions
- [ ] Test manual workflow run
- [ ] Verify first automated run
- [ ] Check picks committed to repository
- [ ] Download artifacts to verify format
- [ ] Monitor API quota usage
- [ ] (Optional) Set up email notifications
- [ ] (Optional) Add status badge to README

---

**Last Updated**: December 9, 2025  
**Status**: ✅ Ready for production use
