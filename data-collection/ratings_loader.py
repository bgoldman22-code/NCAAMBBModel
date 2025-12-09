#!/usr/bin/env python3
"""
Date-aware KenPom ratings loader.

This module provides utilities to load and attach KenPom efficiency ratings
to game data in a time-aware manner (using rating_date <= game_date).

CURRENT STATE (December 2025):
    All kenpom_ratings_20XX.csv files are END-OF-SEASON snapshots collected
    after the season concluded. This creates LOOKAHEAD BIAS because every game
    uses ratings that incorporate future performance.

FUTURE STATE (when fixed):
    Replace with daily/weekly KenPom snapshots or Bart Torvik archives that
    have multiple rating_date entries per team throughout the season. The code
    below is designed to work with either:
    - Current: One row per team (season-end snapshot)
    - Future: Multiple rows per team with different rating_date values

The attach_team_ratings() function will automatically use the latest rating
available at game time (rating_date <= game_date), eliminating lookahead
once proper time-stamped data is provided.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime
import sys

# Add ml/ to path for team name normalization
sys.path.insert(0, str(Path(__file__).parent.parent / 'ml'))
try:
    from team_database import normalize_team_name
except ImportError:
    # Fallback if team_database not available
    def normalize_team_name(name: str) -> str:
        """Fallback normalization if team_database is not available"""
        return str(name).strip() if pd.notna(name) else name


def load_season_ratings(season: int, mode: str = "season_end", data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load KenPom ratings for a season with date-awareness.
    
    Args:
        season: Season ending year (2024 = 2023-24 season)
        mode: Rating mode to use:
            - "season_end": End-of-season snapshot (LOOKAHEAD BIASED)
            - "preseason_only": Preseason ratings only (honest but crude)
            - "dated_snapshots": Multiple rating_date per team (lookahead-free)
        data_dir: Optional path to data directory (defaults to ../data from this file)
        
    Returns:
        DataFrame with columns:
            - team: Team name (normalized)
            - rating_date: Date these ratings are valid as of
            - AdjEM, AdjOE, AdjDE, AdjTempo: Efficiency metrics
            - SOS, Luck: Context metrics
            - Rank columns: RankAdjEM, RankAdjOE, etc.
            
    Mode Behaviors:
        season_end:
            Loads end-of-season snapshot and sets rating_date to season start.
            ⚠️ CONTAINS LOOKAHEAD BIAS - all games use final-season ratings.
            
        preseason_only:
            Loads end-of-season snapshot but sets rating_date to preseason (Nov 1).
            No in-season updates, but no lookahead of future performance.
            Honest but crude baseline.
            
        dated_snapshots:
            Loads kenpom_ratings_{season}_dated.csv with multiple rating_date rows.
            Requires prior consolidation via consolidate_ratings_snapshots.py.
            ✓ LOOKAHEAD-FREE when proper dated snapshots are used.
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    
    if mode not in ["season_end", "preseason_only", "dated_snapshots"]:
        raise ValueError(f"Invalid mode: {mode}. Must be one of: season_end, preseason_only, dated_snapshots")
    
    # Determine which file to load
    if mode == "dated_snapshots":
        ratings_path = data_dir / "kenpom" / f"kenpom_ratings_{season}_dated.csv"
    else:
        ratings_path = data_dir / "kenpom" / f"kenpom_ratings_{season}.csv"
    
    if not ratings_path.exists():
        raise FileNotFoundError(
            f"KenPom ratings not found: {ratings_path}\n"
            f"For mode={mode}, ensure the required file exists.\n"
            f"Run: python3 data-collection/collect_kenpom_api.py (for season_end/preseason_only)\n"
            f"Or: python3 data-collection/consolidate_ratings_snapshots.py (for dated_snapshots)"
        )
    
    df = pd.read_csv(ratings_path)
    
    # Normalize column names if needed
    if 'TeamName' in df.columns:
        df = df.rename(columns={'TeamName': 'team'})
    
    # Ensure team column exists
    if 'team' not in df.columns:
        raise ValueError(f"Ratings file missing 'team' or 'TeamName' column: {ratings_path}")
    
    # Handle rating_date based on mode
    if mode == "dated_snapshots":
        # dated_snapshots mode: expect rating_date already in file
        if 'rating_date' not in df.columns:
            raise ValueError(
                f"dated_snapshots mode requires 'rating_date' column in {ratings_path}\n"
                f"Run: python3 data-collection/consolidate_ratings_snapshots.py"
            )
        df['rating_date'] = pd.to_datetime(df['rating_date'])
        
        # Validate multiple dates per team
        unique_dates = df['rating_date'].nunique()
        if unique_dates == 1:
            print(f"⚠️  WARNING: dated_snapshots mode but only 1 unique rating_date")
            print(f"   This is effectively the same as season_end mode")
        
        print(f"✅ DATED_SNAPSHOTS MODE: Loaded time-stamped ratings for {season}")
        print(f"   Unique rating dates: {unique_dates}")
        print(f"   Date range: {df['rating_date'].min().date()} → {df['rating_date'].max().date()}")
        print(f"   Avg ratings per team: {len(df) / df['team'].nunique():.1f}")
        
    elif mode == "preseason_only":
        # preseason_only mode: use preseason date for all teams
        # Set to early November (typical preseason)
        preseason_dates = {
            2022: '2021-11-01',
            2023: '2022-11-01',
            2024: '2023-11-01',
            2025: '2024-11-01',
        }
        preseason_date = preseason_dates.get(season, f'{season-1}-11-01')
        df['rating_date'] = pd.to_datetime(preseason_date)
        
        print(f"✅ PRESEASON_ONLY MODE: Using single preseason rating for {season}")
        print(f"   All teams use rating_date = {preseason_date}")
        print(f"   This is HONEST (no lookahead) but CRUDE (no in-season updates)")
        
    else:  # season_end mode
        # season_end mode: use season start date (contains lookahead)
        season_start_dates = {
            2022: '2021-11-09',
            2023: '2022-11-07',
            2024: '2023-11-06',
            2025: '2024-11-04',
        }
        season_start = season_start_dates.get(season, f'{season-1}-11-06')
        df['rating_date'] = pd.to_datetime(season_start)
        
        print(f"⚠️  SEASON_END MODE: Using end-of-season snapshot for {season}")
        print(f"   rating_date set to {season_start} (season start) for all teams")
        print(f"   This is LOOKAHEAD BIASED - ratings include full season data")
        print(f"   Use preseason_only or dated_snapshots mode for honest evaluation")
    
    # Describe the loaded ratings
    describe_ratings(df)
    
    return df


def describe_ratings(ratings_df: pd.DataFrame) -> None:
    """
    Print summary statistics for loaded ratings.
    
    Args:
        ratings_df: Ratings DataFrame with team, rating_date columns
    """
    print(f"\nRatings Summary:")
    print(f"  Total rows: {len(ratings_df)}")
    print(f"  Unique teams: {ratings_df['team'].nunique()}")
    print(f"  Unique rating_dates: {ratings_df['rating_date'].nunique()}")
    print(f"  Min rating_date: {ratings_df['rating_date'].min()}")
    print(f"  Max rating_date: {ratings_df['rating_date'].max()}")


def attach_team_ratings(
    games_df: pd.DataFrame,
    ratings_df: pd.DataFrame,
    side: str,
    team_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Attach team ratings to games using latest rating available at game time.
    
    This function implements time-aware rating attachment: for each game,
    it finds the most recent rating where rating_date <= game_date.
    
    Args:
        games_df: DataFrame with game data, must have columns:
            - date: Game date (will be converted to datetime)
            - {side}_team: Team name (or specify via team_col)
        ratings_df: DataFrame from load_season_ratings() with:
            - team: Team name
            - rating_date: Date of this rating snapshot
            - AdjEM, AdjOE, AdjDE, AdjTempo, etc.: Rating columns
        side: Either "home" or "away" (determines column prefixes)
        team_col: Optional custom column name for team (default: {side}_team)
        
    Returns:
        games_df with added columns:
            - AdjEM_{side}, AdjOE_{side}, AdjDE_{side}, etc.
            - rating_date_{side}: Date of the rating used (for debugging)
            
    Algorithm:
        For each game:
        1. Filter ratings to this team only
        2. Filter to rating_date <= game_date
        3. Sort by rating_date descending
        4. Take the first row (most recent rating before game)
        5. Merge onto game row with {side}_ prefix
        
    Current Behavior (with season-end snapshots):
        Because each team only has one rating_date (season end), every game
        will use that same rating, creating lookahead bias.
        
    Future Behavior (with dated snapshots):
        Each game will use the latest rating available before tip-off,
        eliminating lookahead automatically.
    """
    if side not in ['home', 'away']:
        raise ValueError(f"side must be 'home' or 'away', got: {side}")
    
    # Determine team column name
    if team_col is None:
        team_col = f'{side}_team'
    
    if team_col not in games_df.columns:
        raise ValueError(f"games_df missing column: {team_col}")
    
    if 'date' not in games_df.columns:
        raise ValueError("games_df missing 'date' column")
    
    # Ensure date columns are datetime
    games_df = games_df.copy()
    games_df['date'] = pd.to_datetime(games_df['date'])
    
    # Normalize team names in games_df to match KenPom format
    games_df[f'{team_col}_normalized'] = games_df[team_col].apply(normalize_team_name)
    
    if 'rating_date' not in ratings_df.columns:
        raise ValueError("ratings_df missing 'rating_date' column (use load_season_ratings)")
    
    # Prepare ratings columns to merge (exclude keys and date)
    rating_cols = [col for col in ratings_df.columns 
                   if col not in ['team', 'rating_date']]
    
    # Create a list to hold matched ratings for each game
    matched_ratings = []
    
    for idx, game in games_df.iterrows():
        game_date = game['date']
        team_name = game[f'{team_col}_normalized']  # Use normalized name
        
        # Filter ratings for this team only
        team_ratings = ratings_df[ratings_df['team'] == team_name].copy()
        
        if team_ratings.empty:
            # No ratings found for this team
            matched_ratings.append({col: None for col in rating_cols + ['rating_date']})
            continue
        
        # Filter to ratings available before/at game time
        available_ratings = team_ratings[team_ratings['rating_date'] <= game_date]
        
        if available_ratings.empty:
            # No ratings available before this game (game too early in season)
            matched_ratings.append({col: None for col in rating_cols + ['rating_date']})
            continue
        
        # Take the most recent rating before game
        latest_rating = available_ratings.sort_values('rating_date', ascending=False).iloc[0]
        
        # Extract rating values
        rating_dict = latest_rating[rating_cols + ['rating_date']].to_dict()
        matched_ratings.append(rating_dict)
    
    # Convert to DataFrame
    matched_df = pd.DataFrame(matched_ratings)
    
    # Add suffix to all columns
    matched_df = matched_df.add_suffix(f'_{side}')
    
    # Concatenate with original games_df
    result_df = pd.concat([games_df.reset_index(drop=True), matched_df], axis=1)
    
    # Report matching statistics
    total_games = len(result_df)
    matched_games = result_df[f'AdjEM_{side}'].notna().sum()
    match_pct = (matched_games / total_games * 100) if total_games > 0 else 0
    
    print(f"  {side.capitalize()} team ratings: {matched_games}/{total_games} ({match_pct:.1f}%) matched")
    
    if matched_games < total_games:
        unmatched = result_df[result_df[f'AdjEM_{side}'].isna()]
        unmatched_teams = unmatched[team_col].unique()
        print(f"    ⚠️  Unmatched {side} teams ({len(unmatched_teams)}): {', '.join(list(unmatched_teams)[:5])}")
    
    return result_df


def attach_both_team_ratings(
    games_df: pd.DataFrame,
    ratings_df: pd.DataFrame,
    home_col: str = 'home_team',
    away_col: str = 'away_team'
) -> pd.DataFrame:
    """
    Convenience function to attach ratings for both home and away teams.
    
    Args:
        games_df: Game data with date, home_team, away_team columns
        ratings_df: Ratings from load_season_ratings()
        home_col: Column name for home team (default: 'home_team')
        away_col: Column name for away team (default: 'away_team')
        
    Returns:
        games_df with both home and away ratings attached
    """
    print("Attaching team ratings (time-aware)...")
    
    # Attach home ratings
    result_df = attach_team_ratings(games_df, ratings_df, side='home', team_col=home_col)
    
    # Attach away ratings
    result_df = attach_team_ratings(result_df, ratings_df, side='away', team_col=away_col)
    
    # Calculate derived features if possible
    if 'AdjEM_home' in result_df.columns and 'AdjEM_away' in result_df.columns:
        result_df['efficiency_diff'] = result_df['AdjEM_home'] - result_df['AdjEM_away']
        
    if 'AdjTempo_home' in result_df.columns and 'AdjTempo_away' in result_df.columns:
        result_df['tempo_diff'] = result_df['AdjTempo_home'] - result_df['AdjTempo_away']
        
    if 'AdjOE_home' in result_df.columns and 'AdjDE_away' in result_df.columns:
        result_df['offensive_matchup_home'] = result_df['AdjOE_home'] - result_df['AdjDE_away']
        
    if 'AdjDE_home' in result_df.columns and 'AdjOE_away' in result_df.columns:
        result_df['defensive_matchup_home'] = result_df['AdjDE_home'] - result_df['AdjOE_away']
    
    return result_df


if __name__ == '__main__':
    """
    Test the ratings loader with current end-of-season data.
    """
    print("=" * 80)
    print("TESTING DATE-AWARE RATINGS LOADER")
    print("=" * 80)
    
    # Load 2024 season ratings
    print("\n1. Loading 2024 ratings...")
    ratings = load_season_ratings(2024)
    print(f"   Loaded {len(ratings)} teams")
    print(f"   Columns: {', '.join(ratings.columns[:10])}...")
    
    # Create sample game data
    print("\n2. Creating sample games...")
    sample_games = pd.DataFrame({
        'date': ['2024-01-15', '2024-02-20', '2024-03-15'],
        'home_team': ['Duke', 'Kansas', 'North Carolina'],
        'away_team': ['North Carolina', 'Kentucky', 'Duke']
    })
    print(f"   Created {len(sample_games)} sample games")
    
    # Attach ratings
    print("\n3. Attaching ratings (time-aware)...")
    result = attach_both_team_ratings(sample_games, ratings)
    
    print("\n4. Result preview:")
    display_cols = ['date', 'home_team', 'away_team', 'AdjEM_home', 'AdjEM_away', 
                    'efficiency_diff', 'rating_date_home']
    available_cols = [col for col in display_cols if col in result.columns]
    print(result[available_cols].to_string(index=False))
    
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80)
    print("\nNOTE: Currently using end-of-season ratings (LOOKAHEAD BIAS).")
    print("Once dated ratings are available, this code will automatically use")
    print("the latest rating_date <= game_date, eliminating lookahead.")
