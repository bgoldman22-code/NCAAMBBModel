"""
Inspect recent Variant B runs for health monitoring.

Shows the last N runs with key metrics and status to help identify issues.

Usage:
    python3 scripts/ncaabb/inspect_recent_runs.py
    python3 scripts/ncaabb/inspect_recent_runs.py --last 10
    python3 scripts/ncaabb/inspect_recent_runs.py --check-health
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import argparse

def load_run_history():
    """Load run history from logs."""
    log_file = Path('data/ncaabb/logs/variant_b_runs.csv')
    
    if not log_file.exists():
        print(f"❌ No run log found at {log_file}")
        print(f"   Runs will be logged here after first execution")
        return None
    
    # Read with error handling for column mismatches
    try:
        df = pd.read_csv(log_file, on_bad_lines='warn')
    except Exception as e:
        print(f"⚠️  Warning: Error reading log file: {e}")
        print(f"   Attempting to read with error skipping...")
        df = pd.read_csv(log_file, on_bad_lines='skip')
    
    df['run_timestamp'] = pd.to_datetime(df['run_timestamp'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    
    return df


def show_recent_runs(n=5):
    """Show the last N runs."""
    df = load_run_history()
    
    if df is None or len(df) == 0:
        print("No runs found")
        return
    
    recent = df.tail(n)
    
    print(f"\n{'='*80}")
    print(f"Last {n} Runs")
    print(f"{'='*80}\n")
    
    for _, run in recent.iterrows():
        print(f"📅 {run['date']} @ {run['run_timestamp'].strftime('%H:%M:%S')}")
        print(f"   Mode: {run.get('mode', 'N/A')}")
        print(f"   Status: {run.get('status', 'success')}")
        print(f"   Games: {run['num_games']}, Bets: {run['num_bets']}")
        
        if run['num_bets'] > 0:
            print(f"   Avg Edge: {run['avg_edge']:.3f} ({run['avg_edge']*100:.1f}%)")
            print(f"   Max Edge: {run['max_edge']:.3f} ({run['max_edge']*100:.1f}%)")
            print(f"   Total Stake: ${run['total_stake']:,.0f}")
        else:
            print(f"   ⚠️  No qualifying bets")
        
        if 'error_message' in run and pd.notna(run.get('error_message')):
            print(f"   ❌ Error: {run['error_message']}")
        
        print()


def check_health():
    """Check system health and identify potential issues."""
    df = load_run_history()
    
    if df is None or len(df) == 0:
        print("❌ No run history available")
        return False
    
    print(f"\n{'='*80}")
    print(f"Health Check")
    print(f"{'='*80}\n")
    
    issues = []
    warnings = []
    
    # Check 1: Recent run status
    last_run = df.iloc[-1]
    days_since_last = (datetime.now() - last_run['run_timestamp']).days
    
    print(f"📊 Last Run:")
    print(f"   Date: {last_run['date']}")
    print(f"   Time: {last_run['run_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Days ago: {days_since_last}")
    
    if days_since_last > 3:
        issues.append(f"No runs in {days_since_last} days (last: {last_run['date']})")
    
    # Check 2: Recent failures
    if 'status' in df.columns:
        recent_7 = df.tail(7)
        failed = recent_7[recent_7.get('status', 'success') == 'error']
        
        print(f"\n📈 Last 7 Runs:")
        print(f"   Success: {len(recent_7) - len(failed)}")
        print(f"   Failures: {len(failed)}")
        
        if len(failed) > 0:
            issues.append(f"{len(failed)} failures in last 7 runs")
            print(f"   Failed dates: {', '.join([str(d) for d in failed['date'].values])}")
    
    # Check 3: Zero-bet days
    recent_14 = df.tail(14)
    zero_bet_days = recent_14[recent_14['num_bets'] == 0]
    
    print(f"\n🎯 Last 14 Runs - Bet Volume:")
    print(f"   Avg bets/run: {recent_14['num_bets'].mean():.1f}")
    print(f"   Zero-bet days: {len(zero_bet_days)}")
    
    if len(zero_bet_days) > 10:
        warnings.append(f"Very low volume: {len(zero_bet_days)}/14 days with no bets")
    elif len(zero_bet_days) > 7:
        warnings.append(f"Low volume: {len(zero_bet_days)}/14 days with no bets")
    
    # Check 4: Edge drift
    if len(recent_14) > 0:
        recent_with_bets = recent_14[recent_14['num_bets'] > 0]
        
        if len(recent_with_bets) > 0:
            avg_edge = recent_with_bets['avg_edge'].mean()
            
            print(f"\n📊 Edge Analysis (last 14 days with bets):")
            print(f"   Avg edge: {avg_edge:.3f} ({avg_edge*100:.1f}%)")
            print(f"   Min edge: {recent_with_bets['avg_edge'].min():.3f}")
            print(f"   Max edge: {recent_with_bets['avg_edge'].max():.3f}")
            
            # Expected edge from backtest: ~0.194
            if avg_edge < 0.10:
                issues.append(f"Edge collapse: avg {avg_edge:.3f} (expected ~0.19)")
            elif avg_edge < 0.15:
                warnings.append(f"Edge drift: avg {avg_edge:.3f} (expected ~0.19)")
            
            # Check for unrealistic edges
            if recent_with_bets['max_edge'].max() > 0.40:
                warnings.append(f"Suspiciously high edge: {recent_with_bets['max_edge'].max():.3f}")
    
    # Check 5: Mode consistency
    if 'mode' in df.columns:
        recent_7_modes = df.tail(7)['mode'].value_counts()
        
        print(f"\n🔄 Mode Usage (last 7 runs):")
        for mode, count in recent_7_modes.items():
            print(f"   {mode}: {count}")
        
        if 'historical' in recent_7_modes and recent_7_modes['historical'] > 5:
            warnings.append("Mostly using historical mode (expected: live)")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"Health Summary")
    print(f"{'='*80}\n")
    
    if len(issues) == 0 and len(warnings) == 0:
        print("✅ All checks passed - system healthy")
        return True
    
    if len(issues) > 0:
        print(f"❌ Issues Found ({len(issues)}):\n")
        for issue in issues:
            print(f"   • {issue}")
        print()
    
    if len(warnings) > 0:
        print(f"⚠️  Warnings ({len(warnings)}):\n")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    return len(issues) == 0


def show_summary_stats():
    """Show overall summary statistics."""
    df = load_run_history()
    
    if df is None or len(df) == 0:
        return
    
    print(f"\n{'='*80}")
    print(f"All-Time Statistics")
    print(f"{'='*80}\n")
    
    print(f"📊 Overall:")
    print(f"   Total runs: {len(df)}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Total bets: {df['num_bets'].sum()}")
    
    # Mode breakdown
    if 'mode' in df.columns:
        mode_counts = df['mode'].value_counts()
        print(f"\n🔄 By Mode:")
        for mode, count in mode_counts.items():
            mode_df = df[df['mode'] == mode]
            avg_bets = mode_df['num_bets'].mean()
            print(f"   {mode}: {count} runs, {avg_bets:.1f} avg bets")
    
    # Bet volume
    with_bets = df[df['num_bets'] > 0]
    print(f"\n🎯 Bet Volume:")
    print(f"   Days with bets: {len(with_bets)} ({len(with_bets)/len(df)*100:.1f}%)")
    
    if len(with_bets) > 0:
        print(f"   Avg bets (when > 0): {with_bets['num_bets'].mean():.1f}")
        print(f"   Avg edge: {with_bets['avg_edge'].mean():.3f} ({with_bets['avg_edge'].mean()*100:.1f}%)")
        print(f"   Avg stake/run: ${with_bets['total_stake'].mean():,.0f}")


def main():
    parser = argparse.ArgumentParser(description='Inspect Variant B run history')
    
    parser.add_argument('--last', type=int, default=5,
                        help='Number of recent runs to show (default: 5)')
    parser.add_argument('--check-health', action='store_true',
                        help='Run health check')
    parser.add_argument('--summary', action='store_true',
                        help='Show all-time summary statistics')
    
    args = parser.parse_args()
    
    print("="*80)
    print("NCAA Basketball Variant B - Run Inspector")
    print("="*80)
    
    # Show recent runs
    show_recent_runs(args.last)
    
    # Health check
    if args.check_health:
        healthy = check_health()
        
        if not healthy:
            sys.exit(1)
    
    # Summary stats
    if args.summary:
        show_summary_stats()
    
    sys.exit(0)


if __name__ == '__main__':
    main()
