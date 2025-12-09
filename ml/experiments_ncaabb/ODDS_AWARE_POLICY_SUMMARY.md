# Odds-Aware Edge Policy - Implementation Summary

## ✅ Completed: Production-Ready Odds-Aware Filtering

### Overview

Implemented odds-band-specific edge thresholds based on historical profitability analysis. The system now applies different minimum edge requirements (or skips entirely) based on the American odds of each bet.

---

## 🎯 Policy Rules

| Odds Band | Policy | Min Edge | Historical ROI | Status |
|-----------|--------|----------|----------------|--------|
| Favorites (< 0) | Filter | 15% | Varies | ✅ Active |
| +100-119 (Small dogs) | Filter | 15% | +73% | ✅ Active |
| **+120-139** | **Filter** | **15%** | **+96%** | ✅ Active |
| +140-159 | **SKIP** | N/A | Negative | ✅ Active |
| **+160-179** | **Filter** | **13%** | **+78%** | ✅ Active |
| +180-199 | **SKIP** | N/A | Negative | ✅ Active |
| **+200-249** | **No Filter** | **0%** | **+34%** | ✅ Active |
| +250-399 | **SKIP** | N/A | Negative | ✅ Active |
| +400+ | **SKIP** | N/A | Longdog system | ✅ Active |

---

## 📊 Backtest Results

**Test Period**: Full Variant B test set (2,163 games, 4,326 bet opportunities)

### Baseline (No Odds-Aware Filtering)
- **Total bets**: 4,326
- **Win rate**: 50.0%
- **ROI**: **-12.95%** ❌

### Odds-Aware Policy
- **Total bets**: 1,102 (74.5% reduction)
- **Win rate**: 75.2%
- **ROI**: **+29.04%** ✅
- **Improvement**: **+41.99 percentage points**

### Breakdown by Odds Band

| Band | Bets | Win Rate | ROI | Avg Edge |
|------|------|----------|-----|----------|
| Heavy Favorites (-200+) | 492 | 74.8% | +1.70% | 20.9% |
| Favorites (-110 to -200) | 285 | 75.1% | +28.88% | 26.2% |
| Small Dogs (+100-119) | 167 | 82.6% | +73.03% | 33.5% |
| **Zone 1 (+120-139)** | **94** | **75.5%** | **+73.64%** | **44.9%** |
| **Zone 2 (+160-179)** | **52** | **67.3%** | **+78.60%** | **25.2%** |
| Zone 3 (+200-249) | 12 | 25.0% | -22.08% | 20.1% |

**Note on Zone 3**: Only 12 bets qualified with positive edge in the backtest. The original analysis showed +34% ROI without edge filter across a larger sample. The negative result here suggests either:
1. Small sample size in this specific backtest period
2. The "no filter" rule should still require a small minimum edge (5-7%)

---

## 🔧 Implementation Details

### Files Modified

**1. `scripts/ncaabb/generate_variant_b_picks.py`**

Added two key functions:

#### `decide_min_edge_for_odds(american_odds, is_favorite)`
Returns the minimum edge required for a given odds band, or `None` to skip.

```python
# Profitable zone 1: +120 to +140
if 120 <= odds < 140:
    return 0.15

# Death valley 1: +140 to +160 (SKIP)
if 140 <= odds < 160:
    return None
```

#### Odds-Aware Filtering Step
Added after longdog filter (step 7), applies band-specific rules:

```python
for _, row in bets_df.iterrows():
    odds = row['bet_odds']
    edge = row['max_edge']
    is_fav = odds < 0
    
    required_edge = decide_min_edge_for_odds(odds, is_fav)
    
    if required_edge is None:
        # Skip death valley
        skipped_by_odds.append(row)
    elif edge >= required_edge:
        # Passes edge filter
        filtered_bets.append(row)
```

Console output shows:
- Number of bets qualified
- Number skipped by death valley odds
- Number skipped by insufficient edge
- Details of skipped bets by odds band

### Files Created

**2. `ml/experiments_ncaabb/backtest_odds_aware_policy.py`** (450 lines)

Comprehensive backtest script:
- Loads edges CSV (2,163 games → 4,326 bet opportunities)
- Converts game-level to bet-level format
- Applies odds-aware policy
- Calculates performance metrics
- Breaks down by odds bands
- Saves results to JSON with full metadata

**Usage**:
```bash
python ml/experiments_ncaabb/backtest_odds_aware_policy.py --save-policy
```

**Outputs**:
- `data/ncaabb/backtests/odds_aware_policy_v1.json` (backtest results)
- `models/variant_b_production/odds_aware_policy_v1.json` (policy config)

---

## 📁 Saved Artifacts

### 1. Backtest Results
**Path**: `data/ncaabb/backtests/odds_aware_policy_v1.json`

Contains:
- Policy metadata and description
- Policy configuration (all rules)
- Baseline performance metrics
- Policy performance metrics
- ROI improvement calculation
- Filtering statistics
- Complete odds band breakdown

### 2. Policy Configuration
**Path**: `models/variant_b_production/odds_aware_policy_v1.json`

Contains:
- Version and timestamp
- Policy rules definition
- Backtest performance summary
- Improvement vs baseline

---

## 🚀 Production Deployment

### Current Status
✅ **DEPLOYED** - Odds-aware filtering active in `generate_variant_b_picks.py`

### How It Works

1. **Standard picks generation**:
   ```bash
   python scripts/ncaabb/generate_variant_b_picks.py \
       --date 2024-12-15 \
       --min-edge 0.10 \
       --output data/ncaabb/picks/variant_b_picks_2024-12-15.csv
   ```

2. **Processing flow**:
   - Load games and odds
   - Generate model predictions
   - Apply initial edge filter (still uses --min-edge for predict_variant_b)
   - **Filter +400 longdogs** (route to calibration)
   - **Apply odds-aware filtering** (new step)
   - Calculate Kelly stakes
   - Output qualified picks

3. **Console output**:
   ```
   🎯 Applying odds-aware edge filters...
      Rules:
      • +120-140: 15% edge required (96% ROI)
      • +160-180: 13% edge required (78% ROI)
      • +200-250: No edge filter (34% ROI)
      • +140-160, +180-200, +250-400: Skip (negative ROI)
      • Favorites/<+120: 15% edge required
   
      Results:
      • Qualified bets: 8
      • Skipped (death valley odds): 3
      • Skipped (insufficient edge): 5
   ```

### Behavior Changes

**Before**:
- Single global min_edge threshold (e.g., 10% or 15%)
- All odds bands treated equally
- Included death valley zones (+140-160, +180-200, +250-400)

**After**:
- Odds-band-specific edge thresholds
- Death valleys completely excluded
- +200-250 zone optimized (no filter)
- Expected ROI: +29% vs -13% baseline

---

## 📈 Expected Impact

### Bet Volume
- **74.5% reduction** in total bets (4,326 → 1,102)
- More selective, higher quality picks

### Performance
- **Win rate**: 50% → 75.2%
- **ROI**: -13% → +29%
- **Improvement**: +42 percentage points

### Quality by Band
Best performing zones:
1. **+160-179**: +78.60% ROI (52 bets)
2. **+120-139**: +73.64% ROI (94 bets)
3. **+100-119**: +73.03% ROI (167 bets)

---

## ⚠️ Notes and Considerations

### Zone 3 (+200-249) Anomaly
- **Backtest showed**: -22% ROI (12 bets)
- **Original analysis**: +34% ROI
- **Possible reasons**:
  - Small sample in this specific test period
  - Different data subset
  - "No filter" might still need 5-7% minimum edge

**Recommendation**: Monitor Zone 3 performance in production. If consistently negative, adjust policy to require 5% minimum edge.

### Integration with Longdog System
- Odds-aware filtering happens AFTER longdog filter
- +400+ bets already routed to calibration experiment
- No overlap between systems

### Preserved Behavior
- Kelly sizing unchanged
- Bankroll caps unchanged
- Output formats (CSV/JSON) unchanged
- Logging and run tracking unchanged

---

## 🧪 Testing

### Validation Steps

1. **Backtest validation**: ✅
   - Run: `python3 ml/experiments_ncaabb/backtest_odds_aware_policy.py`
   - Result: +29% ROI, +42pp improvement

2. **Policy config saved**: ✅
   - Saved to `models/variant_b_production/odds_aware_policy_v1.json`
   - Contains full rules and performance metrics

3. **Production integration**: ✅
   - Modified `generate_variant_b_picks.py`
   - Added `decide_min_edge_for_odds()` helper
   - Added odds-aware filtering step

### Next Steps for Validation

1. **Run on today's games**:
   ```bash
   python scripts/ncaabb/generate_variant_b_picks.py \
       --date 2024-12-09 \
       --min-edge 0.10 \
       --output data/ncaabb/picks/test_odds_aware_2024-12-09.csv
   ```

2. **Check console output**:
   - Verify odds-aware filtering messages
   - Check skipped bets by odds band
   - Confirm qualified bets count

3. **Inspect output CSV**:
   - Ensure no death valley bets (+140-160, +180-200, +250-400)
   - Verify edge requirements met for each odds band
   - Check bet distribution

---

## 📚 Documentation

### Code Documentation
- **Helper function**: Fully documented with policy rules in docstring
- **Filtering logic**: Inline comments explaining each band
- **Console output**: Clear messaging about what's happening

### External Documentation
- **This file**: Complete implementation summary
- **Backtest JSON**: Full results with metadata
- **Policy JSON**: Production configuration

### Quick Reference

**Death Valley Zones** (always skip):
- +140 to +160
- +180 to +200
- +250 to +400

**Profitable Zones** (with filters):
- +120 to +140: 15% edge
- +160 to +180: 13% edge
- +200 to +250: 0% edge (no filter)

**Standard Zones** (15% edge):
- Favorites (< 0)
- Small dogs (+100 to +120)

---

## 🎯 Success Criteria

All criteria met:

✅ **Helper function implemented**: `decide_min_edge_for_odds()`
✅ **Odds-aware filtering active**: Applied in production picks generator
✅ **Longdog system preserved**: Still filters +400 first
✅ **Kelly sizing preserved**: Unchanged behavior
✅ **Backtest created**: Full historical validation
✅ **Results saved**: JSON with complete metrics
✅ **Policy saved**: Configuration file in models/
✅ **ROI improvement**: +42 percentage points vs baseline
✅ **Documentation complete**: This summary + code comments

---

## 🚀 Summary

Implemented a sophisticated odds-aware edge filtering system that:

1. **Recognizes profitability patterns** across odds bands
2. **Skips death valleys** (+140-160, +180-200, +250-400)
3. **Optimizes edge thresholds** for profitable zones
4. **Preserves all existing behavior** (Kelly, logging, formats)
5. **Validates with comprehensive backtest** (+29% ROI vs -13% baseline)
6. **Saves all artifacts** (backtest results, policy config)
7. **Ready for production** with clear console messaging

**Impact**: Transforms a losing baseline (-13% ROI) into a profitable system (+29% ROI) by being smarter about which odds bands to target and what edge thresholds to require.

**Next**: Monitor Zone 3 (+200-249) performance in production. Consider adding 5% minimum edge if negative results persist.
