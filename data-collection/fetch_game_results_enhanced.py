#!/usr/bin/env python3
"""
Enhanced game result fetcher with comprehensive team database.

Improvements over previous version:
1. Uses comprehensive team name database (200+ teams with all variations)
2. Fuzzy matching with configurable threshold
3. Expanded date window (±1 day) for games listed on different dates
4. ESPN game IDs for reliable matching
"""

import pandas as pd
import requests
from pathlib import Path
import time
import sys
from tqdm import tqdm
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# Add ml/ to path for team database
sys.path.insert(0, str(Path(__file__).parent.parent / 'ml'))
from team_database import normalize_team_name as db_normalize_team

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
WALKFORWARD_FILE = DATA_DIR / "walkforward_results_full.csv"
OUTPUT_FILE = DATA_DIR / "walkforward_results_with_scores.csv"


def fuzzy_match_score(str1: str, str2: str) -> float:
    """
    Calculate similarity score between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Float between 0 and 1 (1 = perfect match)
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def fetch_espn_scoreboard(date_str: str) -> list:
    """
    Fetch all games from ESPN for a specific date.
    
    Args:
        date_str: Date in format 'YYYYMMDD'
        
    Returns:
        List of game dictionaries
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    params = {
        'dates': date_str,
        'limit': 500
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'events' not in data:
            return []
        
        games = []
        for event in data['events']:
            if 'competitions' not in event or len(event['competitions']) == 0:
                continue
                
            comp = event['competitions'][0]
            if 'competitors' not in comp or len(comp['competitors']) < 2:
                continue
            
            # Extract home and away teams
            home_team = None
            away_team = None
            
            for team in comp['competitors']:
                if team.get('homeAway') == 'home':
                    home_team = team
                elif team.get('homeAway') == 'away':
                    away_team = team
            
            if not home_team or not away_team:
                continue
            
            # Only include completed games
            status = comp.get('status', {}).get('type', {})
            if status.get('completed') != True:
                continue
            
            # Extract scores
            try:
                home_score = int(home_team.get('score', 0))
                away_score = int(away_team.get('score', 0))
            except (ValueError, TypeError):
                continue
            
            games.append({
                'espn_id': event.get('id', ''),
                'home_team_raw': home_team['team']['displayName'],
                'away_team_raw': away_team['team']['displayName'],
                'home_team_normalized': db_normalize_team(home_team['team']['displayName']),
                'away_team_normalized': db_normalize_team(away_team['team']['displayName']),
                'home_score': home_score,
                'away_score': away_score,
                'date': date_str
            })
        
        return games
        
    except requests.exceptions.RequestException as e:
        # Silently fail for individual dates
        return []
    except Exception as e:
        print(f"  ⚠️  Error parsing {date_str}: {str(e)}")
        return []


def match_game_to_espn(row: pd.Series, espn_games: list, fuzzy_threshold: float = 0.85) -> dict:
    """
    Match a game from our dataset to ESPN results.
    
    Strategy:
    1. Normalize both team names using comprehensive database
    2. Try exact match on normalized names
    3. Fall back to fuzzy matching if no exact match
    
    Args:
        row: Row from our walkforward dataset
        espn_games: List of ESPN games for relevant dates
        fuzzy_threshold: Minimum similarity score for fuzzy match (default 0.85 = 85%)
        
    Returns:
        Match dictionary or None
    """
    # Normalize our team names using database
    our_home_normalized = db_normalize_team(row['home_team'])
    our_away_normalized = db_normalize_team(row['away_team'])
    
    best_match = None
    best_score = 0
    
    for espn_game in espn_games:
        espn_home = espn_game['home_team_normalized']
        espn_away = espn_game['away_team_normalized']
        
        # Strategy 1: Exact match on normalized names (best case)
        if our_home_normalized == espn_home and our_away_normalized == espn_away:
            return {
                'home_score': espn_game['home_score'],
                'away_score': espn_game['away_score'],
                'matched': True,
                'match_type': 'exact',
                'match_score': 1.0,
                'espn_id': espn_game['espn_id'],
                'espn_home': espn_game['home_team_raw'],
                'espn_away': espn_game['away_team_raw']
            }
        
        # Strategy 2: Fuzzy match
        home_similarity = fuzzy_match_score(our_home_normalized, espn_home)
        away_similarity = fuzzy_match_score(our_away_normalized, espn_away)
        combined_score = (home_similarity + away_similarity) / 2
        
        if combined_score > best_score and combined_score >= fuzzy_threshold:
            best_score = combined_score
            best_match = {
                'home_score': espn_game['home_score'],
                'away_score': espn_game['away_score'],
                'matched': True,
                'match_type': 'fuzzy',
                'match_score': combined_score,
                'espn_id': espn_game['espn_id'],
                'espn_home': espn_game['home_team_raw'],
                'espn_away': espn_game['away_team_raw'],
                'our_home': row['home_team'],
                'our_away': row['away_team']
            }
    
    return best_match


def fetch_and_match_results(walkforward_df: pd.DataFrame, 
                            fuzzy_threshold: float = 0.85,
                            date_buffer_days: int = 1) -> pd.DataFrame:
    """
    Fetch ESPN results and match to our games.
    
    Args:
        walkforward_df: DataFrame with our predictions
        fuzzy_threshold: Minimum similarity for fuzzy matches
        date_buffer_days: Days before/after to search (default ±1)
        
    Returns:
        DataFrame with results added
    """
    print(f"\n{'='*80}")
    print("ENHANCED GAME RESULT MATCHING")
    print(f"{'='*80}")
    print(f"\nConfiguration:")
    print(f"  Fuzzy match threshold: {fuzzy_threshold*100:.0f}%")
    print(f"  Date buffer: ±{date_buffer_days} day(s)")
    print(f"  Team database: 200+ teams with variations")
    
    # Parse dates
    walkforward_df['date'] = pd.to_datetime(walkforward_df['date'])
    
    # Build comprehensive date list with buffer
    dates_to_fetch = set()
    for game_date in walkforward_df['date'].unique():
        date_obj = pd.to_datetime(game_date)
        for delta in range(-date_buffer_days, date_buffer_days + 1):
            buffered_date = date_obj + timedelta(days=delta)
            dates_to_fetch.add(buffered_date.strftime('%Y%m%d'))
    
    dates_to_fetch = sorted(dates_to_fetch)
    
    print(f"\n📅 Date Coverage:")
    print(f"  Games span: {len(walkforward_df['date'].unique())} unique dates")
    print(f"  With ±{date_buffer_days} buffer: {len(dates_to_fetch)} dates to fetch")
    
    # Fetch all ESPN data
    print(f"\n📡 Fetching ESPN scoreboards...")
    espn_cache = {}
    
    for date_str in tqdm(dates_to_fetch, desc="Fetching dates"):
        games = fetch_espn_scoreboard(date_str)
        if games:
            espn_cache[date_str] = games
        time.sleep(0.15)  # Rate limiting
    
    total_espn_games = sum(len(games) for games in espn_cache.values())
    print(f"  ✅ Fetched {total_espn_games:,} completed games from ESPN")
    
    # Initialize result columns
    walkforward_df['home_score'] = None
    walkforward_df['away_score'] = None
    walkforward_df['result_matched'] = False
    walkforward_df['match_type'] = None
    walkforward_df['match_score'] = None
    walkforward_df['espn_id'] = None
    walkforward_df['espn_home'] = None
    walkforward_df['espn_away'] = None
    
    # Match games
    print(f"\n🔗 Matching {len(walkforward_df):,} games...")
    
    matched_count = 0
    exact_matches = 0
    fuzzy_matches = 0
    
    for idx, row in tqdm(walkforward_df.iterrows(), total=len(walkforward_df), desc="Matching"):
        game_date = pd.to_datetime(row['date'])
        
        # Collect all ESPN games in date window
        relevant_espn_games = []
        for delta in range(-date_buffer_days, date_buffer_days + 1):
            search_date = (game_date + timedelta(days=delta)).strftime('%Y%m%d')
            if search_date in espn_cache:
                relevant_espn_games.extend(espn_cache[search_date])
        
        if not relevant_espn_games:
            continue
        
        # Try to match
        match = match_game_to_espn(row, relevant_espn_games, fuzzy_threshold)
        
        if match:
            walkforward_df.at[idx, 'home_score'] = match['home_score']
            walkforward_df.at[idx, 'away_score'] = match['away_score']
            walkforward_df.at[idx, 'result_matched'] = True
            walkforward_df.at[idx, 'match_type'] = match['match_type']
            walkforward_df.at[idx, 'match_score'] = match['match_score']
            walkforward_df.at[idx, 'espn_id'] = match['espn_id']
            walkforward_df.at[idx, 'espn_home'] = match['espn_home']
            walkforward_df.at[idx, 'espn_away'] = match['espn_away']
            
            matched_count += 1
            if match['match_type'] == 'exact':
                exact_matches += 1
            else:
                fuzzy_matches += 1
    
    # Calculate game outcomes
    matched_df = walkforward_df[walkforward_df['result_matched'] == True].copy()
    
    if len(matched_df) > 0:
        matched_df['actual_margin'] = matched_df['home_score'] - matched_df['away_score']
        matched_df['home_won'] = (matched_df['actual_margin'] > 0).astype(int)
        matched_df['home_covered'] = (
            matched_df['actual_margin'] + matched_df['close_spread'] > 0
        ).astype(int)
        
        # Copy back to main dataframe
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'actual_margin'] = matched_df['actual_margin']
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'home_won'] = matched_df['home_won']
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'home_covered'] = matched_df['home_covered']
    
    # Print results
    print(f"\n{'='*80}")
    print("MATCHING RESULTS")
    print(f"{'='*80}")
    print(f"  Total games: {len(walkforward_df):,}")
    print(f"  Matched: {matched_count:,} ({matched_count/len(walkforward_df)*100:.1f}%)")
    print(f"    ├─ Exact matches: {exact_matches:,}")
    print(f"    └─ Fuzzy matches: {fuzzy_matches:,}")
    print(f"  Unmatched: {len(walkforward_df) - matched_count:,}")
    
    if len(matched_df) > 0:
        print(f"\n📊 Matched Game Statistics:")
        print(f"  Avg home score: {matched_df['home_score'].mean():.1f}")
        print(f"  Avg away score: {matched_df['away_score'].mean():.1f}")
        print(f"  Home win rate: {matched_df['home_won'].mean()*100:.1f}%")
        print(f"  Avg margin: {matched_df['actual_margin'].mean():+.1f}")
        
        print(f"\n📋 Sample Matches:")
        for _, row in matched_df.head(5).iterrows():
            print(f"  {row['home_team']} vs {row['away_team']}")
            print(f"    → ESPN: {row['espn_home']} vs {row['espn_away']}")
            print(f"    → Score: {int(row['home_score'])}-{int(row['away_score'])} " +
                  f"({row['match_type']}, {row['match_score']:.2%})")
    
    return walkforward_df


def main():
    """Main execution"""
    print(f"{'='*80}")
    print("ENHANCED GAME RESULT FETCHER")
    print(f"{'='*80}")
    
    # Load walkforward data
    print(f"\n📂 Loading {WALKFORWARD_FILE}...")
    df = pd.read_csv(WALKFORWARD_FILE)
    print(f"  Loaded {len(df):,} games")
    print(f"  Date range: {df['date'].min()} → {df['date'].max()}")
    
    # Fetch and match
    df_with_results = fetch_and_match_results(
        df,
        fuzzy_threshold=0.85,  # 85% similarity required
        date_buffer_days=1     # Search ±1 day
    )
    
    # Save results
    print(f"\n💾 Saving results...")
    df_with_results.to_csv(OUTPUT_FILE, index=False)
    
    file_size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"  ✅ Saved to {OUTPUT_FILE}")
    print(f"  File size: {file_size_mb:.2f} MB")
    
    # Summary
    matched = df_with_results['result_matched'].sum()
    print(f"\n{'='*80}")
    print("COMPLETE")
    print(f"{'='*80}")
    print(f"  Match rate: {matched}/{len(df_with_results)} ({matched/len(df_with_results)*100:.1f}%)")
    print(f"\nNext step:")
    print(f"  python3 ml/calculate_backtest_pnl.py")


if __name__ == '__main__':
    main()
