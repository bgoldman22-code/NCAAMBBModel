# Historical Odds Collection Guide

This guide explains how to collect historical NCAA basketball odds from The Odds API and integrate them with your betting system.

---

## 🔑 API Key Setup

**Your API Key**: `c5d3fe15e6c5be83b2acd8695cff012b`

**Important**: 
- ✅ Use locally via environment variable
- ✅ Use Netlify environment variable in production
- ❌ Never commit API key to git

### Set Environment Variable (Local)

**macOS/Linux**:
```bash
export ODDS_API_KEY="c5d3fe15e6c5be83b2acd8695cff012b"
```

**Add to ~/.zshrc for persistence**:
```bash
echo 'export ODDS_API_KEY="c5d3fe15e6c5be83b2acd8695cff012b"' >> ~/.zshrc
source ~/.zshrc
```

**Verify**:
```bash
echo $ODDS_API_KEY
```

---

## 📊 The Odds API Details

### Sport Key
- **NCAA Men's Basketball**: `basketball_ncaab`

### Available Markets
- `h2h` - Moneyline (head-to-head)
- `spreads` - Point spreads
- `totals` - Over/under totals

### Historical Data Access
- **Endpoint**: `/v4/historical/sports/{sport}/odds`
- **Cost**: 10 quota per request per region per market
- **Format**: JSON with snapshot metadata (timestamp, previous, next)

### Rate Limits
- **Free Tier**: 500 requests/month
- **Paid Plans**: $25/month (5,000 requests), $99/month (25,000 requests)

**Monitor usage**: https://the-odds-api.com/account/

---

## 🚀 Quick Start

### 1. Collect Full Season (Recommended)

Use the helper script for automatic date range selection:

```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball

# Make script executable
chmod +x data-collection/collect_odds_season.sh

# Collect 2024 season (Nov 2023 - Apr 2024)
./data-collection/collect_odds_season.sh 2024
```

**Available Seasons**:
- `2022` → Nov 2021 - Apr 2022
- `2023` → Nov 2022 - Apr 2023
- `2024` → Nov 2023 - Apr 2024
- `2025` → Nov 2024 - Apr 2025 (current season)

---

### 2. Collect Custom Date Range

For more control, use the Python script directly:

```bash
python3 data-collection/collect_odds_historical.py \
    --start-date 2023-11-01 \
    --end-date 2024-03-31 \
    --season 2024 \
    --output-file data/markets/odds_ncaabb_2024.csv \
    --delay 1.5
```

**Parameters**:
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--season`: Season year (e.g., 2024 for 2023-24 season)
- `--output-file`: CSV output path
- `--delay`: Seconds between API calls (default: 1.0, recommend 1.5 for safety)

---

## 📋 What Happens During Collection

### Process Flow

1. **Generate timestamps**: Creates daily snapshots (12:00 UTC) for date range
2. **Fetch odds**: Queries historical API for each timestamp
3. **Parse games**: Extracts home/away teams, spreads, moneylines
4. **Deduplicate**: Removes duplicate games across snapshots
5. **Format CSV**: Converts to required schema
6. **Save locally**: Writes to `data/markets/odds_ncaabb_YEAR.csv`

### Expected Output

```
================================================================================
COLLECTING HISTORICAL NCAA BASKETBALL ODDS
================================================================================
Date range: 2023-11-01 → 2024-03-31
Season: 2024
Output: data/markets/odds_ncaabb_2024.csv
================================================================================

📅 Generated 152 timestamps to query

[1/152] Fetching odds for 2023-11-01T12:00:00Z...
   API quota used: 10, remaining: 490
   Found 84 games (total unique: 84)

[2/152] Fetching odds for 2023-11-02T12:00:00Z...
   API quota used: 20, remaining: 480
   Found 67 games (total unique: 142)

...

✅ Collected 1,247 unique games
💾 Saved to data/markets/odds_ncaabb_2024.csv

📊 Summary:
   Total games: 1,247
   Date range: 2023-11-01 → 2024-03-31
   Games with spreads: 1,247 (100.0%)
   Games with moneylines: 1,247 (100.0%)

📋 Sample games:
season  game_day    home_team        away_team         close_spread  home_ml  away_ml  close_total
2024    2023-11-06  Duke             Dartmouth         -31.5         -25000   6600     152.5
2024    2023-11-06  Kansas           NC Central        -36.5         -50000   10000    159.0
...
```

---

## 💰 API Quota Management

### Understanding Costs

**Per Request**:
- 1 timestamp × 1 region (`us`) × 2 markets (`h2h`, `spreads`) = **10 quota**

**Full Season** (152 days):
- 152 requests × 10 quota = **1,520 total quota**

**Free Tier**:
- 500 requests/month = Can collect ~50 days per month
- Strategy: Split seasons across multiple months OR upgrade to paid plan

### Optimization Strategies

1. **Reduce frequency**: Query every 2-3 days instead of daily
   ```bash
   # Modify script to use 48-hour intervals
   python3 data-collection/collect_odds_historical.py \
       --start-date 2023-11-01 \
       --end-date 2024-03-31 \
       --season 2024 \
       --output-file data/markets/odds_ncaabb_2024.csv \
       --delay 1.5
   # Then manually edit script to change interval_hours=48
   ```

2. **Target key dates**: Only collect during tournament season (March Madness)
   ```bash
   # Conference tournaments + March Madness
   python3 data-collection/collect_odds_historical.py \
       --start-date 2024-03-01 \
       --end-date 2024-04-09 \
       --season 2024 \
       --output-file data/markets/odds_ncaabb_2024_tournament.csv
   ```

3. **Upgrade plan**: $25/month = 5,000 requests (enough for 500 days of data)

---

## 🔧 Team Name Matching

### Potential Issue

The Odds API may use different team names than ESPN/merged data.

**Example mismatches**:
- Odds API: "Saint Mary's (CA)"
- ESPN: "Saint Mary's"

### Solution

After collection, check team name alignment:

```bash
# View unique team names from odds
python3 -c "
import pandas as pd
df = pd.read_csv('data/markets/odds_ncaabb_2024.csv')
teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
for team in sorted(teams):
    print(team)
"

# Compare to ESPN names
head -20 data/merged/merged_games_2024.csv | cut -d',' -f1
```

If mismatches exist, create a mapping function in `ml/markets_ncaabb.py`:

```python
ODDS_API_TO_ESPN = {
    "Saint Mary's (CA)": "Saint Mary's",
    "UConn": "Connecticut",
    # Add more mappings as needed
}

def normalize_odds_team_name(name: str) -> str:
    return ODDS_API_TO_ESPN.get(name, name)
```

---

## 📊 Next Steps After Collection

### 1. Verify Data Quality

```bash
# Check for missing values
python3 -c "
import pandas as pd
df = pd.read_csv('data/markets/odds_ncaabb_2024.csv')
print(f'Total games: {len(df)}')
print(f'Missing spreads: {df["close_spread"].isna().sum()}')
print(f'Missing home_ml: {df["home_ml"].isna().sum()}')
print(f'Missing away_ml: {df["away_ml"].isna().sum()}')
"
```

---

### 2. Generate Edges

```bash
python3 ml/generate_ncaabb_edges.py \
    --merged-dir data/merged \
    --markets-file data/markets/odds_ncaabb_2024.csv \
    --model-dir models/ncaabb \
    --output-file data/edges/edges_ncaabb_2024.csv
```

**Expected match rate**: 80-95% (some games in merged data may not have odds)

---

### 3. Run Backtest

```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 2.0 \
    --min-edge-ml 0.07 \
    --stake 100
```

---

## 🚨 Troubleshooting

### Error: "Invalid API key"

**Solution**: Verify API key is set correctly
```bash
echo $ODDS_API_KEY
# Should output: c5d3fe15e6c5be83b2acd8695cff012b
```

---

### Error: "Rate limit exceeded"

**Solution**: 
1. Check usage at https://the-odds-api.com/account/
2. Increase `--delay` parameter
3. Wait until next month (free tier resets)
4. Upgrade to paid plan

---

### Warning: "No games collected"

**Possible causes**:
1. **Wrong sport key**: NCAA is `basketball_ncaab` (not `basketball_nba`)
2. **No games on that date**: Try a date during season (Nov-Apr)
3. **API outage**: Check https://the-odds-api.com/

---

### Low match rate with merged data

**Solution**: Compare team names and create mapping
```bash
# Show unmatched teams
python3 ml/generate_ncaabb_edges.py \
    --markets-file data/markets/odds_ncaabb_2024.csv \
    --output-file data/edges/edges_ncaabb_2024.csv
# Check unmatched games in output
```

---

## 📚 Additional Resources

- **The Odds API Docs**: https://the-odds-api.com/liveapi/guides/v4/
- **Historical Odds Guide**: https://the-odds-api.com/historical-odds-data
- **API Dashboard**: https://the-odds-api.com/account/
- **Sport Keys**: https://the-odds-api.com/sports-odds-data/sports-apis.html

---

## 🎯 Recommended Workflow

### For backtesting (one-time setup):

```bash
# 1. Set API key
export ODDS_API_KEY="c5d3fe15e6c5be83b2acd8695cff012b"

# 2. Collect full 2024 season
./data-collection/collect_odds_season.sh 2024

# 3. Generate edges
python3 ml/generate_ncaabb_edges.py \
    --markets-file data/markets/odds_ncaabb_2024.csv \
    --output-file data/edges/edges_ncaabb_2024.csv

# 4. Run backtest
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 2.0 \
    --min-edge-ml 0.07 \
    --stake 100

# 5. Analyze results and iterate
```

### For live betting (daily updates):

```bash
# Fetch today's odds
python3 data-collection/collect_odds_historical.py \
    --start-date $(date +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d) \
    --season 2025 \
    --output-file data/markets/odds_today.csv

# Generate edges for today
python3 ml/generate_ncaabb_edges.py \
    --markets-file data/markets/odds_today.csv \
    --output-file data/edges/edges_today.csv

# Review high-value bets
python3 -c "
import pandas as pd
df = pd.read_csv('data/edges/edges_today.csv')
high_edge = df[(df['edge_spread'].abs() > 3) | (df['home_ml_edge'].abs() > 0.1)]
print(high_edge[['team', 'opponent', 'edge_spread', 'home_ml_edge', 'best_bet']])
"
```

---

**Status**: Ready to collect historical odds! Start with 2024 season for backtesting.
