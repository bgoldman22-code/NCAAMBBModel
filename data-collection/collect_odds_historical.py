#!/usr/bin/env python3
"""
Collect historical NCAA basketball odds from The Odds API.

This script fetches historical odds data for NCAA Men's Basketball games
and converts it to the CSV format required by the betting layer.

Usage:
    python3 data-collection/collect_odds_historical.py \
        --start-date 2023-11-01 \
        --end-date 2024-03-31 \
        --output-file data/markets/odds_ncaabb_2024.csv

The Odds API Documentation:
    https://the-odds-api.com/liveapi/guides/v4/

API Key:
    Set via environment variable: ODDS_API_KEY
    Or pass via --api-key argument (not recommended for production)

Rate Limiting:
    - Historical endpoint: 10 quota per request per region per market
    - Free tier: 500 requests/month
    - Monitor usage at: https://the-odds-api.com/account/
"""

import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

import requests
import pandas as pd


# The Odds API Configuration
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
SPORT_KEY = "basketball_ncaab"  # NCAA Men's Basketball
REGIONS = "us"  # US bookmakers
ODDS_FORMAT = "american"  # American odds format (-110, +150, etc.)
MARKETS = "h2h,spreads"  # Moneyline (h2h) and spreads


class OddsAPIError(Exception):
    """Custom exception for Odds API errors"""
    pass


def get_api_key() -> str:
    """
    Get API key from environment variable or prompt user.
    
    Returns:
        API key string
        
    Raises:
        ValueError: If no API key found
    """
    api_key = os.environ.get('ODDS_API_KEY')
    
    if not api_key:
        raise ValueError(
            "ODDS_API_KEY not found in environment variables.\n"
            "Set it with: export ODDS_API_KEY='your_api_key_here'\n"
            "Or pass via --api-key argument"
        )
    
    return api_key


def fetch_historical_odds(
    api_key: str,
    date: str,
    regions: str = REGIONS,
    markets: str = MARKETS,
    odds_format: str = ODDS_FORMAT
) -> Dict:
    """
    Fetch historical odds snapshot for a specific date.
    
    Args:
        api_key: The Odds API key
        date: ISO 8601 timestamp (e.g., "2023-11-15T12:00:00Z")
        regions: Regions to query (default: "us")
        markets: Markets to query (default: "h2h,spreads")
        odds_format: Odds format (default: "american")
        
    Returns:
        Dict containing snapshot data
        
    Raises:
        OddsAPIError: If API request fails
    """
    url = f"{ODDS_API_BASE_URL}/historical/sports/{SPORT_KEY}/odds"
    
    params = {
        'apiKey': api_key,
        'regions': regions,
        'markets': markets,
        'oddsFormat': odds_format,
        'date': date
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Check remaining quota
        remaining = response.headers.get('x-requests-remaining')
        used = response.headers.get('x-requests-used')
        
        print(f"   API quota used: {used}, remaining: {remaining}")
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise OddsAPIError("Invalid API key")
        elif response.status_code == 422:
            raise OddsAPIError(f"Invalid parameters: {response.text}")
        elif response.status_code == 429:
            raise OddsAPIError("Rate limit exceeded. Upgrade plan or wait.")
        else:
            raise OddsAPIError(f"HTTP {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        raise OddsAPIError(f"Request failed: {str(e)}")


def parse_odds_snapshot(snapshot_data: Dict, season: int) -> List[Dict]:
    """
    Parse odds snapshot into list of game records.
    
    Args:
        snapshot_data: Raw API response data
        season: Season year (e.g., 2024 for 2023-24 season)
        
    Returns:
        List of game dicts with standardized format
    """
    games = []
    
    for game in snapshot_data.get('data', []):
        home_team = game['home_team']
        away_team = game['away_team']
        commence_time = game['commence_time']
        
        # Parse commence time to game_day
        game_date = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
        game_day = game_date.strftime('%Y-%m-%d')
        
        # Initialize game record
        game_record = {
            'season': season,
            'game_day': game_day,
            'home_team': home_team,
            'away_team': away_team,
            'commence_time': commence_time,
            'close_spread': None,
            'home_ml': None,
            'away_ml': None,
            'close_total': None,
            'bookmakers': []
        }
        
        # Extract odds from bookmakers (use consensus or first available)
        for bookmaker in game.get('bookmakers', []):
            bm_name = bookmaker['key']
            
            for market in bookmaker.get('markets', []):
                market_key = market['key']
                
                if market_key == 'spreads':
                    # Extract spreads
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team:
                            game_record['close_spread'] = outcome.get('point')
                        elif outcome['name'] == away_team:
                            # Verify away spread is inverse of home
                            away_spread = outcome.get('point')
                
                elif market_key == 'h2h':
                    # Extract moneylines
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team:
                            game_record['home_ml'] = outcome.get('price')
                        elif outcome['name'] == away_team:
                            game_record['away_ml'] = outcome.get('price')
                
                elif market_key == 'totals':
                    # Extract totals (optional)
                    if 'point' in market.get('outcomes', [{}])[0]:
                        game_record['close_total'] = market['outcomes'][0]['point']
            
            game_record['bookmakers'].append(bm_name)
        
        # Only add game if we have at least spread or moneyline
        if game_record['close_spread'] is not None or game_record['home_ml'] is not None:
            games.append(game_record)
    
    return games


def generate_date_range(start_date: str, end_date: str, interval_hours: int = 24) -> List[str]:
    """
    Generate list of ISO timestamps for historical queries.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval_hours: Hours between snapshots (default: 24)
        
    Returns:
        List of ISO 8601 timestamps
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    timestamps = []
    current = start
    
    while current <= end:
        # Query at 12:00 UTC each day (captures closing lines)
        timestamp = current.replace(hour=12, minute=0, second=0)
        timestamps.append(timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'))
        current += timedelta(hours=interval_hours)
    
    return timestamps


def collect_historical_odds(
    api_key: str,
    start_date: str,
    end_date: str,
    season: int,
    output_file: Path,
    delay_seconds: float = 1.0
) -> pd.DataFrame:
    """
    Collect historical odds for date range and save to CSV.
    
    Args:
        api_key: The Odds API key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        season: Season year
        output_file: Path to output CSV
        delay_seconds: Delay between API calls (rate limiting)
        
    Returns:
        DataFrame with collected odds
    """
    print(f"\n{'='*80}")
    print(f"COLLECTING HISTORICAL NCAA BASKETBALL ODDS")
    print(f"{'='*80}")
    print(f"Date range: {start_date} → {end_date}")
    print(f"Season: {season}")
    print(f"Output: {output_file}")
    print(f"{'='*80}\n")
    
    # Generate date range
    timestamps = generate_date_range(start_date, end_date, interval_hours=24)
    print(f"📅 Generated {len(timestamps)} timestamps to query")
    
    all_games = []
    seen_games = set()  # Track unique games (avoid duplicates)
    
    for i, timestamp in enumerate(timestamps, 1):
        print(f"\n[{i}/{len(timestamps)}] Fetching odds for {timestamp}...")
        
        try:
            snapshot = fetch_historical_odds(api_key, timestamp)
            
            # Parse games
            games = parse_odds_snapshot(snapshot, season)
            
            # Deduplicate (same game may appear in multiple snapshots)
            for game in games:
                game_key = (game['game_day'], game['home_team'], game['away_team'])
                if game_key not in seen_games:
                    all_games.append(game)
                    seen_games.add(game_key)
            
            print(f"   Found {len(games)} games (total unique: {len(all_games)})")
            
            # Rate limiting
            if i < len(timestamps):
                time.sleep(delay_seconds)
        
        except OddsAPIError as e:
            print(f"   ⚠️  Error: {e}")
            if "rate limit" in str(e).lower():
                print(f"   Stopping collection due to rate limit")
                break
            continue
    
    print(f"\n✅ Collected {len(all_games)} unique games")
    
    # Convert to DataFrame
    if not all_games:
        print("⚠️  No games collected!")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_games)
    
    # Drop bookmakers column (just metadata)
    df = df.drop(columns=['bookmakers', 'commence_time'])
    
    # Reorder columns
    columns = ['season', 'game_day', 'home_team', 'away_team', 
               'close_spread', 'home_ml', 'away_ml', 'close_total']
    df = df[columns]
    
    # Sort by game_day
    df = df.sort_values('game_day')
    
    # Save to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"💾 Saved to {output_file}")
    
    # Summary statistics
    print(f"\n📊 Summary:")
    print(f"   Total games: {len(df)}")
    print(f"   Date range: {df['game_day'].min()} → {df['game_day'].max()}")
    print(f"   Games with spreads: {df['close_spread'].notna().sum()} ({df['close_spread'].notna().mean()*100:.1f}%)")
    print(f"   Games with moneylines: {df['home_ml'].notna().sum()} ({df['home_ml'].notna().mean()*100:.1f}%)")
    
    # Sample games
    print(f"\n📋 Sample games:")
    print(df.head(10).to_string(index=False))
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Collect historical NCAA basketball odds from The Odds API"
    )
    parser.add_argument(
        '--start-date',
        required=True,
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        '--end-date',
        required=True,
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        '--season',
        type=int,
        required=True,
        help="Season year (e.g., 2024 for 2023-24 season)"
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        required=True,
        help="Output CSV file path"
    )
    parser.add_argument(
        '--api-key',
        help="The Odds API key (or set ODDS_API_KEY env var)"
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help="Delay between API calls in seconds (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    try:
        if args.api_key:
            api_key = args.api_key
        else:
            api_key = get_api_key()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Validate dates
    try:
        datetime.fromisoformat(args.start_date)
        datetime.fromisoformat(args.end_date)
    except ValueError:
        print("❌ Error: Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    # Collect odds
    try:
        collect_historical_odds(
            api_key=api_key,
            start_date=args.start_date,
            end_date=args.end_date,
            season=args.season,
            output_file=args.output_file,
            delay_seconds=args.delay
        )
        
        print(f"\n✅ Collection complete!")
        
    except OddsAPIError as e:
        print(f"\n❌ API Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⚠️  Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
