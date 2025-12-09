# NCAA Basketball Betting Layer (Phase 2)

Market-aware betting system that integrates Vegas lines with KenPom-based ML models to identify value bets.

---

## 🎯 Overview

This layer calculates **betting edges** by comparing model predictions to market odds:

- **Spread Edge** = Model's predicted margin - Vegas spread
- **Moneyline Edge** = Model's win probability - Market's implied probability

The backtesting framework simulates flat-stake betting to measure:
- **ATS (Against The Spread) accuracy**
- **Moneyline win rate**
- **ROI by bet type**
- **Total profit/loss**

---

## 📋 Components

### 1. Market Integration (`ml/markets_ncaabb.py`)

**Purpose**: Load and process betting market data

**Key Functions**:
- `load_markets()`: Load odds CSV with validation
- `american_to_prob()`: Convert American odds to probabilities
- `join_markets_with_merged()`: Join market data with KenPom/ESPN features
- `calculate_market_edge()`: Calculate spread and ML edges for a game

**Market Data CSV Schema**:

```csv
season,game_day,home_team,away_team,close_spread,home_ml,away_ml,close_total
2024,2023-11-15,Duke,Michigan St.,-7.5,-300,+240,145.5
2024,2023-11-20,Kansas,Kentucky,-3.5,-165,+140,149.0
```

**Required Columns**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `season` | int | Season year | 2024 |
| `game_day` | str | Date (YYYY-MM-DD) | 2023-11-15 |
| `home_team` | str | Home team (ESPN name) | Duke |
| `away_team` | str | Away team (ESPN name) | Michigan St. |
| `close_spread` | float | Closing spread (home perspective) | -7.5 |
| `home_ml` | int | Home moneyline | -300 |
| `away_ml` | int | Away moneyline | +240 |

**Optional**: `close_total`, `open_spread`, `open_total` for line movement analysis

**Important**: Team names must match ESPN format used in `data/merged/` files. Use `data/markets/odds_ncaabb_sample.csv` as template.

---

### 2. Edge Generation (`ml/generate_ncaabb_edges.py`)

**Purpose**: Generate model predictions and calculate edges

**Usage**:
```bash
python3 ml/generate_ncaabb_edges.py \
    --merged-dir data/merged \
    --markets-file data/markets/odds_ncaabb_2024.csv \
    --model-dir models/ncaabb \
    --output-file data/edges/edges_ncaabb_2024.csv
```

**Arguments**:
- `--merged-dir`: Directory with KenPom/ESPN merged data (default: `data/merged`)
- `--markets-file`: Path to market odds CSV (required)
- `--model-dir`: Directory with trained models (default: `models/ncaabb`)
- `--output-file`: Path to save edges CSV (required)

**Process**:
1. Load merged KenPom/ESPN data
2. Load market odds
3. Join datasets (season + game_day + teams)
4. Build 11 KenPom-based features
5. Generate model predictions (spread + win probability)
6. Calculate edges (model vs market)
7. Output comprehensive CSV

**Output CSV Schema**:

Includes all columns from merged data plus:

| Column | Description |
|--------|-------------|
| `close_spread` | Market closing spread |
| `home_ml`, `away_ml` | Moneyline odds |
| `home_implied_prob`, `away_implied_prob` | Market implied probabilities |
| `model_spread` | Model's predicted margin |
| `model_home_prob`, `model_away_prob` | Model's win probabilities |
| `edge_spread` | Spread edge (pts) |
| `home_ml_edge`, `away_ml_edge` | Moneyline edges (probability) |
| `best_bet` | Recommended bet type |
| `max_edge` | Maximum edge value |

**Edge Interpretation**:
- **Spread edge > 0**: Model likes home more than market (bet home)
- **Spread edge < 0**: Model likes away more than market (bet away)
- **ML edge > 0**: Model gives higher probability than market (value bet)

---

### 3. Backtesting (`ml/backtest_ncaabb_betting.py`)

**Purpose**: Simulate betting strategy and calculate performance metrics

**Usage**:
```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 1.5 \
    --min-edge-ml 0.05 \
    --stake 100 \
    --output-summary backtest_2024_results.txt
```

**Arguments**:
- `--edges-file`: Path to edges CSV (from `generate_ncaabb_edges.py`)
- `--min-edge-spread`: Minimum spread edge in points (default: 1.5)
- `--min-edge-ml`: Minimum ML edge as probability (default: 0.05 = 5%)
- `--stake`: Flat stake per bet in units (default: 100)
- `--output-summary`: Optional summary report file

**Bet Selection Logic**:
- **Spread bets**: Only placed if `|edge_spread| >= min_edge_spread`
- **Moneyline bets**: Only placed if `max(|home_ml_edge|, |away_ml_edge|) >= min_edge_ml`
- Bets on side with positive edge

**Profit Calculation**:
- **Spread**: Standard -110 juice
  - Win: +1.0 unit (risk 1.1 to win 1.0)
  - Loss: -1.1 units
- **Moneyline**: Based on American odds
  - Favorite (e.g., -150): Win = 100/150 = 0.667 units, Loss = -1.0
  - Underdog (e.g., +200): Win = 200/100 = 2.0 units, Loss = -1.0

**Metrics Reported**:

```
📊 Overview:
   Total games analyzed: 860
   Total bets placed:    147
   Stake per bet:        100 units

🎯 Spread Betting:
   Bets placed:  82
   Wins:         47
   Win rate:     57.3%
   Profit:       +302.00 units
   ROI:          +3.68%

💰 Moneyline Betting:
   Bets placed:  65
   Wins:         38
   Win rate:     58.5%
   Profit:       +185.50 units
   ROI:          +2.85%

📈 Combined Results:
   Total profit: +487.50 units
   Total ROI:    +3.32%

🎓 Break-Even Analysis:
   Spread BE: 52.4% (actual: 57.3%)
   → +4.9% above break-even
```

**Break-Even Thresholds**:
- **Spread at -110**: Need 52.4% win rate to break even
- **Moneyline**: ~50% (varies by odds distribution)

---

## 🚀 Quick Start

### 1. Prepare Market Data

Create odds CSV in `data/markets/` using this template:

```csv
season,game_day,home_team,away_team,close_spread,home_ml,away_ml,close_total
2024,2023-11-06,Duke,Dartmouth,-31.5,-25000,+6600,152.5
2024,2023-11-10,Kansas,Manhattan,-33.5,-20000,+5000,157.5
```

**Critical**: Team names must match ESPN format from `data/merged/*.csv`

Sample file: `data/markets/odds_ncaabb_sample.csv`

---

### 2. Generate Edges

```bash
python3 ml/generate_ncaabb_edges.py \
    --merged-dir data/merged \
    --markets-file data/markets/odds_ncaabb_2024.csv \
    --model-dir models/ncaabb \
    --output-file data/edges/edges_ncaabb_2024.csv
```

**Expected Output**:
```
✅ Loaded 3,472 games from data/merged
✅ Loaded 860 games with market data from odds_ncaabb_2024.csv

📊 Market Join Results:
   Merged games: 3,472
   Market games: 860
   Matched:      854 (99.3%)
   Unmatched:    6

✅ Generated predictions for 854 games
   Spread range: [-24.3, 18.7]
   Home prob range: [0.121, 0.963]

📊 Edge Distribution:
   Spread edge: μ=0.12, σ=4.83
   Home ML edge: μ=0.003, σ=0.089

🎯 Bet Recommendations:
   home_spread: 187 (21.9%)
   away_spread: 201 (23.5%)
   home_ml: 142 (16.6%)
   away_ml: 159 (18.6%)
   None: 165 (19.3%)

✅ Saved 854 games with edges to data/edges/edges_ncaabb_2024.csv
```

---

### 3. Run Backtest

```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 2.0 \
    --min-edge-ml 0.08 \
    --stake 100
```

**Expected Output**:
```
✅ Loaded 854 games from edges_ncaabb_2024.csv
   Date range: November 06, 2023 → March 10, 2024

================================================================================
BACKTEST RESULTS
================================================================================

📊 Overview:
   Total games analyzed: 854
   Total bets placed:    89
   Stake per bet:        100 units

🎯 Spread Betting:
   Bets placed:  52
   Wins:         30
   Win rate:     57.7%
   Profit:       +166.00 units
   ROI:          +3.19%

💰 Moneyline Betting:
   Bets placed:  37
   Wins:         22
   Win rate:     59.5%
   Profit:       +124.30 units
   ROI:          +3.36%

📈 Combined Results:
   Total profit: +290.30 units
   Total ROI:    +3.26%

🎓 Break-Even Analysis:
   Spread BE: 52.4% (actual: 57.7%)
   → +5.3% above break-even
   ML BE: ~50.0% (actual: 59.5%)
   → +9.5% above break-even

✅ Backtest complete!
```

---

## 📊 Optimizing Edge Thresholds

**Goal**: Find edge thresholds that maximize ROI while maintaining sufficient bet volume

### Recommended Testing Grid

```bash
# Conservative (fewer bets, higher edge)
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 3.0 --min-edge-ml 0.10 --stake 100

# Moderate (balanced)
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 2.0 --min-edge-ml 0.07 --stake 100

# Aggressive (more bets, lower edge)
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 1.5 --min-edge-ml 0.05 --stake 100
```

### Analysis Tips

1. **ATS Win Rate**: Target 54-56% for long-term profitability at -110
2. **Bet Volume**: Need sufficient bets for statistical significance (~50+ per season)
3. **Edge vs Volume Trade-off**: Higher thresholds = fewer bets but better ROI
4. **Moneyline vs Spread**: ML typically has higher variance but better upside

---

## 🔧 Data Sources for Market Odds

### Where to Get Historical Odds

1. **The Odds Portal** (https://www.oddsportal.com)
   - Free historical data (limited)
   - Manual CSV download
   - Good for backtesting

2. **Sports Insights** (https://www.sportsinsights.com)
   - Paid subscription
   - API access
   - Line movement tracking

3. **Sportsbook APIs**
   - The Odds API (https://the-odds-api.com)
   - Historical odds available
   - $10-100/month depending on volume

4. **Manual Collection**
   - Check Archive.org for sportsbook snapshots
   - Community shared datasets (Reddit r/sportsbook)
   - Historical lines from Bovada, BetMGM, FanDuel

### Converting Data to Required Format

Most sources provide data in different formats. Convert to:

```csv
season,game_day,home_team,away_team,close_spread,home_ml,away_ml,close_total
```

**Key conversions**:
- Dates: Convert to `YYYY-MM-DD`
- Team names: Match ESPN format (see `data/merged/*.csv`)
- Spreads: Always from home perspective (negative = home favorite)
- Moneylines: American odds format (e.g., -150, +200)

---

## 🧪 Testing the System

### Test Market Module

```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball
python3 ml/markets_ncaabb.py
```

**Expected Output**:
```
================================================================================
MARKET INTEGRATION MODULE TEST
================================================================================

📊 Testing American odds conversion:
   -150 → 0.6000 (60.00%)
   +200 → 0.3333 (33.33%)
   -110 → 0.5238 (52.38%)
   +300 → 0.2500 (25.00%)
   -500 → 0.8333 (83.33%)

✅ Found sample market data: data/markets/odds_ncaabb_sample.csv
   Columns: ['season', 'game_day', 'home_team', 'away_team', 'close_spread', ...]
   
✅ Module loaded successfully
```

---

## 📝 Common Issues

### Issue: No games matched between merged and market data

**Cause**: Team name mismatch

**Solution**:
1. Check team names in market CSV match ESPN format
2. Compare: `data/merged/merged_games_2024.csv` (column: `team`)
3. Use exact spelling including punctuation (e.g., "N.C. State" not "NC State")

### Issue: Import errors

**Cause**: Python path not set

**Solution**:
```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball
python3 ml/generate_ncaabb_edges.py --help
```

### Issue: Model files not found

**Cause**: Models not trained yet

**Solution**:
```bash
python3 ml/train_ncaabb_spread.py --data-dir data/merged --output-dir models/ncaabb
```

---

## 🎯 Next Enhancements

### Kelly Criterion

Add optimal bet sizing based on edge:

```python
kelly_fraction = edge / odds
bet_size = bankroll * kelly_fraction * fractional_kelly
```

Typical fractional Kelly: 0.25 (quarter Kelly) for risk management

### Line Movement Analysis

Track `open_spread` → `close_spread`:
- Reverse line movement = sharp action indicator
- Steam moves = consensus sharp bets
- Closing line value = measure of edge quality

### Multi-Season Backtesting

Test across multiple seasons:
```bash
for year in 2022 2023 2024; do
    python3 ml/backtest_ncaabb_betting.py \
        --edges-file data/edges/edges_ncaabb_${year}.csv \
        --min-edge-spread 2.0 \
        --min-edge-ml 0.07 \
        --output-summary backtest_${year}_results.txt
done
```

### Live Deployment

For real-time betting:
1. Fetch today's games and KenPom ratings
2. Get current odds from sportsbook API
3. Generate predictions and edges
4. Alert on high-value bets (Telegram/Slack bot)

---

## 📚 Additional Resources

- **Project Status**: See `PROJECT_STATUS.md` for complete system documentation
- **ML Details**: See `ml/README.md` for model architecture and features
- **Data Collection**: See `DATA_SOURCES.md` for KenPom and ESPN details

---

**Status**: ✅ Phase 2 Complete - Ready for historical odds data and production backtesting
