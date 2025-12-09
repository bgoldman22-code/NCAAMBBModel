"""
Collect historical game data using CBBpy
Fetches schedules, results, and basic stats for backtesting

NOTE: CBBpy has some bugs with get_games_season and get_games_range.
We'll use a more reliable approach: get all team schedules and merge them.
"""

import cbbpy.mens_scraper as s
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import time
from tqdm import tqdm

# Create data directory
DATA_DIR = Path(__file__).parent.parent / 'data' / 'historical'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Seasons to collect (format: ending year)
SEASONS = [2022, 2023, 2024, 2025]

# Major D1 teams to collect (we'll get their schedules which includes all their opponents)
# This is more reliable than get_games_season which has bugs
MAJOR_TEAMS = [
    'Duke', 'North Carolina', 'Kansas', 'Kentucky', 'Gonzaga',
    'UCLA', 'Arizona', 'Michigan', 'Villanova', 'Texas',
    'Houston', 'Purdue', 'Alabama', 'Tennessee', 'Baylor',
    'UConn', 'Michigan St.', 'Virginia', 'Auburn', 'Arkansas',
    'Creighton', 'Xavier', 'Marquette', 'Saint Mary\'s', 'San Diego St.',
    'Florida Atlantic', 'Memphis', 'Iowa St.', 'TCU', 'Texas Tech'
]

def collect_season_schedules(season):
    """
    Collect game schedules for a season by getting team schedules
    
    Args:
        season (int): Season ending year (e.g., 2022 for 2021-22 season)
    """
    print(f"\n{'='*60}")
    print(f"Collecting schedules for {season-1}-{season} season...")
    print(f"{'='*60}\n")
    
    all_schedules = []
    failed_teams = []
    
    try:
        # Collect schedules from major teams
        for team in tqdm(MAJOR_TEAMS, desc="Collecting team schedules"):
            try:
                schedule = s.get_team_schedule(team=team, season=season)
                all_schedules.append(schedule)
                time.sleep(0.5)  # Be nice to ESPN's servers
            except Exception as e:
                failed_teams.append(team)
                print(f"  ⚠️  Failed to get {team}: {str(e)}")
                continue
        
        if not all_schedules:
            print("❌ No schedules collected")
            return False
        
        # Combine all schedules
        combined_schedules = pd.concat(all_schedules, ignore_index=True)
        
        # Remove duplicates (same game appears in both teams' schedules)
        # Keep only games with game_id (completed games)
        games = combined_schedules[combined_schedules['game_id'].notna()].copy()
        games = games.drop_duplicates(subset=['game_id'])
        
        # Save schedule data
        schedule_path = DATA_DIR / f'schedules_{season}.csv'
        games.to_csv(schedule_path, index=False)
        print(f"\n✅ Saved schedules: {len(games)} unique games")
        
        # Summary stats
        print(f"\n📊 Season {season-1}-{season} Summary:")
        print(f"   Total unique games: {len(games)}")
        print(f"   Teams sampled: {len(MAJOR_TEAMS) - len(failed_teams)}/{len(MAJOR_TEAMS)}")
        if failed_teams:
            print(f"   Failed teams: {', '.join(failed_teams)}")
        
        # Save metadata
        metadata = {
            'season': season,
            'collected_at': datetime.now().isoformat(),
            'total_games': len(games),
            'teams_sampled': len(MAJOR_TEAMS) - len(failed_teams),
            'failed_teams': failed_teams,
            'data_type': 'schedules_only'
        }
        
        metadata_path = DATA_DIR / f'metadata_{season}.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"❌ Error collecting season {season}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def collect_team_schedule(team_name, season):
    """
    Example: Collect a specific team's schedule
    Useful for testing or getting current season data
    """
    try:
        schedule = s.get_team_schedule(team=team_name, season=season)
        return schedule
    except Exception as e:
        print(f"Error collecting schedule for {team_name}: {str(e)}")
        return None

def main():
    """Main data collection workflow"""
    print("\n🏀 NCAA Basketball Historical Data Collection")
    print("Using CBBpy to collect game data from ESPN")
    print(f"Seasons: {SEASONS[0]-1}-{SEASONS[0]} through {SEASONS[-1]-1}-{SEASONS[-1]}")
    
    success_count = 0
    
    for season in SEASONS:
        if collect_season_schedules(season):
            success_count += 1
        
        # Be respectful - add delay between seasons
        if season != SEASONS[-1]:
            print("\nWaiting 5 seconds before next season...")
            time.sleep(5)
    
    print("\n" + "="*60)
    print(f"✅ Collection complete: {success_count}/{len(SEASONS)} seasons successful")
    print(f"📁 Data saved to: {DATA_DIR}")
    print("="*60)
    
    # Show what was collected
    print("\n📊 Collected files:")
    for file in sorted(DATA_DIR.glob("*.csv")):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   {file.name}: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
