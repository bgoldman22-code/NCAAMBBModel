#!/usr/bin/env python3
"""
Feature engineering for NCAA Basketball prediction models.

This module transforms raw merged KenPom + ESPN data into ML-ready features
for predicting game outcomes (moneyline) and point spreads.
"""

import pandas as pd
import numpy as np
from typing import Tuple
import re


def parse_game_result(game_result: str) -> Tuple[bool, int, int]:
    """
    Parse game_result string like "W 92-54" or "L 73-78".
    
    Args:
        game_result: String in format "{W|L} {team_score}-{opp_score}"
        
    Returns:
        (did_win, team_score, opp_score)
    """
    if pd.isna(game_result):
        return None, None, None
    
    # Parse format: "W 92-54" or "L 73-78"
    match = re.match(r'([WL])\s+(\d+)-(\d+)', game_result.strip())
    if not match:
        return None, None, None
    
    result, team_score, opp_score = match.groups()
    did_win = (result == 'W')
    
    return did_win, int(team_score), int(opp_score)


def build_features(df: pd.DataFrame, include_target: bool = True) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Build ML features from merged KenPom + ESPN game data.
    
    Input: raw merged games DataFrame with KenPom metrics for team and opponent.
    
    Output:
        X : design matrix of features
        y_margin : target for spread modeling (team_score - opp_score)
        y_win : binary target for moneyline modeling (1 if team won, else 0)
        
    Features engineered:
        - efficiency_diff: AdjEM_team - AdjEM_opp
        - offensive_matchup: AdjOE_team - AdjDE_opp
        - defensive_matchup: AdjDE_team - AdjOE_opp
        - tempo_diff: AdjTempo_team - AdjTempo_opp
        - sos_diff: SOS_team - SOS_opp
        - luck_diff: Luck_team - Luck_opp
        - home_flag: 1 for home games (placeholder for now)
        
    Future features (TODO):
        - effective_height_diff
        - rim_protection_diff
        - shot_profile_3pa_rate_diff
        - oreb_dreb_matchup
        - turnover_creation_vs_allowed
        - experience_coaching_metrics
    """
    df = df.copy()
    
    # ============================================================
    # PARSE GAME RESULTS (if available)
    # ============================================================
    if include_target and 'game_result' in df.columns:
        results = df['game_result'].apply(parse_game_result)
        df['did_win'] = results.apply(lambda x: x[0])
        df['team_score'] = results.apply(lambda x: x[1])
        df['opp_score'] = results.apply(lambda x: x[2])
        df['margin'] = df['team_score'] - df['opp_score']
    
    # ============================================================
    # CORE KENPOM FEATURES
    # ============================================================
    
    # These may already be in the merged data, but recalculate for clarity
    df['efficiency_diff'] = df['AdjEM_team'] - df['AdjEM_opp']
    df['offensive_matchup'] = df['AdjOE_team'] - df['AdjDE_opp']
    df['defensive_matchup'] = df['AdjDE_team'] - df['AdjOE_opp']
    df['tempo_diff'] = df['AdjTempo_team'] - df['AdjTempo_opp']
    
    # Strength of schedule differential
    df['sos_diff'] = df['SOS_team'] - df['SOS_opp']
    
    # Luck differential (measures overperformance vs expected W-L)
    df['luck_diff'] = df['Luck_team'] - df['Luck_opp']
    
    # Absolute tempo (average pace)
    df['avg_tempo'] = (df['AdjTempo_team'] + df['AdjTempo_opp']) / 2
    
    # Team efficiency ranks (lower is better)
    df['rank_diff'] = df['RankAdjEM_team'] - df['RankAdjEM_opp']
    
    # ============================================================
    # HOME COURT ADVANTAGE
    # ============================================================
    # TODO: Implement proper home/away detection
    # For now, assume team is home by default (neutral games will need refinement)
    # Ideally, parse location from ESPN data or add explicit home/away flag
    df['home_flag'] = 1  # Placeholder: assume all games are home for team
    
    # ============================================================
    # INTERACTION FEATURES
    # ============================================================
    
    # Efficiency advantage × tempo (high tempo amplifies efficiency gaps)
    df['efficiency_x_tempo'] = df['efficiency_diff'] * df['avg_tempo']
    
    # Offensive advantage × defensive advantage (total matchup quality)
    df['matchup_product'] = df['offensive_matchup'] * df['defensive_matchup']
    
    # ============================================================
    # TODO: ADVANCED FEATURES (Phase 2+)
    # ============================================================
    # TODO: effective_height_diff - average height adjusted for position
    # TODO: rim_protection_diff - block% and rim FG% defense
    # TODO: shot_profile_3pa_rate_diff - 3PT attempt rate differential
    # TODO: oreb_dreb_matchup - offensive rebounding vs defensive rebounding
    # TODO: turnover_creation_vs_allowed - TO% forced vs TO% committed
    # TODO: experience_coaching_metrics - years of experience, coaching rating
    # TODO: recent_form - last 5 games efficiency trend
    # TODO: rest_days - days since last game (fatigue factor)
    # TODO: conference_strength - in-conference vs out-of-conference adjustment
    
    # ============================================================
    # SELECT FEATURES FOR MODEL
    # ============================================================
    
    feature_cols = [
        'efficiency_diff',
        'offensive_matchup',
        'defensive_matchup',
        'tempo_diff',
        'sos_diff',
        'luck_diff',
        'avg_tempo',
        'rank_diff',
        'home_flag',
        'efficiency_x_tempo',
        'matchup_product',
    ]
    
    # Filter to rows with complete data
    complete_mask = df[feature_cols].notna().all(axis=1)
    
    if include_target:
        complete_mask &= df['margin'].notna()
    
    df_clean = df[complete_mask].copy()
    
    X = df_clean[feature_cols]
    
    if include_target:
        y_margin = df_clean['margin']
        y_win = (df_clean['margin'] > 0).astype(int)
    else:
        y_margin = None
        y_win = None
    
    return X, y_margin, y_win


def get_feature_names() -> list:
    """Return list of feature names used in the model."""
    return [
        'efficiency_diff',
        'offensive_matchup',
        'defensive_matchup',
        'tempo_diff',
        'sos_diff',
        'luck_diff',
        'avg_tempo',
        'rank_diff',
        'home_flag',
        'efficiency_x_tempo',
        'matchup_product',
    ]


if __name__ == "__main__":
    # Simple test
    import sys
    sys.path.insert(0, '/Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball')
    
    print("Testing feature engineering...")
    df = pd.read_csv('data/merged/merged_games_2024.csv')
    
    X, y_margin, y_win = build_features(df)
    
    print(f"\n✅ Features built successfully!")
    print(f"   Shape: {X.shape}")
    print(f"   Features: {list(X.columns)}")
    print(f"\n   Target (margin) shape: {y_margin.shape}")
    print(f"   Target (win) shape: {y_win.shape}")
    print(f"\n   Sample features:")
    print(X.head())
    print(f"\n   Sample targets:")
    print(pd.DataFrame({'margin': y_margin.head(), 'win': y_win.head()}))
