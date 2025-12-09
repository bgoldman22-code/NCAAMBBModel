# Longdog Calibration System

## Overview

The **Longdog Calibration System** addresses systematic model miscalibration on extreme underdog bets (+400 American odds or higher). Historical analysis revealed that when the Variant B model shows positive edge on these longshots, it has a **0% win rate** (0-27 record when showing 10%+ edge).

This system:
1. **Filters +400 longshots from production picks** to prevent losses
2. **Routes them to a calibration experiment** for data collection
3. **Trains Platt/Isotonic calibrators** to fix probability estimates
4. **Provides utilities** to apply calibration in future iterations

## The Problem

### Historical Performance Analysis

| Odds Range | Total Games | Wins | Win Rate | Notes |
|------------|-------------|------|----------|-------|
| +1000 (15%+ edge) | 2 | 0 | 0.0% | Model showed 15%+ edge, went 0-2 |
| All +900 | 93 | 2 | 2.15% | Only 2 wins had NEGATIVE edge (-3.4%, -4.5%) |
| +400 (10%+ edge) | 27 | 0 | 0.0% | When model sees 10%+ edge: 0-27 record |
| +400 (all edge) | 340 | 19 | 5.59% | Much worse than implied probability |
| +250-400 | 369 | - | -76.45% ROI | Devastating losses |

**Key insight**: The model systematically overestimates win probability on extreme underdogs when it calculates positive edge. The only longshot wins occurred when the model correctly identified NEGATIVE edge (i.e., recommended skipping them).

### Root Cause: Calibration Failure

The model suffers from **overconfidence** on tail probabilities:
- Trained primarily on favorites and moderate underdogs (+100 to +300)
- Limited exposure to +400 longshots in training data
- No regularization for extreme probability estimates
- When it sees edge on a longshot, it's almost always wrong

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Daily Picks Generation                     │
│         (scripts/ncaabb/generate_variant_b_picks.py)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ predict_variant_b│
                    │  (in model.py)   │
                    └─────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
        ┌───────────────┐         ┌─────────────────┐
        │ bet_odds < 400│         │ bet_odds >= 400 │
        └───────────────┘         └─────────────────┘
                │                           │
                ▼                           ▼
    ┌──────────────────────┐    ┌────────────────────────┐
    │  Production Picks    │    │ Log to Experiment CSV  │
    │  (CSV/JSON output)   │    │  (with model_prob,     │
    │                      │    │   edge, outcome=None)  │
    └──────────────────────┘    └────────────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │  Fill outcomes post-game │
                              │  (manual or automated)   │
                              └──────────────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────────┐
                              │  Train Calibration Models    │
                              │  (underdog_longdogs_         │
                              │   calibration.py)            │
                              └──────────────────────────────┘
                                            │
                    ┌───────────────────────┴────────────────────┐
                    ▼                                            ▼
        ┌─────────────────────┐                    ┌──────────────────────┐
        │  Platt Scaling      │                    │ Isotonic Regression  │
        │  (platt_scaling.    │                    │ (isotonic_regression.│
        │   joblib)           │                    │  joblib)             │
        └─────────────────────┘                    └──────────────────────┘
                    │                                            │
                    └───────────────────┬────────────────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │  calibration_metadata  │
                            │  .json                 │
                            └────────────────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │  Utilities for future  │
                            │  longdog predictions   │
                            │  (longdogs_calibration_│
                            │   utils.py)            │
                            └────────────────────────┘
```

## Components

### 1. Production Filter (Task 1)

**File**: `scripts/ncaabb/generate_variant_b_picks.py`

**Changes**:
- Added odds check: `bet_odds >= 400`
- Splits predictions into `core_picks` (< 400) and `longdogs` (≥ 400)
- Only `core_picks` go to production CSV/JSON
- Logs count of excluded longdogs

**Code location**: After step 5 (predict_variant_b), before step 6 (Kelly stakes)

### 2. Experiment Logger (Task 2)

**Function**: `log_longdogs_to_experiment()`

**File**: `scripts/ncaabb/generate_variant_b_picks.py`

**Output**: `data/ncaabb/experiments/variant_b_longdogs_raw.csv`

**Schema**:
```csv
date,home_team,away_team,bet_side,american_odds,implied_prob_market,model_prob,edge,outcome
2024-12-15,Villanova,Creighton,away,1160,0.0794,0.132,0.527,
2024-12-18,UTSA,Baylor,home,450,0.1818,0.245,0.063,
```

**Fields**:
- `date`: Game date (YYYY-MM-DD)
- `home_team`, `away_team`: Team names
- `bet_side`: 'home' or 'away'
- `american_odds`: American odds (e.g., 450 = +450)
- `implied_prob_market`: Market probability (1 / (1 + odds/100))
- `model_prob`: Variant B model probability
- `edge`: model_prob - implied_prob_market
- `outcome`: None initially, filled post-game (1 = win, 0 = loss)

**Behavior**:
- Appends to existing CSV (no duplicates expected due to date-based runs)
- Creates directory if doesn't exist
- Logs count of longdogs written

### 3. Calibration Trainer (Task 3)

**File**: `ml/experiments_ncaabb/underdog_longdogs_calibration.py`

**Purpose**: Train Platt scaling and Isotonic regression calibrators on historical longdog data

**CLI Usage**:
```bash
# Train on all +400 to +2000 longdogs
python ml/experiments_ncaabb/underdog_longdogs_calibration.py \
    --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \
    --output-dir models/variant_b_calibration \
    --save-model

# Train on specific odds range
python ml/experiments_ncaabb/underdog_longdogs_calibration.py \
    --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \
    --min-odds 400 \
    --max-odds 1000 \
    --output-dir models/variant_b_calibration \
    --save-model
```

**Parameters**:
- `--input`: Path to longdog experiment CSV
- `--min-odds`: Minimum American odds (default: 400)
- `--max-odds`: Maximum American odds (default: 2000)
- `--output-dir`: Output directory for models (default: models/variant_b_calibration)
- `--save-model`: Flag to save trained models
- `--test-ratio`: Ratio of data for testing (default: 0.2)

**Outputs**:
1. `platt_scaling.joblib`: Trained Platt scaler
2. `isotonic_regression.joblib`: Trained Isotonic regressor
3. `calibration_metadata.json`: Model metadata and performance metrics

**Training Process**:
1. Load longdog data from CSV
2. Filter by odds range and remove games without outcomes
3. Split chronologically (80% train, 20% test)
4. Train Platt scaling (logistic regression on model_prob)
5. Train Isotonic regression (non-parametric monotonic mapping)
6. Evaluate both on train and test sets
7. Compare to uncalibrated baseline
8. Save models and metadata

**Evaluation Metrics**:
- **AUC**: Discrimination ability (how well it ranks probabilities)
- **Brier Score**: Calibration + discrimination (lower is better)
- **Log Loss**: Probabilistic accuracy (lower is better)
- **ROI**: Betting profitability on positive edge bets

### 4. Calibration Utilities (Task 4)

**File**: `ml/experiments_ncaabb/longdogs_calibration_utils.py`

**Functions**:

#### `load_longdogs_calibrator(calibration_type, model_dir)`
Load a trained calibration model

```python
from longdogs_calibration_utils import load_longdogs_calibrator

# Load Isotonic (usually better)
calibrator = load_longdogs_calibrator('isotonic')

# Load Platt
calibrator = load_longdogs_calibrator('platt')
```

#### `apply_longdogs_calibration(p_model, calibration_type, calibrator, model_dir)`
Apply calibration to model probabilities

```python
from longdogs_calibration_utils import apply_longdogs_calibration

# Single probability
p_cal = apply_longdogs_calibration(0.13, 'isotonic')

# Array of probabilities
p_cal = apply_longdogs_calibration(np.array([0.10, 0.15, 0.20]), 'platt')

# With pre-loaded calibrator (faster)
calibrator = load_longdogs_calibrator('isotonic')
p_cal = apply_longdogs_calibration(p_model, 'isotonic', calibrator=calibrator)
```

#### `get_calibration_info(model_dir)`
Print information about calibration models

```python
from longdogs_calibration_utils import get_calibration_info

get_calibration_info()
```

#### `compare_calibration_methods(p_model_samples, model_dir)`
Compare Platt vs Isotonic on sample probabilities

```python
from longdogs_calibration_utils import compare_calibration_methods

test_probs = np.array([0.05, 0.08, 0.10, 0.12, 0.15])
comparison = compare_calibration_methods(test_probs)
print(comparison)
```

## Calibration Methods

### Platt Scaling

**Method**: Logistic regression on model probabilities

**Formula**: 
```
p_calibrated = 1 / (1 + exp(-(a * p_model + b)))
```

**Pros**:
- Simple, interpretable (2 parameters)
- Fast to train and apply
- Works well when miscalibration is systematic (e.g., consistent overconfidence)

**Cons**:
- Assumes logistic relationship
- Less flexible than Isotonic

**When to use**: 
- Limited data (< 100 samples)
- Prefer interpretability
- Miscalibration appears monotonic

### Isotonic Regression

**Method**: Non-parametric monotonic mapping

**Formula**:
```
p_calibrated = Isotonic(p_model)
(piecewise constant function)
```

**Pros**:
- Very flexible, no assumptions about shape
- Can capture complex miscalibration patterns
- Often outperforms Platt in practice

**Cons**:
- Needs more data (100+ samples)
- Less interpretable (many threshold points)
- Can overfit with sparse data

**When to use**:
- Sufficient data (100+ samples)
- Miscalibration is non-linear
- Prioritize performance over interpretability

## Workflow

### Initial Setup (One-Time)

1. **Filter production picks**:
   - Already done in `generate_variant_b_picks.py`
   - All +400 bets automatically excluded and logged

2. **Accumulate data**:
   - Run daily picks generation as normal
   - Longdogs logged to `data/ncaabb/experiments/variant_b_longdogs_raw.csv`
   - Wait for 50+ samples with outcomes

3. **Fill outcomes** (manual or automated):
   ```python
   import pandas as pd
   
   # Load experiment data
   df = pd.read_csv('data/ncaabb/experiments/variant_b_longdogs_raw.csv')
   
   # Fill outcomes (1 = win, 0 = loss)
   # ... your outcome filling logic ...
   
   df.to_csv('data/ncaabb/experiments/variant_b_longdogs_raw.csv', index=False)
   ```

4. **Train calibrators**:
   ```bash
   python ml/experiments_ncaabb/underdog_longdogs_calibration.py \
       --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \
       --output-dir models/variant_b_calibration \
       --save-model
   ```

5. **Check calibration info**:
   ```bash
   python ml/experiments_ncaabb/longdogs_calibration_utils.py
   ```

### Applying Calibration (Future Iteration)

Once calibration models are trained, you can optionally re-enable longdogs in production with calibrated probabilities:

```python
from ml.experiments_ncaabb.longdogs_calibration_utils import (
    load_longdogs_calibrator,
    apply_longdogs_calibration
)

# In predict_variant_b() or similar:

# Load calibrator once (expensive)
calibrator = load_longdogs_calibrator('isotonic')

# For each longdog candidate:
if bet_odds >= 400:
    # Apply calibration
    p_calibrated = apply_longdogs_calibration(
        model_prob,
        'isotonic',
        calibrator=calibrator
    )
    
    # Recalculate edge with calibrated probability
    edge_calibrated = p_calibrated - implied_prob
    
    # Only bet if calibrated edge is still positive
    if edge_calibrated > min_edge:
        # Add to bets
        pass
```

**Note**: For now, longdogs remain excluded from production. Calibration is an experimental path for future exploration after sufficient data accumulation.

## Data Requirements

### Minimum Sample Sizes

| Calibration Method | Minimum Samples | Recommended Samples |
|--------------------|-----------------|---------------------|
| Platt Scaling | 30 | 50+ |
| Isotonic Regression | 50 | 100+ |

**Current status**: `variant_b_longdogs_raw.csv` starts empty. Need to accumulate data over time.

### Data Quality

- **Chronological order**: Important for train/test split
- **No lookahead bias**: Outcomes filled AFTER game completion
- **Representative odds range**: Should cover +400 to +2000
- **Balanced outcomes**: Ideally some wins, not all losses (though realistically will be ~5-10% win rate)

## Performance Expectations

### Uncalibrated Baseline (Current)

- **Win rate**: ~5-10% (worse than implied probability)
- **ROI**: Highly negative (-50% to -100%)
- **Edge accuracy**: When model shows 10%+ edge: 0% win rate

### Calibrated Performance (Expected)

- **Win rate**: Closer to implied probability (10-15%)
- **ROI**: Break-even to slightly positive (depends on data quality)
- **Edge accuracy**: Calibrated edge should be more reliable

**Goal**: Not to make longdogs wildly profitable, but to:
1. Accurately estimate true win probability
2. Only bet when there's genuine edge (not phantom edge from miscalibration)
3. Reduce losses from overconfident longshot picks

## Files Modified/Created

### Modified Files

1. **scripts/ncaabb/generate_variant_b_picks.py**
   - Added `log_longdogs_to_experiment()` function
   - Added +400 filter after step 5 (predict_variant_b)
   - Splits picks into core_picks and longdogs
   - Logs longdogs to experiment CSV
   - Returns empty output if all picks are longshots

### New Files

1. **ml/experiments_ncaabb/underdog_longdogs_calibration.py** (461 lines)
   - Complete training script for Platt/Isotonic calibrators
   - CLI with configurable odds range
   - Comprehensive evaluation (AUC, Brier, log loss, ROI)
   - Saves models and metadata following project convention

2. **ml/experiments_ncaabb/longdogs_calibration_utils.py** (251 lines)
   - Helper functions to load and apply calibration
   - Supports both Platt and Isotonic
   - Includes comparison utilities
   - Example usage in `__main__`

3. **ncaa-basketball/ml/experiments_ncaabb/LONGDOG_CALIBRATION_SYSTEM.md** (this file)
   - Complete documentation of system
   - Architecture diagrams
   - Usage examples
   - Workflow guide

### Data Files (Generated at Runtime)

1. **data/ncaabb/experiments/variant_b_longdogs_raw.csv**
   - Experiment data sink
   - Appended to daily by picks generator
   - Filled with outcomes post-game

2. **models/variant_b_calibration/**
   - `platt_scaling.joblib`: Trained Platt scaler
   - `isotonic_regression.joblib`: Trained Isotonic regressor
   - `calibration_metadata.json`: Model metadata and metrics

## Troubleshooting

### No longdogs being logged

**Symptoms**: `variant_b_longdogs_raw.csv` not created or empty

**Causes**:
- No games with +400 odds in today's slate
- All longdogs filtered out by min_edge threshold BEFORE odds check
- Check: Are there any +400 games in input odds data?

**Solution**: This is expected behavior. Longshots are rare.

### Not enough data to train calibration

**Symptoms**: Script warns "Only X samples available"

**Causes**:
- Haven't accumulated 50+ longdog samples yet
- Too narrow odds range (--min-odds, --max-odds)

**Solution**: 
- Wait for more data to accumulate
- Widen odds range if possible
- Lower minimum from 50 to 30 for Platt (edit script)

### Calibration makes performance worse

**Symptoms**: Calibrated ROI < Uncalibrated ROI

**Causes**:
- Insufficient training data
- Test set not representative
- Calibration overfitting

**Solution**:
- Increase training data
- Use Platt instead of Isotonic (simpler, less overfitting)
- Add regularization (future enhancement)

### Models not found when loading

**Symptoms**: FileNotFoundError when calling load_longdogs_calibrator()

**Causes**:
- Haven't trained calibration models yet
- Wrong model_dir path

**Solution**:
```bash
python ml/experiments_ncaabb/underdog_longdogs_calibration.py \
    --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \
    --output-dir models/variant_b_calibration \
    --save-model
```

## Future Enhancements

### Short-Term

1. **Automated outcome filling**
   - Script to fetch game results and fill outcomes
   - Run daily after games complete

2. **Real-time calibration**
   - Retrain calibrators weekly as data accumulates
   - Compare performance to previous version

3. **Calibration diagnostics**
   - Reliability diagrams (calibration curves)
   - Calibration error metrics (ECE, MCE)

### Medium-Term

1. **Odds-stratified calibration**
   - Separate calibrators for +400-600, +600-1000, +1000+
   - May improve performance on extreme longshots

2. **Feature-aware calibration**
   - Calibrate based on opponent strength, venue, etc.
   - Not just model_prob, but contextual factors

3. **Ensemble calibration**
   - Weighted combination of Platt and Isotonic
   - Possibly better than either alone

### Long-Term

1. **Beta calibration**
   - Generalization of Platt scaling (3 parameters)
   - More flexible than Platt, more stable than Isotonic

2. **Deep calibration**
   - Neural network calibrator
   - Can capture very complex miscalibration patterns

3. **Online calibration**
   - Update calibrators incrementally as new data arrives
   - No need for full retraining

## References

### Academic Papers

1. **Platt Scaling**: Platt, J. (1999). "Probabilistic outputs for support vector machines"
2. **Isotonic Regression**: Zadrozny, B., & Elkan, C. (2002). "Transforming classifier scores into accurate multiclass probability estimates"
3. **Calibration Overview**: Guo, C., et al. (2017). "On calibration of modern neural networks"

### Project Documentation

- `EDGE_PROFITABILITY_ANALYSIS.md`: Historical analysis revealing miscalibration
- `UNDERDOG_PATTERNS_ANALYSIS.md`: Deep dive into +400 underdog patterns
- `generate_variant_b_picks.py`: Main picks generation script
- `ncaabb_variant_b_model.py`: Model inference module

## Summary

The Longdog Calibration System is a **defensive mechanism** to prevent losses from model overconfidence on extreme underdogs. By:

1. **Filtering +400 bets from production** → Immediately stops losses
2. **Logging them to experiment CSV** → Builds calibration dataset
3. **Training Platt/Isotonic calibrators** → Fixes probability estimates
4. **Providing utilities for future use** → Enables potential reintroduction

We transform a systematic weakness (0-27 record on +400 with 10%+ edge) into a controlled experiment with potential upside (calibrated longdogs might eventually be profitable).

**Current status**: Production filter active, experiment data accumulating, calibration framework ready. Next step: accumulate 50+ samples with outcomes, train calibrators, evaluate performance.
