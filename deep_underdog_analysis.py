"""
Deep analysis of all +400 or greater bets to find patterns in wins vs losses.
Analyze every possible factor available in the data.
"""
import pandas as pd
import numpy as np

# Load the edges data
df = pd.read_csv('data/edges/edges_ncaabb_variant_B.csv')

# Find ALL +400 or greater bets (no edge filter)
home_underdogs = df[df['home_ml'] >= 400].copy()
home_underdogs['bet_side'] = 'home'
home_underdogs['bet_team'] = home_underdogs['home_team']
home_underdogs['opp_team'] = home_underdogs['away_team']
home_underdogs['odds'] = home_underdogs['home_ml']
home_underdogs['edge'] = home_underdogs['edge_home']
home_underdogs['model_prob'] = home_underdogs['model_prob_home']
home_underdogs['market_prob'] = home_underdogs['home_implied_prob']
home_underdogs['opp_odds'] = home_underdogs['away_ml']
home_underdogs['won'] = home_underdogs['home_won']
home_underdogs['score'] = home_underdogs['home_score']
home_underdogs['opp_score'] = home_underdogs['away_score']

away_underdogs = df[df['away_ml'] >= 400].copy()
away_underdogs['bet_side'] = 'away'
away_underdogs['bet_team'] = away_underdogs['away_team']
away_underdogs['opp_team'] = away_underdogs['home_team']
away_underdogs['odds'] = away_underdogs['away_ml']
away_underdogs['edge'] = away_underdogs['edge_away']
away_underdogs['model_prob'] = away_underdogs['model_prob_away']
away_underdogs['market_prob'] = away_underdogs['away_implied_prob']
away_underdogs['opp_odds'] = away_underdogs['home_ml']
away_underdogs['won'] = ~away_underdogs['home_won']
away_underdogs['score'] = away_underdogs['away_score']
away_underdogs['opp_score'] = away_underdogs['home_score']

all_underdogs = pd.concat([home_underdogs, away_underdogs])

# Calculate additional metrics
all_underdogs['margin'] = all_underdogs['score'] - all_underdogs['opp_score']
all_underdogs['total_points'] = all_underdogs['score'] + all_underdogs['opp_score']
all_underdogs['model_vs_market'] = all_underdogs['model_prob'] - all_underdogs['market_prob']
all_underdogs['model_vs_market_ratio'] = all_underdogs['model_prob'] / all_underdogs['market_prob']
all_underdogs['date'] = pd.to_datetime(all_underdogs['date'])
all_underdogs['month'] = all_underdogs['date'].dt.month
all_underdogs['day_of_week'] = all_underdogs['date'].dt.dayofweek

print('\n' + '='*100)
print('DEEP ANALYSIS: ALL +400 OR GREATER BETS')
print('='*100)
print(f'\nTotal bets: {len(all_underdogs)}')
print(f'Wins: {all_underdogs["won"].sum():.0f}')
print(f'Losses: {(~all_underdogs["won"]).sum():.0f}')
print(f'Win Rate: {all_underdogs["won"].mean()*100:.2f}%')

wins = all_underdogs[all_underdogs['won']]
losses = all_underdogs[~all_underdogs['won']]

print('\n' + '='*100)
print('SECTION 1: THE WINS - DETAILED BREAKDOWN')
print('='*100)

for idx, row in wins.iterrows():
    print(f"\n{'='*100}")
    print(f"✅ WIN: {row['bet_team']} (+{row['odds']:.0f}) beat {row['opp_team']} ({row['score']:.0f}-{row['opp_score']:.0f})")
    print(f"{'='*100}")
    print(f"Date: {row['date'].strftime('%Y-%m-%d')} ({row['date'].strftime('%A')}, Month {row['month']})")
    print(f"Margin: {row['margin']:.0f} points")
    print(f"Total Points: {row['total_points']:.0f}")
    print(f"")
    print(f"Odds & Probabilities:")
    print(f"  Underdog Odds: +{row['odds']:.0f}")
    print(f"  Favorite Odds: {row['opp_odds']:.0f}")
    print(f"  Model Win Prob: {row['model_prob']*100:.2f}%")
    print(f"  Market Implied Prob: {row['market_prob']*100:.2f}%")
    print(f"  Edge: {row['edge']*100:.1f}%")
    print(f"  Model vs Market: {row['model_vs_market']*100:.2f}% ({row['model_vs_market_ratio']:.2f}x)")

print('\n' + '='*100)
print('SECTION 2: STATISTICAL COMPARISON - WINS VS LOSSES')
print('='*100)

def print_comparison(metric_name, wins_val, losses_val, format_str='.2f', suffix=''):
    diff = wins_val - losses_val
    pct_diff = ((wins_val / losses_val - 1) * 100) if losses_val != 0 else 0
    print(f"{metric_name:<40} Wins: {wins_val:{format_str}}{suffix}  |  Losses: {losses_val:{format_str}}{suffix}  |  Diff: {diff:+{format_str}}{suffix} ({pct_diff:+.1f}%)")

print(f"\n{'Metric':<40} {'Wins':<20} | {'Losses':<20} | {'Difference'}")
print('-' * 100)

print_comparison('Average Odds', wins['odds'].mean(), losses['odds'].mean(), '.0f', '')
print_comparison('Average Model Win Prob (%)', wins['model_prob'].mean()*100, losses['model_prob'].mean()*100, '.2f', '%')
print_comparison('Average Market Prob (%)', wins['market_prob'].mean()*100, losses['market_prob'].mean()*100, '.2f', '%')
print_comparison('Average Edge (%)', wins['edge'].mean()*100, losses['edge'].mean()*100, '.2f', '%')
print_comparison('Average Model/Market Ratio', wins['model_vs_market_ratio'].mean(), losses['model_vs_market_ratio'].mean(), '.2f', 'x')
print_comparison('Average Opponent Odds', wins['opp_odds'].mean(), losses['opp_odds'].mean(), '.0f', '')
print_comparison('Average Final Score', wins['score'].mean(), losses['score'].mean(), '.1f', '')
print_comparison('Average Opponent Score', wins['opp_score'].mean(), losses['opp_score'].mean(), '.1f', '')
print_comparison('Average Total Points', wins['total_points'].mean(), losses['total_points'].mean(), '.1f', '')

print('\n' + '='*100)
print('SECTION 3: EDGE ANALYSIS')
print('='*100)

print(f"\nPositive Edge Bets (+400 or greater):")
pos_edge = all_underdogs[all_underdogs['edge'] > 0]
print(f"  Total: {len(pos_edge)}")
print(f"  Wins: {pos_edge['won'].sum():.0f}")
print(f"  Win Rate: {pos_edge['won'].mean()*100:.2f}%")
print(f"  Avg Edge: {pos_edge['edge'].mean()*100:.2f}%")
print(f"  Avg Model Prob: {pos_edge['model_prob'].mean()*100:.2f}%")

print(f"\nNegative Edge Bets (+400 or greater):")
neg_edge = all_underdogs[all_underdogs['edge'] < 0]
print(f"  Total: {len(neg_edge)}")
print(f"  Wins: {neg_edge['won'].sum():.0f}")
print(f"  Win Rate: {neg_edge['won'].mean()*100:.2f}%")
print(f"  Avg Edge: {neg_edge['edge'].mean()*100:.2f}%")
print(f"  Avg Model Prob: {neg_edge['model_prob'].mean()*100:.2f}%")

# Edge buckets
print(f"\nBy Edge Bucket:")
edge_buckets = [
    (-1.0, -0.20, 'Very Negative (<-20%)'),
    (-0.20, -0.10, 'Negative (-20% to -10%)'),
    (-0.10, -0.05, 'Slightly Negative (-10% to -5%)'),
    (-0.05, 0.0, 'Near Zero (-5% to 0%)'),
    (0.0, 0.05, 'Slightly Positive (0% to 5%)'),
    (0.05, 0.10, 'Positive (5% to 10%)'),
    (0.10, 0.15, 'Strong Positive (10% to 15%)'),
    (0.15, 1.0, 'Very Strong Positive (15%+)')
]

for min_e, max_e, label in edge_buckets:
    bucket = all_underdogs[(all_underdogs['edge'] >= min_e) & (all_underdogs['edge'] < max_e)]
    if len(bucket) > 0:
        wins_in_bucket = bucket['won'].sum()
        win_rate = wins_in_bucket / len(bucket)
        print(f"  {label:<35} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%)")

print('\n' + '='*100)
print('SECTION 4: MODEL PROBABILITY ANALYSIS')
print('='*100)

prob_buckets = [
    (0.0, 0.05, '0-5%'),
    (0.05, 0.10, '5-10%'),
    (0.10, 0.15, '10-15%'),
    (0.15, 0.20, '15-20%'),
    (0.20, 0.30, '20-30%'),
    (0.30, 1.0, '30%+')
]

print(f"\nBy Model Win Probability:")
for min_p, max_p, label in prob_buckets:
    bucket = all_underdogs[(all_underdogs['model_prob'] >= min_p) & (all_underdogs['model_prob'] < max_p)]
    if len(bucket) > 0:
        wins_in_bucket = bucket['won'].sum()
        win_rate = wins_in_bucket / len(bucket)
        avg_edge = bucket['edge'].mean()
        print(f"  {label:<15} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%), Avg Edge: {avg_edge*100:>6.2f}%")

print('\n' + '='*100)
print('SECTION 5: ODDS RANGE ANALYSIS')
print('='*100)

odds_buckets = [
    (400, 600, '+400 to +600'),
    (600, 800, '+600 to +800'),
    (800, 1000, '+800 to +1000'),
    (1000, 1500, '+1000 to +1500'),
    (1500, 2000, '+1500 to +2000'),
    (2000, 100000, '+2000+')
]

print(f"\nBy Underdog Odds Range:")
for min_o, max_o, label in odds_buckets:
    bucket = all_underdogs[(all_underdogs['odds'] >= min_o) & (all_underdogs['odds'] < max_o)]
    if len(bucket) > 0:
        wins_in_bucket = bucket['won'].sum()
        win_rate = wins_in_bucket / len(bucket)
        avg_model = bucket['model_prob'].mean()
        avg_edge = bucket['edge'].mean()
        print(f"  {label:<20} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%), Model: {avg_model*100:>5.2f}%, Edge: {avg_edge*100:>6.2f}%")

print('\n' + '='*100)
print('SECTION 6: OPPONENT STRENGTH ANALYSIS')
print('='*100)

# Analyze by opponent odds (how strong was the favorite)
opp_odds_buckets = [
    (-10000, -500, 'Huge Favorite (<-500)'),
    (-500, -300, 'Strong Favorite (-500 to -300)'),
    (-300, -200, 'Moderate Favorite (-300 to -200)'),
    (-200, -150, 'Slight Favorite (-200 to -150)'),
    (-150, 0, 'Pick\'em-ish (-150 to 0)')
]

print(f"\nBy Opponent Odds (Favorite Strength):")
for min_o, max_o, label in opp_odds_buckets:
    bucket = all_underdogs[(all_underdogs['opp_odds'] >= min_o) & (all_underdogs['opp_odds'] < max_o)]
    if len(bucket) > 0:
        wins_in_bucket = bucket['won'].sum()
        win_rate = wins_in_bucket / len(bucket)
        avg_model = bucket['model_prob'].mean()
        avg_edge = bucket['edge'].mean()
        print(f"  {label:<35} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%), Model: {avg_model*100:>5.2f}%, Edge: {avg_edge*100:>6.2f}%")

print('\n' + '='*100)
print('SECTION 7: TEMPORAL ANALYSIS')
print('='*100)

print(f"\nBy Month:")
for month in sorted(all_underdogs['month'].unique()):
    bucket = all_underdogs[all_underdogs['month'] == month]
    wins_in_bucket = bucket['won'].sum()
    win_rate = wins_in_bucket / len(bucket)
    month_name = pd.Timestamp(2024, month, 1).strftime('%B')
    print(f"  {month_name:<15} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%)")

print(f"\nBy Day of Week:")
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
for day_num in range(7):
    bucket = all_underdogs[all_underdogs['day_of_week'] == day_num]
    if len(bucket) > 0:
        wins_in_bucket = bucket['won'].sum()
        win_rate = wins_in_bucket / len(bucket)
        print(f"  {day_names[day_num]:<15} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%)")

print('\n' + '='*100)
print('SECTION 8: MODEL/MARKET DISAGREEMENT ANALYSIS')
print('='*100)

# Model vs Market ratio analysis
ratio_buckets = [
    (0.0, 0.5, 'Model Much Lower (<0.5x)'),
    (0.5, 0.8, 'Model Lower (0.5x-0.8x)'),
    (0.8, 1.2, 'Model Similar (0.8x-1.2x)'),
    (1.2, 2.0, 'Model Higher (1.2x-2.0x)'),
    (2.0, 100, 'Model Much Higher (2.0x+)')
]

print(f"\nBy Model/Market Probability Ratio:")
for min_r, max_r, label in ratio_buckets:
    bucket = all_underdogs[(all_underdogs['model_vs_market_ratio'] >= min_r) & (all_underdogs['model_vs_market_ratio'] < max_r)]
    if len(bucket) > 0:
        wins_in_bucket = bucket['won'].sum()
        win_rate = wins_in_bucket / len(bucket)
        avg_edge = bucket['edge'].mean()
        avg_model = bucket['model_prob'].mean()
        print(f"  {label:<30} {len(bucket):>3} bets, {wins_in_bucket:>2.0f} wins ({win_rate*100:>5.2f}%), Model: {avg_model*100:>5.2f}%, Edge: {avg_edge*100:>6.2f}%")

print('\n' + '='*100)
print('SECTION 9: KEY INSIGHTS & PATTERNS')
print('='*100)

print(f"\n🔍 Pattern Detection:")

# Check if wins have higher model prob than losses
if wins['model_prob'].mean() > losses['model_prob'].mean():
    diff = (wins['model_prob'].mean() - losses['model_prob'].mean()) * 100
    print(f"✓ Wins had {diff:.2f}% higher model probability on average")
else:
    print(f"✗ Wins did NOT have higher model probability than losses")

# Check if wins have positive edge more often
pos_edge_win_rate = pos_edge['won'].mean() if len(pos_edge) > 0 else 0
neg_edge_win_rate = neg_edge['won'].mean() if len(neg_edge) > 0 else 0
if pos_edge_win_rate > neg_edge_win_rate:
    print(f"✓ Positive edge bets won {pos_edge_win_rate*100:.2f}% vs negative edge {neg_edge_win_rate*100:.2f}%")
else:
    print(f"✗ Positive edge did NOT improve win rate ({pos_edge_win_rate*100:.2f}% vs {neg_edge_win_rate*100:.2f}%)")

# Check close games
if len(wins) > 0:
    avg_margin = wins['margin'].mean()
    print(f"✓ Winning underdogs won by average of {avg_margin:.1f} points")

# Check if lower odds (less extreme underdogs) win more
low_odds = all_underdogs[all_underdogs['odds'] < 800]
high_odds = all_underdogs[all_underdogs['odds'] >= 800]
if low_odds['won'].mean() > high_odds['won'].mean():
    print(f"✓ Lower odds (+400-800) won {low_odds['won'].mean()*100:.2f}% vs higher odds (800+) {high_odds['won'].mean()*100:.2f}%")

print('\n' + '='*100)
print('SECTION 10: RECOMMENDED FILTERS FOR +400 BETS')
print('='*100)

print("\nBased on this analysis, here are filters that might improve results:")

# Find the best performing segments
best_model_prob = None
best_win_rate = 0
for min_p, max_p, label in prob_buckets:
    bucket = all_underdogs[(all_underdogs['model_prob'] >= min_p) & (all_underdogs['model_prob'] < max_p)]
    if len(bucket) >= 5 and bucket['won'].mean() > best_win_rate:
        best_win_rate = bucket['won'].mean()
        best_model_prob = label

if best_model_prob:
    print(f"\n1. Model Probability: Best performing bucket was {best_model_prob} ({best_win_rate*100:.2f}% win rate)")

# Find best odds range
best_odds = None
best_odds_win_rate = 0
for min_o, max_o, label in odds_buckets:
    bucket = all_underdogs[(all_underdogs['odds'] >= min_o) & (all_underdogs['odds'] < max_o)]
    if len(bucket) >= 5 and bucket['won'].mean() > best_odds_win_rate:
        best_odds_win_rate = bucket['won'].mean()
        best_odds = label

if best_odds:
    print(f"2. Odds Range: Best performing bucket was {best_odds} ({best_odds_win_rate*100:.2f}% win rate)")

# Edge recommendation
if pos_edge_win_rate > 0.05:  # At least 5% win rate
    print(f"3. Edge: Positive edge bets had {pos_edge_win_rate*100:.2f}% win rate (Total: {len(pos_edge)} bets, {pos_edge['won'].sum():.0f} wins)")
else:
    print(f"3. Edge: Even positive edge didn't help much ({pos_edge_win_rate*100:.2f}% win rate)")

print("\n" + "="*100)
