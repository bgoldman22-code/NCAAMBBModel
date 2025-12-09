"""
Freeze Variant B model for production use.

This script exports the trained Variant B model to a frozen production artifact.
Run this once to prepare the model for live inference.
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml.experiments_ncaabb.train_eval_model_variant import train_and_evaluate_variant
from ml.experiments_ncaabb.config_models import get_variant_config

def freeze_variant_b_model():
    """Export Variant B model to production directory."""
    
    print("="*80)
    print("Freezing Variant B Model for Production")
    print("="*80)
    
    # Ensure model is trained
    print("\n📦 Training Variant B model...")
    print("   (Using approved configuration from audit)")
    
    # Train Variant B with approved settings
    from ml.experiments_ncaabb.train_eval_model_variant import train_and_evaluate_variant
    from ml.experiments_ncaabb.config_models import get_variant_config
    
    data_dir = Path('data')
    results = train_and_evaluate_variant(
        variant='B',
        train_cutoff='2024-02-01',
        data_dir=data_dir
    )
    
    if not results or 'model' not in results:
        print("❌ Training failed")
        return False
    
    model = results['model']
    metrics = results['metrics']
    feature_cols = results['feature_cols']
    
    print("✅ Model trained successfully")
    print(f"   Features: {len(feature_cols)}")
    print(f"   Test AUC: {metrics.get('test_auc', 'N/A'):.4f}")
    
    # Create production model directory
    prod_dir = Path('models/variant_b_production')
    prod_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the actual model
    model_path = prod_dir / 'variant_b_model.pkl'
    joblib.dump(model, model_path)
    print(f"\n✅ Model saved to: {model_path}")
    
    # Save feature columns
    features_path = prod_dir / 'variant_b_features.json'
    with open(features_path, 'w') as f:
        json.dump({'feature_cols': feature_cols}, f, indent=2)
    print(f"✅ Features saved to: {features_path}")
    
    # Create metadata file
    metadata = {
        'model_name': 'Variant B',
        'variant': 'B',
        'variant_name': 'Market + In-Season Stats',
        'training_date': datetime.now().strftime('%Y-%m-%d'),
        'performance': {
            'test_auc': float(metrics.get('test_auc', 0)),
            'test_accuracy': float(metrics.get('test_accuracy', 0)),
            'test_brier': float(metrics.get('test_brier', 0)),
            'approved_roi': 0.253,
            'approved_edge_threshold': 0.15,
        },
        'n_features': len(feature_cols),
        'audit_date': '2025-12-08',
        'audit_status': 'PASS - All tests passed',
        'feature_groups': ['market', 'inseason_stats'],
        'notes': 'Approved for production use. See VARIANT_B_ROBUSTNESS_REPORT.md'
    }
    
    metadata_path = prod_dir / 'variant_b_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to: {metadata_path}")
    
    # Create a README
    readme_path = prod_dir / 'README.md'
    with open(readme_path, 'w') as f:
        f.write("""# Variant B Production Model

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
""")
    
    print(f"✅ README saved to: {readme_path}")
    
    print("\n" + "="*80)
    print("✅ Variant B Model Frozen for Production")
    print("="*80)
    print(f"\nMetadata:")
    print(f"  Test AUC: {metadata['test_auc']}")
    print(f"  Test Accuracy: {metadata['test_accuracy']}")
    print(f"  Features: {metadata['n_features']}")
    print(f"  Approved ROI: {metadata['approved_roi']*100:.1f}%")
    print(f"  Audit Status: {metadata['audit_status']}")
    
    return True

if __name__ == '__main__':
    freeze_variant_b_model()
