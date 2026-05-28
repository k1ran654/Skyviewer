import requests
import nbtlib
import base64
import io
import math
import os
import gzip
from dotenv import load_dotenv
import pprint

# Get absolute path to the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, 'api.env')

# Load API Key from api.env
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"WARNING: api.env not found at {ENV_PATH}!")

API_KEY = os.getenv('HYPIXEL_API_KEY')
print(f"DEBUG: Loaded API Key: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else 'NONE'}")

class SkyBlockAPI:
    def __init__(self):
        self.headers = {"API-Key": str(API_KEY) if API_KEY else ""}
        self.collection_map = {}
        self.skill_map = {}
        self.slayer_map = {}
        self.dungeon_map = {}
        self.load_resources()

    def load_resources(self):
        """Fetches static game data from Hypixel API once when the app starts."""
        # Load Collections
        url_collections = "https://api.hypixel.net/v2/resources/skyblock/collections"
        try:
            res = requests.get(url_collections, headers=self.headers).json()
            if res.get('success'):
                for category in res['collections'].values():
                    for item_id, item_data in category['items'].items():
                        self.collection_map[item_id] = {
                            "name": item_data.get('name', 'Unknown'),
                            "max_tier": item_data.get('maxTiers') or item_data.get('maxTier') or item_data.get('MaxTier', 0),
                            "tiers": item_data.get('tiers', [])
                        }
        except Exception as e: print(f"Error loading collections: {e}")

        # Load Skills
        url_skills = "https://api.hypixel.net/v2/resources/skyblock/skills"
        try:
            res = requests.get(url_skills, headers=self.headers).json()
            if res.get('success'):
                self.skill_map = res['skills']
        except Exception as e: print(f"Error loading skills: {e}")

        # Load Slayers
        url_slayers = "https://api.hypixel.net/v2/resources/skyblock/slayer"
        try:
            res = requests.get(url_slayers, headers=self.headers).json()
            if res.get('success'):
                self.slayer_map = res['slayers']
        except Exception as e: print(f"Error loading slayers: {e}")

        # Load Dungeons
        url_dungeons = "https://api.hypixel.net/v2/resources/skyblock/dungeons"
        try:
            res = requests.get(url_dungeons, headers=self.headers).json()
            if res.get('success'):
                self.dungeon_map = res
        except Exception as e: print(f"Error loading dungeons: {e}")

    def get_level(self, xp, levels):
        if not xp: return {"level": 0, "progress": 0, "total_xp": 0}
        current_level = 0
        next_xp = 0
        prev_xp = 0
        for level_data in levels:
            req = level_data.get('totalExpRequired') or level_data.get('xp_required') or level_data.get('xp')
            if req is None: continue
            if xp >= req:
                current_level = level_data.get('level') or level_data.get('tier') or (levels.index(level_data) + 1)
                prev_xp = req
            else:
                next_xp = req
                break
        progress = ((xp - prev_xp) / (next_xp - prev_xp)) * 100 if next_xp > prev_xp else 100
        return {"level": current_level, "progress": min(progress, 100), "total_xp": xp}

    def get_skill_level(self, skill_name, xp):
        if skill_name.upper() == "CATACOMBS" and self.dungeon_map:
            levels = self.dungeon_map.get('dungeon_types', {}).get('catacombs', {}).get('experience_levels', [])
            return self.get_level(xp, levels)
        if not xp or skill_name.upper() not in self.skill_map:
            return {"level": 0, "progress": 0, "total_xp": xp if xp else 0}
        return self.get_level(xp, self.skill_map[skill_name.upper()]['levels'])

    def get_slayer_level(self, boss_name, xp):
        if not xp or boss_name.lower() not in self.slayer_map:
            return {"level": 0, "progress": 0, "total_xp": xp if xp else 0}
        levels = sorted(self.slayer_map[boss_name.lower()]['levels'].values(), key=lambda x: x.get('tier', 0))
        return self.get_level(xp, levels)

    def decode_inventory(self, raw_data):
        if not raw_data:
            return []
            
        try:
            # Decode Base64 and Unzip
            decoded = base64.b64decode(raw_data)
            compressed_stream = io.BytesIO(decoded)
            gzipped_stream = gzip.GzipFile(fileobj=compressed_stream)
            
            # Parse NBT
            nbt_data = nbtlib.File.parse(gzipped_stream)
            items = []
            
            inventory_list = nbt_data.get('i', [])
            
            for item in inventory_list:
                if item and 'tag' in item and 'display' in item['tag'] and 'Name' in item['tag']['display']:
                    # 1. Clean formatting codes from the Name
                    name = str(item['tag']['display']['Name'])
                    clean_name = ""
                    skip = False
                    for char in name:
                        if skip: 
                            skip = False
                            continue
                        if char == '§': 
                            skip = True
                        else: 
                            clean_name += char
                            
                    # 2. Get the SkyBlock ID for the textures!
                    sb_id = "UNKNOWN"
                    try:
                        sb_id = str(item['tag']['ExtraAttributes']['id'])
                    except KeyError:
                        try:
                            # Fallback for vanilla blocks
                            sb_id = str(item.get('id', '')).replace('minecraft:', '').upper()
                        except:
                            pass
                            
                    # --- DEBUG PRINT ---
                    print(f"DEBUG INVENTORY: Found {clean_name} (ID: {sb_id})")
                    # -------------------

                    # 3. Append the dictionary so HTML can use item.name and item.id
                    items.append({
                        "name": clean_name,
                        "id": sb_id
                    })
                else: 
                    items.append(None)
                    
            return items
            
        except Exception as e:
            print(f"DEBUG: NBT Parsing failed: {e}")
            # Ensure it returns a dictionary even on error so HTML doesn't crash
            return [{"name": f"ERROR: {e}", "id": "UNKNOWN"}]

    def get_hypixel_level(self, network_exp):
        return (math.sqrt(2 * network_exp + 30625) / 50) - 2.5

    def get_player_data(self, username):
        # 1. UUID
        print(f"Fetching UUID for {username}...")
        mojang_res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
        if mojang_res.status_code != 200: 
            print(f"Mojang API failed with status {mojang_res.status_code}")
            return None
        uuid = mojang_res.json().get('id')
        print(f"UUID found: {uuid}")

        # 2. Player Info
        print("Fetching Hypixel Player Info...")
        player_res = requests.get(f"https://api.hypixel.net/v2/player?uuid={uuid}", headers=self.headers).json()
        if not player_res.get('success'): 
            print(f"Hypixel Player API failed: {player_res.get('cause')}")
            return None
        if not player_res.get('player'):
            print("Player not found on Hypixel.")
            return None

        # 3. SB Profiles
        print("Fetching SkyBlock Profiles...")
        profiles_res = requests.get(f"https://api.hypixel.net/v2/skyblock/profiles?uuid={uuid}", headers=self.headers).json()
        if not profiles_res.get('success'):
            print(f"Hypixel SkyBlock API failed: {profiles_res.get('cause')}")
            return None
        if not profiles_res.get('profiles'):
            print("No SkyBlock profiles found.")
            return None

        print("Processing profile data...")
        try:
            active_profile = next((p for p in profiles_res['profiles'] if p.get('selected')), profiles_res['profiles'][0])
            profile_stats = active_profile['members'][uuid]
            
            # --- DEBUG VARIABLES START ---
            has_inventory_api = 'inventory' in profile_stats
            has_skills_api = 'player_data' in profile_stats and 'experience' in profile_stats['player_data']
            has_collection_api = 'collection' in profile_stats
            # --- DEBUG VARIABLES END ---
            
            # Organize data
            data = {
                "player": {
                    "username": username,
                    "uuid": uuid,
                    "network_level": round(self.get_hypixel_level(player_res.get('player', {}).get('networkExp', 0)), 2),
                    "active_profile": active_profile.get('cute_name'),
                    "sb_level": (profile_stats.get('leveling', {}).get('experience', 0) / 100),
                    "time_joined": profile_stats.get('first_join', 0),
                    "banking": {
                        "purse": profile_stats.get('currencies', {}).get('coin_purse', 0),
                        "bank": active_profile.get('banking', {}).get('balance', 0)
                    },
                    "avg_skill_level": 0,
                    "fairy_souls": profile_stats.get('fairy_souls', {}).get('total_collected', 0)
                },
                "inventories": {
                    "inventory": self.decode_inventory(profile_stats.get('inventory', {}).get('inv_contents', {}).get('data', "")),
                    "storage": self.decode_inventory(profile_stats.get('inventory', {}).get('ender_chest_contents', {}).get('data', "")),
                    "wardrobe": self.decode_inventory(profile_stats.get('inventory', {}).get('wardrobe_contents', {}).get('data', "")),
                    "sacks": self.decode_inventory(profile_stats.get('inventory', {}).get('bag_contents', {}).get('sacks_bag', {}).get('data', "")), 
                    "accessories": self.decode_inventory(profile_stats.get('inventory', {}).get('bag_contents', {}).get('talisman_bag', {}).get('data', "")), # Fixed to talisman_bag
                    "pets": profile_stats.get('pets_data', {}).get('pets', {}),
                    "museum": {}
                },
                "skills": {
                    "combat": {
                        "level": self.get_skill_level("COMBAT", profile_stats.get('player_data', {}).get('experience', {}).get('SKILL_COMBAT', 0)),
                        "slayers": {boss.capitalize(): self.get_slayer_level(boss, d.get('xp', 0)) for boss, d in profile_stats.get('slayer', {}).get('slayer_bosses', {}).items()},
                        "dungeons": {
                            "catacombs": self.get_skill_level("CATACOMBS", profile_stats.get('dungeons', {}).get('dungeon_types', {}).get('catacombs', {}).get('experience', 0)),
                            "floors": profile_stats.get('dungeons', {}).get('dungeon_types', {}).get('catacombs', {}).get('times_completed', {})
                        },
                        "secrets_found": player_res.get('player', {}).get('achievements', {}).get('skyblock_treasure_hunter', 0)
                    },
                    "farming": {
                        "level": self.get_skill_level("FARMING", profile_stats.get('player_data', {}).get('experience', {}).get('SKILL_FARMING', 0)),
                        "jacob": {
                            "medals": profile_stats.get('jacob2', {}).get('medals_inv', {}),
                            "contests": len(profile_stats.get('jacob2', {}).get('contests', {}))
                        }
                    },
                    "mining": {
                        "level": self.get_skill_level("MINING", profile_stats.get('player_data', {}).get('experience', {}).get('SKILL_MINING', 0)),
                        "hotm": {
                            "tier": profile_stats.get('mining_core', {}).get('nodes', {}).get('experience', 0),
                            "mithril_powder": profile_stats.get('mining_core', {}).get('powder_mithril', 0),
                            "gemstone_powder": profile_stats.get('mining_core', {}).get('powder_gemstone', 0),
                            "glacite_powder": profile_stats.get('mining_core', {}).get('powder_glacite', 0)
                        }
                    },
                    "fishing": {
                        "level": self.get_skill_level("FISHING", profile_stats.get('player_data', {}).get('experience', {}).get('SKILL_FISHING', 0)),
                        "stats": profile_stats.get('stats', {})
                    },
                    "foraging": {
                        "level": self.get_skill_level("FORAGING", profile_stats.get('player_data', {}).get('experience', {}).get('SKILL_FORAGING', 0))
                    },
                    "enchanting": {
                        "level": self.get_skill_level("ENCHANTING", profile_stats.get('player_data', {}).get('experience', {}).get('SKILL_ENCHANTING', 0)),
                        "experiments": profile_stats.get('experimentation', {})
                    }
                },
                "collections": profile_stats.get('collection', {}),
                "islands": {
                    "crimson_isle": profile_stats.get('nether_island_player_data', {}),
                    "rift": profile_stats.get('rift', {}),
                    "garden": active_profile.get('garden', {}),
                    "ch_mines": {},
                    "galatea": {}
                },
                "misc": {
                    "essence": profile_stats.get('currencies', {}).get('essence', {}),
                    "kills": profile_stats.get('stats', {}).get('kills', 0),
                    "deaths": profile_stats.get('stats', {}).get('deaths', 0)
                },
                "debug": {
                    "active_profile_id": active_profile.get('profile_id'),
                    "inventory_api_enabled": has_inventory_api,
                    "skills_api_enabled": has_skills_api,
                    "collection_api_enabled": has_collection_api
                }
            }
            return data
        
        except Exception as e:
            print(f"Error processing profile data: {e}")
            import traceback
            traceback.print_exc()
            return None

api = SkyBlockAPI()

if __name__ == '__main__':
    print("API module initialized.")