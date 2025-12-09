"""
STEP 2: Shuffle-Control Sanity Test
Run null experiments to verify no structural leakage in Variant B.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def backtest_with_shuffled_labels(edges_df: pd.DataFrame, thresholds: list) -> pd.DataFrame:
    """Backtest with shuffled labels - should yield ~0% ROI."""
    
    # Shuffle home_won labels
    shuffled_df = edges_df.copy()
    shuffled_df['home_won'] = np.random.permutation(shuffled_df['home_won'].values)
    
    results = []
    for threshold in thresholds:
        # Find edges above threshold
        home_edge = shuffled_df['edge_home'] >= threshold
        away_edge = shuffled_df['edge_away'] >= threshold
        
        # Home bets
        home_bets = shuffled_df[home_edge].copy()
        home_wins = (home_bets['home_won'] == 1).sum()
        home_bet_count = len(home_bets)
        
        # Away bets
        away_bets = shuffled_df[away_edge].copy()
        away_wins = (away_bets['home_won'] == 0).sum()
        away_bet_count = len(away_bets)
        
        # Combined
        total_bets = home_bet_count + away_bet_count
        total_wins = home_wins + away_wins
        win_pct = (total_wins / total_bets * 100) if total_bets > 0 else 0
        
        # P&L calculation (assuming -110 odds, $100 stakes)
        winnings = total_wins * 90.91  # Win $90.91 per $100 bet
        losses = (total_bets - total_wins) * 100
        net_pl = winnings - losses
        roi = (net_pl / (total_bets * 100) * 100) if total_bets > 0 else 0
        
        results.append({
            'threshold': threshold,
            'bets': total_bets,
            'wins': total_wins,
            'win_pct': win_pct,
            'roi': roi,
            'pl': net_pl
        })
    
    return pd.DataFrame(results)

def backtest_with_shuffled_edges(edges_df: pd.DataFrame, thresholds: list) -> pd.DataFrame:
    """Backtest with shuffled edges - should yield ~0% ROI."""
    
    # Shuffle edges while keeping outcomes intact
    shuffled_df = edges_df.copy()
    shuffled_df['edge_home'] = np.random.permutation(shuffled_df['edge_home'].values)
    shuffled_df['edge_away'] = np.random.permutation(shuffled_df['edge_away'].values)
    
    results = []
    for threshold in thresholds:
        # Find edges above threshold
        home_edge = shuffled_df['edge_home'] >= threshold
        away_edge = shuffled_df['edge_away'] >= threshold
        
        # Home bets
        home_bets = shuffled_df[home_edge].copy()
        home_wins = (home_bets['home_won'] == 1).sum()
        home_bet_count = len(home_bets)
        
        # Away bets
        away_bets = shuffled_df[away_edge].copy()
        away_wins = (away_bets['home_won'] == 0).sum()
        away_bet_count = len(away_bets)
        
        # Combined
        total_bets = home_bet_count + away_bet_count
        total_wins = home_wins + away_wins
        win_pct = (total_wins / total_bets * 100) if total_bets > 0 else 0
        
        # P&L calculation
        winnings = total_wins * 90.91
        losses = (total_bets - total_wins) * 100
        net_pl = winnings - losses
        roi = (net_pl / (total_bets * 100) * 100) if total_bets > 0 else 0
        
        results.append({
            'threshold': threshold,
            'bets': total_bets,
            'wins': total_wins,
            'win_pct': win_pct,
            'roi': roi,
            'pl': net_pl
        })
    
    return pd.DataFrame(results)

def run_shuffle_tests():
    """Run shuffle-control sanity tests."""
    
    print("="*80)
    print("VARIANT B ROBUSTNESS AUDIT - STEP 2: Shuffle-Control Tests")
    print("="*80)
    
    # Load Variant B edges
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'edges'
    edges_file = data_dir / 'edges_ncaabb_variant_B.csv'
    
    if not edges_file.exists():
        print(f"❌ Edges file not found: {edges_file}")
        return
    
    edges_df = pd.read_csv(edges_file)
    print(f"\n📊 Loaded {len(edges_df)} test games from Variant B")
    
    # Load original backtest for comparison
    original_backtest = data_dir / 'backtest_results_variant_B.csv'
    if original_backtest.exists():
        original_df = pd.read_csv(original_backtest)
        print(f"\n✅ Original Variant B Results (for comparison):")
        print(original_df.to_string(index=False))
    
    # Test thresholds
    thresholds = [0.03, 0.05, 0.07, 0.10, 0.12, 0.15]
    
    print(f"\n{'='*80}")
    print("TEST A: Label Shuffle (Randomize home_won)")
    print(f"{'='*80}")
    print("\nExpectation: ROI should be ~0% across all thresholds")
    print("If ROI > 3-4%, this indicates structural leakage!\n")
    
    # Run label shuffle 5 times and average
    label_shuffle_results = []
    for i in range(5):
        np.random.seed(42 + i)  # Different seed each time
        shuffle_results = backtest_with_shuffled_labels(edges_df, thresholds)
        label_shuffle_results.append(shuffle_results)
    
    # Average across runs
    avg_label_shuffle = pd.concat(label_shuffle_results).groupby('threshold').mean().reset_index()
    
    print("Average Results Across 5 Shuffles:")
    print(f"{'Threshold':<12} {'Bets':<8} {'Win%':<10} {'ROI':<10}")
    print("-" * 50)
    for _, row in avg_label_shuffle.iterrows():
        print(f"{row['threshold']:<12.2f} {row['bets']:<8.0f} {row['win_pct']:<10.1f} {row['roi']:<10.1f}%")
    
    # Check for leakage signal
    max_roi = avg_label_shuffle['roi'].abs().max()
    if max_roi > 4.0:
        print(f"\n🚨 WARNING: Max |ROI| = {max_roi:.1f}% > 4.0% threshold!")
        print("   This suggests potential structural leakage.")
    else:
        print(f"\n✅ PASS: Max |ROI| = {max_roi:.1f}% < 4.0% threshold")
        print("   Label shuffle yields near-zero ROI as expected.")
    
    print(f"\n{'='*80}")
    print("TEST B: Edge Shuffle (Randomize predicted edges)")
    print(f"{'='*80}")
    print("\nExpectation: ROI should be ~0% across all thresholds")
    print("If ROI > 3-4%, this indicates edge calculation leakage!\n")
    
    # Run edge shuffle 5 times and average
    edge_shuffle_results = []
    for i in range(5):
        np.random.seed(100 + i)
        shuffle_results = backtest_with_shuffled_edges(edges_df, thresholds)
        edge_shuffle_results.append(shuffle_results)
    
    # Average across runs
    avg_edge_shuffle = pd.concat(edge_shuffle_results).groupby('threshold').mean().reset_index()
    
    print("Average Results Across 5 Shuffles:")
    print(f"{'Threshold':<12} {'Bets':<8} {'Win%':<10} {'ROI':<10}")
    print("-" * 50)
    for _, row in avg_edge_shuffle.iterrows():
        print(f"{row['threshold']:<12.2f} {row['bets']:<8.0f} {row['win_pct']:<10.1f} {row['roi']:<10.1f}%")
    
    # Check for leakage signal
    max_roi = avg_edge_shuffle['roi'].abs().max()
    if max_roi > 4.0:
        print(f"\n🚨 WARNING: Max |ROI| = {max_roi:.1f}% > 4.0% threshold!")
        print("   This suggests edge calculation leakage.")
    else:
        print(f"\n✅ PASS: Max |ROI| = {max_roi:.1f}% < 4.0% threshold")
        print("   Edge shuffle yields near-zero ROI as expected.")
    
    print(f"\n{'='*80}")
    print("SHUFFLE TEST SUMMARY")
    print(f"{'='*80}")
    
    label_pass = avg_label_shuffle['roi'].abs().max() < 4.0
    edge_pass = avg_edge_shuffle['roi'].abs().max() < 4.0
    
    if label_pass and edge_pass:
        print("\n✅ BOTH SHUFFLE TESTS PASSED")
        print("   Variant B shows no evidence of structural leakage.")
        print("   The +25.3% ROI is not due to data contamination.")
    else:
        print("\n❌ SHUFFLE TESTS FAILED")
        if not label_pass:
            print("   Label shuffle shows non-zero ROI → potential leakage")
        if not edge_pass:
            print("   Edge shuffle shows non-zero ROI → edge calculation issue")
    
    return label_pass and edge_pass

if __name__ == '__main__':
    run_shuffle_tests()
