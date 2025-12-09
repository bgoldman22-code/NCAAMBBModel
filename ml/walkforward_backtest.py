#!/usr/bin/env python3
"""
Walk-forward backtest for NCAA Basketball betting with ZERO data leakage.

This script:
1. Splits data chronologically into training windows
2. Trains models on past data only
3. Tests on future unseen data
4. Retrains as we move forward (expanding window)
5. Only uses games where BOTH teams have KenPom data

Usage:
    python3 ml/walkforward_backtest.py \
        --merged-dir data/merged \
        --markets-file data/markets/odds_ncaabb_2024.csv \
        --min-edge-spread 2.0 \
        --min-edge-ml 0.07 \
        --stake 100

Walk-forward Strategy:
    - Train on all data before test period
    - Test on next month of games
    - Roll forward, retrain, test again
    - Never use future data in training
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, accuracy_score

# Add ml/ to path
sys.path.insert(0, str(Path(__file__).parent))

from features_ncaabb import build_features
from markets_ncaabb import load_markets, normalize_odds_team_name
from backtest_ncaabb_betting import backtest_strategy, print_summary


def load_all_data_with_markets(merged_dir: Path, markets_file: Path) -> pd.DataFrame:
    """
    Load all merged data and join with market odds.
    Only keep games where BOTH teams have complete KenPom data.
    
    Args:
        merged_dir: Directory with merged CSV files
        markets_file: Path to market odds CSV
        
    Returns:
        DataFrame with complete data (merged + markets)
    """
    print(f"\n📂 Loading all data...")
    
    # Load all merged files
    merged_files = sorted(merged_dir.glob('merged_games_*.csv'))
    all_merged = []
    
    for file in merged_files:
        df = pd.read_csv(file)
        all_merged.append(df)
    
    merged_df = pd.concat(all_merged, ignore_index=True)
    print(f"   Merged data: {len(merged_df):,} games from {len(merged_files)} files")
    
    # Load markets
    markets_df = pd.read_csv(markets_file)
    
    # Normalize team names
    markets_df['home_team'] = markets_df['home_team'].apply(normalize_odds_team_name)
    markets_df['away_team'] = markets_df['away_team'].apply(normalize_odds_team_name)
    markets_df['game_day'] = pd.to_datetime(markets_df['game_day']).dt.strftime('%B %d, %Y')
    
    print(f"   Market data: {len(markets_df):,} games")
    
    # Join on season, game_day, team, opponent
    joined = merged_df.merge(
        markets_df,
        left_on=['season', 'game_day', 'team', 'opponent'],
        right_on=['season', 'game_day', 'home_team', 'away_team'],
        how='inner'
    )
    
    print(f"   Initial join: {len(joined):,} games")
    
    # Filter for complete KenPom data (both teams)
    kenpom_cols = ['AdjEM_team', 'AdjOE_team', 'AdjDE_team', 
                   'AdjEM_opp', 'AdjOE_opp', 'AdjDE_opp']
    
    before = len(joined)
    joined = joined.dropna(subset=kenpom_cols)
    after = len(joined)
    
    print(f"   After filtering for complete KenPom data: {after:,} games")
    print(f"   Removed {before - after} games with missing data")
    
    # Add implied probabilities
    joined['home_implied_prob'] = joined['home_ml'].apply(american_to_prob)
    joined['away_implied_prob'] = joined['away_ml'].apply(american_to_prob)
    
    # Parse game date for sorting
    joined['date'] = pd.to_datetime(joined['game_day'])
    joined = joined.sort_values('date')
    
    print(f"\n✅ Final dataset: {len(joined):,} games with complete data")
    print(f"   Date range: {joined['date'].min().date()} → {joined['date'].max().date()}")
    print(f"   Unique teams: {joined['team'].nunique()}")
    
    return joined


def american_to_prob(odds: float) -> float:
    """Convert American odds to implied probability"""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def split_train_test_by_date(
    df: pd.DataFrame,
    test_start_date: datetime,
    test_end_date: datetime
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into train (before test_start) and test (between start and end).
    
    Args:
        df: Full dataset with 'date' column
        test_start_date: Start of test period
        test_end_date: End of test period
        
    Returns:
        (train_df, test_df)
    """
    train_df = df[df['date'] < test_start_date].copy()
    test_df = df[(df['date'] >= test_start_date) & (df['date'] <= test_end_date)].copy()
    
    return train_df, test_df


def train_models(train_df: pd.DataFrame) -> Tuple:
    """
    Train spread and moneyline models on training data.
    
    Args:
        train_df: Training data with features
        
    Returns:
        (spread_model, ml_model, feature_cols)
    """
    # Build features
    X_train, y_spread_train, y_win_train = build_features(train_df)
    
    # Train spread model
    spread_model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    spread_model.fit(X_train, y_spread_train)
    
    # Train moneyline model
    ml_model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    ml_model.fit(X_train, y_win_train)
    
    return spread_model, ml_model, X_train.columns.tolist()


def generate_predictions_and_edges(
    test_df: pd.DataFrame,
    spread_model,
    ml_model,
    feature_cols: List[str]
) -> pd.DataFrame:
    """
    Generate predictions and calculate edges for test period.
    
    Args:
        test_df: Test data
        spread_model: Trained spread model
        ml_model: Trained moneyline model
        feature_cols: List of feature column names
        
    Returns:
        DataFrame with predictions and edges
    """
    # Build features
    X_test, _, _ = build_features(test_df)
    
    # Generate predictions
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
    min_edge_ml: float = 0.07,
    stake: float = 100.0
) -> dict:
    """
    Perform walk-forward backtest with expanding training window.
    
    Args:
        df: Full dataset (sorted by date)
        initial_train_months: Months of data for initial training
        test_window_days: Days in each test window
        min_edge_spread: Minimum spread edge to bet
        min_edge_ml: Minimum ML edge to bet
        stake: Bet size per game
        
    Returns:
        Dict with backtest results
    """
    print("\n" + "="*80)
    print("WALK-FORWARD BACKTEST (ZERO DATA LEAKAGE)")
    print("="*80)
    
    # Determine date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Set initial training end date
    initial_train_end = min_date + timedelta(days=initial_train_months * 30)
    
    print(f"\nDataset:")
    print(f"   Total games: {len(df):,}")
    print(f"   Date range: {min_date.date()} → {max_date.date()}")
    print(f"   Duration: {(max_date - min_date).days} days")
    
    print(f"\nWalk-forward setup:")
    print(f"   Initial training: {initial_train_months} months ({min_date.date()} → {initial_train_end.date()})")
    print(f"   Test window: {test_window_days} days")
    print(f"   Strategy: Expanding window (retrain on all past data)")
    
    all_results = []
    test_periods = []
    
    current_test_start = initial_train_end
    period_num = 1
    
    while current_test_start < max_date:
        current_test_end = min(current_test_start + timedelta(days=test_window_days), max_date)
        
        # Split data
        train_df, test_df = split_train_test_by_date(df, current_test_start, current_test_end)
        
        if len(test_df) == 0:
            break
        
        print(f"\n{'='*80}")
        print(f"PERIOD {period_num}: {current_test_start.date()} → {current_test_end.date()}")
        print(f"{'='*80}")
        print(f"   Training: {len(train_df):,} games ({df['date'].min().date()} → {current_test_start.date()})")
        print(f"   Testing:  {len(test_df):,} games")
        
        if len(train_df) < 50:
            print(f"   ⚠️  Skipping - insufficient training data")
            current_test_start = current_test_end
            period_num += 1
            continue
        
        # Train models on past data only
        print(f"   Training models...")
        spread_model, ml_model, feature_cols = train_models(train_df)
        
        # Generate predictions for test period
        print(f"   Generating predictions...")
        test_with_preds = generate_predictions_and_edges(test_df, spread_model, ml_model, feature_cols)
        
        # Evaluate model performance
        X_test, y_spread_test, y_win_test = build_features(test_df)
        spread_mae = mean_absolute_error(y_spread_test, test_with_preds['model_spread'])
        ml_acc = accuracy_score(y_win_test, (test_with_preds['model_home_prob'] > 0.5).astype(int))
        
        print(f"   Model performance: Spread MAE={spread_mae:.2f}, ML Acc={ml_acc:.1%}")
        
        # Run backtest for this period
        period_results = backtest_strategy(
            test_with_preds,
            min_edge_spread=min_edge_spread,
            min_edge_ml=min_edge_ml,
            stake=stake
        )
        
        summary = period_results['summary']
        print(f"   Bets: {summary['spread_bets']} spread, {summary['ml_bets']} ML")
        print(f"   Profit: {summary['total_profit']:+.2f} units (ROI: {summary['total_roi']:+.2f}%)")
        
        # Store results
        period_results['period'] = period_num
        period_results['train_start'] = df['date'].min()
        period_results['train_end'] = current_test_start
        period_results['test_start'] = current_test_start
        period_results['test_end'] = current_test_end
        period_results['train_games'] = len(train_df)
        period_results['test_games'] = len(test_df)
        period_results['spread_mae'] = spread_mae
        period_results['ml_acc'] = ml_acc
        
        all_results.append(period_results)
        test_periods.append(test_with_preds)
        
        # Move to next period
        current_test_start = current_test_end
        period_num += 1
    
    # Aggregate results across all periods
    print(f"\n{'='*80}")
    print(f"AGGREGATE RESULTS (All {len(all_results)} periods)")
    print(f"{'='*80}")
    
    total_games = sum(r['summary']['total_games'] for r in all_results)
    total_spread_bets = sum(r['summary']['spread_bets'] for r in all_results)
    total_ml_bets = sum(r['summary']['ml_bets'] for r in all_results)
    total_spread_wins = sum(r['summary']['spread_wins'] for r in all_results)
    total_ml_wins = sum(r['summary']['ml_wins'] for r in all_results)
    total_spread_profit = sum(r['summary']['spread_profit'] for r in all_results)
    total_ml_profit = sum(r['summary']['ml_profit'] for r in all_results)
    
    aggregate = {
        'periods': len(all_results),
        'total_games': total_games,
        'spread_bets': total_spread_bets,
        'ml_bets': total_ml_bets,
        'spread_wins': total_spread_wins,
        'ml_wins': total_ml_wins,
        'spread_win_pct': (total_spread_wins / total_spread_bets * 100) if total_spread_bets > 0 else 0,
        'ml_win_pct': (total_ml_wins / total_ml_bets * 100) if total_ml_bets > 0 else 0,
        'spread_profit': total_spread_profit,
        'ml_profit': total_ml_profit,
        'spread_roi': (total_spread_profit / (total_spread_bets * stake) * 100) if total_spread_bets > 0 else 0,
        'ml_roi': (total_ml_profit / (total_ml_bets * stake) * 100) if total_ml_bets > 0 else 0,
        'total_profit': total_spread_profit + total_ml_profit,
        'total_roi': ((total_spread_profit + total_ml_profit) / ((total_spread_bets + total_ml_bets) * stake) * 100) if (total_spread_bets + total_ml_bets) > 0 else 0,
    }
    
    print(f"\n🎯 Spread Betting:")
    print(f"   Bets:     {aggregate['spread_bets']}")
    print(f"   Wins:     {aggregate['spread_wins']}")
    print(f"   Win rate: {aggregate['spread_win_pct']:.1f}%")
    print(f"   Profit:   {aggregate['spread_profit']:+.2f} units")
    print(f"   ROI:      {aggregate['spread_roi']:+.2f}%")
    
    print(f"\n💰 Moneyline Betting:")
    print(f"   Bets:     {aggregate['ml_bets']}")
    print(f"   Wins:     {aggregate['ml_wins']}")
    print(f"   Win rate: {aggregate['ml_win_pct']:.1f}%")
    print(f"   Profit:   {aggregate['ml_profit']:+.2f} units")
    print(f"   ROI:      {aggregate['ml_roi']:+.2f}%")
    
    print(f"\n📈 Combined:")
    print(f"   Total bets:   {aggregate['spread_bets'] + aggregate['ml_bets']}")
    print(f"   Total profit: {aggregate['total_profit']:+.2f} units")
    print(f"   Total ROI:    {aggregate['total_roi']:+.2f}%")
    
    print(f"\n🎓 Break-even analysis:")
    print(f"   Spread: Need 52.4% (actual: {aggregate['spread_win_pct']:.1f}%)")
    print(f"   Difference: {aggregate['spread_win_pct'] - 52.4:+.1f}%")
    
    return {
        'aggregate': aggregate,
        'periods': all_results,
        'test_data': pd.concat(test_periods, ignore_index=True) if test_periods else pd.DataFrame()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Walk-forward backtest with zero data leakage"
    )
    parser.add_argument('--merged-dir', type=Path, default=Path('data/merged'))
    parser.add_argument('--markets-file', type=Path, required=True)
    parser.add_argument('--initial-train-months', type=int, default=2)
    parser.add_argument('--test-window-days', type=int, default=30)
    parser.add_argument('--min-edge-spread', type=float, default=2.0)
    parser.add_argument('--min-edge-ml', type=float, default=0.07)
    parser.add_argument('--stake', type=float, default=100.0)
    parser.add_argument('--output-file', type=Path, help="Save results to CSV")
    
    args = parser.parse_args()
    
    # Load all data
    df = load_all_data_with_markets(args.merged_dir, args.markets_file)
    
    if len(df) == 0:
        print("\n❌ No data to backtest!")
        sys.exit(1)
    
    # Run walk-forward backtest
    results = walkforward_backtest(
        df=df,
        initial_train_months=args.initial_train_months,
        test_window_days=args.test_window_days,
        min_edge_spread=args.min_edge_spread,
        min_edge_ml=args.min_edge_ml,
        stake=args.stake
    )
    
    # Save test data with predictions if requested
    if args.output_file and len(results['test_data']) > 0:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        results['test_data'].to_csv(args.output_file, index=False)
        print(f"\n💾 Saved test data to {args.output_file}")
    
    print(f"\n✅ Walk-forward backtest complete!")


if __name__ == '__main__':
    main()
