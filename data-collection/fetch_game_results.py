#!/usr/bin/env python3
"""
Fetch actual game results for backtest validation.

Uses CBBpy to get actual scores for games in our walkforward backtest.
"""

import pandas as pd
import cbbpy.mens_scraper as scraper
from pathlib import Path
import time
from datetime import datetime
from tqdm import tqdm

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
WALKFORWARD_FILE = DATA_DIR / "walkforward_results_full.csv"
OUTPUT_FILE = DATA_DIR / "walkforward_results_with_scores.csv"

# Team name mappings (our data to CBBpy)
TEAM_NAME_MAP = {
    'UConn': 'Connecticut',
    'Miami': 'Miami FL',
    'Miami (FL)': 'Miami FL',
    'Ole Miss': 'Mississippi',
    'USC': 'Southern California',
    'LSU': 'Louisiana State',
    'VCU': 'Virginia Commonwealth',
    'SMU': 'Southern Methodist',
    'UCF': 'Central Florida',
    'St. John\'s': 'St. John\'s',
    'Saint John\'s': 'St. John\'s',
}


def normalize_team_name(team: str) -> str:
    """Normalize team name for CBBpy lookup"""
    team = team.strip()
    return TEAM_NAME_MAP.get(team, team)


def fetch_all_season_games(season: int) -> pd.DataFrame:
    """
    Fetch all games for entire season.
    
    Args:
        season: Season year (e.g., 2024)
        
    Returns:
        DataFrame with all game results for season
    """
    try:
        print(f"   Fetching all games for {season-1}-{season} season...")
        games = scraper.get_games_season(season=season)
        
        if games is None or len(games) == 0:
            return None
        
        print(f"   Found {len(games):,} games")
        return games
        
    except Exception as e:
        print(f"   Error fetching season {season}: {str(e)}")
        return None


def match_game_to_result(row, date_results):
    """
    Match a game from our dataset to actual results.
    
    Args:
        row: Row from walkforward dataset
        date_results: DataFrame with results for that date
        
    Returns:
        Dict with home_score, away_score, or None if no match
    """
    if date_results is None or len(date_results) == 0:
        return None
    
    home_team = normalize_team_name(row['home_team'])
    away_team = normalize_team_name(row['away_team'])
    
    # Try to find matching game
    # CBBpy has columns: 'team', 'opponent', 'home', 'points', 'opp_points'
    
    # Look for home team in results
    home_games = date_results[
        (date_results['team'] == home_team) & 
        (date_results['opponent'] == away_team) &
        (date_results['home'] == True)
    ]
    
    if len(home_games) > 0:
        game = home_games.iloc[0]
        return {
            'home_score': game['points'],
            'away_score': game['opp_points'],
            'matched': True
        }
    
    # Try reverse (away team perspective)
    away_games = date_results[
        (date_results['team'] == away_team) & 
        (date_results['opponent'] == home_team) &
        (date_results['home'] == False)
    ]
    
    if len(away_games) > 0:
        game = away_games.iloc[0]
        return {
            'home_score': game['opp_points'],
            'away_score': game['points'],
            'matched': True
        }
    
    return None


def add_actual_results(walkforward_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add actual game results to walkforward dataset.
    
    Args:
        walkforward_df: DataFrame with predictions
        
    Returns:
        DataFrame with actual scores added
    """
    print(f"\n🏀 Fetching actual game results...")
    print(f"Total games: {len(walkforward_df):,}")
    
    # Get unique seasons
    walkforward_df['date'] = pd.to_datetime(walkforward_df['date'])
    
    # Determine seasons
    walkforward_df['fetch_season'] = walkforward_df['date'].dt.year
    walkforward_df.loc[walkforward_df['date'].dt.month >= 11, 'fetch_season'] = walkforward_df['fetch_season'] + 1
    
    unique_seasons = sorted(walkforward_df['fetch_season'].unique())
    print(f"Seasons: {unique_seasons}")
    
    # Fetch all games for each season
    all_season_results = []
    
    for season in unique_seasons:
        results = fetch_all_season_games(season)
        if results is not None:
            # Add date column for filtering
            if 'game_date' in results.columns:
                results['match_date'] = pd.to_datetime(results['game_date'])
            elif 'date' in results.columns:
                results['match_date'] = pd.to_datetime(results['date'])
            else:
                print(f"   ⚠️  No date column found, using index")
                
            all_season_results.append(results)
        time.sleep(2)  # Rate limiting
    
    if not all_season_results:
        print("\n❌ No season results fetched!")
        walkforward_df['result_matched'] = False
        return walkforward_df
    
    # Combine all seasons
    all_results = pd.concat(all_season_results, ignore_index=True)
    print(f"\n✅ Total results fetched: {len(all_results):,} games")
    
    # Add result columns
    walkforward_df['home_score'] = None
    walkforward_df['away_score'] = None
    walkforward_df['result_matched'] = False
    
    print(f"\n🔗 Matching games to results...")
    
    # Match each game
    matched_count = 0
    
    for idx, row in tqdm(walkforward_df.iterrows(), total=len(walkforward_df), desc="Matching games"):
        # Filter results to same date (or nearby)
        game_date = row['date']
        date_str = game_date.strftime('%Y-%m-%d')
        
        # Get results around this date
        if 'match_date' in all_results.columns:
            date_results = all_results[
                (all_results['match_date'] >= game_date - pd.Timedelta(days=1)) &
                (all_results['match_date'] <= game_date + pd.Timedelta(days=1))
            ]
        else:
            date_results = all_results  # Match across all if no date filter
        
        match = match_game_to_result(row, date_results)
        
        if match:
            walkforward_df.at[idx, 'home_score'] = match['home_score']
            walkforward_df.at[idx, 'away_score'] = match['away_score']
            walkforward_df.at[idx, 'result_matched'] = True
            matched_count += 1
    
    print(f"\n✅ Matched {matched_count}/{len(walkforward_df)} games ({matched_count/len(walkforward_df)*100:.1f}%)")
    
    # Calculate actual results
    matched_df = walkforward_df[walkforward_df['result_matched'] == True].copy()
    
    if len(matched_df) > 0:
        matched_df['actual_margin'] = matched_df['home_score'] - matched_df['away_score']
        matched_df['home_won'] = (matched_df['actual_margin'] > 0).astype(int)
        matched_df['home_covered'] = (
            matched_df['actual_margin'] + matched_df['close_spread'] > 0
        ).astype(int)
        
        # Copy back to main df
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'actual_margin'] = matched_df['actual_margin']
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'home_won'] = matched_df['home_won']
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'home_covered'] = matched_df['home_covered']
    
    return walkforward_df


def main():
    """Main execution"""
    print("="*80)
    print("Fetching Actual Game Results for Backtest")
    print("="*80)
    
    # Load walkforward results
    print(f"\n📂 Loading {WALKFORWARD_FILE}...")
    df = pd.read_csv(WALKFORWARD_FILE)
    print(f"   Loaded {len(df):,} games")
    
    # Add actual results
    df_with_results = add_actual_results(df)
    
    # Save
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    df_with_results.to_csv(OUTPUT_FILE, index=False)
    
    file_size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"   Saved {len(df_with_results):,} games ({file_size_mb:.2f} MB)")
    
    # Summary
    matched = df_with_results['result_matched'].sum()
    print(f"\n📊 Summary:")
    print(f"   Total games: {len(df_with_results):,}")
    print(f"   Matched with results: {matched:,} ({matched/len(df_with_results)*100:.1f}%)")
    print(f"   Unmatched: {len(df_with_results) - matched:,}")
    
    if matched > 0:
        matched_df = df_with_results[df_with_results['result_matched'] == True]
        print(f"\n🎯 Matched games stats:")
        print(f"   Avg home score: {matched_df['home_score'].mean():.1f}")
        print(f"   Avg away score: {matched_df['away_score'].mean():.1f}")
        print(f"   Home win rate: {matched_df['home_won'].mean()*100:.1f}%")
    
    print(f"\n✅ Complete! Ready for P&L calculation.")
    print(f"\nNext step: python3 ml/calculate_backtest_pnl.py")


if __name__ == '__main__':
    main()
