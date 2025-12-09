# Longdog Calibration System - Visual Architecture

## System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                   DAILY PICKS GENERATION WORKFLOW                      │
└───────────────────────────────────────────────────────────────────────┘

                    generate_variant_b_picks.py
                              │
                    ┌─────────┴──────────┐
                    │  Load model        │
                    │  Fetch odds        │
                    │  Build features    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ predict_variant_b()│
                    │  - Calculate probs │
                    │  - Compute edges   │
                    │  - Return all bets │
                    └─────────┬──────────┘
                              │
                   ALL PREDICTIONS WITH ODDS
                              │
            ┌─────────────────┴─────────────────┐
            │      🔍 +400 ODDS FILTER          │
            │      (NEW - Task 1)               │
            └─────────┬───────────────┬─────────┘
                      │               │
              ┌───────▼─────┐   ┌────▼────────┐
              │ odds < 400  │   │ odds ≥ 400  │
              └───────┬─────┘   └────┬────────┘
                      │               │
            ┌─────────▼─────┐   ┌────▼─────────────────┐
            │ CORE PICKS    │   │ LONGDOGS EXCLUDED    │
            │               │   │                      │
            │ • Normal      │   │ • Log to experiment  │
            │   processing  │   │ • Don't bet on these │
            │ • Kelly stakes│   │ • Build dataset      │
            │ • Sort by edge│   │                      │
            └───────┬───────┘   └────┬─────────────────┘
                    │                │
        ┌───────────▼──────────┐     │
        │ OUTPUT FILES         │     │
        │ • variant_b_picks.csv│     │
        │ • variant_b_picks.json    │
        │ • Console summary    │     │
        └──────────────────────┘     │
                                     │
            ┌────────────────────────▼─────────────────────┐
            │    EXPERIMENT DATA ACCUMULATION              │
            │    (Task 2)                                  │
            │                                              │
            │  data/ncaabb/experiments/                    │
            │    variant_b_longdogs_raw.csv                │
            │                                              │
            │  Schema:                                     │
            │    date, teams, side, odds,                  │
            │    market_prob, model_prob, edge,            │
            │    outcome (None initially)                  │
            └────────────┬─────────────────────────────────┘
                         │
            ┌────────────▼──────────────┐
            │  FILL OUTCOMES POST-GAME  │
            │  (Manual or Automated)    │
            │                           │
            │  outcome: 1 = win         │
            │  outcome: 0 = loss        │
            └────────────┬──────────────┘
                         │
            ┌────────────▼──────────────────────────────┐
            │  CALIBRATION TRAINING                     │
            │  (Task 3)                                 │
            │                                           │
            │  underdog_longdogs_calibration.py         │
            │    --input variant_b_longdogs_raw.csv     │
            │    --save-model                           │
            └────────┬─────────────┬────────────────────┘
                     │             │
         ┌───────────▼──────┐   ┌─▼──────────────────┐
         │ PLATT SCALING    │   │ ISOTONIC REGRESSION│
         │                  │   │                    │
         │ • Logistic reg   │   │ • Non-parametric   │
         │ • 2 parameters   │   │ • Flexible         │
         │ • Interpretable  │   │ • Often better     │
         └───────────┬──────┘   └─┬──────────────────┘
                     │             │
                     └──────┬──────┘
                            │
            ┌───────────────▼────────────────────┐
            │  SAVED MODELS & METADATA           │
            │  (Task 3)                          │
            │                                    │
            │  models/variant_b_calibration/     │
            │    • platt_scaling.joblib          │
            │    • isotonic_regression.joblib    │
            │    • calibration_metadata.json     │
            └───────────────┬────────────────────┘
                            │
            ┌───────────────▼────────────────────┐
            │  CALIBRATION UTILITIES             │
            │  (Task 4)                          │
            │                                    │
            │  longdogs_calibration_utils.py     │
            │    • load_longdogs_calibrator()    │
            │    • apply_longdogs_calibration()  │
            │    • get_calibration_info()        │
            │    • compare_calibration_methods() │
            └────────────────────────────────────┘

```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Today's Games + Odds                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Feature Engineering  │
            │  • Team stats         │
            │  • Opponent defense   │
            │  • Market features    │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Model Prediction     │
            │  • Variant B GBM      │
            │  • Output: p_home,    │
            │    p_away             │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Edge Calculation     │
            │  edge = p_model -     │
            │         p_market      │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Edge Filter          │
            │  edge >= min_edge     │
            └───────────┬───────────┘
                        │
                ┌───────┴────────┐
                │                │
        ┌───────▼──────┐   ┌────▼────────┐
        │ odds < 400   │   │ odds ≥ 400  │
        │              │   │             │
        │ GO TO        │   │ GO TO       │
        │ PRODUCTION   │   │ EXPERIMENT  │
        └───────┬──────┘   └────┬────────┘
                │                │
                │                │
        ┌───────▼──────┐   ┌────▼─────────────────┐
        │              │   │                      │
        │  CSV/JSON    │   │  Experiment CSV      │
        │  Output      │   │  (with outcome=None) │
        │              │   │                      │
        └──────────────┘   └──────────────────────┘
                                    │
                            ┌───────▼────────┐
                            │ Post-game:     │
                            │ Fill outcomes  │
                            └───────┬────────┘
                                    │
                            ┌───────▼──────────┐
                            │ Train calibrators│
                            └───────┬──────────┘
                                    │
                            ┌───────▼──────────┐
                            │ Save models      │
                            └──────────────────┘
```

---

## Historical Context: Why We Need This

```
BEFORE CALIBRATION SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model sees +1160 Villanova:
  • Market:     7.9% win probability  (+1160 odds)
  • Model:     13.2% win probability
  • Edge:      53.3% (!!!)
  • Bet Size:  $XX
  • Result:    ❌ LOSS (historical: 0-2 on +1000 with 15%+ edge)

Model sees +450 UTSA:
  • Market:    18.2% win probability
  • Model:     24.5% win probability
  • Edge:      6.3%
  • Bet Size:  $XX
  • Result:    ❌ LOSS (historical: 0-27 on +400 with 10%+ edge)

Total +400 underdogs: 340 games
Wins: 19 (5.59%)
Expected: ~12% based on odds
ROI: Highly negative


AFTER CALIBRATION SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model sees +1160 Villanova:
  • Market:     7.9% win probability
  • Model:     13.2% win probability
  • Edge:      53.3%
  ⚠️  FILTERED: odds ≥ 400
  ✅ LOGGED to experiment (not bet on)
  📊 Data point for calibration training

Model sees +450 UTSA:
  • Market:    18.2% win probability
  • Model:     24.5% win probability
  • Edge:      6.3%
  ⚠️  FILTERED: odds ≥ 400
  ✅ LOGGED to experiment (not bet on)
  📊 Data point for calibration training

Production picks: Only < +400 odds
Experiment data: Growing dataset for calibration
Future: Train Platt/Isotonic, validate, possibly re-enable with calibrated probs
```

---

## Calibration Process (Future)

```
STEP 1: DATA ACCUMULATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Daily picks generation → +400 bets logged → Outcomes filled

Current: 0 samples
Target:  50+ samples (minimum for Platt)
         100+ samples (ideal for Isotonic)


STEP 2: TRAINING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$ python underdog_longdogs_calibration.py \
      --input variant_b_longdogs_raw.csv \
      --save-model

Input:  model_prob (uncalibrated)
Output: p_calibrated (fixed)

Platt:    p_cal = 1/(1 + exp(-(a*p_model + b)))
Isotonic: p_cal = IsotonicRegression(p_model)


STEP 3: EVALUATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Metrics:
  • AUC (discrimination ability)
  • Brier score (calibration + discrimination)
  • Log loss (probabilistic accuracy)
  • ROI (betting profitability)

Compare:
  • Uncalibrated baseline
  • Platt scaling
  • Isotonic regression

Choose best method for production


STEP 4: DEPLOYMENT (Optional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IF calibrated ROI > 0:
  1. Load calibrator in predict_variant_b()
  2. Apply to p_model for +400 bets
  3. Recalculate edge with p_calibrated
  4. Only bet if calibrated edge > threshold
  5. Monitor performance carefully

ELSE:
  Keep +400 bets excluded from production
  Continue accumulating data
  Retrain periodically
```

---

## File Dependency Graph

```
generate_variant_b_picks.py (MODIFIED)
    │
    ├─ Calls: predict_variant_b() from ncaabb_variant_b_model.py
    │
    ├─ Filters: odds >= 400
    │
    ├─ Calls: log_longdogs_to_experiment() (NEW)
    │   │
    │   └─ Writes to: data/ncaabb/experiments/variant_b_longdogs_raw.csv
    │
    └─ Outputs:
        ├─ data/ncaabb/picks/variant_b_picks_YYYY-MM-DD.csv (core picks only)
        └─ data/ncaabb/picks/variant_b_picks_YYYY-MM-DD.json


underdog_longdogs_calibration.py (NEW)
    │
    ├─ Reads: data/ncaabb/experiments/variant_b_longdogs_raw.csv
    │
    ├─ Trains: Platt scaling + Isotonic regression
    │
    └─ Writes:
        ├─ models/variant_b_calibration/platt_scaling.joblib
        ├─ models/variant_b_calibration/isotonic_regression.joblib
        └─ models/variant_b_calibration/calibration_metadata.json


longdogs_calibration_utils.py (NEW)
    │
    ├─ Loads: models/variant_b_calibration/*.joblib
    │
    └─ Provides:
        ├─ load_longdogs_calibrator()
        ├─ apply_longdogs_calibration()
        ├─ get_calibration_info()
        └─ compare_calibration_methods()


test_longdog_filtering.py (NEW)
    │
    └─ Tests: Filtering logic, edge cases, logging schema
```

---

## Testing Strategy

```
UNIT TESTS (test_longdog_filtering.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Test 1: Mixed odds (some < 400, some >= 400)
   Input:  5 predictions with odds [1160, 110, 240, 450, 750]
   Output: 2 core picks, 3 longdogs
   Verify: Correct split, no data loss

✅ Test 2: All longdogs (edge case)
   Input:  3 predictions, all odds >= 400
   Output: 0 core picks, 3 longdogs, empty CSV warning
   Verify: Handles empty output gracefully

✅ Test 3: No longdogs (normal case)
   Input:  3 predictions, all odds < 400
   Output: 3 core picks, 0 longdogs, normal flow
   Verify: No filtering needed


INTEGRATION TESTS (manual)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Run generate_variant_b_picks.py with real data
□ Verify longdogs excluded from production CSV
□ Verify longdogs logged to experiment CSV
□ Verify experiment CSV schema correct
□ Fill outcomes manually
□ Run underdog_longdogs_calibration.py
□ Verify models saved with metadata
□ Load models with longdogs_calibration_utils.py
□ Apply calibration to test probabilities
```

---

## Performance Monitoring

```
METRICS TO TRACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Production Picks (< +400):
  ✓ Win rate
  ✓ ROI
  ✓ Average edge
  ✓ Bet count per day

Filtered Longdogs (>= +400):
  ✓ Count per day (expect: 0-3)
  ✓ Average odds
  ✓ Model probability distribution
  ✓ Edge distribution

Experiment Data:
  ✓ Total samples accumulated
  ✓ Win rate when outcomes filled
  ✓ Sufficient for training? (50+ target)

Calibration Models (after training):
  ✓ Test ROI vs uncalibrated
  ✓ Calibration curves (reliability diagrams)
  ✓ Improvement over baseline
```

---

## Success Criteria

```
IMMEDIATE (Tasks 1-2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All +400 bets excluded from production
✅ Longdogs logged to experiment CSV
✅ No picks lost (all accounted for)
✅ Production picks contain only < +400 odds
✅ Test suite passes


MEDIUM-TERM (Tasks 3-4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Accumulate 50+ longdog samples with outcomes
□ Train calibration models successfully
□ Calibrated probabilities closer to true win rate
□ Test ROI better than uncalibrated baseline
□ Models saved with comprehensive metadata


LONG-TERM (Optional Re-enablement)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Calibrated longdogs show positive test ROI
□ Validate on additional out-of-sample data
□ Modify predict_variant_b() to use calibration
□ Monitor live performance carefully
□ Compare to "no longdogs" baseline
```

---

## 🎯 Key Insight

```
┌─────────────────────────────────────────────────────────────┐
│  "The model is not wrong about longshots being bad bets.   │
│   It's wrong about WHICH longshots are bad bets."          │
│                                                             │
│  When it sees 10%+ edge on +400: 0-27 record (0%)          │
│  The only wins: had NEGATIVE edge (model said skip)        │
│                                                             │
│  → Solution: Don't trust uncalibrated edge on longshots    │
│  → Calibrate probabilities first, THEN calculate edge      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Expected Calibration Effect

```
BEFORE: Model probability vs Actual win rate (Miscalibrated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actual Win Rate
    │
20% ┤
    │                                    ← Perfect calibration
15% ┤               .
    │        x
10% ┤   x                               x = Actual data
    │                                   . = Model prediction
 5% ┤                                   
    │
    └─────────────────────────────────────────
      5%    10%    15%    20%   Model Probability

Model says 15% → Actually wins 5% (overconfident!)


AFTER: Model probability vs Actual win rate (Calibrated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actual Win Rate
    │
20% ┤
    │                           .
15% ┤                    .
    │              .                     x = Actual data
10% ┤        .                           . = Calibrated prediction
    │   .
 5% ┤
    │
    └─────────────────────────────────────────
      5%    10%    15%    20%   Calibrated Probability

Calibrated model matches reality → Better edge estimates
```

---

**Status**: 🚀 System complete and tested  
**Next**: Deploy to production, accumulate data, train when ready
