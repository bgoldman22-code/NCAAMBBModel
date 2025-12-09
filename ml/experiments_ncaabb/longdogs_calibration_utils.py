#!/usr/bin/env python3
"""
Longdog Calibration Utilities

Helper functions to load and apply Platt/Isotonic calibration models
for +400 underdog predictions.

Usage:
    from longdogs_calibration_utils import load_longdogs_calibrator, apply_longdogs_calibration
    
    # Load calibrator
    calibrator = load_longdogs_calibrator('isotonic')
    
    # Apply to model probabilities
    p_calibrated = apply_longdogs_calibration(p_model, 'isotonic')
"""

import json
from pathlib import Path

import joblib
import numpy as np


def load_longdogs_calibrator(calibration_type='isotonic', 
                             model_dir='models/variant_b_calibration'):
    """
    Load a trained longdog calibration model
    
    Args:
        calibration_type: 'platt' or 'isotonic'
        model_dir: Directory containing calibration models
        
    Returns:
        Trained calibration model (sklearn LogisticRegression or IsotonicRegression)
        
    Raises:
        FileNotFoundError: If model file doesn't exist
        ValueError: If calibration_type is invalid
    """
    if calibration_type not in ['platt', 'isotonic']:
        raise ValueError(f"calibration_type must be 'platt' or 'isotonic', got: {calibration_type}")
    
    model_path = Path(model_dir)
    
    if calibration_type == 'platt':
        file_path = model_path / 'platt_scaling.joblib'
    else:  # isotonic
        file_path = model_path / 'isotonic_regression.joblib'
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Calibration model not found: {file_path}\n"
            f"Run underdog_longdogs_calibration.py to train calibration models"
        )
    
    calibrator = joblib.load(file_path)
    
    # Load metadata for info
    metadata_path = model_path / 'calibration_metadata.json'
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        print(f"✓ Loaded {calibration_type} calibrator")
        print(f"  Trained on: {metadata['training_data']['num_samples']} samples")
        print(f"  Odds range: +{metadata['odds_range']['min']} to +{metadata['odds_range']['max']}")
        
        if calibration_type == 'platt':
            test_perf = metadata['test_performance']['platt_scaling']
        else:
            test_perf = metadata['test_performance']['isotonic_regression']
        
        print(f"  Test ROI: {test_perf['roi']:+.2f}%")
        print(f"  Test AUC: {test_perf['auc']:.4f}")
    
    return calibrator


def apply_longdogs_calibration(p_model, calibration_type='isotonic',
                               calibrator=None, model_dir='models/variant_b_calibration'):
    """
    Apply longdog calibration to model probabilities
    
    Args:
        p_model: Model probability (single value or array)
        calibration_type: 'platt' or 'isotonic'
        calibrator: Pre-loaded calibrator (optional, will load if None)
        model_dir: Directory containing calibration models (if calibrator is None)
        
    Returns:
        Calibrated probability (same shape as p_model)
        
    Examples:
        # Single probability
        p_cal = apply_longdogs_calibration(0.13, 'isotonic')
        
        # Array of probabilities
        p_cal = apply_longdogs_calibration(np.array([0.10, 0.15, 0.20]), 'platt')
        
        # With pre-loaded calibrator (faster for batch processing)
        calibrator = load_longdogs_calibrator('isotonic')
        p_cal = apply_longdogs_calibration(p_model, 'isotonic', calibrator=calibrator)
    """
    # Load calibrator if not provided
    if calibrator is None:
        calibrator = load_longdogs_calibrator(calibration_type, model_dir)
    
    # Convert to numpy array
    p_model_arr = np.atleast_1d(p_model)
    
    # Apply calibration
    if calibration_type == 'platt':
        # Platt expects 2D input
        p_calibrated = calibrator.predict_proba(p_model_arr.reshape(-1, 1))[:, 1]
    else:  # isotonic
        # Isotonic expects 1D input
        p_calibrated = calibrator.predict(p_model_arr)
    
    # Return same shape as input
    if np.isscalar(p_model):
        return float(p_calibrated[0])
    else:
        return p_calibrated


def get_calibration_info(model_dir='models/variant_b_calibration'):
    """
    Get information about available calibration models
    
    Args:
        model_dir: Directory containing calibration models
        
    Returns:
        dict with calibration metadata, or None if not found
    """
    metadata_path = Path(model_dir) / 'calibration_metadata.json'
    
    if not metadata_path.exists():
        print(f"⚠️  No calibration metadata found at: {metadata_path}")
        return None
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print("="*60)
    print("Longdog Calibration Models")
    print("="*60)
    print(f"Created: {metadata['created_at']}")
    print(f"Base model: {metadata['base_model']}")
    print(f"Odds range: +{metadata['odds_range']['min']} to +{metadata['odds_range']['max']}")
    print(f"\nTraining data:")
    print(f"  Samples: {metadata['training_data']['num_samples']}")
    print(f"  Date range: {metadata['training_data']['date_range']['start'][:10]} to {metadata['training_data']['date_range']['end'][:10]}")
    print(f"  Win rate: {metadata['training_data']['win_rate']:.1%}")
    
    print(f"\nTest performance:")
    print(f"\n  Platt Scaling:")
    platt = metadata['test_performance']['platt_scaling']
    print(f"    AUC:      {platt['auc']:.4f}")
    print(f"    Brier:    {platt['brier']:.4f}")
    print(f"    ROI:      {platt['roi']:+.2f}%")
    print(f"    Win rate: {platt['win_rate']:.1%}")
    
    print(f"\n  Isotonic Regression:")
    iso = metadata['test_performance']['isotonic_regression']
    print(f"    AUC:      {iso['auc']:.4f}")
    print(f"    Brier:    {iso['brier']:.4f}")
    print(f"    ROI:      {iso['roi']:+.2f}%")
    print(f"    Win rate: {iso['win_rate']:.1%}")
    
    print("="*60)
    
    return metadata


def compare_calibration_methods(p_model_samples, 
                                model_dir='models/variant_b_calibration'):
    """
    Compare Platt vs Isotonic calibration on sample probabilities
    
    Useful for debugging/understanding calibration behavior
    
    Args:
        p_model_samples: Array of model probabilities to compare
        model_dir: Directory containing calibration models
        
    Returns:
        DataFrame comparing uncalibrated vs calibrated probabilities
    """
    import pandas as pd
    
    # Load both calibrators
    platt = load_longdogs_calibrator('platt', model_dir)
    isotonic = load_longdogs_calibrator('isotonic', model_dir)
    
    # Apply both calibrations
    p_platt = apply_longdogs_calibration(p_model_samples, 'platt', calibrator=platt)
    p_isotonic = apply_longdogs_calibration(p_model_samples, 'isotonic', calibrator=isotonic)
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame({
        'p_model': p_model_samples,
        'p_platt': p_platt,
        'p_isotonic': p_isotonic,
        'platt_adjustment': p_platt - p_model_samples,
        'isotonic_adjustment': p_isotonic - p_model_samples
    })
    
    return comparison_df


# Example usage
if __name__ == '__main__':
    import sys
    
    print("Longdog Calibration Utilities - Example Usage\n")
    
    # Check if models exist
    model_dir = 'models/variant_b_calibration'
    metadata_path = Path(model_dir) / 'calibration_metadata.json'
    
    if not metadata_path.exists():
        print("⚠️  No calibration models found!")
        print(f"   Expected at: {model_dir}")
        print("\nTo train calibration models, run:")
        print("   python ml/experiments_ncaabb/underdog_longdogs_calibration.py \\")
        print("       --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \\")
        print("       --output-dir models/variant_b_calibration \\")
        print("       --save-model")
        sys.exit(1)
    
    # Show calibration info
    get_calibration_info(model_dir)
    
    # Example calibration
    print("\nExample: Calibrating model probabilities")
    print("="*60)
    
    # Test probabilities (typical longdog range: 5% to 15%)
    test_probs = np.array([0.05, 0.08, 0.10, 0.12, 0.15])
    
    print(f"\nUncalibrated model probabilities:")
    print(test_probs)
    
    # Load calibrators once
    platt = load_longdogs_calibrator('platt', model_dir)
    isotonic = load_longdogs_calibrator('isotonic', model_dir)
    
    # Apply calibrations
    p_platt = apply_longdogs_calibration(test_probs, 'platt', calibrator=platt)
    p_isotonic = apply_longdogs_calibration(test_probs, 'isotonic', calibrator=isotonic)
    
    print(f"\nPlatt calibrated:")
    print(p_platt)
    
    print(f"\nIsotonic calibrated:")
    print(p_isotonic)
    
    # Show comparison
    print(f"\nDetailed comparison:")
    comparison = compare_calibration_methods(test_probs, model_dir)
    print(comparison.to_string(index=False))
    
    print("\n✅ Calibration utilities working correctly!")
