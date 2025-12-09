#!/usr/bin/env python3
"""
Consolidate daily/weekly rating snapshots into a single dated ratings file.

This script takes multiple CSV files (e.g., one per day/week during the season)
and combines them into a single file with a rating_date column, suitable for
time-aware rating attachment.

Usage:
    python3 data-collection/consolidate_ratings_snapshots.py \\
        --season 2024 \\
        --input-dir data/kenpom/snapshots/2024 \\
        --pattern "kenpom_ratings_2024_*.csv" \\
        --output data/kenpom/kenpom_ratings_2024_dated.csv \\
        --source-type kenpom

Supported source types:
    - kenpom: KenPom.com ratings exports
    - torvik: Bart Torvik ratings exports

Output schema:
    team, rating_date, season, AdjEM, AdjOE, AdjDE, AdjTempo, Tempo, Luck, SOS, ...
"""

import argparse
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from glob import glob

# Column mappings for different data sources
COLUMN_MAPPINGS = {
    'kenpom': {
        # KenPom uses standard names, just ensure consistency
        'TeamName': 'team',
        'Team': 'team',
        'AdjEM': 'AdjEM',
        'AdjOE': 'AdjOE', 
        'AdjDE': 'AdjDE',
        'AdjTempo': 'AdjTempo',
        'Tempo': 'Tempo',
        'Luck': 'Luck',
        'SOS': 'SOS',
        'SOSO': 'SOSO',
        'SOSD': 'SOSD',
        'RankAdjEM': 'RankAdjEM',
        'RankAdjOE': 'RankAdjOE',
        'RankAdjDE': 'RankAdjDE',
        'RankAdjTempo': 'RankAdjTempo',
        # Keep other rank columns if present
    },
    'torvik': {
        # Bart Torvik column mapping (adjust based on actual format)
        # These are educated guesses - adjust when real Torvik data is available
        'team': 'team',
        'barthag': 'AdjEM',  # Torvik's main rating metric
        'adj_o': 'AdjOE',
        'adj_d': 'AdjDE',
        'adj_tempo': 'AdjTempo',
        'tempo': 'Tempo',
        'luck': 'Luck',
        'sos': 'SOS',
        'sos_offense': 'SOSO',
        'sos_defense': 'SOSD',
        'rank': 'RankAdjEM',
        'o_rank': 'RankAdjOE',
        'd_rank': 'RankAdjDE',
        'tempo_rank': 'RankAdjTempo',
    }
}

# Required columns (must be present after mapping)
REQUIRED_COLUMNS = ['team', 'AdjEM', 'AdjOE', 'AdjDE']

def extract_date_from_filename(filename: str, pattern: str) -> datetime:
    """
    Extract date from filename based on pattern.
    
    Assumes filenames contain date in YYYYMMDD or YYYY-MM-DD format.
    Examples:
        kenpom_ratings_2024_20240115.csv -> 2024-01-15
        ratings_2024-01-15.csv -> 2024-01-15
        kenpom_20240115.csv -> 2024-01-15
    """
    # Try YYYYMMDD format
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, '%Y%m%d')
    
    # Try YYYY-MM-DD format
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, '%Y-%m-%d')
    
    raise ValueError(f"Could not extract date from filename: {filename}")

def normalize_columns(df: pd.DataFrame, source_type: str) -> pd.DataFrame:
    """
    Normalize column names based on source type.
    
    Args:
        df: Raw dataframe from source
        source_type: 'kenpom' or 'torvik'
    
    Returns:
        DataFrame with standardized column names
    """
    if source_type not in COLUMN_MAPPINGS:
        raise ValueError(f"Unknown source_type: {source_type}. Must be one of {list(COLUMN_MAPPINGS.keys())}")
    
    mapping = COLUMN_MAPPINGS[source_type]
    
    # Apply mapping (only for columns that exist)
    rename_dict = {}
    for old_col, new_col in mapping.items():
        if old_col in df.columns:
            rename_dict[old_col] = new_col
    
    df_normalized = df.rename(columns=rename_dict)
    
    # Verify required columns are present
    missing = [col for col in REQUIRED_COLUMNS if col not in df_normalized.columns]
    if missing:
        raise ValueError(f"Missing required columns after normalization: {missing}")
    
    return df_normalized

def consolidate_snapshots(
    input_dir: str,
    pattern: str,
    source_type: str,
    season: int,
    output_path: str
) -> pd.DataFrame:
    """
    Consolidate multiple rating snapshot files into single dated file.
    
    Args:
        input_dir: Directory containing snapshot CSV files
        pattern: Glob pattern to match files (e.g., "kenpom_ratings_2024_*.csv")
        source_type: 'kenpom' or 'torvik'
        season: Season ending year (e.g., 2024 for 2023-24 season)
        output_path: Path to write consolidated CSV
    
    Returns:
        Consolidated DataFrame
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    # Find all matching files
    search_pattern = str(input_dir / pattern)
    files = sorted(glob(search_pattern))
    
    if not files:
        raise FileNotFoundError(f"No files matching pattern: {search_pattern}")
    
    print(f"\n{'='*60}")
    print(f"Consolidating Rating Snapshots")
    print(f"{'='*60}")
    print(f"Input directory: {input_dir}")
    print(f"Pattern: {pattern}")
    print(f"Source type: {source_type}")
    print(f"Season: {season}")
    print(f"Files found: {len(files)}")
    
    all_snapshots = []
    date_range = {'min': None, 'max': None}
    
    for file_path in files:
        try:
            # Extract date from filename
            rating_date = extract_date_from_filename(Path(file_path).name, pattern)
            
            # Track date range
            if date_range['min'] is None or rating_date < date_range['min']:
                date_range['min'] = rating_date
            if date_range['max'] is None or rating_date > date_range['max']:
                date_range['max'] = rating_date
            
            # Load CSV
            df = pd.read_csv(file_path)
            
            # Normalize column names
            df = normalize_columns(df, source_type)
            
            # Add rating_date column
            df['rating_date'] = rating_date.strftime('%Y-%m-%d')
            
            # Add season column
            df['season'] = season
            
            all_snapshots.append(df)
            
            print(f"  ✓ {Path(file_path).name}: {len(df)} teams, date={rating_date.date()}")
            
        except Exception as e:
            print(f"  ✗ {Path(file_path).name}: ERROR - {e}")
            continue
    
    if not all_snapshots:
        raise ValueError("No snapshots were successfully processed")
    
    # Concatenate all snapshots
    print(f"\nCombining {len(all_snapshots)} snapshot files...")
    combined_df = pd.concat(all_snapshots, ignore_index=True)
    
    print(f"Raw combined rows: {len(combined_df)}")
    
    # Drop duplicates (same team on same date)
    combined_df = combined_df.drop_duplicates(subset=['team', 'rating_date'], keep='last')
    print(f"After deduplication: {len(combined_df)} rows")
    
    # Sort by team, then rating_date
    combined_df = combined_df.sort_values(['team', 'rating_date'])
    
    # Basic stats
    unique_teams = combined_df['team'].nunique()
    unique_dates = combined_df['rating_date'].nunique()
    
    print(f"\n{'='*60}")
    print(f"Consolidation Summary")
    print(f"{'='*60}")
    print(f"Total rows: {len(combined_df)}")
    print(f"Unique teams: {unique_teams}")
    print(f"Unique rating dates: {unique_dates}")
    print(f"Date range: {date_range['min'].date()} to {date_range['max'].date()}")
    print(f"Avg snapshots per team: {len(combined_df) / unique_teams:.1f}")
    
    # Show sample teams
    sample_teams = ['Duke', 'Kansas', 'North Carolina', 'Kentucky', 'Gonzaga']
    available_samples = [t for t in sample_teams if t in combined_df['team'].values]
    
    if available_samples:
        print(f"\nSample Teams (showing rating date evolution):")
        for team in available_samples[:2]:  # Show 2 teams
            team_df = combined_df[combined_df['team'] == team][['rating_date', 'AdjEM', 'AdjOE', 'AdjDE']]
            print(f"\n{team}:")
            print(team_df.head(5).to_string(index=False))
            if len(team_df) > 5:
                print(f"  ... ({len(team_df) - 5} more snapshots)")
    
    # Write output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Consolidated file written to: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    return combined_df

def main():
    parser = argparse.ArgumentParser(
        description='Consolidate daily/weekly rating snapshots into single dated file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--season',
        type=int,
        required=True,
        help='Season ending year (e.g., 2024 for 2023-24 season)'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        required=True,
        help='Directory containing snapshot CSV files'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.csv',
        help='Glob pattern to match files (default: *.csv)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output path for consolidated CSV'
    )
    
    parser.add_argument(
        '--source-type',
        type=str,
        choices=['kenpom', 'torvik'],
        required=True,
        help='Data source type (determines column mapping)'
    )
    
    args = parser.parse_args()
    
    try:
        consolidate_snapshots(
            input_dir=args.input_dir,
            pattern=args.pattern,
            source_type=args.source_type,
            season=args.season,
            output_path=args.output
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
