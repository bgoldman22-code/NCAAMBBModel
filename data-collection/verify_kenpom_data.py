#!/usr/bin/env python3
"""
Verify KenPom data merge quality.

This script validates the merged game data by checking:
- Total rows per year
- Match rate (games with both team and opponent KenPom metrics)
- Sample rows for key teams to verify correct mappings
"""

import pandas as pd
from pathlib import Path
import sys

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
MERGED_DIR = DATA_DIR / "merged"

def verify_merged_data():
    """Verify quality of merged KenPom data."""
    print("=" * 80)
    print("KenPom Data Merge Verification")
    print("=" * 80)
    print()
    
    years = [2022, 2023, 2024, 2025]
    total_games = 0
    total_matched = 0
    
    for year in years:
        file_path = MERGED_DIR / f"merged_games_{year}.csv"
        
        if not file_path.exists():
            print(f"⚠️  Missing: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        
        # Count rows
        total_rows = len(df)
        total_games += total_rows
        
        # Count fully matched games (both team and opponent have KenPom data)
        # Check if opponent metrics exist (not NaN)
        matched = df['AdjEM_opp'].notna().sum()
        total_matched += matched
        match_rate = (matched / total_rows * 100) if total_rows > 0 else 0
        
        print(f"{year-1}-{str(year)[2:]} Season:")
        print(f"  Total games: {total_rows:,}")
        print(f"  Fully matched: {matched:,} ({match_rate:.1f}%)")
        print(f"  Unmatched: {total_rows - matched:,}")
        print()
        
        # Sample specific teams to verify mappings
        if year == 2025:
            print("Sample Verification (2024-25 Season):")
            print("-" * 80)
            
            # Check Illinois (Big Ten) - should NOT be Illinois Chicago
            illinois_games = df[df['team'] == 'Illinois'].head(3)
            if len(illinois_games) > 0:
                print("\n✅ Illinois (Big Ten) games found:")
                for _, game in illinois_games.iterrows():
                    print(f"  - vs {game['opponent']}: AdjEM={game['AdjEM_team']:.2f}")
            
            # Check Charleston vs Charleston Southern
            charleston = df[df['team'] == 'Charleston'].head(2)
            if len(charleston) > 0:
                print("\n✅ Charleston (not Charleston Southern) games found:")
                for _, game in charleston.iterrows():
                    print(f"  - vs {game['opponent']}: AdjEM={game['AdjEM_team']:.2f}")
            
            # Check Portland vs Portland State
            portland = df[df['team'] == 'Portland'].head(2)
            portland_st = df[df['team'] == 'Portland St.'].head(2)
            if len(portland) > 0:
                print("\n✅ Portland (not Portland State) games found:")
                for _, game in portland.iterrows():
                    print(f"  - vs {game['opponent']}: AdjEM={game['AdjEM_team']:.2f}")
            
            # Check UC system schools
            uc_schools = ['UC Irvine', 'UC Riverside', 'UC Davis', 'UC Santa Barbara']
            for school in uc_schools:
                uc_games = df[df['team'] == school].head(1)
                if len(uc_games) > 0:
                    print(f"\n✅ {school} games found:")
                    for _, game in uc_games.iterrows():
                        print(f"  - vs {game['opponent']}: AdjEM={game['AdjEM_team']:.2f}")
            
            # Check Corpus Christi
            corpus = df[df['team'] == 'Texas A&M Corpus Chris'].head(2)
            if len(corpus) > 0:
                print("\n✅ Texas A&M Corpus Christi games found:")
                for _, game in corpus.iterrows():
                    print(f"  - vs {game['opponent']}: AdjEM={game['AdjEM_team']:.2f}")
            
            print("\n" + "-" * 80)
    
    print()
    print("=" * 80)
    print("Overall Summary:")
    print(f"  Total games: {total_games:,}")
    print(f"  Fully matched: {total_matched:,} ({total_matched/total_games*100:.1f}%)")
    print(f"  Unmatched: {total_games - total_matched:,}")
    print()
    
    # Quality check
    match_rate = (total_matched / total_games * 100) if total_games > 0 else 0
    if match_rate >= 90:
        print("✅ EXCELLENT: Match rate >= 90% - Ready for modeling!")
    elif match_rate >= 85:
        print("✅ GOOD: Match rate >= 85% - Ready for modeling")
    elif match_rate >= 80:
        print("⚠️  ACCEPTABLE: Match rate >= 80% - Consider improving mappings")
    else:
        print("❌ POOR: Match rate < 80% - Improve mappings before modeling")
    
    print("=" * 80)
    
    return match_rate

if __name__ == "__main__":
    try:
        match_rate = verify_merged_data()
        sys.exit(0 if match_rate >= 85 else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
