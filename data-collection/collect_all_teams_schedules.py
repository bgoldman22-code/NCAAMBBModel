"""
Collect schedules for ALL teams in our walkforward predictions.

This will give us comprehensive game result coverage for our backtest.
"""

import cbbpy.mens_scraper as s
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import time
from tqdm import tqdm

# Output directory
DATA_DIR = Path(__file__).parent.parent / 'data' / 'historical'
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_teams_from_predictions():
    """Get all unique teams from walkforward predictions"""
    pred_path = Path(__file__).parent.parent / 'data' / 'walkforward_results_full.csv'
    df = pd.read_csv(pred_path)
    
    all_teams = pd.concat([df['home_team'], df['away_team']]).unique()
    return sorted(all_teams)


def collect_team_schedule(team_name: str, season: int = 2024) -> pd.DataFrame:
    """
    Collect schedule for a single team.
    
    Args:
        team_name: Team name as it appears in our data
        season: Season ending year (2024 = 2023-24 season)
        
    Returns:
        DataFrame of team's games
    """
    try:
        # CBBpy uses team names that might differ slightly
        # Try exact name first
        schedule = s.get_team_schedule(team=team_name, season=season)
        
        if schedule is not None and len(schedule) > 0:
            return schedule
        
        # If that fails, try with some variations
        variations = [
            team_name.replace('State', 'St.'),
            team_name.replace('St.', 'State'),
            team_name.replace('&', 'and'),
        ]
        
        for variant in variations:
            if variant != team_name:
                try:
                    schedule = s.get_team_schedule(team=variant, season=season)
                    if schedule is not None and len(schedule) > 0:
                        return schedule
                except:
                    continue
        
        return None
        
    except Exception as e:
        return None


def collect_all_schedules(season: int = 2024):
    """
    Collect schedules for all teams in our predictions.
    
    Args:
        season: Season ending year (2024 = 2023-24 season)
    """
    print(f"\n{'='*80}")
    print(f"COLLECTING SCHEDULES FOR ALL TEAMS - {season-1}-{season} SEASON")
    print(f"{'='*80}\n")
    
    # Get teams from predictions
    teams = get_teams_from_predictions()
    print(f"📊 Teams to collect: {len(teams)}")
    
    # Collect schedules
    all_schedules = []
    successful = []
    failed = []
    
    print(f"\n🏀 Collecting team schedules...")
    for team in tqdm(teams, desc="Teams"):
        schedule = collect_team_schedule(team, season)
        
        if schedule is not None and len(schedule) > 0:
            all_schedules.append(schedule)
            successful.append(team)
        else:
            failed.append(team)
        
        # Be polite to the server
        time.sleep(0.5)
    
    # Combine all schedules
    if all_schedules:
        combined_df = pd.concat(all_schedules, ignore_index=True)
        
        # Save to CSV
        output_file = DATA_DIR / f'schedules_{season}_complete.csv'
        combined_df.to_csv(output_file, index=False)
        
        print(f"\n{'='*80}")
        print(f"COLLECTION COMPLETE")
        print(f"{'='*80}")
        print(f"  ✅ Successful: {len(successful)} teams")
        print(f"  ❌ Failed: {len(failed)} teams")
        print(f"  📊 Total games: {len(combined_df)}")
        print(f"  💾 Saved to: {output_file}")
        
        if failed:
            print(f"\n❌ Failed teams ({len(failed)}):")
            for team in failed[:20]:
                print(f"  - {team}")
            if len(failed) > 20:
                print(f"  ... and {len(failed) - 20} more")
        
        # Save metadata
        metadata = {
            'season': season,
            'collection_date': datetime.now().isoformat(),
            'teams_requested': len(teams),
            'teams_successful': len(successful),
            'teams_failed': len(failed),
            'total_games': len(combined_df),
            'successful_teams': successful,
            'failed_teams': failed
        }
        
        metadata_file = DATA_DIR / f'metadata_{season}_complete.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n📋 Summary saved to: {metadata_file}")
        
        # Game date range
        if 'game_day' in combined_df.columns:
            combined_df['parsed_date'] = pd.to_datetime(combined_df['game_day'], format='%B %d, %Y', errors='coerce')
            print(f"\n📅 Game date range:")
            print(f"  {combined_df['parsed_date'].min().date()} → {combined_df['parsed_date'].max().date()}")
        
        print(f"\n{'='*80}")
        
    else:
        print("\n❌ No schedules collected!")


if __name__ == "__main__":
    collect_all_schedules(season=2024)
