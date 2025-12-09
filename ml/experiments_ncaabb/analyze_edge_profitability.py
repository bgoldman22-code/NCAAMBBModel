"""
Analyze profitability by edge buckets, win probability buckets, and odds ranges.

This script helps answer questions like:
- Are longshots (+1000 or more) actually profitable?
- Which edge buckets have the best ROI?
- Is there a sweet spot for model win probability?
- Should we filter out certain odds ranges?
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json


def calculate_bet_pnl(row, bet_side):
    """Calculate P&L for a single bet."""
    if bet_side == 'home':
        won = row['home_won'] == 1
        odds = row['home_ml']
    else:  # away
        won = row['home_won'] == 0
        odds = row['away_ml']
    
    if won:
        # Win
        if odds < 0:
            profit = 100 * (100 / abs(odds))
        else:
            profit = 100 * (odds / 100)
        return profit
    else:
        # Loss
        return -100


def analyze_by_buckets(edges_df, bucket_col, bucket_edges, bucket_labels, min_edge=0.15):
    """Analyze profitability by buckets (edge, win prob, or odds)."""
    results = []
    
    # Create buckets
    df = edges_df.copy()
    
    # Prepare bets for both sides
    home_bets = df[df['edge_home'] >= min_edge].copy()
    home_bets['bet_side'] = 'home'
    home_bets['edge'] = home_bets['edge_home']
    home_bets['model_prob'] = home_bets['model_prob_home']
    home_bets['odds'] = home_bets['home_ml']
    home_bets['won'] = home_bets['home_won']
    
    away_bets = df[df['edge_away'] >= min_edge].copy()
    away_bets['bet_side'] = 'away'
    away_bets['edge'] = away_bets['edge_away']
    away_bets['model_prob'] = away_bets['model_prob_away']
    away_bets['odds'] = away_bets['away_ml']
    away_bets['won'] = 1 - away_bets['home_won']
    
    all_bets = pd.concat([home_bets, away_bets], ignore_index=True)
    
    if len(all_bets) == 0:
        print(f"⚠️ No bets found with edge >= {min_edge}")
        return pd.DataFrame()
    
    # Create bucket column
    all_bets['bucket'] = pd.cut(
        all_bets[bucket_col],
        bins=bucket_edges,
        labels=bucket_labels,
        include_lowest=True
    )
    
    # Analyze each bucket
    for bucket_label in bucket_labels:
        bucket_bets = all_bets[all_bets['bucket'] == bucket_label]
        
        if len(bucket_bets) == 0:
            continue
        
        total_bets = len(bucket_bets)
        wins = bucket_bets['won'].sum()
        losses = total_bets - wins
        
        # Calculate P&L
        pnl = 0
        for _, row in bucket_bets.iterrows():
            if row['won'] == 1:
                if row['odds'] < 0:
                    profit = 100 * (100 / abs(row['odds']))
                else:
                    profit = 100 * (row['odds'] / 100)
                pnl += profit
            else:
                pnl -= 100
        
        win_rate = wins / total_bets if total_bets > 0 else 0
        roi = (pnl / (total_bets * 100)) * 100 if total_bets > 0 else 0
        avg_edge = bucket_bets['edge'].mean()
        avg_model_prob = bucket_bets['model_prob'].mean()
        avg_odds = bucket_bets['odds'].mean()
        
        results.append({
            'bucket': bucket_label,
            'bets': total_bets,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'pnl': pnl,
            'roi': roi,
            'avg_edge': avg_edge,
            'avg_model_prob': avg_model_prob,
            'avg_odds': avg_odds
        })
    
    return pd.DataFrame(results)


def analyze_2d_buckets(edges_df, min_edge=0.15):
    """Analyze profitability by edge AND model probability buckets."""
    results = []
    
    # Prepare bets
    df = edges_df.copy()
    
    home_bets = df[df['edge_home'] >= min_edge].copy()
    home_bets['bet_side'] = 'home'
    home_bets['edge'] = home_bets['edge_home']
    home_bets['model_prob'] = home_bets['model_prob_home']
    home_bets['odds'] = home_bets['home_ml']
    home_bets['won'] = home_bets['home_won']
    
    away_bets = df[df['edge_away'] >= min_edge].copy()
    away_bets['bet_side'] = 'away'
    away_bets['edge'] = away_bets['edge_away']
    away_bets['model_prob'] = away_bets['model_prob_away']
    away_bets['odds'] = away_bets['away_ml']
    away_bets['won'] = 1 - away_bets['home_won']
    
    all_bets = pd.concat([home_bets, away_bets], ignore_index=True)
    
    if len(all_bets) == 0:
        return pd.DataFrame()
    
    # Define buckets
    edge_buckets = [0.15, 0.25, 0.35, 0.50, 1.0]
    edge_labels = ['15-25%', '25-35%', '35-50%', '50%+']
    
    prob_buckets = [0.0, 0.15, 0.30, 0.50, 0.70, 1.0]
    prob_labels = ['0-15%', '15-30%', '30-50%', '50-70%', '70%+']
    
    all_bets['edge_bucket'] = pd.cut(
        all_bets['edge'],
        bins=edge_buckets,
        labels=edge_labels,
        include_lowest=True
    )
    
    all_bets['prob_bucket'] = pd.cut(
        all_bets['model_prob'],
        bins=prob_buckets,
        labels=prob_labels,
        include_lowest=True
    )
    
    # Analyze each combination
    for edge_label in edge_labels:
        for prob_label in prob_labels:
            bucket_bets = all_bets[
                (all_bets['edge_bucket'] == edge_label) &
                (all_bets['prob_bucket'] == prob_label)
            ]
            
            if len(bucket_bets) == 0:
                continue
            
            total_bets = len(bucket_bets)
            wins = bucket_bets['won'].sum()
            
            # Calculate P&L
            pnl = 0
            for _, row in bucket_bets.iterrows():
                if row['won'] == 1:
                    if row['odds'] < 0:
                        profit = 100 * (100 / abs(row['odds']))
                    else:
                        profit = 100 * (row['odds'] / 100)
                    pnl += profit
                else:
                    pnl -= 100
            
            win_rate = wins / total_bets
            roi = (pnl / (total_bets * 100)) * 100
            
            results.append({
                'edge_bucket': edge_label,
                'prob_bucket': prob_label,
                'bets': total_bets,
                'wins': wins,
                'win_rate': win_rate,
                'roi': roi,
                'pnl': pnl
            })
    
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description='Analyze profitability by buckets')
    parser.add_argument('--variant', type=str, required=True, choices=['A', 'B', 'C'],
                       help='Model variant to analyze')
    parser.add_argument('--min-edge', type=float, default=0.15,
                       help='Minimum edge threshold (default: 0.15)')
    args = parser.parse_args()
    
    variant = args.variant
    min_edge = args.min_edge
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    edges_file = data_dir / 'edges' / f'edges_ncaabb_variant_{variant}.csv'
    
    if not edges_file.exists():
        print(f"❌ Edges file not found: {edges_file}")
        return
    
    print(f"\n{'='*80}")
    print(f"Edge Profitability Analysis - Variant {variant}")
    print(f"Minimum Edge Threshold: {min_edge:.1%}")
    print(f"{'='*80}")
    
    edges_df = pd.read_csv(edges_file)
    print(f"\nLoaded {len(edges_df)} test games")
    
    # Load metrics
    metrics_file = data_dir / 'edges' / f'metrics_variant_{variant}.json'
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
            print(f"Variant: {metrics['variant_name']}")
            print(f"Test AUC: {metrics['test_auc']:.4f}")
    
    # Analysis 1: By Edge Buckets
    print(f"\n{'='*80}")
    print(f"1. PROFITABILITY BY EDGE BUCKETS")
    print(f"{'='*80}")
    
    edge_buckets = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 1.0]
    edge_labels = ['15-20%', '20-25%', '25-30%', '30-40%', '40-50%', '50%+']
    
    edge_results = analyze_by_buckets(
        edges_df, 'edge_home', edge_buckets, edge_labels, min_edge
    )
    
    if not edge_results.empty:
        print(f"\n{'Bucket':<12} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'ROI':<10} {'Avg Edge':<12} {'P&L'}")
        print("-" * 80)
        for _, row in edge_results.iterrows():
            print(f"{row['bucket']:<12} "
                  f"{row['bets']:<8.0f} "
                  f"{row['wins']:<8.0f} "
                  f"{row['win_rate']*100:<9.1f}% "
                  f"{row['roi']:>8.1f}% "
                  f"{row['avg_edge']*100:>10.1f}% "
                  f"${row['pnl']:>10,.0f}")
    
    # Analysis 2: By Model Win Probability
    print(f"\n{'='*80}")
    print(f"2. PROFITABILITY BY MODEL WIN PROBABILITY")
    print(f"{'='*80}")
    
    prob_buckets = [0.0, 0.10, 0.15, 0.25, 0.35, 0.50, 0.65, 1.0]
    prob_labels = ['0-10%', '10-15%', '15-25%', '25-35%', '35-50%', '50-65%', '65%+']
    
    # For this, we need to work with individual bets
    df = edges_df.copy()
    
    home_bets = df[df['edge_home'] >= min_edge].copy()
    home_bets['model_prob'] = home_bets['model_prob_home']
    
    away_bets = df[df['edge_away'] >= min_edge].copy()
    away_bets['model_prob'] = away_bets['model_prob_away']
    
    # Temporarily use edge_home as the column for bucketing model_prob
    home_bets['edge_home'] = home_bets['model_prob']
    away_bets['edge_home'] = away_bets['model_prob']
    
    combined_for_prob = pd.concat([home_bets, away_bets], ignore_index=True)
    
    prob_results = analyze_by_buckets(
        combined_for_prob, 'edge_home', prob_buckets, prob_labels, min_edge=0
    )
    
    if not prob_results.empty:
        print(f"\n{'Bucket':<12} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'ROI':<10} {'Avg Prob':<12} {'P&L'}")
        print("-" * 80)
        for _, row in prob_results.iterrows():
            print(f"{row['bucket']:<12} "
                  f"{row['bets']:<8.0f} "
                  f"{row['wins']:<8.0f} "
                  f"{row['win_rate']*100:<9.1f}% "
                  f"{row['roi']:>8.1f}% "
                  f"{row['avg_model_prob']*100:>10.1f}% "
                  f"${row['pnl']:>10,.0f}")
    
    # Analysis 3: By Odds Ranges (focus on longshots)
    print(f"\n{'='*80}")
    print(f"3. PROFITABILITY BY ODDS RANGES (Longshots Analysis)")
    print(f"{'='*80}")
    
    # Prepare bets with actual odds
    df = edges_df.copy()
    
    home_bets = df[df['edge_home'] >= min_edge].copy()
    home_bets['edge_home'] = home_bets['home_ml']  # Temporarily use for bucketing
    
    away_bets = df[df['edge_away'] >= min_edge].copy()
    away_bets['edge_home'] = away_bets['away_ml']  # Temporarily use for bucketing
    
    combined_for_odds = pd.concat([home_bets, away_bets], ignore_index=True)
    
    odds_buckets = [-1000, -300, -200, -150, -110, 110, 200, 400, 1000, 5000]
    odds_labels = ['-300 to -1000', '-200 to -300', '-150 to -200', '-110 to -150', 
                   '+100 to +110', '+110 to +200', '+200 to +400', '+400 to +1000', '+1000+']
    
    odds_results = analyze_by_buckets(
        combined_for_odds, 'edge_home', odds_buckets, odds_labels, min_edge=0
    )
    
    if not odds_results.empty:
        print(f"\n{'Odds Range':<18} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'ROI':<10} {'Avg Edge':<12} {'P&L'}")
        print("-" * 85)
        for _, row in odds_results.iterrows():
            print(f"{row['bucket']:<18} "
                  f"{row['bets']:<8.0f} "
                  f"{row['wins']:<8.0f} "
                  f"{row['win_rate']*100:<9.1f}% "
                  f"{row['roi']:>8.1f}% "
                  f"{row['avg_edge']*100:>10.1f}% "
                  f"${row['pnl']:>10,.0f}")
    
    # Analysis 4: 2D Analysis (Edge x Model Probability)
    print(f"\n{'='*80}")
    print(f"4. COMBINED ANALYSIS: EDGE × MODEL WIN PROBABILITY")
    print(f"{'='*80}")
    
    combo_results = analyze_2d_buckets(edges_df, min_edge)
    
    if not combo_results.empty:
        print(f"\n{'Edge':<12} {'Model Prob':<12} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'ROI':<10} {'P&L'}")
        print("-" * 80)
        
        # Sort by edge bucket then prob bucket
        combo_results = combo_results.sort_values(['edge_bucket', 'prob_bucket'])
        
        for _, row in combo_results.iterrows():
            print(f"{row['edge_bucket']:<12} "
                  f"{row['prob_bucket']:<12} "
                  f"{row['bets']:<8.0f} "
                  f"{row['wins']:<8.0f} "
                  f"{row['win_rate']*100:<9.1f}% "
                  f"{row['roi']:>8.1f}% "
                  f"${row['pnl']:>10,.0f}")
    
    # Key insights
    print(f"\n{'='*80}")
    print(f"KEY INSIGHTS")
    print(f"{'='*80}")
    
    # Find best performing buckets
    if not odds_results.empty:
        longshots = odds_results[odds_results['bucket'] == '+1000+']
        if not longshots.empty:
            ls = longshots.iloc[0]
            print(f"\n📊 Longshots (+1000 or more):")
            print(f"   Bets: {ls['bets']:.0f}")
            print(f"   Win Rate: {ls['win_rate']*100:.1f}%")
            print(f"   ROI: {ls['roi']:+.1f}%")
            print(f"   P&L: ${ls['pnl']:,.0f}")
            print(f"   Average Edge: {ls['avg_edge']*100:.1f}%")
            
            if ls['roi'] > 0:
                print(f"   ✅ PROFITABLE - Longshots are beating the market!")
            else:
                print(f"   ❌ NOT PROFITABLE - Model overestimates longshot chances")
    
    if not edge_results.empty:
        best_edge = edge_results.loc[edge_results['roi'].idxmax()]
        print(f"\n🎯 Best Edge Bucket: {best_edge['bucket']}")
        print(f"   ROI: {best_edge['roi']:+.1f}%")
        print(f"   Bets: {best_edge['bets']:.0f}")
        print(f"   Win Rate: {best_edge['win_rate']*100:.1f}%")
    
    if not prob_results.empty:
        # Filter to buckets with at least 10 bets for reliability
        reliable = prob_results[prob_results['bets'] >= 10]
        if not reliable.empty:
            best_prob = reliable.loc[reliable['roi'].idxmax()]
            print(f"\n🎲 Best Win Probability Range: {best_prob['bucket']}")
            print(f"   ROI: {best_prob['roi']:+.1f}%")
            print(f"   Bets: {best_prob['bets']:.0f}")
            print(f"   Win Rate: {best_prob['win_rate']*100:.1f}%")


if __name__ == '__main__':
    main()
