#!/usr/bin/env python3
"""
Market integration module for NCAA Basketball betting.

This module handles loading and processing sports betting market data
(spreads, moneylines, totals) and joining it with KenPom/ESPN game data.

Expected Market Data CSV Schema
================================

Place odds files in: data/markets/odds_ncaabb_YEAR.csv

Required columns:
- season (int): Season year (e.g., 2024 for 2023-24 season)
- game_day (str): Game date in YYYY-MM-DD format
- home_team (str): Home team name (ESPN-style naming)
- away_team (str): Away team name (ESPN-style naming)
- close_spread (float): Closing spread from home team's perspective
                        Negative = home is favorite (e.g., -5.5 means home favored by 5.5)
                        Positive = home is underdog (e.g., +3.5 means home getting 3.5 points)
- home_ml (int): Home team moneyline in American odds format (e.g., -150, +200)
- away_ml (int): Away team moneyline in American odds format

Optional columns:
- close_total (float): Closing over/under total points
- open_spread (float): Opening spread (for line movement analysis)
- open_total (float): Opening total

Example CSV:
    season,game_day,home_team,away_team,close_spread,home_ml,away_ml,close_total
    2024,2023-11-15,Duke,Michigan St.,-7.5,-300,+240,145.5
    2024,2023-11-20,Kansas,Kentucky,-3.5,-165,+140,149.0

Notes:
- Team names should match ESPN naming convention (same as in merged_games_*.csv)
- If team names don't match exactly, the join will fail (TEAM_NAME_MAP not applied here)
- Spreads are always from home team perspective
- Moneylines are in American odds format (negative = favorite, positive = underdog)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union


def normalize_odds_team_name(name: str) -> str:
    """
    Normalize team names from The Odds API to ESPN format.
    
    The Odds API includes mascots (e.g., "Duke Blue Devils")
    ESPN uses just the school name (e.g., "Duke")
    
    Args:
        name: Team name from The Odds API
        
    Returns:
        Normalized team name matching ESPN format
    """
    # Common mascots to remove (from The Odds API format)
    mascots = [
        'Aggies', 'Aztecs', 'Badgers', 'Bears', 'Bearcats', 'Bengals', 'Big Green',
        'Billikens', 'Bison', 'Black Knights', 'Blackbirds', 'Blue Devils', 'Blue Raiders',
        'Bobcats', 'Boilermakers', 'Braves', 'Broncos', 'Bruins', 'Buccaneers', 'Bulldogs',
        'Bulls', 'Cardinals', 'Catamounts', 'Cavaliers', 'Chanticleers', 'Chippewas',
        'Colonels', 'Commodores', 'Cougars', 'Cowboys', 'Crimson Tide', 'Crusaders',
        'Cyclones', 'Demon Deacons', 'Dons', 'Ducks', 'Dukes', 'Eagles', 'Engineers',
        'Explorers', 'Falcons', 'Fighting Hawks', 'Fighting Illini', 'Fighting Irish',
        'Flames', 'Flyers', 'Friars', 'Gators', 'Gaels', 'Golden Bears', 'Golden Eagles',
        'Golden Flashes', 'Golden Gophers', 'Golden Grizzlies', 'Golden Hurricane',
        'Great Danes', 'Green Wave', 'Greyhounds', 'Grizzlies', 'Hawkeyes', 'Highlanders',
        'Hilltoppers', 'Hokies', 'Hornets', 'Huskies', 'Hurricanes', 'Jaguars', 'Jaspers',
        'Jayhawks', 'Knights', 'Lumberjacks', 'Lions', 'Lobos', 'Longhorns', 'Matadors',
        'Mavericks', 'Mean Green', 'Midshipmen', 'Miners', 'Minutemen', 'Monarchs',
        'Mountaineers', 'Musketeers', 'Mustangs', 'Nittany Lions', 'Norse', 'Orange',
        'Orangemen', 'Owls', 'Panthers', 'Patriots', 'Peacocks', 'Penguins', 'Phoenix',
        'Pirates', 'Pioneers', 'Ragin Cajuns', 'Raiders', 'Rams', 'Ramblers', 'Rattlers',
        'Ravens', 'Razorbacks', 'Rebels', 'Red Flash', 'Red Raiders', 'Red Storm',
        'Redbirds', 'Redhawks', 'Retrievers', 'Riverhawks', 'Roadrunners', 'Rockets',
        'Runn Rebels', 'Running Rebels', 'Salukis', 'Scarlet Knights', 'Seahawks',
        'Seawolves', 'Seminoles', 'Shockers', 'Skyhawks', 'Sooners', 'Spartans',
        'Spiders', 'Stags', 'Sun Devils', 'Tar Heels', 'Terrapins', 'Terriers',
        'Thunderbirds', 'Tigers', 'Titans', 'Trojans', 'Utes', 'Vandals', 'Vikings',
        'Volunteers', 'Waves', 'Wildcats', 'Wolfpack', 'Wolverines', 'Wonders',
        'Yellow Jackets', 'Zips', 'Screaming Eagles', 'Leathernecks', 'Riverhawks',
        'Lopes', 'Hatters'
    ]
    
    # Remove mascot if present
    for mascot in mascots:
        if name.endswith(' ' + mascot):
            name = name[:-len(mascot)-1]
            break
    
    # Handle special cases
    special_cases = {
        'UConn': 'Connecticut',
        'Miami (FL)': 'Miami',
        'Miami (OH)': 'Miami (OH)',
        "Saint Mary's (CA)": "Saint Mary's",
        'Southern California': 'USC',
        'Central Florida': 'UCF',
        'Louisiana State': 'LSU',
        'Texas Christian': 'TCU',
        'Southern Methodist': 'SMU',
        'Brigham Young': 'BYU',
        'Texas-San Antonio': 'UTSA',
        'Nevada-Las Vegas': 'UNLV',
        'Mississippi': 'Ole Miss',
    }
    
    if name in special_cases:
        name = special_cases[name]
    
    return name


def load_markets(markets_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load NCAA market data (spreads/moneylines) from a CSV.
    
    Args:
        markets_path: Path to markets CSV file
        
    Returns:
        DataFrame with market odds data
        
    Required columns:
        - season, game_day, home_team, away_team
        - close_spread, home_ml, away_ml
        
    Raises:
        FileNotFoundError: If markets file doesn't exist
        ValueError: If required columns are missing
    """
    markets_path = Path(markets_path)
    
    if not markets_path.exists():
        raise FileNotFoundError(f"Markets file not found: {markets_path}")
    
    df = pd.read_csv(markets_path)
    
    # Validate required columns
    required_cols = ['season', 'game_day', 'home_team', 'away_team', 
                     'close_spread', 'home_ml', 'away_ml']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in markets file: {missing_cols}")
    
    # Normalize team names (remove mascots)
    df['home_team'] = df['home_team'].apply(normalize_odds_team_name)
    df['away_team'] = df['away_team'].apply(normalize_odds_team_name)
    
    # Convert game_day to ESPN format (e.g., "November 06, 2023")
    df['game_day'] = pd.to_datetime(df['game_day']).dt.strftime('%B %d, %Y')
    
    print(f"✅ Loaded {len(df):,} games with market data from {markets_path.name}")
    print(f"   Seasons: {sorted(df['season'].unique())}")
    
    return df


def american_to_prob(american_odds: float) -> float:
    """
    Convert American odds to implied probability (no vig adjustment).
    
    Args:
        american_odds: American odds (e.g., -150, +200)
                      Negative = favorite, Positive = underdog
                      
    Returns:
        Implied probability as decimal (0.0 to 1.0)
        
    Examples:
        >>> american_to_prob(-150)  # Favorite
        0.6
        >>> american_to_prob(+200)  # Underdog
        0.333...
    """
    if pd.isna(american_odds):
        return np.nan
    
    if american_odds < 0:
        # Favorite: -odds / (-odds + 100)
        return abs(american_odds) / (abs(american_odds) + 100)
    else:
        # Underdog: 100 / (odds + 100)
        return 100 / (american_odds + 100)


def join_markets_with_merged(
    merged_df: pd.DataFrame,
    markets_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join merged KenPom/ESPN game data with market data.
    
    Matching strategy:
    - Uses season + game_day + team/opponent alignment
    - Assumes merged_df['team'] is the home team (or perspective team)
    - Matches merged_df['team'] with markets_df['home_team']
    - Matches merged_df['opponent'] with markets_df['away_team']
    
    Args:
        merged_df: Merged KenPom + ESPN data (from data/merged/)
        markets_df: Market odds data (from data/markets/)
        
    Returns:
        DataFrame with both game features and market lines
        Adds columns:
            - close_spread: Spread from home (team) perspective
            - home_ml, away_ml: Moneyline odds
            - home_implied_prob, away_implied_prob: Implied probabilities
            - close_total: Over/under (if present)
            
    Notes:
        - This assumes merged_df['team'] corresponds to the home side
        - If your data has explicit home/away flags, this may need adjustment
        - Unmatched games will be dropped (inner join)
    """
    # Ensure game_day formats match
    merged_df = merged_df.copy()
    markets_df = markets_df.copy()
    
    # Normalize game_day format (merged data has "November 06, 2023" format)
    if 'game_day' in merged_df.columns:
        # Already in "Month DD, YYYY" format from merged data
        pass
    
    # Join on season, game_day, and team alignment
    # Assumption: merged_df['team'] = home, merged_df['opponent'] = away
    joined = merged_df.merge(
        markets_df,
        left_on=['season', 'game_day', 'team', 'opponent'],
        right_on=['season', 'game_day', 'home_team', 'away_team'],
        how='inner'
    )
    
    # Calculate implied probabilities
    joined['home_implied_prob'] = joined['home_ml'].apply(american_to_prob)
    joined['away_implied_prob'] = joined['away_ml'].apply(american_to_prob)
    
    # Report match statistics
    total_merged = len(merged_df)
    matched = len(joined)
    match_rate = (matched / total_merged * 100) if total_merged > 0 else 0
    
    print(f"\n📊 Market Join Results:")
    print(f"   Merged games: {total_merged:,}")
    print(f"   Market games: {len(markets_df):,}")
    print(f"   Matched:      {matched:,} ({match_rate:.1f}%)")
    print(f"   Unmatched:    {total_merged - matched:,}")
    
    if matched == 0:
        print("\n⚠️  WARNING: No games matched!")
        print("   Check that:")
        print("   1. Team names in markets CSV match ESPN names in merged data")
        print("   2. game_day formats are compatible")
        print("   3. Seasons overlap between datasets")
    
    return joined


def calculate_market_edge(
    model_spread: float,
    close_spread: float,
    model_win_prob: float,
    home_implied_prob: float,
    away_implied_prob: float
) -> dict:
    """
    Calculate betting edges for spread and moneyline.
    
    Args:
        model_spread: Model's predicted margin (from home team perspective)
        close_spread: Market closing spread (from home team perspective)
        model_win_prob: Model's predicted win probability for home team
        home_implied_prob: Market implied probability for home team
        away_implied_prob: Market implied probability for away team
        
    Returns:
        Dict with edge calculations:
            - edge_spread: Points of value vs spread
            - home_edge: Home ML probability edge
            - away_edge: Away ML probability edge
            - best_bet: 'home_ml', 'away_ml', 'home_spread', 'away_spread', or None
    """
    # Spread edge (positive = model likes home more than market)
    edge_spread = model_spread - close_spread
    
    # Moneyline edges (positive = model gives higher probability than market)
    home_edge = model_win_prob - home_implied_prob
    away_edge = (1 - model_win_prob) - away_implied_prob
    
    # Determine best bet (highest positive edge)
    best_bet = None
    max_edge = 0
    
    if abs(edge_spread) > 2:  # Arbitrary threshold for spread consideration
        if edge_spread > 0:
            # Model likes home more than spread suggests
            best_bet = 'home_spread'
            max_edge = edge_spread
        else:
            # Model likes away more than spread suggests
            best_bet = 'away_spread'
            max_edge = abs(edge_spread)
    
    if home_edge > max_edge:
        best_bet = 'home_ml'
        max_edge = home_edge
    
    if away_edge > max_edge:
        best_bet = 'away_ml'
        max_edge = away_edge
    
    return {
        'edge_spread': edge_spread,
        'home_edge': home_edge,
        'away_edge': away_edge,
        'best_bet': best_bet,
        'max_edge': max_edge
    }


if __name__ == "__main__":
    # Simple test
    import sys
    
    print("="*80)
    print("MARKET INTEGRATION MODULE TEST")
    print("="*80)
    
    # Test American odds conversion
    print("\n📊 Testing American odds conversion:")
    test_odds = [-150, +200, -110, +300, -500]
    for odds in test_odds:
        prob = american_to_prob(odds)
        print(f"   {odds:>6} → {prob:.4f} ({prob*100:.2f}%)")
    
    # Check if sample market data exists
    sample_market_path = Path('data/markets/odds_ncaabb_2024.csv')
    if sample_market_path.exists():
        print(f"\n✅ Found sample market data: {sample_market_path}")
        markets_df = load_markets(sample_market_path)
        print(f"   Columns: {list(markets_df.columns)}")
        print(f"\n   Sample rows:")
        print(markets_df.head().to_string())
    else:
        print(f"\n⚠️  No sample market data found at {sample_market_path}")
        print("   Expected schema documented in module docstring")
    
    print("\n✅ Module loaded successfully")
