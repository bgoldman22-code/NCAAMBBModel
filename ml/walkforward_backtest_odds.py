#!/usr/bin/env python3
"""
Walk-forward backtest using Odds + KenPom merged data.

Zero data leakage: trains on past, tests on future, never uses future data in training.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple
import pandas as pd
import numpy as np

from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, accuracy_score


def american_to_prob(odds: float) -> float:
    """Convert American odds to implied probability"""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def load_data(merged_file: Path) -> pd.DataFrame:
    """
    Load merged odds + KenPom data.
    
    Args:
        merged_file: Path to merged CSV
        
    Returns:
        DataFrame with complete data
    """
    print(f"\n📂 Loading data from {merged_file}...")
    
    df = pd.read_csv(merged_file)
    
    # Parse date
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Add implied probabilities
    df['home_implied_prob'] = df['home_ml'].apply(american_to_prob)
    df['away_implied_prob'] = df['away_ml'].apply(american_to_prob)
    
    print(f"✅ Loaded {len(df):,} games")
    print(f"   Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"   Unique teams: {pd.concat([df['home_team'], df['away_team']]).nunique()}")
    
    return df


def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Build feature matrix for prediction.
    
    Features include:
    - Team efficiency ratings (home and away)
    - Matchup metrics
    - Tempo differences
    - Strength of schedule
    
    Args:
        df: DataFrame with KenPom metrics
        
    Returns:
        (X, y_spread, y_home_win)
    """
    feature_cols = [
        # Home team metrics
        'AdjEM_home', 'AdjOE_home', 'AdjDE_home', 'AdjTempo_home',
        # Away team metrics
        'AdjEM_away', 'AdjOE_away', 'AdjDE_away', 'AdjTempo_away',
        # Derived features
        'efficiency_diff', 'tempo_diff',
        'offensive_matchup_home', 'defensive_matchup_home'
    ]
    
    X = df[feature_cols].copy()
    
    # For now, we don't have actual results, so we'll use the spread as proxy
    # In a real backtest, you'd need actual game results
    # For this demo, we'll create synthetic targets based on spread
    y_spread = df['close_spread']  # This is what Vegas thinks
    y_home_win = (df['close_spread'] < 0).astype(int)  # If spread negative, home favored
    
    return X, y_spread, y_home_win


def split_train_test(
    df: pd.DataFrame,
    test_start: datetime,
    test_end: datetime
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split into train (before test_start) and test (between test_start and test_end)"""
    train = df[df['date'] < test_start].copy()
    test = df[(df['date'] >= test_start) & (df['date'] <= test_end)].copy()
    return train, test


def train_models(train_df: pd.DataFrame) -> Tuple:
    """
    Train spread and moneyline models.
    
    Args:
        train_df: Training data
        
    Returns:
        (spread_model, ml_model)
    """
    X_train, y_spread, y_win = build_features(train_df)
    
    # Train spread model (fewer estimators for speed)
    spread_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    spread_model.fit(X_train, y_spread)
    
    # Train ML model (fewer estimators for speed)
    ml_model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    ml_model.fit(X_train, y_win)
    
    return spread_model, ml_model


def generate_predictions(
    test_df: pd.DataFrame,
    spread_model,
    ml_model
) -> pd.DataFrame:
    """Generate predictions and calculate edges"""
    X_test, _, _ = build_features(test_df)
    
    test_df = test_df.copy()
    test_df['model_spread'] = spread_model.predict(X_test)
    test_df['model_home_prob'] = ml_model.predict_proba(X_test)[:, 1]
    test_df['model_away_prob'] = 1 - test_df['model_home_prob']
    
    # Calculate edges
    test_df['edge_spread'] = test_df['model_spread'] - test_df['close_spread']
    test_df['home_ml_edge'] = test_df['model_home_prob'] - test_df['home_implied_prob']
    test_df['away_ml_edge'] = test_df['model_away_prob'] - test_df['away_implied_prob']
    
    return test_df


def walkforward_backtest(
    df: pd.DataFrame,
    initial_train_months: int = 2,
    test_window_days: int = 30,
    min_edge_spread: float = 2.0,
    min_edge_ml: float = 0.07
) -> dict:
    """
    Perform walk-forward backtest.
    
    Note: This backtest doesn't have actual game results, so we can't calculate
    real P&L. This demonstrates the PROCESS of walk-forward testing with zero
    data leakage. To calculate actual performance, you'd need actual game results.
    
    Args:
        df: Full dataset
        initial_train_months: Months of initial training data
        test_window_days: Days in each test window
        min_edge_spread: Minimum spread edge to bet
        min_edge_ml: Minimum ML edge to bet
        
    Returns:
        Dict with backtest results
    """
    print("\n" + "="*80)
    print("WALK-FORWARD BACKTEST (ZERO DATA LEAKAGE)")
    print("="*80)
    
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    initial_train_end = min_date + timedelta(days=initial_train_months * 30)
    
    print(f"\nDataset:")
    print(f"   Total games: {len(df):,}")
    print(f"   Date range: {min_date.date()} → {max_date.date()}")
    print(f"   Duration: {(max_date - min_date).days} days")
    
    print(f"\nWalk-forward setup:")
    print(f"   Initial training: {initial_train_months} months")
    print(f"   Test window: {test_window_days} days")
    print(f"   Min edge spread: {min_edge_spread}")
    print(f"   Min edge ML: {min_edge_ml}")
    
    all_periods = []
    current_test_start = initial_train_end
    period_num = 1
    
    while current_test_start < max_date:
        current_test_end = min(current_test_start + timedelta(days=test_window_days), max_date)
        
        train_df, test_df = split_train_test(df, current_test_start, current_test_end)
        
        if len(test_df) == 0:
            break
        
        print(f"\n{'='*80}")
        print(f"PERIOD {period_num}: {current_test_start.date()} → {current_test_end.date()}")
        print(f"{'='*80}")
        print(f"   Training: {len(train_df):,} games")
        print(f"   Testing:  {len(test_df):,} games")
        
        if len(train_df) < 100:
            print(f"   ⚠️  Skipping - insufficient training data (need 100+)")
            current_test_start = current_test_end
            period_num += 1
            continue
        
        # Train models
        print(f"   Training models...")
        spread_model, ml_model = train_models(train_df)
        
        # Generate predictions
        print(f"   Generating predictions...")
        test_with_preds = generate_predictions(test_df, spread_model, ml_model)
        
        # Calculate model performance
        X_test, y_spread_test, y_win_test = build_features(test_df)
        spread_mae = mean_absolute_error(y_spread_test, test_with_preds['model_spread'])
        ml_acc = accuracy_score(y_win_test, (test_with_preds['model_home_prob'] > 0.5).astype(int))
        
        print(f"   Model performance:")
        print(f"      Spread MAE: {spread_mae:.2f} points")
        print(f"      ML Accuracy: {ml_acc:.1%}")
        
        # Count betting opportunities
        spread_bets = (abs(test_with_preds['edge_spread']) >= min_edge_spread).sum()
        ml_bets = ((test_with_preds['home_ml_edge'] >= min_edge_ml) | 
                   (test_with_preds['away_ml_edge'] >= min_edge_ml)).sum()
        
        print(f"   Betting opportunities:")
        print(f"      Spread: {spread_bets} bets")
        print(f"      ML: {ml_bets} bets")
        print(f"      Total: {spread_bets + ml_bets} bets ({(spread_bets + ml_bets)/len(test_df)*100:.1f}% of games)")
        
        # Store results
        all_periods.append({
            'period': period_num,
            'train_start': min_date,
            'train_end': current_test_start,
            'test_start': current_test_start,
            'test_end': current_test_end,
            'train_games': len(train_df),
            'test_games': len(test_df),
            'spread_mae': spread_mae,
            'ml_acc': ml_acc,
            'spread_bets': spread_bets,
            'ml_bets': ml_bets,
            'test_data': test_with_preds
        })
        
        current_test_start = current_test_end
        period_num += 1
    
    # Aggregate results
    print(f"\n{'='*80}")
    print(f"AGGREGATE RESULTS ({len(all_periods)} periods)")
    print(f"{'='*80}")
    
    total_games = sum(p['test_games'] for p in all_periods)
    total_spread_bets = sum(p['spread_bets'] for p in all_periods)
    total_ml_bets = sum(p['ml_bets'] for p in all_periods)
    avg_spread_mae = np.mean([p['spread_mae'] for p in all_periods])
    avg_ml_acc = np.mean([p['ml_acc'] for p in all_periods])
    
    print(f"\n📊 Model Performance:")
    print(f"   Avg Spread MAE: {avg_spread_mae:.2f} points")
    print(f"   Avg ML Accuracy: {avg_ml_acc:.1%}")
    
    print(f"\n🎯 Betting Volume:")
    print(f"   Total games tested: {total_games:,}")
    print(f"   Spread bets: {total_spread_bets} ({total_spread_bets/total_games*100:.1f}%)")
    print(f"   ML bets: {total_ml_bets} ({total_ml_bets/total_games*100:.1f}%)")
    print(f"   Total bets: {total_spread_bets + total_ml_bets}")
    
    print(f"\n⚠️  Note: To calculate actual P&L, you need actual game results.")
    print(f"   This backtest demonstrates ZERO DATA LEAKAGE methodology.")
    
    return {
        'periods': all_periods,
        'aggregate': {
            'total_games': total_games,
            'spread_bets': total_spread_bets,
            'ml_bets': total_ml_bets,
            'avg_spread_mae': avg_spread_mae,
            'avg_ml_acc': avg_ml_acc
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Walk-forward backtest with odds + KenPom data")
    parser.add_argument('--merged-file', type=Path, required=True, help="Path to merged CSV")
    parser.add_argument('--initial-train-months', type=int, default=2)
    parser.add_argument('--test-window-days', type=int, default=30)
    parser.add_argument('--min-edge-spread', type=float, default=2.0)
    parser.add_argument('--min-edge-ml', type=float, default=0.07)
    parser.add_argument('--output-file', type=Path, help="Save test data to CSV")
    
    args = parser.parse_args()
    
    # Load data
    df = load_data(args.merged_file)
    
    if len(df) == 0:
        print("\n❌ No data to backtest!")
        sys.exit(1)
    
    # Run backtest
    results = walkforward_backtest(
        df=df,
        initial_train_months=args.initial_train_months,
        test_window_days=args.test_window_days,
        min_edge_spread=args.min_edge_spread,
        min_edge_ml=args.min_edge_ml
    )
    
    # Save results if requested
    if args.output_file and results['periods']:
        all_test_data = pd.concat([p['test_data'] for p in results['periods']], ignore_index=True)
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        all_test_data.to_csv(args.output_file, index=False)
        print(f"\n💾 Saved test data to {args.output_file}")
    
    print(f"\n✅ Walk-forward backtest complete!")
    print(f"\n🎓 Next step: Add actual game results to calculate real P&L")


if __name__ == '__main__':
    main()
