#!/bin/bash
#
# Daily Current Season Data Update Script
#
# This script automates the process of:
# 1. Fetching recent NCAA basketball game results (last 7 days)
# 2. Computing in-season rolling stats
# 3. Updating the production dataset
#
# Usage:
#   ./scripts/ncaabb/update_current_season_data.sh
#
# Can be run via cron:
#   0 6 * * * cd /path/to/repo && ./scripts/ncaabb/update_current_season_data.sh
#
# Or via GitHub Actions (see .github/workflows/update_current_season_data.yml)

set -e  # Exit on any error

echo "=================================="
echo "NCAA Basketball - Daily Data Update"
echo "=================================="
echo "$(date)"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$PROJECT_ROOT"

# Step 1: Fetch recent game results
echo "📥 Step 1: Fetching recent game results (last 7 days)..."
python3 data-collection/fetch_current_season_games.py --recent 7

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch game results"
    exit 1
fi

echo ""

# Step 2: Update in-season stats
echo "🔧 Step 2: Computing in-season rolling stats..."
python3 data-collection/update_inseason_stats.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to update in-season stats"
    exit 1
fi

echo ""
echo "✅ Daily data update complete!"
echo ""

# Optional: Show summary stats
echo "📊 Dataset Summary:"
python3 -c "
import pandas as pd
from pathlib import Path

# Load updated stats
df = pd.read_csv('data/merged/game_results_with_inseason_stats.csv')

print(f'  Total games: {len(df):,}')
print(f'  Date range: {df[\"date\"].min()} to {df[\"date\"].max()}')

# Current season
current = df[df['season'] == 2026]
print(f'  Current season (2025-26): {len(current):,} games')

# Check coverage
stat_cols = [col for col in df.columns if 'ORtg_L10' in col]
if stat_cols:
    coverage = df[stat_cols[0]].notna().mean()
    print(f'  In-season stats coverage: {coverage*100:.1f}%')
"

echo ""
echo "✅ Ready for live predictions!"
