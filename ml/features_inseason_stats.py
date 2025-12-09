"""
Compute rolling in-season statistics for NCAA basketball teams.

This module generates lookahead-free rolling statistics from historical game results.
For each game, only data from strictly prior games is used.

Key statistics:
    - Offensive/Defensive Rating (points per 100 possessions)
    - Pace (possessions per game)
    - Margin of Victory
    - Win percentage
    - Home/away splits

All stats are computed with multiple lookback windows (L3, L5, L10).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

def estimate_possessions(points: int, fga: int, fta: int, oreb: int, tov: int) -> float:
    """
    Estimate possessions using box score stats.
    
    Formula: FGA + 0.44 * FTA - OREB + TOV
    
    If detailed stats unavailable, use simplified estimate: points / 1.0 (assumes ~100 ORtg)
    """
    if pd.notna(fga) and pd.notna(fta):
        return fga + 0.44 * fta - oreb + tov
    else:
        # Fallback: assume average pace of ~70 possessions per team
        return 70.0

def compute_team_rolling_stats(
    team_games: pd.DataFrame,
    lookback_windows: List[int] = [3, 5, 10]
) -> pd.DataFrame:
    """
    Compute rolling statistics for a single team.
    
    Args:
        team_games: DataFrame with games for one team, sorted by date
            Required columns: date, points_for, points_against, won, is_home
            Optional: fga, fta, oreb, tov (for better possession estimates)
        lookback_windows: List of window sizes for rolling stats
    
    Returns:
        DataFrame with rolling stats added for each game
    """
    team_games = team_games.sort_values('date').copy()
    
    # Estimate possessions
    if 'fga' in team_games.columns:
        team_games['possessions'] = team_games.apply(
            lambda row: estimate_possessions(
                row['points_for'], 
                row.get('fga', np.nan),
                row.get('fta', np.nan), 
                row.get('oreb', 0),
                row.get('tov', 0)
            ), axis=1
        )
    else:
        # Simplified: assume ~70 poss/game
        team_games['possessions'] = 70.0
    
    # Compute per-possession metrics
    team_games['ORtg'] = (team_games['points_for'] / team_games['possessions']) * 100
    team_games['DRtg'] = (team_games['points_against'] / team_games['possessions']) * 100
    team_games['Pace'] = team_games['possessions']
    team_games['MoV'] = team_games['points_for'] - team_games['points_against']
    
    # Compute rolling stats for each window
    for window in lookback_windows:
        # Offensive rating
        team_games[f'ORtg_L{window}'] = (
            team_games['ORtg'].shift(1).rolling(window=window, min_periods=1).mean()
        )
        
        # Defensive rating
        team_games[f'DRtg_L{window}'] = (
            team_games['DRtg'].shift(1).rolling(window=window, min_periods=1).mean()
        )
        
        # Pace
        team_games[f'Pace_L{window}'] = (
            team_games['Pace'].shift(1).rolling(window=window, min_periods=1).mean()
        )
        
        # Margin of victory
        team_games[f'MoV_L{window}'] = (
            team_games['MoV'].shift(1).rolling(window=window, min_periods=1).mean()
        )
        
        # Win percentage
        team_games[f'WinPct_L{window}'] = (
            team_games['won'].shift(1).rolling(window=window, min_periods=1).mean()
        )
    
    # Home/away splits (last 5 games at home or away)
    if 'is_home' in team_games.columns:
        home_games = team_games[team_games['is_home'] == True].copy()
        away_games = team_games[team_games['is_home'] == False].copy()
        
        # Compute splits
        home_games['ORtg_at_home_L5'] = (
            home_games['ORtg'].shift(1).rolling(window=5, min_periods=1).mean()
        )
        home_games['DRtg_at_home_L5'] = (
            home_games['DRtg'].shift(1).rolling(window=5, min_periods=1).mean()
        )
        
        away_games['ORtg_on_road_L5'] = (
            away_games['ORtg'].shift(1).rolling(window=5, min_periods=1).mean()
        )
        away_games['DRtg_on_road_L5'] = (
            away_games['DRtg'].shift(1).rolling(window=5, min_periods=1).mean()
        )
        
        # Merge splits back
        team_games = team_games.merge(
            home_games[['date', 'ORtg_at_home_L5', 'DRtg_at_home_L5']],
            on='date', how='left'
        )
        team_games = team_games.merge(
            away_games[['date', 'ORtg_on_road_L5', 'DRtg_on_road_L5']],
            on='date', how='left'
        )
    
    # Games played (for time decay features)
    team_games['games_played'] = range(len(team_games))
    
    return team_games

def build_inseason_stats(
    results_df: pd.DataFrame,
    lookback_windows: List[int] = [3, 5, 10]
) -> pd.DataFrame:
    """
    Build rolling in-season statistics for all teams from game results.
    
    Args:
        results_df: DataFrame with game results
            Required columns: date, home_team, away_team, home_score, away_score
        lookback_windows: List of window sizes
    
    Returns:
        DataFrame with rolling stats for both home and away teams
    """
    print(f"\n{'='*60}")
    print("Building Rolling In-Season Statistics")
    print(f"{'='*60}")
    
    # Ensure date is datetime
    results_df['date'] = pd.to_datetime(results_df['date'])
    results_df = results_df.sort_values('date')
    
    print(f"Total games: {len(results_df)}")
    print(f"Date range: {results_df['date'].min().date()} → {results_df['date'].max().date()}")
    
    # Reshape to team-centric view
    home_games = results_df.copy()
    home_games['team'] = home_games['home_team']
    home_games['opponent'] = home_games['away_team']
    home_games['points_for'] = home_games['home_score']
    home_games['points_against'] = home_games['away_score']
    home_games['won'] = (home_games['home_score'] > home_games['away_score']).astype(int)
    home_games['is_home'] = True
    
    away_games = results_df.copy()
    away_games['team'] = away_games['away_team']
    away_games['opponent'] = away_games['home_team']
    away_games['points_for'] = away_games['away_score']
    away_games['points_against'] = away_games['home_score']
    away_games['won'] = (away_games['away_score'] > away_games['home_score']).astype(int)
    away_games['is_home'] = False
    
    # Combine
    all_team_games = pd.concat([home_games, away_games], ignore_index=True)
    all_team_games = all_team_games.sort_values(['team', 'date'])
    
    # Compute rolling stats per team
    print(f"\nComputing rolling stats for {all_team_games['team'].nunique()} teams...")
    
    team_stats_list = []
    for team in all_team_games['team'].unique():
        team_games = all_team_games[all_team_games['team'] == team].copy()
        team_stats = compute_team_rolling_stats(team_games, lookback_windows)
        team_stats_list.append(team_stats)
    
    all_stats = pd.concat(team_stats_list, ignore_index=True)
    
    print(f"✅ Rolling stats computed for all teams")
    
    # Merge back to original game structure
    print("\nMerging stats back to games...")
    
    # Home team stats
    home_stat_cols = [col for col in all_stats.columns if col.startswith(('ORtg_', 'DRtg_', 'Pace_', 'MoV_', 'WinPct_', 'games_played'))]
    home_stats = all_stats[all_stats['is_home'] == True][['date', 'team'] + home_stat_cols].copy()
    home_stats = home_stats.rename(columns={col: f'{col}_home' if not col in ['date', 'team'] else col for col in home_stats.columns})
    home_stats = home_stats.rename(columns={'team': 'home_team'})
    
    # Away team stats
    away_stats = all_stats[all_stats['is_home'] == False][['date', 'team'] + home_stat_cols].copy()
    away_stats = away_stats.rename(columns={col: f'{col}_away' if not col in ['date', 'team'] else col for col in away_stats.columns})
    away_stats = away_stats.rename(columns={'team': 'away_team'})
    
    # Merge
    merged = results_df.merge(home_stats, on=['date', 'home_team'], how='left')
    merged = merged.merge(away_stats, on=['date', 'away_team'], how='left')
    
    # Compute matchup features
    merged['ORtg_vs_DRtg_L5'] = merged['ORtg_L5_home'] - merged['DRtg_L5_away']
    merged['Pace_diff_L5'] = merged['Pace_L5_home'] - merged['Pace_L5_away']
    merged['MoV_diff_L5'] = merged['MoV_L5_home'] - merged['MoV_L5_away']
    merged['Form_diff_L5'] = merged['WinPct_L5_home'] - merged['WinPct_L5_away']
    
    # Count features available
    inseason_cols = [col for col in merged.columns if any(
        col.endswith(f'_L{w}') or col.endswith(f'_L{w}_home') or col.endswith(f'_L{w}_away')
        for w in lookback_windows
    )]
    
    print(f"✅ In-season feature columns created: {len(inseason_cols)}")
    print(f"   Sample: {inseason_cols[:5]}")
    
    # Report missingness
    missing_pct = merged[inseason_cols].isna().mean().mean() * 100
    print(f"\nMissing data: {missing_pct:.1f}% (early-season games have fewer lookback games)")
    
    return merged

def main():
    """Test the rolling stats module."""
    from pathlib import Path
    
    # Load results
    data_dir = Path(__file__).parent.parent / 'data'
    results_file = data_dir / 'walkforward_results_with_scores.csv'
    
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        return
    
    print(f"Loading results from: {results_file}")
    results_df = pd.read_csv(results_file)
    
    # Use game_day as date column (walkforward results use this)
    if 'game_day' in results_df.columns:
        results_df = results_df.rename(columns={'game_day': 'date'})
    
    # Drop duplicate 'date' column if it exists
    if 'date' in results_df.columns:
        date_cols = [col for col in results_df.columns if col == 'date']
        if len(date_cols) > 1:
            # Keep first, drop rest
            results_df = results_df.loc[:, ~results_df.columns.duplicated()]
    
    # Build stats
    enhanced_df = build_inseason_stats(results_df)
    
    # Show sample
    print(f"\n{'='*60}")
    print("Sample Enhanced Data")
    print(f"{'='*60}")
    
    sample_cols = ['date', 'home_team', 'away_team', 'ORtg_L5_home', 'DRtg_L5_home', 'ORtg_L5_away', 'DRtg_L5_away', 'ORtg_vs_DRtg_L5']
    print(enhanced_df[sample_cols].head(10).to_string(index=False))
    
    # Save
    output_file = data_dir / 'merged' / 'game_results_with_inseason_stats.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    enhanced_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved enhanced results to: {output_file}")

if __name__ == '__main__':
    main()
