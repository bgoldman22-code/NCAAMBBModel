"""
Generate Variant B picks for a given date.

This is the main production script for daily NCAA basketball betting picks.

Modes:
    --mode historical (default):
        Loads games and odds from pre-collected historical data
        (data/walkforward_results_with_scores.csv).
        Used for backtesting and validation.
    
    --mode live:
        Fetches today's games and odds from The Odds API in real-time.
        Requires ODDS_API_KEY environment variable.
        Used for production daily picks generation.
        Dependency: data-collection/live_odds_client.py

Usage (Historical):
    python3 scripts/ncaabb/generate_variant_b_picks.py \\
        --date 2025-12-10 \\
        --mode historical \\
        --min-edge 0.15 \\
        --kelly-fraction 0.25 \\
        --bankroll 10000 \\
        --output data/ncaabb/picks/variant_b_picks_2025-12-10.csv

Usage (Live):
    export ODDS_API_KEY='your_key_here'
    
    python3 scripts/ncaabb/generate_variant_b_picks.py \\
        --date 2025-12-10 \\
        --mode live \\
        --min-edge 0.15 \\
        --kelly-fraction 0.25 \\
        --bankroll 10000 \\
        --output data/ncaabb/picks/variant_b_picks_2025-12-10.csv
"""

import pandas as pd
import numpy as np
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Add data-collection folder to path (hyphenated folder name)
data_collection_path = project_root / 'data-collection'
sys.path.append(str(data_collection_path))

from ml.ncaabb_variant_b_model import (
    load_variant_b_model,
    build_features_for_games,
    predict_variant_b,
    add_kelly_stakes
)

# Import live odds client for live mode
try:
    from live_odds_client import fetch_today_moneyline_odds, fetch_odds_with_fallback
    LIVE_ODDS_AVAILABLE = True
except ImportError:
    LIVE_ODDS_AVAILABLE = False
    print("⚠️  Warning: live_odds_client not available, --mode live will fail")

def load_todays_games(date_str: str, mode: str = 'historical', lookahead_hours: int = 72) -> pd.DataFrame:
    """
    Load scheduled games and odds for a given date range.
    
    Args:
        date_str: Start date string (YYYY-MM-DD)
        mode: 'historical' or 'live'
        lookahead_hours: Hours to look ahead from start date (default: 72)
    
    Returns:
        DataFrame with game schedule and odds
    """
    print(f"\n📅 Loading games for {date_str} + {lookahead_hours}h (mode: {mode})...")
    
    if mode == 'live':
        return load_todays_games_live(date_str, lookahead_hours)
    else:
        return load_todays_games_historical(date_str, lookahead_hours)


def load_todays_games_live(date_str: str, lookahead_hours: int = 72) -> pd.DataFrame:
    """
    Load games and odds from live API for the next N hours.
    
    Args:
        date_str: Start date string (YYYY-MM-DD)
        lookahead_hours: Hours to look ahead (default: 72)
    
    Returns:
        DataFrame with live odds
    """
    if not LIVE_ODDS_AVAILABLE:
        raise ImportError(
            "Live odds client not available. "
            "Ensure data-collection/live_odds_client.py is properly set up."
        )
    
    target_date = pd.to_datetime(date_str).date()
    
    try:
        # Fetch from API with fallback, using lookahead hours
        df = fetch_odds_with_fallback(target_date, lookahead_hours=lookahead_hours)
        
        if len(df) == 0:
            print(f"   ⚠️  No games found via API for {date_str}")
            return pd.DataFrame()
        
        print(f"   ✅ Found {len(df)} games from live API")
        print(f"   Books: {', '.join(df['book_name'].unique())}")
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Add placeholder columns if needed (for compatibility)
        if 'home_score' not in df.columns:
            df['home_score'] = None
        if 'away_score' not in df.columns:
            df['away_score'] = None
        
        return df
    
    except Exception as e:
        print(f"   ❌ Failed to fetch live odds: {e}")
        print(f"   � Check ODDS_API_KEY environment variable")
        raise


def load_todays_games_historical(date_str: str, lookahead_hours: int = 72) -> pd.DataFrame:
    """
    Load games from pre-collected historical data for the next N hours.
    
    Args:
        date_str: Start date string (YYYY-MM-DD)
        lookahead_hours: Hours to look ahead (default: 72)
    
    Returns:
        DataFrame with historical odds
    """
    data_file = Path('data/walkforward_results_with_scores.csv')
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        print("   In production live mode, this would fetch from an odds API")
        return pd.DataFrame()
    
    df = pd.read_csv(data_file)
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Use game_day as date
    if 'game_day' in df.columns:
        df['date'] = pd.to_datetime(df['game_day'])
    else:
        df['date'] = pd.to_datetime(df['date'])
    
    # Filter to date range (start_date to start_date + lookahead_hours)
    target_date = pd.to_datetime(date_str)
    end_date = target_date + timedelta(hours=lookahead_hours)
    games = df[(df['date'] >= target_date) & (df['date'] < end_date)].copy()
    
    print(f"   Found {len(games)} games between {date_str} and {end_date.date()}")
    
    if len(games) == 0:
        print(f"   ⚠️  No games found. Using nearby date for demo...")
        # Use a date with games for demo
        games = df[df['date'] >= target_date].head(10).copy()
        print(f"   Using {len(games)} demo games from {games['date'].min().date()}")
    
    return games

def load_inseason_stats(date_str: str) -> pd.DataFrame:
    """
    Load in-season rolling stats up to (but not including) the target date.
    
    In production, this would query a live stats database.
    For now, loads from the pre-computed dataset.
    """
    print(f"\n📊 Loading in-season stats (as of {date_str})...")
    
    # Load pre-computed stats
    stats_file = Path('data/merged/game_results_with_inseason_stats.csv')
    
    if not stats_file.exists():
        print(f"   ⚠️  Pre-computed stats not found at {stats_file}")
        print(f"   Computing in-season stats now...")
        
        # Compute stats
        from ml.features_inseason_stats import build_inseason_stats
        
        results_file = Path('data/walkforward_results_with_scores.csv')
        results_df = pd.read_csv(results_file)
        results_df = results_df.loc[:, ~results_df.columns.duplicated()]
        
        if 'game_day' in results_df.columns:
            results_df = results_df.rename(columns={'game_day': 'date'})
        
        enhanced_df = build_inseason_stats(results_df)
        
        # Save
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        enhanced_df.to_csv(stats_file, index=False)
        print(f"   ✅ Stats computed and saved to {stats_file}")
        
        return enhanced_df
    
    df = pd.read_csv(stats_file)
    print(f"   ✅ Loaded {len(df)} games with in-season stats")
    
    return df

def merge_games_with_stats(games_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge today's games with in-season stats.
    
    For each game, we need to find the most recent in-season stats for both teams
    (not stats from the same date, since the game hasn't been played yet).
    """
    
    print(f"\n🔗 Merging games with in-season stats...")
    
    # Ensure date columns match
    games_df['date'] = pd.to_datetime(games_df['date'])
    stats_df['date'] = pd.to_datetime(stats_df['date'])
    
    merged_rows = []
    
    for _, game in games_df.iterrows():
        game_date = game['date']
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Find most recent stats for home team (before game date)
        home_stats = stats_df[
            ((stats_df['home_team'] == home_team) | (stats_df['away_team'] == home_team)) &
            (stats_df['date'] < game_date)
        ].sort_values('date', ascending=False)
        
        # Find most recent stats for away team (before game date)
        away_stats = stats_df[
            ((stats_df['home_team'] == away_team) | (stats_df['away_team'] == away_team)) &
            (stats_df['date'] < game_date)
        ].sort_values('date', ascending=False)
        
        # Start with game data
        merged_game = game.to_dict()
        
        # Add home team's rolling stats
        if len(home_stats) > 0:
            recent_home = home_stats.iloc[0]
            # Extract stats for the home team (whether they were home or away in that game)
            if recent_home['home_team'] == home_team:
                for col in recent_home.index:
                    if col.startswith('home_') and any(x in col for x in ['ORtg', 'DRtg', 'MoV', 'Pace', 'WinPct']):
                        # Keep as home_ prefix
                        merged_game[col] = recent_home[col]
            else:  # They were away in that game
                for col in recent_home.index:
                    if col.startswith('away_') and any(x in col for x in ['ORtg', 'DRtg', 'MoV', 'Pace', 'WinPct']):
                        # Change away_ to home_ since they're home now
                        home_col = col.replace('away_', 'home_')
                        merged_game[home_col] = recent_home[col]
        
        # Add away team's rolling stats
        if len(away_stats) > 0:
            recent_away = away_stats.iloc[0]
            # Extract stats for the away team
            if recent_away['away_team'] == away_team:
                for col in recent_away.index:
                    if col.startswith('away_') and any(x in col for x in ['ORtg', 'DRtg', 'MoV', 'Pace', 'WinPct']):
                        # Keep as away_ prefix
                        merged_game[col] = recent_away[col]
            else:  # They were home in that game
                for col in recent_away.index:
                    if col.startswith('home_') and any(x in col for x in ['ORtg', 'DRtg', 'MoV', 'Pace', 'WinPct']):
                        # Change home_ to away_ since they're away now
                        away_col = col.replace('home_', 'away_')
                        merged_game[away_col] = recent_away[col]
        
        merged_rows.append(merged_game)
    
    merged = pd.DataFrame(merged_rows)
    
    # Count stats coverage
    inseason_cols = [c for c in merged.columns if any(x in c for x in ['ORtg', 'DRtg', 'MoV', 'Pace', 'WinPct']) and c.endswith(('_L3', '_L5', '_L10'))]
    if inseason_cols:
        coverage = merged[inseason_cols].notna().mean().mean() * 100
    else:
        coverage = 0
    
    print(f"   Merged {len(merged)} games")
    print(f"   In-season stats coverage: {coverage:.1f}%")
    
    return merged

def generate_picks(args):
    """Main picks generation logic."""
    
    # Get lookahead hours from args (default to 72 if not present)
    lookahead_hours = getattr(args, 'lookahead_hours', 72)
    
    print("="*80)
    print("NCAA Basketball Variant B - Live Picks Generator")
    print("="*80)
    print(f"\nMode: {args.mode}")
    print(f"Date: {args.date}")
    print(f"Lookahead: {lookahead_hours} hours")
    print(f"Min Edge: {args.min_edge}")
    print(f"Kelly Fraction: {args.kelly_fraction}")
    print(f"Bankroll: ${args.bankroll:,.0f}")
    
    # 1. Load today's games
    games_df = load_todays_games(args.date, mode=args.mode, lookahead_hours=lookahead_hours)
    
    if len(games_df) == 0:
        print("\n❌ No games found for this date")
        return None
    
    # 2. Load in-season stats
    stats_df = load_inseason_stats(args.date)
    
    # 3. Merge
    features_df = merge_games_with_stats(games_df, stats_df)
    
    # 4. Build features
    print("\n🔧 Building Variant B features...")
    features_df, feature_cols = build_features_for_games(features_df)
    
    # 5. Load model and generate predictions
    print("\n🤖 Loading Variant B model...")
    model, scaler, metadata = load_variant_b_model()
    print(f"   Model: {metadata['model_name']}")
    print(f"   Test AUC: {metadata['performance']['test_auc']:.4f}")
    if metadata['performance'].get('approved_roi'):
        print(f"   Approved ROI: {metadata['performance']['approved_roi']:.1%}")
    
    # 6. Generate predictions
    print("\n🔮 Generating predictions...")
    
    # Load feature columns from metadata
    features_path = Path('models/variant_b_production/variant_b_features.json')
    with open(features_path, 'r') as f:
        feature_data = json.load(f)
        feature_cols = feature_data['feature_cols']
    
    bets_df = predict_variant_b(features_df, model, feature_cols, min_edge=args.min_edge, scaler=scaler)
    
    if len(bets_df) == 0:
        print(f"\n⚠️  No bets found above {args.min_edge} edge threshold")
        print("   Try lowering --min-edge or wait for better opportunities")
        
        # Still create empty output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        empty_df = pd.DataFrame(columns=[
            'date', 'home_team', 'away_team', 'side', 'market',
            'odds', 'model_prob', 'implied_prob', 'edge',
            'kelly_full', 'kelly_applied', 'bet_size_dollars'
        ])
        empty_df.to_csv(output_path, index=False)
        
        # Save JSON too
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({
                'date': args.date,
                'model': 'Variant B',
                'min_edge': args.min_edge,
                'picks': []
            }, f, indent=2)
        
        return None
    
    # 6. Filter out +400 or greater underdogs (route to calibration experiment)
    print(f"\n🔍 Filtering longshot underdogs (+400 or greater)...")
    longdogs_df = bets_df[bets_df['bet_odds'] >= 400].copy()
    core_picks_df = bets_df[bets_df['bet_odds'] < 400].copy()
    
    if len(longdogs_df) > 0:
        print(f"   ⚠️  Excluded {len(longdogs_df)} longshot bets (≥+400 odds) from production picks")
        print(f"   Routing to calibration experiment: data/ncaabb/experiments/variant_b_longdogs_raw.csv")
        log_longdogs_to_experiment(longdogs_df, args)
    else:
        print(f"   ✓ No longshot underdogs found")
    
    # Continue with core picks only
    bets_df = core_picks_df
    
    if len(bets_df) == 0:
        print(f"\n⚠️  No bets remaining after filtering longshots (all were ≥+400)")
        print("   Try lowering --min-edge or wait for better opportunities")
        
        # Create empty output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        empty_df = pd.DataFrame(columns=[
            'date', 'home_team', 'away_team', 'side', 'market',
            'odds', 'model_prob', 'implied_prob', 'edge',
            'kelly_full', 'kelly_applied', 'bet_size_dollars'
        ])
        empty_df.to_csv(output_path, index=False)
        
        # Save JSON too
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({
                'date': args.date,
                'model': 'Variant B',
                'min_edge': args.min_edge,
                'picks': [],
                'note': 'All qualifying bets were longshots (≥+400) and excluded from production'
            }, f, indent=2)
        
        return None
    
    # 7. Apply odds-aware edge filtering
    print(f"\n🎯 Applying odds-aware edge filters...")
    print(f"   Rules:")
    print(f"   • +120-140: 15% edge required (96% ROI)")
    print(f"   • +160-180: 13% edge required (78% ROI)")
    print(f"   • +200-250: No edge filter (34% ROI)")
    print(f"   • +140-160, +180-200, +250-400: Skip (negative ROI)")
    print(f"   • Favorites/<+120: 15% edge required")
    
    filtered_bets = []
    skipped_by_odds = []
    skipped_by_edge = []
    
    for _, row in bets_df.iterrows():
        odds = row['bet_odds']
        edge = row['max_edge']
        is_fav = odds < 0
        
        # Determine required edge for this odds band
        required_edge = decide_min_edge_for_odds(odds, is_fav)
        
        if required_edge is None:
            # Skip this odds band entirely
            skipped_by_odds.append(row)
        elif edge >= required_edge:
            # Passes edge filter for this odds band
            filtered_bets.append(row)
        else:
            # Doesn't meet edge requirement
            skipped_by_edge.append(row)
    
    # Convert to DataFrame
    if len(filtered_bets) > 0:
        bets_df = pd.DataFrame(filtered_bets)
    else:
        bets_df = pd.DataFrame(columns=bets_df.columns)
    
    print(f"\n   Results:")
    print(f"   • Qualified bets: {len(filtered_bets)}")
    print(f"   • Skipped (death valley odds): {len(skipped_by_odds)}")
    print(f"   • Skipped (insufficient edge): {len(skipped_by_edge)}")
    
    if len(skipped_by_odds) > 0:
        skipped_odds_df = pd.DataFrame(skipped_by_odds)
        print(f"\n   Skipped by odds band:")
        for _, skip_row in skipped_odds_df.iterrows():
            print(f"   • {skip_row['home_team']} vs {skip_row['away_team']}: "
                  f"{skip_row['chosen_side']} @ {skip_row['bet_odds']:+.0f} "
                  f"(edge: {skip_row['max_edge']:.1%})")
    
    if len(bets_df) == 0:
        print(f"\n⚠️  No bets remaining after odds-aware filtering")
        print("   All bets either in death valleys or insufficient edge for their odds band")
        
        # Create empty output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        empty_df = pd.DataFrame(columns=[
            'date', 'home_team', 'away_team', 'side', 'market',
            'odds', 'model_prob', 'implied_prob', 'edge',
            'kelly_full', 'kelly_applied', 'bet_size_dollars'
        ])
        empty_df.to_csv(output_path, index=False)
        
        # Save JSON too
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({
                'date': args.date,
                'model': 'Variant B',
                'min_edge': args.min_edge,
                'picks': [],
                'note': 'No bets passed odds-aware filtering'
            }, f, indent=2)
        
        return None
    
    # 8. Calculate Kelly stakes
    print(f"\n💰 Calculating Kelly stakes...")
    bets_df = add_kelly_stakes(
        bets_df,
        bankroll=args.bankroll,
        kelly_fraction=args.kelly_fraction,
        max_fraction=0.10  # Cap at 10% of bankroll
    )
    
    # 8. Sort by edge (highest first)
    bets_df = bets_df.sort_values('max_edge', ascending=False)
    
    # 8. Format output
    output_df = bets_df[[
        'date', 'home_team', 'away_team', 'chosen_side',
        'bet_odds', 'bet_prob', 'bet_implied_prob', 'max_edge',
        'kelly_full', 'kelly_applied', 'bet_size_dollars'
    ]].copy()
    
    output_df = output_df.rename(columns={
        'chosen_side': 'side',
        'bet_odds': 'odds',
        'bet_prob': 'model_prob',
        'bet_implied_prob': 'implied_prob',
        'max_edge': 'edge'
    })
    
    output_df['market'] = output_df['side'].apply(lambda x: f'{x}_ml')
    
    # 9. Save outputs
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # CSV
    output_df.to_csv(output_path, index=False)
    print(f"\n✅ Picks saved to: {output_path}")
    
    # JSON
    json_path = output_path.with_suffix('.json')
    
    # Convert to JSON-serializable format
    output_json = output_df.copy()
    output_json['date'] = output_json['date'].dt.strftime('%Y-%m-%d')
    
    picks_json = {
        'date': args.date,
        'model': 'Variant B',
        'min_edge': args.min_edge,
        'kelly_fraction': args.kelly_fraction,
        'bankroll': args.bankroll,
        'num_picks': len(output_df),
        'total_bet_size': int(output_df['bet_size_dollars'].sum()),
        'avg_edge': float(output_df['edge'].mean()),
        'max_edge': float(output_df['edge'].max()),
        'picks': output_json.to_dict(orient='records')
    }
    
    with open(json_path, 'w') as f:
        json.dump(picks_json, f, indent=2)
    
    print(f"✅ JSON saved to: {json_path}")
    
    # 10. Summary
    print("\n" + "="*80)
    print("📋 PICKS SUMMARY")
    print("="*80)
    print(f"  Bets: {len(output_df)}")
    print(f"  Total stake: ${output_df['bet_size_dollars'].sum():,.0f}")
    print(f"  Average edge: {output_df['edge'].mean():.3f}")
    print(f"  Max edge: {output_df['edge'].max():.3f}")
    print(f"  Largest bet: ${output_df['bet_size_dollars'].max():,.0f}")
    
    print(f"\n📊 Top 5 Picks:")
    print(output_df[['home_team', 'away_team', 'side', 'edge', 'bet_size_dollars']].head().to_string(index=False))
    
    # 11. Log run
    log_run(args, len(games_df), len(output_df), output_df)
    
    return output_df

def decide_min_edge_for_odds(american_odds: float, is_favorite: bool) -> float | None:
    """
    Determine the minimum edge threshold for a given odds band.
    
    Returns:
        - float: minimum edge required for this odds band
        - None: skip this odds band entirely (no bets allowed)
    
    Rules based on historical profitability analysis:
    - +120-140: 15% edge (96% ROI)
    - +160-180: 13% edge (78% ROI, 15% also OK)
    - +200-250: No filter (34% ROI baseline)
    - +140-160, +180-200, +250-400: Skip (negative ROI)
    - Favorites/small dogs (<+120): 15% edge (default)
    - +400+: Already filtered by longdog system
    """
    # Favorites (negative odds)
    if is_favorite:
        return 0.15
    
    # Underdogs (positive odds)
    odds = american_odds
    
    # Very small dogs: +100 to +120
    if 100 <= odds < 120:
        return 0.15
    
    # Profitable zone 1: +120 to +140
    if 120 <= odds < 140:
        return 0.15
    
    # Death valley 1: +140 to +160 (SKIP)
    if 140 <= odds < 160:
        return None
    
    # Profitable zone 2: +160 to +180
    if 160 <= odds < 180:
        return 0.13  # Could use 0.15, but 13% is optimal
    
    # Death valley 2: +180 to +200 (SKIP)
    if 180 <= odds < 200:
        return None
    
    # Profitable zone 3: +200 to +250 (NO FILTER)
    if 200 <= odds < 250:
        return 0.0  # No edge filter - baseline performance is best
    
    # Death valley 3: +250 to +400 (SKIP)
    if 250 <= odds < 400:
        return None
    
    # +400+ should already be filtered by longdog system
    # But if somehow one slips through, use default
    return 0.15


def log_longdogs_to_experiment(longdogs_df, args):
    """
    Log longshot underdogs (≥+400 odds) to calibration experiment CSV
    
    This builds a dataset for training Platt/Isotonic calibration models
    to fix model miscalibration on extreme underdogs.
    """
    exp_dir = Path('data/ncaabb/experiments')
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    exp_file = exp_dir / 'variant_b_longdogs_raw.csv'
    
    # Format for experiment tracking
    exp_data = []
    for _, row in longdogs_df.iterrows():
        exp_data.append({
            'date': args.date,
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'bet_side': row['chosen_side'],
            'american_odds': int(row['bet_odds']),
            'implied_prob_market': row['bet_implied_prob'],
            'model_prob': row['bet_prob'],
            'edge': row['max_edge'],
            'outcome': None  # Will be filled in post-game
        })
    
    exp_df = pd.DataFrame(exp_data)
    
    # Append to existing file or create new
    if exp_file.exists():
        exp_df.to_csv(exp_file, mode='a', header=False, index=False)
    else:
        exp_df.to_csv(exp_file, index=False)
    
    print(f"   Logged {len(exp_df)} longdogs to {exp_file}")

def log_run(args, num_games, num_bets, bets_df):
    """Log this run to CSV."""
    
    log_file = Path('data/ncaabb/logs/variant_b_runs.csv')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'run_timestamp': datetime.now().isoformat(),
        'date': args.date,
        'mode': args.mode,
        'min_edge': args.min_edge,
        'kelly_fraction': args.kelly_fraction,
        'bankroll': args.bankroll,
        'num_games': num_games,
        'num_bets': num_bets,
        'avg_edge': bets_df['edge'].mean() if len(bets_df) > 0 else 0,
        'max_edge': bets_df['edge'].max() if len(bets_df) > 0 else 0,
        'total_stake': bets_df['bet_size_dollars'].sum() if len(bets_df) > 0 else 0,
        'status': 'success'
    }
    
    log_df = pd.DataFrame([log_entry])
    
    if log_file.exists():
        log_df.to_csv(log_file, mode='a', header=False, index=False)
    else:
        log_df.to_csv(log_file, index=False)
    
    print(f"\n📝 Run logged to: {log_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate Variant B picks for NCAA basketball')
    
    parser.add_argument('--date', type=str, required=True,
                        help='Date for picks (YYYY-MM-DD)')
    parser.add_argument('--mode', type=str, default='historical', choices=['historical', 'live'],
                        help='Data source mode: historical (pre-collected) or live (API)')
    parser.add_argument('--lookahead-hours', type=int, default=72,
                        help='Hours to look ahead from start date (default: 72)')
    parser.add_argument('--min-edge', type=float, default=0.15,
                        help='Minimum edge threshold (default: 0.15)')
    parser.add_argument('--kelly-fraction', type=float, default=0.25,
                        help='Fraction of full Kelly (default: 0.25 for 25%% Kelly)')
    parser.add_argument('--bankroll', type=float, default=10000,
                        help='Total bankroll in dollars (default: 10000)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output CSV path')
    
    args = parser.parse_args()
    
    # Validate mode
    if args.mode == 'live' and not LIVE_ODDS_AVAILABLE:
        print(f"❌ --mode live requires live_odds_client.py")
        print(f"   Check that data-collection/live_odds_client.py exists")
        sys.exit(1)
    
    # Validate inputs
    if args.min_edge < 0 or args.min_edge > 0.5:
        print(f"❌ Invalid min-edge: {args.min_edge} (must be 0-0.5)")
        sys.exit(1)
    
    if args.kelly_fraction <= 0 or args.kelly_fraction > 1:
        print(f"❌ Invalid kelly-fraction: {args.kelly_fraction} (must be 0-1)")
        sys.exit(1)
    
    if args.bankroll <= 0:
        print(f"❌ Invalid bankroll: {args.bankroll} (must be > 0)")
        sys.exit(1)
    
    # Generate picks
    try:
        picks_df = generate_picks(args)
        
        if picks_df is not None and len(picks_df) > 0:
            print("\n✅ Picks generation complete!")
            sys.exit(0)
        else:
            print("\n⚠️  No qualifying bets found")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Error generating picks: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
