# Variant B Production Model

This directory contains the frozen Variant B model for production use.

## Model Specification
- **Variant**: B (Market + In-Season Rolling Stats)
- **Features**: 43
- **Test AUC**: 0.8111
- **Approved ROI**: +25.3% at 0.15 edge threshold
- **Audit Date**: December 8, 2025
- **Status**: PRODUCTION-READY ✅

## Files
- `variant_b_metadata.json`: Model metadata and configuration
- `variant_b_model.pkl`: Trained GradientBoostingClassifier (TODO)
- `variant_b_scaler.pkl`: Feature scaler if needed (TODO)

## Usage
```python
from ml.ncaabb_variant_b_model import load_variant_b_model, predict_variant_b

# Load model
model, scaler, metadata = load_variant_b_model()

# Generate predictions
bets_df = predict_variant_b(games_df, model, feature_cols, min_edge=0.15)
```

## Retraining
To retrain and re-freeze the model:
```bash
python3 scripts/ncaabb/freeze_variant_b_model.py
```

## Audit
See `VARIANT_B_ROBUSTNESS_REPORT.md` for full audit results.
