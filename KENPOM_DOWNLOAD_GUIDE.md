# KenPom Data Download Guide

Now that you have a KenPom subscription, here's how to get the data you need:

## 📥 What to Download

### 1. Current Season Ratings (2024-25)
**URL**: https://kenpom.com/

**How to download**:
1. Go to https://kenpom.com/
2. Scroll to bottom of ratings table
3. Look for "Download ratings data as .csv" link
4. Click and save as: `kenpom_2025_current.csv`
5. Place in: `/Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball/data/kenpom/`

**What this gives you**:
- Team rankings (1-362)
- Adjusted Offensive Efficiency (AdjO)
- Adjusted Defensive Efficiency (AdjD)
- Adjusted Tempo (AdjT)
- Luck rating
- Strength of Schedule (SOS)
- And more...

---

### 2. Historical Season Ratings

For backtesting, you need ratings for each historical season:

**2021-22 Season**:
1. Go to: https://kenpom.com/index.php?y=2022
2. Scroll to bottom → "Download ratings data as .csv"
3. Save as: `kenpom_2022_final.csv`

**2022-23 Season**:
1. Go to: https://kenpom.com/index.php?y=2023
2. Download → Save as: `kenpom_2023_final.csv`

**2023-24 Season**:
1. Go to: https://kenpom.com/index.php?y=2024
2. Download → Save as: `kenpom_2024_final.csv`

All files go in: `/Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball/data/kenpom/`

---

### 3. Four Factors Data (Optional but Recommended)

**URL**: https://kenpom.com/stats.php

Download for each season:
- Offensive Four Factors: `kenpom_YEAR_offense.csv`
- Defensive Four Factors: `kenpom_YEAR_defense.csv`

**What this gives you**:
- Effective FG% (eFG%)
- Turnover Rate (TOV%)
- Offensive Rebound Rate (ORB%)
- Free Throw Rate (FTR)

---

### 4. Game Predictions (Optional)

**URL**: https://kenpom.com/fanmatch.php

This shows KenPom's predicted spreads for upcoming games.
Good for comparing your model vs his.

---

## 📁 Final Directory Structure

After downloading, you should have:

```
ncaa-basketball/
└── data/
    └── kenpom/
        ├── kenpom_2022_final.csv      (End of 2021-22 season)
        ├── kenpom_2023_final.csv      (End of 2022-23 season)
        ├── kenpom_2024_final.csv      (End of 2023-24 season)
        ├── kenpom_2025_current.csv    (Current 2024-25 season)
        ├── kenpom_2022_offense.csv    (Optional)
        ├── kenpom_2022_defense.csv    (Optional)
        ├── kenpom_2023_offense.csv    (Optional)
        ├── kenpom_2023_defense.csv    (Optional)
        ├── kenpom_2024_offense.csv    (Optional)
        └── kenpom_2024_defense.csv    (Optional)
```

---

## 🔍 What the Data Looks Like

**Sample KenPom ratings file**:

| Rank | Team | Conf | W-L | AdjEM | AdjO | AdjD | AdjT | Luck | SOS | ...
|------|------|------|-----|-------|------|------|------|------|-----|
| 1 | Houston | Amer | 33-5 | 31.72 | 119.4 | 87.7 | 67.5 | 0.040 | 8.09 |
| 2 | UConn | BE | 31-8 | 31.23 | 120.1 | 88.9 | 68.2 | -0.001 | 10.21 |
| 3 | Purdue | B10 | 34-5 | 29.87 | 123.8 | 93.9 | 66.8 | 0.048 | 8.94 |

**Key columns**:
- `AdjEM`: Adjusted Efficiency Margin (AdjO - AdjD)
- `AdjO`: Adjusted Offensive Efficiency (higher = better)
- `AdjD`: Adjusted Defensive Efficiency (lower = better)
- `AdjT`: Adjusted Tempo (possessions per 40 min)
- `Luck`: Deviation from expected wins
- `SOS`: Strength of Schedule

---

## ⚡ Quick Start After Download

Once you've downloaded the files, run:

```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball
python3 data-collection/verify_kenpom_data.py
```

This will verify all files are present and properly formatted.

---

## 🔄 Ongoing Updates

During the season, KenPom updates daily (usually around 11am ET).

**For live predictions**, download fresh ratings:
1. Every Monday morning (after weekend games)
2. Before any predictions you want to make
3. Save with timestamp: `kenpom_2025_MMDD.csv`

---

## 💡 Tips

1. **Keep original filenames**: Makes it easier to track what's what
2. **Backup the files**: KenPom only keeps current season easily accessible
3. **Note the date**: Ratings change daily during season
4. **Check team names**: Sometimes KenPom uses slightly different names than ESPN (e.g., "Connecticut" vs "UConn")

---

## ✅ Checklist

- [ ] Downloaded kenpom_2022_final.csv (2021-22 season)
- [ ] Downloaded kenpom_2023_final.csv (2022-23 season)
- [ ] Downloaded kenpom_2024_final.csv (2023-24 season)
- [ ] Downloaded kenpom_2025_current.csv (2024-25 season)
- [ ] All files placed in `data/kenpom/` directory
- [ ] Verified files with verify_kenpom_data.py

---

**Next step**: Once files are downloaded, I'll create a script to merge KenPom data with your game schedules for backtesting!
