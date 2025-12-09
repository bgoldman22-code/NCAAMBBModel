#!/usr/bin/env python3
"""
Merge KenPom efficiency ratings with game schedules.

This script combines:
- Game schedules from CBBpy (team, opponent, date, result)
- KenPom efficiency ratings (AdjO, AdjD, AdjT, SOS, etc.)

Creates a unified dataset with both team and opponent metrics for each game.
"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
SCHEDULE_DIR = DATA_DIR / "historical"
KENPOM_DIR = DATA_DIR / "kenpom"
OUTPUT_DIR = DATA_DIR / "merged"

# Team name mappings (ESPN to KenPom)
TEAM_NAME_MAP = {
    # Common mismatches between ESPN and KenPom
    'UConn': 'Connecticut',
    'Miami (FL)': 'Miami FL',
    'Miami Hurricanes': 'Miami FL',
    'Miami-Florida': 'Miami FL',
    'Ole Miss': 'Mississippi',
    'Ole Miss Rebels': 'Mississippi',
    'USC': 'Southern California',
    'USC Trojans': 'Southern California',
    'LSU': 'Louisiana State',
    'LSU Tigers': 'Louisiana State',
    'VCU': 'Virginia Commonwealth',
    'SMU': 'Southern Methodist',
    'UCF': 'Central Florida',
    'BYU': 'Brigham Young',
    'UNLV': 'Nevada Las Vegas',
    'St. John\'s': 'St. John\'s',
    'Saint John\'s': 'St. John\'s',
    'UMass': 'Massachusetts',
    'UTEP': 'UTEP',
    'UAB': 'UAB',
    'UTSA': 'UT San Antonio',
    'UNC': 'North Carolina',
    'Pitt': 'Pittsburgh',
    'UVA': 'Virginia',
    'VT': 'Virginia Tech',
    'NC State': 'North Carolina St.',
    # State abbreviations (ESPN uses "State", KenPom uses "St.")
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
    # App State special case
    'App State': 'Appalachian St.',
    'App St.': 'Appalachian St.',
    # NC State variations - KenPom uses "N.C. State"
    'NC State': 'N.C. State',
    'North Carolina State': 'N.C. State',
    'NC State Wolfpack': 'N.C. State',
    # SMU
    'SMU': 'Southern Methodist',
    'SMU Mustangs': 'Southern Methodist',
    # Stanford
    'Stanford Cardinal': 'Stanford',
    # Alabama
    'Alabama Crimson Tide': 'Alabama',
    # Oklahoma
    'Oklahoma St. Cowboys': 'Oklahoma St.',
    'Oklahoma State Cowboys': 'Oklahoma St.',
    # Oregon
    'Oregon St. Beavers': 'Oregon St.',
    'Oregon State Beavers': 'Oregon St.',
    # Mount St. Mary's
    'Mount St. Mary\'s Mountaineers': 'Mount St. Mary\'s',
    # Florida schools - MUST be exact matches
    'Florida': 'Florida',
    'Florida Gators': 'Florida',
    'Florida International': 'FIU',
    'Florida Tech': 'Florida Tech',
    'Florida A&M': 'Florida A&M',
    'Florida Atlantic': 'Florida Atlantic',
    'Florida Gulf Coast': 'Florida Gulf Coast',
    'Florida St.': 'Florida St.',
    'North Florida': 'North Florida',
    'South Florida': 'South Florida',
    # San Diego schools
    'San Diego State': 'San Diego St.',
    'San Diego State Aztecs': 'San Diego St.',
    'UC San Diego': 'UC San Diego',
    'San Diego': 'San Diego',
    # Hawaii
    'Hawai\'i': 'Hawaii',
    'Hawai\'i Rainbow Warriors': 'Hawaii',
    # TCU
    'TCU': 'TCU',
    'TCU Horned Frogs': 'TCU',
    # Oklahoma schools
    'Oklahoma': 'Oklahoma',
    'Oklahoma Sooners': 'Oklahoma',
    # Texas schools (MUST be before "Texas" entry to match correctly)
    'Texas Longhorns': 'Texas',
    'Texas Tech': 'Texas Tech',
    'Texas Tech Red Raiders': 'Texas Tech',
    'Texas A&M Corpus Christi': 'Texas A&M Corpus Chris',
    'Texas Rio Grande Valley': 'UT Rio Grande Valley',
    'North Texas': 'North Texas',
    'Texas Southern': 'Texas Southern',
    # California schools
    'Cal': 'California',
    'California Golden': 'California',
    'Cal Poly': 'Cal Poly',
    'California Baptist': 'Cal Baptist',
    'Cal St. Bakersfield': 'Cal St. Bakersfield',
    'Cal St. Fullerton': 'Cal St. Fullerton',
    'Cal St. Northridge': 'Cal St. Northridge',
    # UC System schools
    'UC Irvine': 'UC Irvine',
    'UC Riverside': 'UC Riverside',
    'UC Davis': 'UC Davis',
    'UC Santa Barbara': 'UC Santa Barbara',
    # Common schools with mascots removed
    'Arkansas-Pine Bluff Golden Lions': 'Arkansas Pine Bluff',
    'Buffalo Bulls': 'Buffalo',
    'Canisius Golden Griffins': 'Canisius',
    'DePaul Blue Demons': 'DePaul',
    'Denver Pioneers': 'Denver',
    'Gardner-Webb Runnin\'': 'Gardner Webb',
    'Alabama St.': 'Alabama St.',
    'Alcorn St.': 'Alcorn St.',
    'Arkansas St.': 'Arkansas St.',
    'Cleveland St.': 'Cleveland St.',
    'Delaware St.': 'Delaware St.',
    'Denver Pioneers': 'Denver',
    'Harvard Crimson': 'Harvard',
    'Idaho St.': 'Idaho St.',
    'Idaho State Bengals': 'Idaho St.',
    'Illinois': 'Illinois',
    'Illinois Fighting Illini': 'Illinois',
    'Illinois St.': 'Illinois St.',
    'Indiana St.': 'Indiana St.',
    'Iowa St.': 'Iowa St.',
    'Jacksonville St.': 'Jacksonville St.',
    'Kansas City Roos': 'Kansas City',
    'Kent State Golden Flashes': 'Kent St.',
    'Long Beach St.': 'Long Beach St.',
    'Marshall Thundering Herd': 'Marshall',
    'Miami (OH) RedHawks': 'Miami OH',
    'Montana Grizzlies': 'Montana',
    'Montana St.': 'Montana St.',
    'Murray St.': 'Murray St.',
    'New Mexico Lobos': 'New Mexico',
    'Nicholls Colonels': 'Nicholls',
    'North Florida Ospreys': 'North Florida',
    'Old Dominion Monarchs': 'Old Dominion',
    'Pennsylvania Quakers': 'Pennsylvania',
    'Pepperdine Waves': 'Pepperdine',
    'Purdue Fort Wayne Mastodons': 'Purdue Fort Wayne',
    'Rider Broncs': 'Rider',
    'San Diego Toreros': 'San Diego',
    'San Francisco Dons': 'San Francisco',
    'Southern Indiana Screaming Eagles': 'Southern Indiana',
    'Southern Jaguars': 'Southern',
    'Stonehill Skyhawks': 'Stonehill',
    'Texas A&M-Corpus Christi Islanders': 'Texas A&M Corpus Chris',
    'Toledo Rockets': 'Toledo',
    'UAlbany Great Danes': 'Albany',
    'UC Riverside Highlanders': 'UC Riverside',
    'UMass Lowell River Hawks': 'UMass Lowell',
    'UT Rio Grande Valley Vaqueros': 'UT Rio Grande Valley',
    'Utah Tech Trailblazers': 'Utah Tech',
    'Utah Utes': 'Utah',
    'Vanderbilt Commodores': 'Vanderbilt',
    'Western Kentucky Hilltoppers': 'Western Kentucky',
    'Wichita State Shockers': 'Wichita St.',
    'Long Beach St.': 'Long Beach St.',
    'Montana St.': 'Montana St.',
    'Murray St.': 'Murray St.',
    'McNeese': 'McNeese St.',
    'Grambling': 'Grambling St.',
    'Grambling Tigers': 'Grambling St.',
    'Maine Black': 'Maine',
    'Marquette Golden': 'Marquette',
    'Middle Tennessee': 'Middle Tennessee',
    'Mississippi Valley St.': 'Mississippi Valley St.',
    'Mount St. Mary\'s': 'Mount St. Mary\'s',
    # Other common variations
    'SMU': 'Southern Methodist',
    'American University': 'American',
    'American U': 'American',
    'N Carolina': 'North Carolina',
    'UW-Green Bay': 'Green Bay',
    'Ark-Little Rock': 'Little Rock',
    'Arkansas-Pine Bluff': 'Arkansas Pine Bluff',
    'Bethune-Cookman': 'Bethune Cookman',
    'Central Connecticut St.': 'Central Connecticut',
    'Charleston': 'Charleston',
    'Charleston Southern': 'Charleston Southern',
    'East Texas A&M Lions': 'Texas A&M Commerce',
    'Eastern Kentucky': 'Eastern Kentucky',
    'Green Bay': 'Green Bay',
    'Grand Canyon': 'Grand Canyon',
    'Holy Cross': 'Holy Cross',
    'Houston Christian': 'Houston Baptist',
    'James Madison': 'James Madison',
    'Kansas City': 'Kansas City',
    'Long Island University': 'LIU',
    'Loyola Chicago': 'Loyola Chicago',
    'Loyola Marymount': 'Loyola Marymount',
    'Loyola Marymount Lions': 'Loyola Marymount',
    'Loyola Maryland': 'Loyola MD',
    'Maryland Eastern Shore': 'MD Eastern Shore',
    'Maryland-Eastern Shore': 'MD Eastern Shore',
    'South Carolina Upstate': 'USC Upstate',
    'Seattle U': 'Seattle',
    'Queens University': 'Queens',
    'Lindenwood': 'Lindenwood',
    'Lipscomb': 'Lipscomb',
    'Longwood': 'Longwood',
    'Merrimack': 'Merrimack',
    'Monmouth': 'Monmouth',
    'Little Rock': 'Arkansas Little Rock',
    'UT Martin': 'Tennessee Martin',
    'Southeast Missouri St.': 'Southeast Missouri',
    'SIU Edwardsville': 'SIU Edwardsville',
    'Omaha': 'Nebraska Omaha',
    'Omaha Mavericks': 'Nebraska Omaha',
    'Coastal Georgia': 'Coastal Carolina',
    'Stony Brook': 'Stony Brook',
    # Southern schools - be specific!
    'Southern': 'Southern',
    'Southern Illinois': 'Southern Illinois',
    'Southern Indiana': 'Southern Indiana',
    'Southern Miss': 'Southern Miss',
    'Southern Utah': 'Southern Utah',
    'Southern Utah Thunderbirds': 'Southern Utah',
    'Charleston Southern': 'Charleston Southern',
    'Georgia Southern': 'Georgia Southern',
    # Portland schools
    'Portland': 'Portland',
    'Portland Pilots': 'Portland',
    'Portland Vikings': 'Portland St.',
    'Portland St.': 'Portland St.',
    'Portland State': 'Portland St.',
    # Other common teams
    'Oral Roberts': 'Oral Roberts',
    'Oral Roberts Golden Eagles': 'Oral Roberts',
    'Vermont': 'Vermont',
    'Vermont Catamounts': 'Vermont',
    'Radford': 'Radford',
    'Radford Highlanders': 'Radford',
    'Lehigh': 'Lehigh',
    'Lehigh Mountain Hawks': 'Lehigh',
    'Robert Morris': 'Robert Morris',
    'Robert Morris Colonials': 'Robert Morris',
    'Oakland': 'Oakland',
    'Oakland Golden Grizzlies': 'Oakland',
    'UNC Wilmington': 'UNC Wilmington',
    'UNC Wilmington Seahawks': 'UNC Wilmington',
}

def normalize_team_name(name):
    """
    Normalize team names for matching between ESPN and KenPom.
    
    Args:
        name: Team name from ESPN
        
    Returns:
        Normalized team name
    """
    if pd.isna(name):
        return name
    
    # Start with original name
    name = name.strip()
    
    # FIRST: Apply manual mappings for exact matches (before suffix removal)
    if name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[name]
    
    # SECOND: Remove common mascot suffixes
    suffixes = [
        ' Wildcats', ' Tigers', ' Bulldogs', ' Blue Devils', ' Tar Heels',
        ' Cardinals', ' Spartans', ' Wolverines', ' Buckeyes', ' Hoosiers',
        ' Jayhawks', ' Terrapins', ' Illini', ' Boilermakers', ' Nittany Lions',
        ' Badgers', ' Golden Gophers', ' Cornhuskers', ' Hawkeyes', ' Huskers',
        ' Scarlet Knights', ' Bruins', ' Sun Devils', ' Bears',
        ' Ducks', ' Trojans', ' Huskies', ' Cougars', ' Eagles', ' Friars',
        ' Pirates', ' Musketeers', ' Hoyas', ' Red Storm', ' Orange',
        ' Black Knights', ' Fighting Camels', ' Runnin\' Bulldogs',
        ' Hokies', ' Fighting Irish', ' Yellow Jackets', ' Demon Deacons',
        ' Wolfpack', ' Seminoles', ' Cavaliers', ' Panthers', ' Titans',
        ' Red Raiders', ' Razorbacks', ' Greyhounds', ' Volunteers',
        ' Paladins', ' Golden Eagles', ' Peacocks', ' Texans', ' Seawolves',
        ' Mean Green', ' Flyers', ' Gaels', ' Miners', ' Lumberjacks',
        ' Buffaloes', ' Wolf Pack', ' Patriots', ' Rebels', ' Broncos',
        ' Rams', ' Aggies', ' Knights', ' Owls', ' Penguins',
        ' Dolphins', ' Explorers', ' Big Green', ' Bison', ' Blue Hens',
        ' Screaming Eagles', ' Redhawks', ' Black Bears', ' Terriers',
        ' Crimson Tide', ' Mountaineers', ' Cowboys', ' Mustangs', ' Cardinal',
        ' Bearcats', ' Leopards', ' Phoenix', ' Beavers', ' Seahawks',
        ' Pride', ' Royals', ' Gamecocks', ' Dukes', ' Flames', ' Ramblers',
        ' Lopes', ' Governors', ' Redbirds', ' Sycamores', ' Cyclones',
        ' Beach', ' Lancers', ' Bisons', ' Lions', ' Jaspers', ' Warriors',
        ' Blue Raiders', ' Delta Devils', ' Hawks', ' Bobcats', ' Racers',
        ' Braves', ' Stags', ' Rattlers', ' Gators', ' Chippewas', ' Buccaneers',
        ' 49ers', ' Mocs', ' Vikings', ' Raiders', ' Big Red', ' Bluejays',
        ' Dragons', ' Dukes', ' Colonels', ' Griffins', ' Mariner',
        ' Silverswords', ' Zips', ' Hornets', ' Red Wolves', ' Golden Lions',
        ' Roadrunners', ' Matadors', ' Golden', ' Fighting'
    ]
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break
    
    # THIRD: Check mapping again after suffix removal
    if name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[name]
    
    # FOURTH: Handle "State" -> "St." conversion for remaining cases
    if ' State' in name and name not in TEAM_NAME_MAP.values():
        name = name.replace(' State', ' St.')
    
    return name

def load_kenpom_ratings(season):
    """
    Load KenPom ratings for a season.
    
    Args:
        season: Year (e.g., 2022 for 2021-22 season)
        
    Returns:
        DataFrame with team ratings
    """
    file_path = KENPOM_DIR / f"kenpom_ratings_{season}.csv"
    
    if not file_path.exists():
        print(f"⚠️  KenPom file not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    
    # Normalize team names
    df['TeamName'] = df['TeamName'].apply(normalize_team_name)
    
    # Select key columns for modeling
    columns = [
        'TeamName', 'AdjEM', 'AdjOE', 'AdjDE', 'AdjTempo', 
        'Tempo', 'Luck', 'SOS', 'SOSO', 'SOSD',
        'RankAdjEM', 'RankAdjOE', 'RankAdjDE'
    ]
    
    # Only keep columns that exist
    available_cols = [col for col in columns if col in df.columns]
    df = df[available_cols].copy()
    
    return df

def load_schedule(season):
    """
    Load game schedule for a season.
    
    Args:
        season: Year (e.g., 2022 for 2021-22 season)
        
    Returns:
        DataFrame with schedule
    """
    file_path = SCHEDULE_DIR / f"schedules_{season}.csv"
    
    if not file_path.exists():
        print(f"⚠️  Schedule file not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    
    # Normalize team names
    df['team_normalized'] = df['team'].apply(normalize_team_name)
    df['opponent_normalized'] = df['opponent'].apply(normalize_team_name)
    
    return df

def merge_season_data(season):
    """
    Merge schedule and KenPom data for a season.
    
    Args:
        season: Year (e.g., 2022 for 2021-22 season)
        
    Returns:
        DataFrame with merged data
    """
    print(f"\nProcessing {season-1}-{str(season)[-2:]} season...")
    
    # Load data
    schedule = load_schedule(season)
    kenpom = load_kenpom_ratings(season)
    
    if schedule is None or kenpom is None:
        print(f"❌ Missing data for season {season}")
        return None
    
    print(f"  Schedule: {len(schedule)} games")
    print(f"  KenPom: {len(kenpom)} teams")
    
    # Merge team ratings
    merged = schedule.merge(
        kenpom,
        left_on='team_normalized',
        right_on='TeamName',
        how='left',
        suffixes=('', '_team')
    )
    
    # Merge opponent ratings
    merged = merged.merge(
        kenpom,
        left_on='opponent_normalized',
        right_on='TeamName',
        how='left',
        suffixes=('_team', '_opp')
    )
    
    # Count successful matches
    team_matches = merged['AdjEM_team'].notna().sum()
    opp_matches = merged['AdjEM_opp'].notna().sum()
    
    print(f"  Team matches: {team_matches}/{len(schedule)} ({team_matches/len(schedule)*100:.1f}%)")
    print(f"  Opponent matches: {opp_matches}/{len(schedule)} ({opp_matches/len(schedule)*100:.1f}%)")
    
    # Show unmatched teams
    unmatched_teams = merged[merged['AdjEM_team'].isna()]['team'].unique()
    unmatched_opps = merged[merged['AdjEM_opp'].isna()]['opponent'].unique()
    
    if len(unmatched_teams) > 0:
        print(f"  ⚠️  Unmatched teams ({len(unmatched_teams)}): {', '.join(list(unmatched_teams)[:5])}")
    if len(unmatched_opps) > 0:
        print(f"  ⚠️  Unmatched opponents ({len(unmatched_opps)}): {', '.join(list(unmatched_opps)[:5])}")
    
    # Calculate derived features
    if 'AdjEM_team' in merged.columns and 'AdjEM_opp' in merged.columns:
        merged['efficiency_diff'] = merged['AdjEM_team'] - merged['AdjEM_opp']
        merged['tempo_diff'] = merged['AdjTempo_team'] - merged['AdjTempo_opp']
        merged['offensive_matchup'] = merged['AdjOE_team'] - merged['AdjDE_opp']
        merged['defensive_matchup'] = merged['AdjDE_team'] - merged['AdjOE_opp']
    
    return merged

def main():
    """Main execution function."""
    print("=" * 60)
    print("Merging KenPom Ratings with Game Schedules")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    seasons = [2022, 2023, 2024, 2025]
    results = {}
    
    for season in seasons:
        merged = merge_season_data(season)
        
        if merged is not None:
            # Save merged data
            output_file = OUTPUT_DIR / f"merged_games_{season}.csv"
            merged.to_csv(output_file, index=False)
            
            file_size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"  ✅ Saved: {output_file.name} ({file_size_mb:.2f} MB)")
            
            results[season] = {
                'total_games': len(merged),
                'team_matches': int(merged['AdjEM_team'].notna().sum()),
                'opp_matches': int(merged['AdjEM_opp'].notna().sum()),
                'file_size_mb': round(file_size_mb, 2)
            }
    
    # Save metadata
    metadata = {
        'merge_date': datetime.now().isoformat(),
        'seasons': results,
        'total_games': sum(r['total_games'] for r in results.values())
    }
    
    with open(OUTPUT_DIR / 'merge_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Merge Complete!")
    print("=" * 60)
    print(f"Total games merged: {metadata['total_games']}")
    print(f"Files saved to: {OUTPUT_DIR}")
    print("\nNext step: Build prediction model using merged dataset")

if __name__ == "__main__":
    main()
