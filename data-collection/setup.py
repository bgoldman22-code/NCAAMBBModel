"""
NCAA Basketball Data Collection - Setup and Installation
This script installs required dependencies and sets up the environment
"""

import subprocess
import sys

def install_packages():
    """Install required Python packages"""
    packages = [
        'cbbpy',           # Primary NCAA basketball data source
        'pandas',          # Data manipulation
        'numpy',           # Numerical operations
        'requests',        # HTTP requests
        'beautifulsoup4',  # Web scraping
        'lxml',            # XML/HTML parser
        'tqdm',            # Progress bars
        'python-dateutil', # Date utilities
        'pytz',            # Timezone handling
    ]
    
    print("Installing required packages...")
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\n✅ All packages installed successfully!")

if __name__ == "__main__":
    install_packages()
    
    print("\n" + "="*60)
    print("🏀 NCAA Basketball Data Collection - Ready!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: python collect_historical_games.py")
    print("   - Collects game schedules and results for 2021-22 through 2024-25")
    print("\n2. Run: python collect_team_stats.py")
    print("   - Scrapes efficiency metrics from T-Rank")
    print("\n3. Subscribe to KenPom.com ($24.95/year)")
    print("   - Download historical efficiency data")
    print("\n4. Test with: python test_data_collection.py")
