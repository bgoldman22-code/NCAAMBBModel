"""
Smoke test for live odds API client.

Tests that the odds API integration is working correctly.
Should be run before deploying any live automation.

Usage:
    python3 scripts/ncaabb/test_live_odds_client.py
    python3 scripts/ncaabb/test_live_odds_client.py --date 2024-03-15
"""

import sys
from pathlib import Path
from datetime import date, datetime
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.live_odds_client import (
    fetch_today_moneyline_odds,
    fetch_odds_with_fallback,
    normalize_team_name
)


def test_team_normalization():
    """Test that team name normalization works."""
    print("\n🔤 Testing team name normalization...")
    
    test_cases = {
        'UConn': 'Connecticut',
        'UCONN': 'Connecticut',
        'UNC': 'North Carolina',
        'Duke Blue Devils': 'Duke',
        'Kansas Jayhawks': 'Kansas',
    }
    
    passed = 0
    failed = 0
    
    for raw, expected in test_cases.items():
        normalized = normalize_team_name(raw)
        if normalized == expected:
            print(f"   ✅ '{raw}' → '{normalized}'")
            passed += 1
        else:
            print(f"   ❌ '{raw}' → '{normalized}' (expected '{expected}')")
            failed += 1
    
    print(f"\n   Normalization tests: {passed} passed, {failed} failed")
    
    return failed == 0


def test_odds_fetch(target_date: date):
    """Test fetching odds for a specific date."""
    print(f"\n📡 Testing odds fetch for {target_date}...")
    
    try:
        df = fetch_today_moneyline_odds(target_date)
        
        if len(df) == 0:
            print(f"   ⚠️  No games found for {target_date}")
            print(f"   This may be expected if:")
            print(f"     - Date is not during NCAA basketball season")
            print(f"     - No games scheduled for this date")
            print(f"     - Games haven't been published yet")
            return False
        
        # Validate DataFrame structure
        required_cols = [
            'game_id', 'date', 'home_team', 'away_team',
            'home_ml', 'away_ml', 'book_name', 'last_update'
        ]
        
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            print(f"   ❌ Missing required columns: {missing_cols}")
            return False
        
        print(f"   ✅ Fetched {len(df)} games")
        print(f"   ✅ All required columns present")
        
        # Check for nulls in critical columns
        critical_cols = ['home_team', 'away_team', 'home_ml', 'away_ml']
        null_counts = df[critical_cols].isnull().sum()
        
        if null_counts.any():
            print(f"   ⚠️  Null values found:")
            for col, count in null_counts[null_counts > 0].items():
                print(f"      {col}: {count} nulls")
        else:
            print(f"   ✅ No nulls in critical columns")
        
        # Display sample
        print(f"\n   📊 Sample of first 10 games:\n")
        sample_df = df[['date', 'home_team', 'away_team', 'home_ml', 'away_ml', 'close_spread', 'book_name']].head(10)
        print(sample_df.to_string(index=False))
        
        # Check odds ranges
        print(f"\n   📈 Odds ranges:")
        print(f"      Home ML: {df['home_ml'].min():.0f} to {df['home_ml'].max():.0f}")
        print(f"      Away ML: {df['away_ml'].min():.0f} to {df['away_ml'].max():.0f}")
        
        if df['close_spread'].notna().any():
            print(f"      Spreads: {df['close_spread'].min():.1f} to {df['close_spread'].max():.1f}")
        
        # Check books
        print(f"\n   📚 Books used: {', '.join(df['book_name'].unique())}")
        
        return True
    
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        print(f"\n   💡 To fix:")
        print(f"      1. Get API key from https://the-odds-api.com/")
        print(f"      2. Set environment variable:")
        print(f"         export ODDS_API_KEY='your_key_here'")
        return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_mechanism():
    """Test fallback to multiple books."""
    print(f"\n🔄 Testing fallback mechanism...")
    
    try:
        target_date = date.today()
        df = fetch_odds_with_fallback(target_date)
        
        if len(df) > 0:
            print(f"   ✅ Fallback successful, fetched {len(df)} games")
            return True
        else:
            print(f"   ⚠️  No games found via fallback")
            return False
    
    except Exception as e:
        print(f"   ❌ Fallback failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test live odds API client')
    parser.add_argument('--date', type=str, default=None,
                        help='Date to test (YYYY-MM-DD, default: today)')
    parser.add_argument('--skip-normalization', action='store_true',
                        help='Skip team name normalization tests')
    parser.add_argument('--skip-fallback', action='store_true',
                        help='Skip fallback mechanism test')
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = date.today()
    
    print("="*80)
    print("NCAA Basketball Live Odds API - Smoke Test")
    print("="*80)
    print(f"Target date: {target_date}")
    
    # Run tests
    results = []
    
    if not args.skip_normalization:
        results.append(('Team Normalization', test_team_normalization()))
    
    results.append(('Odds Fetch', test_odds_fetch(target_date)))
    
    if not args.skip_fallback:
        results.append(('Fallback Mechanism', test_fallback_mechanism()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check configuration before deploying live automation.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! Ready for live deployment.")
        sys.exit(0)


if __name__ == '__main__':
    main()
