# NCAA Men's Basketball Data Sources

## 🏆 Priority Python Packages (HIGHLY RECOMMENDED)

### 1. **CBBpy** - Best Overall Python Package ⭐⭐⭐⭐⭐
- **GitHub**: https://github.com/dcstats/CBBpy
- **Installation**: `pip install cbbpy`
- **Language**: Python
- **Data Available**:
  - ✅ **Play-by-play data** (detailed event tracking)
  - ✅ **Box scores** (player stats per game)
  - ✅ **Game metadata** (dates, scores, attendance, referees)
  - ✅ **Team schedules** (full season schedules)
  - ✅ **Conference schedules** (all teams in conference)
  - ✅ **Player info and rosters**
  - ✅ **Historical data back to 2015+**
- **Key Functions**:
  - `get_game_pbp(game_id)` - Play-by-play
  - `get_game_boxscore(game_id)` - Box scores
  - `get_games_season(season)` - All games in season
  - `get_games_range(start_date, end_date)` - Date range
  - `get_games_team(team, season)` - Team's full season
  - `get_team_schedule(team, season)` - Schedule with game IDs
- **Data Source**: ESPN (scrapes from ESPN's website)
- **Historical Coverage**: 2015-present for most data
- **Cost**: Free
- **Quality**: ★★★★★
- **Verdict**: **USE THIS AS PRIMARY DATA SOURCE** - Most comprehensive Python package

### 2. **hoopR** - R Package (If we need R compatibility)
- **GitHub**: https://github.com/sportsdataverse/hoopR
- **Language**: R (not Python, but very comprehensive)
- **Data Available**:
  - Play-by-play for NCAA and NBA
  - Box scores
  - Historical data 2006-2024
  - Full NBA Stats API wrapper
- **Note**: Since your project is JavaScript/Python, we'd need to either:
  - Call R from Python (possible but complex)
  - Use their pre-compiled data files
  - **Recommendation**: Skip this, use CBBpy instead

### 3. **ncaa-api** - REST API Alternative
- **GitHub**: https://github.com/henrygd/ncaa-api
- **Demo API**: https://ncaa-api.henrygd.me/openapi
- **Language**: TypeScript/Node.js (REST API)
- **Data Available**:
  - ✅ Live scores (scoreboards)
  - ✅ Team stats and rankings
  - ✅ Standings
  - ✅ Individual game details
  - ✅ Play-by-play
  - ✅ Box scores
  - ✅ Historical championship data
- **Access**: REST API calls
- **Rate Limit**: 5 requests/second on public API
- **Cost**: Free (can self-host for unlimited)
- **Quality**: ★★★★☆
- **Verdict**: **Good backup/supplement** - Use if CBBpy is missing something

## Free Advanced Stats Sources

### 4. **T-Rank (Barttorvik)** ⭐⭐⭐⭐⭐
- **URL**: https://barttorvik.com/
- **Data Available**:
  - Adjusted offensive/defensive efficiency
  - Tempo (possessions per game)
  - Four Factors breakdowns
  - Strength of schedule
  - Game predictions
  - Team rankings and ratings
  - **Historical data available**
- **Access**: Free website, some CSV exports available
- **Cost**: Free (with premium option)
- **Quality**: ★★★★★ (Excellent, very similar to KenPom)
- **Verdict**: **PRIMARY SOURCE FOR EFFICIENCY METRICS**

### 5. **Sports-Reference (College Basketball Reference)**
- **URL**: https://www.sports-reference.com/cbb/
- **Data Available**:
  - Team schedules and results
  - Basic box scores
  - Team season stats (offensive/defensive efficiency approximations)
  - Historical data back many years
  - Player stats
- **Access**: Web scraping (be respectful of rate limits)
- **Cost**: Free with ethical scraping
- **Quality**: ★★★★☆ (Good but not as advanced as KenPom)

### 6. **ESPN API (Unofficial)**
- **URL**: Various ESPN endpoints
- **Data Available**:
  - Schedules
  - Scores
  - Basic team stats
  - Odds/lines (sometimes)
- **Access**: Unofficial API endpoints
- **Cost**: Free
- **Quality**: ★★★☆☆ (Good for schedules/scores, weak on advanced stats)
- **Note**: CBBpy uses ESPN as source, so this is redundant

### 7. **The Odds API**
- **URL**: https://the-odds-api.com/
- **Data Available**:
  - Current betting lines (ML, spread, totals)
  - Line movement
  - Multiple sportsbooks
- **Access**: API with free tier (500 requests/month)
- **Cost**: Free tier, then $25-100/month for more
- **Quality**: ★★★★★ (Essential for line comparisons)

## Paid Data Sources (Worth It)

### 8. **KenPom**
- **URL**: https://kenpom.com/
- **Data Available**:
  - Gold standard adjusted efficiency ratings
  - Tempo-adjusted stats
  - Luck metrics (Pythagorean wins)
  - Game predictions
  - Conference adjustments
  - Experience ratings
- **Access**: Subscription required for full data
- **Cost**: $24.95/year
- **Quality**: ★★★★★ (Industry standard)
- **Verdict**: **WORTH IT** - This is the foundation
- **⚠️ Snapshot timing**: Current files in `data/kenpom/kenpom_ratings_20XX.csv` are tagged `DataThrough = "End of season"` and metadata timestamps (e.g., `metadata_2025.json` collected `2025-12-04`) show they were pulled after the season concluded. When merged via `merge_kenpom_schedules.py`, every game in a season uses the same final ratings, which leaks future information into training/backtests. To avoid lookahead, capture rolling daily downloads (or Bart Torvik snapshots) so that each game only sees ratings available prior to tip-off.

## 📋 RECOMMENDED DATA ARCHITECTURE

### Phase 1: MVP (Start This Week)
1. **CBBpy (Python)** - PRIMARY data source
   - Install: `pip install cbbpy`
   - Collect 3-4 years of historical data (2021-22 through 2024-25)
   - Game-level data: schedules, results, box scores
2. **T-Rank web scraping** - Efficiency metrics
   - Scrape current season efficiency ratings
   - Build historical database from archived data
3. **KenPom subscription** ($25/year) - Gold standard metrics
   - Manual download of historical data
   - Weekly updates during season
4. **The Odds API** - Current lines (for backtesting validation)

### Phase 2: Enhancement (After MVP Working)
1. Add play-by-play analysis from CBBpy
2. Injury tracking (news scraping)
3. Home court advantage adjustments
4. Conference tournament simulation

## 🗂️ Historical Data Requirements (3-4 Years)

For proper backtesting, we need **2021-22, 2022-23, 2023-24, and 2024-25** seasons:

### Game Results (CBBpy)
- Date, home/away teams, scores
- Game IDs for detailed analysis
- **Estimated rows**: ~350 teams × 30 games × 4 years = ~42,000 games

### Team Efficiency (T-Rank / KenPom)
- Daily snapshots during season
- Adjusted offensive/defensive efficiency
- Tempo
- Four Factors
- **Estimated rows**: 350 teams × 120 days × 4 years = ~168,000 snapshots

### Vegas Lines (The Odds API or manual collection)
- Spreads, moneylines, totals
- Closing lines (most important)
- **Estimated rows**: ~42,000 games with lines

### Box Scores (CBBpy - optional for Phase 1)
- Player-level stats per game
- **Estimated rows**: ~42,000 games × 20 players = ~840,000 player-game records

## Key Metrics We Need

### Offensive Efficiency (Points per 100 possessions)
- Adjusted for opponent quality
- Home/away splits
- Recent form (last 5-10 games)

### Defensive Efficiency (Points allowed per 100 possessions)
- Adjusted for opponent quality
- Home/away splits
- Recent form

### Tempo (Possessions per game)
- Critical for spread modeling
- Fast vs slow team mismatches

### Four Factors
**Offense:**
1. Effective FG% (includes 3PT bonus)
2. Turnover Rate
3. Offensive Rebound Rate
4. Free Throw Rate

**Defense:**
1. Opponent eFG%
2. Opponent Turnover Rate
3. Defensive Rebound Rate
4. Opponent FT Rate

### Experience/Continuity
- Average experience (years in program)
- Returning minutes %
- Coaching stability

### Strength of Schedule
- Adjusted for opponent quality
- Non-conference vs conference

### Home Court Advantage
- Varies by venue (some arenas worth 5+ points, others 2-3)
- Altitude factors (Denver, Wyoming, etc.)

## Model Features (Preliminary)

```javascript
const teamFeatures = {
  // Core Efficiency (from KenPom/T-Rank)
  adjOffEff: 115.2,        // Adjusted offensive efficiency
  adjDefEff: 98.5,         // Adjusted defensive efficiency
  adjTempo: 68.4,          // Adjusted tempo
  
  // Four Factors
  eFG_offense: 0.535,
  eFG_defense: 0.485,
  TORate_offense: 0.165,
  TORate_defense: 0.210,
  OReb_rate: 0.325,
  DReb_rate: 0.735,
  FTRate_offense: 0.325,
  FTRate_defense: 0.285,
  
  // Context
  experience: 2.3,          // Average years
  homeCourtAdv: 3.8,       // Points at home
  strengthOfSchedule: 0.525,
  
  // Recent Form (last 10 games)
  recentOffEff: 118.5,
  recentDefEff: 96.2,
  wins_L10: 7,
  
  // Matchup Specific
  vs_fast_teams: 0.520,    // Win rate vs high tempo
  vs_slow_teams: 0.680,    // Win rate vs low tempo
  vs_top50: 0.450,         // Performance vs elite teams
};
```

## Next Steps
1. ✅ Document data sources (this file)
2. Subscribe to KenPom
3. Build T-Rank scraper
4. Create data collection scripts
5. Build prediction model
