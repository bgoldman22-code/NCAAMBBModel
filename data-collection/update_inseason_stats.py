"""
Update in-season rolling stats for current season games.

This script computes rolling window statistics (L3, L5, L10) for teams
based on current season game results. Required for live predictions.

Input:
    data/ncaabb/current_season/games_2025-26.csv (from fetch_current_season_games.py)

Output:
    Updates data/merged/game_results_with_inseason_stats.csv
    Appends current season games with computed rolling stats

Rolling Stats Computed:
    - ORtg (Offensive Rating): Points per 100 possessions
    - DRtg (Defensive Rating): Points allowed per 100 possessions
    - MoV (Margin of Victory): Average point differential
    - Pace: Possessions per game
    - WinPct: Win percentage

Windows: L3 (last 3 games), L5 (last 5), L10 (last 10)

Usage:
    # Update with latest current season games
    python3 data-collection/update_inseason_stats.py
    
    # Rebuild from scratch (clears old current season data first)
    python3 data-collection/update_inseason_stats.py --rebuild

Author: AI Assistant
Date: 2025-12-08
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
from typing import Dict, List

# Estimation for possessions (standard NCAA formula approximation)
def estimate_possessions(points: int, fg_attempts: int = None) -> float:
    """
    Estimate possessions from points scored.
    
    Uses simplified formula when play-by-play data unavailable:
        Poss ≈ Points / (eFG% * 2)
    
    Assumes league-average eFG% of ~50%
    """
    if fg_attempts:
        # More accurate with FG attempts
        return fg_attempts * 1.08  # Accounts for FTs and TOs
    else:
        # Rough estimate from points only
        return points / 1.0  # Assumes 1 point per possession average


def compute_rolling_stats(games_df: pd.DataFrame, team: str, 
                          as_of_date: str, window: int) -> Dict[str, float]:
    """
    Compute rolling window stats for a team as of a specific date.
    
    Args:
        games_df: DataFrame with all games
        team: Team name
        as_of_date: Compute stats as of this date (YYYY-MM-DD)
        window: Number of recent games to include (3, 5, or 10)
        
    Returns:
        Dict with ORtg, DRtg, MoV, Pace, WinPct for the window
    """
    # Get team's games before the as_of_date
    team_games = games_df[
        ((games_df['home_team'] == team) | (games_df['away_team'] == team)) &
        (games_df['date'] < as_of_date)
    ].sort_values('date').tail(window)
    
    if len(team_games) == 0:
        return {
            f'ORtg_L{window}': np.nan,
            f'DRtg_L{window}': np.nan,
            f'MoV_L{window}': np.nan,
            f'Pace_L{window}': np.nan,
            f'WinPct_L{window}': np.nan,
        }
    
    # Calculate stats for each game
    points_scored = []
    points_allowed = []
    wins = []
    poss_list = []
    
    for _, game in team_games.iterrows():
        is_home = game['home_team'] == team
        
        if is_home:
            scored = game['home_score']
            allowed = game['away_score']
        else:
            scored = game['away_score']
            allowed = game['home_score']
        
        points_scored.append(scored)
        points_allowed.append(allowed)
        wins.append(1 if scored > allowed else 0)
        
        # Estimate possessions (average of both teams)
        home_poss = estimate_possessions(game['home_score'])
        away_poss = estimate_possessions(game['away_score'])
        poss = (home_poss + away_poss) / 2
        poss_list.append(poss)
    
    # Aggregate stats
    avg_poss = np.mean(poss_list)
    
    # ORtg: Points per 100 possessions
    ortg = (np.sum(points_scored) / np.sum(poss_list)) * 100
    
    # DRtg: Points allowed per 100 possessions
    drtg = (np.sum(points_allowed) / np.sum(poss_list)) * 100
    
    # MoV: Average margin
    mov = np.mean([s - a for s, a in zip(points_scored, points_allowed)])
    
    # Pace: Possessions per game
    pace = avg_poss
    
    # WinPct: Win percentage
    win_pct = np.mean(wins)
    
    return {
        f'ORtg_L{window}': round(ortg, 2),
        f'DRtg_L{window}': round(drtg, 2),
        f'MoV_L{window}': round(mov, 2),
        f'Pace_L{window}': round(pace, 2),
        f'WinPct_L{window}': round(win_pct, 3),
    }


def build_inseason_stats(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build in-season stats for all games in dataset.
    
    For each game, computes rolling stats for both teams
    as of the game date (excluding the game itself).
    
    Args:
        games_df: DataFrame with game results
        
    Returns:
        DataFrame with added in-season stat columns
    """
    print(f"🔧 Computing in-season stats for {len(games_df)} games...")
    
    result_rows = []
    
    for idx, game in games_df.iterrows():
        if idx % 100 == 0:
            print(f"  Progress: {idx}/{len(games_df)} games processed...")
        
        row = game.to_dict()
        
        # Compute stats for home team
        for window in [3, 5, 10]:
            home_stats = compute_rolling_stats(
                games_df, game['home_team'], game['date'], window
            )
            for key, val in home_stats.items():
                row[f'home_{key}'] = val
        
        # Compute stats for away team
        for window in [3, 5, 10]:
            away_stats = compute_rolling_stats(
                games_df, game['away_team'], game['date'], window
            )
            for key, val in away_stats.items():
                row[f'away_{key}'] = val
        
        result_rows.append(row)
    
    result_df = pd.DataFrame(result_rows)
    print(f"✅ Computed stats for {len(result_df)} games")
    
    return result_df


def load_historical_stats() -> pd.DataFrame:
    """Load historical games with in-season stats (2023-24 season)."""
    hist_path = Path('data/merged/game_results_with_inseason_stats.csv')
    
    if not hist_path.exists():
        print("⚠️  Historical stats file not found, will create new one")
        return pd.DataFrame()
    
    print(f"📂 Loading historical in-season stats from {hist_path}")
    df = pd.read_csv(hist_path)
    
    # Keep only historical seasons (not current)
    df = df[df['season'] < 2026]
    print(f"   Loaded {len(df)} historical games (pre-2025-26)")
    
    return df


def main():
    parser = argparse.ArgumentParser(description='Update in-season stats with current season games')
    parser.add_argument('--current-games', type=str,
                       default='data/ncaabb/current_season/games_2025-26.csv',
                       help='Path to current season games CSV')
    parser.add_argument('--output', type=str,
                       default='data/merged/game_results_with_inseason_stats.csv',
                       help='Output path for updated stats')
    parser.add_argument('--rebuild', action='store_true',
                       help='Rebuild from scratch (clears old current season data)')
    
    args = parser.parse_args()
    
    # Load current season games
    current_path = Path(args.current_games)
    if not current_path.exists():
        print(f"❌ Current season games not found: {current_path}")
        print(f"   Run fetch_current_season_games.py first")
        sys.exit(1)
    
    print(f"📂 Loading current season games from {current_path}")
    current_games = pd.read_csv(current_path)
    print(f"   Loaded {len(current_games)} current season games")
    
    if current_games.empty:
        print("⚠️  No current season games to process")
        sys.exit(0)
    
    # Compute in-season stats for current season
    current_with_stats = build_inseason_stats(current_games)
    
    # Load historical stats
    historical = load_historical_stats()
    
    # Merge
    if historical.empty:
        final_df = current_with_stats
        print(f"📊 Created new stats file with {len(final_df)} games")
    else:
        # Combine historical + current
        final_df = pd.concat([historical, current_with_stats], ignore_index=True)
        final_df = final_df.sort_values('date').reset_index(drop=True)
        print(f"📊 Merged historical + current: {len(final_df)} total games")
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"✅ Saved updated stats to {output_path}")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   Total games: {len(final_df)}")
    print(f"   Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    print(f"   Historical games: {len(final_df[final_df['season'] < 2026])}")
    print(f"   Current season: {len(final_df[final_df['season'] == 2026])}")
    
    # Check coverage
    stat_cols = [col for col in final_df.columns if 'ORtg_L' in col or 'DRtg_L' in col]
    if stat_cols:
        sample_col = stat_cols[0]
        coverage = final_df[sample_col].notna().mean()
        print(f"   In-season stats coverage: {coverage*100:.1f}%")


if __name__ == '__main__':
    main()
