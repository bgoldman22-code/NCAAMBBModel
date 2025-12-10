"""
Live Odds API Client for NCAA Basketball

Fetches moneyline odds and spreads from The Odds API (or similar providers).
Normalizes team names and returns data in a format compatible with Variant B.

Environment Variables Required:
    ODDS_API_KEY: API key for The Odds API
    ODDS_API_BASE_URL: Base URL (default: https://api.the-odds-api.com/v4)
    ODDS_PRIMARY_BOOK: Preferred sportsbook (default: fanduel)

Example:
    from data_collection.live_odds_client import fetch_today_moneyline_odds
    
    odds_df = fetch_today_moneyline_odds(date(2024, 3, 15))
    print(odds_df[['home_team', 'away_team', 'home_ml', 'away_ml']])
"""

import os
import sys
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import time

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Team name normalization (import from existing utilities if available)
# For now, we'll use a simple mapping aligned with historical data
TEAM_NAME_MAPPING = {
    # The Odds API names → Our database names
    'UConn': 'Connecticut',
    'UCONN': 'Connecticut',
    'Connecticut Huskies': 'Connecticut',
    'UNC': 'North Carolina',
    'North Carolina Tar Heels': 'North Carolina',
    'Duke Blue Devils': 'Duke',
    'Kansas Jayhawks': 'Kansas',
    'Kentucky Wildcats': 'Kentucky',
    'Louisville Cardinals': 'Louisville',
    'Syracuse Orange': 'Syracuse',
    'Michigan State Spartans': 'Michigan State',
    'Gonzaga Bulldogs': 'Gonzaga',
    'Villanova': 'Villanova Wildcats',
    'UCLA Bruins': 'UCLA',
    'Arizona Wildcats': 'Arizona',
    
    # Short names that need full mascots
    'South Carolina St': 'South Carolina State Bulldogs',
    'Grambling St': 'Grambling Tigers',
    'Grambling': 'Grambling Tigers',
    'Incarnate Word': 'Incarnate Word Cardinals',
    'BYU Cougars': 'Brigham Young Cougars',
    'BYU': 'Brigham Young Cougars',
    'Clemson': 'Clemson Tigers',
    'Michigan': 'Michigan Wolverines',
    'Texas': 'Texas Longhorns',
    'Southern': 'Southern Jaguars',
    
    # Add more as needed - this is a starter set
}


def normalize_team_name(raw_name: str) -> str:
    """
    Normalize team names from odds API to match our database.
    
    Args:
        raw_name: Team name from API (e.g., "UConn Huskies")
    
    Returns:
        Normalized name (e.g., "Connecticut")
    """
    # Try exact match first
    if raw_name in TEAM_NAME_MAPPING:
        return TEAM_NAME_MAPPING[raw_name]
    
    # Try removing common suffixes
    for suffix in [' Huskies', ' Tar Heels', ' Blue Devils', ' Jayhawks', 
                   ' Wildcats', ' Cardinals', ' Orange', ' Spartans', 
                   ' Bulldogs', ' Bruins', ' Tigers', ' Bears']:
        if raw_name.endswith(suffix):
            base_name = raw_name[:-len(suffix)].strip()
            if base_name in TEAM_NAME_MAPPING:
                return TEAM_NAME_MAPPING[base_name]
            return base_name
    
    # Return as-is if no mapping found
    return raw_name


def fetch_today_moneyline_odds(
    target_date: date,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    primary_book: Optional[str] = None,
    timeout: int = 30,
    lookahead_hours: int = 72
) -> pd.DataFrame:
    """
    Fetch moneyline odds for NCAA basketball games in the next N hours from target date.
    
    Args:
        target_date: Start date to fetch odds from
        api_key: The Odds API key (defaults to ODDS_API_KEY env var)
        base_url: API base URL (defaults to ODDS_API_BASE_URL env var)
        primary_book: Preferred sportsbook (defaults to ODDS_PRIMARY_BOOK env var)
        timeout: Request timeout in seconds
        lookahead_hours: Hours to look ahead from target date (default: 72)
    
    Returns:
        DataFrame with columns:
            - game_id: Unique game identifier
            - date: Game date
            - home_team: Normalized home team name
            - away_team: Normalized away team name
            - home_ml: Home moneyline (American odds)
            - away_ml: Away moneyline (American odds)
            - close_spread: Closing spread (if available)
            - book_name: Sportsbook name
            - last_update: Timestamp of last odds update
    
    Raises:
        ValueError: If API key is missing or invalid
        requests.RequestException: If API request fails
    """
    # Get config from env or args
    api_key = api_key or os.getenv('ODDS_API_KEY')
    base_url = base_url or os.getenv('ODDS_API_BASE_URL', 'https://api.the-odds-api.com/v4')
    primary_book = primary_book or os.getenv('ODDS_PRIMARY_BOOK', 'fanduel')
    
    if not api_key:
        raise ValueError(
            "ODDS_API_KEY environment variable not set. "
            "Get your key from https://the-odds-api.com/"
        )
    
    # The Odds API parameters
    sport = 'basketball_ncaab'
    regions = 'us'
    markets = 'h2h,spreads'  # h2h = moneylines, spreads = point spreads
    odds_format = 'american'
    
    # Build request URL
    url = f"{base_url}/sports/{sport}/odds/"
    params = {
        'apiKey': api_key,
        'regions': regions,
        'markets': markets,
        'oddsFormat': odds_format,
        'dateFormat': 'iso'
    }
    
    print(f"📡 Fetching NCAA basketball odds from The Odds API...")
    print(f"   Target date: {target_date}")
    print(f"   Lookahead: {lookahead_hours} hours")
    print(f"   Primary book: {primary_book}")
    
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        
        # Check API quota
        remaining = response.headers.get('x-requests-remaining')
        used = response.headers.get('x-requests-used')
        if remaining:
            print(f"   API quota: {used} used, {remaining} remaining")
        
        data = response.json()
        
        if not data:
            print(f"   ⚠️  No games found from API")
            return pd.DataFrame()
        
        # Parse games
        games = []
        target_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = target_datetime + timedelta(hours=lookahead_hours)
        
        for game in data:
            game_datetime = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00')).replace(tzinfo=None)
            game_date = game_datetime.date()
            
            # Filter to date range (target_date to target_date + lookahead_hours)
            if not (target_datetime <= game_datetime < end_datetime):
                continue
            
            game_id = game.get('id', '')
            home_team_raw = game.get('home_team', '')
            away_team_raw = game.get('away_team', '')
            
            # Normalize team names
            home_team = normalize_team_name(home_team_raw)
            away_team = normalize_team_name(away_team_raw)
            
            # Extract odds from bookmakers
            bookmakers = game.get('bookmakers', [])
            
            # Prefer primary book, fall back to first available
            selected_book = None
            for book in bookmakers:
                if book['key'] == primary_book:
                    selected_book = book
                    break
            
            if not selected_book and bookmakers:
                selected_book = bookmakers[0]  # Fall back to first book
            
            if not selected_book:
                print(f"   ⚠️  No odds found for {home_team} vs {away_team}")
                continue
            
            book_name = selected_book['title']
            last_update = selected_book['last_update']
            
            # Extract moneylines
            home_ml = None
            away_ml = None
            close_spread = None
            
            for market in selected_book.get('markets', []):
                if market['key'] == 'h2h':
                    # Moneylines
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team_raw:
                            home_ml = outcome['price']
                        elif outcome['name'] == away_team_raw:
                            away_ml = outcome['price']
                
                elif market['key'] == 'spreads':
                    # Spreads
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team_raw:
                            close_spread = outcome['point']
            
            if home_ml is None or away_ml is None:
                print(f"   ⚠️  Missing moneylines for {home_team} vs {away_team}")
                continue
            
            games.append({
                'game_id': game_id,
                'date': game_date,
                'home_team': home_team,
                'away_team': away_team,
                'home_ml': home_ml,
                'away_ml': away_ml,
                'close_spread': close_spread,
                'book_name': book_name,
                'last_update': last_update
            })
        
        df = pd.DataFrame(games)
        
        print(f"   ✅ Fetched {len(df)} games for {target_date}")
        
        if len(df) > 0:
            print(f"   Books used: {df['book_name'].nunique()} ({', '.join(df['book_name'].unique()[:3])})")
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API request failed: {e}")
        raise
    
    except Exception as e:
        print(f"   ❌ Error parsing odds data: {e}")
        raise


def load_team_name_mapping(mapping_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Load team name mapping from a CSV file.
    
    File format:
        api_name,database_name
        UConn,Connecticut
        UNC,North Carolina
    
    Args:
        mapping_file: Path to CSV file (optional)
    
    Returns:
        Dictionary mapping API names to database names
    """
    if mapping_file and mapping_file.exists():
        df = pd.read_csv(mapping_file)
        return dict(zip(df['api_name'], df['database_name']))
    
    return TEAM_NAME_MAPPING


def fetch_odds_with_fallback(
    target_date: date,
    fallback_books: Optional[List[str]] = None,
    lookahead_hours: int = 72
) -> pd.DataFrame:
    """
    Fetch odds with fallback to multiple books if primary fails.
    
    Args:
        target_date: Start date to fetch odds from
        fallback_books: List of book keys to try (default: fanduel, draftkings, betmgm)
        lookahead_hours: Hours to look ahead from target date (default: 72)
    
    Returns:
        DataFrame of odds, preferring first successful book
    """
    fallback_books = fallback_books or ['fanduel', 'draftkings', 'betmgm']
    
    for book in fallback_books:
        try:
            df = fetch_today_moneyline_odds(target_date, primary_book=book, lookahead_hours=lookahead_hours)
            if len(df) > 0:
                return df
        except Exception as e:
            print(f"   ⚠️  Failed to fetch from {book}: {e}")
            continue
    
    print(f"   ❌ All fallback books failed")
    return pd.DataFrame()


# CLI interface for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch live NCAA basketball odds')
    parser.add_argument('--date', type=str, default=None,
                        help='Date to fetch (YYYY-MM-DD, default: today)')
    parser.add_argument('--book', type=str, default='fanduel',
                        help='Primary sportsbook (default: fanduel)')
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = date.today()
    
    # Fetch odds
    try:
        df = fetch_today_moneyline_odds(target_date, primary_book=args.book)
        
        if len(df) == 0:
            print(f"\n⚠️  No games found for {target_date}")
            sys.exit(1)
        
        print(f"\n📊 Sample of {len(df)} games:\n")
        print(df[['date', 'home_team', 'away_team', 'home_ml', 'away_ml', 'close_spread', 'book_name']].head(10).to_string(index=False))
        
        print(f"\n✅ Successfully fetched odds for {len(df)} games")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
