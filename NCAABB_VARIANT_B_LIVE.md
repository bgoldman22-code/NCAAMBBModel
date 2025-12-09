# NCAA Basketball Variant B - Live Picks System

**Status**: ✅ Production Ready  
**Model**: Variant B (Market + In-Season Rolling Stats)  
**Performance**: +25.3% ROI (0.8111 AUC, 78.6% accuracy, 72.6% win rate)  
**Audit Status**: PASS - All 5/5 robustness tests passed

---

## Quick Start

Generate picks for today:

```bash
python3 scripts/ncaabb/generate_variant_b_picks.py \
    --date 2024-03-15 \
    --min-edge 0.15 \
    --kelly-fraction 0.25 \
    --bankroll 10000 \
    --output data/ncaabb/picks/variant_b_picks_2024-03-15.csv
```

---

## Daily Workflow

### 1. Generate Picks (Morning)

```bash
# Use today's date
TODAY=$(date +%Y-%m-%d)

python3 scripts/ncaabb/generate_variant_b_picks.py \
    --date $TODAY \
    --min-edge 0.15 \
    --kelly-fraction 0.25 \
    --bankroll 10000 \
    --output data/ncaabb/picks/variant_b_picks_$TODAY.csv
```

### 2. Review Picks

Check the CSV output:
```bash
cat data/ncaabb/picks/variant_b_picks_$TODAY.csv
```

Or the JSON:
```bash
cat data/ncaabb/picks/variant_b_picks_$TODAY.json | jq .
```

### 3. Place Bets

- Review the `edge` and `bet_size_dollars` columns
- Bet sizes are calculated using 25% Kelly Criterion (capped at 10% of bankroll)
- Only bet games with edge ≥ 0.15 (configurable via `--min-edge`)

---

## CLI Arguments

| Argument | Description | Default | Safe Range |
|----------|-------------|---------|------------|
| `--date` | Target date (YYYY-MM-DD) | **Required** | Any valid date |
| `--min-edge` | Minimum edge threshold | 0.15 | 0.10 - 0.20 |
| `--kelly-fraction` | Fraction of full Kelly | 0.25 | 0.15 - 0.50 |
| `--bankroll` | Total bankroll ($) | 10000 | > 0 |
| `--output` | Output CSV path | **Required** | Any valid path |

---

## Safe Defaults

**Recommended configuration for daily operation:**

```bash
--min-edge 0.15        # Conservative edge threshold
--kelly-fraction 0.25  # 25% Kelly (fractional for safety)
--bankroll 10000       # Adjust to your actual bankroll
```

**Aggressive configuration (not recommended):**
```bash
--min-edge 0.10        # Lower threshold = more bets
--kelly-fraction 0.50  # 50% Kelly = higher variance
```

**Ultra-conservative (for testing):**
```bash
--min-edge 0.20        # Very high threshold
--kelly-fraction 0.15  # ~1.5% bankroll per bet
```

---

## Output Format

### CSV Columns

| Column | Description |
|--------|-------------|
| `date` | Game date |
| `home_team` | Home team name |
| `away_team` | Away team name |
| `side` | Recommended bet side (`home` or `away`) |
| `market` | Market type (`home_ml` or `away_ml`) |
| `odds` | American odds (e.g., -110, +150) |
| `model_prob` | Model's win probability (0-1) |
| `implied_prob` | Market's implied probability (0-1) |
| `edge` | Model edge (model_prob - implied_prob) |
| `kelly_full` | Full Kelly stake (as fraction) |
| `kelly_applied` | Applied Kelly (fractional + capped) |
| `bet_size_dollars` | Recommended bet size ($) |

### JSON Structure

```json
{
  "date": "2024-03-15",
  "model": "Variant B",
  "min_edge": 0.15,
  "kelly_fraction": 0.25,
  "bankroll": 10000,
  "num_picks": 8,
  "total_bet_size": 6536,
  "avg_edge": 0.218,
  "max_edge": 0.301,
  "picks": [ ... ]
}
```

---

## Logging

Every run is logged to `data/ncaabb/logs/variant_b_runs.csv`:

```csv
run_timestamp,date,min_edge,kelly_fraction,bankroll,num_games,num_bets,avg_edge,max_edge,total_stake
2024-03-15T09:30:00,2024-03-15,0.15,0.25,10000,14,8,0.218,0.301,6536
```

---

## Safety Rails

### Built-in Protections

1. **Kelly Cap**: Applied stakes are capped at 10% of bankroll (even if full Kelly suggests more)
2. **Edge Validation**: Only bets with edge ≥ `--min-edge` are included
3. **Input Validation**: 
   - `min_edge` must be 0-0.5
   - `kelly_fraction` must be 0-1
   - `bankroll` must be > 0
4. **Zero Bets Handling**: Script exits gracefully if no qualifying bets found

### Manual Checks

Before placing bets:
- ✅ Verify edge is reasonable (< 0.40)
- ✅ Verify bet size is < 10% of bankroll
- ✅ Verify total stake is < 50% of bankroll
- ✅ Check that you have current odds (script uses pre-collected data)

---

## Model Specifications

### Variant B Feature Set (43 Features)

**Market Features (11)**:
- Home/Away moneyline odds
- Implied probabilities
- Vig (overround)
- Spread features

**In-Season Rolling Stats (32)**:
- Offensive Rating (ORtg)
- Defensive Rating (DRtg)
- Pace
- Margin of Victory (MoV)
- Win Percentage (WinPct)

Each stat computed over L3, L5, L10 game windows (both teams = 2 × 5 stats × 3 windows = 30 features)

Plus:
- GP_home, GP_away (games played)

### Model Training

- **Training data**: 2023-24 season through Feb 1, 2024
- **Test data**: Feb 2 - April 9, 2024
- **Algorithm**: Logistic Regression (balanced classes, L2 penalty)
- **Features**: Standardized (mean=0, std=1)

### Performance Metrics

| Metric | Value |
|--------|-------|
| Test AUC | 0.8111 |
| Test Accuracy | 78.64% |
| Test ROI | +25.3% |
| Win Rate | 72.6% |
| Bets per Season | ~1,150 |
| Avg Edge | 0.194 |

---

## Robustness Audit Summary

**Status**: ✅ PASS (5/5 tests)

1. **Rolling Window Leakage**: ✅ Manually verified 6 games, no leakage
2. **Label Shuffle Test**: ✅ ROI collapsed to -1.2% (near zero)
3. **Edge Shuffle Test**: ✅ ROI collapsed to -2.7% (near zero)
4. **Time Stability Test**: ✅ Late-season ROI +27.9% (BETTER than original)
5. **Baseline Comparison**: ✅ Variant B 4.4x more profitable than KenPom

See [VARIANT_B_ROBUSTNESS_REPORT.md](VARIANT_B_ROBUSTNESS_REPORT.md) for full audit details.

---

## Known Limitations

### Current Implementation

1. **Odds Source**: 
   - **Historical mode**: Uses pre-collected odds from `data/walkforward_results_with_scores.csv`
   - **Live mode** ✅: Integrated with The Odds API via `data-collection/live_odds_client.py`
   - Primary book: FanDuel (configurable via `ODDS_PRIMARY_BOOK` env var)
   
2. **In-Season Stats**: Computed from historical game results in `data/merged/game_results_with_inseason_stats.csv`
   - Rolling L3/L5/L10 windows computed up to yesterday
   - Graceful handling of teams with partial history

3. **Model Serialization**: Currently loads from training script output
   - Production artifacts in `models/variant_b_production/`

### Live Odds Setup

**Required Environment Variables**:
```bash
export ODDS_API_KEY='your_key_here'          # Get from https://the-odds-api.com/
export ODDS_API_BASE_URL='https://api.the-odds-api.com/v4'  # Optional, default shown
export ODDS_PRIMARY_BOOK='fanduel'           # Optional, default: fanduel
```

**Test the integration**:
```bash
python3 scripts/ncaabb/test_live_odds_client.py
```

**Supported books**: fanduel, draftkings, betmgm, caesars, pointsbet

### Deployment Status

- [x] ✅ Integrate live odds API (The Odds API)
- [x] ✅ Add HTTP endpoint for web integration
- [x] ✅ Automate daily stats updates (via live mode)
- [ ] 🔄 Set up daily cron job (GitHub Actions ready)
- [ ] 🔄 Serialize model to .pkl (uses on-demand training)
- [ ] Add Slack/email notifications

---

## Troubleshooting

### No picks generated

```
⚠️  No bets found above 0.15 edge threshold
```

**Solution**: Try lowering `--min-edge` or wait for better opportunities

### Missing in-season stats

```
In-season stats coverage: 0.0%
```

**Solution**: Ensure `data/merged/game_results_with_inseason_stats.csv` exists
```bash
python3 ml/features_inseason_stats.py
```

### No games found

```
📅 Loading games for 2024-12-10...
   Found 0 games on 2024-12-10
```

**Solution**: 
- Check that date is during the season (Nov - April)
- Verify `data/walkforward_results_with_scores.csv` contains games for that date
- Script will use demo data if no games found

---

## Production Checklist

Before going live:

- [x] Model trained and validated
- [x] Robustness audit complete (5/5 tests passed)
- [x] CLI script tested
- [x] Kelly criterion implemented
- [x] Safety rails in place
- [x] Logging enabled
- [ ] Live odds API integrated
- [ ] Daily automation configured
- [ ] Monitoring dashboard set up
- [ ] Bankroll management system ready

---

## Support

- **Audit Report**: [VARIANT_B_ROBUSTNESS_REPORT.md](VARIANT_B_ROBUSTNESS_REPORT.md)
- **Model Module**: [ml/ncaabb_variant_b_model.py](ml/ncaabb_variant_b_model.py)
- **Training Script**: [scripts/ncaabb/train_variant_b.py](scripts/ncaabb/train_variant_b.py)
- **Picks Generator**: [scripts/ncaabb/generate_variant_b_picks.py](scripts/ncaabb/generate_variant_b_picks.py)

---

**Last Updated**: 2024-12-10  
**Model Version**: Variant B v1 (Phase 3)  
**Audit Date**: 2024-12-10
