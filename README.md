# Pokemon Go Stats Flask App

## Setup Instructions

1. **Move into the root of the project:**
   ```bash
   cd pokemon-go-helper
   ```

1. **Create a virtual environment:**
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

1. **Run the application:**
   ```bash
   python app.py
   ```

1. **Open your browser and go to:**
   ```
   http://127.0.0.1:5000
   ```

## Features

### 1. Pokemon Go Stats Conversion
- **Input:** Dropdown with first 151 Pokemon
- **Output:** Converts base stats to Pokemon Go format using the official updated formulas:
  - Speed Modifier = 1 + (Speed - 75) / 500
  - Attack = 2 × (7/8 × higher_attack + 1/8 × lower_attack) × speed_mod
  - Defense = 2 × (5/8 × higher_defense + 3/8 × lower_defense) × speed_mod
  - Stamina = 50 + (1.75 × Base HP)
- **Display:** Shows both Pokemon Go stats and original base stats
- **Accuracy:** Uses the current Pokemon GO stat conversion system that favors specialized attackers

### 2. Top 25 Attackers vs Specific Pokemon
- **Input:** Dropdown to select a defender Pokemon, Filters for Legendary, Shadow, Mega, Max inclusion/disclusion
- **Calculation:**
  - Calculates type effectiveness multipliers using Pokemon Go's type chart
  - Computes effective attack = base attack × type effectiveness
  - Ranks all Pokemon by effective attack power
- **Output:** Top 25 attackers with their stats, type effectiveness, and effective attack values

### 3. Top 25 Attackers by Type
- **Input:** Dropdown with all 18 Pokemon types, Filters for Legendary, Shadow, Mega, Max inclusion/disclusion
- **Output:** Top 25 Pokemon of the selected type ranked by their Pokemon Go attack stat
- **Display:** Shows Pokemon name, types, and attack value

## Key Technical Features

### Pokemon Go Stat Conversion
The app uses the actual Pokemon Go stat conversion formulas to translate main series stats into Pokemon Go format. This provides accurate representations of how Pokemon perform in Pokemon Go.

### Type Effectiveness System
Implements Pokemon Go's type effectiveness chart with precise multipliers:
- Super Effective: 1.6x damage
- Not Very Effective: 0.625x damage
- Double resistance: 0.390625x damage (0.625²)

### Caching System
Uses pokebase's built-in caching system to automatically cache API responses:
- **Automatic Caching:** pokebase automatically caches all API responses to disk
- **Persistent Cache:** Cache persists between app restarts
- **Cache Warming:** App pre-loads Generation 1 Pokemon data on startup for faster initial responses
- **No Manual Cache Management:** pokebase handles cache invalidation and storage automatically

### Database Storage
Stores pokemon data (including calculated values) in a small local SQLite database for faster queries.

### Responsive Design
Modern, mobile-friendly interface with:
- Tabbed navigation
- Dropdown selectors for easy input
- Color-coded type badges
- Loading animations
- Grid layouts for optimal viewing

### Error Handling
Robust error handling for:
- API failures
- Invalid Pokemon IDs
- Network issues
- Missing data

## API Endpoints

The app provides several REST API endpoints:

- `GET /api/pokemon/<id>` - Get Pokemon Go stats for specific Pokemon
- `GET /api/top-attackers/<id>` - Get top attackers vs defender Pokemon
- `GET /api/top-attackers-by-type/<type>` - Get top attackers of specific type
- `GET /api/pokemon-list` - Get list of available Pokemon
- `GET /api/types` - Get list of Pokemon types

## Data Coverage

- **Pokemon Coverage:** First 1010 Pokemon (covers all generations available in Pokemon Go)
- **Type Coverage:** All 18 Pokemon types
- **Stat Calculations:** Accurate Pokemon Go formulas
- **Type Chart:** Complete Pokemon Go type effectiveness system

## Performance Notes

- **First Run:** Initial load may be slower as Pokemon data is fetched and cached by pokebase
- **Subsequent Runs:** Much faster as pokebase uses persistent disk caching
- **Cache Warming:** App automatically preloads Generation 1 Pokemon on startup
- **Automatic Cache Management:** pokebase handles all caching - no manual intervention needed
- The app checks 1010 Pokemon for rankings, cached data makes this much faster
- Cache persists between app restarts for optimal performance

## Potential Enhancements

1. **More Pokemon Specifics:** Filters need more corrections, especially Shadow/Max/Mega availability
1. **Move Analysis:** Add move effectiveness calculations
1. **CP Calculations:** Include Combat Power calculations
1. **Favorites System:** Allow users to save favorite Pokemon
1. **Battle Simulations:** Implement damage calculations and battle outcomes