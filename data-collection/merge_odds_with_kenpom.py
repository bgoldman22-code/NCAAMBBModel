#!/usr/bin/env python3
"""
Merge Odds API game data with KenPom ratings (TIME-AWARE).

NOTE ON LOOKAHEAD BIAS (December 2025):
    Currently using end-of-season KenPom ratings with a dummy rating_date equal to season start.
    This creates LOOKAHEAD BIAS because the ratings incorporate the entire season's performance,
    yet are attached to games throughout the season as if they were available pregame.
    
    FUTURE FIX:
    Replace kenpom_ratings_20XX.csv files with time-stamped snapshots (daily KenPom logs or
    Bart Torvik dated archives). Once those exist, this pipeline will automatically pick the
    latest rating_date <= game_date for each game, eliminating lookahead with ZERO code changes.

This script uses The Odds API data as the source of truth for games,
then enriches with KenPom efficiency ratings for BOTH teams using time-aware logic.

This allows us to use ALL NCAA games (not just the 30 teams in historical schedules).
"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import sys
import argparse

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'ml'))
sys.path.insert(0, str(Path(__file__).parent))

from markets_ncaabb import normalize_odds_team_name
from ratings_loader import load_season_ratings, attach_both_team_ratings

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
ODDS_FILE = DATA_DIR / "markets" / "odds_ncaabb_2024.csv"
KENPOM_DIR = DATA_DIR / "kenpom"
OUTPUT_DIR = DATA_DIR / "merged"

# Team name mappings (Odds API to KenPom)
TEAM_NAME_MAP = {
    # Common mismatches
    'UConn': 'Connecticut',
    'Connecticut': 'Connecticut',
    'Miami': 'Miami FL',
    'Miami (FL)': 'Miami FL',
    'Ole Miss': 'Mississippi',
    'USC': 'Southern California',
    'LSU': 'Louisiana State',
    'VCU': 'Virginia Commonwealth',
    'SMU': 'Southern Methodist',
    'UCF': 'Central Florida',
    'BYU': 'Brigham Young',
    'UNLV': 'Nevada Las Vegas',
    'UMass': 'Massachusetts',
    'UTEP': 'UTEP',
    'UAB': 'UAB',
    'UTSA': 'UT San Antonio',
    'UNC': 'North Carolina',
    'Pitt': 'Pittsburgh',
    'UVA': 'Virginia',
    'VT': 'Virginia Tech',
    # State abbreviations (Odds uses "State", KenPom uses "St.")
    'Michigan State': 'Michigan St.',
    'San Diego State': 'San Diego St.',
    'Iowa State': 'Iowa St.',
    'Ohio State': 'Ohio St.',
    'Oklahoma State': 'Oklahoma St.',
    'Oregon State': 'Oregon St.',
    'Kansas State': 'Kansas St.',
    'Penn State': 'Penn St.',
    'Fresno State': 'Fresno St.',
    'Boise State': 'Boise St.',
    'Colorado State': 'Colorado St.',
    'Washington State': 'Washington St.',
    'Arizona State': 'Arizona St.',
    'Ball State': 'Ball St.',
    'Illinois State': 'Illinois St.',
    'Indiana State': 'Indiana St.',
    'Kent State': 'Kent St.',
    'Missouri State': 'Missouri St.',
    'Montana State': 'Montana St.',
    'New Mexico State': 'New Mexico St.',
    'North Dakota State': 'North Dakota St.',
    'San Jose State': 'San Jose St.',
    'South Carolina State': 'South Carolina St.',
    'South Dakota State': 'South Dakota St.',
    'Utah State': 'Utah St.',
    'Wichita State': 'Wichita St.',
    'Wright State': 'Wright St.',
    'App State': 'Appalachian St.',
    # NC State special
    'NC State': 'N.C. State',
    'North Carolina State': 'N.C. State',
    # Florida schools
    'Florida State': 'Florida St.',
    'Florida International': 'FIU',
    'Florida Atlantic': 'Florida Atlantic',
    'Florida Gulf Coast': 'Florida Gulf Coast',
    # UC/Cal schools
    'Cal': 'California',
    'UC Irvine': 'UC Irvine',
    'UC Riverside': 'UC Riverside',
    'UC Davis': 'UC Davis',
    'UC Santa Barbara': 'UC Santa Barbara',
    'UC San Diego': 'UC San Diego',
    'Cal Poly': 'Cal Poly',
    'Cal Baptist': 'Cal Baptist',
    'Cal State Bakersfield': 'Cal St. Bakersfield',
    'Cal State Fullerton': 'Cal St. Fullerton',
    'Cal State Northridge': 'Cal St. Northridge',
    # Texas schools
    'Texas A&M Corpus Christi': 'Texas A&M Corpus Chris',
    'UT Rio Grande Valley': 'UT Rio Grande Valley',
    # Directional schools
    'Central Michigan': 'Central Michigan',
    'Eastern Michigan': 'Eastern Michigan',
    'Western Michigan': 'Western Michigan',
    'Northern Michigan': 'Northern Michigan',
    # Common variations
    'St. John\'s': 'St. John\'s',
    'Saint John\'s': 'St. John\'s',
    'Albany': 'Albany',
    'UAlbany': 'Albany',
    'UMass Lowell': 'UMass Lowell',
    'Miami (OH)': 'Miami OH',
    # Hawaii
    'Hawai\'i': 'Hawaii',
    'Hawaii': 'Hawaii',
}


def normalize_team_to_kenpom(team_name: str) -> str:
    """
    Normalize team name from Odds API to KenPom format.
    
    Args:
        team_name: Team name from Odds API (already has mascots removed)
        
    Returns:
        Normalized team name matching KenPom
    """
    # Remove any trailing/leading whitespace
    team_name = team_name.strip()
    
    # Check mapping
    if team_name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[team_name]
    
    # Return as-is if no mapping
    return team_name


def load_odds_data(odds_file: Path) -> pd.DataFrame:
    """Load and normalize odds data"""
    print(f"📂 Loading odds data from {odds_file}...")
    df = pd.read_csv(odds_file)
    
    # Normalize team names (remove mascots)
    df['home_team'] = df['home_team'].apply(normalize_odds_team_name)
    df['away_team'] = df['away_team'].apply(normalize_odds_team_name)
    
    # Further normalize to KenPom format
    df['home_team_kenpom'] = df['home_team'].apply(normalize_team_to_kenpom)
    df['away_team_kenpom'] = df['away_team'].apply(normalize_team_to_kenpom)
    
    # Parse date
    df['date'] = pd.to_datetime(df['game_day'])
    
    print(f"   Loaded {len(df):,} games")
    print(f"   Unique teams: {pd.concat([df['home_team'], df['away_team']]).nunique()}")
    print(f"   Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    
    return df


def merge_with_kenpom(odds_df: pd.DataFrame, season: int, ratings_mode: str = "season_end") -> pd.DataFrame:
    """
    Merge odds data with KenPom ratings for both home and away teams (TIME-AWARE).
    
    Uses the new ratings_loader module which implements date-aware rating attachment.
    For each game, the latest rating_date <= game_date is used.
    
    Args:
        odds_df: Odds data with normalized team names and 'date' column
        season: Season year
        ratings_mode: One of "season_end", "preseason_only", "dated_snapshots"
        
    Returns:
        Merged DataFrame with KenPom metrics for both teams
    """
    print(f"\n🔗 Merging with KenPom data for {season} season (ratings_mode={ratings_mode})...")
    
    try:
        # Load time-stamped KenPom ratings with specified mode
        kenpom = load_season_ratings(season, mode=ratings_mode, data_dir=DATA_DIR)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return None
    
    # Attach ratings for both teams using time-aware logic
    # This will pick rating_date <= game_date for each game
    merged = attach_both_team_ratings(
        odds_df,
        kenpom,
        home_col='home_team_kenpom',
        away_col='away_team_kenpom'
    )
    
    # Filter to only games where BOTH teams have KenPom data
    complete_games = merged[
        (merged['AdjEM_home'].notna()) & (merged['AdjEM_away'].notna())
    ].copy()
    
    print(f"\n✅ Complete games (both teams have KenPom data): {len(complete_games):,}")
    
    # The derived features (efficiency_diff, tempo_diff, etc.) are already
    # calculated by attach_both_team_ratings(), so we're done!
    
    return complete_games


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Merge Odds API data with KenPom ratings')
    parser.add_argument(
        '--ratings-mode',
        type=str,
        choices=['season_end', 'preseason_only', 'dated_snapshots'],
        default='season_end',
        help='Rating mode: season_end (lookahead), preseason_only (honest), dated_snapshots (target)'
    )
    args = parser.parse_args()
    
    ratings_mode = args.ratings_mode
    
    print("=" * 80)
    print(f"Merging Odds API Data with KenPom Ratings (mode={ratings_mode})")
    print("=" * 80)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load odds data
    odds_df = load_odds_data(ODDS_FILE)
    
    if odds_df is None or len(odds_df) == 0:
        print("❌ No odds data loaded!")
        return
    
    # Group by season
    odds_df['season'] = odds_df['date'].dt.year
    odds_df.loc[odds_df['date'].dt.month <= 6, 'season'] = odds_df['season']
    odds_df.loc[odds_df['date'].dt.month >= 11, 'season'] = odds_df['season'] + 1
    
    print(f"\nGames by season:")
    for season, count in odds_df.groupby('season').size().items():
        print(f"   {season}: {count} games")
    
    all_merged = []
    results = {}
    
    for season in sorted(odds_df['season'].unique()):
        season_odds = odds_df[odds_df['season'] == season]
        merged = merge_with_kenpom(season_odds, season, ratings_mode=ratings_mode)
        
        if merged is not None and len(merged) > 0:
            all_merged.append(merged)
            
            results[int(season)] = {
                'total_games': len(merged),
                'unique_teams': pd.concat([merged['home_team'], merged['away_team']]).nunique()
            }
    
    if not all_merged:
        print("\n❌ No data merged!")
        return
    
    # Combine all seasons
    final_df = pd.concat(all_merged, ignore_index=True)
    
    # Save combined dataset with mode-specific filename
    if ratings_mode == "season_end":
        output_file = OUTPUT_DIR / "merged_odds_kenpom_full_season_end.csv"
    elif ratings_mode == "preseason_only":
        output_file = OUTPUT_DIR / "merged_odds_kenpom_full_preseason.csv"
    else:  # dated_snapshots
        output_file = OUTPUT_DIR / "merged_odds_kenpom_full_dated.csv"
    
    final_df.to_csv(output_file, index=False)
    
    # Also save as default filename if season_end mode (for backwards compatibility)
    if ratings_mode == "season_end":
        default_file = OUTPUT_DIR / "merged_odds_kenpom_full.csv"
        final_df.to_csv(default_file, index=False)
        print(f"\n💾 Saved: {default_file.name} (default, for backwards compatibility)")
    
    file_size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"💾 Saved: {output_file.name} ({file_size_mb:.2f} MB)")
    
    # Print summary with ratings mode info
    unique_rating_dates_home = final_df['rating_date_home'].nunique() if 'rating_date_home' in final_df.columns else 0
    unique_rating_dates_away = final_df['rating_date_away'].nunique() if 'rating_date_away' in final_df.columns else 0
    
    print(f"\n[merge_odds_with_kenpom] ratings_mode={ratings_mode}")
    print(f"                        games={len(final_df):,}")
    print(f"                        unique_rating_dates_home={unique_rating_dates_home}")
    print(f"                        unique_rating_dates_away={unique_rating_dates_away}")
    
    # Save metadata
    metadata = {
        'merge_date': datetime.now().isoformat(),
        'source': 'odds_api_with_kenpom',
        'seasons': results,
        'total_games': len(final_df),
        'unique_teams': pd.concat([final_df['home_team'], final_df['away_team']]).nunique(),
        'date_range': {
            'start': final_df['date'].min().isoformat(),
            'end': final_df['date'].max().isoformat()
        }
    }
    
    with open(OUTPUT_DIR / 'merge_odds_kenpom_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ Merge Complete!")
    print("=" * 80)
    print(f"Total games: {len(final_df):,}")
    print(f"Unique teams: {metadata['unique_teams']}")
    print(f"Date range: {final_df['date'].min().date()} → {final_df['date'].max().date()}")
    print(f"Files saved to: {OUTPUT_DIR}")
    
    print("\n🎯 Next step: Run walk-forward backtest")
    print("python3 ml/walkforward_backtest_odds.py --merged-file data/merged/merged_odds_kenpom_full.csv")


if __name__ == "__main__":
    main()
