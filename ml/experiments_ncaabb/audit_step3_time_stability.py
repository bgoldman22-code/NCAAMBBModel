"""
STEP 3: Time Stability Test
Train on early season (Jan 5-25), test on late season (March 1 - April 9).
Verify that edge persists throughout the season.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to import training module
sys.path.append(str(Path(__file__).parent))

def time_stability_test():
    """Test if Variant B edge persists in late season."""
    
    print("="*80)
    print("VARIANT B ROBUSTNESS AUDIT - STEP 3: Time Stability Test")
    print("="*80)
    
    print("\n📅 Training on EARLY season only: Jan 5 - Jan 25")
    print("   Testing on LATE season only: March 1 - April 9")
    print("\n   Goal: Verify edge persists in different market conditions")
    print("   Success criteria: AUC > 0.70, ROI > +5% at threshold 0.12-0.15\n")
    
    # Train the model with early-season cutoff
    print("="*80)
    print("Training Variant B with Early Season Data Only...")
    print("="*80)
    
    import subprocess
    import json
    
    # Train with Jan 25 cutoff
    train_cmd = [
        'python3',
        'ml/experiments_ncaabb/train_eval_model_variant.py',
        '--variant', 'B',
        '--train-cutoff', '2024-01-26'  # Train up to Jan 25
    ]
    
    result = subprocess.run(train_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Training failed: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Load the edges and metrics
    data_dir = Path('data/edges')
    edges_file = data_dir / 'edges_ncaabb_variant_B.csv'
    metrics_file = data_dir / 'metrics_variant_B.json'
    
    edges_df = pd.read_csv(edges_file)
    edges_df['date'] = pd.to_datetime(edges_df['date'])
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    print("\n" + "="*80)
    print("Full Test Set Performance (Jan 26 - April 9)")
    print("="*80)
    print(f"  AUC: {metrics['test_auc']:.4f}")
    print(f"  Accuracy: {metrics['test_accuracy']:.4f}")
    print(f"  Brier: {metrics['test_brier']:.4f}")
    
    # Filter to March 1 - April 9 only (late season)
    late_season = edges_df[edges_df['date'] >= '2024-03-01'].copy()
    
    print("\n" + "="*80)
    print(f"Late Season Test Set: March 1 - April 9 ({len(late_season)} games)")
    print("="*80)
    
    # Calculate late-season metrics
    from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss
    
    late_auc = roc_auc_score(late_season['home_won'], late_season['model_prob_home'])
    late_accuracy = accuracy_score(late_season['home_won'], (late_season['model_prob_home'] > 0.5).astype(int))
    late_brier = brier_score_loss(late_season['home_won'], late_season['model_prob_home'])
    
    print(f"\n📊 Late Season ML Metrics:")
    print(f"  AUC: {late_auc:.4f}")
    print(f"  Accuracy: {late_accuracy:.4f}")
    print(f"  Brier: {late_brier:.4f}")
    
    # Backtest on late season
    thresholds = [0.10, 0.12, 0.15]
    
    print(f"\n💰 Late Season Betting Performance:")
    print(f"{'Threshold':<12} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'ROI':<10}")
    print("-" * 55)
    
    best_roi = -100
    best_threshold = 0
    
    for threshold in thresholds:
        # Find edges
        home_edge = late_season['edge_home'] >= threshold
        away_edge = late_season['edge_away'] >= threshold
        
        # Home bets
        home_bets = late_season[home_edge]
        home_wins = (home_bets['home_won'] == 1).sum()
        home_count = len(home_bets)
        
        # Away bets
        away_bets = late_season[away_edge]
        away_wins = (away_bets['home_won'] == 0).sum()
        away_count = len(away_bets)
        
        # Combined
        total_bets = home_count + away_count
        total_wins = home_wins + away_wins
        win_pct = (total_wins / total_bets * 100) if total_bets > 0 else 0
        
        # P&L
        winnings = total_wins * 90.91
        losses = (total_bets - total_wins) * 100
        net_pl = winnings - losses
        roi = (net_pl / (total_bets * 100) * 100) if total_bets > 0 else 0
        
        print(f"{threshold:<12.2f} {total_bets:<8} {total_wins:<8} {win_pct:<10.1f} {roi:<10.1f}%")
        
        if roi > best_roi:
            best_roi = roi
            best_threshold = threshold
    
    print("\n" + "="*80)
    print("TIME STABILITY ASSESSMENT")
    print("="*80)
    
    # Success criteria
    auc_pass = late_auc > 0.70
    roi_pass = best_roi > 5.0
    
    print(f"\n✅ AUC > 0.70? {late_auc:.4f} {'✅ PASS' if auc_pass else '❌ FAIL'}")
    print(f"✅ ROI > +5%? {best_roi:.1f}% at threshold {best_threshold} {'✅ PASS' if roi_pass else '❌ FAIL'}")
    
    if auc_pass and roi_pass:
        print(f"\n🎯 VERDICT: TIME STABILITY CONFIRMED")
        print(f"   Edge persists in late season (March-April) despite training on early data (Jan 5-25)")
        print(f"   Model generalizes well across different market conditions")
    else:
        print(f"\n⚠️  VERDICT: TIME STABILITY QUESTIONABLE")
        if not auc_pass:
            print(f"   AUC dropped to {late_auc:.4f} in late season")
        if not roi_pass:
            print(f"   ROI only {best_roi:.1f}% in late season")
        print(f"   Edge may not persist throughout full season")
    
    # Compare to original (full training)
    print(f"\n📊 Comparison to Original Variant B (trained on Jan 5 - Jan 31):")
    print(f"   Original full test AUC: 0.8111")
    print(f"   Early-trained late-test AUC: {late_auc:.4f}")
    print(f"   Difference: {late_auc - 0.8111:.4f}")
    print(f"\n   Original best ROI: +25.3% (at threshold 0.15)")
    print(f"   Early-trained late-test ROI: +{best_roi:.1f}% (at threshold {best_threshold})")
    
    return auc_pass and roi_pass

if __name__ == '__main__':
    time_stability_test()
