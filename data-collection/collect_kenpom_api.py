"""
Collect efficiency ratings from KenPom API
Pulls adjusted offensive/defensive efficiency, tempo, and other metrics
"""

import requests
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Import config
try:
    from kenpom_config import KENPOM_EMAIL, KENPOM_API_KEY, KENPOM_API_BASE
except ImportError:
    print("❌ Error: kenpom_config.py not found or not configured")
    print("Please edit data-collection/kenpom_config.py with your KenPom API credentials")
    exit(1)

# Create data directory
DATA_DIR = Path(__file__).parent.parent / 'data' / 'kenpom'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Seasons to collect
SEASONS = [2022, 2023, 2024, 2025]  # 2021-22 through 2024-25

class KenPomAPI:
    """KenPom API client"""
    
    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key
        self.base_url = KENPOM_API_BASE
        self.session = requests.Session()
        # Set up Bearer token authentication
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })
        
    def _make_request(self, endpoint, params=None):
        """Make authenticated request to KenPom API"""
        # Use api.php with endpoint parameter
        url = f"{self.base_url}/api.php"
        
        # Add endpoint to params
        request_params = {'endpoint': endpoint}
        if params:
            request_params.update(params)
        
        try:
            response = self.session.get(url, params=request_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text[:500]}")
            return None
    
    def get_ratings(self, year=None):
        """
        Get team ratings for a specific year
        
        Args:
            year: Season ending year (e.g., 2025 for 2024-25 season)
                  None = current season (will use latest year)
        """
        endpoint = "ratings"
        params = {}
        
        if year:
            params['y'] = year
        else:
            # Use current season (2025)
            params['y'] = 2025
        
        print(f"Fetching ratings for {params['y']} season...")
        data = self._make_request(endpoint, params)
        
        if data:
            return pd.DataFrame(data)
        return None
    
    def get_team_stats(self, year=None):
        """Get detailed team statistics including Four Factors"""
        # KenPom API doesn't have a separate team-stats endpoint
        # The ratings endpoint includes most of what we need
        # This is kept for compatibility but just returns None
        return None

def collect_season_data(api_client, season):
    """
    Collect all data for a season
    
    Args:
        api_client: KenPomAPI instance
        season: Season ending year
    """
    print(f"\n{'='*60}")
    print(f"Collecting KenPom data for {season-1}-{season} season")
    print(f"{'='*60}\n")
    
    # Get ratings (efficiency, tempo, etc.)
    ratings = api_client.get_ratings(year=season)
    
    if ratings is not None and len(ratings) > 0:
        # Save ratings
        ratings_path = DATA_DIR / f'kenpom_ratings_{season}.csv'
        ratings.to_csv(ratings_path, index=False)
        print(f"✅ Saved ratings: {len(ratings)} teams")
        
        # Show sample
        print(f"\n📊 Sample data (top 5 teams):")
        display_cols = ['team', 'rank', 'adj_em', 'adj_o', 'adj_d', 'adj_t'] if 'team' in ratings.columns else ratings.columns[:6]
        print(ratings[display_cols].head().to_string(index=False))
    else:
        print(f"❌ Failed to get ratings for {season}")
        return False
    
    # Optional: Get detailed team stats
    time.sleep(1)  # Rate limiting
    team_stats = api_client.get_team_stats(year=season)
    
    if team_stats is not None and len(team_stats) > 0:
        stats_path = DATA_DIR / f'kenpom_stats_{season}.csv'
        team_stats.to_csv(stats_path, index=False)
        print(f"✅ Saved team stats: {len(team_stats)} teams")
    
    # Save metadata
    metadata = {
        'season': season,
        'collected_at': datetime.now().isoformat(),
        'teams_count': len(ratings) if ratings is not None else 0,
        'source': 'kenpom_api',
        'has_stats': team_stats is not None and len(team_stats) > 0
    }
    
    metadata_path = DATA_DIR / f'metadata_{season}.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return True

def main():
    """Main collection workflow"""
    print("\n🏀 KenPom API Data Collection")
    print("="*60)
    
    # Check credentials
    if KENPOM_EMAIL == "your_email@example.com" or KENPOM_API_KEY == "your_api_key_here":
        print("\n❌ ERROR: KenPom API credentials not configured!")
        print("\nPlease edit: data-collection/kenpom_config.py")
        print("Add your:")
        print("  - KenPom login email")
        print("  - KenPom API key (from https://kenpom.com/api-documentation.php)")
        return
    
    # Initialize API client
    api_client = KenPomAPI(KENPOM_EMAIL, KENPOM_API_KEY)
    
    # Test connection with current season
    print("\nTesting API connection...")
    test_data = api_client.get_ratings()
    
    if test_data is None or len(test_data) == 0:
        print("\n❌ API connection failed!")
        print("\nPossible issues:")
        print("  1. Invalid API credentials")
        print("  2. API subscription not active")
        print("  3. Network/connection issue")
        print("\nPlease check your credentials in kenpom_config.py")
        return
    
    print(f"✅ API connection successful! ({len(test_data)} teams found)")
    
    # Collect historical data
    success_count = 0
    
    for season in SEASONS:
        if collect_season_data(api_client, season):
            success_count += 1
        
        # Rate limiting between requests
        if season != SEASONS[-1]:
            print("\nWaiting 2 seconds before next season...")
            time.sleep(2)
    
    print("\n" + "="*60)
    print(f"✅ Collection complete: {success_count}/{len(SEASONS)} seasons")
    print(f"📁 Data saved to: {DATA_DIR}")
    print("="*60)
    
    # Show collected files
    print("\n📊 Collected files:")
    for file in sorted(DATA_DIR.glob("kenpom_*.csv")):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   {file.name}: {size_mb:.2f} MB")
    
    print("\n✅ Next step: Merge KenPom data with game schedules")
    print("Run: python3 data-collection/merge_kenpom_schedules.py")

if __name__ == "__main__":
    main()
