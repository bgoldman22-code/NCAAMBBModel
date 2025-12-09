#!/usr/bin/env python3
"""
Utility functions for NCAA Basketball modeling pipeline.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import json
import pickle


def load_all_merged_data(data_dir: str, max_season: int = None) -> pd.DataFrame:
    """
    Load and concatenate all merged game files.
    
    Args:
        data_dir: Directory containing merged_games_*.csv files
        max_season: Optional maximum season to include (e.g., 2023)
        
    Returns:
        Concatenated DataFrame with all games
    """
    data_path = Path(data_dir)
    merged_files = sorted(data_path.glob('merged_games_*.csv'))
    
    if not merged_files:
        raise FileNotFoundError(f"No merged_games_*.csv files found in {data_dir}")
    
    dfs = []
    for file in merged_files:
        df = pd.read_csv(file)
        
        # Filter by season if specified
        if max_season is not None and 'season' in df.columns:
            if df['season'].iloc[0] > max_season:
                continue
        
        dfs.append(df)
    
    if not dfs:
        raise ValueError(f"No data found for seasons <= {max_season}")
    
    combined = pd.concat(dfs, ignore_index=True)
    
    print(f"✅ Loaded {len(combined):,} games from {len(dfs)} files")
    print(f"   Seasons: {sorted(combined['season'].unique())}")
    
    return combined


def time_based_split(
    df: pd.DataFrame,
    train_seasons: List[int],
    test_seasons: List[int]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data by season for time-aware train/test split.
    
    Args:
        df: DataFrame with 'season' column
        train_seasons: List of seasons for training (e.g., [2022, 2023])
        test_seasons: List of seasons for testing (e.g., [2024])
        
    Returns:
        (train_df, test_df)
    """
    train_df = df[df['season'].isin(train_seasons)].copy()
    test_df = df[df['season'].isin(test_seasons)].copy()
    
    print(f"\n📊 Time-based split:")
    print(f"   Train: {len(train_df):,} games from seasons {train_seasons}")
    print(f"   Test:  {len(test_df):,} games from seasons {test_seasons}")
    
    return train_df, test_df


def save_model(model, filepath: str):
    """Save a model to disk using pickle."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Saved model to {filepath}")


def load_model(filepath: str):
    """Load a model from disk."""
    with open(filepath, 'rb') as f:
        model = pickle.load(f)
    return model


def save_json(data: dict, filepath: str):
    """Save dictionary as JSON."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved metadata to {filepath}")


def load_json(filepath: str) -> dict:
    """Load JSON file as dictionary."""
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Calculate regression metrics for spread model.
    
    Returns:
        Dict with MAE, RMSE, correlation
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    correlation = np.corrcoef(y_true, y_pred)[0, 1]
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'correlation': float(correlation)
    }


def calculate_classification_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray) -> dict:
    """
    Calculate classification metrics for moneyline model.
    
    Args:
        y_true: Binary labels (0 or 1)
        y_pred_proba: Predicted probabilities for class 1
        
    Returns:
        Dict with accuracy, brier_score, log_loss, auc
    """
    from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
    
    y_pred_binary = (y_pred_proba >= 0.5).astype(int)
    
    accuracy = accuracy_score(y_true, y_pred_binary)
    brier = brier_score_loss(y_true, y_pred_proba)
    logloss = log_loss(y_true, y_pred_proba)
    auc = roc_auc_score(y_true, y_pred_proba)
    
    return {
        'accuracy': float(accuracy),
        'brier_score': float(brier),
        'log_loss': float(logloss),
        'auc': float(auc)
    }


def calibration_report(y_true: np.ndarray, y_pred_proba: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    """
    Generate calibration report showing predicted vs actual win rates by probability bin.
    
    Args:
        y_true: Binary labels (0 or 1)
        y_pred_proba: Predicted probabilities for class 1
        n_bins: Number of bins to use
        
    Returns:
        DataFrame with bin ranges, avg predicted prob, actual win rate, and count
    """
    df = pd.DataFrame({
        'y_true': y_true,
        'y_pred': y_pred_proba
    })
    
    # Create bins
    df['bin'] = pd.cut(df['y_pred'], bins=n_bins, labels=False, duplicates='drop')
    
    # Calculate stats per bin
    calibration = df.groupby('bin').agg({
        'y_pred': ['mean', 'min', 'max'],
        'y_true': ['mean', 'count']
    }).reset_index()
    
    calibration.columns = ['bin', 'avg_predicted', 'min_pred', 'max_pred', 'actual_win_rate', 'count']
    
    return calibration


if __name__ == "__main__":
    # Simple test
    print("Testing utility functions...")
    
    df = load_all_merged_data('data/merged')
    print(f"\n✅ Loaded {len(df):,} games")
    
    train_df, test_df = time_based_split(df, [2022, 2023], [2024])
    print(f"✅ Split complete")
