#!/usr/bin/env python3
"""
Calculate P&L for walk-forward backtest with actual game results.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse

DATA_DIR = Path(__file__).parent.parent / "data"


def calculate_spread_pnl(df: pd.DataFrame, min_edge: float, stake: float) -> dict:
    """Calculate spread betting P&L"""
    
    # Filter for bets we would have made
    bets = df[abs(df['edge_spread']) >= min_edge].copy()
    
    if len(bets) == 0:
        return {
            'bets': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'profit': 0,
            'roi': 0
        }
    
    # Determine bet side and outcome
    # edge_spread = model_spread - close_spread
    # Positive edge = model higher than market = home undervalued = BET HOME
    # Negative edge = model lower than market = away undervalued = BET AWAY
    bets['bet_home'] = (bets['edge_spread'] > 0).astype(int)  # Positive edge = bet home
    bets['won'] = (
        ((bets['bet_home'] == 1) & (bets['home_covered'] == 1)) |
        ((bets['bet_home'] == 0) & (bets['home_covered'] == 0))
    ).astype(int)
    
    wins = bets['won'].sum()
    losses = len(bets) - wins
    profit = wins * (stake * 0.909) - losses * stake  # -110 odds = 0.909 payout
    
    return {
        'bets': len(bets),
        'wins': wins,
        'losses': losses,
        'win_rate': wins / len(bets) if len(bets) > 0 else 0,
        'profit': profit,
        'roi': (profit / (len(bets) * stake)) * 100 if len(bets) > 0 else 0,
        'detail': bets
    }


def calculate_ml_pnl(df: pd.DataFrame, min_edge: float, stake: float) -> dict:
    """Calculate moneyline betting P&L"""
    
    # Find ML betting opportunities
    home_ml_bets = df[df['home_ml_edge'] >= min_edge].copy()
    away_ml_bets = df[df['away_ml_edge'] >= min_edge].copy()
    
    total_bets = 0
    total_wins = 0
    total_profit = 0
    all_bets = []
    
    # Home ML bets
    if len(home_ml_bets) > 0:
        home_ml_bets['bet_side'] = 'home'
        home_ml_bets['won'] = home_ml_bets['home_won']
        
        for _, row in home_ml_bets.iterrows():
            if row['won'] == 1:
                if row['home_ml'] < 0:
                    profit = stake * (100 / abs(row['home_ml']))
                else:
                    profit = stake * (row['home_ml'] / 100)
                total_profit += profit
                total_wins += 1
            else:
                total_profit -= stake
            total_bets += 1
        
        all_bets.append(home_ml_bets)
    
    # Away ML bets
    if len(away_ml_bets) > 0:
        away_ml_bets['bet_side'] = 'away'
        away_ml_bets['won'] = 1 - away_ml_bets['home_won']  # Invert for away
        
        for _, row in away_ml_bets.iterrows():
            if row['won'] == 1:
                if row['away_ml'] < 0:
                    profit = stake * (100 / abs(row['away_ml']))
                else:
                    profit = stake * (row['away_ml'] / 100)
                total_profit += profit
                total_wins += 1
            else:
                total_profit -= stake
            total_bets += 1
        
        all_bets.append(away_ml_bets)
    
    detail_df = pd.concat(all_bets, ignore_index=True) if all_bets else pd.DataFrame()
    
    return {
        'bets': total_bets,
        'wins': total_wins,
        'losses': total_bets - total_wins,
        'win_rate': total_wins / total_bets if total_bets > 0 else 0,
        'profit': total_profit,
        'roi': (total_profit / (total_bets * stake)) * 100 if total_bets > 0 else 0,
        'detail': detail_df
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate backtest P&L")
    parser.add_argument('--results-file', type=Path, 
                       default=DATA_DIR / 'walkforward_results_with_scores.csv')
    parser.add_argument('--min-edge-spread', type=float, default=2.0)
    parser.add_argument('--min-edge-ml', type=float, default=0.07)
    parser.add_argument('--stake', type=float, default=100.0)
    
    args = parser.parse_args()
    
    print("="*80)
    print("BACKTEST P&L CALCULATION")
    print("="*80)
    
    # Load data
    print(f"\n📂 Loading {args.results_file}...")
    df = pd.read_csv(args.results_file)
    
    # Filter to matched games only (handle both column name variations)
    if 'result_matched' in df.columns:
        matched = df[df['result_matched'] == True].copy()
    elif 'matched' in df.columns:
        matched = df[df['matched'] == True].copy()
    else:
        print("\n❌ No match status column found (looking for 'result_matched' or 'matched')")
        return
    
    print(f"\n📊 Dataset:")
    print(f"   Total games: {len(df):,}")
    print(f"   Matched with results: {len(matched):,} ({len(matched)/len(df)*100:.1f}%)")
    
    if len(matched) == 0:
        print("\n❌ No games with results to calculate P&L!")
        return
    
    print(f"\nBetting thresholds:")
    print(f"   Min spread edge: {args.min_edge_spread} points")
    print(f"   Min ML edge: {args.min_edge_ml*100:.1f}%")
    print(f"   Stake per bet: ${args.stake:.2f}")
    
    # Calculate P&L
    spread_results = calculate_spread_pnl(matched, args.min_edge_spread, args.stake)
    ml_results = calculate_ml_pnl(matched, args.min_edge_ml, args.stake)
    
    # Display results
    print(f"\n{'='*80}")
    print(f"🎯 SPREAD BETTING RESULTS")
    print(f"{'='*80}")
    print(f"   Bets placed:    {spread_results['bets']}")
    print(f"   Wins:           {spread_results['wins']}")
    print(f"   Losses:         {spread_results['losses']}")
    print(f"   Win rate:       {spread_results['win_rate']*100:.1f}%")
    print(f"   Total profit:   ${spread_results['profit']:+,.2f}")
    print(f"   ROI:            {spread_results['roi']:+.2f}%")
    
    print(f"\n{'='*80}")
    print(f"💰 MONEYLINE BETTING RESULTS")
    print(f"{'='*80}")
    print(f"   Bets placed:    {ml_results['bets']}")
    print(f"   Wins:           {ml_results['wins']}")
    print(f"   Losses:         {ml_results['losses']}")
    print(f"   Win rate:       {ml_results['win_rate']*100:.1f}%")
    print(f"   Total profit:   ${ml_results['profit']:+,.2f}")
    print(f"   ROI:            {ml_results['roi']:+.2f}%")
    
    # Combined
    total_bets = spread_results['bets'] + ml_results['bets']
    total_profit = spread_results['profit'] + ml_results['profit']
    total_roi = (total_profit / (total_bets * args.stake)) * 100 if total_bets > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"📈 COMBINED RESULTS")
    print(f"{'='*80}")
    print(f"   Total bets:     {total_bets}")
    print(f"   Total profit:   ${total_profit:+,.2f}")
    print(f"   Combined ROI:   {total_roi:+.2f}%")
    
    # Break-even analysis
    print(f"\n{'='*80}")
    print(f"🎓 ANALYSIS")
    print(f"{'='*80}")
    print(f"   Spread break-even: 52.4% (actual: {spread_results['win_rate']*100:.1f}%)")
    if spread_results['win_rate'] > 0:
        print(f"   Edge over break-even: {(spread_results['win_rate'] - 0.524)*100:+.1f}%")
    
    print(f"\n   Sample size: {len(matched)} games with results")
    print(f"   Coverage: {len(matched)/len(df)*100:.1f}% of test games")
    
    if len(matched) < 100:
        print(f"\n   ⚠️  WARNING: Small sample size ({len(matched)} games)")
        print(f"   Results may not be statistically significant")
        print(f"   Recommend: Match more games or collect more data")
    
    print(f"\n✅ P&L calculation complete!")


if __name__ == '__main__':
    main()
