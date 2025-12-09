#!/usr/bin/env python3
"""
Market-only baseline model (GUARANTEED LOOKAHEAD-FREE).

This model uses ONLY market information (spreads, moneylines) and trivial flags,
with NO KenPom ratings. It serves as a clean baseline that's guaranteed to be
free of rating-date issues.

Purpose:
    - Separate "KenPom lookahead" from "model logic" issues
    - Establish floor performance using market-implied probabilities
    - Validate that our edge calculation logic is sound

Features used:
    - close_spread (market expectation)
    - home_ml, away_ml (converted to implied probabilities)
    - home_favorite (boolean: is home team favored?)
    - spread_magnitude (abs value of spread)
    - NO KENPOM RATINGS

Usage:
    python3 ml/train_baseline_market_only.py
    python3 ml/train_baseline_market_only.py --merged-file data/merged/merged_odds_kenpom_full.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss, log_loss
import json


def american_to_prob(odds: float) -> float:
    """Convert American odds to implied probability"""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def build_market_features(df: pd.DataFrame) -> tuple:
    """
    Build features using ONLY market information (no KenPom).
    
    Args:
        df: Merged dataset with market odds
        
    Returns:
        (X, y_home_won, feature_names)
    """
    features = df.copy()
    
    # Market-implied probabilities
    features['home_implied_prob'] = features['home_ml'].apply(american_to_prob)
    features['away_implied_prob'] = features['away_ml'].apply(american_to_prob)
    
    # Market expectations
    features['home_favorite'] = (features['close_spread'] < 0).astype(int)
    features['spread_magnitude'] = features['close_spread'].abs()
    
    # Simple derived features
    features['prob_diff'] = features['home_implied_prob'] - features['away_implied_prob']
    features['vig'] = features['home_implied_prob'] + features['away_implied_prob'] - 1.0
    
    # Feature matrix
    feature_cols = [
        'close_spread',
        'home_implied_prob',
        'away_implied_prob',
        'home_favorite',
        'spread_magnitude',
        'prob_diff',
        'vig'
    ]
    
    X = features[feature_cols].copy()
    
    # Handle missing values (fill with median or 0)
    X = X.fillna(X.median())
    
    # Target: did home team win? (for ML models)
    # We'll calculate this if we have scores, otherwise just for structure
    y_home_won = None
    if 'home_score' in features.columns and 'away_score' in features.columns:
        y_home_won = (features['home_score'] > features['away_score']).astype(int)
    
    return X, y_home_won, feature_cols


def train_market_model(X_train: pd.DataFrame, y_train: pd.Series, 
                       model_type: str = 'gbm') -> object:
    """
    Train market-only model.
    
    Args:
        X_train: Training features (market only)
        y_train: Home team won (0/1)
        model_type: 'gbm' or 'logistic'
        
    Returns:
        Trained model
    """
    if model_type == 'gbm':
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )
    else:
        model = LogisticRegression(
            max_iter=1000,
            random_state=42
        )
    
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Evaluate model performance.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: True outcomes
        
    Returns:
        Dict with metrics
    """
    # Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    brier = brier_score_loss(y_test, y_prob)
    logloss = log_loss(y_test, y_prob)
    
    return {
        'accuracy': acc,
        'auc': auc,
        'brier_score': brier,
        'log_loss': logloss
    }


def calculate_ml_edge_pnl(test_df: pd.DataFrame, model_probs: np.ndarray, 
                          edge_thresholds: list, stake: float = 100) -> dict:
    """
    Calculate P&L for moneyline betting at various edge thresholds.
    
    Args:
        test_df: Test dataset with market odds and outcomes
        model_probs: Model's predicted home win probabilities
        edge_thresholds: List of edge thresholds to test
        stake: Bet size
        
    Returns:
        Dict with P&L for each threshold
    """
    # Add model probabilities to test data
    test_df = test_df.copy()
    test_df['model_home_prob'] = model_probs
    test_df['model_away_prob'] = 1 - model_probs
    
    # Calculate edges
    test_df['home_implied_prob'] = test_df['home_ml'].apply(american_to_prob)
    test_df['away_implied_prob'] = test_df['away_ml'].apply(american_to_prob)
    test_df['home_ml_edge'] = test_df['model_home_prob'] - test_df['home_implied_prob']
    test_df['away_ml_edge'] = test_df['model_away_prob'] - test_df['away_implied_prob']
    
    results = {}
    
    for threshold in edge_thresholds:
        # Find bets
        home_bets = test_df[test_df['home_ml_edge'] >= threshold].copy()
        away_bets = test_df[test_df['away_ml_edge'] >= threshold].copy()
        
        total_profit = 0
        total_wins = 0
        total_bets = 0
        
        # Home ML bets
        for _, bet in home_bets.iterrows():
            total_bets += 1
            if bet['home_won'] == 1:
                # Win
                if bet['home_ml'] < 0:
                    profit = stake * (100 / abs(bet['home_ml']))
                else:
                    profit = stake * (bet['home_ml'] / 100)
                total_profit += profit
                total_wins += 1
            else:
                # Loss
                total_profit -= stake
        
        # Away ML bets
        for _, bet in away_bets.iterrows():
            total_bets += 1
            if bet['home_won'] == 0:
                # Win
                if bet['away_ml'] < 0:
                    profit = stake * (100 / abs(bet['away_ml']))
                else:
                    profit = stake * (bet['away_ml'] / 100)
                total_profit += profit
                total_wins += 1
            else:
                # Loss
                total_profit -= stake
        
        roi = (total_profit / (total_bets * stake) * 100) if total_bets > 0 else 0
        
        results[threshold] = {
            'bets': total_bets,
            'wins': total_wins,
            'win_rate': (total_wins / total_bets * 100) if total_bets > 0 else 0,
            'profit': total_profit,
            'roi': roi
        }
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Train market-only baseline model")
    parser.add_argument('--merged-file', type=Path,
                       default=Path('data/merged/merged_odds_kenpom_full.csv'))
    parser.add_argument('--results-file', type=Path,
                       default=Path('data/walkforward_results_with_scores.csv'),
                       help='File with actual game results for evaluation')
    parser.add_argument('--model-type', choices=['gbm', 'logistic'], default='gbm')
    parser.add_argument('--train-cutoff', type=str, default='2024-02-01',
                       help='Date to split train/test (YYYY-MM-DD)')
    parser.add_argument('--stake', type=float, default=100.0)
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("MARKET-ONLY BASELINE MODEL (LOOKAHEAD-FREE)")
    print("=" * 80)
    
    # Load merged data
    print(f"\n📂 Loading merged data: {args.merged_file}")
    df = pd.read_csv(args.merged_file)
    df['date'] = pd.to_datetime(df['date'])
    print(f"   Loaded {len(df):,} games")
    print(f"   Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    
    # Load results for evaluation
    print(f"\n📂 Loading game results: {args.results_file}")
    results_df = pd.read_csv(args.results_file)
    results_df['date'] = pd.to_datetime(results_df['date'])
    
    # Match results to merged data
    # Merge on date + teams
    merged_with_results = df.merge(
        results_df[['date', 'home_team', 'away_team', 'home_score', 'away_score', 'home_won']],
        on=['date', 'home_team', 'away_team'],
        how='inner'
    )
    
    print(f"   Matched {len(merged_with_results):,} games with results")
    
    if len(merged_with_results) == 0:
        print("❌ No games matched! Check that team names align between files.")
        return
    
    # Build market-only features
    print(f"\n🔧 Building market-only features...")
    X, y, feature_cols = build_market_features(merged_with_results)
    
    print(f"   Features: {', '.join(feature_cols)}")
    print(f"   ✅ NO KENPOM RATINGS - purely market-based")
    
    # Time-based split
    cutoff_date = pd.to_datetime(args.train_cutoff)
    train_mask = merged_with_results['date'] < cutoff_date
    test_mask = merged_with_results['date'] >= cutoff_date
    
    X_train = X[train_mask]
    X_test = X[test_mask]
    y_train = y[train_mask]
    y_test = y[test_mask]
    
    train_df = merged_with_results[train_mask].copy()
    test_df = merged_with_results[test_mask].copy()
    
    print(f"\n📊 Train/Test Split (cutoff: {cutoff_date.date()}):")
    print(f"   Training: {len(X_train):,} games ({train_df['date'].min().date()} → {train_df['date'].max().date()})")
    print(f"   Test: {len(X_test):,} games ({test_df['date'].min().date()} → {test_df['date'].max().date()})")
    
    # Train model
    print(f"\n🎯 Training {args.model_type.upper()} model...")
    model = train_market_model(X_train, y_train, model_type=args.model_type)
    
    # Evaluate
    print(f"\n📈 Model Performance (Test Set):")
    metrics = evaluate_model(model, X_test, y_test)
    
    print(f"   Accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"   AUC: {metrics['auc']:.4f}")
    print(f"   Brier Score: {metrics['brier_score']:.4f}")
    print(f"   Log Loss: {metrics['log_loss']:.4f}")
    
    # Feature importance (if GBM)
    if args.model_type == 'gbm':
        print(f"\n📊 Feature Importance:")
        importances = model.feature_importances_
        for feat, imp in sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True):
            print(f"   {feat:25s}: {imp:.4f}")
    
    # Calculate ML betting P&L
    print(f"\n💰 Moneyline Betting P&L (Test Set):")
    test_probs = model.predict_proba(X_test)[:, 1]
    
    edge_thresholds = [0.03, 0.05, 0.07, 0.10]
    pnl_results = calculate_ml_edge_pnl(test_df, test_probs, edge_thresholds, args.stake)
    
    for threshold, result in pnl_results.items():
        print(f"\n   Edge ≥ {threshold*100:.0f}%:")
        print(f"      Bets: {result['bets']}")
        print(f"      Wins: {result['wins']} ({result['win_rate']:.1f}%)")
        print(f"      Profit: ${result['profit']:+,.2f}")
        print(f"      ROI: {result['roi']:+.2f}%")
    
    # Save model and results
    output_dir = Path('models/baseline')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import joblib
    model_path = output_dir / f'market_only_{args.model_type}.pkl'
    joblib.dump(model, model_path)
    
    metadata = {
        'model_type': args.model_type,
        'features': feature_cols,
        'train_cutoff': args.train_cutoff,
        'train_games': len(X_train),
        'test_games': len(X_test),
        'metrics': metrics,
        'ml_pnl': {str(k): v for k, v in pnl_results.items()},
        'created': datetime.now().isoformat()
    }
    
    with open(output_dir / f'market_only_{args.model_type}_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Model saved to: {model_path}")
    
    print(f"\n" + "=" * 80)
    print("✅ BASELINE MODEL COMPLETE")
    print("=" * 80)
    print(f"\nKey Takeaway:")
    print(f"   This model uses ZERO KenPom ratings → guaranteed lookahead-free")
    print(f"   Performance represents floor using only market information")
    print(f"   Best ROI: {max([r['roi'] for r in pnl_results.values()]):+.2f}% at edge threshold {max(pnl_results.items(), key=lambda x: x[1]['roi'])[0]*100:.0f}%")


if __name__ == '__main__':
    main()
