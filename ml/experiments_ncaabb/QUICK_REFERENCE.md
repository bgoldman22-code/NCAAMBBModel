# Longdog Calibration - Quick Reference

## 🎯 What It Does

**Filters +400 underdogs from production picks** (they went 0-27 when model showed 10%+ edge)  
**Routes them to calibration experiment** to fix model overconfidence

---

## 📋 Quick Command Reference

### Generate Picks (Longdogs Auto-Filtered)
```bash
python scripts/ncaabb/generate_variant_b_picks.py \
    --date 2024-12-15 \
    --min-edge 0.10 \
    --output data/ncaabb/picks/variant_b_picks_2024-12-15.csv
```
**Result**: +400 bets excluded, logged to `data/ncaabb/experiments/variant_b_longdogs_raw.csv`

### Train Calibration (When 50+ Samples)
```bash
python ml/experiments_ncaabb/underdog_longdogs_calibration.py \
    --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \
    --output-dir models/variant_b_calibration \
    --save-model
```
**Output**: Platt + Isotonic models saved to `models/variant_b_calibration/`

### Check Calibration Info
```bash
python ml/experiments_ncaabb/longdogs_calibration_utils.py
```
**Shows**: Training data, test performance, ROI for both methods

### Test Filtering Logic
```bash
python ml/experiments_ncaabb/test_longdog_filtering.py
```
**Verifies**: +400 threshold, logging, edge cases (all tests pass ✅)

---

## 📂 Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `generate_variant_b_picks.py` | Modified picks generator (adds filter) | +81 |
| `underdog_longdogs_calibration.py` | Train Platt/Isotonic calibrators | 461 |
| `longdogs_calibration_utils.py` | Load/apply calibration | 251 |
| `variant_b_longdogs_raw.csv` | Experiment data sink | Runtime |
| `LONGDOG_CALIBRATION_SYSTEM.md` | Full documentation | 550 |

---

## 🔢 By The Numbers

| Metric | Before | After |
|--------|--------|-------|
| +400 bets with 10%+ edge | 0-27 (0%) | **0 bets placed** ✅ |
| +900 longshots | 2.15% win rate | **Filtered out** ✅ |
| Data lost | None | **None** (logged to experiment) ✅ |
| Calibration framework | ❌ | **✅ Ready** |

---

## 🎓 Calibration Methods

### Platt Scaling
- **Type**: Logistic regression (2 parameters)
- **Best for**: Limited data (30-50 samples), prefer interpretability
- **Speed**: Fast

### Isotonic Regression
- **Type**: Non-parametric monotonic mapping
- **Best for**: Sufficient data (100+ samples), prioritize performance
- **Speed**: Fast

**Recommendation**: Try both, use whichever has better test ROI

---

## 📊 Experiment Data Schema

```csv
date,home_team,away_team,bet_side,american_odds,implied_prob_market,model_prob,edge,outcome
2024-12-15,Villanova,Creighton,away,1160,0.0794,0.132,0.527,
```

**Fill `outcome` column post-game**: 1 = win, 0 = loss, None = pending

---

## 🚦 Status Indicators

### When Running Picks Generator

```
🔍 Filtering longshot underdogs (+400 or greater)...
   ⚠️  Excluded 3 longshot bets (≥+400 odds) from production picks
   Routing to calibration experiment: data/ncaabb/experiments/variant_b_longdogs_raw.csv
   Logged 3 longdogs to [path]
```
**Meaning**: Working as designed ✅

```
   ✓ No longshot underdogs found
```
**Meaning**: All picks < +400, normal production flow ✅

```
⚠️  No bets remaining after filtering longshots (all were ≥+400)
   Try lowering --min-edge or wait for better opportunities
```
**Meaning**: All qualifying bets were longshots, none go to production ✅

---

## 🔧 Python API Usage

### Load and Apply Calibration
```python
from ml.experiments_ncaabb.longdogs_calibration_utils import (
    load_longdogs_calibrator,
    apply_longdogs_calibration
)

# Load once (expensive)
calibrator = load_longdogs_calibrator('isotonic')

# Apply many times (fast)
p_calibrated = apply_longdogs_calibration(
    model_prob,
    'isotonic',
    calibrator=calibrator
)

# Recalculate edge
edge_calibrated = p_calibrated - implied_prob_market
```

---

## ⚠️ Common Issues

### "Not enough data to train calibration"
**Cause**: < 50 samples in experiment CSV  
**Fix**: Wait for more games, or widen odds range

### "Calibration models not found"
**Cause**: Haven't trained calibrators yet  
**Fix**: Run `underdog_longdogs_calibration.py --save-model`

### "No longdogs logged"
**Cause**: No +400 games today (normal)  
**Fix**: None needed, longshots are rare

---

## 🎯 Design Philosophy

1. **Be conservative**: 0-27 record = stop betting immediately
2. **Build dataset**: Route to experiment, don't discard
3. **Validate first**: Train calibrators, check test ROI before re-enabling
4. **Save everything**: All models saved with metadata (project convention)
5. **Make it automatic**: No manual intervention needed for filtering

---

## 📖 Further Reading

- **Full documentation**: `LONGDOG_CALIBRATION_SYSTEM.md` (550 lines)
- **Implementation summary**: `IMPLEMENTATION_COMPLETE.md`
- **Historical analysis**: `EDGE_PROFITABILITY_ANALYSIS.md`
- **Test suite**: `test_longdog_filtering.py`

---

## ✅ Checklist

- ✅ Production filter active (all +400 excluded)
- ✅ Experiment logger working (appends to CSV)
- ✅ Calibration training ready (Platt + Isotonic)
- ✅ Utilities available (load/apply calibration)
- ✅ Tests passing (all scenarios validated)
- ✅ Documentation complete (3 markdown files)

**Status**: 🚀 **PRODUCTION READY**

---

## 🎉 Bottom Line

**Problem**: Model went 0-27 on +400 underdogs when showing 10%+ edge  
**Solution**: Filter them out, route to calibration experiment  
**Result**: Immediate loss prevention + future improvement potential  

**Deploy now, calibrate later** ✅
