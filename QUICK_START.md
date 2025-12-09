# NCAA Basketball Variant B - Daily Operations Cheat Sheet

## ✅ NEW: Live Mode Available!

The system now supports both **historical** (backtesting) and **live** (real-time odds) modes.

---

## Morning Routine (5 minutes)

### Option A: Live Mode (Production)

```bash
# 1. Set API key (first time only)
export ODDS_API_KEY='your_key_here'  # Get from https://the-odds-api.com/

# 2. Generate today's picks
TODAY=$(date +%Y-%m-%d)
python3 scripts/ncaabb/generate_variant_b_picks.py \
    --date $TODAY \
    --mode live \
    --min-edge 0.15 \
    --kelly-fraction 0.25 \
    --bankroll 10000 \
    --output data/ncaabb/picks/variant_b_picks_$TODAY.csv

# 3. View picks
cat data/ncaabb/picks/variant_b_picks_$TODAY.csv
```

### Option B: Historical Mode (Backtesting)

```bash
# Use pre-collected historical data
TODAY=$(date +%Y-%m-%d)
python3 scripts/ncaabb/generate_variant_b_picks.py \
    --date $TODAY \
    --mode historical \
    --min-edge 0.15 \
    --kelly-fraction 0.25 \
    --bankroll 10000 \
    --output data/ncaabb/picks/variant_b_picks_$TODAY.csv
```

### Automated (GitHub Actions)

If you've set up the workflow:
1. Picks auto-generate daily at 3:00 PM UTC (10 AM ET)
2. Download from: Repository → Actions → Latest run → Artifacts
3. Or check committed files in `data/ncaabb/picks/`

---

## Quick Reference

### CLI Arguments
| Flag | Default | Safe Range | Description |
|------|---------|------------|-------------|
| `--date` | **Required** | Any | Target date (YYYY-MM-DD) |
| `--min-edge` | 0.15 | 0.10-0.20 | Min edge threshold |
| `--kelly-fraction` | 0.25 | 0.15-0.50 | Fraction of Kelly |
| `--bankroll` | 10000 | > 0 | Total bankroll ($) |
| `--output` | **Required** | Any | Output file path |

### Conservative Config
```bash
--min-edge 0.20 --kelly-fraction 0.15  # Ultra safe
```

### Standard Config (Recommended)
```bash
--min-edge 0.15 --kelly-fraction 0.25  # Default
```

### Aggressive Config
```bash
--min-edge 0.10 --kelly-fraction 0.50  # High risk
```

---

## Output Files

### CSV (`data/ncaabb/picks/variant_b_picks_YYYY-MM-DD.csv`)
Human-readable table with columns:
- `home_team`, `away_team` - Teams
- `side` - Bet side (home/away)
- `odds` - American odds (-110, +150, etc.)
- `edge` - Model edge (0-1)
- `bet_size_dollars` - Recommended stake

### JSON (`data/ncaabb/picks/variant_b_picks_YYYY-MM-DD.json`)
Structured data with:
- `num_picks` - Total bets
- `total_bet_size` - Total stake
- `avg_edge`, `max_edge` - Edge stats
- `picks[]` - Array of bet objects

### Log (`data/ncaabb/logs/variant_b_runs.csv`)
Run history with timestamp, date, num_bets, avg_edge, total_stake

---

## HTTP API

### Endpoint
```
GET /.netlify/functions/ncaabb-variant-b-picks?date=YYYY-MM-DD
```

### Response (200 OK)
```json
{
  "date": "2024-03-15",
  "model": "Variant B",
  "num_picks": 8,
  "total_bet_size": 6536,
  "avg_edge": 0.218,
  "picks": [...]
}
```

### Response (404)
```json
{
  "error": "No picks found for 2024-03-15"
}
```

---

## Safety Checks Before Betting

✅ **Edge < 0.40** (unrealistic if higher)  
✅ **Bet size < 10% bankroll**  
✅ **Total stake < 50% bankroll**  
✅ **Cross-check odds with current market**  
✅ **Verify date is correct**

---

## Expected Stats (2024 Test Set)

- **ROI**: +25.3%
- **Win Rate**: 72.6%
- **Bets/Season**: ~1,150
- **Avg Bet**: ~$300 (on $10K bankroll)
- **Avg Edge**: 0.194

---

## Troubleshooting

### No picks generated
```
⚠️  No bets found above 0.15 edge threshold
```
**Fix**: Lower `--min-edge` or wait for better games

### Missing stats
```
In-season stats coverage: 0.0%
```
**Fix**: Run `python3 ml/features_inseason_stats.py`

### No games found
```
Found 0 games on 2024-12-10
```
**Fix**: Check date is during season (Nov-April)

---

## File Locations

| File | Purpose |
|------|---------|
| `scripts/ncaabb/generate_variant_b_picks.py` | Main generator |
| `ml/ncaabb_variant_b_model.py` | Model logic |
| `data/ncaabb/picks/*.csv` | Daily picks |
| `data/ncaabb/logs/variant_b_runs.csv` | Run history |
| `NCAABB_VARIANT_B_LIVE.md` | Full documentation |

---

## Model Specs

- **Algorithm**: Logistic Regression
- **Features**: 43 (market + in-season stats)
- **Windows**: L3, L5, L10 games
- **Training**: 2023-24 through Feb 1
- **Test**: Feb 2 - April 9, 2024
- **Audit**: ✅ 5/5 tests passed

---

## One-Liner

```bash
# Generate picks for today
TODAY=$(date +%Y-%m-%d) && python3 scripts/ncaabb/generate_variant_b_picks.py --date $TODAY --min-edge 0.15 --kelly-fraction 0.25 --bankroll 10000 --output data/ncaabb/picks/variant_b_picks_$TODAY.csv && cat data/ncaabb/picks/variant_b_picks_$TODAY.csv
```

---

**Status**: ✅ Production Ready  
**Last Updated**: 2024-12-10  
**Model Version**: Variant B v1
