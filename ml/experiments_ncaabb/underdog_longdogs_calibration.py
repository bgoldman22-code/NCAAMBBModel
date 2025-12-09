#!/usr/bin/env python3
"""
Longdog Calibration Training Script

Trains Platt scaling and Isotonic regression calibrators on +400 underdogs
to fix model miscalibration. Historical analysis showed:

- +1000 longshots with 15%+ edge: 0-2 record (0% win rate)
- All +900 longshots: 93 games, 2 wins (2.15%), both had NEGATIVE edge
- +400 underdogs with 10%+ edge: 0-27 record (0% win rate)

The model systematically overestimates win probability on extreme underdogs
when it sees an edge. This script trains calibrators to fix this.

Usage:
    python underdog_longdogs_calibration.py \\
        --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \\
        --min-odds 400 \\
        --max-odds 2000 \\
        --output-dir models/variant_b_calibration \\
        --save-model
"""

import argparse
import json
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

warnings.filterwarnings('ignore')


def american_to_implied_prob(odds):
    """Convert American odds to implied probability"""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def load_longdogs_data(input_path, min_odds=400, max_odds=2000):
    """
    Load longdog candidates from experiment CSV
    
    Returns:
        pd.DataFrame with columns: date, model_prob, outcome, american_odds
    """
    df = pd.read_csv(input_path)
    
    # Filter by odds range
    df = df[(df['american_odds'] >= min_odds) & (df['american_odds'] <= max_odds)].copy()
    
    # Remove rows without outcomes (future games)
    df = df[df['outcome'].notna()].copy()
    
    # Convert outcome to binary (1 = win, 0 = loss)
    df['outcome'] = df['outcome'].astype(int)
    
    # Sort by date
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    print(f"📊 Loaded {len(df)} longdog candidates")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"   Odds range: +{df['american_odds'].min():.0f} to +{df['american_odds'].max():.0f}")
    print(f"   Win rate: {df['outcome'].mean():.1%} ({df['outcome'].sum()}/{len(df)})")
    
    return df


def split_by_date(df, test_ratio=0.2):
    """
    Split data chronologically (avoids lookahead bias)
    
    Returns:
        train_df, test_df
    """
    split_idx = int(len(df) * (1 - test_ratio))
    
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    print(f"\n📅 Chronological split:")
    print(f"   Train: {len(train_df)} games ({train_df['date'].min().date()} to {train_df['date'].max().date()})")
    print(f"   Test:  {len(test_df)} games ({test_df['date'].min().date()} to {test_df['date'].max().date()})")
    print(f"   Train win rate: {train_df['outcome'].mean():.1%}")
    print(f"   Test win rate:  {test_df['outcome'].mean():.1%}")
    
    return train_df, test_df


def train_platt_scaling(train_df):
    """
    Train Platt scaling (logistic regression on model probabilities)
    
    Maps: p_model -> p_calibrated
    """
    X = train_df['model_prob'].values.reshape(-1, 1)
    y = train_df['outcome'].values
    
    platt = LogisticRegression(solver='lbfgs', max_iter=1000)
    platt.fit(X, y)
    
    print(f"\n🔧 Platt Scaling Trained")
    print(f"   Coefficient: {platt.coef_[0][0]:.4f}")
    print(f"   Intercept:   {platt.intercept_[0]:.4f}")
    
    return platt


def train_isotonic_regression(train_df):
    """
    Train Isotonic regression (non-parametric monotonic mapping)
    
    More flexible than Platt, doesn't assume logistic shape
    """
    X = train_df['model_prob'].values
    y = train_df['outcome'].values
    
    isotonic = IsotonicRegression(out_of_bounds='clip')
    isotonic.fit(X, y)
    
    print(f"\n🔧 Isotonic Regression Trained")
    print(f"   Min X: {isotonic.X_min_:.4f}")
    print(f"   Max X: {isotonic.X_max_:.4f}")
    print(f"   Num thresholds: {len(isotonic.X_thresholds_)}")
    
    return isotonic


def evaluate_calibration(df, model, model_type='platt'):
    """
    Evaluate calibration model on train or test set
    
    Computes:
    - AUC (discrimination)
    - Brier score (calibration + discrimination)
    - Log loss (probabilistic accuracy)
    - ROI (betting profitability)
    """
    X = df['model_prob'].values
    y = df['outcome'].values
    
    # Get calibrated probabilities
    if model_type == 'platt':
        p_calibrated = model.predict_proba(X.reshape(-1, 1))[:, 1]
    else:  # isotonic
        p_calibrated = model.predict(X)
    
    # Compute metrics
    auc = roc_auc_score(y, p_calibrated)
    brier = brier_score_loss(y, p_calibrated)
    logloss = log_loss(y, p_calibrated)
    
    # Compute ROI (if we bet all these)
    df_eval = df.copy()
    df_eval['p_calibrated'] = p_calibrated
    df_eval['p_market'] = df_eval['american_odds'].apply(american_to_implied_prob)
    df_eval['calibrated_edge'] = df_eval['p_calibrated'] - df_eval['p_market']
    
    # Only bet when calibrated model sees positive edge
    bets = df_eval[df_eval['calibrated_edge'] > 0].copy()
    
    if len(bets) > 0:
        # Profit calculation (American odds)
        bets['profit'] = bets.apply(
            lambda row: row['american_odds'] / 100 if row['outcome'] == 1 else -1,
            axis=1
        )
        
        total_profit = bets['profit'].sum()
        total_bets = len(bets)
        roi = (total_profit / total_bets) * 100
        
        num_wins = bets['outcome'].sum()
        win_rate = num_wins / total_bets
    else:
        total_bets = 0
        num_wins = 0
        win_rate = 0
        roi = 0
    
    return {
        'auc': auc,
        'brier': brier,
        'log_loss': logloss,
        'total_bets': total_bets,
        'num_wins': num_wins,
        'win_rate': win_rate,
        'roi': roi
    }


def print_metrics(metrics, label='Model'):
    """Pretty print evaluation metrics"""
    print(f"\n{'='*60}")
    print(f"{label} Performance")
    print(f"{'='*60}")
    print(f"Discrimination:")
    print(f"  AUC:         {metrics['auc']:.4f}")
    print(f"\nCalibration:")
    print(f"  Brier Score: {metrics['brier']:.4f} (lower is better)")
    print(f"  Log Loss:    {metrics['log_loss']:.4f} (lower is better)")
    print(f"\nBetting Performance (positive edge only):")
    print(f"  Total Bets:  {metrics['total_bets']}")
    print(f"  Wins:        {metrics['num_wins']}")
    print(f"  Win Rate:    {metrics['win_rate']:.1%}")
    print(f"  ROI:         {metrics['roi']:+.2f}%")
    print(f"{'='*60}")


def save_calibration_models(platt, isotonic, train_df, test_metrics_platt, 
                            test_metrics_isotonic, output_dir, min_odds, max_odds):
    """
    Save both calibration models and metadata to disk
    
    Follows project convention: save ALL trained models with metadata
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save Platt scaling model
    platt_path = output_path / 'platt_scaling.joblib'
    joblib.dump(platt, platt_path)
    print(f"\n💾 Saved Platt model: {platt_path}")
    
    # Save Isotonic regression model
    isotonic_path = output_path / 'isotonic_regression.joblib'
    joblib.dump(isotonic, isotonic_path)
    print(f"💾 Saved Isotonic model: {isotonic_path}")
    
    # Save metadata
    metadata = {
        'created_at': datetime.now().isoformat(),
        'model_type': 'longdog_calibration',
        'base_model': 'Variant B GradientBoostingClassifier',
        'calibration_methods': ['platt_scaling', 'isotonic_regression'],
        'odds_range': {
            'min': int(min_odds),
            'max': int(max_odds)
        },
        'training_data': {
            'num_samples': len(train_df),
            'date_range': {
                'start': train_df['date'].min().isoformat(),
                'end': train_df['date'].max().isoformat()
            },
            'win_rate': float(train_df['outcome'].mean()),
            'avg_odds': float(train_df['american_odds'].mean())
        },
        'test_performance': {
            'platt_scaling': {
                'auc': float(test_metrics_platt['auc']),
                'brier': float(test_metrics_platt['brier']),
                'log_loss': float(test_metrics_platt['log_loss']),
                'roi': float(test_metrics_platt['roi']),
                'total_bets': int(test_metrics_platt['total_bets']),
                'win_rate': float(test_metrics_platt['win_rate'])
            },
            'isotonic_regression': {
                'auc': float(test_metrics_isotonic['auc']),
                'brier': float(test_metrics_isotonic['brier']),
                'log_loss': float(test_metrics_isotonic['log_loss']),
                'roi': float(test_metrics_isotonic['roi']),
                'total_bets': int(test_metrics_isotonic['total_bets']),
                'win_rate': float(test_metrics_isotonic['win_rate'])
            }
        },
        'platt_params': {
            'coefficient': float(platt.coef_[0][0]),
            'intercept': float(platt.intercept_[0])
        },
        'isotonic_params': {
            'num_thresholds': len(isotonic.X_thresholds_),
            'min_x': float(isotonic.X_min_),
            'max_x': float(isotonic.X_max_)
        },
        'usage': {
            'load': 'joblib.load(model_path)',
            'apply_platt': 'platt.predict_proba(p_model.reshape(-1, 1))[:, 1]',
            'apply_isotonic': 'isotonic.predict(p_model)'
        }
    }
    
    metadata_path = output_path / 'calibration_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Saved metadata: {metadata_path}")
    print(f"\n✅ All calibration models saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Train Platt/Isotonic calibration for longdog underdogs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train on all +400 to +2000 longdogs
  python underdog_longdogs_calibration.py \\
      --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \\
      --output-dir models/variant_b_calibration \\
      --save-model
  
  # Train on specific odds range
  python underdog_longdogs_calibration.py \\
      --input data/ncaabb/experiments/variant_b_longdogs_raw.csv \\
      --min-odds 400 \\
      --max-odds 1000 \\
      --output-dir models/variant_b_calibration \\
      --save-model
        """
    )
    
    parser.add_argument('--input', required=True,
                        help='Path to longdog experiment CSV')
    parser.add_argument('--min-odds', type=int, default=400,
                        help='Minimum American odds (default: 400)')
    parser.add_argument('--max-odds', type=int, default=2000,
                        help='Maximum American odds (default: 2000)')
    parser.add_argument('--output-dir', default='models/variant_b_calibration',
                        help='Output directory for models (default: models/variant_b_calibration)')
    parser.add_argument('--save-model', action='store_true',
                        help='Save trained models to disk')
    parser.add_argument('--test-ratio', type=float, default=0.2,
                        help='Ratio of data for testing (default: 0.2)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("Longdog Calibration Training")
    print("="*60)
    
    # 1. Load data
    df = load_longdogs_data(args.input, args.min_odds, args.max_odds)
    
    if len(df) < 50:
        print(f"\n⚠️  Warning: Only {len(df)} samples available")
        print("   Need at least 50 samples for reliable calibration")
        print("   Consider:")
        print("   - Widening odds range (--min-odds, --max-odds)")
        print("   - Waiting for more data to accumulate")
        return
    
    # 2. Split chronologically
    train_df, test_df = split_by_date(df, args.test_ratio)
    
    # 3. Train Platt scaling
    platt = train_platt_scaling(train_df)
    
    # 4. Train Isotonic regression
    isotonic = train_isotonic_regression(train_df)
    
    # 5. Evaluate on training data
    print("\n" + "="*60)
    print("Training Set Evaluation")
    print("="*60)
    
    train_metrics_platt = evaluate_calibration(train_df, platt, 'platt')
    print_metrics(train_metrics_platt, 'Platt Scaling (Train)')
    
    train_metrics_isotonic = evaluate_calibration(train_df, isotonic, 'isotonic')
    print_metrics(train_metrics_isotonic, 'Isotonic Regression (Train)')
    
    # 6. Evaluate on test data
    print("\n" + "="*60)
    print("Test Set Evaluation (Unseen Data)")
    print("="*60)
    
    test_metrics_platt = evaluate_calibration(test_df, platt, 'platt')
    print_metrics(test_metrics_platt, 'Platt Scaling (Test)')
    
    test_metrics_isotonic = evaluate_calibration(test_df, isotonic, 'isotonic')
    print_metrics(test_metrics_isotonic, 'Isotonic Regression (Test)')
    
    # 7. Compare uncalibrated baseline
    print("\n" + "="*60)
    print("Baseline (Uncalibrated Model)")
    print("="*60)
    
    # Use model_prob directly as "predictions"
    test_df_baseline = test_df.copy()
    test_df_baseline['p_market'] = test_df_baseline['american_odds'].apply(american_to_implied_prob)
    test_df_baseline['uncalibrated_edge'] = test_df_baseline['model_prob'] - test_df_baseline['p_market']
    
    baseline_bets = test_df_baseline[test_df_baseline['uncalibrated_edge'] > 0].copy()
    
    if len(baseline_bets) > 0:
        baseline_bets['profit'] = baseline_bets.apply(
            lambda row: row['american_odds'] / 100 if row['outcome'] == 1 else -1,
            axis=1
        )
        baseline_roi = (baseline_bets['profit'].sum() / len(baseline_bets)) * 100
        baseline_win_rate = baseline_bets['outcome'].mean()
    else:
        baseline_roi = 0
        baseline_win_rate = 0
    
    print(f"Total Bets:  {len(baseline_bets)}")
    print(f"Win Rate:    {baseline_win_rate:.1%}")
    print(f"ROI:         {baseline_roi:+.2f}%")
    print("="*60)
    
    # 8. Save models if requested
    if args.save_model:
        save_calibration_models(
            platt, isotonic, train_df,
            test_metrics_platt, test_metrics_isotonic,
            args.output_dir, args.min_odds, args.max_odds
        )
    
    print("\n✅ Calibration training complete!")
    print(f"\nRecommendation:")
    if test_metrics_isotonic['roi'] > test_metrics_platt['roi']:
        print(f"  Use Isotonic Regression (ROI: {test_metrics_isotonic['roi']:+.2f}%)")
    else:
        print(f"  Use Platt Scaling (ROI: {test_metrics_platt['roi']:+.2f}%)")


if __name__ == '__main__':
    main()
