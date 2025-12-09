#!/usr/bin/env python3
"""
Backtest Odds-Aware Edge Policy

Replays the new odds-aware edge filtering policy over the full test period
to validate expected ROI improvements.

Policy Rules:
- +120-140: Require 15% edge (96% ROI)
- +160-180: Require 13% edge (78% ROI) 
- +200-250: No edge filter (34% ROI)
- +140-160, +180-200, +250-400: Skip (negative ROI)
- Favorites/<+120: 15% edge
- +400+: Already filtered (longdog system)

Usage:
    python ml/experiments_ncaabb/backtest_odds_aware_policy.py \
        --input data/edges/edges_ncaabb_variant_B.csv \
        --output data/ncaabb/backtests/odds_aware_policy_v1.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def decide_min_edge_for_odds(american_odds: float, is_favorite: bool) -> float | None:
    """
    Determine the minimum edge threshold for a given odds band.
    
    Returns:
        - float: minimum edge required for this odds band
        - None: skip this odds band entirely (no bets allowed)
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
        return 0.13
    
    # Death valley 2: +180 to +200 (SKIP)
    if 180 <= odds < 200:
        return None
    
    # Profitable zone 3: +200 to +250 (NO FILTER)
    if 200 <= odds < 250:
        return 0.0  # No edge filter
    
    # Death valley 3: +250 to +400 (SKIP)
    if 250 <= odds < 400:
        return None
    
    # +400+ filtered by longdog system
    if odds >= 400:
        return None
    
    # Default
    return 0.15


def american_to_decimal(odds):
    """Convert American odds to decimal odds"""
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1


def calculate_profit(row):
    """Calculate profit for a single bet (assumes $1 unit bet)"""
    if row['outcome'] == 1:  # Win
        # Profit = (decimal_odds - 1)
        decimal_odds = american_to_decimal(row['american_odds'])
        return decimal_odds - 1
    else:  # Loss
        return -1.0


def classify_odds_band(odds, is_favorite):
    """Classify odds into descriptive bands"""
    if is_favorite:
        if odds <= -200:
            return "Heavy Favorite (-200 or better)"
        else:
            return "Favorite (-110 to -200)"
    
    # Underdogs
    if odds < 120:
        return "Small Dog (+100-119)"
    elif 120 <= odds < 140:
        return "Zone 1: +120-139 (15% edge)"
    elif 140 <= odds < 160:
        return "Death Valley 1: +140-159 (SKIP)"
    elif 160 <= odds < 180:
        return "Zone 2: +160-179 (13% edge)"
    elif 180 <= odds < 200:
        return "Death Valley 2: +180-199 (SKIP)"
    elif 200 <= odds < 250:
        return "Zone 3: +200-249 (No filter)"
    elif 250 <= odds < 400:
        return "Death Valley 3: +250-399 (SKIP)"
    else:
        return "Longdog: +400+ (Filtered)"


def load_edges_data(input_path):
    """
    Load edges data from CSV and convert to bet-level format
    
    The edges CSV has one row per game with home/away edges.
    We need to convert this to one row per potential bet.
    """
    df = pd.read_csv(input_path)
    
    print(f"📊 Loaded {len(df)} games from {input_path}")
    
    # Convert to bet-level format (one row per bet opportunity)
    bets = []
    
    for _, row in df.iterrows():
        # Home bet opportunity
        home_bet = {
            'date': row['date'],
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'bet_side': 'home',
            'american_odds': row['home_ml'],
            'edge': row['edge_home'],
            'model_prob': row['model_prob_home'],
            'implied_prob': row['home_implied_prob'],
            'outcome': int(row['home_won'])
        }
        bets.append(home_bet)
        
        # Away bet opportunity
        away_bet = {
            'date': row['date'],
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'bet_side': 'away',
            'american_odds': row['away_ml'],
            'edge': row['edge_away'],
            'model_prob': row['model_prob_away'],
            'implied_prob': row['away_implied_prob'],
            'outcome': int(not row['home_won'])
        }
        bets.append(away_bet)
    
    bets_df = pd.DataFrame(bets)
    
    # Add is_favorite flag
    bets_df['is_favorite'] = bets_df['american_odds'] < 0
    
    # Add odds band classification
    bets_df['odds_band'] = bets_df.apply(
        lambda row: classify_odds_band(row['american_odds'], row['is_favorite']),
        axis=1
    )
    
    print(f"   Converted to {len(bets_df)} bet opportunities (2 per game)")
    
    return bets_df


def apply_odds_aware_policy(df):
    """
    Apply odds-aware policy to filter bets
    
    Returns:
        filtered_df: Bets that pass the policy
        stats: Dictionary with filtering statistics
    """
    results = {
        'total_candidates': len(df),
        'filtered_longdogs': 0,
        'filtered_death_valleys': 0,
        'filtered_insufficient_edge': 0,
        'qualified_bets': 0
    }
    
    filtered_bets = []
    
    for _, row in df.iterrows():
        odds = row['american_odds']
        edge = row['edge']
        is_fav = row['is_favorite']
        
        # Filter +400 longdogs first
        if odds >= 400:
            results['filtered_longdogs'] += 1
            continue
        
        # Get required edge for this odds band
        required_edge = decide_min_edge_for_odds(odds, is_fav)
        
        if required_edge is None:
            # Death valley - skip
            results['filtered_death_valleys'] += 1
        elif edge >= required_edge:
            # Passes policy
            filtered_bets.append(row)
            results['qualified_bets'] += 1
        else:
            # Insufficient edge
            results['filtered_insufficient_edge'] += 1
    
    filtered_df = pd.DataFrame(filtered_bets) if filtered_bets else pd.DataFrame()
    
    return filtered_df, results


def calculate_performance_metrics(df):
    """Calculate comprehensive performance metrics"""
    if len(df) == 0:
        return {
            'total_bets': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'total_profit': 0.0,
            'roi': 0.0,
            'avg_odds': 0.0,
            'avg_edge': 0.0
        }
    
    # Calculate profit for each bet
    df = df.copy()
    df['profit'] = df.apply(calculate_profit, axis=1)
    
    metrics = {
        'total_bets': len(df),
        'wins': int(df['outcome'].sum()),
        'losses': int((df['outcome'] == 0).sum()),
        'win_rate': float(df['outcome'].mean()),
        'total_profit': float(df['profit'].sum()),
        'roi': float((df['profit'].sum() / len(df)) * 100),
        'avg_odds': float(df['american_odds'].mean()),
        'avg_edge': float(df['edge'].mean())
    }
    
    return metrics


def analyze_by_odds_bands(df):
    """Break down performance by odds bands"""
    if len(df) == 0:
        return {}
    
    band_analysis = {}
    
    for band in df['odds_band'].unique():
        band_df = df[df['odds_band'] == band].copy()
        metrics = calculate_performance_metrics(band_df)
        band_analysis[band] = metrics
    
    return band_analysis


def main():
    parser = argparse.ArgumentParser(
        description='Backtest odds-aware edge filtering policy',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--input', 
                       default='data/edges/edges_ncaabb_variant_B.csv',
                       help='Path to edges CSV file')
    parser.add_argument('--output',
                       default='data/ncaabb/backtests/odds_aware_policy_v1.json',
                       help='Output path for backtest results')
    parser.add_argument('--save-policy',
                       action='store_true',
                       help='Save policy configuration to models/ directory')
    
    args = parser.parse_args()
    
    print("="*80)
    print("Odds-Aware Edge Policy Backtest")
    print("="*80)
    
    # Load data
    df = load_edges_data(args.input)
    
    # Show baseline (no filtering except initial edge threshold used during training)
    print("\n" + "="*80)
    print("BASELINE: All bets in dataset (already passed initial edge filter)")
    print("="*80)
    baseline_metrics = calculate_performance_metrics(df)
    print(f"Total bets:  {baseline_metrics['total_bets']}")
    print(f"Win rate:    {baseline_metrics['win_rate']:.1%}")
    print(f"ROI:         {baseline_metrics['roi']:+.2f}%")
    print(f"Avg odds:    {baseline_metrics['avg_odds']:+.0f}")
    print(f"Avg edge:    {baseline_metrics['avg_edge']:.1%}")
    
    # Apply odds-aware policy
    print("\n" + "="*80)
    print("APPLYING ODDS-AWARE POLICY")
    print("="*80)
    
    filtered_df, filter_stats = apply_odds_aware_policy(df)
    
    print(f"\nFiltering Results:")
    print(f"  Total candidates:           {filter_stats['total_candidates']}")
    print(f"  Filtered (longdogs +400):   {filter_stats['filtered_longdogs']}")
    print(f"  Filtered (death valleys):   {filter_stats['filtered_death_valleys']}")
    print(f"  Filtered (insufficient edge): {filter_stats['filtered_insufficient_edge']}")
    print(f"  Qualified bets:             {filter_stats['qualified_bets']}")
    print(f"  Reduction:                  {(1 - filter_stats['qualified_bets']/filter_stats['total_candidates'])*100:.1f}%")
    
    # Calculate policy performance
    print("\n" + "="*80)
    print("POLICY PERFORMANCE")
    print("="*80)
    
    policy_metrics = calculate_performance_metrics(filtered_df)
    
    print(f"Total bets:  {policy_metrics['total_bets']}")
    print(f"Wins:        {policy_metrics['wins']}")
    print(f"Losses:      {policy_metrics['losses']}")
    print(f"Win rate:    {policy_metrics['win_rate']:.1%}")
    print(f"Total profit: {policy_metrics['total_profit']:+.2f} units")
    print(f"ROI:         {policy_metrics['roi']:+.2f}%")
    print(f"Avg odds:    {policy_metrics['avg_odds']:+.0f}")
    print(f"Avg edge:    {policy_metrics['avg_edge']:.1%}")
    
    # Improvement vs baseline
    roi_improvement = policy_metrics['roi'] - baseline_metrics['roi']
    print(f"\n✨ ROI Improvement: {roi_improvement:+.2f} percentage points")
    
    # Breakdown by odds bands
    print("\n" + "="*80)
    print("PERFORMANCE BY ODDS BAND")
    print("="*80)
    
    band_analysis = analyze_by_odds_bands(filtered_df)
    
    # Sort by total bets descending
    sorted_bands = sorted(band_analysis.items(), 
                         key=lambda x: x[1]['total_bets'], 
                         reverse=True)
    
    for band, metrics in sorted_bands:
        print(f"\n{band}:")
        print(f"  Bets:     {metrics['total_bets']}")
        print(f"  Win rate: {metrics['win_rate']:.1%}")
        print(f"  ROI:      {metrics['roi']:+.2f}%")
        print(f"  Avg odds: {metrics['avg_odds']:+.0f}")
        print(f"  Avg edge: {metrics['avg_edge']:.1%}")
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'policy_name': 'Odds-Aware Edge Policy v1',
            'description': 'Applies odds-band-specific edge thresholds based on historical profitability',
            'input_file': str(args.input)
        },
        'policy_config': {
            'rules': {
                'favorites': {'min_edge': 0.15, 'description': 'Standard 15% edge'},
                'small_dogs_100_119': {'min_edge': 0.15, 'description': 'Standard 15% edge'},
                'zone1_120_139': {'min_edge': 0.15, 'description': '96% ROI historical'},
                'death_valley1_140_159': {'skip': True, 'description': 'Negative ROI'},
                'zone2_160_179': {'min_edge': 0.13, 'description': '78% ROI historical'},
                'death_valley2_180_199': {'skip': True, 'description': 'Negative ROI'},
                'zone3_200_249': {'min_edge': 0.0, 'description': '34% ROI, no filter optimal'},
                'death_valley3_250_399': {'skip': True, 'description': 'Negative ROI'},
                'longdogs_400_plus': {'skip': True, 'description': 'Longdog calibration system'}
            }
        },
        'baseline_performance': baseline_metrics,
        'policy_performance': policy_metrics,
        'roi_improvement': float(roi_improvement),
        'filtering_stats': filter_stats,
        'odds_band_breakdown': {
            band: metrics for band, metrics in sorted_bands
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Backtest results saved to: {output_path}")
    
    # Optionally save policy configuration
    if args.save_policy:
        policy_dir = Path('models/variant_b_production')
        policy_dir.mkdir(parents=True, exist_ok=True)
        
        policy_config = {
            'version': 'v1',
            'created_at': datetime.now().isoformat(),
            'description': 'Odds-aware edge filtering policy',
            'rules': results['policy_config']['rules'],
            'backtest_performance': {
                'roi': policy_metrics['roi'],
                'win_rate': policy_metrics['win_rate'],
                'total_bets': policy_metrics['total_bets'],
                'improvement_vs_baseline': float(roi_improvement)
            }
        }
        
        policy_path = policy_dir / 'odds_aware_policy_v1.json'
        with open(policy_path, 'w') as f:
            json.dump(policy_config, f, indent=2)
        
        print(f"✅ Policy configuration saved to: {policy_path}")
    
    print("\n" + "="*80)
    print("✅ Backtest Complete!")
    print("="*80)
    print(f"\nKey Findings:")
    print(f"  • Baseline ROI:  {baseline_metrics['roi']:+.2f}%")
    print(f"  • Policy ROI:    {policy_metrics['roi']:+.2f}%")
    print(f"  • Improvement:   {roi_improvement:+.2f} pp")
    print(f"  • Bets reduced:  {filter_stats['total_candidates']} → {filter_stats['qualified_bets']}")
    print(f"  • Bet reduction: {(1 - filter_stats['qualified_bets']/filter_stats['total_candidates'])*100:.1f}%")


if __name__ == '__main__':
    main()
