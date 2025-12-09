"""
Comprehensive NCAA Basketball Team Name Database

This database handles all the variations of team names across different data sources:
- The Odds API
- ESPN API
- KenPom
- CBBpy
"""

# Master team database - canonical name is the key
TEAM_DATABASE = {
    # Power 5 - ACC
    'Boston College': ['Boston College', 'Boston College Eagles', 'BC', 'BC Eagles'],
    'Clemson': ['Clemson', 'Clemson Tigers'],
    'Duke': ['Duke', 'Duke Blue Devils'],
    'Florida State': ['Florida State', 'Florida St.', 'Florida St', 'FSU', 'Florida State Seminoles'],
    'Georgia Tech': ['Georgia Tech', 'Georgia Tech Yellow Jackets', 'GT'],
    'Louisville': ['Louisville', 'Louisville Cardinals'],
    'Miami': ['Miami', 'Miami (FL)', 'Miami FL', 'Miami Hurricanes', 'The U'],
    'North Carolina': ['North Carolina', 'UNC', 'North Carolina Tar Heels', 'Tar Heels'],
    'NC State': ['NC State', 'N.C. State', 'North Carolina State', 'NC State Wolfpack', 'NCSU'],
    'Notre Dame': ['Notre Dame', 'Notre Dame Fighting Irish'],
    'Pittsburgh': ['Pittsburgh', 'Pitt', 'Pittsburgh Panthers'],
    'Syracuse': ['Syracuse', 'Syracuse Orange'],
    'Virginia': ['Virginia', 'UVA', 'Virginia Cavaliers'],
    'Virginia Tech': ['Virginia Tech', 'VT', 'Va Tech', 'Virginia Tech Hokies'],
    'Wake Forest': ['Wake Forest', 'Wake Forest Demon Deacons'],
    
    # Power 5 - Big Ten
    'Illinois': ['Illinois', 'Illinois Fighting Illini', 'Illini'],
    'Indiana': ['Indiana', 'Indiana Hoosiers', 'IU'],
    'Iowa': ['Iowa', 'Iowa Hawkeyes'],
    'Maryland': ['Maryland', 'Maryland Terrapins'],
    'Michigan': ['Michigan', 'Michigan Wolverines'],
    'Michigan State': ['Michigan State', 'Michigan St.', 'Michigan St', 'MSU', 'Michigan State Spartans'],
    'Minnesota': ['Minnesota', 'Minnesota Golden Gophers'],
    'Nebraska': ['Nebraska', 'Nebraska Cornhuskers'],
    'Northwestern': ['Northwestern', 'Northwestern Wildcats'],
    'Ohio State': ['Ohio State', 'Ohio St.', 'Ohio St', 'OSU', 'Ohio State Buckeyes'],
    'Penn State': ['Penn State', 'Penn St.', 'Penn St', 'PSU', 'Penn State Nittany Lions'],
    'Purdue': ['Purdue', 'Purdue Boilermakers'],
    'Rutgers': ['Rutgers', 'Rutgers Scarlet Knights'],
    'Wisconsin': ['Wisconsin', 'Wisconsin Badgers'],
    
    # Power 5 - Big 12
    'Baylor': ['Baylor', 'Baylor Bears'],
    'BYU': ['BYU', 'Brigham Young', 'Brigham Young Cougars'],
    'Cincinnati': ['Cincinnati', 'Cincinnati Bearcats'],
    'Houston': ['Houston', 'Houston Cougars'],
    'Iowa State': ['Iowa State', 'Iowa St.', 'Iowa St', 'Iowa State Cyclones'],
    'Kansas': ['Kansas', 'Kansas Jayhawks', 'KU'],
    'Kansas State': ['Kansas State', 'Kansas St.', 'Kansas St', 'K-State', 'Kansas State Wildcats'],
    'Oklahoma': ['Oklahoma', 'Oklahoma Sooners', 'OU'],
    'Oklahoma State': ['Oklahoma State', 'Oklahoma St.', 'Oklahoma St', 'OSU', 'Oklahoma State Cowboys'],
    'TCU': ['TCU', 'Texas Christian', 'TCU Horned Frogs'],
    'Texas': ['Texas', 'Texas Longhorns', 'UT'],
    'Texas Tech': ['Texas Tech', 'Texas Tech Red Raiders', 'TTU'],
    'UCF': ['UCF', 'Central Florida', 'UCF Knights'],
    'West Virginia': ['West Virginia', 'West Virginia Mountaineers', 'WVU'],
    
    # Power 5 - Pac-12
    'Arizona': ['Arizona', 'Arizona Wildcats'],
    'Arizona State': ['Arizona State', 'Arizona St.', 'Arizona St', 'ASU', 'Arizona State Sun Devils'],
    'California': ['California', 'Cal', 'Cal Berkeley', 'California Golden Bears'],
    'Colorado': ['Colorado', 'Colorado Buffaloes'],
    'Oregon': ['Oregon', 'Oregon Ducks'],
    'Oregon State': ['Oregon State', 'Oregon St.', 'Oregon St', 'OSU', 'Oregon State Beavers'],
    'Stanford': ['Stanford', 'Stanford Cardinal'],
    'UCLA': ['UCLA', 'UCLA Bruins'],
    'USC': ['USC', 'Southern California', 'Southern Cal', 'USC Trojans'],
    'Utah': ['Utah', 'Utah Utes'],
    'Washington': ['Washington', 'Washington Huskies', 'UW'],
    'Washington State': ['Washington State', 'Washington St.', 'Washington St', 'WSU', 'Washington State Cougars'],
    
    # Power 5 - SEC
    'Alabama': ['Alabama', 'Alabama Crimson Tide', 'Bama'],
    'Arkansas': ['Arkansas', 'Arkansas Razorbacks'],
    'Auburn': ['Auburn', 'Auburn Tigers'],
    'Florida': ['Florida', 'Florida Gators', 'UF'],
    'Georgia': ['Georgia', 'Georgia Bulldogs', 'UGA'],
    'Kentucky': ['Kentucky', 'Kentucky Wildcats', 'UK'],
    'LSU': ['LSU', 'Louisiana State', 'LSU Tigers'],
    'Mississippi': ['Mississippi', 'Ole Miss', 'Ole Miss Rebels'],
    'Mississippi State': ['Mississippi State', 'Mississippi St.', 'Mississippi St', 'MSU', 'Mississippi State Bulldogs'],
    'Missouri': ['Missouri', 'Missouri Tigers', 'Mizzou'],
    'South Carolina': ['South Carolina', 'South Carolina Gamecocks', 'USC'],
    'Tennessee': ['Tennessee', 'Tennessee Volunteers', 'Vols'],
    'Texas A&M': ['Texas A&M', 'Texas A&M Aggies', 'TAMU'],
    'Vanderbilt': ['Vanderbilt', 'Vanderbilt Commodores'],
    
    # Big East
    'Butler': ['Butler', 'Butler Bulldogs'],
    'Connecticut': ['Connecticut', 'UConn', 'UCONN', 'Connecticut Huskies'],
    'Creighton': ['Creighton', 'Creighton Bluejays'],
    'DePaul': ['DePaul', 'DePaul Blue Demons'],
    'Georgetown': ['Georgetown', 'Georgetown Hoyas'],
    'Marquette': ['Marquette', 'Marquette Golden Eagles'],
    'Providence': ['Providence', 'Providence Friars'],
    'Seton Hall': ['Seton Hall', 'Seton Hall Pirates'],
    'St. John\'s': ['St. John\'s', 'Saint John\'s', 'St John\'s', 'St. John\'s Red Storm'],
    'Villanova': ['Villanova', 'Villanova Wildcats'],
    'Xavier': ['Xavier', 'Xavier Musketeers'],
    
    # WCC
    'Gonzaga': ['Gonzaga', 'Gonzaga Bulldogs'],
    'Saint Mary\'s': ['Saint Mary\'s', 'St. Mary\'s', 'Saint Mary\'s Gaels'],
    'San Francisco': ['San Francisco', 'San Francisco Dons', 'USF'],
    'Santa Clara': ['Santa Clara', 'Santa Clara Broncos'],
    'Pepperdine': ['Pepperdine', 'Pepperdine Waves'],
    'Loyola Marymount': ['Loyola Marymount', 'LMU', 'Loyola Marymount Lions'],
    'Pacific': ['Pacific', 'Pacific Tigers'],
    'Portland': ['Portland', 'Portland Pilots'],
    'San Diego': ['San Diego', 'San Diego Toreros', 'USD'],
    
    # Mountain West
    'Boise State': ['Boise State', 'Boise St.', 'Boise St', 'Boise State Broncos'],
    'Colorado State': ['Colorado State', 'Colorado St.', 'Colorado St', 'CSU', 'Colorado State Rams'],
    'Fresno State': ['Fresno State', 'Fresno St.', 'Fresno St', 'Fresno State Bulldogs'],
    'Nevada': ['Nevada', 'Nevada Wolf Pack'],
    'New Mexico': ['New Mexico', 'New Mexico Lobos', 'UNM'],
    'San Diego State': ['San Diego State', 'San Diego St.', 'San Diego St', 'SDSU', 'San Diego State Aztecs'],
    'San Jose State': ['San Jose State', 'San Jose St.', 'San Jose St', 'SJSU', 'San Jose State Spartans'],
    'UNLV': ['UNLV', 'Nevada Las Vegas', 'UNLV Rebels'],
    'Utah State': ['Utah State', 'Utah St.', 'Utah St', 'USU', 'Utah State Aggies'],
    'Wyoming': ['Wyoming', 'Wyoming Cowboys'],
    
    # American Athletic
    'East Carolina': ['East Carolina', 'ECU', 'East Carolina Pirates'],
    'Memphis': ['Memphis', 'Memphis Tigers'],
    'SMU': ['SMU', 'Southern Methodist', 'SMU Mustangs'],
    'South Florida': ['South Florida', 'USF', 'South Florida Bulls'],
    'Temple': ['Temple', 'Temple Owls'],
    'Tulane': ['Tulane', 'Tulane Green Wave'],
    'Tulsa': ['Tulsa', 'Tulsa Golden Hurricane'],
    'Wichita State': ['Wichita State', 'Wichita St.', 'Wichita St', 'Wichita State Shockers'],
    
    # Atlantic 10
    'Davidson': ['Davidson', 'Davidson Wildcats'],
    'Dayton': ['Dayton', 'Dayton Flyers'],
    'Duquesne': ['Duquesne', 'Duquesne Dukes'],
    'Fordham': ['Fordham', 'Fordham Rams'],
    'George Mason': ['George Mason', 'George Mason Patriots', 'GMU'],
    'George Washington': ['George Washington', 'GW', 'George Washington Colonials'],
    'La Salle': ['La Salle', 'La Salle Explorers'],
    'UMass': ['UMass', 'Massachusetts', 'UMass Minutemen'],
    'Rhode Island': ['Rhode Island', 'Rhode Island Rams', 'URI'],
    'Richmond': ['Richmond', 'Richmond Spiders'],
    'Saint Joseph\'s': ['Saint Joseph\'s', 'St. Joseph\'s', 'Saint Joseph\'s Hawks'],
    'Saint Louis': ['Saint Louis', 'St. Louis', 'Saint Louis Billikens', 'SLU'],
    'VCU': ['VCU', 'Virginia Commonwealth', 'VCU Rams'],
    
    # Conference USA
    'Charlotte': ['Charlotte', 'Charlotte 49ers'],
    'FAU': ['FAU', 'Florida Atlantic', 'Florida Atlantic Owls'],
    'FIU': ['FIU', 'Florida International', 'Florida International Panthers'],
    'Louisiana Tech': ['Louisiana Tech', 'La Tech', 'Louisiana Tech Bulldogs'],
    'Marshall': ['Marshall', 'Marshall Thundering Herd'],
    'Middle Tennessee': ['Middle Tennessee', 'Middle Tennessee St.', 'MTSU', 'Middle Tennessee Blue Raiders'],
    'North Texas': ['North Texas', 'North Texas Mean Green', 'UNT'],
    'Old Dominion': ['Old Dominion', 'ODU', 'Old Dominion Monarchs'],
    'Rice': ['Rice', 'Rice Owls'],
    'UAB': ['UAB', 'Alabama Birmingham', 'UAB Blazers'],
    'UTEP': ['UTEP', 'Texas El Paso', 'UTEP Miners'],
    'UTSA': ['UTSA', 'UT San Antonio', 'UTSA Roadrunners'],
    'Western Kentucky': ['Western Kentucky', 'WKU', 'Western Kentucky Hilltoppers'],
    
    # MAC
    'Akron': ['Akron', 'Akron Zips'],
    'Ball State': ['Ball State', 'Ball St.', 'Ball St', 'Ball State Cardinals'],
    'Bowling Green': ['Bowling Green', 'BGSU', 'Bowling Green Falcons'],
    'Buffalo': ['Buffalo', 'Buffalo Bulls'],
    'Central Michigan': ['Central Michigan', 'Central Michigan Chippewas', 'CMU'],
    'Eastern Michigan': ['Eastern Michigan', 'Eastern Michigan Eagles', 'EMU'],
    'Kent State': ['Kent State', 'Kent St.', 'Kent St', 'Kent State Golden Flashes'],
    'Miami (OH)': ['Miami (OH)', 'Miami OH', 'Miami Ohio', 'Miami (Ohio)', 'Miami RedHawks'],
    'Northern Illinois': ['Northern Illinois', 'NIU', 'Northern Illinois Huskies'],
    'Ohio': ['Ohio', 'Ohio Bobcats'],
    'Toledo': ['Toledo', 'Toledo Rockets'],
    'Western Michigan': ['Western Michigan', 'Western Michigan Broncos', 'WMU'],
    
    # Sun Belt
    'Appalachian State': ['Appalachian State', 'Appalachian St.', 'App State', 'App St.', 'Appalachian State Mountaineers'],
    'Arkansas State': ['Arkansas State', 'Arkansas St.', 'Arkansas St', 'A-State', 'Arkansas State Red Wolves'],
    'Coastal Carolina': ['Coastal Carolina', 'Coastal Carolina Chanticleers', 'CCU'],
    'Georgia Southern': ['Georgia Southern', 'Georgia Southern Eagles'],
    'Georgia State': ['Georgia State', 'Georgia St.', 'Georgia St', 'Georgia State Panthers'],
    'James Madison': ['James Madison', 'JMU', 'James Madison Dukes'],
    'Louisiana': ['Louisiana', 'Louisiana Lafayette', 'UL Lafayette', 'Louisiana Ragin\' Cajuns'],
    'South Alabama': ['South Alabama', 'South Alabama Jaguars', 'USA'],
    'Southern Miss': ['Southern Miss', 'Southern Mississippi', 'USM', 'Southern Miss Golden Eagles'],
    'Texas State': ['Texas State', 'Texas St.', 'Texas St', 'Texas State Bobcats'],
    'Troy': ['Troy', 'Troy Trojans'],
    'ULM': ['ULM', 'Louisiana Monroe', 'UL Monroe', 'Louisiana Monroe Warhawks'],
    
    # More mid-majors and small conferences
    'Air Force': ['Air Force', 'Air Force Falcons'],
    'Army': ['Army', 'Army Black Knights'],
    'Navy': ['Navy', 'Navy Midshipmen'],
    'Bryant': ['Bryant', 'Bryant Bulldogs'],
    'Colgate': ['Colgate', 'Colgate Raiders'],
    'Cornell': ['Cornell', 'Cornell Big Red'],
    'Dartmouth': ['Dartmouth', 'Dartmouth Big Green'],
    'Harvard': ['Harvard', 'Harvard Crimson'],
    'Penn': ['Penn', 'Pennsylvania', 'Penn Quakers'],
    'Princeton': ['Princeton', 'Princeton Tigers'],
    'Yale': ['Yale', 'Yale Bulldogs'],
    'Charleston': ['Charleston', 'College of Charleston', 'Charleston Cougars', 'CofC'],
    'Drexel': ['Drexel', 'Drexel Dragons'],
    'Hofstra': ['Hofstra', 'Hofstra Pride'],
    'Delaware': ['Delaware', 'Delaware Fightin\' Blue Hens'],
    'Towson': ['Towson', 'Towson Tigers'],
    'UNC Wilmington': ['UNC Wilmington', 'UNCW', 'UNC Wilmington Seahawks'],
    'William & Mary': ['William & Mary', 'William and Mary', 'William & Mary Tribe'],
    'Drake': ['Drake', 'Drake Bulldogs'],
    'Illinois State': ['Illinois State', 'Illinois St.', 'Illinois St', 'ISU', 'Illinois State Redbirds'],
    'Indiana State': ['Indiana State', 'Indiana St.', 'Indiana St', 'ISU', 'Indiana State Sycamores'],
    'Loyola Chicago': ['Loyola Chicago', 'Loyola', 'Loyola-Chicago', 'Loyola (IL)', 'Loyola Chicago Ramblers'],
    'Missouri State': ['Missouri State', 'Missouri St.', 'Missouri St', 'Missouri State Bears'],
    'Murray State': ['Murray State', 'Murray St.', 'Murray St', 'Murray State Racers'],
    'Northern Iowa': ['Northern Iowa', 'UNI', 'Northern Iowa Panthers'],
    'Southern Illinois': ['Southern Illinois', 'SIU', 'Southern Illinois Salukis'],
    'Valparaiso': ['Valparaiso', 'Valpo', 'Valparaiso Beacons'],
    'Bradley': ['Bradley', 'Bradley Braves'],
    'Belmont': ['Belmont', 'Belmont Bruins'],
    'Liberty': ['Liberty', 'Liberty Flames'],
    'Lipscomb': ['Lipscomb', 'Lipscomb Bisons'],
    'North Florida': ['North Florida', 'UNF', 'North Florida Ospreys'],
    'Stetson': ['Stetson', 'Stetson Hatters'],
    'Vermont': ['Vermont', 'Vermont Catamounts'],
    'Albany': ['Albany', 'UAlbany', 'Albany Great Danes'],
    'Binghamton': ['Binghamton', 'Binghamton Bearcats'],
    'Maine': ['Maine', 'Maine Black Bears'],
    'New Hampshire': ['New Hampshire', 'UNH', 'New Hampshire Wildcats'],
    'Stony Brook': ['Stony Brook', 'Stony Brook Seawolves'],
    'UMass Lowell': ['UMass Lowell', 'UMass-Lowell', 'UMass Lowell River Hawks'],
    'UMBC': ['UMBC', 'Maryland Baltimore County', 'UMBC Retrievers'],
    'UC Irvine': ['UC Irvine', 'UCI', 'UC Irvine Anteaters'],
    'UC Davis': ['UC Davis', 'UCD', 'UC Davis Aggies'],
    'UC Riverside': ['UC Riverside', 'UCR', 'UC Riverside Highlanders'],
    'UC Santa Barbara': ['UC Santa Barbara', 'UCSB', 'UC Santa Barbara Gauchos'],
    'UC San Diego': ['UC San Diego', 'UCSD', 'UC San Diego Tritons'],
    'Cal Poly': ['Cal Poly', 'Cal Poly Mustangs'],
    'Long Beach State': ['Long Beach State', 'Long Beach St.', 'Long Beach St', 'LBSU', 'Long Beach State Beach'],
    'CSU Bakersfield': ['CSU Bakersfield', 'Cal St. Bakersfield', 'Cal State Bakersfield', 'CSUB'],
    'CSU Fullerton': ['CSU Fullerton', 'Cal St. Fullerton', 'Cal State Fullerton', 'CSUF'],
    'CSU Northridge': ['CSU Northridge', 'Cal St. Northridge', 'Cal State Northridge', 'CSUN'],
    'Hawaii': ['Hawaii', 'Hawai\'i', 'Hawaii Rainbow Warriors'],
    'Grand Canyon': ['Grand Canyon', 'GCU', 'Grand Canyon Antelopes'],
    'Seattle': ['Seattle', 'Seattle U', 'Seattle Redhawks'],
    'Northern Colorado': ['Northern Colorado', 'UNC', 'Northern Colorado Bears'],
    'North Dakota': ['North Dakota', 'UND', 'North Dakota Fighting Hawks'],
    'North Dakota State': ['North Dakota State', 'North Dakota St.', 'NDSU', 'North Dakota State Bison'],
    'South Dakota': ['South Dakota', 'South Dakota Coyotes', 'USD'],
    'South Dakota State': ['South Dakota State', 'South Dakota St.', 'SDSU', 'South Dakota State Jackrabbits'],
    'Oral Roberts': ['Oral Roberts', 'ORU', 'Oral Roberts Golden Eagles'],
    'Denver': ['Denver', 'Denver Pioneers'],
    'Omaha': ['Omaha', 'Nebraska Omaha', 'UNO', 'Omaha Mavericks'],
    'Western Illinois': ['Western Illinois', 'Western Illinois Leathernecks', 'WIU'],
    'Southern Utah': ['Southern Utah', 'SUU', 'Southern Utah Thunderbirds'],
    'Weber State': ['Weber State', 'Weber St.', 'Weber St', 'Weber State Wildcats'],
    'Idaho': ['Idaho', 'Idaho Vandals'],
    'Idaho State': ['Idaho State', 'Idaho St.', 'Idaho St', 'ISU', 'Idaho State Bengals'],
    'Montana': ['Montana', 'Montana Grizzlies'],
    'Montana State': ['Montana State', 'Montana St.', 'Montana St', 'MSU', 'Montana State Bobcats'],
    'Eastern Washington': ['Eastern Washington', 'Eastern Washington Eagles', 'EWU'],
    'Portland State': ['Portland State', 'Portland St.', 'Portland St', 'PSU', 'Portland State Vikings'],
    'Sacramento State': ['Sacramento State', 'Sacramento St.', 'Sac State', 'CSUS'],
    'Northern Arizona': ['Northern Arizona', 'NAU', 'Northern Arizona Lumberjacks'],
}


def normalize_team_name(team: str) -> str:
    """
    Normalize any team name to its canonical form.
    CRITICAL: Strips ESPN-style mascots before database lookup.
    
    Examples:
        "Duke Blue Devils" → "Duke"
        "North Carolina Tar Heels" → "North Carolina"
        "Houston Cougars" → "Houston"
    
    Args:
        team: Team name in any format
        
    Returns:
        Canonical team name
    """
    team = team.strip()
    
    # Step 1: Strip ESPN-style mascots (School + Mascot format)
    # This is the KEY FIX - ESPN returns "Duke Blue Devils", we need "Duke"
    mascots = [
        'Aggies', 'Aztecs', 'Badgers', 'Bears', 'Bearcats', 'Beavers', 'Bengals',
        'Billikens', 'Bison', 'Blazers', 'Blue Devils', 'Blue Jays', 'Bluejays',
        'Bobcats', 'Boilermakers', 'Bonnies', 'Braves', 'Broncos', 'Bruins',
        'Buckeyes', 'Buffaloes', 'Bulls', 'Bulldogs', 'Camels', 'Cardinals',
        'Catamounts', 'Cavaliers', 'Chanticleers', 'Chippewas', 'Colonials',
        'Commodores', 'Cornhuskers', 'Cougars', 'Cowboys', 'Crimson', 'Crusaders',
        'Cyclones', 'Demons', 'Demon Deacons', 'Devils', 'Dolphins', 'Dons',
        'Dragons', 'Ducks', 'Dukes', 'Eagles', 'Explorers', 'Falcons', 'Fightin Illini',
        'Fighting Illini', 'Fighting Irish', 'Flames', 'Flyers', 'Friars',
        'Gamecocks', 'Gators', 'Gaels', 'Greyhounds', 'Golden Bears', 'Golden Eagles',
        'Golden Gophers', 'Golden Hurricane', 'Gophers', 'Green Wave', 'Grizzlies',
        'Hawkeyes', 'Highlanders', 'Hilltoppers', 'Hokies', 'Hoosiers', 'Horned Frogs',
        'Huskies', 'Hurricanes', 'Indians', 'Jaguars', 'Jayhawks', 'Jets',
        'Knights', 'Lancers', 'Lions', 'Lumberjacks', 'Mastodons', 'Matadors',
        'Mavericks', 'Mean Green', 'Midshipmen', 'Miners', 'Minutemen', 'Monarchs',
        'Mountaineers', 'Musketeers', 'Mustangs', 'Nittany Lions', 'Orange',
        'Orangemen', 'Owls', 'Panthers', 'Patriots', 'Peacocks', 'Penguins',
        'Phoenix', 'Pirates', 'Racers', 'Raiders', 'Rainbow Warriors', 'Rams',
        'Razorbacks', 'Rebels', 'Redbirds', 'Red Flash', 'Red Raiders', 'Red Storm',
        'Retrievers', 'Roos', 'Running Rebels', 'Salukis', 'Scarlet Knights',
        'Seminoles', 'Seawolves', 'Seahawks', 'Shockers', 'Sooners', 'Spartans',
        'Spiders', 'Sun Devils', 'Sycamores', 'Tar Heels', 'Terrapins', 'Terriers',
        'Thundering Herd', 'Tigers', 'Titans', 'Toreros', 'Trojans', 'Utes',
        'Vandals', 'Vikings', 'Volunteers', 'Warriors', 'Waves', 'Wildcats',
        'Wolf Pack', 'Wolfpack', 'Wolverines', 'Yellow Jackets', 'Zips',
        '49ers', 'Anteaters', 'Roadrunners', 'Tritons', 'Gauchos', 'Cardinal',
    ]
    
    # Remove mascot if found at end (case-insensitive)
    team_lower = team.lower()
    for mascot in mascots:
        mascot_lower = mascot.lower()
        if team_lower.endswith(f' {mascot_lower}'):
            # Strip the mascot, keeping the school name
            team = team[:-(len(mascot)+1)].strip()
            break
    
    # Step 2: Search through database with original and stripped version
    for canonical_name, variations in TEAM_DATABASE.items():
        if team in variations:
            return canonical_name
        # Case-insensitive match
        if team.lower() in [v.lower() for v in variations]:
            return canonical_name
    
    # If not found, return stripped version (better than full ESPN name)
    return team


def get_team_variations(canonical_name: str) -> list:
    """Get all variations of a team name"""
    return TEAM_DATABASE.get(canonical_name, [canonical_name])


def search_team(query: str) -> list:
    """
    Search for teams matching a query.
    
    Args:
        query: Search string
        
    Returns:
        List of (canonical_name, variations) tuples
    """
    query_lower = query.lower()
    matches = []
    
    for canonical, variations in TEAM_DATABASE.items():
        if query_lower in canonical.lower():
            matches.append((canonical, variations))
        elif any(query_lower in v.lower() for v in variations):
            matches.append((canonical, variations))
    
    return matches
