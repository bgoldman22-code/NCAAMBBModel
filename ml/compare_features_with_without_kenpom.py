#!/usr/bin/env python3
"""
Compare ML model performance with and without KenPom features.

This script trains two models on the same data:
1. Full model: Market features + KenPom ratings
2. Baseline model: Market features only (no KenPom)

Purpose: Quantify how much value KenPom features add, even with lookahead bias.
Once dated ratings are available, re-run to measure true KenPom contribution.

Usage:
    python3 ml/compare_features_with_without_kenpom.py --train-cutoff 2024-02-01
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import argparse

def american_to_prob(odds):
    """Convert American odds to implied probability."""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return (-odds) / (-odds + 100)
    else:
        return 100 / (odds + 100)

def load_data():
    """Load walkforward results with odds, KenPom, and game outcomes."""
    data_path = Path(__file__).parent.parent / 'data' / 'walkforward_results_with_scores.csv'
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total games loaded: {len(df)}")
    return df

def prepare_features(df, include_kenpom=True):
    """
    Prepare feature set with optional KenPom inclusion.
    
    Args:
        df: Raw dataframe
        include_kenpom: If True, include KenPom features; if False, market only
    
    Returns:
        X (features), y (target), feature_names
    """
    # Engineer market features
    df_features = df.copy()
    
    # Implied probabilities from moneylines
    df_features['home_implied_prob'] = df_features['home_ml'].apply(american_to_prob)
    df_features['away_implied_prob'] = df_features['away_ml'].apply(american_to_prob)
    
    # Market-derived features
    df_features['home_favorite'] = (df_features['close_spread'] < 0).astype(int)
    df_features['spread_magnitude'] = df_features['close_spread'].abs()
    
    # Probability differences and vig
    df_features['prob_diff'] = df_features['home_implied_prob'] - df_features['away_implied_prob']
    df_features['vig'] = df_features['home_implied_prob'] + df_features['away_implied_prob'] - 1.0
    
    # Market features (always included)
    market_features = [
        'close_spread',
        'home_implied_prob',
        'away_implied_prob',
        'home_favorite',
        'spread_magnitude',
        'prob_diff',
        'vig'
    ]
    
    # KenPom features (optional)
    kenpom_features = [
        'AdjEM_home', 'AdjOE_home', 'AdjDE_home', 'AdjTempo_home',
        'Tempo_home', 'Luck_home', 'SOS_home', 'SOSO_home', 'SOSD_home',
        'RankAdjEM_home', 'RankAdjOE_home', 'RankAdjDE_home', 'RankAdjTempo_home',
        'AdjEM_away', 'AdjOE_away', 'AdjDE_away', 'AdjTempo_away',
        'Tempo_away', 'Luck_away', 'SOS_away', 'SOSO_away', 'SOSD_away',
        'RankAdjEM_away', 'RankAdjOE_away', 'RankAdjDE_away', 'RankAdjTempo_away',
        'tempo_diff'
    ]
    
    # Compute em_diff, oe_diff, etc. if KenPom columns available
    if 'AdjEM_home' in df_features.columns and 'AdjEM_away' in df_features.columns:
        df_features['em_diff'] = df_features['AdjEM_home'] - df_features['AdjEM_away']
        df_features['oe_diff'] = df_features['AdjOE_home'] - df_features['AdjOE_away']
        df_features['de_diff'] = df_features['AdjDE_away'] - df_features['AdjDE_home']  # Lower DE is better
        df_features['sos_diff'] = df_features['SOS_home'] - df_features['SOS_away']
        df_features['luck_diff'] = df_features['Luck_home'] - df_features['Luck_away']
        
        kenpom_features.extend(['em_diff', 'oe_diff', 'de_diff', 'sos_diff', 'luck_diff'])
    
    # Select features based on include_kenpom flag
    if include_kenpom:
        feature_cols = market_features + kenpom_features
        model_name = "Full (Market + KenPom)"
    else:
        feature_cols = market_features
        model_name = "Baseline (Market Only)"
    
    # Filter to available columns
    available_features = [col for col in feature_cols if col in df_features.columns]
    missing_features = set(feature_cols) - set(available_features)
    
    if missing_features:
        print(f"\n⚠️  Missing features for {model_name}: {missing_features}")
    
    # Create feature matrix
    X = df_features[available_features].copy()
    y = df_features['home_covered'].astype(int)
    
    # Fill missing values with median (should be minimal)
    X = X.fillna(X.median())
    
    print(f"\n{model_name} Features:")
    print(f"  Total features: {len(available_features)}")
    print(f"  Market features: {len([f for f in available_features if f in market_features])}")
    if include_kenpom:
        print(f"  KenPom features: {len([f for f in available_features if f in kenpom_features])}")
    print(f"  Samples: {len(X)}")
    
    return X, y, available_features, model_name

def train_and_evaluate(X_train, X_test, y_train, y_test, model_name):
    """Train GBM model and evaluate on test set."""
    print(f"\n{'='*60}")
    print(f"Training: {model_name}")
    print(f"{'='*60}")
    
    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    
    print(f"Training on {len(X_train)} samples...")
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    print(f"\n{'='*60}")
    print(f"Test Performance: {model_name}")
    print(f"{'='*60}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"AUC: {auc:.3f}")
    print(f"Test samples: {len(y_test)}")
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=['Away Covers', 'Home Covers'],
                                digits=3))
    
    # Feature importance (top 10)
    if hasattr(model, 'feature_importances_'):
        importances = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Feature Importances:")
        print(importances.head(10).to_string(index=False))
    
    # Edge-based ROI analysis
    print(f"\n{'='*60}")
    print(f"ROI Analysis: {model_name}")
    print(f"{'='*60}")
    
    # Calculate model edge (|predicted prob - 0.5|)
    model_edge = np.abs(y_proba - 0.5)
    
    # Test different edge thresholds
    thresholds = [0.00, 0.03, 0.05, 0.07, 0.10, 0.12, 0.15]
    
    print(f"\n{'Threshold':<12} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'P&L ($100)':<12}")
    print("-" * 60)
    
    best_roi = -999
    best_threshold = 0
    
    for threshold in thresholds:
        # Filter to bets meeting edge threshold
        bet_mask = model_edge >= threshold
        
        if bet_mask.sum() == 0:
            continue
        
        # Evaluate bets
        bet_correct = (y_pred[bet_mask] == y_test[bet_mask]).sum()
        bet_count = bet_mask.sum()
        win_rate = bet_correct / bet_count
        
        # Calculate P&L (assuming -110 odds)
        wins = bet_correct
        losses = bet_count - bet_correct
        pnl = (wins * 100 * (100/110)) - (losses * 100)
        roi = (pnl / (bet_count * 100)) * 100
        
        print(f"{threshold:.2f}          {bet_count:<8} {win_rate*100:<7.1f}% {roi:>8.1f}%  ${pnl:>10,.0f}")
        
        if roi > best_roi:
            best_roi = roi
            best_threshold = threshold
    
    print(f"\nBest threshold: {best_threshold:.2f} (ROI: {best_roi:+.1f}%)")
    
    return {
        'model': model,
        'accuracy': accuracy,
        'auc': auc,
        'best_roi': best_roi,
        'best_threshold': best_threshold,
        'y_proba': y_proba
    }

def main():
    parser = argparse.ArgumentParser(description='Compare ML models with/without KenPom features')
    parser.add_argument('--train-cutoff', type=str, default='2024-02-01',
                       help='Date cutoff for train/test split (YYYY-MM-DD)')
    args = parser.parse_args()
    
    print("="*80)
    print("Feature Comparison: Market-Only vs Market+KenPom")
    print("="*80)
    print(f"Train cutoff: {args.train_cutoff}")
    
    # Load data
    df = load_data()
    
    # Convert game_day to datetime
    df['game_day'] = pd.to_datetime(df['game_day'])
    train_cutoff = pd.to_datetime(args.train_cutoff)
    
    # Filter to games with results (home_covered must exist)
    matched_df = df[df['home_covered'].notna()].copy()
    print(f"Games with results: {len(matched_df)}")
    
    # Train/test split by date
    train_df = matched_df[matched_df['game_day'] < train_cutoff]
    test_df = matched_df[matched_df['game_day'] >= train_cutoff]
    
    print(f"\nTrain games: {len(train_df)} (before {args.train_cutoff})")
    print(f"Test games: {len(test_df)} (on/after {args.train_cutoff})")
    
    # === Model 1: Market Only ===
    X_market_train, y_train, market_features, market_name = prepare_features(train_df, include_kenpom=False)
    X_market_test, y_test, _, _ = prepare_features(test_df, include_kenpom=False)
    
    market_results = train_and_evaluate(X_market_train, X_market_test, y_train, y_test, market_name)
    
    # === Model 2: Market + KenPom ===
    X_full_train, y_train, full_features, full_name = prepare_features(train_df, include_kenpom=True)
    X_full_test, y_test, _, _ = prepare_features(test_df, include_kenpom=True)
    
    full_results = train_and_evaluate(X_full_train, X_full_test, y_train, y_test, full_name)
    
    # === Final Comparison ===
    print("\n" + "="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    
    comparison = pd.DataFrame({
        'Model': [market_name, full_name],
        'Features': [len(market_features), len(full_features)],
        'Accuracy': [market_results['accuracy'], full_results['accuracy']],
        'AUC': [market_results['auc'], full_results['auc']],
        'Best ROI': [market_results['best_roi'], full_results['best_roi']],
        'Best Threshold': [market_results['best_threshold'], full_results['best_threshold']]
    })
    
    print("\n" + comparison.to_string(index=False))
    
    # Calculate improvement
    acc_improvement = (full_results['accuracy'] - market_results['accuracy']) * 100
    auc_improvement = full_results['auc'] - market_results['auc']
    roi_improvement = full_results['best_roi'] - market_results['best_roi']
    
    print(f"\n{'='*80}")
    print("KenPom Features Value-Add:")
    print(f"{'='*80}")
    print(f"Accuracy improvement: {acc_improvement:+.1f} percentage points")
    print(f"AUC improvement: {auc_improvement:+.3f}")
    print(f"ROI improvement: {roi_improvement:+.1f}%")
    
    if roi_improvement > 0:
        print(f"\n✅ KenPom features add value (+{roi_improvement:.1f}% ROI)")
        print(f"\n⚠️  IMPORTANT: This measurement includes LOOKAHEAD BIAS!")
        print(f"   Current KenPom ratings are season-end snapshots (all games use final ratings).")
        print(f"   True value-add will likely be LOWER once dated ratings are implemented.")
        print(f"   This {roi_improvement:+.1f}% represents an UPPER BOUND, not real-world expectation.")
    else:
        print(f"\n⚠️  KenPom features reduce performance ({roi_improvement:.1f}% ROI)")
        print(f"   This may indicate overfitting or that current implementation isn't optimal.")
        print(f"   Could also mean market already prices in KenPom information efficiently.")
    
    print("\n" + "="*80)
    print("Next Steps:")
    print("="*80)
    print("1. Acquire dated KenPom ratings (see TIME_AWARE_IMPLEMENTATION.md)")
    print("2. Re-run this script with dated ratings")
    print("3. Measure true KenPom value-add without lookahead bias")
    print("4. If still positive, optimize thresholds on clean data")

if __name__ == '__main__':
    main()
