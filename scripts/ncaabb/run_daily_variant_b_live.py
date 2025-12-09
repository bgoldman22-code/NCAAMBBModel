"""
Daily automation script for Variant B live picks generation.

This script is designed to be run by cron, GitHub Actions, or Netlify scheduled functions.
It generates picks for today's NCAA basketball games using live odds.

Usage:
    python3 scripts/ncaabb/run_daily_variant_b_live.py
    
Environment Variables:
    ODDS_API_KEY: Required for live mode
    VARIANT_B_MIN_EDGE: Minimum edge threshold (default: 0.15)
    VARIANT_B_KELLY_FRACTION: Kelly fraction (default: 0.25)
    VARIANT_B_BANKROLL: Bankroll in dollars (default: 10000)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pytz

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.ncaabb.generate_variant_b_picks import generate_picks


class Args:
    """Simple args container to mimic argparse."""
    def __init__(self, date, mode, min_edge, kelly_fraction, bankroll, output):
        self.date = date
        self.mode = mode
        self.min_edge = min_edge
        self.kelly_fraction = kelly_fraction
        self.bankroll = bankroll
        self.output = output


def main():
    """Run daily picks generation."""
    
    print("="*80)
    print("NCAA Basketball Variant B - Daily Automation")
    print("="*80)
    print(f"Run time: {datetime.now().isoformat()}")
    
    # Get today's date in America/New_York timezone
    tz = pytz.timezone('America/New_York')
    today = datetime.now(tz).date()
    date_str = today.strftime('%Y-%m-%d')
    
    print(f"Target date: {date_str} (America/New_York)")
    
    # Get config from environment with defaults
    min_edge = float(os.getenv('VARIANT_B_MIN_EDGE', '0.15'))
    kelly_fraction = float(os.getenv('VARIANT_B_KELLY_FRACTION', '0.25'))
    bankroll = float(os.getenv('VARIANT_B_BANKROLL', '10000'))
    mode = os.getenv('VARIANT_B_MODE', 'live')
    
    print(f"\nConfiguration:")
    print(f"  Mode: {mode}")
    print(f"  Min Edge: {min_edge}")
    print(f"  Kelly Fraction: {kelly_fraction}")
    print(f"  Bankroll: ${bankroll:,.0f}")
    
    # Check for API key if using live mode
    if mode == 'live':
        api_key = os.getenv('ODDS_API_KEY')
        if not api_key:
            print("\n❌ ERROR: ODDS_API_KEY environment variable not set")
            print("   Live mode requires an API key from https://the-odds-api.com/")
            print("   Set it with: export ODDS_API_KEY='your_key_here'")
            sys.exit(1)
        print(f"  API Key: {'*' * 20}{api_key[-4:]} (last 4 chars)")
    
    # Set output path
    output_dir = Path('data/ncaabb/picks')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'variant_b_picks_{date_str}.csv'
    
    print(f"  Output: {output_file}")
    
    # Build args
    args = Args(
        date=date_str,
        mode=mode,
        min_edge=min_edge,
        kelly_fraction=kelly_fraction,
        bankroll=bankroll,
        output=str(output_file)
    )
    
    # Run picks generation
    try:
        print("\n" + "="*80)
        picks_df = generate_picks(args)
        
        if picks_df is not None and len(picks_df) > 0:
            print("\n" + "="*80)
            print("✅ Daily automation complete!")
            print("="*80)
            print(f"Generated {len(picks_df)} picks for {date_str}")
            print(f"Output: {output_file}")
            print(f"JSON: {output_file.with_suffix('.json')}")
            
            # Additional summary for automation
            total_stake = picks_df['bet_size_dollars'].sum()
            avg_edge = picks_df['edge'].mean()
            max_edge = picks_df['edge'].max()
            
            print(f"\nSummary:")
            print(f"  Total stake: ${total_stake:,.0f} ({total_stake/bankroll*100:.1f}% of bankroll)")
            print(f"  Avg edge: {avg_edge:.3f} ({avg_edge*100:.1f}%)")
            print(f"  Max edge: {max_edge:.3f} ({max_edge*100:.1f}%)")
            
            sys.exit(0)
        
        else:
            print("\n" + "="*80)
            print("⚠️  No qualifying bets found")
            print("="*80)
            print(f"Date: {date_str}")
            print(f"Min edge: {min_edge}")
            print(f"Possible reasons:")
            print(f"  - No games scheduled today")
            print(f"  - All games below edge threshold")
            print(f"  - Odds not available yet")
            
            sys.exit(0)
    
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERROR: Daily automation failed")
        print("="*80)
        print(f"Error: {e}")
        
        import traceback
        traceback.print_exc()
        
        # Log error to run log
        from scripts.ncaabb.generate_variant_b_picks import log_run
        import pandas as pd
        
        try:
            # Create error log entry
            log_file = Path('data/ncaabb/logs/variant_b_runs.csv')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            error_entry = {
                'run_timestamp': datetime.now().isoformat(),
                'date': date_str,
                'mode': mode,
                'min_edge': min_edge,
                'kelly_fraction': kelly_fraction,
                'bankroll': bankroll,
                'num_games': 0,
                'num_bets': 0,
                'avg_edge': 0,
                'max_edge': 0,
                'total_stake': 0,
                'status': 'error',
                'error_message': str(e)
            }
            
            log_df = pd.DataFrame([error_entry])
            
            if log_file.exists():
                log_df.to_csv(log_file, mode='a', header=False, index=False)
            else:
                log_df.to_csv(log_file, index=False)
            
            print(f"\n📝 Error logged to: {log_file}")
        
        except Exception as log_err:
            print(f"\n⚠️  Failed to log error: {log_err}")
        
        sys.exit(1)


if __name__ == '__main__':
    main()
