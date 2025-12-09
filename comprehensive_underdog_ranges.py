"""
Comprehensive analysis of underdogs in 10-point odds ranges from +100 to +400.
Find the sweet spots and danger zones.
"""
import pandas as pd

# Load the edges data
df = pd.read_csv('data/edges/edges_ncaabb_variant_B.csv')

# Find all underdogs +100 to +400
home_dogs = df[(df['home_ml'] >= 100) & (df['home_ml'] < 400)].copy()
home_dogs['bet_side'] = 'home'
home_dogs['odds'] = home_dogs['home_ml']
home_dogs['edge'] = home_dogs['edge_home']
home_dogs['model_prob'] = home_dogs['model_prob_home']
home_dogs['won'] = home_dogs['home_won']

away_dogs = df[(df['away_ml'] >= 100) & (df['away_ml'] < 400)].copy()
away_dogs['bet_side'] = 'away'
away_dogs['odds'] = away_dogs['away_ml']
away_dogs['edge'] = away_dogs['edge_away']
away_dogs['model_prob'] = away_dogs['model_prob_away']
away_dogs['won'] = ~away_dogs['home_won']

dogs = pd.concat([home_dogs, away_dogs])

print('\n' + '='*100)
print('COMPREHENSIVE UNDERDOG ANALYSIS: +100 TO +400 IN 10-POINT RANGES')
print('='*100)

# Define 10-point ranges
odds_ranges = []
for start in range(100, 400, 10):
    end = start + 10
    odds_ranges.append((start, end, f'+{start} to +{end}'))

print(f"\n{'Odds Range':<18} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'Avg Edge':<12} {'Avg Model%':<12} {'P&L':<15} {'ROI'}")
print('-' * 100)

results = []

for min_o, max_o, label in odds_ranges:
    bucket = dogs[(dogs['odds'] >= min_o) & (dogs['odds'] < max_o)]
    
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    avg_edge = bucket['edge'].mean()
    avg_model_prob = bucket['model_prob'].mean()
    
    # Calculate P&L
    pnl = 0
    for _, row in bucket.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl += profit
        else:
            pnl -= 100
    
    roi = (pnl / (len(bucket) * 100)) * 100
    
    results.append({
        'range': label,
        'min_odds': min_o,
        'bets': len(bucket),
        'wins': wins,
        'win_rate': win_rate,
        'avg_edge': avg_edge,
        'avg_model_prob': avg_model_prob,
        'pnl': pnl,
        'roi': roi
    })
    
    roi_marker = '✅' if roi > 0 else '❌'
    print(f"{label:<18} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% {avg_edge*100:<11.2f}% {avg_model_prob*100:<11.2f}% ${pnl:<14,.0f} {roi:>7.2f}% {roi_marker}")

# Summary stats
print('\n' + '='*100)
print('SUMMARY STATISTICS')
print('='*100)

total_bets = sum(r['bets'] for r in results)
total_wins = sum(r['wins'] for r in results)
total_pnl = sum(r['pnl'] for r in results)
overall_win_rate = total_wins / total_bets if total_bets > 0 else 0
overall_roi = (total_pnl / (total_bets * 100)) * 100 if total_bets > 0 else 0

print(f"\nOverall (+100 to +400):")
print(f"  Total Bets: {total_bets}")
print(f"  Total Wins: {total_wins:.0f}")
print(f"  Win Rate: {overall_win_rate*100:.2f}%")
print(f"  Total P&L: ${total_pnl:,.0f}")
print(f"  ROI: {overall_roi:+.2f}%")

# Find best and worst ranges
results_df = pd.DataFrame(results)
best = results_df.loc[results_df['roi'].idxmax()]
worst = results_df.loc[results_df['roi'].idxmin()]

print(f"\n🎯 BEST Range: {best['range']}")
print(f"   {best['bets']:.0f} bets, {best['wins']:.0f} wins ({best['win_rate']*100:.2f}%)")
print(f"   ROI: {best['roi']:+.2f}%")
print(f"   Avg Edge: {best['avg_edge']*100:.2f}%")
print(f"   Avg Model Prob: {best['avg_model_prob']*100:.2f}%")

print(f"\n❌ WORST Range: {worst['range']}")
print(f"   {worst['bets']:.0f} bets, {worst['wins']:.0f} wins ({worst['win_rate']*100:.2f}%)")
print(f"   ROI: {worst['roi']:+.2f}%")
print(f"   Avg Edge: {worst['avg_edge']*100:.2f}%")
print(f"   Avg Model Prob: {worst['avg_model_prob']*100:.2f}%")

# Find profitable ranges
profitable = results_df[results_df['roi'] > 0]
unprofitable = results_df[results_df['roi'] < 0]

print(f"\n💰 PROFITABLE Ranges ({len(profitable)}):")
if len(profitable) > 0:
    for _, row in profitable.sort_values('roi', ascending=False).iterrows():
        print(f"   {row['range']:<18} {row['bets']:<4.0f} bets, {row['wins']:<3.0f} wins, ROI: {row['roi']:>7.2f}%")
else:
    print("   None!")

print(f"\n📉 UNPROFITABLE Ranges ({len(unprofitable)}):")
for _, row in unprofitable.sort_values('roi').head(5).iterrows():
    print(f"   {row['range']:<18} {row['bets']:<4.0f} bets, {row['wins']:<3.0f} wins, ROI: {row['roi']:>7.2f}%")

# Grouped analysis
print('\n' + '='*100)
print('GROUPED ANALYSIS (20-POINT BUCKETS)')
print('='*100)

grouped_ranges = [
    (100, 120, '+100 to +120'),
    (120, 140, '+120 to +140'),
    (140, 160, '+140 to +160'),
    (160, 180, '+160 to +180'),
    (180, 200, '+180 to +200'),
    (200, 250, '+200 to +250'),
    (250, 300, '+250 to +300'),
    (300, 350, '+300 to +350'),
    (350, 400, '+350 to +400'),
]

print(f"\n{'Odds Range':<18} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'Avg Edge':<12} {'P&L':<15} {'ROI'}")
print('-' * 100)

for min_o, max_o, label in grouped_ranges:
    bucket = dogs[(dogs['odds'] >= min_o) & (dogs['odds'] < max_o)]
    
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    avg_edge = bucket['edge'].mean()
    
    pnl = 0
    for _, row in bucket.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl += profit
        else:
            pnl -= 100
    
    roi = (pnl / (len(bucket) * 100)) * 100
    roi_marker = '✅' if roi > 0 else '❌'
    
    print(f"{label:<18} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% {avg_edge*100:<11.2f}% ${pnl:<14,.0f} {roi:>7.2f}% {roi_marker}")

# With 15% edge filter analysis
print('\n' + '='*100)
print('WITH 15% EDGE FILTER (BY 20-POINT BUCKETS)')
print('='*100)

print(f"\n{'Odds Range':<18} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'P&L':<15} {'ROI'}")
print('-' * 100)

for min_o, max_o, label in grouped_ranges:
    bucket = dogs[(dogs['odds'] >= min_o) & (dogs['odds'] < max_o) & (dogs['edge'] >= 0.15)]
    
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    
    pnl = 0
    for _, row in bucket.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl += profit
        else:
            pnl -= 100
    
    roi = (pnl / (len(bucket) * 100)) * 100
    roi_marker = '✅' if roi > 0 else '❌'
    
    print(f"{label:<18} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% ${pnl:<14,.0f} {roi:>7.2f}% {roi_marker}")

print('\n' + '='*100)
print('KEY INSIGHTS')
print('='*100)

# Find the cutoff where things go bad
profitable_ranges = results_df[results_df['roi'] > 0]
unprofitable_ranges = results_df[results_df['roi'] < 0]

if len(profitable_ranges) > 0 and len(unprofitable_ranges) > 0:
    max_profitable_odds = profitable_ranges['min_odds'].max()
    min_unprofitable_odds = unprofitable_ranges['min_odds'].min()
    
    print(f"\n📊 Profitability Cutoff:")
    print(f"   Last profitable range starts at: +{max_profitable_odds}")
    print(f"   First unprofitable range starts at: +{min_unprofitable_odds}")
    
    if max_profitable_odds < min_unprofitable_odds:
        print(f"   ⚠️ Clear cutoff between +{max_profitable_odds} and +{min_unprofitable_odds}")
    else:
        print(f"   ⚠️ Mixed results - profitability varies throughout range")

# Best sample size ranges
print(f"\n📈 Ranges with Best Sample Size (50+ bets):")
large_sample = results_df[results_df['bets'] >= 50].sort_values('roi', ascending=False)
for _, row in large_sample.head(5).iterrows():
    print(f"   {row['range']:<18} {row['bets']:<4.0f} bets, ROI: {row['roi']:>7.2f}%")

print('\n' + '='*100)
