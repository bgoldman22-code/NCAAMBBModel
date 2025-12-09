#!/usr/bin/env python3
"""
Test Odds-Aware Filtering Logic

Unit tests for the decide_min_edge_for_odds() function
to ensure it correctly implements the policy rules.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts' / 'ncaabb'))

from generate_variant_b_picks import decide_min_edge_for_odds


def test_favorites():
    """Test favorites (negative odds) require 15% edge"""
    assert decide_min_edge_for_odds(-150, True) == 0.15
    assert decide_min_edge_for_odds(-200, True) == 0.15
    assert decide_min_edge_for_odds(-500, True) == 0.15
    print("✅ Favorites: Require 15% edge")


def test_small_dogs():
    """Test small dogs (+100-119) require 15% edge"""
    assert decide_min_edge_for_odds(100, False) == 0.15
    assert decide_min_edge_for_odds(110, False) == 0.15
    assert decide_min_edge_for_odds(119, False) == 0.15
    print("✅ Small dogs (+100-119): Require 15% edge")


def test_zone1_120_139():
    """Test Zone 1 (+120-139) requires 15% edge"""
    assert decide_min_edge_for_odds(120, False) == 0.15
    assert decide_min_edge_for_odds(130, False) == 0.15
    assert decide_min_edge_for_odds(139, False) == 0.15
    print("✅ Zone 1 (+120-139): Require 15% edge")


def test_death_valley1_140_159():
    """Test Death Valley 1 (+140-159) is skipped"""
    assert decide_min_edge_for_odds(140, False) is None
    assert decide_min_edge_for_odds(150, False) is None
    assert decide_min_edge_for_odds(159, False) is None
    print("✅ Death Valley 1 (+140-159): Skip entirely")


def test_zone2_160_179():
    """Test Zone 2 (+160-179) requires 13% edge"""
    assert decide_min_edge_for_odds(160, False) == 0.13
    assert decide_min_edge_for_odds(170, False) == 0.13
    assert decide_min_edge_for_odds(179, False) == 0.13
    print("✅ Zone 2 (+160-179): Require 13% edge")


def test_death_valley2_180_199():
    """Test Death Valley 2 (+180-199) is skipped"""
    assert decide_min_edge_for_odds(180, False) is None
    assert decide_min_edge_for_odds(190, False) is None
    assert decide_min_edge_for_odds(199, False) is None
    print("✅ Death Valley 2 (+180-199): Skip entirely")


def test_zone3_200_249():
    """Test Zone 3 (+200-249) has no edge filter"""
    assert decide_min_edge_for_odds(200, False) == 0.0
    assert decide_min_edge_for_odds(225, False) == 0.0
    assert decide_min_edge_for_odds(249, False) == 0.0
    print("✅ Zone 3 (+200-249): No edge filter (0%)")


def test_death_valley3_250_399():
    """Test Death Valley 3 (+250-399) is skipped"""
    assert decide_min_edge_for_odds(250, False) is None
    assert decide_min_edge_for_odds(300, False) is None
    assert decide_min_edge_for_odds(399, False) is None
    print("✅ Death Valley 3 (+250-399): Skip entirely")


def test_longdogs_400_plus():
    """Test +400 longdogs default to 15% (but should be filtered earlier)"""
    # These should already be filtered by longdog system,
    # but if they slip through, use default
    assert decide_min_edge_for_odds(400, False) == 0.15
    assert decide_min_edge_for_odds(500, False) == 0.15
    assert decide_min_edge_for_odds(1000, False) == 0.15
    print("✅ Longdogs (+400+): Default 15% (should be filtered earlier)")


def test_edge_boundaries():
    """Test edge cases at boundaries"""
    # Boundary between small dogs and zone 1
    assert decide_min_edge_for_odds(119, False) == 0.15
    assert decide_min_edge_for_odds(120, False) == 0.15
    
    # Boundary between zone 1 and death valley 1
    assert decide_min_edge_for_odds(139, False) == 0.15
    assert decide_min_edge_for_odds(140, False) is None
    
    # Boundary between death valley 1 and zone 2
    assert decide_min_edge_for_odds(159, False) is None
    assert decide_min_edge_for_odds(160, False) == 0.13
    
    # Boundary between zone 2 and death valley 2
    assert decide_min_edge_for_odds(179, False) == 0.13
    assert decide_min_edge_for_odds(180, False) is None
    
    # Boundary between death valley 2 and zone 3
    assert decide_min_edge_for_odds(199, False) is None
    assert decide_min_edge_for_odds(200, False) == 0.0
    
    # Boundary between zone 3 and death valley 3
    assert decide_min_edge_for_odds(249, False) == 0.0
    assert decide_min_edge_for_odds(250, False) is None
    
    # Boundary between death valley 3 and longdogs
    assert decide_min_edge_for_odds(399, False) is None
    assert decide_min_edge_for_odds(400, False) == 0.15
    
    print("✅ Boundary cases: All correct")


def test_filtering_logic():
    """Test complete filtering scenarios"""
    
    # Scenario 1: Zone 1 bet with 20% edge -> ACCEPT
    odds = 130
    edge = 0.20
    required = decide_min_edge_for_odds(odds, False)
    assert required is not None and edge >= required
    print("✅ Zone 1 (+130) with 20% edge: ACCEPTED")
    
    # Scenario 2: Zone 1 bet with 10% edge -> REJECT
    odds = 130
    edge = 0.10
    required = decide_min_edge_for_odds(odds, False)
    assert required is not None and edge < required
    print("✅ Zone 1 (+130) with 10% edge: REJECTED")
    
    # Scenario 3: Death Valley bet with 50% edge -> REJECT
    odds = 150
    edge = 0.50
    required = decide_min_edge_for_odds(odds, False)
    assert required is None
    print("✅ Death Valley (+150) with 50% edge: REJECTED (death valley)")
    
    # Scenario 4: Zone 3 bet with 5% edge -> ACCEPT
    odds = 220
    edge = 0.05
    required = decide_min_edge_for_odds(odds, False)
    assert required is not None and edge >= required
    print("✅ Zone 3 (+220) with 5% edge: ACCEPTED (no filter)")
    
    # Scenario 5: Zone 2 bet with 13% edge -> ACCEPT
    odds = 170
    edge = 0.13
    required = decide_min_edge_for_odds(odds, False)
    assert required is not None and edge >= required
    print("✅ Zone 2 (+170) with 13% edge: ACCEPTED")
    
    # Scenario 6: Zone 2 bet with 12% edge -> REJECT
    odds = 170
    edge = 0.12
    required = decide_min_edge_for_odds(odds, False)
    assert required is not None and edge < required
    print("✅ Zone 2 (+170) with 12% edge: REJECTED")


if __name__ == '__main__':
    print("="*80)
    print("Testing Odds-Aware Filtering Logic")
    print("="*80)
    print()
    
    try:
        test_favorites()
        test_small_dogs()
        test_zone1_120_139()
        test_death_valley1_140_159()
        test_zone2_160_179()
        test_death_valley2_180_199()
        test_zone3_200_249()
        test_death_valley3_250_399()
        test_longdogs_400_plus()
        test_edge_boundaries()
        test_filtering_logic()
        
        print()
        print("="*80)
        print("✅ All Tests Passed!")
        print("="*80)
        print()
        print("Policy implementation verified:")
        print("  • Correct edge thresholds for all zones")
        print("  • Death valleys properly skipped")
        print("  • Boundary cases handled correctly")
        print("  • Filtering logic works as expected")
        print()
        print("🚀 Ready for production!")
        
    except AssertionError as e:
        print()
        print("="*80)
        print("❌ Test Failed!")
        print("="*80)
        print(f"Error: {e}")
        sys.exit(1)
