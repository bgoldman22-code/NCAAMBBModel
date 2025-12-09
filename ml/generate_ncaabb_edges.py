#!/usr/bin/env python3
"""
Generate betting edges for NCAA Basketball using trained models and market data.

This script:
1. Loads trained spread + moneyline models
2. Loads merged KenPom/ESPN game data
3. Loads market odds data (spreads, moneylines)
4. Generates model predictions
5. Calculates edges (model vs market)
6. Outputs edges to CSV for backtesting

Usage:
    python3 ml/generate_ncaabb_edges.py \
        --merged-dir data/merged \
        --markets-file data/markets/odds_ncaabb_2024.csv \
        --model-dir models/ncaabb \
        --output-file data/edges/edges_ncaabb_2024.csv

Output CSV Schema:
    - All merged data columns (team, opponent, KenPom features, etc.)
    - Market columns (close_spread, home_ml, away_ml, implied probs)
    - Model predictions (model_spread, model_home_prob, model_away_prob)
    - Edge calculations (edge_spread, home_ml_edge, away_ml_edge)
    - Bet recommendation (best_bet, max_edge)
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

# Add ml/ to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_all_merged_data
from features_ncaabb import build_features
from markets_ncaabb import load_markets, join_markets_with_merged, calculate_market_edge


def load_models(model_dir: Path) -> tuple:
    """
    Load trained spread and moneyline models.
    
    Args:
        model_dir: Directory containing model files
        
    Returns:
        (spread_model, moneyline_model)
        
    Raises:
        FileNotFoundError: If models don't exist
    """
    spread_path = model_dir / 'spread_model.pkl'
    ml_path = model_dir / 'moneyline_model.pkl'
    
    if not spread_path.exists():
        raise FileNotFoundError(f"Spread model not found: {spread_path}")
    if not ml_path.exists():
        raise FileNotFoundError(f"Moneyline model not found: {ml_path}")
    
    spread_model = joblib.load(spread_path)
    ml_model = joblib.load(ml_path)
    
    print(f"✅ Loaded models from {model_dir}")
    
    return spread_model, ml_model


def generate_predictions(
    df: pd.DataFrame,
    spread_model,
    ml_model,
    feature_cols: list
) -> pd.DataFrame:
    """
    Generate model predictions for all games.
    
    Args:
        df: DataFrame with features
        spread_model: Trained spread regression model
        ml_model: Trained moneyline classification model
        feature_cols: List of feature column names
        
    Returns:
        DataFrame with added prediction columns:
            - model_spread: Predicted margin from home (team) perspective
            - model_home_prob: Predicted win probability for home team
            - model_away_prob: 1 - model_home_prob
    """
    df = df.copy()
    
    X = df[feature_cols]
    
    # Spread predictions
    df['model_spread'] = spread_model.predict(X)
    
    # Moneyline predictions (probability of home team winning)
    df['model_home_prob'] = ml_model.predict_proba(X)[:, 1]
    df['model_away_prob'] = 1 - df['model_home_prob']
    
    print(f"✅ Generated predictions for {len(df):,} games")
    print(f"   Spread range: [{df['model_spread'].min():.1f}, {df['model_spread'].max():.1f}]")
    print(f"   Home prob range: [{df['model_home_prob'].min():.3f}, {df['model_home_prob'].max():.3f}]")
    
    return df


def calculate_all_edges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate betting edges for all games.
    
    Args:
        df: DataFrame with model predictions and market data
        
    Returns:
        DataFrame with added edge columns:
            - edge_spread: Model spread - market spread
            - home_ml_edge: Model home prob - market home implied prob
            - away_ml_edge: Model away prob - market away implied prob
            - best_bet: Recommended bet type
            - max_edge: Maximum edge value
    """
    df = df.copy()
    
    # Vectorized edge calculations
    df['edge_spread'] = df['model_spread'] - df['close_spread']
    df['home_ml_edge'] = df['model_home_prob'] - df['home_implied_prob']
    df['away_ml_edge'] = df['model_away_prob'] - df['away_implied_prob']
    
    # Determine best bet for each game
    # (This is a simplified version; calculate_market_edge() has more logic)
    edges_dict = []
    for _, row in df.iterrows():
        edge_info = calculate_market_edge(
            model_spread=row['model_spread'],
            close_spread=row['close_spread'],
            model_win_prob=row['model_home_prob'],
            home_implied_prob=row['home_implied_prob'],
            away_implied_prob=row['away_implied_prob']
        )
        edges_dict.append(edge_info)
    
    edge_df = pd.DataFrame(edges_dict)
    df['best_bet'] = edge_df['best_bet']
    df['max_edge'] = edge_df['max_edge']
    
    print(f"\n📊 Edge Distribution:")
    print(f"   Spread edge: μ={df['edge_spread'].mean():.2f}, σ={df['edge_spread'].std():.2f}")
    print(f"   Home ML edge: μ={df['home_ml_edge'].mean():.3f}, σ={df['home_ml_edge'].std():.3f}")
    print(f"   Away ML edge: μ={df['away_ml_edge'].mean():.3f}, σ={df['away_ml_edge'].std():.3f}")
    
    # Count bet recommendations
    bet_counts = df['best_bet'].value_counts()
    print(f"\n🎯 Bet Recommendations:")
    for bet_type, count in bet_counts.items():
        pct = count / len(df) * 100
        print(f"   {bet_type}: {count} ({pct:.1f}%)")
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Generate betting edges for NCAA Basketball"
    )
    parser.add_argument(
        '--merged-dir',
        type=Path,
        default=Path('data/merged'),
        help="Directory with merged KenPom/ESPN data"
    )
    parser.add_argument(
        '--markets-file',
        type=Path,
        required=True,
        help="Path to market odds CSV"
    )
    parser.add_argument(
        '--model-dir',
        type=Path,
        default=Path('models/ncaabb'),
        help="Directory with trained models"
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        required=True,
        help="Path to output edges CSV"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("NCAA BASKETBALL EDGE GENERATION")
    print("="*80)
    
    # 1. Load merged data
    print(f"\n1️⃣ Loading merged data from {args.merged_dir}...")
    merged_df = load_all_merged_data(args.merged_dir)
    
    # 2. Load market data
    print(f"\n2️⃣ Loading market data from {args.markets_file}...")
    markets_df = load_markets(args.markets_file)
    
    # 3. Join data
    print(f"\n3️⃣ Joining merged data with market data...")
    joined_df = join_markets_with_merged(merged_df, markets_df)
    
    if len(joined_df) == 0:
        print("\n❌ ERROR: No games matched between merged and market data")
        print("   Check team name consistency and date formats")
        sys.exit(1)
    
    # 4. Build features
    print(f"\n4️⃣ Building features...")
    X, _, _ = build_features(joined_df)
    
    # Combine features back with original data
    feature_df = joined_df.copy()
    for col in X.columns:
        feature_df[col] = X[col]
    
    # Get feature columns (same as used in training)
    feature_cols = [
        'efficiency_diff', 'offensive_matchup', 'defensive_matchup',
        'tempo_diff', 'sos_diff', 'luck_diff', 'avg_tempo',
        'rank_diff', 'home_flag', 'efficiency_x_tempo', 'matchup_product'
    ]
    
    # 5. Load models
    print(f"\n5️⃣ Loading models from {args.model_dir}...")
    spread_model, ml_model = load_models(args.model_dir)
    
    # 6. Generate predictions
    print(f"\n6️⃣ Generating model predictions...")
    pred_df = generate_predictions(feature_df, spread_model, ml_model, feature_cols)
    
    # 7. Calculate edges
    print(f"\n7️⃣ Calculating betting edges...")
    edge_df = calculate_all_edges(pred_df)
    
    # 8. Save output
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    edge_df.to_csv(args.output_file, index=False)
    
    print(f"\n✅ Saved {len(edge_df):,} games with edges to {args.output_file}")
    
    # Summary statistics
    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    print(f"Total games processed: {len(edge_df):,}")
    print(f"Date range: {edge_df['game_day'].min()} → {edge_df['game_day'].max()}")
    
    # Games with significant edges
    sig_spread = len(edge_df[edge_df['edge_spread'].abs() > 2])
    sig_ml = len(edge_df[(edge_df['home_ml_edge'].abs() > 0.05) | 
                          (edge_df['away_ml_edge'].abs() > 0.05)])
    
    print(f"\nGames with significant edges:")
    print(f"  Spread (|edge| > 2 pts): {sig_spread} ({sig_spread/len(edge_df)*100:.1f}%)")
    print(f"  Moneyline (|edge| > 5%):  {sig_ml} ({sig_ml/len(edge_df)*100:.1f}%)")
    
    print(f"\n✅ Edge generation complete!")


if __name__ == '__main__':
    main()
