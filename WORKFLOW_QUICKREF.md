# NCAA Basketball Betting System - Quick Reference

## 📊 Complete Workflow: Data → Models → Betting

This guide shows the end-to-end workflow from data collection through backtesting.

---

## Phase 1: Data Collection & Modeling

### 1. Collect ESPN Game Schedules

```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball
python3 data-collection/collect_historical_games.py
```

**Output**: `data/schedules/schedules_YEAR.csv` (952+ games per season)

---

### 2. Collect KenPom Efficiency Metrics

```bash
python3 data-collection/collect_kenpom_api.py
```

**Output**: `data/kenpom/kenpom_ratings_YEAR.csv` (360+ teams per season)

**Note**: Requires KenPom API credentials in `data-collection/kenpom_config.py`

---

### 3. Merge ESPN + KenPom Data

```bash
python3 data-collection/merge_kenpom_schedules.py
```

**Output**: `data/merged/merged_games_YEAR.csv` (3,472 matched games)

**Features Added**:
- Opponent KenPom metrics
- Efficiency differentials
- Matchup advantages
- Tempo differentials
- Home court flags

---

### 4. Verify Data Quality

```bash
python3 data-collection/verify_kenpom_data.py
```

**Target**: 94%+ opponent match rate

---

### 5. Train ML Models

```bash
python3 ml/train_ncaabb_spread.py \
    --data-dir data/merged \
    --output-dir models/ncaabb
```

**Output**:
- `models/ncaabb/ncaabb_spread_model.pkl` (MAE: 9.57 pts)
- `models/ncaabb/ncaabb_moneyline_model.pkl` (Acc: 72.8%)
- `models/ncaabb/feature_columns.json`
- `models/ncaabb/metadata.json`

---

### 6. Evaluate Models

```bash
python3 ml/eval_ncaabb_spread.py \
    --model-dir models/ncaabb \
    --data-dir data/merged
```

**Reports**:
- Spread: MAE, RMSE, Correlation
- Moneyline: Accuracy, AUC, Brier Score
- Calibration curves by confidence bin

---

## Phase 2: Market Integration & Backtesting

### 7. Prepare Market Odds Data

**Manual Step**: Create CSV in `data/markets/odds_ncaabb_YEAR.csv`

**Required Schema**:
```csv
season,game_day,home_team,away_team,close_spread,home_ml,away_ml,close_total
2024,2023-11-06,Duke,Dartmouth,-31.5,-25000,+6600,152.5
2024,2023-11-10,Kansas,Manhattan,-33.5,-20000,+5000,157.5
```

**Important**:
- Team names must match ESPN format in `data/merged/*.csv`
- Dates in `YYYY-MM-DD` format
- Spreads from home perspective (negative = favorite)
- Moneylines in American odds format

**Template**: Use `data/markets/odds_ncaabb_sample.csv`

---

### 8. Generate Betting Edges

```bash
python3 ml/generate_ncaabb_edges.py \
    --merged-dir data/merged \
    --markets-file data/markets/odds_ncaabb_2024.csv \
    --model-dir models/ncaabb \
    --output-file data/edges/edges_ncaabb_2024.csv
```

**Output**: `data/edges/edges_ncaabb_2024.csv` with:
- All merged game data
- Market odds and implied probabilities
- Model predictions (spread + win prob)
- Edge calculations (model vs market)
- Bet recommendations

**Key Metrics**:
- `edge_spread`: Model spread - Vegas spread (in points)
- `home_ml_edge`: Model win prob - Implied prob
- `away_ml_edge`: Model loss prob - Implied prob
- `best_bet`: Recommended bet type

---

### 9. Backtest Betting Strategy

```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 2.0 \
    --min-edge-ml 0.07 \
    --stake 100 \
    --output-summary results_2024.txt
```

**Parameters**:
- `--min-edge-spread`: Points threshold (e.g., 2.0 = only bet if model differs by 2+ pts)
- `--min-edge-ml`: Probability threshold (e.g., 0.07 = 7% edge required)
- `--stake`: Flat bet size in units (default: 100)

**Output Metrics**:
- Spread: Win rate, bets placed, profit, ROI
- Moneyline: Win rate, bets placed, profit, ROI
- Combined: Total profit, total ROI
- Break-even analysis (52.4% needed for spread)

**Success Criteria**:
- Spread win rate: 54-56% (break-even is 52.4% at -110)
- Positive ROI over 100+ bets
- Higher confidence bets outperform lower confidence

---

## 🎯 Recommended Parameter Testing

### Conservative Strategy (High Edge, Low Volume)

```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 3.0 \
    --min-edge-ml 0.10 \
    --stake 100
```

**Expected**: Fewer bets (~30-50), higher win rate (~58-62%), ROI ~4-6%

---

### Moderate Strategy (Balanced)

```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 2.0 \
    --min-edge-ml 0.07 \
    --stake 100
```

**Expected**: Moderate bets (~80-120), good win rate (~55-58%), ROI ~3-4%

---

### Aggressive Strategy (Low Edge, High Volume)

```bash
python3 ml/backtest_ncaabb_betting.py \
    --edges-file data/edges/edges_ncaabb_2024.csv \
    --min-edge-spread 1.5 \
    --min-edge-ml 0.05 \
    --stake 100
```

**Expected**: Many bets (~150-200), lower win rate (~53-55%), ROI ~2-3%

---

## 🔄 Multi-Season Backtesting Loop

Test strategy consistency across multiple seasons:

```bash
#!/bin/bash
# Run backtest on all available seasons

for YEAR in 2022 2023 2024; do
    echo "===================="
    echo "Testing Season: $YEAR"
    echo "===================="
    
    # Generate edges
    python3 ml/generate_ncaabb_edges.py \
        --merged-dir data/merged \
        --markets-file data/markets/odds_ncaabb_${YEAR}.csv \
        --model-dir models/ncaabb \
        --output-file data/edges/edges_ncaabb_${YEAR}.csv
    
    # Run backtest
    python3 ml/backtest_ncaabb_betting.py \
        --edges-file data/edges/edges_ncaabb_${YEAR}.csv \
        --min-edge-spread 2.0 \
        --min-edge-ml 0.07 \
        --stake 100 \
        --output-summary results_${YEAR}.txt
    
    echo ""
done

# Aggregate results
echo "===================="
echo "Combined Results"
echo "===================="
cat results_*.txt
```

---

## 📈 Performance Benchmarks

### Spread Betting
- **Break-even**: 52.4% win rate at -110 odds
- **Target**: 54-56% win rate
- **Elite**: 57%+ win rate
- **Expected ROI**: 2-4% long-term

### Moneyline Betting
- **Break-even**: ~50% (depends on odds distribution)
- **Target**: 55-58% on filtered bets
- **Elite**: 60%+ on high-confidence bets
- **Expected ROI**: 3-6% long-term

### Profitability Formula

For spread betting at -110:
- Win rate needed: 52.38%
- Above 52.38%: Profitable
- Every 1% above = ~1.9% ROI improvement

**Example**: 55% win rate = ~5% ROI

---

## 🚨 Common Issues & Solutions

### Issue: "Models not found"
**Solution**: Run training first:
```bash
python3 ml/train_ncaabb_spread.py --data-dir data/merged --output-dir models/ncaabb
```

---

### Issue: "No games matched between merged and market data"
**Solution**: Check team name alignment:
```bash
# View team names in merged data
head -20 data/merged/merged_games_2024.csv | cut -d',' -f1

# Compare to market data team names
head -20 data/markets/odds_ncaabb_2024.csv | cut -d',' -f3,4
```

Team names must match exactly (including punctuation like "N.C. State")

---

### Issue: "Module import errors"
**Solution**: Run from project root:
```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball
python3 ml/script_name.py
```

---

### Issue: "KenPom API authentication failed"
**Solution**: Check credentials in `data-collection/kenpom_config.py`:
```python
KENPOM_EMAIL = "your_email@example.com"
KENPOM_API_KEY = "your_api_key_here"
```

Get API key: https://kenpom.com/api.php ($25/year)

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview |
| `PROJECT_STATUS.md` | Complete system documentation |
| `BETTING_LAYER_README.md` | Phase 2 market integration details |
| `DATA_SOURCES.md` | KenPom and ESPN data sources |
| `ml/README.md` | ML model architecture and features |
| `WORKFLOW_QUICKREF.md` | This file - quick reference guide |

---

## 🎯 Next Steps

1. **Obtain Historical Odds**:
   - Source: The Odds Portal, Sports Insights, or sportsbook APIs
   - Format: Convert to required CSV schema
   - Coverage: 2022-2024 seasons for backtesting

2. **Run Multi-Season Backtests**:
   - Test parameter combinations
   - Validate edge thresholds
   - Measure consistency across seasons

3. **Implement Kelly Criterion**:
   - Add optimal bet sizing
   - Compare Kelly vs flat staking
   - Use fractional Kelly (0.25) for risk management

4. **Deploy Live System**:
   - Fetch daily games and odds
   - Generate predictions
   - Alert on high-value bets
   - Track actual performance

---

**System Status**: ✅ Phases 1 & 2 Complete - Ready for production backtesting

**Model Performance**:
- Spread: MAE 9.57 pts, Correlation 0.67
- Moneyline: 72.8% accuracy, 82.6% on high-confidence

**Target**: 54-56% ATS accuracy for profitable betting at -110 odds
