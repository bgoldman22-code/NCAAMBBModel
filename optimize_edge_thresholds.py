"""
Test the profitable odds ranges (+120-140, +160-180, +200-250) 
at every edge threshold from 7% to 15% (1% increments).
"""
import pandas as pd

# Load the edges data
df = pd.read_csv('data/edges/edges_ncaabb_variant_B.csv')

# Find all underdogs
home_dogs = df.copy()
home_dogs['bet_side'] = 'home'
home_dogs['odds'] = home_dogs['home_ml']
home_dogs['edge'] = home_dogs['edge_home']
home_dogs['model_prob'] = home_dogs['model_prob_home']
home_dogs['won'] = home_dogs['home_won']

away_dogs = df.copy()
away_dogs['bet_side'] = 'away'
away_dogs['odds'] = away_dogs['away_ml']
away_dogs['edge'] = away_dogs['edge_away']
away_dogs['model_prob'] = away_dogs['model_prob_away']
away_dogs['won'] = ~away_dogs['home_won']

dogs = pd.concat([home_dogs, away_dogs])

# Define the profitable ranges to test
profitable_ranges = [
    (120, 140, '+120 to +140'),
    (160, 180, '+160 to +180'),
    (200, 250, '+200 to +250'),
]

# Test edge thresholds from 7% to 15%
edge_thresholds = [0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]

print('\n' + '='*120)
print('EDGE THRESHOLD OPTIMIZATION FOR PROFITABLE RANGES')
print('='*120)

for min_odds, max_odds, range_label in profitable_ranges:
    print(f'\n{"="*120}')
    print(f'RANGE: {range_label}')
    print(f'{"="*120}')
    
    # Get all bets in this odds range
    range_bets = dogs[(dogs['odds'] >= min_odds) & (dogs['odds'] < max_odds)]
    
    print(f'\nTotal bets in range: {len(range_bets)}')
    print(f'Wins without filter: {range_bets["won"].sum():.0f}')
    
    # Calculate baseline (no edge filter)
    baseline_wins = range_bets['won'].sum()
    baseline_pnl = 0
    for _, row in range_bets.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            baseline_pnl += profit
        else:
            baseline_pnl -= 100
    baseline_roi = (baseline_pnl / (len(range_bets) * 100)) * 100 if len(range_bets) > 0 else 0
    
    print(f'Baseline ROI (no filter): {baseline_roi:+.2f}%')
    
    print(f'\n{"Edge":<8} {"Bets":<8} {"Wins":<8} {"Win%":<10} {"Avg Edge":<12} {"Avg Model%":<12} {"P&L":<15} {"ROI":<10} {"vs Baseline"}')
    print('-' * 120)
    
    results = []
    
    for edge_threshold in edge_thresholds:
        filtered = range_bets[range_bets['edge'] >= edge_threshold]
        
        if len(filtered) == 0:
            continue
        
        wins = filtered['won'].sum()
        win_rate = wins / len(filtered)
        avg_edge = filtered['edge'].mean()
        avg_model = filtered['model_prob'].mean()
        
        # Calculate P&L
        pnl = 0
        for _, row in filtered.iterrows():
            if row['won']:
                profit = 100 * (row['odds'] / 100)
                pnl += profit
            else:
                pnl -= 100
        
        roi = (pnl / (len(filtered) * 100)) * 100
        roi_improvement = roi - baseline_roi
        
        results.append({
            'edge': edge_threshold,
            'bets': len(filtered),
            'wins': wins,
            'win_rate': win_rate,
            'avg_edge': avg_edge,
            'avg_model': avg_model,
            'pnl': pnl,
            'roi': roi,
            'improvement': roi_improvement
        })
        
        marker = '✅' if roi > baseline_roi else '❌'
        print(f"{edge_threshold*100:<7.0f}% {len(filtered):<8} {wins:<8.0f} {win_rate*100:<9.2f}% {avg_edge*100:<11.2f}% {avg_model*100:<11.2f}% ${pnl:<14,.0f} {roi:>8.2f}% {roi_improvement:>+8.2f}% {marker}")
    
    # Find best edge threshold for this range
    if results:
        results_df = pd.DataFrame(results)
        best = results_df.loc[results_df['roi'].idxmax()]
        
        print(f'\n🎯 BEST EDGE THRESHOLD for {range_label}: {best["edge"]*100:.0f}%')
        print(f'   Bets: {best["bets"]:.0f}')
        print(f'   Win Rate: {best["win_rate"]*100:.2f}%')
        print(f'   ROI: {best["roi"]:+.2f}%')
        print(f'   Improvement over baseline: {best["improvement"]:+.2f}%')

# Now test all three ranges combined with different edge thresholds
print(f'\n{"="*120}')
print('COMBINED ANALYSIS: ALL THREE PROFITABLE RANGES')
print(f'{"="*120}')

print(f'\n{"Edge":<8} {"Bets":<8} {"Wins":<8} {"Win%":<10} {"P&L":<15} {"ROI":<10} {"Breakdown"}')
print('-' * 120)

for edge_threshold in edge_thresholds:
    combined_bets = dogs[
        (
            ((dogs['odds'] >= 120) & (dogs['odds'] < 140)) |
            ((dogs['odds'] >= 160) & (dogs['odds'] < 180)) |
            ((dogs['odds'] >= 200) & (dogs['odds'] < 250))
        ) &
        (dogs['edge'] >= edge_threshold)
    ]
    
    if len(combined_bets) == 0:
        continue
    
    wins = combined_bets['won'].sum()
    win_rate = wins / len(combined_bets)
    
    # Calculate P&L
    pnl = 0
    for _, row in combined_bets.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl += profit
        else:
            pnl -= 100
    
    roi = (pnl / (len(combined_bets) * 100)) * 100
    
    # Breakdown by range
    range1 = combined_bets[(combined_bets['odds'] >= 120) & (combined_bets['odds'] < 140)]
    range2 = combined_bets[(combined_bets['odds'] >= 160) & (combined_bets['odds'] < 180)]
    range3 = combined_bets[(combined_bets['odds'] >= 200) & (combined_bets['odds'] < 250)]
    
    breakdown = f"120-140:{len(range1)}, 160-180:{len(range2)}, 200-250:{len(range3)}"
    
    print(f"{edge_threshold*100:<7.0f}% {len(combined_bets):<8} {wins:<8.0f} {win_rate*100:<9.2f}% ${pnl:<14,.0f} {roi:>8.2f}% {breakdown}")

# Summary recommendations
print(f'\n{"="*120}')
print('SUMMARY & RECOMMENDATIONS')
print(f'{"="*120}')

print('\nBased on this analysis, here are the optimal edge thresholds for each range:')
print('\nTo maximize ROI while maintaining sample size:')
print('  • Lower edge threshold = More bets, but some unprofitable')
print('  • Higher edge threshold = Fewer bets, but higher win rate')
print('\nLook for the edge % where ROI peaks before sample size becomes too small.')

# Test with original 15% edge across all ranges for comparison
print(f'\n{"="*120}')
print('COMPARISON: Current 15% Edge Filter vs Optimized')
print(f'{"="*120}')

current_system = dogs[
    (
        ((dogs['odds'] >= 120) & (dogs['odds'] < 140)) |
        ((dogs['odds'] >= 160) & (dogs['odds'] < 180)) |
        ((dogs['odds'] >= 200) & (dogs['odds'] < 250))
    ) &
    (dogs['edge'] >= 0.15)
]

if len(current_system) > 0:
    wins = current_system['won'].sum()
    pnl = 0
    for _, row in current_system.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl += profit
        else:
            pnl -= 100
    roi = (pnl / (len(current_system) * 100)) * 100
    
    print(f'\nCurrent System (15% edge):')
    print(f'  Bets: {len(current_system)}')
    print(f'  Wins: {wins:.0f}')
    print(f'  Win Rate: {wins/len(current_system)*100:.2f}%')
    print(f'  ROI: {roi:+.2f}%')

print('\n' + '='*120)
