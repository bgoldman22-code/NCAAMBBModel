"""
Train and evaluate a specific model variant (A, B, or C).

This script:
1. Loads data and builds features for the specified variant
2. Performs time-aware train/test split
3. Trains a classification model
4. Evaluates metrics (Accuracy, AUC, Brier, calibration)
5. Exports predictions with edges to CSV

Usage:
    python3 ml/experiments_ncaabb/train_eval_model_variant.py --variant A --train-cutoff 2024-02-01
"""

import argparse
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import sys
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss
try:
    from sklearn.calibration import calibration_curve
except ImportError:
    # Fallback for older sklearn versions
    from sklearn.metrics import calibration_curve
import json
from datetime import datetime
from typing import Dict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config_models import get_variant_config, get_feature_list, print_variant_summary
from features_inseason_stats import build_inseason_stats

def american_to_prob(odds):
    """Convert American odds to implied probability."""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return (-odds) / (-odds + 100)
    else:
        return 100 / (odds + 100)

def build_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build market-derived features."""
    df = df.copy()
    
    # Implied probabilities
    df['home_implied_prob'] = df['home_ml'].apply(american_to_prob)
    df['away_implied_prob'] = df['away_ml'].apply(american_to_prob)
    
    # Market features
    df['home_favorite'] = (df['close_spread'] < 0).astype(int)
    df['spread_magnitude'] = df['close_spread'].abs()
    df['prob_diff'] = df['home_implied_prob'] - df['away_implied_prob']
    df['vig'] = df['home_implied_prob'] + df['away_implied_prob'] - 1.0
    
    return df

def build_preseason_kenpom_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build preseason KenPom features (treat season-end ratings as static priors)."""
    df = df.copy()
    
    # Compute diffs if base columns exist
    if 'AdjEM_home' in df.columns and 'AdjEM_away' in df.columns:
        df['AdjEM_diff'] = df['AdjEM_home'] - df['AdjEM_away']
        df['AdjOE_diff'] = df['AdjOE_home'] - df['AdjOE_away']
        df['AdjDE_diff'] = df['AdjDE_away'] - df['AdjDE_home']  # Lower DE is better
        df['AdjTempo_diff'] = df['AdjTempo_home'] - df['AdjTempo_away']
        df['SOS_diff'] = df['SOS_home'] - df['SOS_away']
        df['Luck_diff'] = df['Luck_home'] - df['Luck_away']
    
    return df

def build_time_decay_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build time-based features for preseason prior decay."""
    df = df.copy()
    
    # Ensure date is datetime
    if 'date' not in df.columns:
        df['date'] = pd.to_datetime(df['game_day'])
    else:
        df['date'] = pd.to_datetime(df['date'])
    
    # Season start (approximate: Nov 6)
    df['season_start'] = pd.to_datetime(df['season'].astype(str).str[:4] + '-11-06')
    df['days_into_season'] = (df['date'] - df['season_start']).dt.days
    
    # Games played (if available from in-season stats)
    if 'games_played_home' not in df.columns:
        # Estimate: assign sequential game numbers per team
        df['games_played_home'] = df.groupby('home_team').cumcount()
        df['games_played_away'] = df.groupby('away_team').cumcount()
    
    # Season progress (0 at start, 1 at end)
    # Assume ~140 days season (Nov 6 to Mar 25)
    df['season_progress'] = df['days_into_season'] / 140.0
    df['season_progress'] = df['season_progress'].clip(0, 1)
    
    return df

def prepare_features_for_variant(
    variant: str,
    merged_df: pd.DataFrame,
    inseason_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Prepare features for a specific variant.
    
    Args:
        variant: 'A', 'B', or 'C'
        merged_df: Merged odds + KenPom data
        inseason_df: Optional dataframe with in-season stats
    
    Returns:
        DataFrame with all features for this variant
    """
    config = get_variant_config(variant)
    print(f"\n{'='*60}")
    print(f"Preparing Features for Variant {variant}")
    print(f"{'='*60}")
    
    df = merged_df.copy()
    
    # Build market features (all variants use these)
    df = build_market_features(df)
    print(f"✅ Market features built")
    
    # Build KenPom features if needed
    if config['use_kenpom']:
        df = build_preseason_kenpom_features(df)
        print(f"✅ Preseason KenPom features built")
    
    # Build time decay features if needed
    if config['time_decay']:
        df = build_time_decay_features(df)
        print(f"✅ Time decay features built")
    
    # Merge in-season stats if needed
    if config['use_inseason_stats'] and inseason_df is not None:
        print(f"✅ Merging in-season stats...")
        # Merge on date + teams
        df['date'] = pd.to_datetime(df.get('date', df['game_day']))
        inseason_df['date'] = pd.to_datetime(inseason_df['date'])
        
        # Get in-season columns
        inseason_cols = [col for col in inseason_df.columns if '_L' in col or col in ['date', 'home_team', 'away_team']]
        df = df.merge(
            inseason_df[inseason_cols],
            on=['date', 'home_team', 'away_team'],
            how='left'
        )
        print(f"   In-season features merged: {len([c for c in df.columns if '_L' in c])}")
    
    return df

def train_and_evaluate_variant(
    variant: str,
    train_cutoff: str,
    data_dir: Path
) -> Dict:
    """
    Train and evaluate a model variant.
    
    Returns dictionary with metrics and paths to outputs.
    """
    print(f"\n{'='*80}")
    print(f"TRAINING AND EVALUATING VARIANT {variant}")
    print(f"{'='*80}")
    
    config = get_variant_config(variant)
    print_variant_summary(variant)
    
    # Load data
    print(f"\n📂 Loading data...")
    merged_file = data_dir / 'walkforward_results_with_scores.csv'
    merged_df = pd.read_csv(merged_file)
    print(f"   Loaded {len(merged_df)} games from {merged_file.name}")
    
    # Load/build in-season stats if needed
    inseason_df = None
    if config['use_inseason_stats']:
        inseason_file = data_dir / 'merged' / 'game_results_with_inseason_stats.csv'
        if inseason_file.exists():
            print(f"   Loading pre-computed in-season stats...")
            inseason_df = pd.read_csv(inseason_file)
        else:
            print(f"   Building in-season stats (this may take a minute)...")
            inseason_df = build_inseason_stats(merged_df.copy())
            inseason_df.to_csv(inseason_file, index=False)
            print(f"   Saved in-season stats to: {inseason_file}")
    
    # Prepare features
    df = prepare_features_for_variant(variant, merged_df, inseason_df)
    
    # Get feature list for this variant
    feature_list = get_feature_list(variant)
    
    # Filter to available features
    available_features = [f for f in feature_list if f in df.columns]
    missing_features = set(feature_list) - set(available_features)
    
    if missing_features:
        print(f"\n⚠️  Missing features: {len(missing_features)}")
        print(f"   {list(missing_features)[:10]}...")
    
    print(f"\n📊 Feature Summary:")
    print(f"   Expected features: {len(feature_list)}")
    print(f"   Available features: {len(available_features)}")
    print(f"   Missing: {len(missing_features)}")
    
    # Filter to games with outcomes
    df = df[df['home_won'].notna()].copy()
    print(f"\n   Games with outcomes: {len(df)}")
    
    # Create target
    y = df['home_won'].astype(int)
    
    # Create feature matrix
    X = df[available_features].copy()
    
    # Fill missing values with median
    X = X.fillna(X.median())
    
    # Handle any remaining NaNs
    X = X.fillna(0)
    
    # Time-aware split
    df['date'] = pd.to_datetime(df.get('date', df['game_day']))
    train_cutoff_date = pd.to_datetime(train_cutoff)
    
    train_mask = df['date'] < train_cutoff_date
    test_mask = df['date'] >= train_cutoff_date
    
    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]
    
    print(f"\n📅 Train/Test Split:")
    print(f"   Train cutoff: {train_cutoff}")
    print(f"   Train games: {len(X_train)} ({train_mask.sum()})")
    print(f"   Test games: {len(X_test)} ({test_mask.sum()})")
    print(f"   Train date range: {df[train_mask]['date'].min().date()} → {df[train_mask]['date'].max().date()}")
    print(f"   Test date range: {df[test_mask]['date'].min().date()} → {df[test_mask]['date'].max().date()}")
    
    # Train model
    print(f"\n🔧 Training {config['model_type'].upper()} model...")
    model = GradientBoostingClassifier(**config['model_params'])
    model.fit(X_train, y_train)
    print(f"   ✅ Model trained")
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_proba_train = model.predict_proba(X_train)[:, 1]
    
    y_pred_test = model.predict(X_test)
    y_proba_test = model.predict_proba(X_test)[:, 1]
    
    # Evaluate
    print(f"\n{'='*60}")
    print(f"EVALUATION METRICS - Variant {variant}")
    print(f"{'='*60}")
    
    # Training metrics
    train_acc = accuracy_score(y_train, y_pred_train)
    train_auc = roc_auc_score(y_train, y_proba_train)
    train_brier = brier_score_loss(y_train, y_proba_train)
    
    print(f"\nTraining Set:")
    print(f"  Accuracy: {train_acc:.4f}")
    print(f"  AUC: {train_auc:.4f}")
    print(f"  Brier Score: {train_brier:.4f}")
    
    # Test metrics
    test_acc = accuracy_score(y_test, y_pred_test)
    test_auc = roc_auc_score(y_test, y_proba_test)
    test_brier = brier_score_loss(y_test, y_proba_test)
    
    print(f"\nTest Set:")
    print(f"  Accuracy: {test_acc:.4f}")
    print(f"  AUC: {test_auc:.4f}")
    print(f"  Brier Score: {test_brier:.4f}")
    
    # Calibration
    print(f"\nCalibration (Test Set):")
    prob_true, prob_pred = calibration_curve(y_test, y_proba_test, n_bins=10, strategy='uniform')
    
    print(f"{'Predicted':<12} {'Actual':<12} {'Count':<8} {'Error':<8}")
    print("-" * 50)
    for i in range(len(prob_pred)):
        bin_mask = (y_proba_test >= i/10) & (y_proba_test < (i+1)/10)
        count = bin_mask.sum()
        error = abs(prob_pred[i] - prob_true[i])
        print(f"{prob_pred[i]:<12.3f} {prob_true[i]:<12.3f} {count:<8} {error:<8.3f}")
    
    # Feature importance
    if hasattr(model, 'feature_importances_'):
        print(f"\nTop 10 Feature Importances:")
        importances = pd.DataFrame({
            'feature': available_features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(importances.head(10).to_string(index=False))
    
    # Export predictions with edges
    print(f"\n💾 Exporting predictions...")
    
    test_df = df[test_mask].copy()
    test_df['model_prob_home'] = y_proba_test
    test_df['model_prob_away'] = 1 - y_proba_test
    test_df['edge_home'] = test_df['model_prob_home'] - test_df['home_implied_prob']
    test_df['edge_away'] = test_df['model_prob_away'] - test_df['away_implied_prob']
    
    # Save edges
    edges_dir = data_dir / 'edges'
    edges_dir.mkdir(parents=True, exist_ok=True)
    edges_file = edges_dir / f'edges_ncaabb_variant_{variant}.csv'
    
    export_cols = [
        'date', 'home_team', 'away_team',
        'home_ml', 'away_ml', 'home_implied_prob', 'away_implied_prob',
        'model_prob_home', 'model_prob_away',
        'edge_home', 'edge_away',
        'home_won', 'home_score', 'away_score'
    ]
    test_df[export_cols].to_csv(edges_file, index=False)
    print(f"   Saved edges to: {edges_file}")
    
    # Save metrics
    metrics = {
        'variant': variant,
        'variant_name': config['name'],
        'train_cutoff': train_cutoff,
        'train_games': int(len(X_train)),
        'test_games': int(len(X_test)),
        'features_available': len(available_features),
        'features_missing': len(missing_features),
        'train_accuracy': float(train_acc),
        'train_auc': float(train_auc),
        'train_brier': float(train_brier),
        'test_accuracy': float(test_acc),
        'test_auc': float(test_auc),
        'test_brier': float(test_brier),
        'calibration': {
            'prob_pred': prob_pred.tolist(),
            'prob_true': prob_true.tolist()
        },
        'timestamp': datetime.now().isoformat()
    }
    
    metrics_file = edges_dir / f'metrics_variant_{variant}.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   Saved metrics to: {metrics_file}")
    
    # Save the trained model
    model_dir = data_dir.parent / 'models' / f'variant_{variant.lower()}_production'
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_file = model_dir / f'variant_{variant.lower()}_model.pkl'
    joblib.dump(model, model_file)
    print(f"   Saved model to: {model_file}")
    
    # Save feature columns
    features_file = model_dir / f'variant_{variant.lower()}_features.json'
    with open(features_file, 'w') as f:
        json.dump({'feature_cols': available_features}, f, indent=2)
    print(f"   Saved features to: {features_file}")
    
    # Save metadata
    metadata = {
        'model_name': f'Variant {variant}',
        'variant': variant,
        'variant_name': config['name'],
        'training_date': datetime.now().strftime('%Y-%m-%d'),
        'performance': {
            'test_auc': float(test_auc),
            'test_accuracy': float(test_acc),
            'test_brier': float(test_brier),
            'approved_roi': 0.253 if variant == 'B' else None,
            'approved_edge_threshold': 0.15 if variant == 'B' else None,
        },
        'n_features': len(available_features),
        'feature_groups': config['feature_groups'],
        'model_type': config['model_type'],
        'notes': f'Trained on {len(X_train)} games, tested on {len(X_test)} games'
    }
    
    metadata_file = model_dir / f'variant_{variant.lower()}_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   Saved metadata to: {metadata_file}")
    
    print(f"\n✅ Variant {variant} training complete!")
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description='Train and evaluate a model variant')
    parser.add_argument('--variant', type=str, required=True, choices=['A', 'B', 'C'],
                       help='Model variant to train (A, B, or C)')
    parser.add_argument('--train-cutoff', type=str, default='2024-02-01',
                       help='Date cutoff for train/test split (YYYY-MM-DD)')
    args = parser.parse_args()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    metrics = train_and_evaluate_variant(
        variant=args.variant,
        train_cutoff=args.train_cutoff,
        data_dir=data_dir
    )
    
    print(f"\n{'='*80}")
    print(f"✅ TRAINING COMPLETE - Variant {args.variant}")
    print(f"{'='*80}")
    print(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
    print(f"Test AUC: {metrics['test_auc']:.4f}")
    print(f"Test Brier: {metrics['test_brier']:.4f}")

if __name__ == '__main__':
    main()
