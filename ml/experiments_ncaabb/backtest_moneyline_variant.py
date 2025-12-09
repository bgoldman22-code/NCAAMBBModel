"""
Backtest moneyline betting for a specific model variant.

This script:
1. Loads edges CSV for a variant
2. Applies edge threshold grid
3. Computes P&L and ROI for moneyline bets
4. Outputs threshold → bets → win% → ROI table

Usage:
    python3 ml/experiments_ncaabb/backtest_moneyline_variant.py --variant A
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json

def backtest_moneyline(
    edges_df: pd.DataFrame,
    thresholds: list = [0.03, 0.05, 0.07, 0.10, 0.12, 0.15]
) -> pd.DataFrame:
    """
    Backtest moneyline betting with edge thresholds.
    
    Args:
        edges_df: DataFrame with model_prob, implied_prob, edge, moneyline odds
        thresholds: List of edge thresholds to test
    
    Returns:
        DataFrame with results for each threshold
    """
    results = []
    
    for threshold in thresholds:
        # Bet home when edge_home >= threshold
        home_bets_mask = edges_df['edge_home'] >= threshold
        home_bets = edges_df[home_bets_mask].copy()
        
        # Bet away when edge_away >= threshold
        away_bets_mask = edges_df['edge_away'] >= threshold
        away_bets = edges_df[away_bets_mask].copy()
        
        # Calculate home P&L
        home_wins = home_bets['home_won'].sum()
        home_losses = len(home_bets) - home_wins
        home_pnl = 0
        
        for _, row in home_bets.iterrows():
            if row['home_won'] == 1:
                # Win
                odds = row['home_ml']
                if odds < 0:
                    profit = 100 * (100 / abs(odds))
                else:
                    profit = 100 * (odds / 100)
                home_pnl += profit
            else:
                # Loss
                home_pnl -= 100
        
        # Calculate away P&L
        away_wins = (1 - away_bets['home_won']).sum()
        away_losses = len(away_bets) - away_wins
        away_pnl = 0
        
        for _, row in away_bets.iterrows():
            if row['home_won'] == 0:
                # Win (away won)
                odds = row['away_ml']
                if odds < 0:
                    profit = 100 * (100 / abs(odds))
                else:
                    profit = 100 * (odds / 100)
                away_pnl += profit
            else:
                # Loss
                away_pnl -= 100
        
        # Combined stats
        total_bets = len(home_bets) + len(away_bets)
        total_wins = home_wins + away_wins
        total_losses = home_losses + away_losses
        total_pnl = home_pnl + away_pnl
        
        if total_bets > 0:
            win_rate = total_wins / total_bets
            roi = (total_pnl / (total_bets * 100)) * 100
        else:
            win_rate = 0
            roi = 0
        
        results.append({
            'threshold': threshold,
            'total_bets': total_bets,
            'home_bets': len(home_bets),
            'away_bets': len(away_bets),
            'wins': total_wins,
            'losses': total_losses,
            'win_rate': win_rate,
            'pnl': total_pnl,
            'roi': roi
        })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Backtest moneyline betting for a variant')
    parser.add_argument('--variant', type=str, required=True, choices=['A', 'B', 'C'],
                       help='Model variant to backtest')
    args = parser.parse_args()
    
    variant = args.variant
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Load edges
    edges_file = data_dir / 'edges' / f'edges_ncaabb_variant_{variant}.csv'
    
    if not edges_file.exists():
        print(f"❌ Edges file not found: {edges_file}")
        print(f"   Run: python3 ml/experiments_ncaabb/train_eval_model_variant.py --variant {variant}")
        return
    
    print(f"\n{'='*60}")
    print(f"Moneyline Backtest - Variant {variant}")
    print(f"{'='*60}")
    
    edges_df = pd.read_csv(edges_file)
    print(f"\nLoaded {len(edges_df)} test games from {edges_file.name}")
    
    # Load metrics for variant name
    metrics_file = data_dir / 'edges' / f'metrics_variant_{variant}.json'
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
            print(f"Variant: {metrics['variant_name']}")
            print(f"Test AUC: {metrics['test_auc']:.4f}")
            print(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
    
    # Backtest
    print(f"\n{'='*60}")
    print(f"Backtest Results")
    print(f"{'='*60}")
    
    results = backtest_moneyline(edges_df)
    
    # Print table
    print(f"\n{'Threshold':<12} {'Bets':<8} {'Home':<8} {'Away':<8} {'Wins':<8} {'Win%':<8} {'ROI':<10} {'P&L ($100)':<12}")
    print("-" * 90)
    
    for _, row in results.iterrows():
        print(f"{row['threshold']:<12.2f} "
              f"{row['total_bets']:<8.0f} "
              f"{row['home_bets']:<8.0f} "
              f"{row['away_bets']:<8.0f} "
              f"{row['wins']:<8.0f} "
              f"{row['win_rate']*100:<7.1f}% "
              f"{row['roi']:>8.1f}% "
              f"${row['pnl']:>10,.0f}")
    
    # Find best threshold
    best_idx = results['roi'].idxmax()
    best = results.iloc[best_idx]
    
    print(f"\n{'='*60}")
    print(f"Best Threshold: {best['threshold']:.2f}")
    print(f"{'='*60}")
    print(f"Bets: {best['total_bets']:.0f}")
    print(f"Win Rate: {best['win_rate']*100:.1f}%")
    print(f"ROI: {best['roi']:+.1f}%")
    print(f"P&L: ${best['pnl']:,.0f}")
    
    # Save results
    results_file = data_dir / 'edges' / f'backtest_results_variant_{variant}.csv'
    results.to_csv(results_file, index=False)
    print(f"\n💾 Saved backtest results to: {results_file}")
    
    # Update metrics file with backtest results
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        metrics['backtest'] = {
            'best_threshold': float(best['threshold']),
            'best_roi': float(best['roi']),
            'best_bets': int(best['total_bets']),
            'best_win_rate': float(best['win_rate']),
            'all_thresholds': results.to_dict('records')
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"   Updated metrics file with backtest results")

if __name__ == '__main__':
    main()
