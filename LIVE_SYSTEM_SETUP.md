# Variant B Live System - Complete Setup Guide

## Overview

This guide covers the complete setup and operation of the Variant B live betting system, now fully integrated with live odds APIs.

---

## Prerequisites

1. **The Odds API Account**
   - Sign up at https://the-odds-api.com/
   - Free tier: 500 requests/month
   - Recommended tier: $40/month (1,000 requests)
   - Get your API key from the dashboard

2. **Python Environment**
   ```bash
   pip install pandas numpy scikit-learn lightgbm requests pytz
   ```

3. **GitHub Account** (for automation)
   - Repository with Actions enabled
   - Ability to set secrets

---

## Quick Start (Local)

### 1. Set Environment Variables

```bash
# Required for live mode
export ODDS_API_KEY='your_api_key_here'

# Optional (with defaults)
export ODDS_PRIMARY_BOOK='fanduel'  # or draftkings, betmgm, etc.
export VARIANT_B_MIN_EDGE='0.15'
export VARIANT_B_KELLY_FRACTION='0.25'
export VARIANT_B_BANKROLL='10000'
```

### 2. Test Live Odds Integration

```bash
cd /path/to/NEWMODEL/ncaa-basketball

# Smoke test - verifies API key and connection
python3 scripts/ncaabb/test_live_odds_client.py

# Test with specific date
python3 scripts/ncaabb/test_live_odds_client.py --date 2024-03-15

# Expected output:
# ✅ Fetched N games for 2024-03-15
# ✅ All required columns present
# ✅ No nulls in critical columns
# Sample of first 10 games...
```

### 3. Generate Live Picks

```bash
# For today
TODAY=$(date +%Y-%m-%d)

python3 scripts/ncaabb/generate_variant_b_picks.py \
    --date $TODAY \
    --mode live \
    --min-edge 0.15 \
    --kelly-fraction 0.25 \
    --bankroll 10000 \
    --output data/ncaabb/picks/variant_b_picks_$TODAY.csv

# Expected output:
# Mode: live
# 📡 Fetching NCAA basketball odds from The Odds API...
# ✅ Fetched N games for YYYY-MM-DD
# 📋 PICKS SUMMARY: X bets, $Y total stake
```

### 4. Monitor System Health

```bash
# Show last 5 runs
python3 scripts/ncaabb/inspect_recent_runs.py

# Health check with all-time stats
python3 scripts/ncaabb/inspect_recent_runs.py --check-health --summary

# Show last 10 runs
python3 scripts/ncaabb/inspect_recent_runs.py --last 10
```

---

## GitHub Actions Automation

### Setup Steps

1. **Add Secrets to GitHub**
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add: `ODDS_API_KEY` with your API key

2. **Configure Variables (Optional)**
   - In same section, go to "Variables" tab
   - Add custom config (or use defaults):
     - `VARIANT_B_MIN_EDGE` = 0.15
     - `VARIANT_B_KELLY_FRACTION` = 0.25
     - `VARIANT_B_BANKROLL` = 10000
     - `VARIANT_B_MODE` = live

3. **Enable Workflow**
   - File location: `.github/workflows/ncaabb_variant_b_daily.yml`
   - Go to: Repository → Actions tab
   - Find "NCAA Basketball Variant B - Daily Picks"
   - Enable if needed

4. **Test Workflow**
   - Click "Run workflow" dropdown
   - Select branch (usually `main`)
   - Click "Run workflow"
   - Monitor progress in Actions tab

### Workflow Schedule

**Default**: Runs at **3:00 PM UTC** daily (10:00 AM ET / 11:00 AM ET depending on DST)

**To change**:
- Edit `.github/workflows/ncaabb_variant_b_daily.yml`
- Modify the cron expression under `schedule:`
- Format: `'minute hour * * *'` (UTC time)
- Examples:
  - `'0 14 * * *'` = 2:00 PM UTC (9:00 AM ET)
  - `'0 16 * * *'` = 4:00 PM UTC (11:00 AM ET)
  - `'30 15 * * *'` = 3:30 PM UTC (10:30 AM ET)

### Workflow Outputs

**Artifacts** (downloadable from Actions page):
- `variant-b-picks-{run_number}` - CSV + JSON picks files
- `variant-b-logs-{run_number}` - Run logs

**Optional**: Workflow can auto-commit picks back to repository
- Enabled in workflow file (see `Commit picks` step)
- Commits to `data/ncaabb/picks/` and `data/ncaabb/logs/`

---

## Netlify Function Deployment

### Setup Steps

1. **Deploy to Netlify**
   - Connect your GitHub repository to Netlify
   - Build settings:
     - Base directory: (leave empty)
     - Build command: (not needed for functions)
     - Publish directory: (not needed for functions)
     - Functions directory: `netlify/functions`

2. **Add Environment Variable**
   - Netlify dashboard → Site settings → Environment variables
   - Add `ODDS_API_KEY` with your API key
   - Click "Save"

3. **Deploy**
   - Push changes to connected branch
   - Netlify auto-deploys
   - Function available at: `https://your-site.netlify.app/.netlify/functions/ncaabb-variant-b-picks`

### API Usage

**Endpoint**: `GET /.netlify/functions/ncaabb-variant-b-picks`

**Query Parameters** (all optional):
- `date` - Target date (YYYY-MM-DD, default: today)
- `minEdge` - Minimum edge (default: 0.15)
- `kellyFraction` - Kelly fraction (default: 0.25)
- `bankroll` - Bankroll in dollars (default: 10000)
- `mode` - Data mode: 'live' or 'historical' (default: live)

**Example Requests**:
```bash
# Today's picks with defaults
curl "https://your-site.netlify.app/.netlify/functions/ncaabb-variant-b-picks"

# Specific date
curl "https://your-site.netlify.app/.netlify/functions/ncaabb-variant-b-picks?date=2024-03-15"

# Custom config
curl "https://your-site.netlify.app/.netlify/functions/ncaabb-variant-b-picks?minEdge=0.20&kellyFraction=0.15&bankroll=5000"

# Use historical mode
curl "https://your-site.netlify.app/.netlify/functions/ncaabb-variant-b-picks?date=2024-03-15&mode=historical"
```

**Response Format**:
```json
{
  "date": "2024-03-15",
  "mode": "live",
  "model": "Variant B",
  "min_edge": 0.15,
  "kelly_fraction": 0.25,
  "bankroll": 10000,
  "num_picks": 8,
  "total_bet_size": 6536,
  "avg_edge": 0.218,
  "max_edge": 0.301,
  "picks": [
    {
      "home_team": "Quinnipiac",
      "away_team": "Saint Peter's",
      "book_name": "FanDuel",
      "side": "away",
      "odds": 110,
      "home_ml": -130,
      "away_ml": 110,
      "edge": 0.301,
      "model_prob": 0.565,
      "implied_prob": 0.476,
      "kelly_full": 0.274,
      "kelly_applied": 0.068,
      "bet_size_dollars": 685,
      "units": 6.85
    }
  ],
  "warnings": null
}
```

**Error Responses**:
- `400` - Invalid parameters
- `404` - No games found for date
- `503` - Live mode unavailable (API key not configured)
- `500` - Internal server error

---

## Monitoring & Health Checks

### Run History

All runs are logged to `data/ncaabb/logs/variant_b_runs.csv`:

```csv
run_timestamp,date,mode,min_edge,kelly_fraction,bankroll,num_games,num_bets,avg_edge,max_edge,total_stake,status,error_message
2025-12-08T14:35:55,2024-03-15,historical,0.15,0.25,10000,14,8,0.218,0.301,6536,success,
```

### Health Check Command

```bash
python3 scripts/ncaabb/inspect_recent_runs.py --check-health
```

**Checks performed**:
1. ✅ Last run date (flags if > 3 days ago)
2. ✅ Recent failures (last 7 runs)
3. ✅ Zero-bet days (last 14 runs)
4. ✅ Edge drift (compares to expected ~0.19)
5. ✅ Mode consistency (warns if mostly historical)

**Exit codes**:
- `0` - All checks passed
- `1` - Issues found (see output)

### Alerting (Manual)

Set up a cron job or CI workflow to run health checks:

```bash
# Example: Daily health check at 9 PM
0 21 * * * cd /path/to/ncaa-basketball && python3 scripts/ncaabb/inspect_recent_runs.py --check-health || echo "Health check failed!" | mail -s "Variant B Alert" you@example.com
```

---

## Operational Workflows

### Daily Morning Routine

1. **Check latest run** (if using automation):
   ```bash
   python3 scripts/ncaabb/inspect_recent_runs.py --last 1
   ```

2. **Review today's picks**:
   ```bash
   TODAY=$(date +%Y-%m-%d)
   cat data/ncaabb/picks/variant_b_picks_$TODAY.csv
   ```

3. **Verify picks** (optional):
   - Check that edges are reasonable (< 0.40)
   - Verify odds match current market
   - Confirm bet sizes are within limits

4. **Place bets**:
   - Use the CSV as your bet sheet
   - Place bets according to `bet_size_dollars` column
   - Track results for validation

### Weekly Health Check

```bash
python3 scripts/ncaabb/inspect_recent_runs.py --check-health --summary
```

Review:
- Bet volume (should average ~10/day during peak season)
- Average edge (should be ~0.19, acceptable range 0.15-0.25)
- Success rate of runs
- Any warning flags

### Monthly Revalidation

1. **Check API quota**:
   - Log into https://the-odds-api.com/account
   - Verify remaining requests
   - Upgrade plan if needed

2. **Review model performance**:
   - Track actual W-L record vs predictions
   - Compare to expected 72.6% win rate
   - If significantly worse, investigate:
     - Market conditions changed?
     - Data quality issues?
     - Model drift?

3. **Update dependencies** (if needed):
   ```bash
   pip install --upgrade pandas numpy scikit-learn lightgbm requests
   ```

---

## Troubleshooting

### Issue: "ODDS_API_KEY not set"

**Solution**:
```bash
export ODDS_API_KEY='your_key_here'
```

For persistence, add to `.bashrc` or `.zshrc`:
```bash
echo 'export ODDS_API_KEY="your_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "No games found"

**Possible causes**:
1. **Out of season** - NCAA basketball runs Nov-April
2. **No games today** - Check schedule
3. **Too early** - Odds may not be published yet (typically available ~24h before tip-off)
4. **API error** - Check API status at https://the-odds-api.com/

**Solution**:
- Test with a known date with games: `--date 2024-03-15`
- Check API quota/status
- Try fallback books: Script automatically tries fanduel → draftkings → betmgm

### Issue: "No bets above edge threshold"

**This is normal!** Not every day will have qualifying bets.

**Options**:
1. **Lower threshold**: `--min-edge 0.10` (more bets, lower quality)
2. **Wait**: Check again closer to game time (lines may move)
3. **Historical mode**: Verify system is working with `--mode historical`

### Issue: GitHub Actions failing

**Check**:
1. **Secrets configured**: Repository → Settings → Secrets → Actions
2. **Workflow enabled**: Actions tab → Enable workflow
3. **API key valid**: Test locally with same key
4. **Logs**: Actions tab → Click failed run → View logs

### Issue: Netlify function returning 503

**Check**:
1. **Environment variable**: Site settings → Environment variables → ODDS_API_KEY
2. **Redeploy**: Trigger a new deploy after adding env var
3. **Test locally**: Run function locally with same API key

---

## Best Practices

### API Quota Management

- **Free tier**: 500 requests/month = ~16/day
- **One request per pick generation** (fetches all games at once)
- **Recommendation**: Paid tier ($40/month) for daily automation

### Edge Threshold Selection

| Threshold | Bets/Day | Win Rate | Use Case |
|-----------|----------|----------|----------|
| 0.10 | ~20 | 70% | Maximum volume |
| 0.15 | ~10 | 73% | **Recommended** |
| 0.20 | ~5 | 75% | Conservative |

### Kelly Fraction Guidelines

| Fraction | Risk | Typical Bet | Use Case |
|----------|------|-------------|----------|
| 0.15 | Very Low | 1.5% | Ultra-conservative |
| 0.25 | Low | 2.5% | **Recommended** |
| 0.50 | Medium | 5% | Aggressive |
| 1.00 | High | 10%+ | Not recommended |

### Bankroll Management

- **Never bet more than 10% on a single game** (enforced by cap)
- **Keep total daily stake < 50% of bankroll** (check before placing bets)
- **Track results separately** (use the JSON files for record-keeping)
- **Adjust bankroll monthly** (increase if profitable, never chase losses)

---

## FAQ

**Q: How often are odds updated?**  
A: The Odds API updates every 1-2 minutes. Our system fetches once per generation.

**Q: Which sportsbook should I use?**  
A: The system defaults to FanDuel. Actual odds may vary by book - always verify before betting.

**Q: Can I use multiple API keys?**  
A: Yes, rotate keys in environment variable. But one key is usually sufficient.

**Q: What if a game is postponed?**  
A: Check logs - postponed games won't have odds and will be skipped.

**Q: How do I track results?**  
A: Save picks JSON files daily. Build a simple tracker that compares predictions to actual outcomes.

**Q: Is this profitable in practice?**  
A: Backtest shows +25.3% ROI. Live performance may vary due to:
- Market efficiency (books may adjust to your bets)
- Execution (slippage, limit issues)
- Overhead (fees, taxes)

**Q: Can I use this for other sports?**  
A: The system is NCAA basketball specific. For NBA, see the `nba/` folder (separate system).

---

## Support & Documentation

**Full Documentation**:
- `NCAABB_VARIANT_B_LIVE.md` - Complete usage guide
- `PRODUCTION_READY.md` - Production deployment summary
- `QUICK_START.md` - Daily operations cheat sheet
- `VARIANT_B_ROBUSTNESS_REPORT.md` - Model audit (5/5 tests passed)
- `DEPLOYMENT_SUMMARY.md` - System architecture

**Source Code**:
- `ml/ncaabb_variant_b_model.py` - Model logic
- `data-collection/live_odds_client.py` - API integration
- `scripts/ncaabb/generate_variant_b_picks.py` - Picks generator
- `scripts/ncaabb/run_daily_variant_b_live.py` - Daily automation
- `scripts/ncaabb/inspect_recent_runs.py` - Health monitoring

**Workflow Files**:
- `.github/workflows/ncaabb_variant_b_daily.yml` - GitHub Actions
- `netlify/functions/ncaabb-variant-b-picks.py` - HTTP endpoint

---

**Last Updated**: 2024-12-08  
**Model Version**: Variant B v1  
**System Status**: ✅ Production Ready with Live Odds
