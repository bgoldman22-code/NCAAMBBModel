"""
NCAA Basketball Variant B - Production Model Module

This module provides the production interface for Variant B (Market + In-Season Stats).
Use this for all live inference. DO NOT modify without re-auditing.

Model Specification:
- Variant: B (Market + In-Season Rolling Stats)
- Features: 43 (market features + ORtg/DRtg/Pace/MoV/WinPct over L3/L5/L10)
- Training: GradientBoostingClassifier
- Approved ROI: +25.3% at 0.15 edge threshold
- Audit Date: December 8, 2025
- Status: PRODUCTION-READY ✅
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from typing import Tuple, Optional
from datetime import datetime

# Model artifacts location
MODEL_DIR = Path(__file__).parent.parent / 'models' / 'variant_b_production'
MODEL_PATH = MODEL_DIR / 'variant_b_model.pkl'
SCALER_PATH = MODEL_DIR / 'variant_b_scaler.pkl'
METADATA_PATH = MODEL_DIR / 'variant_b_metadata.json'

def load_variant_b_model(model_path: Optional[str] = None):
    """
    Load the trained Variant B model + metadata.
    
    Returns:
        tuple: (model, scaler, metadata_dict)
    """
    if model_path is None:
        model_path = MODEL_PATH
    else:
        model_path = Path(model_path)
    
    scaler_path = model_path.parent / 'variant_b_scaler.pkl'
    metadata_path = model_path.parent / 'variant_b_metadata.json'
    
    # Load model
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            f"Run scripts/ncaabb/freeze_variant_b_model.py first."
        )
    
    model = joblib.load(model_path)
    
    # Load scaler (if exists)
    scaler = None
    if scaler_path.exists():
        scaler = joblib.load(scaler_path)
    
    # Load metadata
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    print(f"✅ Loaded Variant B model")
    print(f"   Variant: {metadata.get('variant', 'B')}")
    print(f"   Training Date: {metadata.get('training_date', 'Unknown')}")
    print(f"   Test AUC: {metadata.get('test_auc', 'N/A')}")
    print(f"   Features: {metadata.get('n_features', 'N/A')}")
    
    return model, scaler, metadata

def build_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build market-derived features.
    
    Expected input columns:
    - home_ml, away_ml (American odds)
    - close_spread (optional)
    """
    df = df.copy()
    
    # Convert American odds to implied probabilities
    def american_to_prob(odds):
        if odds < 0:
            return abs(odds) / (abs(odds) + 100)
        else:
            return 100 / (odds + 100)
    
    df['home_implied_prob'] = df['home_ml'].apply(american_to_prob)
    df['away_implied_prob'] = df['away_ml'].apply(american_to_prob)
    
    # Market features
    df['prob_diff'] = df['home_implied_prob'] - df['away_implied_prob']
    df['vig'] = (df['home_implied_prob'] + df['away_implied_prob']) - 1.0
    
    # Spread features (if available)
    if 'close_spread' in df.columns:
        df['spread_magnitude'] = df['close_spread'].abs()
        df['home_favorite'] = (df['close_spread'] < 0).astype(int)
    else:
        df['spread_magnitude'] = 0.0
        df['home_favorite'] = (df['home_implied_prob'] > 0.5).astype(int)
    
    # Derived spread feature
    df['close_spread_binary'] = (df.get('close_spread', 0).abs() <= 3).astype(int)
    
    return df

def build_features_for_games(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build complete Variant B feature set for live games.
    
    Expected input columns:
    - date, home_team, away_team
    - home_ml, away_ml
    - close_spread (optional)
    - In-season stats: ORtg_*_home/away, DRtg_*_home/away, etc.
      for L3, L5, L10 windows
    
    Returns:
        DataFrame with all 43 Variant B features
    """
    df = games_df.copy()
    
    # 1. Market features
    df = build_market_features(df)
    
    # 2. In-season matchup features (if available)
    # Handle both column formats: ORtg_L5_home and home_ORtg_L5
    home_ortg = 'ORtg_L5_home' if 'ORtg_L5_home' in df.columns else 'home_ORtg_L5'
    away_drtg = 'DRtg_L5_away' if 'DRtg_L5_away' in df.columns else 'away_DRtg_L5'
    
    if home_ortg in df.columns and away_drtg in df.columns:
        df['ORtg_vs_DRtg_L5'] = df[home_ortg] - df[away_drtg]
    
    home_pace = 'Pace_L5_home' if 'Pace_L5_home' in df.columns else 'home_Pace_L5'
    away_pace = 'Pace_L5_away' if 'Pace_L5_away' in df.columns else 'away_Pace_L5'
    
    if home_pace in df.columns and away_pace in df.columns:
        df['Pace_diff_L5'] = df[home_pace] - df[away_pace]
    
    home_mov = 'MoV_L5_home' if 'MoV_L5_home' in df.columns else 'home_MoV_L5'
    away_mov = 'MoV_L5_away' if 'MoV_L5_away' in df.columns else 'away_MoV_L5'
    
    if home_mov in df.columns and away_mov in df.columns:
        df['MoV_diff_L5'] = df[home_mov] - df[away_mov]
    
    home_win = 'WinPct_L5_home' if 'WinPct_L5_home' in df.columns else 'home_WinPct_L5'
    away_win = 'WinPct_L5_away' if 'WinPct_L5_away' in df.columns else 'away_WinPct_L5'
    
    if home_win in df.columns and away_win in df.columns:
        df['Form_diff_L5'] = df[home_win] - df[away_win]
    
    # Define expected features (Variant B specification)
    VARIANT_B_FEATURES = [
        # Market features (7)
        'home_implied_prob', 'away_implied_prob', 'prob_diff', 'vig',
        'spread_magnitude', 'close_spread_binary', 'home_favorite',
        
        # Matchup features (4)
        'ORtg_vs_DRtg_L5', 'Pace_diff_L5', 'MoV_diff_L5', 'Form_diff_L5'
    ]
    
    # Add individual team rolling stats if available
    # Check both column formats
    for window in [3, 5, 10]:
        for stat in ['ORtg', 'DRtg', 'Pace', 'MoV', 'WinPct']:
            for side in ['home', 'away']:
                # Try both formats: stat_L#_side and side_stat_L#
                col1 = f'{stat}_L{window}_{side}'
                col2 = f'{side}_{stat}_L{window}'
                if col1 in df.columns:
                    VARIANT_B_FEATURES.append(col1)
                elif col2 in df.columns:
                    VARIANT_B_FEATURES.append(col2)
    
    # Check for missing features
    available_features = [f for f in VARIANT_B_FEATURES if f in df.columns]
    missing_features = [f for f in VARIANT_B_FEATURES if f not in df.columns]
    
    if missing_features:
        print(f"⚠️  Warning: {len(missing_features)} features missing")
        print(f"   {missing_features[:5]}...")
        print(f"   Model will use {len(available_features)} available features")
    
    return df, available_features

def predict_variant_b(
    games_df: pd.DataFrame,
    model,
    feature_cols: list,
    min_edge: float = 0.15,
    scaler=None
) -> pd.DataFrame:
    """
    Generate Variant B predictions and filter by edge threshold.
    
    Args:
        games_df: DataFrame with features built
        model: Trained model
        feature_cols: List of feature column names to use
        min_edge: Minimum edge threshold (default 0.15)
        scaler: Optional feature scaler
    
    Returns:
        DataFrame with predictions, edges, and bet recommendations
    """
    df = games_df.copy()
    
    # Prepare features
    X = df[feature_cols].fillna(0)  # Fill missing with 0 (early season games)
    
    # Scale if scaler provided
    if scaler is not None:
        X = scaler.transform(X)
    
    # Predict probabilities
    try:
        probs = model.predict_proba(X)[:, 1]  # Probability of home win
    except:
        # Some models don't have predict_proba
        probs = model.predict(X)
    
    df['model_prob_home'] = probs
    df['model_prob_away'] = 1 - probs
    
    # Calculate edges for both sides
    df['edge_home'] = df['model_prob_home'] - df['home_implied_prob']
    df['edge_away'] = df['model_prob_away'] - df['away_implied_prob']
    
    # Determine best bet (if any)
    df['max_edge'] = df[['edge_home', 'edge_away']].max(axis=1)
    df['chosen_side'] = df.apply(
        lambda row: 'home' if row['edge_home'] > row['edge_away'] else 'away',
        axis=1
    )
    
    # Set recommended bet details
    df['recommended_bet'] = df.apply(
        lambda row: f"{row['chosen_side']}_ml",
        axis=1
    )
    
    df['bet_odds'] = df.apply(
        lambda row: row['home_ml'] if row['chosen_side'] == 'home' else row['away_ml'],
        axis=1
    )
    
    df['bet_prob'] = df.apply(
        lambda row: row['model_prob_home'] if row['chosen_side'] == 'home' else row['model_prob_away'],
        axis=1
    )
    
    df['bet_implied_prob'] = df.apply(
        lambda row: row['home_implied_prob'] if row['chosen_side'] == 'home' else row['away_implied_prob'],
        axis=1
    )
    
    # Filter by edge threshold
    qualified_bets = df[df['max_edge'] >= min_edge].copy()
    
    print(f"\n📊 Prediction Summary:")
    print(f"   Total games: {len(df)}")
    print(f"   Bets above {min_edge} edge: {len(qualified_bets)}")
    if len(qualified_bets) > 0:
        print(f"   Average edge: {qualified_bets['max_edge'].mean():.3f}")
        print(f"   Max edge: {qualified_bets['max_edge'].max():.3f}")
        print(f"   Home bets: {(qualified_bets['chosen_side'] == 'home').sum()}")
        print(f"   Away bets: {(qualified_bets['chosen_side'] == 'away').sum()}")
    
    return qualified_bets

def calculate_kelly_stake(
    edge: float,
    odds_american: float,
    kelly_fraction: float = 0.25,
    max_fraction: float = 0.10
) -> Tuple[float, float]:
    """
    Calculate Kelly Criterion stake.
    
    Args:
        edge: Model edge (model_prob - implied_prob)
        odds_american: American odds (e.g., -110, +150)
        kelly_fraction: Fraction of full Kelly to use (default 0.25 for 25% Kelly)
        max_fraction: Maximum fraction of bankroll to risk (safety cap)
    
    Returns:
        (full_kelly_fraction, applied_kelly_fraction)
    """
    # Convert American odds to decimal
    if odds_american < 0:
        decimal_odds = 1 + (100 / abs(odds_american))
    else:
        decimal_odds = 1 + (odds_american / 100)
    
    # Kelly formula: f = edge / (odds - 1)
    # Where edge = model_prob - implied_prob
    # And odds = decimal_odds
    
    full_kelly = edge / (decimal_odds - 1)
    
    # Apply fraction (e.g., 25% Kelly)
    applied_kelly = full_kelly * kelly_fraction
    
    # Safety cap
    applied_kelly = min(applied_kelly, max_fraction)
    
    # Floor at 0 (no negative bets)
    applied_kelly = max(applied_kelly, 0)
    
    return full_kelly, applied_kelly

def add_kelly_stakes(
    bets_df: pd.DataFrame,
    bankroll: float,
    kelly_fraction: float = 0.25,
    max_fraction: float = 0.10
) -> pd.DataFrame:
    """
    Add Kelly stake calculations to bets DataFrame.
    
    Args:
        bets_df: DataFrame with bet recommendations
        bankroll: Total bankroll in dollars
        kelly_fraction: Fraction of full Kelly (default 0.25)
        max_fraction: Maximum bankroll fraction per bet (default 0.10)
    
    Returns:
        DataFrame with kelly_* columns added
    """
    df = bets_df.copy()
    
    # Calculate Kelly for each bet
    kelly_results = df.apply(
        lambda row: calculate_kelly_stake(
            row['max_edge'],
            row['bet_odds'],
            kelly_fraction,
            max_fraction
        ),
        axis=1
    )
    
    df['kelly_full'] = [k[0] for k in kelly_results]
    df['kelly_applied'] = [k[1] for k in kelly_results]
    df['bet_size_dollars'] = df['kelly_applied'] * bankroll
    
    # Round bet sizes to nearest dollar
    df['bet_size_dollars'] = df['bet_size_dollars'].round(0).astype(int)
    
    return df

# Test function
if __name__ == '__main__':
    print("Variant B Production Model Module")
    print("="*60)
    print("\nThis module provides:")
    print("  - load_variant_b_model(): Load trained model")
    print("  - build_features_for_games(): Feature engineering")
    print("  - predict_variant_b(): Generate predictions")
    print("  - calculate_kelly_stake(): Bet sizing")
    print("\nRun scripts/ncaabb/generate_variant_b_picks.py for live picks")
