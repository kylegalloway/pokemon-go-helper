import sqlite3
import json
from flask import Flask, render_template, request, jsonify
import pokebase as pb
import math
import threading
import os
from contextlib import contextmanager
from move_to_db import (
    POKEMON_GO_AVAILABLE,
    LEGENDARY_POKEMON,
    MEGA_POKEMON,
    SHADOW_POKEMON,
    DMAX_POKEMON,
    GMAX_POKEMON,
    TYPE_CHART,
)

app = Flask(__name__)

# Database configuration
DATABASE_PATH = "pokemon_go.db"

# Configure pokebase caching for better performance
# pokebase automatically caches API responses to avoid repeated requests
from pokebase import cache

cache.API_CACHE

# Global variables for Pokemon list
pokemon_list_cache = None
pokemon_stats_cache = {}
pokemon_count = 0


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize the SQLite database with required tables"""
    print("DEBUG: Initializing database...")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create pokemon table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER NOT NULL,
                name TEXT NOT NULL,
                form TEXT NOT NULL, -- New column to store 'normal', 'mega', 'shadow', 'max', etc.
                type1 TEXT NOT NULL,
                type2 TEXT,
                base_hp INTEGER NOT NULL,
                base_attack INTEGER NOT NULL,
                base_defense INTEGER NOT NULL,
                base_sp_attack INTEGER NOT NULL,
                base_sp_defense INTEGER NOT NULL,
                base_speed INTEGER NOT NULL,
                pogo_attack INTEGER NOT NULL,
                pogo_defense INTEGER NOT NULL,
                pogo_stamina INTEGER NOT NULL,
                is_in_go BOOLEAN NOT NULL DEFAULT 0,
                is_legendary BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, form) -- Composite primary key
            );
        """
        )

        # Create index for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pokemon_id ON pokemon(id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pokemon_name ON pokemon(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pokemon_type1 ON pokemon(type1)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pokemon_type2 ON pokemon(type2)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pokemon_in_go ON pokemon(is_in_go)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pokemon_legendary ON pokemon(is_legendary)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pokemon_pogo_attack ON pokemon(pogo_attack)"
        )

        # Create a metadata table to track database version and updates
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        print("DEBUG: Database initialized successfully")


def is_pokemon_in_go(pokemon_id):
    """Check if Pokemon is available in Pokemon GO"""
    return pokemon_id in POKEMON_GO_AVAILABLE


def is_legendary(pokemon_id):
    """Check if Pokemon is Legendary/Mythical/Ultra Beast"""
    return pokemon_id in LEGENDARY_POKEMON


def has_mega(pokemon_id):
    """Check if Pokemon has Mega Evolution in Pokemon GO"""
    return pokemon_id in MEGA_POKEMON


def has_shadow(pokemon_id):
    """Check if Pokemon can be Shadow in Pokemon GO"""
    return pokemon_id in SHADOW_POKEMON


def has_max(pokemon_id):
    """Check if Pokemon can be Max in Pokemon GO"""
    return (pokemon_id in DMAX_POKEMON) or (pokemon_id in GMAX_POKEMON)


def get_pokemon_id_list(limit=None):
    """Get list of Pokemon IDs, optionally limited"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pokemon WHERE is_in_go = 1")
        all_pokemon = cursor.fetchall()

        ids = [p["id"] for p in all_pokemon]

        if limit:
            ids = ids[:limit]
            print(f"DEBUG: Returning {len(ids)} Pokemon IDs (limited)")
        else:
            print(f"DEBUG: Returning all {len(ids)} Pokemon IDs")

        return ids


def convert_to_pogo_stats(base_stats, is_shadow=False):
    """Convert base stats to Pokemon Go format using official formulas"""
    try:
        # print(f"DEBUG: Converting stats for Pokemon with base_stats: {base_stats}")

        # Get individual stats
        attack = base_stats["attack"]
        defense = base_stats["defense"]
        sp_attack = base_stats["special-attack"]
        sp_defense = base_stats["special-defense"]
        hp = base_stats["hp"]
        speed = base_stats["speed"]

        # print(f"DEBUG: Individual stats - ATK: {attack}, DEF: {defense}, SP_ATK: {sp_attack}, SP_DEF: {sp_defense}, HP: {hp}, SPD: {speed}")

        # Speed scaling factor (used in all calculations)
        speed_mod = 1 + (speed - 75) / 500
        # print(f"DEBUG: Speed modifier: {speed_mod}")

        # Attack: 2 * (7/8 * higher_attack + 1/8 * lower_attack) * speed_mod
        higher_attack = max(attack, sp_attack)
        lower_attack = min(attack, sp_attack)
        pogo_attack_raw = 2 * (7 / 8 * higher_attack + 1 / 8 * lower_attack) * speed_mod
        # print(f"DEBUG: Attack calc - Higher: {higher_attack}, Lower: {lower_attack}, Raw: {pogo_attack_raw}")

        # Defense: 2 * (5/8 * higher_defense + 3/8 * lower_defense) * speed_mod
        higher_defense = max(defense, sp_defense)
        lower_defense = min(defense, sp_defense)
        pogo_defense_raw = (
            2 * (5 / 8 * higher_defense + 3 / 8 * lower_defense) * speed_mod
        )
        # print(f"DEBUG: Defense calc - Higher: {higher_defense}, Lower: {lower_defense}, Raw: {pogo_defense_raw}")

        # Stamina: 50 + (1.75 * HP)
        pogo_stamina_raw = 50 + (1.75 * hp)
        # print(f"DEBUG: Stamina calc - Raw: {pogo_stamina_raw}")

        # Round and apply minimums
        result = {
            "attack": max(round(pogo_attack_raw), 10),
            "defense": max(round(pogo_defense_raw), 10),
            "stamina": max(round(pogo_stamina_raw), 10),
        }

        # print(f"DEBUG: Final Pokemon GO stats: {result}")
        return result

    except Exception as e:
        print(f"ERROR in convert_to_pogo_stats: {e}")
        print(f"ERROR: base_stats was: {base_stats}")
        # Return default values to prevent crash
        return {"attack": 10, "defense": 10, "stamina": 10}


def fetch_and_store_pokemon_data(pokemon_id):
    """Fetch Pokemon data from API and store in database"""
    try:
        print(f"DEBUG: Fetching Pokemon data for ID: {pokemon_id}")
                
        # Get base form data
        base_data = pb.pokemon(pokemon_id)
        
        # Determine all forms to process
        forms_to_process = [
            {'form_name': 'normal', 'is_mega': False, 'is_shadow': False, 'is_max': False}
        ]
        
        if pokemon_id in MEGA_POKEMON:
            forms_to_process.append({'form_name': 'mega', 'is_mega': True, 'is_shadow': False, 'is_max': False})
        if pokemon_id in SHADOW_POKEMON:
            forms_to_process.append({'form_name': 'shadow', 'is_mega': False, 'is_shadow': True, 'is_max': False})
        if pokemon_id in DMAX_POKEMON or pokemon_id in GMAX_POKEMON:
            forms_to_process.append({'form_name': 'max', 'is_mega': False, 'is_shadow': False, 'is_max': True})

        # Update name for clarity
        full_name = f"{base_data.name.title()}" if form_name == "normal" else f"{base_data.name.title()} ({form_name.title()})"

        for form_info in forms_to_process:
            form_name = form_info['form_name']
            

            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Check if this specific form already exists to avoid duplicates
                cursor.execute("SELECT COUNT(*) FROM pokemon WHERE id = ? AND form = ?", (pokemon_id, form_name))
                db_count = cursor.fetchone()[0]
            if db_count > 0:
                continue

            # Calculate stats and apply bonuses for the specific form
            base_stats = {s.stat.name: s.base_stat for s in base_data.stats}
            pogo_stats = convert_to_pogo_stats(base_stats)
            
            # Apply form-specific bonuses
            if form_name == 'mega':
                pogo_stats['attack'] = math.ceil(pogo_stats['attack'] * 1.3)
            elif form_name == 'shadow':
                pogo_stats['attack'] = math.ceil(pogo_stats['attack'] * 1.2)
            elif form_name == 'max':
                pogo_stats['attack'] = math.ceil(pogo_stats['attack'] * 1.1)

            # Insert into the database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO pokemon (
                        id, name, form, type1, type2, 
                        base_hp, base_attack, base_defense, base_sp_attack, base_sp_defense, base_speed,
                        pogo_attack, pogo_defense, pogo_stamina,
                        is_in_go, is_legendary,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        base_data.id,
                        full_name,
                        form_name,
                        base_data.types[0].type.name if len(base_data.types) > 0 else 'normal',
                        base_data.types[1].type.name if len(base_data.types) > 1 else None,
                        base_stats["hp"], base_stats["attack"], base_stats["defense"],
                        base_stats["special-attack"], base_stats["special-defense"], base_stats["speed"],
                        pogo_stats["attack"], pogo_stats["defense"], pogo_stats["stamina"],
                        is_pokemon_in_go(base_data.id),
                        is_legendary(base_data.id),
                    ),
                )
                conn.commit()

        print(f"DEBUG: Successfully stored {full_name}) in database")
        return True

    except Exception as e:
        print(f"ERROR fetching Pokemon {pokemon_id}: {e}")
        return False


def get_pokemon_data_from_db(pokemon_id, form):
    """Get Pokemon data from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pokemon WHERE id = ? AND form = ?", (pokemon_id, form))
        row = cursor.fetchone()

        if row:
            types = [row["type1"]]
            if row["type2"]:
                types.append(row["type2"])

            return {
                "name": row["name"],
                "id": row["id"],
                "form": row["form"],
                "types": types,
                "base_stats": {
                    "hp": row["base_hp"],
                    "attack": row["base_attack"],
                    "defense": row["base_defense"],
                    "special-attack": row["base_sp_attack"],
                    "special-defense": row["base_sp_defense"],
                    "speed": row["base_speed"],
                },
                "pogo_stats": {
                    "attack": row["pogo_attack"],
                    "defense": row["pogo_defense"],
                    "stamina": row["pogo_stamina"],
                },
                "is_in_go": bool(row["is_in_go"]),
                "is_legendary": bool(row["is_legendary"])
            }
        return None


def get_pokemon_data(pokemon_id, form):
    """Get Pokemon data - first try database, then API if not found"""
    # Try database first
    data = get_pokemon_data_from_db(pokemon_id, form)
    if data:
        return data

    # If not in database, fetch from API and store
    if fetch_and_store_pokemon_data(pokemon_id):
        return get_pokemon_data_from_db(pokemon_id, form)

    return None


def should_include_pokemon_db(row, filters):
    """
    Checks if a database row (which is a specific Pokemon form)
    should be included based on the filters.
    """
    if not row["is_in_go"]:
        return False

    # Legendary filter
    legendary_filter = filters.get("legendary_filter", "all")
    if legendary_filter == "only" and not row["is_legendary"]:
        return False
    elif legendary_filter == "exclude" and row["is_legendary"]:
        return False

    # Form filters check the 'form' column, not flags
    mega_filter = filters.get("mega_filter", "all")
    if mega_filter == "only" and row["form"] != "mega":
        return False
    elif mega_filter == "exclude" and row["form"] == "mega":
        return False

    shadow_filter = filters.get("shadow_filter", "all")
    if shadow_filter == "only" and row["form"] != "shadow":
        return False
    elif shadow_filter == "exclude" and row["form"] == "shadow":
        return False

    max_filter = filters.get("max_filter", "all")
    if max_filter == "only" and row["form"] != "max":
        return False
    elif max_filter == "exclude" and row["form"] == "max":
        return False

    return True


def calculate_type_effectiveness(attacker_types, defender_types):
    """Calculate type effectiveness multiplier"""
    effectiveness = 1.0

    for att_type in attacker_types:
        type_mult = 1.0
        for def_type in defender_types:
            if att_type in TYPE_CHART and def_type in TYPE_CHART[att_type]:
                type_mult *= TYPE_CHART[att_type][def_type]
        if type_mult > effectiveness:
            effectiveness = type_mult

    return effectiveness


def populate_database():
    """Populate database with Pokemon data from the API"""
    print("DEBUG: Starting database population...")

    try:
        # Get Pokemon list from API
        print("DEBUG: Fetching Pokemon list from API...")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pokemon")
            count = cursor.fetchone()[0]

            pokemon_resource_list = pb.APIResourceList("pokemon")

            total_pokemon = min(
                pokemon_resource_list.count, 1010
            )  # Limit to reasonable range
            print(f"DEBUG: Will populate {total_pokemon} Pokemon...")

            # Check if database is already populated

            if count >= total_pokemon:
                print(f"DEBUG: Database already contains {count} Pokemon. Skipping population.")
                return

            success_count = 0

            for i, pokemon_ref in enumerate(pokemon_resource_list):
                if i > total_pokemon: # Limit total of pokemon that are processed
                    break

                if (i + 1) % 50 == 0:  # Progress every 50
                    print(
                        f"DEBUG: Populated {i + 1}/{total_pokemon} Pokemon... ({success_count} successful)"
                    )

                # Extract ID from URL
                pokemon_id = int(pokemon_ref["url"].strip("/").split("/")[-1])

                # Skip if pokemon is already in the DB
                cursor.execute("SELECT COUNT(*) FROM pokemon WHERE id = ?", (pokemon_id,))
                db_count = cursor.fetchone()[0]
                if db_count > 0:
                    success_count += 1
                    continue
                
                # If not skipping, pull data and store
                if fetch_and_store_pokemon_data(pokemon_id):
                    success_count += 1

            print(
                f"DEBUG: Database population completed! {success_count}/{total_pokemon} Pokemon stored successfully."
            )

            # Update metadata
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                ("last_populated", f"{success_count} Pokemon"),
            )
            conn.commit()

    except Exception as e:
        print(f"ERROR during database population: {e}")
        import traceback

        print(f"ERROR: Full traceback: {traceback.format_exc()}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/pokemon/<int:pokemon_id>/<form>")
def get_pokemon_stats(pokemon_id, form):
    """Get Pokemon Go stats for a specific Pokemon"""
    form = form.lower()
    try:
        data = get_pokemon_data(pokemon_id, form)
        if data:
            return jsonify(data)
        else:
            return jsonify({"error": "Pokemon not found"}), 404
    except Exception as e:
        print(f"ERROR in get_pokemon_stats: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/top-attackers/<int:defender_id>/<form>")
def get_top_attackers(defender_id, form):
    """Get top 25 attackers against a specific Pokemon using database"""
    form = form.lower()
    print(f"DEBUG: Finding top attackers against Pokemon ID: {defender_id}, Form: {form}")

    filters = {
        "legendary_filter": request.args.get("legendary_filter", "all"),
        "mega_filter": request.args.get("mega_filter", "all"),
        "shadow_filter": request.args.get("shadow_filter", "all"),
        "max_filter": request.args.get("max_filter", "all"),
    }

    try:
        defender = get_pokemon_data(defender_id, form)
        if not defender:
            return jsonify({"error": "Defender Pokemon not found"}), 404
        
        attackers = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pokemon WHERE is_in_go = 1")
            
            for row in cursor.fetchall():
                if not should_include_pokemon_db(row, filters):
                    continue
                    
                # No more multipliers needed, they are pre-calculated in the DB
                pogo_attack = row["pogo_attack"]
                attacker_types = [row["type1"]]
                if row["type2"]:
                    attacker_types.append(row["type2"])
                    
                effectiveness = calculate_type_effectiveness(attacker_types, defender["types"])
                effective_attack = pogo_attack * effectiveness
                
                # ... append to attackers list ...
                attackers.append({
                    "name": row["name"],
                    "id": row["id"],
                    "form": row["form"],
                    "types": attacker_types,
                    "attack": pogo_attack,
                    "effectiveness": round(effectiveness, 2),
                    "effective_attack": round(effective_attack, 1),
                    "is_legendary": bool(row["is_legendary"]),
                })

        # Sort by effective attack and return top 25
        attackers.sort(key=lambda x: x["effective_attack"], reverse=True)
        top_25 = attackers[:25]

        print(f"DEBUG: Found {len(attackers)} valid attackers")
        print(f"DEBUG: Top attacker is {top_25[0]['name'] if top_25 else 'None'}")

        return jsonify(
            {
                "defender": defender["name"],
                "top_attackers": top_25,
                "filters_applied": filters,
                "total_candidates": len(attackers),
            }
        )

    except Exception as e:
        print(f"ERROR in get_top_attackers: {e}")
        import traceback

        print(f"ERROR: Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/top-attackers-by-type/<type_name>")
def get_top_attackers_by_type(type_name):
    """Get top 25 attackers of a specific type using database"""
    type_name = type_name.lower()
    print(f"DEBUG: Finding top {type_name} type attackers")

    filters = {
        "legendary_filter": request.args.get("legendary_filter", "all"),
        "mega_filter": request.args.get("mega_filter", "all"),
        "shadow_filter": request.args.get("shadow_filter", "all"),
        "max_filter": request.args.get("max_filter", "all"),
    }

    try:
        attackers = []

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM pokemon WHERE is_in_go = 1 AND (type1 = ? OR type2 = ?)",
                (type_name, type_name),
            )

            for row in cursor.fetchall():
                if not should_include_pokemon_db(row, filters):
                    continue

                attacker_types = [row["type1"]]
                if row["type2"]:
                    attacker_types.append(row["type2"])
                
                attackers.append({
                    "name": row["name"],
                    "id": row["id"],
                    "form": row["form"],
                    "types": attacker_types,
                    "attack": row["pogo_attack"],
                    "is_legendary": bool(row["is_legendary"]),
                })

        # Sort by attack and return top 25
        attackers.sort(key=lambda x: x["attack"], reverse=True)
        top_25 = attackers[:25]

        print(f"DEBUG: Found {len(attackers)} {type_name} type Pokemon")

        return jsonify(
            {
                "type": type_name.title(),
                "top_attackers": top_25,
                "filters_applied": filters,
                "total_candidates": len(attackers),
            }
        )

    except Exception as e:
        print(f"ERROR in get_top_attackers_by_type: {e}")
        import traceback

        print(f"ERROR: Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/pokemon-list")
def get_pokemon_list():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Fetch all Pokemon and their forms
            cursor.execute("SELECT id, name, form FROM pokemon WHERE is_in_go = 1 ORDER BY id, form")
            all_pokemon = cursor.fetchall()

            dropdown_list = []
            for pokemon in all_pokemon:
                dropdown_list.append({
                    "id": pokemon["id"],
                    "name": pokemon["name"],
                    "form": pokemon["form"]
                })
            
            # You might want to format the name for the dropdown, e.g., "Gengar (Shadow)"
            formatted_list = [
                {"id": f"{p['id']}", "name": f"{p['name']}", "form": f" {p['form']}"} for p in dropdown_list
            ]
            
            return jsonify(formatted_list)

    except Exception as e:
        print(f"ERROR in get_pokemon_list: {e}")
        import traceback

        print(f"ERROR: Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


def create_app():
    """Application factory function"""
    app = Flask(__name__)
    init_database()

    # Warm up the cache in the background for better performance
    import threading

    thread = threading.Thread(target=populate_database)
    thread.daemon = True
    thread.start()

    return app


@app.route("/api/types")
def get_types():
    """Get list of all Pokemon types"""
    types = [
        "normal",
        "fire",
        "water",
        "electric",
        "grass",
        "ice",
        "fighting",
        "poison",
        "ground",
        "flying",
        "psychic",
        "bug",
        "rock",
        "ghost",
        "dragon",
        "dark",
        "steel",
        "fairy",
    ]
    return jsonify([{"name": t.title(), "value": t} for t in types])

# @app.route("/admin/cleardb")
# def clear_table():
#     """
#     Deletes all records from a specified table in an SQLite database.
#     """
#     try:
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(f"DELETE FROM pokemon")
#             conn.commit()
#         print(f"All records cleared from table 'pokemon' in '{DATABASE_PATH}'.")
#     except sqlite3.Error as e:
#         print(f"Error clearing table: {e}")
#     finally:
#         if conn:
#             conn.close()


if __name__ == "__main__":
    print("DEBUG: Starting Flask application...")

    # Load Pokemon list first
    print("DEBUG: Loading Pokemon list...")
    init_database()

    # Start cache warming in background when app starts
    import threading

    cache_thread = threading.Thread(target=populate_database)
    cache_thread.daemon = True
    cache_thread.start()
    print("DEBUG: Cache warming thread started")

    print("DEBUG: Starting Flask server...")
    app.run(debug=True)
