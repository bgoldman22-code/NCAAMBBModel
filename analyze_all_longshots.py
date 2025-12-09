"""Analyze ALL longshots (+900 or more) regardless of edge threshold."""
import pandas as pd
import numpy as np

# Load the edges data
df = pd.read_csv('data/edges/edges_ncaabb_variant_B.csv')

# Find ALL longshots +900 or more (no edge filter)
home_longshots = df[df['home_ml'] >= 900].copy()
home_longshots['bet_side'] = 'home'
home_longshots['bet_team'] = home_longshots['home_team']
home_longshots['opp_team'] = home_longshots['away_team']
home_longshots['odds'] = home_longshots['home_ml']
home_longshots['edge'] = home_longshots['edge_home']
home_longshots['model_prob'] = home_longshots['model_prob_home']
home_longshots['market_prob'] = home_longshots['home_implied_prob']
home_longshots['won'] = home_longshots['home_won']

away_longshots = df[df['away_ml'] >= 900].copy()
away_longshots['bet_side'] = 'away'
away_longshots['bet_team'] = away_longshots['away_team']
away_longshots['opp_team'] = away_longshots['home_team']
away_longshots['odds'] = away_longshots['away_ml']
away_longshots['edge'] = away_longshots['edge_away']
away_longshots['model_prob'] = away_longshots['model_prob_away']
away_longshots['market_prob'] = away_longshots['away_implied_prob']
away_longshots['won'] = ~away_longshots['home_won']

all_longshots = pd.concat([home_longshots, away_longshots]).sort_values('odds', ascending=False)

print('\n' + '='*100)
print('ALL LONGSHOTS (+900 OR MORE) IN TEST SET')
print('='*100)
print(f'\nTotal longshots: {len(all_longshots)}')
print(f'Wins: {all_longshots["won"].sum():.0f}')
print(f'Losses: {(~all_longshots["won"]).sum():.0f}')
print(f'Win Rate: {all_longshots["won"].mean()*100:.2f}%')
print(f'Average Model Prob: {all_longshots["model_prob"].mean()*100:.2f}%')
print(f'Average Market Prob: {all_longshots["market_prob"].mean()*100:.2f}%')

# Show the WINS
wins = all_longshots[all_longshots['won']]
print(f'\n' + '='*100)
print(f'THE {len(wins)} LONGSHOT WINS:')
print('='*100)

for idx, row in wins.iterrows():
    payout = 100 * (row['odds'] / 100)
    print(f"\n✅ {row['bet_team']} (+{row['odds']:.0f}) beat {row['opp_team']}")
    print(f"   Date: {row['date']}")
    print(f"   Score: {row['home_team']} {row['home_score']:.0f} - {row['away_score']:.0f} {row['away_team']}")
    print(f"   Model Win Prob: {row['model_prob']*100:.2f}%")
    print(f"   Market Implied Prob: {row['market_prob']*100:.2f}%")
    print(f"   Edge: {row['edge']*100:.1f}%")
    print(f"   Profit: +${payout:.0f} on $100 bet")

# Analyze by edge buckets
print(f'\n' + '='*100)
print('PERFORMANCE BY EDGE BUCKET:')
print('='*100)

edge_buckets = [
    (-1.0, 0.0, 'Negative Edge'),
    (0.0, 0.05, '0-5% Edge'),
    (0.05, 0.10, '5-10% Edge'),
    (0.10, 0.15, '10-15% Edge'),
    (0.15, 0.20, '15-20% Edge'),
    (0.20, 1.0, '20%+ Edge')
]

print(f"\n{'Edge Bucket':<20} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'Avg Model Prob':<18} {'P&L ($100 units)'}")
print('-' * 100)

for min_edge, max_edge, label in edge_buckets:
    bucket = all_longshots[(all_longshots['edge'] >= min_edge) & (all_longshots['edge'] < max_edge)]
    
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    avg_model_prob = bucket['model_prob'].mean()
    
    # Calculate P&L
    pnl = 0
    for _, row in bucket.iterrows():
        if row['won']:
            pnl += 100 * (row['odds'] / 100)
        else:
            pnl -= 100
    
    roi = (pnl / (len(bucket) * 100)) * 100
    
    print(f"{label:<20} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% {avg_model_prob*100:<17.2f}% ${pnl:>10,.0f} ({roi:+.1f}%)")

# Analyze by odds ranges
print(f'\n' + '='*100)
print('PERFORMANCE BY ODDS RANGE:')
print('='*100)

odds_buckets = [
    (900, 1200, '+900 to +1200'),
    (1200, 1500, '+1200 to +1500'),
    (1500, 2000, '+1500 to +2000'),
    (2000, 5000, '+2000 to +5000'),
    (5000, 100000, '+5000+')
]

print(f"\n{'Odds Range':<20} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'Avg Model Prob':<18} {'P&L ($100 units)'}")
print('-' * 100)

for min_odds, max_odds, label in odds_buckets:
    bucket = all_longshots[(all_longshots['odds'] >= min_odds) & (all_longshots['odds'] < max_odds)]
    
    if len(bucket) == 0:
        continue
    
    wins = bucket['won'].sum()
    win_rate = wins / len(bucket)
    avg_model_prob = bucket['model_prob'].mean()
    
    # Calculate P&L
    pnl = 0
    for _, row in bucket.iterrows():
        if row['won']:
            pnl += 100 * (row['odds'] / 100)
        else:
            pnl -= 100
    
    roi = (pnl / (len(bucket) * 100)) * 100
    
    print(f"{label:<20} {len(bucket):<8} {wins:<8.0f} {win_rate*100:<9.2f}% {avg_model_prob*100:<17.2f}% ${pnl:>10,.0f} ({roi:+.1f}%)")

# Show ALL longshots with positive edge
print(f'\n' + '='*100)
print('ALL LONGSHOTS WITH POSITIVE EDGE (sorted by edge):')
print('='*100)

positive_edge = all_longshots[all_longshots['edge'] > 0].sort_values('edge', ascending=False)
print(f"\nTotal with positive edge: {len(positive_edge)}")
print(f"Wins: {positive_edge['won'].sum():.0f}")
print(f"Win rate: {positive_edge['won'].mean()*100:.2f}%")

print(f"\n{'Result':<8} {'Team':<25} {'Odds':<10} {'Edge':<10} {'Model%':<10} {'Market%':<10} {'Date'}")
print('-' * 100)

for idx, row in positive_edge.head(30).iterrows():  # Show top 30
    result = '✅ WIN' if row['won'] else '❌ LOSS'
    print(f"{result:<8} {row['bet_team']:<25} +{row['odds']:<9.0f} {row['edge']*100:<9.1f}% {row['model_prob']*100:<9.2f}% {row['market_prob']*100:<9.2f}% {row['date']}")
