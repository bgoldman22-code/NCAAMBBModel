"""Quick script to examine longshot bets in detail."""
import pandas as pd

# Load the edges data
df = pd.read_csv('data/edges/edges_ncaabb_variant_B.csv')

# Find longshot bets (+1000 or more with edge >= 15%)
home_longshots = df[(df['home_ml'] >= 1000) & (df['edge_home'] >= 0.15)].copy()
home_longshots['bet_side'] = 'home'
home_longshots['bet_team'] = home_longshots['home_team']
home_longshots['opp_team'] = home_longshots['away_team']
home_longshots['odds'] = home_longshots['home_ml']
home_longshots['edge'] = home_longshots['edge_home']
home_longshots['model_prob'] = home_longshots['model_prob_home']
home_longshots['won'] = home_longshots['home_won']

away_longshots = df[(df['away_ml'] >= 1000) & (df['edge_away'] >= 0.15)].copy()
away_longshots['bet_side'] = 'away'
away_longshots['bet_team'] = away_longshots['away_team']
away_longshots['opp_team'] = away_longshots['home_team']
away_longshots['odds'] = away_longshots['away_ml']
away_longshots['edge'] = away_longshots['edge_away']
away_longshots['model_prob'] = away_longshots['model_prob_away']
away_longshots['won'] = ~away_longshots['home_won']

longshots = pd.concat([home_longshots, away_longshots])

print('\n' + '='*80)
print('LONGSHOT BETS (+1000 or more) WITH 15%+ EDGE')
print('='*80)
print(f'\nTotal longshot bets: {len(longshots)}')
print(f'Won: {longshots["won"].sum():.0f}')
print(f'Lost: {(~longshots["won"]).sum():.0f}')
print(f'Win Rate: {longshots["won"].mean()*100:.1f}%')
print('\nDetailed breakdown:')
print('-'*80)

for idx, row in longshots.iterrows():
    result = '✅ WON' if row['won'] else '❌ LOST'
    print(f"\n{result}: {row['bet_team']} (+{row['odds']:.0f}) vs {row['opp_team']}")
    print(f"  Date: {row['date']}")
    print(f"  Model Win Prob: {row['model_prob']*100:.1f}%")
    print(f"  Market Implied Prob: {(100/(row['odds']+100))*100:.2f}%")
    print(f"  Edge: {row['edge']*100:.1f}%")
    print(f"  Score: {row['home_team']} {row['home_score']:.0f} - {row['away_score']:.0f} {row['away_team']}")
    
    if row['won']:
        payout = 100 * (row['odds'] / 100)
        print(f"  Profit: +${payout:.0f} on $100 bet")
    else:
        print(f"  Loss: -$100")

print('\n' + '='*80)
print('COMPARISON: All longshots vs filtered by edge')
print('='*80)

# All longshots (no edge filter)
all_home_longshots = df[df['home_ml'] >= 1000].copy()
all_home_longshots['model_prob'] = all_home_longshots['model_prob_home']
all_home_longshots['won'] = all_home_longshots['home_won']

all_away_longshots = df[df['away_ml'] >= 1000].copy()
all_away_longshots['model_prob'] = all_away_longshots['model_prob_away']
all_away_longshots['won'] = ~all_away_longshots['home_won']

all_longshots = pd.concat([all_home_longshots, all_away_longshots])

print(f'\nALL longshots (+1000 or more):')
print(f'  Total: {len(all_longshots)}')
print(f'  Won: {all_longshots["won"].sum():.0f}')
print(f'  Win Rate: {all_longshots["won"].mean()*100:.1f}%')
print(f'  Avg Model Prob: {all_longshots["model_prob"].mean()*100:.1f}%')

print(f'\nLongshots with 15%+ edge:')
print(f'  Total: {len(longshots)}')
print(f'  Won: {longshots["won"].sum():.0f}')
print(f'  Win Rate: {longshots["won"].mean()*100:.1f}%')
print(f'  Avg Model Prob: {longshots["model_prob"].mean()*100:.1f}%')
