#!/usr/bin/env python3
"""
Evaluate NCAA Basketball spread and moneyline prediction models.

This script loads trained models and evaluates them on a test dataset,
producing detailed metrics and calibration reports.

Usage:
    python3 ml/eval_ncaabb_spread.py \\
        --data-file data/merged/merged_games_2024.csv \\
        --model-dir models/ncaabb
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.features_ncaabb import build_features
from ml.utils import (
    load_model,
    load_json,
    calculate_regression_metrics,
    calculate_classification_metrics,
    calibration_report
)


def evaluate_spread_model(model, X, y_true):
    """Evaluate spread prediction model."""
    print("\n" + "="*80)
    print("SPREAD MODEL EVALUATION (Regression)")
    print("="*80)
    
    y_pred = model.predict(X)
    metrics = calculate_regression_metrics(y_true, y_pred)
    
    print(f"\n📈 Metrics:")
    print(f"   MAE:         {metrics['mae']:.2f} points")
    print(f"   RMSE:        {metrics['rmse']:.2f} points")
    print(f"   Correlation: {metrics['correlation']:.4f}")
    
    # Error distribution
    errors = np.abs(y_true - y_pred)
    
    print(f"\n📊 Error Distribution:")
    print(f"   Within 5 points:  {(errors <= 5).mean()*100:.1f}%")
    print(f"   Within 10 points: {(errors <= 10).mean()*100:.1f}%")
    print(f"   Within 15 points: {(errors <= 15).mean()*100:.1f}%")
    print(f"   Max error:        {errors.max():.1f} points")
    
    # Sample predictions
    print(f"\n🎯 Sample Predictions:")
    sample_df = pd.DataFrame({
        'Actual': y_true.values[:10],
        'Predicted': y_pred[:10],
        'Error': errors[:10]
    })
    print(sample_df.to_string(index=False))
    
    return metrics, y_pred


def evaluate_moneyline_model(model, X, y_true):
    """Evaluate win probability prediction model."""
    print("\n" + "="*80)
    print("MONEYLINE MODEL EVALUATION (Classification)")
    print("="*80)
    
    y_pred_proba = model.predict_proba(X)[:, 1]
    metrics = calculate_classification_metrics(y_true, y_pred_proba)
    
    print(f"\n📈 Metrics:")
    print(f"   Accuracy:    {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"   Brier Score: {metrics['brier_score']:.4f}")
    print(f"   Log Loss:    {metrics['log_loss']:.4f}")
    print(f"   AUC:         {metrics['auc']:.4f}")
    
    # Calibration analysis
    print(f"\n📊 Calibration Report:")
    print(f"   (Comparing predicted win probability vs actual win rate)")
    
    calibration_df = calibration_report(y_true.values, y_pred_proba, n_bins=10)
    
    print(f"\n   {'Pred Range':15s} {'Avg Pred':>10s} {'Actual':>10s} {'Count':>8s} {'Diff':>8s}")
    print(f"   {'-'*15} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    
    for _, row in calibration_df.iterrows():
        pred_range = f"{row['min_pred']:.2f}-{row['max_pred']:.2f}"
        diff = row['actual_win_rate'] - row['avg_predicted']
        diff_str = f"{diff:+.3f}"
        
        print(f"   {pred_range:15s} {row['avg_predicted']:10.3f} {row['actual_win_rate']:10.3f} "
              f"{int(row['count']):8d} {diff_str:>8s}")
    
    # Confidence analysis
    print(f"\n📊 Prediction Confidence Analysis:")
    high_conf = (y_pred_proba >= 0.7) | (y_pred_proba <= 0.3)
    medium_conf = (y_pred_proba >= 0.55) & (y_pred_proba <= 0.7) | (y_pred_proba >= 0.3) & (y_pred_proba <= 0.45)
    low_conf = (y_pred_proba > 0.45) & (y_pred_proba < 0.55)
    
    if high_conf.sum() > 0:
        acc_high = ((y_pred_proba[high_conf] >= 0.5) == y_true[high_conf]).mean()
        print(f"   High confidence (p >= 0.7 or p <= 0.3): {high_conf.sum():4d} games, {acc_high*100:.1f}% accurate")
    
    if medium_conf.sum() > 0:
        acc_med = ((y_pred_proba[medium_conf] >= 0.5) == y_true[medium_conf]).mean()
        print(f"   Medium confidence (0.55-0.7, 0.3-0.45):  {medium_conf.sum():4d} games, {acc_med*100:.1f}% accurate")
    
    if low_conf.sum() > 0:
        acc_low = ((y_pred_proba[low_conf] >= 0.5) == y_true[low_conf]).mean()
        print(f"   Low confidence (0.45-0.55):              {low_conf.sum():4d} games, {acc_low*100:.1f}% accurate")
    
    # Sample predictions
    print(f"\n🎯 Sample Predictions:")
    y_pred_binary = (y_pred_proba >= 0.5).astype(int)
    sample_df = pd.DataFrame({
        'Actual': y_true.values[:10],
        'Predicted': y_pred_binary[:10],
        'Win Prob': y_pred_proba[:10],
        'Correct': (y_pred_binary[:10] == y_true.values[:10])
    })
    print(sample_df.to_string(index=False))
    
    return metrics, y_pred_proba, calibration_df


def main():
    parser = argparse.ArgumentParser(description='Evaluate NCAA Basketball prediction models')
    parser.add_argument('--data-file', type=str, required=True,
                       help='Path to merged game data CSV file')
    parser.add_argument('--model-dir', type=str, required=True,
                       help='Directory containing trained models')
    parser.add_argument('--output-predictions', type=str, default=None,
                       help='Optional path to save predictions CSV')
    
    args = parser.parse_args()
    
    print("="*80)
    print("NCAA BASKETBALL MODEL EVALUATION")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Data file:       {args.data_file}")
    print(f"  Model directory: {args.model_dir}")
    
    model_path = Path(args.model_dir)
    
    # ============================================================
    # LOAD DATA
    # ============================================================
    
    print("\n" + "="*80)
    print("LOADING DATA")
    print("="*80)
    
    df = pd.read_csv(args.data_file)
    print(f"\n✅ Loaded {len(df):,} games")
    
    if 'season' in df.columns:
        print(f"   Season: {df['season'].iloc[0]}")
    
    # ============================================================
    # BUILD FEATURES
    # ============================================================
    
    print("\n" + "="*80)
    print("BUILDING FEATURES")
    print("="*80)
    
    X, y_margin, y_win = build_features(df)
    
    print(f"\n✅ Features built: {X.shape[0]:,} games, {X.shape[1]} features")
    
    # ============================================================
    # LOAD MODELS AND EVALUATE
    # ============================================================
    
    results = {}
    
    # Check which models are available
    spread_model_path = model_path / 'spread_model.pkl'
    ml_model_path = model_path / 'moneyline_model.pkl'
    
    if spread_model_path.exists():
        print(f"\n✅ Found spread model")
        spread_model = load_model(spread_model_path)
        
        metrics_spread, pred_margin = evaluate_spread_model(spread_model, X, y_margin)
        results['spread_predictions'] = pred_margin
        results['spread_metrics'] = metrics_spread
    else:
        print(f"\n⚠️  Spread model not found at {spread_model_path}")
    
    if ml_model_path.exists():
        print(f"\n✅ Found moneyline model")
        ml_model = load_model(ml_model_path)
        
        metrics_ml, pred_proba, calibration_df = evaluate_moneyline_model(ml_model, X, y_win)
        results['win_probabilities'] = pred_proba
        results['ml_metrics'] = metrics_ml
        results['calibration'] = calibration_df
    else:
        print(f"\n⚠️  Moneyline model not found at {ml_model_path}")
    
    # ============================================================
    # SAVE PREDICTIONS (Optional)
    # ============================================================
    
    if args.output_predictions and results:
        output_df = df.copy()
        
        if 'spread_predictions' in results:
            output_df['predicted_margin'] = results['spread_predictions']
        
        if 'win_probabilities' in results:
            output_df['win_probability'] = results['win_probabilities']
        
        output_df.to_csv(args.output_predictions, index=False)
        print(f"\n✅ Predictions saved to {args.output_predictions}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    
    print("\n" + "="*80)
    print("✅ EVALUATION COMPLETE")
    print("="*80)
    
    if 'spread_metrics' in results:
        print(f"\nSpread Model: MAE = {results['spread_metrics']['mae']:.2f} points")
    
    if 'ml_metrics' in results:
        print(f"Moneyline Model: Accuracy = {results['ml_metrics']['accuracy']*100:.2f}%")


if __name__ == "__main__":
    main()
