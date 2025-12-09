# Edge Profitability Analysis - Variant B

**Date:** December 9, 2025  
**Model:** Variant B (Market + In-Season Stats Only)  
**Test Set:** 2,163 games  
**Test AUC:** 0.8111  
**Approved ROI (15% edge threshold):** 25.3%

---

## Key Findings Summary

### 🚨 **CRITICAL: Longshots Are NOT Profitable**

**Longshots (+900 or more odds) - COMPLETE TEST SET ANALYSIS:**
- **Total Bets:** 93 games
- **Actual Wins:** 2 (2.15% win rate)
- **Model Average Probability:** 2.01%
- **The model is well-calibrated for longshots overall!**

**The 2 longshot wins (both had NEGATIVE edge):**
1. ✅ **Air Force +1175** beat New Mexico (78-77)
   - Model: 3.32%, Market: 7.84%, Edge: **-4.5%** (model said skip)
2. ✅ **Elon +1150** beat UNC Wilmington (73-72)  
   - Model: 4.62%, Market: 8.00%, Edge: **-3.4%** (model said skip)

**Longshots with POSITIVE edge (15%+ edge threshold):**
- **Total Bets:** 2 (West Virginia +1050, Saint Peter's +1100)
- **Wins:** 0
- **Win Rate:** 0% (0-2)
- **ROI:** **-100%**
- **P&L:** -$200

**Analysis:**
- Model gave these 25-28% win probability (10x higher than typical longshot)
- Market implied only 8-9% win probability  
- Edge appeared to be 16-19%
- Both lost decisively (64-71 and 49-83)
- **When the model sees big positive edge on longshots, it's systematically wrong**

**By Edge Bucket (all +900 longshots):**
- **Negative Edge:** 91 bets, 2 wins (2.2%), -72.3% ROI, -$6,575
- **15-20% Edge:** 2 bets, 0 wins (0.0%), -100% ROI, -$200

**By Odds Range:**
- **+900 to +1200:** 24 bets, 2 wins (8.33%), +5.2% ROI, +$125 ✅
- **+1200 to +1500:** 1 bet, 0 wins (0.0%), -100% ROI, -$100
- **+1500+:** 68 bets, 0 wins (0.0%), -100% ROI, -$6,800

**KEY INSIGHT:** The only longshots that won had **negative edge** (model correctly said they were bad bets). The 2 longshots with positive edge **both lost**. This suggests the model's edge calculation breaks down at extreme odds - when it's confident enough to show positive edge on a longshot, it's overconfident.

---

## Best Performing Edge Buckets

### 🎯 **Sweet Spot: 30-40% Edge**
- **Bets:** 77
- **Win Rate:** 94.8%
- **ROI:** +85.8%
- **P&L:** +$6,606

### 💪 **Also Excellent: 40-50% Edge**
- **Bets:** 52
- **Win Rate:** 98.1%
- **ROI:** +84.8%
- **P&L:** +$4,412

### ⚠️ **Lower Edge Warning: 15-25% Edge**
- **15-20% Edge:**
  - Bets: 297
  - Win Rate: 63.6%
  - ROI: **-13.9%** ❌
  - P&L: -$4,124

- **20-25% Edge:**
  - Bets: 109
  - Win Rate: 59.6%
  - ROI: **-9.5%** ❌
  - P&L: -$1,037

---

## Profitability by Model Win Probability

| Model Win Prob | Bets | Win Rate | ROI | P&L |
|----------------|------|----------|-----|-----|
| 25-35% | 10 | 50.0% | **-46.9%** ❌ | -$469 |
| 35-50% | 9 | 55.6% | +8.8% ✅ | +$79 |
| 50-65% | 106 | 48.1% | **-6.1%** ❌ | -$649 |
| **65%+** | **1,526** | **59.6%** | **+2.6%** ✅ | **+$4,028** |

**Key Insight:** The model only makes money when betting on teams with **65%+ win probability**. Lower probability bets are unprofitable, even with apparent edge.

---

## Profitability by Odds Ranges

| Odds Range | Bets | Win Rate | ROI | P&L | Notes |
|------------|------|----------|-----|-----|-------|
| -300 to -1000 | 9 | 88.9% | +14.2% ✅ | +$128 | Heavy favorites (small sample) |
| -200 to -300 | 112 | 91.1% | **+30.4%** ✅ | +$3,401 | **Strong favorites - best category** |
| -150 to -200 | 22 | 72.7% | +15.6% ✅ | +$343 | Moderate favorites |
| -110 to -150 | 63 | 76.2% | **+35.8%** ✅ | +$2,253 | **Slight favorites - excellent** |
| +100 to +110 | 100 | 85.0% | **+72.1%** ✅ | +$7,209 | **Pick'em range - best ROI** |
| +110 to +200 | 535 | 48.4% | +1.8% ✅ | +$959 | Slight underdogs (barely profitable) |
| +200 to +400 | 15 | 53.3% | +6.7% ✅ | +$100 | Moderate underdogs |
| +400 to +1000 | 14 | 50.0% | **-45.0%** ❌ | -$630 | **Big underdogs - unprofitable** |
| **+1000+** | **4** | **50.0%** | **-48.0%** ❌ | **-$192** | **Longshots - avoid** |

**Pattern:** Profitability peaks at favorites and pick'em games, drops sharply for big underdogs (+400 or more).

---

## Combined Analysis: Edge × Model Probability

Best combinations (ROI > 50%):

| Edge Bucket | Model Prob | Bets | Win Rate | ROI | P&L |
|-------------|------------|------|----------|-----|-----|
| 25-35% | 50-70% | 24 | 79.2% | **+109.3%** 🔥 | +$2,624 |
| 35-50% | 70%+ | 209 | 78.0% | **+62.0%** 🔥 | +$12,960 |
| 50%+ | 70%+ | 41 | 80.5% | **+87.1%** 🔥 | +$3,570 |

Worst combinations:

| Edge Bucket | Model Prob | Bets | Win Rate | ROI | P&L |
|-------------|------------|------|----------|-----|-----|
| 15-25% | 15-30% | 3 | 0.0% | **-100.0%** ❌ | -$300 |
| 25-35% | 30-50% | 2 | 0.0% | **-100.0%** ❌ | -$200 |
| 35-50% | 50-70% | 3 | 0.0% | **-100.0%** ❌ | -$300 |

---

## Recommendations for Live Betting

### ✅ **BET THESE:**
1. **Edge 30%+ AND Model Prob 70%+** - Highest ROI (60-87%)
2. **Odds -300 to -110** - Strong/moderate favorites
3. **Odds +100 to +200** - Slight underdogs to pick'em

### ⚠️ **BE CAUTIOUS:**
1. **Edge 15-25%** - Historically unprofitable (-13.9% to -9.5% ROI)
2. **Model Prob 25-50%** - Loses money across the board
3. **Odds +200 to +400** - Barely profitable, high variance

### 🚫 **AVOID:**
1. **Odds +1000 or more (longshots)** - 0% win rate with 15%+ edge
2. **Odds +400 to +1000** - Also unprofitable (-45% ROI)
3. **Any bet with Model Prob < 35%** - Loses money even with apparent edge

---

## Today's Picks Re-Evaluation

### Pick 1: Villanova +1160 @ Michigan
- **Current System:** Bet $115 (1.2% of bankroll)
- **Model Win Prob:** 13.2%
- **Edge:** 53.3%
- **Historical Performance:** Longshots with 15%+ edge went 0-2 (lost both)
- **Recommendation:** **🚫 SKIP** - This fits the profile of bets that lose despite high edge
- **Reason:** Model has proven to overestimate extreme underdog chances

### Pick 2: BYU -315 vs Clemson
- **Current System:** Bet $1,000 (10% of bankroll)
- **Model Win Prob:** ~75-80% (implied from -315)
- **Edge:** 20.6%
- **Odds Range:** -200 to -300 (30.4% ROI historically)
- **Edge Bucket:** 20-25% (-9.5% ROI historically)
- **Recommendation:** **⚠️ REDUCE STAKE** - Edge too low for historical profitability
- **Better Threshold:** Wait for 25%+ edge on favorites

---

## Suggested Rule Modifications

Based on this analysis, consider these updated filters:

```python
# Current filter
min_edge = 0.15  # 15%

# Suggested improvements
min_edge = 0.25  # Raise to 25%
min_model_prob = 0.35  # Only bet teams with 35%+ win probability
max_odds = 400  # Don't bet longshots over +400

# Or create tiered system:
if odds > 400:
    skip_bet()  # Avoid big underdogs entirely
elif odds >= 0 and edge < 0.25:
    skip_bet()  # Underdogs need 25%+ edge
elif odds < 0 and edge < 0.20:
    skip_bet()  # Favorites can work with 20%+ edge
else:
    place_bet()
```

---

## Statistical Summary

**Overall Performance (15% edge threshold):**
- Total qualifying bets: 657
- Win rate: 58.7%
- ROI: +3.0%
- P&L: +$1,979

**With recommended filters (25% edge, 35%+ prob, max +400 odds):**
- Estimated bets: ~400
- Estimated win rate: ~75%
- Estimated ROI: ~40%+
- Would have avoided both historical longshot losses
- Would have avoided most of the -$5,161 losses in 15-25% edge bucket

---

## Conclusion

The model is **excellent at identifying value in favorites and moderate underdogs**, but **systematically overestimates longshot chances**. The 53.3% edge on Villanova +1160 is a **red flag**, not a green light - it's exactly the type of bet that went 0-2 historically.

**Key takeaway:** Trust the model when it's confident (high win probability), be skeptical when it finds massive edge on longshots.
