# Bug Fix: CSV Column Mapping for Away Bets
**Date**: December 9, 2025  
**Severity**: Critical (Data Integrity)  
**Status**: ✅ Resolved  
**File**: `scripts/ncaabb/generate_variant_b_picks.py`

---

## Summary

The picks generator was incorrectly mapping `model_prob_home` (home team's win probability) to the CSV's `model_prob` column, regardless of which side was being bet on. This caused **away bets** to show inverted probabilities in the output.

---

## Impact

### Affected Output
- **CSV files**: `variant_b_picks_odds_aware_*.csv`
- **Columns**: `model_prob`, `implied_prob`

### Symptoms
When betting on the **away** team:
- `model_prob` showed the **home team's** win probability (incorrect)
- `implied_prob` showed the **home team's** implied probability (incorrect)
- Edge calculation appeared inverted (though internally correct)

### Example
**UConn +172 vs Florida** (betting on UConn home):
- ❌ **Buggy output**: `model_prob = 0.278` (Florida's prob)
- ✅ **Correct output**: `model_prob = 0.722` (UConn's prob)

**South Dakota St -285 @ Ball State** (betting on SDSU away):
- ❌ **Buggy output**: `model_prob = 0.031` (Ball State's prob)
- ✅ **Correct output**: `model_prob = 0.969` (SDSU's prob)

---

## Root Cause

### Location
File: `scripts/ncaabb/generate_variant_b_picks.py`  
Lines: 505-519 (output formatting section)

### Buggy Code
```python
# 8. Format output
output_df = bets_df[[
    'date', 'home_team', 'away_team', 'chosen_side',
    'bet_odds', 'model_prob_home', 'home_implied_prob', 'max_edge',  # ❌ WRONG
    'kelly_full', 'kelly_applied', 'bet_size_dollars'
]].copy()

output_df = output_df.rename(columns={
    'chosen_side': 'side',
    'bet_odds': 'odds',
    'model_prob_home': 'model_prob',        # ❌ Always home team
    'home_implied_prob': 'implied_prob',    # ❌ Always home team
    'max_edge': 'edge'
})
```

### Why This Was Wrong
- `model_prob_home` **always** contains the home team's win probability
- `home_implied_prob` **always** contains the home team's market probability
- When betting on the **away** team, these values are inverted from the bet's perspective
- The internal calculations used `bet_prob` and `bet_implied_prob` correctly (set by `predict_variant_b()`)
- But the CSV output ignored these correct values and used the wrong columns

---

## Fix Applied

### Corrected Code
```python
# 8. Format output
output_df = bets_df[[
    'date', 'home_team', 'away_team', 'chosen_side',
    'bet_odds', 'bet_prob', 'bet_implied_prob', 'max_edge',  # ✅ CORRECT
    'kelly_full', 'kelly_applied', 'bet_size_dollars'
]].copy()

output_df = output_df.rename(columns={
    'chosen_side': 'side',
    'bet_odds': 'odds',
    'bet_prob': 'model_prob',           # ✅ Correct - chosen side
    'bet_implied_prob': 'implied_prob',  # ✅ Correct - chosen side
    'max_edge': 'edge'
})
```

### Why This Is Correct
- `bet_prob` is set by `predict_variant_b()` to the **chosen side's** win probability
- `bet_implied_prob` is set to the **chosen side's** market probability
- These values are already correctly calculated for both home and away bets
- Edge calculation: `edge = bet_prob - bet_implied_prob` (always correct)

### Source of Correct Values
From `ml/ncaabb_variant_b_model.py` lines 250-260:
```python
df['bet_prob'] = df.apply(
    lambda row: row['model_prob_home'] if row['chosen_side'] == 'home' else row['model_prob_away'],
    axis=1
)

df['bet_implied_prob'] = df.apply(
    lambda row: row['home_implied_prob'] if row['chosen_side'] == 'home' else row['away_implied_prob'],
    axis=1
)
```

These are the **correct** bet-specific probabilities that should be used for output.

---

## Verification

### Test Case 1: Home Bet (BYU -295 vs Clemson)
```
home_team: Brigham Young Cougars
away_team: Clemson Tigers
side: home (betting on BYU)
odds: -295
✅ model_prob = 0.9563 (BYU's probability) ✓
✅ implied_prob = 0.7468 (BYU's market probability) ✓
✅ edge = 0.2095 (20.95%) ✓
```

### Test Case 2: Away Bet (Connecticut vs Florida)
```
home_team: Connecticut
away_team: Florida Gators
side: away (betting on Florida)
odds: +172
✅ model_prob = 0.7218 (Florida's win probability = 1 - 0.278 Connecticut) ✓
✅ implied_prob = 0.3676 (Florida's market probability) ✓
✅ edge = 0.3541 (35.41%) ✓
```

**Before fix**: Would have shown `model_prob = 0.278` (Connecticut's prob), making it look like negative edge

### Test Case 3: Away Bet (South Dakota St @ Ball State)
```
home_team: Ball State
away_team: South Dakota St Jackrabbits
side: away (betting on SDSU)
odds: -285
✅ model_prob = 0.9686 (SDSU's win probability = 1 - 0.031 Ball State) ✓
✅ implied_prob = 0.7403 (SDSU's market probability) ✓
✅ edge = 0.2283 (22.83%) ✓
```

**Before fix**: Would have shown `model_prob = 0.031` (Ball State's prob), making it look like massive negative edge

---

## Impact Assessment

### Data Integrity
- ✅ Internal calculations were **always correct** (Kelly sizing, filtering based on actual edges)
- ❌ CSV output was **misleading** for away bets (probabilities inverted)
- ✅ Home bets were **unaffected** (model_prob_home matched bet_prob)

### User Impact
- **Critical**: Users reviewing CSVs for away bets would see inverted probabilities
- **Confusion**: Edge calculations would appear negative when actually positive
- **Decision Risk**: Could lead to skipping good bets or questioning system integrity
- **Severity**: High - affects trust and usability despite correct internal logic

### System Impact
- ✅ Odds-aware filtering logic: **Not affected** (uses internal `max_edge`)
- ✅ Kelly stake calculation: **Not affected** (uses internal `bet_prob`)
- ✅ Longdog filtering: **Not affected** (uses internal calculations)
- ❌ CSV exports: **Affected** (misleading output for away bets)
- ❌ JSON exports: **Affected** (same column mapping)
- ❌ User reports/summaries: **Affected** (based on CSV data)

---

## Resolution Timeline

1. **Detection**: December 9, 2025 (immediately after generating picks)
   - User review flagged apparent negative edges for UConn and SDSU bets
   - Manual calculation revealed probabilities were inverted

2. **Investigation**: ~10 minutes
   - Traced to line 509-516 of generate_variant_b_picks.py
   - Identified wrong column references in output formatting

3. **Fix**: ~2 minutes
   - Changed `model_prob_home` → `bet_prob`
   - Changed `home_implied_prob` → `bet_implied_prob`

4. **Verification**: ~5 minutes
   - Regenerated all picks for Dec 9-10
   - Manually verified probabilities for all 7 bets
   - Confirmed edge calculations accurate

5. **Documentation**: ~15 minutes
   - Updated picks summary document
   - Created comprehensive bug report
   - Added test cases for future reference

**Total time**: ~32 minutes from detection to full resolution and documentation

---

## Prevention

### Code Review Checklist
- [ ] When formatting output, verify column names match the bet-specific values
- [ ] Test with both home and away bets to catch side-specific bugs
- [ ] Add assertions that edge = model_prob - implied_prob in output
- [ ] Include sanity checks (e.g., probabilities should never be < 0.01 for high-confidence bets)

### Testing Recommendations
1. **Unit test** for output formatting with known home/away scenarios
2. **Integration test** comparing internal edge to CSV edge for sample bets
3. **Regression test** to catch future column mapping errors

### Documentation
- ✅ This bug report serves as reference for similar issues
- ✅ Summary document updated with bug fix notation
- ✅ Future developers will see the correct pattern

---

## Related Code

### Function: predict_variant_b() 
**File**: `ml/ncaabb_variant_b_model.py` lines 223-276

Sets the correct bet-specific values:
- `bet_prob`: Win probability for chosen side
- `bet_implied_prob`: Market probability for chosen side  
- `max_edge`: Maximum edge (already correct by definition)

### Section: Output Formatting
**File**: `scripts/ncaabb/generate_variant_b_picks.py` lines 505-528

Creates CSV/JSON output. **Must use bet_prob and bet_implied_prob**, not model_prob_home/away.

---

## Lessons Learned

1. **Always use bet-specific columns for output** - `bet_prob` not `model_prob_home`
2. **Test with away bets explicitly** - Home bias can hide bugs
3. **Verify output manually** - Automated tests should include sanity checks
4. **Document column semantics clearly** - Prevent future confusion
5. **Quick detection is key** - User review caught this immediately

---

## Status

✅ **RESOLVED** - All systems operational with corrected data
- All picks regenerated with accurate probabilities
- CSV and JSON outputs verified
- Documentation updated
- No further action required

**Confidence**: High - Manual verification confirms all 7 picks have correct data