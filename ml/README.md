# NCAA Basketball ML Pipeline

Phase 1 implementation of KenPom-based prediction models for NCAA Men's Basketball.

## Overview

This pipeline trains machine learning models to predict game outcomes using tempo-adjusted efficiency metrics from KenPom. No Vegas lines are integrated yet (that's Phase 2).

## Models

### 1. Spread Model (Regression)
- **Purpose**: Predict expected point margin
- **Algorithm**: Gradient Boosting Regressor
- **Performance**: MAE 9.57 points, Correlation 0.67

### 2. Moneyline Model (Classification)
- **Purpose**: Predict win probability
- **Algorithm**: Gradient Boosting Classifier
- **Performance**: 72.8% accuracy, AUC 0.77

## Files

- `features_ncaabb.py` - Feature engineering from merged KenPom data
- `train_ncaabb_spread.py` - Training pipeline with CLI
- `eval_ncaabb_spread.py` - Evaluation pipeline with CLI
- `utils.py` - Shared utilities (data loading, metrics, etc.)

## Features Used (11 total)

1. **efficiency_diff** - AdjEM differential
2. **offensive_matchup** - Team offense vs opponent defense
3. **defensive_matchup** - Team defense vs opponent offense
4. **tempo_diff** - Pace differential
5. **sos_diff** - Strength of schedule differential
6. **luck_diff** - Performance vs expectation differential
7. **avg_tempo** - Average game pace
8. **rank_diff** - KenPom rank differential
9. **home_flag** - Home court advantage (placeholder)
10. **efficiency_x_tempo** - Efficiency × pace interaction ⭐ Most important
11. **matchup_product** - Offensive × defensive advantage

## Quick Start

### Train Models

```bash
# Train both spread and moneyline models
python3 ml/train_ncaabb_spread.py \
  --data-dir data/merged \
  --output-dir models/ncaabb \
  --target both \
  --seed 42
```

**Options:**
- `--target`: Choose `spread`, `moneyline`, or `both`
- `--max-season`: Limit training to specific seasons (e.g., `2023`)
- `--seed`: Random seed for reproducibility

### Evaluate Models

```bash
# Evaluate on 2024 test data
python3 ml/eval_ncaabb_spread.py \
  --data-file data/merged/merged_games_2024.csv \
  --model-dir models/ncaabb

# Save predictions to CSV
python3 ml/eval_ncaabb_spread.py \
  --data-file data/merged/merged_games_2025.csv \
  --model-dir models/ncaabb \
  --output-predictions predictions_2025.csv
```

## Training Details

- **Train Set**: 2022-2023 seasons (1,706 games)
- **Test Set**: 2024 season (860 games)
- **Split**: Time-aware (no data leakage)
- **Validation**: Cross-validation on training set

## Model Performance

### Spread Model
- MAE: 9.57 points
- RMSE: 12.12 points
- Correlation: 0.67
- Within 10 points: 59.7%

### Moneyline Model
- Accuracy: 72.8%
- AUC: 0.77
- Brier Score: 0.176
- High confidence (p ≥ 0.7): 82.6% accurate

## Feature Importance

Top 3 features by importance:
1. **efficiency_x_tempo** (32%) - Efficiency advantage amplified by pace
2. **efficiency_diff** (28%) - Raw team quality gap
3. **luck_diff** (6%) - Over/underperformance vs expectation

## Future Enhancements (TODO)

Phase 2+ features to add:
- Effective height differential
- Rim protection metrics
- 3PT attempt rate differential
- Offensive/defensive rebounding matchup
- Turnover creation vs allowed
- Recent form (last 5 games)
- Rest days (fatigue factor)
- Conference strength adjustment

See `features_ncaabb.py` for full list of TODO stubs.

## Phase 2: Vegas Integration

Next steps:
1. Ingest market lines (spreads, moneylines)
2. Calculate edge (model prediction vs market)
3. Backtest betting strategies
4. Implement Kelly criterion bet sizing
5. Track ROI by confidence threshold

Target: 54-56% ATS accuracy for profitable betting.
