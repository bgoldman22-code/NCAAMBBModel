#!/usr/bin/env python3
"""
Train NCAA Basketball spread and moneyline prediction models.

This script trains two models:
1. Spread model (regression): Predicts expected point margin
2. Moneyline model (classification): Predicts win probability

Usage:
    python3 ml/train_ncaabb_spread.py \\
        --data-dir data/merged \\
        --output-dir models/ncaabb \\
        --target both \\
        --seed 42
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.features_ncaabb import build_features, get_feature_names
from ml.utils import (
    load_all_merged_data,
    time_based_split,
    save_model,
    save_json,
    calculate_regression_metrics,
    calculate_classification_metrics
)

# ML imports
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score


def train_spread_model(X_train, y_train, X_test, y_test, seed=42):
    """
    Train gradient boosting model for spread prediction.
    
    Returns:
        (model, train_metrics, test_metrics)
    """
    print("\n" + "="*80)
    print("TRAINING SPREAD MODEL (Regression)")
    print("="*80)
    
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        random_state=seed,
        verbose=0
    )
    
    print(f"\n📊 Training on {len(X_train):,} games...")
    model.fit(X_train, y_train)
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Metrics
    train_metrics = calculate_regression_metrics(y_train, y_train_pred)
    test_metrics = calculate_regression_metrics(y_test, y_test_pred)
    
    print(f"\n📈 Training Metrics:")
    print(f"   MAE:         {train_metrics['mae']:.2f} points")
    print(f"   RMSE:        {train_metrics['rmse']:.2f} points")
    print(f"   Correlation: {train_metrics['correlation']:.4f}")
    
    print(f"\n📈 Test Metrics:")
    print(f"   MAE:         {test_metrics['mae']:.2f} points")
    print(f"   RMSE:        {test_metrics['rmse']:.2f} points")
    print(f"   Correlation: {test_metrics['correlation']:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🔍 Top 5 Most Important Features:")
    for idx, row in feature_importance.head().iterrows():
        print(f"   {row['feature']:25s} {row['importance']:.4f}")
    
    return model, train_metrics, test_metrics, feature_importance


def train_moneyline_model(X_train, y_train, X_test, y_test, seed=42):
    """
    Train gradient boosting model for win probability prediction.
    
    Returns:
        (model, train_metrics, test_metrics)
    """
    print("\n" + "="*80)
    print("TRAINING MONEYLINE MODEL (Classification)")
    print("="*80)
    
    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        random_state=seed,
        verbose=0
    )
    
    print(f"\n📊 Training on {len(X_train):,} games...")
    model.fit(X_train, y_train)
    
    # Predictions
    y_train_pred = model.predict_proba(X_train)[:, 1]
    y_test_pred = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    train_metrics = calculate_classification_metrics(y_train, y_train_pred)
    test_metrics = calculate_classification_metrics(y_test, y_test_pred)
    
    print(f"\n📈 Training Metrics:")
    print(f"   Accuracy:    {train_metrics['accuracy']:.4f} ({train_metrics['accuracy']*100:.2f}%)")
    print(f"   Brier Score: {train_metrics['brier_score']:.4f}")
    print(f"   Log Loss:    {train_metrics['log_loss']:.4f}")
    print(f"   AUC:         {train_metrics['auc']:.4f}")
    
    print(f"\n📈 Test Metrics:")
    print(f"   Accuracy:    {test_metrics['accuracy']:.4f} ({test_metrics['accuracy']*100:.2f}%)")
    print(f"   Brier Score: {test_metrics['brier_score']:.4f}")
    print(f"   Log Loss:    {test_metrics['log_loss']:.4f}")
    print(f"   AUC:         {test_metrics['auc']:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🔍 Top 5 Most Important Features:")
    for idx, row in feature_importance.head().iterrows():
        print(f"   {row['feature']:25s} {row['importance']:.4f}")
    
    return model, train_metrics, test_metrics, feature_importance


def main():
    parser = argparse.ArgumentParser(description='Train NCAA Basketball prediction models')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directory containing merged_games_*.csv files')
    parser.add_argument('--output-dir', type=str, required=True,
                       help='Directory to save trained models')
    parser.add_argument('--target', type=str, choices=['spread', 'moneyline', 'both'], default='both',
                       help='Which model(s) to train')
    parser.add_argument('--max-season', type=int, default=None,
                       help='Maximum season to include in training (e.g., 2023)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    print("="*80)
    print("NCAA BASKETBALL MODEL TRAINING")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Data directory:  {args.data_dir}")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Target:          {args.target}")
    print(f"  Max season:      {args.max_season or 'None (use all)'}")
    print(f"  Random seed:     {args.seed}")
    
    # ============================================================
    # LOAD DATA
    # ============================================================
    
    print("\n" + "="*80)
    print("LOADING DATA")
    print("="*80)
    
    df = load_all_merged_data(args.data_dir, max_season=args.max_season)
    
    # ============================================================
    # TIME-BASED SPLIT
    # ============================================================
    
    # Use 2022-2023 for training, 2024 for testing
    train_seasons = [2022, 2023]
    test_seasons = [2024]
    
    train_df, test_df = time_based_split(df, train_seasons, test_seasons)
    
    # ============================================================
    # FEATURE ENGINEERING
    # ============================================================
    
    print("\n" + "="*80)
    print("BUILDING FEATURES")
    print("="*80)
    
    X_train, y_margin_train, y_win_train = build_features(train_df)
    X_test, y_margin_test, y_win_test = build_features(test_df)
    
    print(f"\n✅ Training set: {X_train.shape[0]:,} games, {X_train.shape[1]} features")
    print(f"✅ Test set:     {X_test.shape[0]:,} games, {X_test.shape[1]} features")
    
    print(f"\n📊 Feature list:")
    for i, col in enumerate(X_train.columns, 1):
        print(f"   {i:2d}. {col}")
    
    # ============================================================
    # TRAIN MODELS
    # ============================================================
    
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'train_date': datetime.now().isoformat(),
        'train_seasons': train_seasons,
        'test_seasons': test_seasons,
        'features': list(X_train.columns),
        'random_seed': args.seed,
        'n_train': len(X_train),
        'n_test': len(X_test)
    }
    
    if args.target in ['spread', 'both']:
        spread_model, train_metrics_spread, test_metrics_spread, fi_spread = train_spread_model(
            X_train, y_margin_train,
            X_test, y_margin_test,
            seed=args.seed
        )
        
        # Save model
        save_model(spread_model, output_path / 'spread_model.pkl')
        
        # Save feature importance
        fi_spread.to_csv(output_path / 'spread_feature_importance.csv', index=False)
        
        # Add to metadata
        metadata['spread_model'] = {
            'train_metrics': train_metrics_spread,
            'test_metrics': test_metrics_spread,
            'feature_importance': fi_spread.to_dict('records')
        }
    
    if args.target in ['moneyline', 'both']:
        ml_model, train_metrics_ml, test_metrics_ml, fi_ml = train_moneyline_model(
            X_train, y_win_train,
            X_test, y_win_test,
            seed=args.seed
        )
        
        # Save model
        save_model(ml_model, output_path / 'moneyline_model.pkl')
        
        # Save feature importance
        fi_ml.to_csv(output_path / 'moneyline_feature_importance.csv', index=False)
        
        # Add to metadata
        metadata['moneyline_model'] = {
            'train_metrics': train_metrics_ml,
            'test_metrics': test_metrics_ml,
            'feature_importance': fi_ml.to_dict('records')
        }
    
    # ============================================================
    # SAVE METADATA
    # ============================================================
    
    # Save feature names
    save_json({'features': list(X_train.columns)}, output_path / 'feature_columns.json')
    
    # Save full metadata
    save_json(metadata, output_path / 'metadata.json')
    
    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    print(f"\nModels and metadata saved to: {output_path}")
    print(f"\nTo evaluate models, run:")
    print(f"  python3 ml/eval_ncaabb_spread.py \\")
    print(f"    --data-file data/merged/merged_games_2024.csv \\")
    print(f"    --model-dir {args.output_dir}")


if __name__ == "__main__":
    main()
