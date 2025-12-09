"""
Fetch current season (2025-26) NCAA basketball game results.

This script scrapes completed games from ESPN or sports-reference to build
rolling in-season stats for live predictions.

Data Sources:
    Primary: ESPN Scoreboard API (free, no auth required)
    Fallback: Sports-Reference (requires parsing HTML)

Output:
    data/ncaabb/current_season/games_2025-26.csv

Columns:
    date, season, home_team, away_team, home_score, away_score,
    neutral_site, tournament

Usage:
    # Fetch all games from season start to today
    python3 data-collection/fetch_current_season_games.py
    
    # Fetch specific date range
    python3 data-collection/fetch_current_season_games.py --start 2025-11-01 --end 2025-12-08
    
    # Update only recent games (last 7 days)
    python3 data-collection/fetch_current_season_games.py --recent 7

Environment:
    No API keys required (uses public ESPN API)

Author: AI Assistant
Date: 2025-12-08
"""

import requests
import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import json

# Season configuration
CURRENT_SEASON = 2026  # NCAA season is labeled by end year (2025-26 = 2026)
SEASON_START = "2025-11-04"  # Typical NCAA season start (early November)

# ESPN API configuration
ESPN_SCOREBOARD_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
ESPN_TEAM_MAPPING = {
    # Map ESPN team names to our database format
    # Add mappings as needed
}

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between requests


def normalize_team_name(espn_name: str) -> str:
    """
    Normalize ESPN team names to match our database format.
    
    Args:
        espn_name: Team name from ESPN API
        
    Returns:
        Normalized team name matching database format
    """
    # Direct mapping if exists
    if espn_name in ESPN_TEAM_MAPPING:
        return ESPN_TEAM_MAPPING[espn_name]
    
    # Standard normalization rules
    name = espn_name.strip()
    
    # Remove common prefixes
    prefixes = ['University of ', 'College of ', 'The ']
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    
    # State abbreviations
    name = name.replace(' St.', ' State')
    name = name.replace(' St ', ' State ')
    
    # Handle special cases
    replacements = {
        'Miami (FL)': 'Miami Florida',
        'Miami (OH)': 'Miami Ohio',
        'USC': 'Southern California',
        'TCU': 'Texas Christian',
        'SMU': 'Southern Methodist',
        'BYU': 'Brigham Young',
        'VCU': 'Virginia Commonwealth',
        'LSU': 'Louisiana State',
        'UCF': 'Central Florida',
        'UNLV': 'Nevada Las Vegas',
        'UConn': 'Connecticut',
    }
    
    for old, new in replacements.items():
        if old in name:
            name = name.replace(old, new)
    
    return name


def fetch_games_for_date(date_str: str) -> List[Dict]:
    """
    Fetch all completed NCAA basketball games for a specific date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        List of game dictionaries
    """
    games = []
    
    try:
        # ESPN API expects date in YYYYMMDD format
        date_param = date_str.replace('-', '')
        
        params = {
            'dates': date_param,
            'limit': 500,  # Get all games
            'groups': '50',  # NCAA Division I Men's Basketball
        }
        
        print(f"  Fetching games for {date_str}...", end='')
        response = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        events = data.get('events', [])
        
        for event in events:
            # Only process completed games
            status = event.get('status', {})
            if status.get('type', {}).get('state') != 'post':
                continue  # Skip in-progress or scheduled games
            
            competitions = event.get('competitions', [])
            if not competitions:
                continue
            
            comp = competitions[0]
            competitors = comp.get('competitors', [])
            
            if len(competitors) != 2:
                continue
            
            # Extract team data
            home_team = None
            away_team = None
            
            for team in competitors:
                team_data = team.get('team', {})
                team_name = normalize_team_name(team_data.get('displayName', ''))
                score = int(team.get('score', 0))
                is_home = team.get('homeAway') == 'home'
                
                if is_home:
                    home_team = team_name
                    home_score = score
                else:
                    away_team = team_name
                    away_score = score
            
            if not home_team or not away_team:
                continue
            
            # Determine if neutral site
            neutral = comp.get('neutralSite', False)
            
            # Check if tournament game
            notes = comp.get('notes', [])
            tournament = any('tournament' in note.get('headline', '').lower() for note in notes)
            
            game = {
                'date': date_str,
                'season': CURRENT_SEASON,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'neutral_site': neutral,
                'tournament': tournament,
            }
            
            games.append(game)
        
        print(f" ✅ {len(games)} completed games")
        
    except requests.exceptions.RequestException as e:
        print(f" ❌ Error: {e}")
    except Exception as e:
        print(f" ❌ Parsing error: {e}")
    
    return games


def fetch_games_date_range(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch games for a range of dates.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with all games
    """
    print(f"📅 Fetching games from {start_date} to {end_date}...")
    
    all_games = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        games = fetch_games_for_date(date_str)
        all_games.extend(games)
        
        current += timedelta(days=1)
        time.sleep(REQUEST_DELAY)  # Rate limiting
    
    if not all_games:
        print("⚠️  No games found")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_games)
    print(f"✅ Fetched {len(df)} total games")
    
    return df


def load_existing_games(output_path: Path) -> pd.DataFrame:
    """Load existing current season games if file exists."""
    if output_path.exists():
        print(f"📂 Loading existing games from {output_path}")
        df = pd.read_csv(output_path)
        print(f"   Found {len(df)} existing games")
        return df
    return pd.DataFrame()


def merge_and_dedupe(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """
    Merge new games with existing, removing duplicates.
    
    Args:
        existing: Existing games DataFrame
        new: New games DataFrame
        
    Returns:
        Merged and deduplicated DataFrame
    """
    if existing.empty:
        return new
    
    if new.empty:
        return existing
    
    # Concatenate
    combined = pd.concat([existing, new], ignore_index=True)
    
    # Remove duplicates based on date + teams
    before = len(combined)
    combined = combined.drop_duplicates(
        subset=['date', 'home_team', 'away_team'],
        keep='last'  # Keep newer data
    )
    after = len(combined)
    
    if before > after:
        print(f"🔄 Removed {before - after} duplicate games")
    
    # Sort by date
    combined = combined.sort_values('date').reset_index(drop=True)
    
    return combined


def main():
    parser = argparse.ArgumentParser(description='Fetch current season NCAA basketball games')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--recent', type=int, help='Fetch last N days only')
    parser.add_argument('--output', type=str, 
                       default='data/ncaabb/current_season/games_2025-26.csv',
                       help='Output CSV path')
    parser.add_argument('--season', type=int, default=CURRENT_SEASON,
                       help='Season year (end year, default: 2026 for 2025-26)')
    
    args = parser.parse_args()
    
    # Determine date range
    today = datetime.now().strftime('%Y-%m-%d')
    
    if args.recent:
        start_date = (datetime.now() - timedelta(days=args.recent)).strftime('%Y-%m-%d')
        end_date = today
        print(f"📅 Fetching recent games (last {args.recent} days)")
    elif args.start and args.end:
        start_date = args.start
        end_date = args.end
    elif args.start:
        start_date = args.start
        end_date = today
    else:
        # Default: fetch entire season to date
        start_date = SEASON_START
        end_date = today
        print(f"📅 Fetching full season {CURRENT_SEASON-1}-{CURRENT_SEASON % 100}")
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing games
    existing_df = load_existing_games(output_path)
    
    # Fetch new games
    new_df = fetch_games_date_range(start_date, end_date)
    
    if new_df.empty and existing_df.empty:
        print("❌ No games to save")
        sys.exit(1)
    
    # Merge and deduplicate
    final_df = merge_and_dedupe(existing_df, new_df)
    
    # Save
    final_df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(final_df)} games to {output_path}")
    
    # Summary stats
    if not final_df.empty:
        print(f"\n📊 Summary:")
        print(f"   Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        print(f"   Total games: {len(final_df)}")
        print(f"   Unique teams: {len(set(final_df['home_team']) | set(final_df['away_team']))}")
        print(f"   Neutral site games: {final_df['neutral_site'].sum()}")
        print(f"   Tournament games: {final_df['tournament'].sum()}")


if __name__ == '__main__':
    main()
