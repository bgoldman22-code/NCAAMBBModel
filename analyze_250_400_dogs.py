"""Analyze +250 to +400 underdogs for ROI."""
import pandas as pd

# Load the edges data
df = pd.read_csv('data/edges/edges_ncaabb_variant_B.csv')

# Find +250 to +400 underdogs
home_dogs = df[(df['home_ml'] >= 250) & (df['home_ml'] < 400)].copy()
home_dogs['bet_side'] = 'home'
home_dogs['odds'] = home_dogs['home_ml']
home_dogs['edge'] = home_dogs['edge_home']
home_dogs['won'] = home_dogs['home_won']

away_dogs = df[(df['away_ml'] >= 250) & (df['away_ml'] < 400)].copy()
away_dogs['bet_side'] = 'away'
away_dogs['odds'] = away_dogs['away_ml']
away_dogs['edge'] = away_dogs['edge_away']
away_dogs['won'] = ~away_dogs['home_won']

dogs = pd.concat([home_dogs, away_dogs])

print('\n' + '='*80)
print('+250 TO +400 UNDERDOGS ANALYSIS')
print('='*80)

print(f'\nTotal bets: {len(dogs)}')
print(f'Wins: {dogs["won"].sum():.0f}')
print(f'Losses: {(~dogs["won"]).sum():.0f}')
print(f'Win Rate: {dogs["won"].mean()*100:.2f}%')

# Calculate P&L
pnl = 0
for _, row in dogs.iterrows():
    if row['won']:
        profit = 100 * (row['odds'] / 100)
        pnl += profit
    else:
        pnl -= 100

roi = (pnl / (len(dogs) * 100)) * 100

print(f'\nP&L ($100 units): ${pnl:,.0f}')
print(f'ROI: {roi:+.2f}%')

# With 15% edge filter
print('\n' + '-'*80)
print('WITH 15% EDGE FILTER:')
print('-'*80)

pos_edge = dogs[dogs['edge'] >= 0.15]
print(f'\nTotal bets: {len(pos_edge)}')
print(f'Wins: {pos_edge["won"].sum():.0f}')
print(f'Win Rate: {pos_edge["won"].mean()*100:.2f}%' if len(pos_edge) > 0 else 'N/A')
print(f'Avg Edge: {pos_edge["edge"].mean()*100:.2f}%' if len(pos_edge) > 0 else 'N/A')

pnl_edge = 0
for _, row in pos_edge.iterrows():
    if row['won']:
        profit = 100 * (row['odds'] / 100)
        pnl_edge += profit
    else:
        pnl_edge -= 100

roi_edge = (pnl_edge / (len(pos_edge) * 100)) * 100 if len(pos_edge) > 0 else 0

print(f'\nP&L ($100 units): ${pnl_edge:,.0f}' if len(pos_edge) > 0 else 'N/A')
print(f'ROI: {roi_edge:+.2f}%' if len(pos_edge) > 0 else 'N/A')

# By edge buckets
print('\n' + '-'*80)
print('BY EDGE BUCKET:')
print('-'*80)

edge_buckets = [
    (-1.0, 0.0, 'Negative Edge'),
    (0.0, 0.10, '0-10% Edge'),
    (0.10, 0.15, '10-15% Edge'),
    (0.15, 0.20, '15-20% Edge'),
    (0.20, 0.25, '20-25% Edge'),
    (0.25, 1.0, '25%+ Edge')
]

print(f"\n{'Edge Bucket':<20} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'P&L':<15} {'ROI'}")
print('-'*80)

for min_e, max_e, label in edge_buckets:
    bucket = dogs[(dogs['edge'] >= min_e) & (dogs['edge'] < max_e)]
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    
    pnl_bucket = 0
    for _, row in bucket.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl_bucket += profit
        else:
            pnl_bucket -= 100
    
    roi_bucket = (pnl_bucket / (len(bucket) * 100)) * 100
    
    print(f"{label:<20} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% ${pnl_bucket:<14,.0f} {roi_bucket:+.2f}%")

# By odds subranges
print('\n' + '-'*80)
print('BY ODDS SUBRANGE:')
print('-'*80)

odds_buckets = [
    (250, 300, '+250 to +300'),
    (300, 350, '+300 to +350'),
    (350, 400, '+350 to +400')
]

print(f"\n{'Odds Range':<20} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'P&L':<15} {'ROI'}")
print('-'*80)

for min_o, max_o, label in odds_buckets:
    bucket = dogs[(dogs['odds'] >= min_o) & (dogs['odds'] < max_o)]
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    
    pnl_bucket = 0
    for _, row in bucket.iterrows():
        if row['won']:
            profit = 100 * (row['odds'] / 100)
            pnl_bucket += profit
        else:
            pnl_bucket -= 100
    
    roi_bucket = (pnl_bucket / (len(bucket) * 100)) * 100
    
    print(f"{label:<20} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% ${pnl_bucket:<14,.0f} {roi_bucket:+.2f}%")
