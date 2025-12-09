#!/usr/bin/env python3
"""
Test The Odds API connection and verify API key works.

This script:
1. Tests API authentication
2. Checks available sports
3. Tests historical odds endpoint with a sample date
4. Reports API quota usage

Usage:
    export ODDS_API_KEY="c5d3fe15e6c5be83b2acd8695cff012b"
    python3 data-collection/test_odds_api.py
"""

import os
import sys
import requests
from datetime import datetime, timedelta


API_KEY = "c5d3fe15e6c5be83b2acd8695cff012b"
BASE_URL = "https://api.the-odds-api.com/v4"


def test_sports_endpoint():
    """Test the sports list endpoint"""
    print("\n1️⃣ Testing Sports Endpoint...")
    
    url = f"{BASE_URL}/sports"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        sports = response.json()
        
        # Find NCAA Basketball
        ncaa_sports = [s for s in sports if 'ncaab' in s.get('key', '').lower() or 'basketball' in s.get('title', '').lower()]
        
        print(f"   ✅ API key valid!")
        print(f"   Found {len(sports)} total sports")
        print(f"\n   NCAA Basketball sports:")
        for sport in ncaa_sports:
            print(f"      • {sport['key']}: {sport['title']}")
            print(f"        Group: {sport.get('group', 'N/A')}")
            print(f"        Active: {sport.get('active', False)}")
        
        # Check quota usage
        remaining = response.headers.get('x-requests-remaining')
        used = response.headers.get('x-requests-used')
        print(f"\n   API Quota: {used} used, {remaining} remaining")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print(f"   ❌ Invalid API key!")
            return False
        else:
            print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_historical_endpoint():
    """Test the historical odds endpoint with a sample date"""
    print("\n2️⃣ Testing Historical Odds Endpoint...")
    
    # Use a date from last season (should have data)
    test_date = "2024-03-15T12:00:00Z"  # March Madness 2024
    
    url = f"{BASE_URL}/historical/sports/basketball_ncaab/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads',
        'oddsFormat': 'american',
        'date': test_date
    }
    
    try:
        print(f"   Querying date: {test_date}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        timestamp = data.get('timestamp')
        games = data.get('data', [])
        
        print(f"   ✅ Historical endpoint working!")
        print(f"   Snapshot timestamp: {timestamp}")
        print(f"   Games found: {len(games)}")
        
        if games:
            print(f"\n   📋 Sample game:")
            game = games[0]
            print(f"      {game['away_team']} @ {game['home_team']}")
            print(f"      Commence: {game['commence_time']}")
            print(f"      Bookmakers: {len(game.get('bookmakers', []))}")
            
            # Show first bookmaker's odds
            if game.get('bookmakers'):
                bm = game['bookmakers'][0]
                print(f"\n      {bm['title']} odds:")
                for market in bm.get('markets', []):
                    print(f"         {market['key']}:")
                    for outcome in market.get('outcomes', []):
                        name = outcome['name']
                        if market['key'] == 'spreads':
                            print(f"            {name}: {outcome.get('price')} ({outcome.get('point'):+.1f})")
                        else:
                            print(f"            {name}: {outcome.get('price')}")
        
        # Check quota usage
        remaining = response.headers.get('x-requests-remaining')
        used = response.headers.get('x-requests-used')
        print(f"\n   API Quota: {used} used, {remaining} remaining")
        print(f"   ⚠️  Note: Historical endpoint costs 10 quota per request")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 422:
            print(f"   ⚠️  Date may not have data: {response.text}")
            print(f"   This is normal for dates without NCAA basketball games")
            return True
        else:
            print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("="*80)
    print("THE ODDS API CONNECTION TEST")
    print("="*80)
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-8:]}")
    print(f"Base URL: {BASE_URL}")
    
    # Test endpoints
    sports_ok = test_sports_endpoint()
    
    if sports_ok:
        historical_ok = test_historical_endpoint()
        
        if historical_ok:
            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED")
            print("="*80)
            print("\nYou're ready to collect historical odds!")
            print("\nNext step:")
            print("  ./data-collection/collect_odds_season.sh 2024")
        else:
            print("\n" + "="*80)
            print("⚠️  Historical endpoint test failed")
            print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ API KEY VALIDATION FAILED")
        print("="*80)
        print("\nCheck your API key at: https://the-odds-api.com/account/")


if __name__ == '__main__':
    main()
