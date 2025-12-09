# 🏀 NCAA Men's Basketball Prediction System

Building a KenPom-style efficiency model to beat Vegas lines on NCAA basketball spreads and moneylines.

## 🎯 Project Goals

1. **Beat Vegas** on NCAA Men's Basketball spreads and moneylines
2. **High volume** market with 300+ games per week during season
3. **Proven approach** - similar to successful NBA model
4. **Backtestable** with 3-4 years of historical data

## 📊 Why NCAA Basketball is Beatable

- **Softer lines** than NBA - Vegas less sharp on 350+ teams
- **Tempo mismatches** create exploitable spreads
- **Experience gaps** are massive and predictable
- **Early season** lines don't adjust for roster changes
- **Conference play** lags reality by 2-3 games

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd /Users/brentgoldman/Desktop/NEWMODEL/ncaa-basketball
python data-collection/setup.py
```

This installs:
- `cbbpy` - ESPN data scraper
- `pandas`, `numpy` - data processing
- `beautifulsoup4`, `requests` - web scraping

### Step 2: Test Data Collection

```bash
python data-collection/test_data_collection.py
```

This validates that CBBpy is working and shows sample data.

### Step 3: Collect Historical Data

```bash
python data-collection/collect_historical_games.py
```

This collects **4 seasons** of game data (2021-22 through 2024-25):
- Game schedules and results (~42,000 games)
- Box scores (~840,000 player-game records)
- Game metadata (dates, attendance, officials)

**Time required**: 20-60 minutes depending on your connection

### Step 4: Subscribe to KenPom ($25/year)

1. Go to https://kenpom.com/
2. Subscribe for $24.95/year
3. Download historical efficiency data
4. Place in `data/kenpom/` directory

## 📁 Project Structure

```
ncaa-basketball/
├── DATA_SOURCES.md          # Comprehensive data source documentation
├── README.md                 # This file
├── data-collection/
│   ├── setup.py             # Install dependencies
│   ├── test_data_collection.py  # Validate CBBpy works
│   ├── collect_historical_games.py  # Collect 4 years of data
│   └── scrape_trank.py      # T-Rank efficiency scraper (TODO)
├── data/
│   ├── historical/          # Game results, box scores (auto-created)
│   ├── kenpom/             # KenPom efficiency data (manual download)
│   ├── trank/              # T-Rank efficiency data (scraped)
│   └── odds/               # Historical Vegas lines (TODO)
├── models/
│   └── efficiency_model.py  # Core prediction model (TODO)
├── prediction-engine/
│   └── generate_predictions.py  # Daily picks generator (TODO)
└── frontend/
    └── ncaa-picks.mjs       # Display picks (TODO)
```

## 🔑 Key Data Sources

### Primary Sources

1. **CBBpy** (Python) - Game data, schedules, box scores
   - Free, comprehensive ESPN scraper
   - Historical data back to 2015
   - ⭐ **Main data source**

2. **T-Rank/Barttorvik** - Efficiency metrics
   - Free advanced stats
   - Adjusted tempo and efficiency
   - Similar quality to KenPom

3. **KenPom** - Gold standard efficiency ratings
   - $25/year subscription
   - Industry standard for efficiency
   - **Worth every penny**

4. **The Odds API** - Vegas lines
   - Compare our predictions vs market
   - Validate backtesting accuracy

See [DATA_SOURCES.md](./DATA_SOURCES.md) for complete documentation.

## 🎓 Model Features (Planned)

Based on successful NBA model architecture:

### Core Efficiency Metrics
- Adjusted offensive/defensive efficiency (points per 100 possessions)
- Tempo (pace of play)
- Four Factors (eFG%, TOV%, OREB%, FTR)

### Matchup Analysis
- Pace mismatch detection (fast vs slow)
- 3PT shooting vs 3PT defense
- Rebounding battles
- Turnover creation vs ball security

### Context Factors
- Home court advantage (varies by venue)
- Recent form (last 5-10 games)
- Experience/continuity
- Strength of schedule
- Rest/travel (back-to-backs)

### Edge Detection
- Early season lines (roster changes)
- Conference play adjustments
- Injury impacts
- Coaching effects

## 📈 Success Metrics

- **Win Rate Target**: 54%+ ATS (Against The Spread)
- **ROI Target**: 8%+ (after juice)
- **Volume**: 50-100 picks per week during season
- **Confidence Tiers**: High (5u), Medium (3u), Low (1u)

## 🗓️ Timeline

### Week 1: Data Collection ✅
- [x] Document data sources
- [x] Install CBBpy
- [ ] Collect 4 years historical data
- [ ] Subscribe to KenPom
- [ ] Manual KenPom data download

### Week 2: Model Development
- [ ] Build efficiency rating system
- [ ] Create matchup analysis layer
- [ ] Implement Four Factors
- [ ] Add home court adjustment

### Week 3: Backtesting
- [ ] Test model on 2022-23 season
- [ ] Test model on 2023-24 season
- [ ] Compare predictions vs actual spreads
- [ ] Identify profitable spots

### Week 4: Production System
- [ ] Daily data pipeline
- [ ] Prediction generation
- [ ] Frontend interface
- [ ] Confidence scoring

## 🏆 Similar to NBA Model

Our NBA model currently achieves:
- **56% win rate** on spreads/ML
- **Profitable** after juice
- **150+ picks per week**

NCAA should be **easier to beat** because:
- Lines are softer (more teams, less attention)
- Public overvalues name brands
- Experience gaps are exploitable
- Home court varies more

## 📚 Resources

- [KenPom](https://kenpom.com/) - Efficiency ratings and methodology
- [T-Rank](https://barttorvik.com/) - Free alternative to KenPom
- [CBBpy Docs](https://github.com/dcstats/CBBpy) - Data collection library
- [The Odds API](https://the-odds-api.com/) - Current lines

## 🤝 Next Steps

1. **Run setup.py** to install dependencies
2. **Run test_data_collection.py** to validate
3. **Run collect_historical_games.py** to build database
4. **Subscribe to KenPom** for efficiency data
5. **Review DATA_SOURCES.md** for additional context

---

**Current Status**: 📊 Data Collection Phase
**Next Milestone**: Historical data collected (4 seasons)
**Season Start**: November 2024 (already underway!)
