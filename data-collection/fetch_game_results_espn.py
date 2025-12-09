#!/usr/bin/env python3
"""
Fetch game results using ESPN API directly (much faster than CBBpy).
"""

import pandas as pd
import requests
from pathlib import Path
import time
from tqdm import tqdm
from datetime import datetime

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
WALKFORWARD_FILE = DATA_DIR / "walkforward_results_full.csv"
OUTPUT_FILE = DATA_DIR / "walkforward_results_with_scores.csv"

def fetch_espn_scoreboard(date_str: str) -> list:
    """
    Fetch scoreboard from ESPN for a specific date.
    
    Args:
        date_str: Date in format 'YYYYMMDD'
        
    Returns:
        List of games
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
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
            
            # Get teams (competitors[0] could be home or away)
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
            if comp.get('status', {}).get('type', {}).get('completed') != True:
                continue
            
            games.append({
                'home_team': home_team['team']['displayName'],
                'away_team': away_team['team']['displayName'],
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'date': date_str
            })
        
        return games
        
    except Exception as e:
        print(f"Error fetching {date_str}: {str(e)}")
        return []


def normalize_team_name(team: str) -> str:
    """Normalize team name for matching"""
    team = team.strip()
    
    # Common mappings
    mappings = {
        'UConn Huskies': 'UConn',
        'Connecticut Huskies': 'UConn',
        'Miami Hurricanes': 'Miami',
        'Miami (FL) Hurricanes': 'Miami',
        'LSU Tigers': 'LSU',
        'Ole Miss Rebels': 'Ole Miss',
        'USC Trojans': 'USC',
        'VCU Rams': 'VCU',
        'SMU Mustangs': 'SMU',
        'UCF Knights': 'UCF',
        'BYU Cougars': 'BYU',
        'UNLV Rebels': 'UNLV',
        'UMass Minutemen': 'UMass',
        'TCU Horned Frogs': 'TCU',
    }
    
    # Check direct mapping
    if team in mappings:
        return mappings[team]
    
    # Remove common suffixes
    suffixes = [
        ' Aggies', ' Aztecs', ' Badgers', ' Bears', ' Bearcats', ' Beavers',
        ' Bengals', ' Billikens', ' Bison', ' Blue Devils', ' Blue Jays',
        ' Bobcats', ' Boilermakers', ' Bonnies', ' Bruins', ' Buccaneers',
        ' Buffaloes', ' Bulldogs', ' Bulls', ' Catamounts', ' Cavaliers',
        ' Chanticleers', ' Chippewas', ' Cougars', ' Cowboys', ' Crimson',
        ' Crimson Tide', ' Crusaders', ' Cyclones', ' Demons', ' Demon Deacons',
        ' Eagles', ' Explorers', ' Falcons', ' Fighting Irish', ' Flames',
        ' Flyers', ' Friars', ' Gators', ' Golden Eagles', ' Golden Gophers',
        ' Golden Hurricanes', ' Governors', ' Grizzlies', ' Hardrockers',
        ' Hatters', ' Hawks', ' Hawkeyes', ' Hilltoppers', ' Hokies',
        ' Hoosiers', ' Hornets', ' Horned Frogs', ' Huskies', ' Hurricanes',
        ' Illini', ' Jaguars', ' Jayhawks', ' Knights', ' Lancers', ' Lions',
        ' Lobos', ' Longhorns', ' Lumberjacks', ' Minutemen', ' Monarchs',
        ' Mountaineers', ' Musketeers', ' Mustangs', ' Nittany Lions',
        ' Orangemen', ' Orange', ' Owls', ' Panthers', ' Patriots', ' Peacocks',
        ' Phoenix', ' Pirates', ' Privateers', ' Quakers', ' Racers',
        ' Rainbow Warriors', ' Ramblers', ' Rams', ' Ravens', ' Razorbacks',
        ' Red Raiders', ' Red Storm', ' Redhawks', ' Rebels', ' Retrievers',
        ' Rockets', ' Rough Riders', ' Runnin\' Rebels', ' Salukis',
        ' Scarlet Knights', ' Seminoles', ' Shockers', ' Sooners', ' Spartans',
        ' Spiders', ' Sun Devils', ' Sycamores', ' Tar Heels', ' Terrapins',
        ' Terriers', ' Thundering Herd', ' Tigers', ' Titans', ' Tritons',
        ' Trojans', ' Utes', ' Vandals', ' Vikings', ' Violets', ' Volunteers',
        ' Waves', ' Wildcats', ' Wolfpack', ' Wolverines', ' Yellow Jackets',
        ' Zips', ' 49ers', ' Colonials', ' Fighting Hawks', ' Golden Flashes',
    ]
    
    for suffix in suffixes:
        if team.endswith(suffix):
            return team[:-len(suffix)]
    
    return team


def match_teams(row, espn_games):
    """Match our game to ESPN result"""
    our_home = normalize_team_name(row['home_team'])
    our_away = normalize_team_name(row['away_team'])
    
    for game in espn_games:
        espn_home = normalize_team_name(game['home_team'])
        espn_away = normalize_team_name(game['away_team'])
        
        if our_home == espn_home and our_away == espn_away:
            return {
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'matched': True
            }
    
    return None


def add_espn_results(walkforward_df: pd.DataFrame) -> pd.DataFrame:
    """Add actual results from ESPN API"""
    print(f"\n🏀 Fetching results from ESPN API...")
    print(f"Total games: {len(walkforward_df):,}")
    
    # Parse dates
    walkforward_df['date'] = pd.to_datetime(walkforward_df['date'])
    unique_dates = sorted(walkforward_df['date'].dt.strftime('%Y%m%d').unique())
    
    print(f"Unique dates: {len(unique_dates)}")
    
    # Fetch all dates
    espn_cache = {}
    
    for date_str in tqdm(unique_dates, desc="Fetching ESPN scoreboards"):
        games = fetch_espn_scoreboard(date_str)
        espn_cache[date_str] = games
        time.sleep(0.2)  # Be nice to ESPN
    
    # Add result columns
    walkforward_df['home_score'] = None
    walkforward_df['away_score'] = None
    walkforward_df['result_matched'] = False
    
    print(f"\n🔗 Matching games...")
    
    matched_count = 0
    for idx, row in tqdm(walkforward_df.iterrows(), total=len(walkforward_df), desc="Matching"):
        date_str = row['date'].strftime('%Y%m%d')
        espn_games = espn_cache.get(date_str, [])
        
        match = match_teams(row, espn_games)
        
        if match:
            walkforward_df.at[idx, 'home_score'] = match['home_score']
            walkforward_df.at[idx, 'away_score'] = match['away_score']
            walkforward_df.at[idx, 'result_matched'] = True
            matched_count += 1
    
    print(f"\n✅ Matched {matched_count}/{len(walkforward_df)} games ({matched_count/len(walkforward_df)*100:.1f}%)")
    
    # Calculate outcomes
    matched_df = walkforward_df[walkforward_df['result_matched'] == True].copy()
    
    if len(matched_df) > 0:
        matched_df['actual_margin'] = matched_df['home_score'] - matched_df['away_score']
        matched_df['home_won'] = (matched_df['actual_margin'] > 0).astype(int)
        matched_df['home_covered'] = (
            matched_df['actual_margin'] + matched_df['close_spread'] > 0
        ).astype(int)
        
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'actual_margin'] = matched_df['actual_margin']
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'home_won'] = matched_df['home_won']
        walkforward_df.loc[walkforward_df['result_matched'] == True, 'home_covered'] = matched_df['home_covered']
    
    return walkforward_df


def main():
    print("="*80)
    print("Fetching Game Results from ESPN API")
    print("="*80)
    
    # Load walkforward data
    print(f"\n📂 Loading {WALKFORWARD_FILE}...")
    df = pd.read_csv(WALKFORWARD_FILE)
    print(f"   Loaded {len(df):,} games")
    
    # Add results
    df_with_results = add_espn_results(df)
    
    # Save
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    df_with_results.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n📊 Summary:")
    matched = df_with_results['result_matched'].sum()
    print(f"   Total: {len(df_with_results):,}")
    print(f"   Matched: {matched:,} ({matched/len(df_with_results)*100:.1f}%)")
    
    if matched > 0:
        m = df_with_results[df_with_results['result_matched'] == True]
        print(f"\n🎯 Results:")
        print(f"   Avg home score: {m['home_score'].mean():.1f}")
        print(f"   Avg away score: {m['away_score'].mean():.1f}")
        print(f"   Home win rate: {m['home_won'].mean()*100:.1f}%")
    
    print(f"\n✅ Complete!")
    print(f"\nNext: python3 ml/calculate_backtest_pnl.py")


if __name__ == '__main__':
    main()
