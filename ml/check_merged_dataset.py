#!/usr/bin/env python3
"""
Check merged dataset integrity and consistency.

This script validates that the merged odds + KenPom dataset is structured
correctly for the time-aware modeling pipeline.

Usage:
    python3 ml/check_merged_dataset.py
    python3 ml/check_merged_dataset.py --file data/merged/merged_odds_kenpom_full.csv
"""

import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime


def check_merged_dataset(file_path: Path) -> dict:
    """
    Validate merged dataset structure and content.
    
    Args:
        file_path: Path to merged CSV file
        
    Returns:
        Dict with validation results
    """
    print("=" * 80)
    print("MERGED DATASET VALIDATION")
    print("=" * 80)
    print(f"\n📂 Loading: {file_path}")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return {'valid': False, 'error': 'File not found'}
    
    # Load dataset
    df = pd.read_csv(file_path)
    print(f"   ✅ Loaded {len(df):,} rows")
    
    # Basic structure check
    print(f"\n📊 Dataset Structure:")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    
    # Check required columns
    required_cols = [
        'date', 'home_team', 'away_team',
        'close_spread', 'home_ml', 'away_ml',
        'AdjEM_home', 'AdjEM_away',
        'AdjOE_home', 'AdjOE_away',
        'AdjDE_home', 'AdjDE_away',
        'AdjTempo_home', 'AdjTempo_away'
    ]
    
    time_aware_cols = ['rating_date_home', 'rating_date_away']
    
    missing_required = [col for col in required_cols if col not in df.columns]
    missing_time_aware = [col for col in time_aware_cols if col not in df.columns]
    
    print(f"\n✅ Required Columns Check:")
    if missing_required:
        print(f"   ❌ Missing: {', '.join(missing_required)}")
    else:
        print(f"   ✅ All required columns present")
    
    print(f"\n🕐 Time-Aware Columns Check:")
    if missing_time_aware:
        print(f"   ⚠️  Missing: {', '.join(missing_time_aware)}")
        print(f"   → Dataset may not be using new time-aware merge")
        has_time_aware = False
    else:
        print(f"   ✅ Time-aware columns present (rating_date_home/away)")
        has_time_aware = True
    
    # Date range check
    df['date'] = pd.to_datetime(df['date'])
    date_min = df['date'].min()
    date_max = df['date'].max()
    
    print(f"\n📅 Date Range:")
    print(f"   Games: {date_min.date()} → {date_max.date()}")
    print(f"   Duration: {(date_max - date_min).days} days")
    
    # Check for season consistency
    df['season'] = df['date'].apply(lambda x: x.year if x.month >= 7 else x.year)
    seasons = sorted(df['season'].unique())
    print(f"   Seasons: {seasons}")
    
    # Rating date checks (if time-aware)
    if has_time_aware:
        df['rating_date_home'] = pd.to_datetime(df['rating_date_home'])
        df['rating_date_away'] = pd.to_datetime(df['rating_date_away'])
        
        print(f"\n🎯 Rating Date Validation:")
        
        # Check non-null
        home_nulls = df['rating_date_home'].isna().sum()
        away_nulls = df['rating_date_away'].isna().sum()
        
        if home_nulls > 0 or away_nulls > 0:
            print(f"   ⚠️  Null rating dates:")
            print(f"      Home: {home_nulls:,} ({home_nulls/len(df)*100:.1f}%)")
            print(f"      Away: {away_nulls:,} ({away_nulls/len(df)*100:.1f}%)")
        else:
            print(f"   ✅ No null rating dates")
        
        # Check rating_date <= game_date (time-aware correctness)
        home_future = (df['rating_date_home'] > df['date']).sum()
        away_future = (df['rating_date_away'] > df['date']).sum()
        
        if home_future > 0 or away_future > 0:
            print(f"   ❌ VIOLATION: Ratings from AFTER game date:")
            print(f"      Home: {home_future:,} games")
            print(f"      Away: {away_future:,} games")
            print(f"      → This indicates lookahead or date logic error!")
        else:
            print(f"   ✅ All ratings are from on/before game date")
        
        # Rating date distribution
        home_rating_min = df['rating_date_home'].min()
        home_rating_max = df['rating_date_home'].max()
        away_rating_min = df['rating_date_away'].min()
        away_rating_max = df['rating_date_away'].max()
        
        print(f"\n   Rating Date Range:")
        print(f"      Home: {home_rating_min.date()} → {home_rating_max.date()}")
        print(f"      Away: {away_rating_min.date()} → {away_rating_max.date()}")
        
        # Check if all rating dates are the same (indicates season-end snapshot)
        unique_home_dates = df['rating_date_home'].nunique()
        unique_away_dates = df['rating_date_away'].nunique()
        
        print(f"\n   Rating Date Diversity:")
        print(f"      Home: {unique_home_dates} unique dates")
        print(f"      Away: {unique_away_dates} unique dates")
        
        if unique_home_dates == 1 and unique_away_dates == 1:
            print(f"      ⚠️  All ratings from single date (season-end snapshot)")
            print(f"      → Using dummy rating_date; still has lookahead bias")
            print(f"      → Code is ready for dated ratings when available")
        elif unique_home_dates > 100 or unique_away_dates > 100:
            print(f"      ✅ Multiple rating dates (dated snapshots)")
            print(f"      → True time-aware ratings!")
        else:
            print(f"      ⚠️  Limited rating date diversity")
    
    # KenPom ratings coverage
    print(f"\n📈 KenPom Coverage:")
    home_ratings = df['AdjEM_home'].notna().sum()
    away_ratings = df['AdjEM_away'].notna().sum()
    both_ratings = ((df['AdjEM_home'].notna()) & (df['AdjEM_away'].notna())).sum()
    
    print(f"   Home team: {home_ratings:,}/{len(df):,} ({home_ratings/len(df)*100:.1f}%)")
    print(f"   Away team: {away_ratings:,}/{len(df):,} ({away_ratings/len(df)*100:.1f}%)")
    print(f"   Both teams: {both_ratings:,}/{len(df):,} ({both_ratings/len(df)*100:.1f}%)")
    
    if both_ratings < len(df):
        missing = len(df) - both_ratings
        print(f"   ⚠️  {missing:,} games missing ratings for at least one team")
    
    # Derived features check
    derived_features = ['efficiency_diff', 'tempo_diff', 'offensive_matchup_home', 'defensive_matchup_home']
    present_derived = [col for col in derived_features if col in df.columns]
    
    print(f"\n🔧 Derived Features:")
    if present_derived:
        print(f"   ✅ Present: {', '.join(present_derived)}")
    else:
        print(f"   ⚠️  No derived features found")
        print(f"      Expected: {', '.join(derived_features)}")
    
    # Sample data
    print(f"\n📋 Sample Data (first 5 rows):")
    
    display_cols = ['date', 'home_team', 'away_team', 'close_spread',
                    'AdjEM_home', 'AdjEM_away', 'efficiency_diff']
    
    if has_time_aware:
        display_cols.extend(['rating_date_home', 'rating_date_away'])
    
    available_cols = [col for col in display_cols if col in df.columns]
    
    sample = df[available_cols].head(5).copy()
    
    # Format for display
    if 'date' in sample.columns:
        sample['date'] = sample['date'].dt.strftime('%Y-%m-%d')
    if has_time_aware:
        if 'rating_date_home' in sample.columns:
            sample['rating_date_home'] = pd.to_datetime(sample['rating_date_home']).dt.strftime('%Y-%m-%d')
        if 'rating_date_away' in sample.columns:
            sample['rating_date_away'] = pd.to_datetime(sample['rating_date_away']).dt.strftime('%Y-%m-%d')
    
    print(sample.to_string(index=False))
    
    # Team coverage
    unique_home = df['home_team'].nunique()
    unique_away = df['away_team'].nunique()
    all_teams = pd.concat([df['home_team'], df['away_team']]).nunique()
    
    print(f"\n🏀 Team Coverage:")
    print(f"   Unique home teams: {unique_home}")
    print(f"   Unique away teams: {unique_away}")
    print(f"   Total unique teams: {all_teams}")
    
    # Summary verdict
    print(f"\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    issues = []
    
    if missing_required:
        issues.append(f"Missing required columns: {', '.join(missing_required)}")
    
    if not has_time_aware:
        issues.append("Missing time-aware columns (rating_date_home/away)")
    
    if has_time_aware:
        if home_future > 0 or away_future > 0:
            issues.append("Ratings from AFTER game date detected (logic error!)")
        
        if unique_home_dates == 1:
            issues.append("Single rating_date (season-end snapshot, lookahead bias remains)")
    
    if both_ratings < len(df) * 0.9:
        issues.append(f"Low KenPom coverage: {both_ratings/len(df)*100:.1f}%")
    
    if issues:
        print("⚠️  Issues Found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ Dataset passes all validation checks!")
    
    print(f"\n📊 Ready for modeling: {'YES' if not issues or len(issues) == 1 and 'lookahead' in str(issues) else 'REVIEW NEEDED'}")
    print(f"   → Time-aware infrastructure: {'✅ Active' if has_time_aware else '❌ Not using new pipeline'}")
    print(f"   → Lookahead status: {'⚠️ Present (awaiting dated ratings)' if has_time_aware and unique_home_dates == 1 else '✅ Clean' if has_time_aware and unique_home_dates > 100 else '❓ Unknown'}")
    
    return {
        'valid': len(issues) == 0 or (len(issues) == 1 and 'lookahead' in str(issues)),
        'has_time_aware': has_time_aware,
        'rows': len(df),
        'issues': issues
    }


def main():
    parser = argparse.ArgumentParser(description="Validate merged dataset")
    parser.add_argument('--file', type=Path, 
                       default=Path('data/merged/merged_odds_kenpom_full.csv'),
                       help='Path to merged CSV file')
    
    args = parser.parse_args()
    
    result = check_merged_dataset(args.file)
    
    # Exit code: 0 if valid, 1 if issues
    exit(0 if result['valid'] else 1)


if __name__ == '__main__':
    main()
