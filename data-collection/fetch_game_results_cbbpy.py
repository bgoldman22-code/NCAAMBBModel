"""
Match predictions to actual game results using CBBpy historical data.

This uses the schedules we already collected from ESPN via CBBpy.
Should have much better coverage than direct ESPN API (which only shows featured games).
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'ml'))
from team_database import normalize_team_name as db_normalize_team

def fuzzy_match_score(str1: str, str2: str) -> float:
    """Calculate fuzzy match similarity between two strings"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def load_historical_data(year: int = 2024) -> pd.DataFrame:
    """
    Load and parse historical game data from CBBpy schedules.
    
    Args:
        year: Season ending year (2024 = 2023-24 season)
        
    Returns:
        DataFrame with game results
    """
    # Try complete dataset first (all teams), fall back to original (30 major teams)
    complete_path = Path(__file__).parent.parent / 'data' / 'historical' / f'schedules_{year}_complete.csv'
    original_path = Path(__file__).parent.parent / 'data' / 'historical' / f'schedules_{year}.csv'
    
    if complete_path.exists():
        data_path = complete_path
        print(f"  📚 Using complete dataset: {complete_path.name}")
    elif original_path.exists():
        data_path = original_path
        print(f"  📚 Using original dataset: {original_path.name}")
    else:
        raise FileNotFoundError(f"Historical data not found: {complete_path} or {original_path}")
    
    df = pd.read_csv(data_path)
    
    # Filter for completed games only
    df = df[df['game_status'] == 'Final'].copy()
    
    # Parse game_result column (format: 'W 92-54' or 'L 73-78')
    def parse_result(row):
        result = row['game_result']
        if pd.isna(result):
            return None, None
        
        parts = result.split()
        if len(parts) != 2:
            return None, None
        
        scores = parts[1].split('-')
        if len(scores) != 2:
            return None, None
        
        try:
            team_score = int(scores[0])
            opp_score = int(scores[1])
            return team_score, opp_score
        except:
            return None, None
    
    df[['team_score', 'opp_score']] = df.apply(parse_result, axis=1, result_type='expand')
    df = df[df['team_score'].notna()].copy()
    
    # Parse date (format: "January 05, 2024")
    df['date'] = pd.to_datetime(df['game_day'], format='%B %d, %Y')
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Normalize team names for matching
    df['team_normalized'] = df['team'].apply(db_normalize_team)
    df['opponent_normalized'] = df['opponent'].apply(db_normalize_team)
    
    print(f"  ✅ Loaded {len(df)} completed games from historical data")
    print(f"  Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    
    return df


def match_game_to_historical(row: pd.Series, historical_df: pd.DataFrame, fuzzy_threshold: float = 0.85) -> dict:
    """
    Match a prediction to historical game result.
    
    Strategy:
    1. Filter historical games by date (±1 day window)
    2. Normalize team names using database
    3. Try exact match
    4. Fall back to fuzzy matching
    
    Args:
        row: Row from walkforward predictions
        historical_df: DataFrame of historical games
        fuzzy_threshold: Minimum similarity for fuzzy match
        
    Returns:
        Match dictionary or None
    """
    # Parse our date
    our_date = pd.to_datetime(row['date'])
    
    # Filter historical games to ±1 day window
    date_min = our_date - pd.Timedelta(days=1)
    date_max = our_date + pd.Timedelta(days=1)
    candidates = historical_df[
        (historical_df['date'] >= date_min) & 
        (historical_df['date'] <= date_max)
    ].copy()
    
    if len(candidates) == 0:
        return None
    
    # Normalize our team names
    our_home_normalized = db_normalize_team(row['home_team'])
    our_away_normalized = db_normalize_team(row['away_team'])
    
    best_match = None
    best_score = 0
    
    # Check each candidate game
    for _, hist_game in candidates.iterrows():
        # Historical data is from team perspective, so check both directions:
        # 1. hist_team=home, hist_opponent=away
        # 2. hist_team=away, hist_opponent=home
        
        # Direction 1: Team is home
        if hist_game['team_normalized'] == our_home_normalized and \
           hist_game['opponent_normalized'] == our_away_normalized:
            return {
                'home_score': hist_game['team_score'],
                'away_score': hist_game['opp_score'],
                'matched': True,
                'match_type': 'exact',
                'match_score': 1.0,
                'data_source': 'cbbpy',
                'game_id': hist_game['game_id']
            }
        
        # Direction 2: Team is away
        if hist_game['opponent_normalized'] == our_home_normalized and \
           hist_game['team_normalized'] == our_away_normalized:
            return {
                'home_score': hist_game['opp_score'],
                'away_score': hist_game['team_score'],
                'matched': True,
                'match_type': 'exact',
                'match_score': 1.0,
                'data_source': 'cbbpy',
                'game_id': hist_game['game_id']
            }
        
        # Fuzzy matching - Direction 1
        home_sim = fuzzy_match_score(our_home_normalized, hist_game['team_normalized'])
        away_sim = fuzzy_match_score(our_away_normalized, hist_game['opponent_normalized'])
        score1 = (home_sim + away_sim) / 2
        
        if score1 > best_score and score1 >= fuzzy_threshold:
            best_score = score1
            best_match = {
                'home_score': hist_game['team_score'],
                'away_score': hist_game['opp_score'],
                'matched': True,
                'match_type': 'fuzzy',
                'match_score': score1,
                'data_source': 'cbbpy',
                'game_id': hist_game['game_id']
            }
        
        # Fuzzy matching - Direction 2
        home_sim = fuzzy_match_score(our_home_normalized, hist_game['opponent_normalized'])
        away_sim = fuzzy_match_score(our_away_normalized, hist_game['team_normalized'])
        score2 = (home_sim + away_sim) / 2
        
        if score2 > best_score and score2 >= fuzzy_threshold:
            best_score = score2
            best_match = {
                'home_score': hist_game['opp_score'],
                'away_score': hist_game['team_score'],
                'matched': True,
                'match_type': 'fuzzy',
                'match_score': score2,
                'data_source': 'cbbpy',
                'game_id': hist_game['game_id']
            }
    
    return best_match


def match_predictions_to_results(predictions_path: str, output_path: str, fuzzy_threshold: float = 0.85):
    """
    Match all predictions to historical game results.
    
    Args:
        predictions_path: Path to walkforward predictions CSV
        output_path: Path to save matched results
        fuzzy_threshold: Minimum similarity for fuzzy match (default 0.85)
    """
    print("\n" + "="*80)
    print("CBBPY GAME RESULT MATCHER")
    print("="*80 + "\n")
    
    # Load predictions
    print(f"📂 Loading {predictions_path}...")
    predictions_df = pd.read_csv(predictions_path)
    print(f"  Loaded {len(predictions_df)} predictions")
    print(f"  Date range: {predictions_df['date'].min()} → {predictions_df['date'].max()}")
    
    # Load historical data (2024 season = Jan-Apr 2024)
    print("\n📚 Loading historical game data...")
    historical_df = load_historical_data(year=2024)
    
    print(f"\n🔗 Matching predictions to results...")
    print(f"Configuration:")
    print(f"  Fuzzy threshold: {fuzzy_threshold*100:.0f}%")
    print(f"  Date buffer: ±1 day")
    
    # Match each prediction
    matches = []
    exact_count = 0
    fuzzy_count = 0
    
    for _, row in tqdm(predictions_df.iterrows(), total=len(predictions_df), desc="Matching"):
        match = match_game_to_historical(row, historical_df, fuzzy_threshold)
        
        if match:
            if match['match_type'] == 'exact':
                exact_count += 1
            else:
                fuzzy_count += 1
            matches.append(match)
        else:
            matches.append({
                'home_score': None,
                'away_score': None,
                'matched': False,
                'match_type': None,
                'match_score': 0.0,
                'data_source': None,
                'game_id': None
            })
    
    # Add matches to predictions
    match_df = pd.DataFrame(matches)
    result_df = pd.concat([predictions_df, match_df], axis=1)
    
    # Calculate derived fields for matched games
    matched_mask = result_df['matched'] == True
    result_df.loc[matched_mask, 'actual_margin'] = \
        result_df.loc[matched_mask, 'home_score'] - result_df.loc[matched_mask, 'away_score']
    result_df.loc[matched_mask, 'home_won'] = \
        result_df.loc[matched_mask, 'home_score'] > result_df.loc[matched_mask, 'away_score']
    # home_covered = did home beat the MARKET spread (standard home perspective)
    # A home bet covers when (actual_margin + close_spread) > 0 (pushes treated as non-wins)
    result_df.loc[matched_mask, 'home_covered'] = (
        result_df.loc[matched_mask, 'actual_margin'] + result_df.loc[matched_mask, 'close_spread'] > 0
    )
    
    # Save results
    result_df.to_csv(output_path, index=False)
    
    # Print summary
    matched_count = exact_count + fuzzy_count
    match_rate = (matched_count / len(predictions_df)) * 100
    
    print("\n" + "="*80)
    print("MATCHING RESULTS")
    print("="*80)
    print(f"  Total predictions: {len(predictions_df)}")
    print(f"  Matched: {matched_count} ({match_rate:.1f}%)")
    print(f"    ├─ Exact matches: {exact_count}")
    print(f"    └─ Fuzzy matches: {fuzzy_count}")
    print(f"  Unmatched: {len(predictions_df) - matched_count}")
    
    if matched_count > 0:
        matched_games = result_df[result_df['matched'] == True]
        print(f"\n📊 Matched Game Statistics:")
        print(f"  Avg home score: {matched_games['home_score'].mean():.1f}")
        print(f"  Avg away score: {matched_games['away_score'].mean():.1f}")
        print(f"  Home win rate: {matched_games['home_won'].mean()*100:.1f}%")
        print(f"  Avg margin: {matched_games['actual_margin'].mean():+.1f}")
        
        print(f"\n📋 Sample Matches:")
        for _, row in matched_games.head(5).iterrows():
            print(f"  {row['home_team']} vs {row['away_team']}")
            print(f"    → Score: {int(row['home_score'])}-{int(row['away_score'])} "
                  f"({row['match_type']}, {row['match_score']*100:.0f}%)")
    
    print(f"\n💾 Saved to {output_path}")
    print(f"  File size: {Path(output_path).stat().st_size / 1024 / 1024:.2f} MB")
    
    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)
    print(f"  Match rate: {matched_count}/{len(predictions_df)} ({match_rate:.1f}%)")
    print(f"\nNext step:")
    print(f"  python3 ml/calculate_backtest_pnl.py")


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent
    predictions_path = base_dir / 'data' / 'walkforward_results_full.csv'
    output_path = base_dir / 'data' / 'walkforward_results_with_scores.csv'
    
    # Match predictions to results
    match_predictions_to_results(
        predictions_path=str(predictions_path),
        output_path=str(output_path),
        fuzzy_threshold=0.85
    )
