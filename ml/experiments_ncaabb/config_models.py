"""
Model variant configurations for NCAA basketball experiments.

Three variants to test:
    A: Preseason KenPom + Market (static priors, no in-season updates)
    B: Market + In-Season Stats (no KenPom at all)
    C: Hybrid (Preseason KenPom + In-Season Stats + Market)

Each config defines:
    - name: Variant identifier
    - description: What this variant tests
    - features: List of feature groups to include
    - model_params: Model hyperparameters
    - time_decay: Whether to include time-based decay features
"""

from typing import Dict, List, Any

VARIANT_CONFIGS: Dict[str, Dict[str, Any]] = {
    'A': {
        'name': 'Preseason KenPom + Market',
        'description': 'Static preseason KenPom ratings treated as priors, no in-season updates',
        'feature_groups': ['preseason_kenpom', 'market', 'time_decay'],
        'model_type': 'gbm',  # GradientBoostingClassifier
        'model_params': {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'min_samples_split': 20,
            'min_samples_leaf': 10,
            'random_state': 42
        },
        'time_decay': True,
        'use_kenpom': True,
        'use_inseason_stats': False
    },
    
    'B': {
        'name': 'Market + In-Season Stats Only',
        'description': 'Rolling in-season performance statistics, NO KenPom at all',
        'feature_groups': ['market', 'inseason_stats'],
        'model_type': 'gbm',
        'model_params': {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'min_samples_split': 20,
            'min_samples_leaf': 10,
            'random_state': 42
        },
        'time_decay': False,
        'use_kenpom': False,
        'use_inseason_stats': True
    },
    
    'C': {
        'name': 'Hybrid (All Features)',
        'description': 'Preseason KenPom + rolling in-season stats + market features',
        'feature_groups': ['preseason_kenpom', 'market', 'inseason_stats', 'time_decay'],
        'model_type': 'gbm',
        'model_params': {
            'n_estimators': 150,
            'learning_rate': 0.1,
            'max_depth': 5,
            'min_samples_split': 20,
            'min_samples_leaf': 10,
            'random_state': 42
        },
        'time_decay': True,
        'use_kenpom': True,
        'use_inseason_stats': True
    }
}

# Feature definitions
FEATURE_DEFINITIONS = {
    'preseason_kenpom': {
        'description': 'Static preseason KenPom ratings (from season-end snapshot)',
        'features': [
            'AdjEM_home', 'AdjOE_home', 'AdjDE_home', 'AdjTempo_home',
            'Tempo_home', 'Luck_home', 'SOS_home',
            'RankAdjEM_home', 'RankAdjOE_home', 'RankAdjDE_home',
            'AdjEM_away', 'AdjOE_away', 'AdjDE_away', 'AdjTempo_away',
            'Tempo_away', 'Luck_away', 'SOS_away',
            'RankAdjEM_away', 'RankAdjOE_away', 'RankAdjDE_away',
            # Diffs
            'AdjEM_diff', 'AdjOE_diff', 'AdjDE_diff', 'AdjTempo_diff',
            'SOS_diff', 'Luck_diff'
        ]
    },
    
    'market': {
        'description': 'Market-derived features from betting odds',
        'features': [
            'close_spread',
            'home_implied_prob',
            'away_implied_prob',
            'home_favorite',
            'spread_magnitude',
            'prob_diff',
            'vig'
        ]
    },
    
    'time_decay': {
        'description': 'Time-based features for preseason prior decay',
        'features': [
            'days_into_season',
            'games_played_home',
            'games_played_away',
            'season_progress'  # 0.0 at start, 1.0 at end
        ]
    },
    
    'inseason_stats': {
        'description': 'Rolling in-season performance statistics',
        'features': [
            # Offensive efficiency (rolling)
            'ORtg_home_L3', 'ORtg_home_L5', 'ORtg_home_L10',
            'ORtg_away_L3', 'ORtg_away_L5', 'ORtg_away_L10',
            # Defensive efficiency (rolling)
            'DRtg_home_L3', 'DRtg_home_L5', 'DRtg_home_L10',
            'DRtg_away_L3', 'DRtg_away_L5', 'DRtg_away_L10',
            # Pace (rolling)
            'Pace_home_L3', 'Pace_home_L5', 'Pace_home_L10',
            'Pace_away_L3', 'Pace_away_L5', 'Pace_away_L10',
            # Margin of victory (rolling)
            'MoV_home_L3', 'MoV_home_L5', 'MoV_home_L10',
            'MoV_away_L3', 'MoV_away_L5', 'MoV_away_L10',
            # Win rate (rolling)
            'WinPct_home_L5', 'WinPct_home_L10',
            'WinPct_away_L5', 'WinPct_away_L10',
            # Home/away splits
            'ORtg_home_at_home_L5', 'ORtg_away_on_road_L5',
            'DRtg_home_at_home_L5', 'DRtg_away_on_road_L5',
            # Matchup features
            'ORtg_vs_DRtg_L5',  # home_ORtg_L5 - away_DRtg_L5
            'Pace_diff_L5',
            'MoV_diff_L5',
            'Form_diff_L5'  # WinPct difference
        ]
    }
}

def get_variant_config(variant: str) -> Dict[str, Any]:
    """Get configuration for a specific variant."""
    if variant not in VARIANT_CONFIGS:
        raise ValueError(f"Unknown variant: {variant}. Must be one of {list(VARIANT_CONFIGS.keys())}")
    return VARIANT_CONFIGS[variant]

def get_feature_list(variant: str) -> List[str]:
    """Get complete list of features for a variant."""
    config = get_variant_config(variant)
    all_features = []
    
    for group in config['feature_groups']:
        if group in FEATURE_DEFINITIONS:
            all_features.extend(FEATURE_DEFINITIONS[group]['features'])
    
    return all_features

def print_variant_summary(variant: str) -> None:
    """Print a summary of a variant's configuration."""
    config = get_variant_config(variant)
    features = get_feature_list(variant)
    
    print(f"\n{'='*60}")
    print(f"Variant {variant}: {config['name']}")
    print(f"{'='*60}")
    print(f"Description: {config['description']}")
    print(f"Feature groups: {', '.join(config['feature_groups'])}")
    print(f"Total features: {len(features)}")
    print(f"Model type: {config['model_type']}")
    print(f"Use KenPom: {config['use_kenpom']}")
    print(f"Use in-season stats: {config['use_inseason_stats']}")
    print(f"Time decay: {config['time_decay']}")

if __name__ == '__main__':
    # Print all variant summaries
    for variant in ['A', 'B', 'C']:
        print_variant_summary(variant)
