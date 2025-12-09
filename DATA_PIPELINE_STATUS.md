# Data Ingestion & Validation Pipeline - Implementation Status

**Date**: December 8, 2025  
**Status**: Core infrastructure complete, revalidation pipeline in progress

---

## ✅ Completed Components

### 1. Snapshot Consolidator (`consolidate_ratings_snapshots.py`)

**Purpose**: Merge daily/weekly rating snapshots into single dated file.

**Usage**:
```bash
python3 data-collection/consolidate_ratings_snapshots.py \
    --season 2024 \
    --input-dir data/kenpom/snapshots/2024 \
    --pattern "kenpom_ratings_2024_*.csv" \
    --output data/kenpom/kenpom_ratings_2024_dated.csv \
    --source-type kenpom
```

**Features**:
- Extracts `rating_date` from filenames (YYYYMMDD or YYYY-MM-DD format)
- Supports both KenPom and Bart Torvik column mappings
- Deduplicates and sorts by team, rating_date
- Validates required columns (team, AdjEM, AdjOE, AdjDE)
- Outputs summary statistics

**Output Schema**:
```csv
team,rating_date,season,AdjEM,AdjOE,AdjDE,AdjTempo,Tempo,Luck,SOS,...
```

### 2. Ratings Mode Support (`ratings_loader.py`)

**Enhancement**: Added `mode` parameter to `load_season_ratings()`.

**Three Modes**:

| Mode | Description | Data Source | Lookahead? |
|------|-------------|-------------|------------|
| `season_end` | End-of-season snapshot | `kenpom_ratings_YYYY.csv` | ⚠️ YES (biased) |
| `preseason_only` | Preseason ratings only | `kenpom_ratings_YYYY.csv` | ✅ NO (honest but crude) |
| `dated_snapshots` | Multiple dates per team | `kenpom_ratings_YYYY_dated.csv` | ✅ NO (target state) |

**Usage**:
```python
from ratings_loader import load_season_ratings

# Load with specific mode
ratings = load_season_ratings(2024, mode="preseason_only")
```

**New Helper**:
```python
describe_ratings(ratings_df)  # Prints summary stats
```

### 3. Merge Pipeline (`merge_odds_with_kenpom.py`)

**Enhancement**: Added `--ratings-mode` CLI argument.

**Usage**:
```bash
# Season-end mode (default, lookahead biased)
python3 data-collection/merge_odds_with_kenpom.py --ratings-mode season_end

# Preseason-only mode (honest baseline)
python3 data-collection/merge_odds_with_kenpom.py --ratings-mode preseason_only

# Dated snapshots mode (target, lookahead-free)
python3 data-collection/merge_odds_with_kenpom.py --ratings-mode dated_snapshots
```

**Mode-Specific Output Files**:
- `season_end` → `merged_odds_kenpom_full_season_end.csv` (+ default `merged_odds_kenpom_full.csv` for backwards compatibility)
- `preseason_only` → `merged_odds_kenpom_full_preseason.csv`
- `dated_snapshots` → `merged_odds_kenpom_full_dated.csv`

**Summary Output**:
```
[merge_odds_with_kenpom] ratings_mode=preseason_only
                        games=2,457
                        unique_rating_dates_home=1
                        unique_rating_dates_away=1
```

---

## 🔧 In Progress

### 4. One-Command Revalidation Pipeline

**Goal**: Single script to run full evaluation chain and generate Markdown report.

**Planned Script**: `ml/run_full_revalidation.py`

**Workflow**:
1. Merge odds + ratings (specified mode)
2. Validate merged dataset
3. Run walk-forward backtest
4. Match game results
5. Calculate P&L (spread + moneyline)
6. Train market-only baseline
7. Train full model (market + ratings)
8. Compare performance
9. Generate Markdown report

**Planned Usage**:
```bash
# Evaluate preseason-only mode
python3 ml/run_full_revalidation.py \
    --season 2024 \
    --ratings-mode preseason_only \
    --output-report reports/revalidation_preseason_2024.md

# Evaluate dated snapshots (once data available)
python3 ml/run_full_revalidation.py \
    --season 2024 \
    --ratings-mode dated_snapshots \
    --output-report reports/revalidation_dated_2024.md
```

**Report Sections** (planned):
- Configuration (season, mode, files)
- Data Validation (rating_date stats, lookahead check)
- Market-Only Baseline (accuracy, AUC, ROI)
- Full Model (market + ratings)
- Spread P&L Analysis
- Moneyline P&L Analysis
- Conclusion (does this mode add value vs baseline?)

---

## 📋 Next Steps

### Immediate Tasks

1. **Test Current Infrastructure**:
   ```bash
   # Test merge with preseason_only mode
   python3 data-collection/merge_odds_with_kenpom.py --ratings-mode preseason_only
   
   # Verify output
   python3 ml/check_merged_dataset.py
   ```

2. **Build Revalidation Pipeline**:
   - Create `ml/run_full_revalidation.py`
   - Orchestrate existing scripts programmatically
   - Generate Markdown report

3. **Update Documentation**:
   - Add "Ratings Modes" section to `PROJECT_STATUS.md`
   - Document consolidator in `TIME_AWARE_IMPLEMENTATION.md`
   - Add revalidation usage to both docs

### Testing Scenarios

**Scenario 1: Preseason-Only Validation**
```bash
# Run full revalidation with preseason-only ratings
python3 ml/run_full_revalidation.py \
    --season 2024 \
    --ratings-mode preseason_only \
    --output-report reports/revalidation_preseason_2024.md
```

**Expected**:
- Market-only ROI: ~-4.7% (unchanged, no ratings)
- Full model ROI: Unknown (likely worse than season_end due to no in-season rating updates)
- Conclusion: Honest baseline, but crude (no rating evolution)

**Scenario 2: Season-End Validation (Current)**
```bash
# Re-validate current biased state
python3 ml/run_full_revalidation.py \
    --season 2024 \
    --ratings-mode season_end \
    --output-report reports/revalidation_season_end_2024.md
```

**Expected**:
- Market-only ROI: ~-4.7%
- Full model ROI: ~-2.3% (inflated by lookahead)
- KenPom value-add: +2.5% (upper bound)

**Scenario 3: Dated Snapshots (Future)**
```bash
# Once dated ratings are consolidated
python3 data-collection/consolidate_ratings_snapshots.py \
    --season 2024 \
    --input-dir data/kenpom/snapshots/2024 \
    --pattern "kenpom_*.csv" \
    --output data/kenpom/kenpom_ratings_2024_dated.csv \
    --source-type kenpom

# Run revalidation
python3 ml/run_full_revalidation.py \
    --season 2024 \
    --ratings-mode dated_snapshots \
    --output-report reports/revalidation_dated_2024.md
```

**Expected**:
- Market-only ROI: ~-4.7% (unchanged)
- Full model ROI: Unknown (true KenPom value without lookahead)
- KenPom value-add: Real measurement (could be positive, zero, or negative)

---

## 🎯 Success Criteria

### Infrastructure Goals ✅
- [x] Consolidator script handles multiple snapshot files
- [x] Ratings loader supports 3 modes
- [x] Merge pipeline accepts --ratings-mode
- [x] Mode-specific output filenames
- [x] Summary statistics in console output

### Revalidation Goals 🔧
- [ ] Single-command full evaluation
- [ ] Automated report generation
- [ ] Mode comparison (preseason vs season_end vs dated)
- [ ] Clear value-add measurement

### Documentation Goals 📚
- [ ] Modes explained in PROJECT_STATUS.md
- [ ] Consolidator usage in TIME_AWARE_IMPLEMENTATION.md
- [ ] Revalidation workflow documented
- [ ] Example commands for all 3 modes

---

## 📁 File Manifest

### New Files Created ✨
1. `data-collection/consolidate_ratings_snapshots.py` (352 lines)
2. `ml/run_full_revalidation.py` (TODO)

### Modified Files 🔧
1. `data-collection/ratings_loader.py`
   - Added `mode` parameter to `load_season_ratings()`
   - Implemented 3-mode logic
   - Added `describe_ratings()` helper

2. `data-collection/merge_odds_with_kenpom.py`
   - Added `--ratings-mode` CLI argument
   - Updated `merge_with_kenpom()` signature
   - Mode-specific output filenames
   - Summary statistics

### Files to Update 📝
1. `PROJECT_STATUS.md` - Add "Ratings Modes" section
2. `TIME_AWARE_IMPLEMENTATION.md` - Document consolidator + modes
3. `ml/train_baseline_market_only.py` - Add --merged-mode flag (optional)
4. `ml/compare_features_with_without_kenpom.py` - Add --merged-mode flag (optional)

---

## 🚀 Quick Start (When Dated Ratings Available)

```bash
# Step 1: Consolidate daily snapshots
python3 data-collection/consolidate_ratings_snapshots.py \
    --season 2024 \
    --input-dir data/kenpom/snapshots/2024 \
    --pattern "kenpom_ratings_2024_*.csv" \
    --output data/kenpom/kenpom_ratings_2024_dated.csv \
    --source-type kenpom

# Step 2: Run full revalidation
python3 ml/run_full_revalidation.py \
    --season 2024 \
    --ratings-mode dated_snapshots \
    --output-report reports/revalidation_dated_2024.md

# Step 3: Compare to baselines
python3 ml/run_full_revalidation.py --season 2024 --ratings-mode preseason_only \
    --output-report reports/revalidation_preseason_2024.md

python3 ml/run_full_revalidation.py --season 2024 --ratings-mode season_end \
    --output-report reports/revalidation_season_end_2024.md

# Step 4: Review reports
open reports/revalidation_dated_2024.md
open reports/revalidation_preseason_2024.md
open reports/revalidation_season_end_2024.md
```

---

## ⚠️ Current Limitations

1. **No Dated Ratings Data**: Still using season-end snapshots
   - Solution: Acquire KenPom subscription or Torvik archives

2. **Revalidation Pipeline Incomplete**: Manual script orchestration required
   - Solution: Complete `ml/run_full_revalidation.py`

3. **Limited Mode Testing**: Only tested season_end mode extensively
   - Solution: Run preseason_only mode to validate infrastructure

4. **Documentation Gaps**: New features not fully documented
   - Solution: Update PROJECT_STATUS.md and TIME_AWARE_IMPLEMENTATION.md

---

## 💡 Design Philosophy

**Zero Code Changes When Data Arrives**:
- Infrastructure ready for dated ratings
- Just swap CSV files and re-run
- Same code works for all 3 modes

**Explicit Mode Selection**:
- No guessing which data is being used
- CLI args make intent clear
- Mode-specific filenames prevent confusion

**Reproducible Evaluation**:
- One command to run full validation
- Automated reports for comparison
- Clear separation of honest vs biased baselines

---

**Next Action**: Create `ml/run_full_revalidation.py` to orchestrate the full evaluation pipeline.
