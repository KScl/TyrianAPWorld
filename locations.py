# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import TYPE_CHECKING, Any, Dict, List, Set, Tuple

from BaseClasses import LocationProgressType as LPType

from .items import Episode

if TYPE_CHECKING:
    from . import TyrianLocation, TyrianWorld


class LevelRegion:
    # I don't really like the distribution I was getting from just doing random.triangular, so
    # instead we have multiple different types of random prices that can get generated, and we choose
    # which one we want randomly (based on the level we're generating it for).
    # Appending an "!" makes the shop location prioritized.
    # Appending a "#" makes the shop location excluded.
    base_shop_setup_list: Dict[str, Tuple[int, int, int]] = {
        "A": (   50,   501,   1),
        "B": (  100,  1001,   1),
        "C": (  200,  2001,   2),
        "D": (  400,  3001,   2),
        "E": (  750,  3001,   5),
        "F": (  500,  5001,   5),
        "G": ( 1000,  7501,   5),
        "H": ( 2000,  7501,  10),
        "I": ( 3000,  9001,  10),
        "J": ( 2000, 10001,   5),
        "K": ( 3000, 10001,  10),
        "L": ( 5000, 10001,  25),
        "M": ( 3000, 15001,  10),
        "N": ( 5000, 15001,  25),
        "O": ( 7500, 15001,  50),
        "P": ( 4000, 20001,  10),
        "Q": ( 6000, 20001,  25),
        "R": ( 5000, 25001,  50),
        "S": ( 5000, 30001, 100),
        "T": (10000, 30001,  25),
        "U": (10000, 40001,  50),
        "V": (10000, 50001, 100),
        "W": (10000, 65601, 100),
        "X": (20000, 65601, 100),
        "Y": (30000, 65601, 100),
        "Z": (65535, 65536,   1)  # Always max shop price
    }

    episode: Episode
    locations: Dict[str, Any]  # List of strings to location or sub-region names
    flattened_locations: Dict[str, int]  # Only location names, ignoring sub-regions
    shop_setups: List[str]  # See base_shop_setups_list above

    def __init__(self, episode: Episode, locations: Dict[str, Any], shop_setups: List[str] = ["F", "H", "K", "L"]):
        self.episode = episode
        self.locations = locations
        self.shop_setups = shop_setups

        # Immediately create a flattened location list
        def shop_locations(name: str, all_ids: Tuple[Any]) -> Dict[str, int]:
            # Turns "Shop - LEVELNAME (Episode 1)": (...) into individual location names
            return {f"{name} - Item {(shop_id - all_ids[0]) + 1}": shop_id for shop_id in all_ids}

        def flatten(locations: Dict[str, Any]) -> Dict[str, int]:
            results: Dict[str, int] = {}
            for name, value in locations.items():
                if type(value) is dict:
                    results.update(flatten(value))
                elif type(value) is tuple:
                    results.update(shop_locations(name, value))
                else:
                    results[name] = value
            return results

        self.flattened_locations = flatten(locations)

    # Gets a random price based on this level's shop setups, and assigns it to the locaton.
    # Also changes location to prioritized/excluded automatically based on the setup rolled.
    def set_random_shop_price(self, world: "TyrianWorld", location: "TyrianLocation") -> None:
        setup_choice = world.random.choice(self.shop_setups)
        if len(setup_choice) > 1:
            location.progress_type = LPType.PRIORITY if setup_choice[-1] == "!" else LPType.EXCLUDED
        location.shop_price = min(world.random.randrange(*self.base_shop_setup_list[setup_choice[0]]), 65535)

    # Gets a flattened dict of all locations, id: name
    def get_locations(self, base_id: int = 0) -> Dict[str, int]:
        return {name: base_id + location_id for (name, location_id) in self.flattened_locations.items()}

    # Returns just names from the above.
    def get_location_names(self) -> Set[str]:
        return {name for name in self.flattened_locations.keys()}


class LevelLocationData:

    level_regions: Dict[str, LevelRegion] = {

        # =============================================================================================
        # EPISODE 1 - ESCAPE
        # =============================================================================================

        # The hard variant of Tyrian is similarly designed, just with more enemies, so it shares checks.
        "TYRIAN (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "TYRIAN (Episode 1) - First U-Ship Secret": 0,
            "TYRIAN (Episode 1) - Early Spinner Formation": 1,
            "TYRIAN (Episode 1) - Lander near BUBBLES Warp Rock": 2,
            "TYRIAN (Episode 1) - BUBBLES Warp Rock": 3,
            "TYRIAN (Episode 1) - HOLES Warp Orb": 4,
            "TYRIAN (Episode 1) - Ships Between Platforms": 5,
            "TYRIAN (Episode 1) - First Line of Tanks": 6,
            "TYRIAN (Episode 1) - Tank Turn-and-fire Secret": 7,
            "TYRIAN (Episode 1) - SOH JIN Warp Orb": 8,

            "TYRIAN (Episode 1) @ Pass Boss (can time out)": {
                "TYRIAN (Episode 1) - Boss": 9,
                "Shop - TYRIAN (Episode 1)": (1000, 1001, 1002, 1003, 1004),
            },
        }, shop_setups=["A#", "B", "C", "D", "D", "E", "F", "F", "G", "I!"]),

        "BUBBLES (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "BUBBLES (Episode 1) @ Pass Bubble Lines": {
                "BUBBLES (Episode 1) - Orbiting Bubbles": 10,
                "BUBBLES (Episode 1) - Shooting Bubbles": 11,
                "BUBBLES (Episode 1) - Final Bubble Line": 15,
                "Shop - BUBBLES (Episode 1)": (1010, 1011, 1012, 1013, 1014),

                "BUBBLES (Episode 1) @ Speed Up Section": {
                    "BUBBLES (Episode 1) - Coin Rain 1": 12,
                    "BUBBLES (Episode 1) - Coin Rain 2": 13,
                    "BUBBLES (Episode 1) - Coin Rain 3": 14,
                },
            },
        }, shop_setups=["C", "D", "E", "G", "I"]),

        "HOLES (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "HOLES (Episode 1) - U-Ship Formation 1": 20,
            "HOLES (Episode 1) - U-Ship Formation 2": 21,

            "HOLES (Episode 1) @ Pass Spinner Gauntlet": {
                "HOLES (Episode 1) - Lander after Spinners": 22,
                "HOLES (Episode 1) - U-Ships after Boss Fly-By": 24,
                "HOLES (Episode 1) - Before Speed Up Section": 26,
                "Shop - HOLES (Episode 1)": (1020, 1021, 1022, 1023, 1024),

                "HOLES (Episode 1) @ Destroy Boss Ships": {
                    "HOLES (Episode 1) - Boss Ship Fly-By 1": 23,
                    "HOLES (Episode 1) - Boss Ship Fly-By 2": 25,
                },
            },
        }, shop_setups=["C", "D", "D", "E", "F", "F", "H"]),

        "SOH JIN (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "SOH JIN (Episode 1) - Starting Alcove": 30,
            "SOH JIN (Episode 1) - Triple Diagonal Launchers": 32,
            "SOH JIN (Episode 1) - Checkerboard Pattern": 33,
            "SOH JIN (Episode 1) - Triple Orb Launchers": 34,
            "SOH JIN (Episode 1) - Double Orb Launcher Line": 35,
            "SOH JIN (Episode 1) - Next to Double Point Items": 36,
            "Shop - SOH JIN (Episode 1)": (1030, 1031, 1032, 1033, 1034),

            "SOH JIN (Episode 1) @ Destroy Walls": {
                "SOH JIN (Episode 1) - Walled-in Orb Launcher": 31,
            },
        }, shop_setups=["F", "H", "H", "J", "J", "T"]),

        "ASTEROID1 (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "ASTEROID1 (Episode 1) - Shield Ship in Asteroid Field": 40,
            "ASTEROID1 (Episode 1) - Railgunner 1": 41,
            "ASTEROID1 (Episode 1) - Railgunner 2": 42,
            "ASTEROID1 (Episode 1) - Railgunner 3": 43,
            "ASTEROID1 (Episode 1) - ASTEROID? Warp Orb": 44,
            "ASTEROID1 (Episode 1) - Maneuvering Missiles": 45,

            "ASTEROID1 (Episode 1) @ Destroy Boss": {
                "ASTEROID1 (Episode 1) - Boss": 46,
                "Shop - ASTEROID1 (Episode 1)": (1040, 1041, 1042, 1043, 1044),
            },
        }, shop_setups=["E", "F", "F", "F", "G"]),

        "ASTEROID2 (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1": 50,
            "ASTEROID2 (Episode 1) - First Tank Squadron": 51,
            "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2": 52,
            "ASTEROID2 (Episode 1) - Second Tank Squadron": 53,
            "ASTEROID2 (Episode 1) - Tank Bridge": 54,
            "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret": 55,
            "ASTEROID2 (Episode 1) - MINEMAZE Warp Orb": 56,

            "ASTEROID2 (Episode 1) @ Destroy Boss": {
                "ASTEROID2 (Episode 1) - Boss": 57,
                "Shop - ASTEROID2 (Episode 1)": (1050, 1051, 1052, 1053, 1054),
            },
        }, shop_setups=["E", "F", "F", "F", "G"]),

        "ASTEROID? (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "ASTEROID? (Episode 1) @ Initial Welcome": {
                "ASTEROID? (Episode 1) - Welcoming Launchers 1": 60,
                "ASTEROID? (Episode 1) - Welcoming Launchers 2": 61,
                "ASTEROID? (Episode 1) - Boss Launcher": 62,
                "ASTEROID? (Episode 1) - WINDY Warp Orb": 63,

                "ASTEROID? (Episode 1) @ Quick Shots": {
                    "ASTEROID? (Episode 1) - Quick Shot 1": 64,
                    "ASTEROID? (Episode 1) - Quick Shot 2": 65,
                },
                "ASTEROID? (Episode 1) @ Final Gauntlet": {
                    "Shop - ASTEROID? (Episode 1)": (1060, 1061, 1062, 1063, 1064),
                },
            },
        }, shop_setups=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]),

        "MINEMAZE (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "MINEMAZE (Episode 1) @ Destroy Gates": {
                "MINEMAZE (Episode 1) - Starting Gate": 70,
                "MINEMAZE (Episode 1) - Lone Orb": 71,
                "MINEMAZE (Episode 1) - Right Path Gate": 72,
                "MINEMAZE (Episode 1) - That's not a Strawberry": 73,
                "MINEMAZE (Episode 1) - ASTEROID? Warp Orb": 74,
                "MINEMAZE (Episode 1) - Ships Behind Central Gate": 75,
                "Shop - MINEMAZE (Episode 1)": (1070, 1071, 1072, 1073, 1074),
            },
        }, shop_setups=["E", "F", "F", "F", "G"]),

        "WINDY (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "WINDY (Episode 1) @ Fly Through": {
                "Shop - WINDY (Episode 1)": (1080, 1081, 1082, 1083, 1084),

                "WINDY (Episode 1) @ Phase Through Walls": {
                    "WINDY (Episode 1) - Central Question Mark": 80,
                },
            },
        }, shop_setups=["F", "G", "I"]),

        # This is the variant of Savara on Easy or Medium.
        "SAVARA (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "SAVARA (Episode 1) - White Formation Leader 1": 90,
            "SAVARA (Episode 1) - White Formation Leader 2": 91,
            "SAVARA (Episode 1) - Green Plane Line": 92,
            "SAVARA (Episode 1) - Brown Plane Breaking Formation": 93,
            "SAVARA (Episode 1) - Huge Plane, Speeds By": 94,
            "SAVARA (Episode 1) - Vulcan Plane": 95,

            "SAVARA (Episode 1) @ Pass Boss (can time out)": {
                "SAVARA (Episode 1) - Boss": 96,
                "Shop - SAVARA (Episode 1)": (1090, 1091, 1092, 1093, 1094),
            },
        }, shop_setups=["E", "H", "L", "P"]),

        # This is the variant of Savara on Hard or above.
        "SAVARA II (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "SAVARA II (Episode 1) @ Base Requirements": {
                "SAVARA II (Episode 1) - Launched Planes 1": 100,
                "SAVARA II (Episode 1) - Huge Plane Amidst Turrets": 102,
                "SAVARA II (Episode 1) - Vulcan Planes Near Blimp": 103,
                "SAVARA II (Episode 1) - Launched Planes 2": 105,

                "SAVARA II (Episode 1) @ Destroy Green Planes": {
                    "SAVARA II (Episode 1) - Green Plane Sequence 1": 101,
                    "SAVARA II (Episode 1) - Green Plane Sequence 2": 104,
                },
                "SAVARA II (Episode 1) @ Pass Boss (can time out)": {
                    "SAVARA II (Episode 1) - Boss": 106,
                    "Shop - SAVARA II (Episode 1)": (1100, 1101, 1102, 1103, 1104),
                },
            },
        }, shop_setups=["E", "H", "L", "P"]),

        "BONUS (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "BONUS (Episode 1) @ Destroy Patterns": {
                "Shop - BONUS (Episode 1)": (1110, 1111, 1112, 1113, 1114),
            }
        }, shop_setups=["J", "J", "J", "K", "K", "L"]),

        "MINES (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "MINES (Episode 1) - Blue Mine": 121,
            "MINES (Episode 1) - Absolutely Free": 123,
            "MINES (Episode 1) - But Wait There's More": 124,
            "Shop - MINES (Episode 1)": (1120, 1121, 1122, 1123, 1124),

            "MINES (Episode 1) @ Destroy First Orb": {
                "MINES (Episode 1) - Regular Spinning Orbs": 120,

                "MINES (Episode 1) @ Destroy Second Orb": {
                    "MINES (Episode 1) - Repulsor Spinning Orbs": 122,
                },
            },
        }, shop_setups=["E", "F", "G", "H", "J"]),

        "DELIANI (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "DELIANI (Episode 1) - First Turret Wave 1": 130,
            "DELIANI (Episode 1) - First Turret Wave 2": 131,
            "DELIANI (Episode 1) - Tricky Rail Turret": 132,
            "DELIANI (Episode 1) - Second Turret Wave 1": 133,
            "DELIANI (Episode 1) - Second Turret Wave 2": 134,

            "DELIANI (Episode 1) @ Pass Ambush": {
                "DELIANI (Episode 1) - Ambush": 135,
                "DELIANI (Episode 1) - Last Cross Formation": 136,

                "DELIANI (Episode 1) @ Destroy Boss": {
                    "DELIANI (Episode 1) - Boss": 137,
                    "Shop - DELIANI (Episode 1)": (1130, 1131, 1132, 1133, 1134),
                },
            },
        }, shop_setups=["K", "M", "O", "P", "Q"]),

        "SAVARA V (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "SAVARA V (Episode 1) - Green Plane Sequence": 140,
            "SAVARA V (Episode 1) - Flying Between Blimps": 141,
            "SAVARA V (Episode 1) - Brown Plane Sequence": 142,
            "SAVARA V (Episode 1) - Flying Alongside Green Planes": 143,
            "SAVARA V (Episode 1) - Super Blimp": 144,

            "SAVARA V (Episode 1) @ Destroy Bosses": {
                "SAVARA V (Episode 1) - Mid-Boss": 145,
                "SAVARA V (Episode 1) - Boss": 146,
                "Shop - SAVARA V (Episode 1)": (1140, 1141, 1142, 1143, 1144),
            },
        }, shop_setups=["E", "H", "L", "P"]),

        "ASSASSIN (Episode 1)": LevelRegion(episode=Episode.Escape, locations={
            "ASSASSIN (Episode 1) @ Destroy Boss": {
                "ASSASSIN (Episode 1) - Boss": 150,
                "Shop - ASSASSIN (Episode 1)": (1150, 1151, 1152, 1153, 1154),
                # Event: "Episode 1 (Escape) Complete"
            },
        }, shop_setups=["S"]),

        # =============================================================================================
        # EPISODE 2 - TREACHERY
        # =============================================================================================

        "TORM (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "TORM (Episode 2) - Jungle Ship V Formation 1": 160,
            "TORM (Episode 2) - Ship Fleeing Dragon Secret": 161,
            "TORM (Episode 2) - Excuse Me, You Dropped This": 162,
            "TORM (Episode 2) - Jungle Ship V Formation 2": 163,
            "TORM (Episode 2) - Jungle Ship V Formation 3": 164,
            "TORM (Episode 2) - Undocking Jungle Ship": 165,
            "TORM (Episode 2) - Boss Ship Fly-By": 166,

            "TORM (Episode 2) @ Pass Boss (can time out)": {
                "TORM (Episode 2) - Boss": 167,
                "Shop - TORM (Episode 2)": (1160, 1161, 1162, 1163, 1164),
            },
        }, shop_setups=["A#", "B", "C", "D", "D", "E", "F", "F", "G", "I!"]),

        "GYGES (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "GYGES (Episode 2) - Circled Shapeshifting Turret 1": 170,
            "GYGES (Episode 2) - Wide Waving Worm": 171,
            "GYGES (Episode 2) - Orbsnake": 172,
            "GYGES (Episode 2) @ After Speed Up Section": {
                "GYGES (Episode 2) - GEM WAR Warp Orb": 173,
                "GYGES (Episode 2) - Circled Shapeshifting Turret 2": 174,
                "GYGES (Episode 2) - Last Set of Worms": 175,

                "GYGES (Episode 2) @ Destroy Boss": {
                    "GYGES (Episode 2) - Boss": 176,
                    "Shop - GYGES (Episode 2)": (1170, 1171, 1172, 1173, 1174),
                },
            },
        }),

        "BONUS 1 (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "BONUS 1 (Episode 2) @ Destroy Patterns": {
                "Shop - BONUS 1 (Episode 2)": (1180, 1181, 1182, 1183, 1184),
            },
        }),

        "ASTCITY (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "ASTCITY (Episode 2) @ Base Requirements": {
                "ASTCITY (Episode 2) - Shield Ship V Formation 1": 190,
                "ASTCITY (Episode 2) - Shield Ship V Formation 2": 191,
                "ASTCITY (Episode 2) - Plasma Turrets Going Uphill": 192,
                "ASTCITY (Episode 2) - Warehouse 92": 193,
                "ASTCITY (Episode 2) - Shield Ship V Formation 3": 194,
                "ASTCITY (Episode 2) - Shield Ship Canyon 1": 195,
                "ASTCITY (Episode 2) - Shield Ship Canyon 2": 196,
                "ASTCITY (Episode 2) - Shield Ship Canyon 3": 197,
                "ASTCITY (Episode 2) - MISTAKES Warp Orb": 198,
                "ASTCITY (Episode 2) - Ending Turret Group": 199,
                "Shop - ASTCITY (Episode 2)": (1190, 1191, 1192, 1193, 1194),
            },
        }),

        "BONUS 2 (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "Shop - BONUS 2 (Episode 2)": (1200, 1201, 1202, 1203, 1204),
        }),

        "GEM WAR (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "GEM WAR (Episode 2) @ Base Requirements": {
                "GEM WAR (Episode 2) @ Red Gem Leaders Easy": {
                    "GEM WAR (Episode 2) - Red Gem Leader 2": 211,
                    "GEM WAR (Episode 2) - Red Gem Leader 3": 212,

                    "GEM WAR (Episode 2) @ Red Gem Leaders Medium": {
                        "GEM WAR (Episode 2) - Red Gem Leader 1": 210,

                        "GEM WAR (Episode 2) @ Red Gem Leaders Hard": {
                            "GEM WAR (Episode 2) - Red Gem Leader 4": 213,
                        },
                    },
                },
                "GEM WAR (Episode 2) @ Blue Gem Bosses": {
                    "GEM WAR (Episode 2) - Blue Gem Boss 1": 214,
                    "GEM WAR (Episode 2) - Blue Gem Boss 2": 215,
                    "Shop - GEM WAR (Episode 2)": (1210, 1211, 1212, 1213, 1214),
                },
            },
        }),

        "MARKERS (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "MARKERS (Episode 2) @ Base Requirements": {
                "MARKERS (Episode 2) - Right Path Turret": 220,

                "MARKERS (Episode 2) @ Through Minelayer Blockade": {
                    "MARKERS (Episode 2) - Persistent Minelayer": 221,
                    "MARKERS (Episode 2) - Car Destroyer Secret": 222,
                    "MARKERS (Episode 2) - Left Path Turret": 223,
                    "MARKERS (Episode 2) - End Section Turret": 224,
                    "Shop - MARKERS (Episode 2)": (1220, 1221, 1222, 1223, 1224),
                },
            },
        }),

        "MISTAKES (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "MISTAKES (Episode 2) @ Base Requirements": {
                "MISTAKES (Episode 2) - Start, Trigger Enemy 1": 230,
                "MISTAKES (Episode 2) - Start, Trigger Enemy 2": 231,
                "MISTAKES (Episode 2) - Orbsnakes, Trigger Enemy 1": 232,
                "MISTAKES (Episode 2) - Claws, Trigger Enemy 1": 234,
                "MISTAKES (Episode 2) - Drills, Trigger Enemy 1": 236,
                "MISTAKES (Episode 2) - Drills, Trigger Enemy 2": 237,
                "Shop - MISTAKES (Episode 2)": (1230, 1231, 1232, 1233, 1234),

                "MISTAKES (Episode 2) @ Bubble Spawner Path": {
                    "MISTAKES (Episode 2) - Claws, Trigger Enemy 2": 235,
                    "MISTAKES (Episode 2) - Super Bubble Spawner": 238,
                },
                "MISTAKES (Episode 2) @ Softlock Path": {
                    "MISTAKES (Episode 2) - Orbsnakes, Trigger Enemy 2": 233,
                    "MISTAKES (Episode 2) - Anti-Softlock": 239,
                },
            },
        }, shop_setups=["B", "D", "J", "K", "L", "O", "V", "Z!"]),

        "SOH JIN (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "SOH JIN (Episode 2) @ Base Requirements": {
                "SOH JIN (Episode 2) - Sinusoidal Missile Wave": 240,
                "SOH JIN (Episode 2) - Second Missile Ship Set": 241,

                "SOH JIN (Episode 2) @ Destroy Second Wave Paddles": {
                    "SOH JIN (Episode 2) - Paddle Destruction 1": 242,
                    "SOH JIN (Episode 2) - Paddle Destruction 2": 243,
                },
                "SOH JIN (Episode 2) @ Fly Through Third Wave Orbs": {
                    "SOH JIN (Episode 2) - Last Missile Ship Set": 244,
                    "Shop - SOH JIN (Episode 2)": (1240, 1241, 1242, 1243, 1244),

                    "SOH JIN (Episode 2) @ Destroy Third Wave Orbs": {
                        "SOH JIN (Episode 2) - Boss Orbs 1": 245,
                        "SOH JIN (Episode 2) - Boss Orbs 2": 246,
                    },
                },
            },
        }),

        "BOTANY A (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "BOTANY A (Episode 2) - Retreating Mobile Turret": 250,

            "BOTANY A (Episode 2) @ Beyond Starting Area": {
                "BOTANY A (Episode 2) - Green Ship Pincer": 254,

                "BOTANY A (Episode 2) @ Can Destroy Turrets": {
                    "BOTANY A (Episode 2) - End of Path Secret 1": 251,
                    "BOTANY A (Episode 2) - Mobile Turret Approaching Head-On": 252,
                    "BOTANY A (Episode 2) - End of Path Secret 2": 253,
                },
                "BOTANY A (Episode 2) @ Pass Boss (can time out)": {
                    "BOTANY A (Episode 2) - Boss": 255,
                    "Shop - BOTANY A (Episode 2)": (1250, 1251, 1252, 1253, 1254),
                },
            },
        }),

        "BOTANY B (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "BOTANY B (Episode 2) - Starting Platform Sensor": 260,

            "BOTANY B (Episode 2) @ Beyond Starting Platform": {
                "BOTANY B (Episode 2) - Main Platform Sensor 1": 261,
                "BOTANY B (Episode 2) - Main Platform Sensor 2": 262,
                "BOTANY B (Episode 2) - Main Platform Sensor 3": 263,
                "BOTANY B (Episode 2) - Super-Turret on Bridge": 264,

                "BOTANY B (Episode 2) @ Pass Boss (can time out)": {
                    "BOTANY B (Episode 2) - Boss": 265,
                    "Shop - BOTANY B (Episode 2)": (1260, 1261, 1262, 1263, 1264),
                },
            },
        }),

        "GRYPHON (Episode 2)": LevelRegion(episode=Episode.Treachery, locations={
            "GRYPHON (Episode 2) @ Base Requirements": {
                "GRYPHON (Episode 2) - Pulse-Turret Wave Mid-Spikes": 270,
                "GRYPHON (Episode 2) - Swooping Pulse-Turrets": 271,
                "GRYPHON (Episode 2) - Sweeping Pulse-Turrets": 272,
                "GRYPHON (Episode 2) - Spike From Behind": 273,
                "GRYPHON (Episode 2) - Breaking Formation 1": 274,
                "GRYPHON (Episode 2) - Breaking Formation 2": 275,
                "GRYPHON (Episode 2) - Breaking Formation 3": 276,
                "GRYPHON (Episode 2) - Breaking Formation 4": 277,
                "GRYPHON (Episode 2) - Breaking Formation 5": 278,

                "GRYPHON (Episode 2) @ Destroy Boss": {
                    "GRYPHON (Episode 2) - Boss": 279,
                    "Shop - GRYPHON (Episode 2)": (1270, 1271, 1272, 1273, 1274),
                    # Event: "Episode 2 (Treachery) Complete"
                },
            },
        }, shop_setups=["S", "S", "V"]),

        # =============================================================================================
        # EPISODE 3 - MISSION: SUICIDE
        # =============================================================================================

        "GAUNTLET (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "GAUNTLET (Episode 3) - Fork Ships, Right": 280,
            "GAUNTLET (Episode 3) - Fork Ships, Middle": 281,
            "GAUNTLET (Episode 3) - Doubled-up Gates": 282,
            "GAUNTLET (Episode 3) - Capsule Ships Near Mace": 283,
            "GAUNTLET (Episode 3) - Split Gates, Left": 284,

            "GAUNTLET (Episode 3) @ Clear Orb Tree": {
                "GAUNTLET (Episode 3) - Tree of Spinning Orbs": 285,
                "GAUNTLET (Episode 3) - Gate near Freebie Item": 286,
                "GAUNTLET (Episode 3) - Freebie Item": 287,

                "Shop - GAUNTLET (Episode 3)": (1280, 1281, 1282, 1283, 1284),
            }
        }, shop_setups=["A#", "B", "C", "D", "D", "E", "F", "F", "G", "I!"]),

        "IXMUCANE (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "IXMUCANE (Episode 3) - Pebble Ship, Start": 290,

            "IXMUCANE (Episode 3) @ Pass Minelayers Requirements": {
                "IXMUCANE (Episode 3) - Pebble Ship, Speed Up Section": 291,
                "IXMUCANE (Episode 3) - Enemy From Behind": 292,
                "IXMUCANE (Episode 3) - Sideways Minelayer, Domes": 293,
                "IXMUCANE (Episode 3) - Pebble Ship, Domes": 294,
                "IXMUCANE (Episode 3) - Sideways Minelayer, Before Boss": 295,

                "IXMUCANE (Episode 3) @ Pass Boss (can time out)": {
                    "IXMUCANE (Episode 3) - Boss": 296,
                    "Shop - IXMUCANE (Episode 3)": (1290, 1291, 1292, 1293, 1294),
                },
            }
        }),

        "BONUS (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "BONUS (Episode 3) - Lone Turret 1": 300,

            "BONUS (Episode 3) @ Pass Onslaughts": {
                "BONUS (Episode 3) - Lone Turret 2": 303,

                "BONUS (Episode 3) @ Get Items from Onslaughts": {
                    "BONUS (Episode 3) - Behind Onslaught 1": 301,
                    "BONUS (Episode 3) - Behind Onslaught 2": 302,
                },
                "BONUS (Episode 3) @ Sonic Wave Hell": {
                    "BONUS (Episode 3) - Sonic Wave Hell Turret": 304,
                    "Shop - BONUS (Episode 3)": (1300, 1301, 1302, 1303, 1304),
                },
            },
        }, shop_setups=["G", "G"]),

        "STARGATE (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "STARGATE (Episode 3) - The Bubbleway": 310,
            "STARGATE (Episode 3) - First Bubble Spawner": 311,
            "STARGATE (Episode 3) - AST. CITY Warp Orb 1": 312,
            "STARGATE (Episode 3) - AST. CITY Warp Orb 2": 313,
            "STARGATE (Episode 3) - SAWBLADES Warp Orb 1": 314,
            "STARGATE (Episode 3) - SAWBLADES Warp Orb 2": 315,

            "STARGATE (Episode 3) @ Reach Bubble Spawner": {
                "STARGATE (Episode 3) - Super Bubble Spawner": 316,
                "Shop - STARGATE (Episode 3)": (1310, 1311, 1312, 1313, 1314),
            },
        }),

        "AST. CITY (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "AST. CITY (Episode 3) @ Base Requirements": {
                "AST. CITY (Episode 3) - Shield Ship, Start": 320,
                "AST. CITY (Episode 3) - Shield Ship, After Boss Dome 1": 322,
                "AST. CITY (Episode 3) - Shield Ship, Before Boss Dome 2": 323,
                "AST. CITY (Episode 3) - Shield Ship, Near Boss Dome 2": 325,
                "AST. CITY (Episode 3) - Shield Ship, Near Boss Dome 3": 327,
                "Shop - AST. CITY (Episode 3)": (1320, 1321, 1322, 1323, 1324),

                "AST. CITY (Episode 3) @ Destroy Boss Domes": {
                    "AST. CITY (Episode 3) - Boss Dome 1": 321,
                    "AST. CITY (Episode 3) - Boss Dome 2": 324,
                    "AST. CITY (Episode 3) - Boss Dome 3": 326,
                    "AST. CITY (Episode 3) - Boss Dome 4": 328,
                }
            }
        }),

        "SAWBLADES (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "SAWBLADES (Episode 3) @ Base Requirements": {
                "SAWBLADES (Episode 3) - Pebble Ship, Start 1": 330,
                "SAWBLADES (Episode 3) - Pebble Ship, Start 2": 331,
                "SAWBLADES (Episode 3) - Light Turret, Gravitium Rocks": 332,
                "SAWBLADES (Episode 3) - Waving Sawblade": 333,
                "SAWBLADES (Episode 3) - Light Turret, After Sawblades": 334,
                "SAWBLADES (Episode 3) - Pebble Ship, After Sawblades": 335,
                "SAWBLADES (Episode 3) - SuperCarrot Secret Drop": 336,
                "Shop - SAWBLADES (Episode 3)": (1330, 1331, 1332, 1333, 1334),
            }
        }),

        "CAMANIS (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "CAMANIS (Episode 3) @ Base Requirements": {
                "CAMANIS (Episode 3) - Ice Spitter, Near Plasma Guns": 340,
                "CAMANIS (Episode 3) - Blizzard Ship Assault": 341,
                "CAMANIS (Episode 3) - Ice Spitter, After Blizzard": 342,
                "CAMANIS (Episode 3) - Roaming Snowball": 343,
                "CAMANIS (Episode 3) - Ice Spitter, Ending": 344,

                "CAMANIS (Episode 3) @ Pass Boss (can time out)": {
                    "CAMANIS (Episode 3) - Boss": 345,
                    "Shop - CAMANIS (Episode 3)": (1340, 1341, 1342, 1343, 1344),
                }
            }
        }),

        "MACES (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "MACES (Episode 3) - Third Mace's Path": 350,
            "MACES (Episode 3) - Sixth Mace's Path": 351,
            "MACES (Episode 3) - A Brief Reprieve, Left": 352,
            "MACES (Episode 3) - A Brief Reprieve, Center": 353,
            "MACES (Episode 3) - A Brief Reprieve, Right": 354,
            "Shop - MACES (Episode 3)": (1350, 1351, 1352, 1353, 1354),
        }),

        "TYRIAN X (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "TYRIAN X (Episode 3) @ Base Requirements": {
                "TYRIAN X (Episode 3) - First U-Ship Secret": 360,
                "TYRIAN X (Episode 3) - Second Secret, Same as the First": 361,
                "TYRIAN X (Episode 3) - Side-flying Ship Near Landers": 362,
                "TYRIAN X (Episode 3) - Platform Spinner Sequence": 363,
                "TYRIAN X (Episode 3) - Ships Between Platforms": 364,

                "TYRIAN X (Episode 3) @ Tanks Behind Structures": {
                    "TYRIAN X (Episode 3) - Tank Near Purple Structure": 365,
                    "TYRIAN X (Episode 3) - Tank Turn-and-fire Secret": 366,
                },
                "TYRIAN X (Episode 3) @ Pass Boss (can time out)": {
                    "TYRIAN X (Episode 3) - Boss": 367,
                    "Shop - TYRIAN X (Episode 3)": (1360, 1361, 1362, 1363, 1364),
                },
            }
        }),

        "SAVARA Y (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "SAVARA Y (Episode 3) - White Formation Leader": 370,
            "SAVARA Y (Episode 3) - Flying Between Huge Planes": 371,
            "SAVARA Y (Episode 3) - Vulcan Plane Set": 372,

            "SAVARA Y (Episode 3) @ Through Blimp Blockade": {
                "SAVARA Y (Episode 3) - Boss Ship Fly-By": 373,

                "SAVARA Y (Episode 3) @ Death Plane Set": {
                    "SAVARA Y (Episode 3) - Death Plane Set, Right": 374,
                    "SAVARA Y (Episode 3) - Death Plane Set, Center": 375,
                },
                "SAVARA Y (Episode 3) @ Pass Boss (can time out)": {
                    "SAVARA Y (Episode 3) - Boss": 376,
                    "Shop - SAVARA Y (Episode 3)": (1370, 1371, 1372, 1373, 1374),
                },
            }
        }),

        "NEW DELI (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "NEW DELI (Episode 3) @ Base Requirements": {
                "NEW DELI (Episode 3) - First Turret Wave 1": 380,
                "NEW DELI (Episode 3) - First Turret Wave 2": 381,

                "NEW DELI (Episode 3) @ The Gauntlet Begins": {
                    "NEW DELI (Episode 3) - Second Turret Wave 1": 382,
                    "NEW DELI (Episode 3) - Second Turret Wave 2": 383,
                    "NEW DELI (Episode 3) - Second Turret Wave 3": 384,
                    "NEW DELI (Episode 3) - Second Turret Wave 4": 385,

                    "NEW DELI (Episode 3) @ Destroy Boss": {
                        "NEW DELI (Episode 3) - Boss": 386,
                        "Shop - NEW DELI (Episode 3)": (1380, 1381, 1382, 1383, 1384),
                    },
                }
            }
        }),

        "FLEET (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, locations={
            "FLEET (Episode 3) @ Base Requirements": {
                "FLEET (Episode 3) - Attractor Crane, Entrance": 390,
                "FLEET (Episode 3) - Fire Shooter, Between Ships": 391,
                "FLEET (Episode 3) - Fire Shooter, Near Massive Ship": 392,
                "FLEET (Episode 3) - Attractor Crane, Mid-Fleet": 393,

                "FLEET (Episode 3) @ Destroy Boss": {
                    "FLEET (Episode 3) - Boss": 394,
                    "Shop - FLEET (Episode 3)": (1390, 1391, 1392, 1393, 1394),
                    # Event: "Episode 3 (Mission: Suicide) Complete"
                },
            }
        }, shop_setups=["S", "V", "X"]),

        # =============================================================================================
        # EPISODE 4 - AN END TO FATE
        # =============================================================================================

        "SURFACE (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "SURFACE (Episode 4) - WINDY Warp Orb": 400,
            "SURFACE (Episode 4) - Triple V Formation": 401,

            "Shop - SURFACE (Episode 4)": (1400, 1401, 1402, 1403, 1404),
        }),

        "WINDY (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "Shop - WINDY (Episode 4)": (1410, 1411, 1412, 1413, 1414),
        }),

        "LAVA RUN (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "LAVA RUN (Episode 4) - Second Laser Shooter": 420,
            "LAVA RUN (Episode 4) - Left Side Missile Launcher": 421,

            "LAVA RUN (Episode 4) @ Pass Boss (can time out)": {
                "LAVA RUN (Episode 4) - Boss": 422,
                "Shop - LAVA RUN (Episode 4)": (1420, 1421, 1422, 1423, 1424),
            },
        }),

        "CORE (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "CORE (Episode 4) @ Destroy Boss": {
                "CORE (Episode 4) - Boss": 430,
                "Shop - CORE (Episode 4)": (1430, 1431, 1432, 1433, 1434),
            },
        }),

        "LAVA EXIT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "LAVA EXIT (Episode 4) - Central Lightning Shooter": 440,
            "LAVA EXIT (Episode 4) - Lava Bubble Wave 1": 441,
            "LAVA EXIT (Episode 4) - Lava Bubble Wave 2": 442,
            "LAVA EXIT (Episode 4) - DESERTRUN Warp Orb": 443,
            "LAVA EXIT (Episode 4) - Final Lava Bubble Assault 1": 444,
            "LAVA EXIT (Episode 4) - Final Lava Bubble Assault 2": 445,
            "LAVA EXIT (Episode 4) - Boss": 446,
            "Shop - LAVA EXIT (Episode 4)": (1440, 1441, 1442, 1443, 1444),
        }),

        "DESERTRUN (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "DESERTRUN (Episode 4) - Afterburner Smooth Flying": 450,
            "DESERTRUN (Episode 4) - Ending Slalom 1": 451,
            "DESERTRUN (Episode 4) - Ending Slalom 2": 452,
            "DESERTRUN (Episode 4) - Ending Slalom 3": 453,
            "DESERTRUN (Episode 4) - Ending Slalom 4": 454,
            "DESERTRUN (Episode 4) - Ending Slalom 5": 455,
            "Shop - DESERTRUN (Episode 4)": (1450, 1451, 1452, 1453, 1454),
        }),

        "SIDE EXIT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "SIDE EXIT (Episode 4) - Waving X-shaped Enemies 1": 460,
            "SIDE EXIT (Episode 4) - Third Laser Shooter": 461,
            "SIDE EXIT (Episode 4) - Waving X-shaped Enemies 2": 462,
            "SIDE EXIT (Episode 4) - Final Laser Shooter Onslaught": 463,
            "Shop - SIDE EXIT (Episode 4)": (1460, 1461, 1462, 1463, 1464),
        }),

        "?TUNNEL? (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "?TUNNEL? (Episode 4) @ Destroy Boss": {
                "?TUNNEL? (Episode 4) - Boss": 470,
                "Shop - ?TUNNEL? (Episode 4)": (1470, 1471, 1472, 1473, 1474),
            },
        }),

        "ICE EXIT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "ICE EXIT (Episode 4) - ICESECRET Orb": 480,

            "ICE EXIT (Episode 4) @ Destroy Boss": {
                "ICE EXIT (Episode 4) - Boss": 481,
                "Shop - ICE EXIT (Episode 4)": (1480, 1481, 1482, 1483, 1484),
            },
        }),

        "ICESECRET (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "ICESECRET (Episode 4) - Large U-Ship Mini-Boss": 490,
            "ICESECRET (Episode 4) - MegaLaser Dual Drop": 491,
            "ICESECRET (Episode 4) - Boss": 492,
            "Shop - ICESECRET (Episode 4)": (1490, 1491, 1492, 1493, 1494),
        }),

        "HARVEST (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "HARVEST (Episode 4) - High Speed V Formation": 500,
            "HARVEST (Episode 4) - Shooter with Gravity Orbs": 501,
            "HARVEST (Episode 4) - Shooter with Clone Bosses": 502,
            "HARVEST (Episode 4) - Grounded Shooter 1": 503,
            "HARVEST (Episode 4) - Grounded Shooter 2": 504,
            "HARVEST (Episode 4) - Ending V Formation": 505,

            "HARVEST (Episode 4) @ Destroy Boss": {
                "HARVEST (Episode 4) - Boss": 506,
                "Shop - HARVEST (Episode 4)": (1500, 1501, 1502, 1503, 1504),
            },
        }),

        "UNDERDELI (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "UNDERDELI (Episode 4) - Boss's Red Eye": 510,
            "UNDERDELI (Episode 4) - Boss": 511,
            "Shop - UNDERDELI (Episode 4)": (1510, 1511, 1512, 1513, 1514),
        }),

        "APPROACH (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "Shop - APPROACH (Episode 4)": (1520, 1521, 1522, 1523, 1524),
        }),

        "SAVARA IV (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "SAVARA IV (Episode 4) - Early Breakaway V Formation": 530,
            "SAVARA IV (Episode 4) - First Drunk Plane": 531,
            "SAVARA IV (Episode 4) - Last Breakaway V Formation": 532,
            "SAVARA IV (Episode 4) - Second Drunk Plane": 533,
            "SAVARA IV (Episode 4) - Boss": 534,
            "Shop - SAVARA IV (Episode 4)": (1530, 1531, 1532, 1533, 1534),
        }),

        "DREAD-NOT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "DREAD-NOT (Episode 4) @ Defeat Boss": {
                "DREAD-NOT (Episode 4) - Boss": 540,
                "Shop - DREAD-NOT (Episode 4)": (1540, 1541, 1542, 1543, 1544),
            }
        }),

        "EYESPY (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "EYESPY (Episode 4) - Green Exploding Eye 1": 550,
            "EYESPY (Episode 4) - Blue Splitting Eye 1": 551,
            "EYESPY (Episode 4) - Green Exploding Eye 2": 552,
            "EYESPY (Episode 4) - Blue Splitting Eye 2": 553,
            "EYESPY (Episode 4) - Blue Splitting Eye 3": 554,
            "EYESPY (Episode 4) - Billiard Break Secret": 555,
            "EYESPY (Episode 4) - Boss": 556,
            "Shop - EYESPY (Episode 4)": (1550, 1551, 1552, 1553, 1554),
        }),

        "BRAINIAC (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "BRAINIAC (Episode 4) - Turret-Guarded Pathway": 560,
            "BRAINIAC (Episode 4) - Mid-Boss 1": 561,
            "BRAINIAC (Episode 4) - Mid-Boss 2": 562,
            "BRAINIAC (Episode 4) - Boss": 563,
            "Shop - BRAINIAC (Episode 4)": (1560, 1561, 1562, 1563, 1564),
        }),

        "NOSE DRIP (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, locations={
            "NOSE DRIP (Episode 4) @ Destroy Boss": {
                "NOSE DRIP (Episode 4) - Boss": 570,
                "Shop - NOSE DRIP (Episode 4)": (1570, 1571, 1572, 1573, 1574),
                # Event: "Episode 4 (An End To Fate) Complete"
            },
        }, shop_setups=["S", "W", "Y"]),

        # =============================================================================================
        # EPISODE 5 - HAZUDRA FODDER
        # =============================================================================================

        "ASTEROIDS (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "ASTEROIDS (Episode 5) - Ship 1": 580,
            "ASTEROIDS (Episode 5) - Railgunner 1": 581,
            "ASTEROIDS (Episode 5) - Ship": 582,
            "ASTEROIDS (Episode 5) - Railgunner 2": 583,
            "ASTEROIDS (Episode 5) - Ship 2": 584,
            "ASTEROIDS (Episode 5) - Boss": 585,
            "Shop - ASTEROIDS (Episode 5)": (1580, 1581, 1582, 1583, 1584),
        }),

        "AST ROCK (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "Shop - AST ROCK (Episode 5)": (1590, 1591, 1592, 1593, 1594),
        }),

        "MINERS (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "MINERS (Episode 5) - Boss": 600,
            "Shop - MINERS (Episode 5)": (1600, 1601, 1602, 1603, 1604),
        }),

        "SAVARA (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "SAVARA (Episode 5) - Green Vulcan Plane 1": 610,
            "SAVARA (Episode 5) - Huge Plane Formation": 611,
            "SAVARA (Episode 5) - Surrounded Vulcan Plane": 612,
            "SAVARA (Episode 5) - Unknown 1": 613,
            "SAVARA (Episode 5) - Unknown 2": 614,

            "SAVARA (Episode 5) @ Destroy Boss": {
                "SAVARA (Episode 5) - Boss": 615,
                "Shop - SAVARA (Episode 5)": (1610, 1611, 1612, 1613, 1614),
            },
        }),

        "CORAL (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "CORAL (Episode 5) @ Destroy Boss": {
                "CORAL (Episode 5) - Boss": 620,
                "Shop - CORAL (Episode 5)": (1620, 1621, 1622, 1623, 1624),
            },
        }),

        # Remains here for possible future use (corresponds to unused level)
#       "CANYONRUN (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
#           "Shop - CANYONRUN (Episode 5)": (1630, 1631, 1632, 1633, 1634),
#       })

        "STATION (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "STATION (Episode 5) - Pulse-Turret 1": 640,
            "STATION (Episode 5) - Pulse-Turret 2": 641,
            "STATION (Episode 5) - Pulse-Turret 3": 642,
            "STATION (Episode 5) - Spike from Rear Corner 1": 643,
            "STATION (Episode 5) - Pulse-Turret 4": 644,
            "STATION (Episode 5) - Spike from Rear Corner 2": 645,
            "STATION (Episode 5) - Repulsor Crane": 646,
            "STATION (Episode 5) - Pulse-Turret 5": 647,
            "STATION (Episode 5) - Pulse-Turret 6": 648,

            "STATION (Episode 5) @ Pass Boss (can time out)": {
                "STATION (Episode 5) - Boss": 649,
                "Shop - STATION (Episode 5)": (1640, 1641, 1642, 1643, 1644),
            },
        }),

        "FRUIT (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, locations={
            "FRUIT (Episode 5) - Apple UFO Wave": 650,

            "FRUIT (Episode 5) @ Destroy Boss": {
                "FRUIT (Episode 5) - Boss": 651,
                "Shop - FRUIT (Episode 5)": (1650, 1651, 1652, 1653, 1654),
                # Event: "Episode 5 (Hazudra Fodder) Complete"
            }
        }, shop_setups=["W"]),
    }

    # Events for game completion
    events: Dict[str, str] = {
        "Episode 1 (Escape) Complete":           "ASSASSIN (Episode 1)",
        "Episode 2 (Treachery) Complete":        "GRYPHON (Episode 2)",
        "Episode 3 (Mission: Suicide) Complete": "FLEET (Episode 3)",
        "Episode 4 (An End to Fate) Complete":   "NOSE DRIP (Episode 4)",
        "Episode 5 (Hazudra Fodder) Complete":   "FRUIT (Episode 5)",
    }

    @classmethod
    def get_location_name_to_id(cls, base_id: int) -> Dict[str, int]:
        all_locs = {}
        for region in cls.level_regions.values():
            all_locs.update(region.get_locations(base_id=base_id))
        return all_locs

    @classmethod
    def get_location_groups(cls) -> Dict[str, Set[str]]:
        # Bring all locations in a level, shop included, into a region named after the level.
        return {level: region.get_location_names() for (level, region) in cls.level_regions.items()}

    secret_descriptions: Dict[str, str] = {
        "TYRIAN (Episode 1) - First U-Ship Secret": """
            Wait for the first U-Ship in the level to start heading upwards.
        """,
        "TYRIAN (Episode 1) - HOLES Warp Orb": """
            Destroy every wave of U-Ships at the start of the level.
            The first spinner formation after you approach the enemy platforms will then yield this item.
        """,
        "TYRIAN (Episode 1) - Tank Turn-and-fire Secret": """
            At the section with four tanks driving across two parallel strips of road, wait for the rightmost tank
            to get into position, turn, and start firing.
        """,
        "TYRIAN (Episode 1) - SOH JIN Warp Orb": """
            Destry none of the U-Ships at the start of the level, except for the one that drops the
            "First U-Ship Secret" item.
            Just before the boss flies in, there will be an additional ship that will give this item.
        """,
        "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1": """
            Wait for the first tank you see to turn around and start firing at you.
        """,
        "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2": """
            In the second squadron of tanks, two tanks will turn around and start heading upwards after a short time.
            One of those two tanks will yield this item if you wait until it turns around and starts firing again.
        """,
        "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret": """
            As you're approaching the Tank Assault section, destroy the rightmost tank as it turns onto the
            rightmost road, but before it goes offscreen and turns around to fire at you.
        """,
        "ASTEROID? (Episode 1) - WINDY Warp Orb": """
            Destroy the platform on the left side of the screen next to the four "welcoming" launchers,
            then destroy the two heavy missile launchers that spawn afterwards.
            After the miniboss launcher, an additional tank will spawn containing this item.
        """,
        "ASTEROID? (Episode 1) - Quick Shot 1": """
            Destroy the two ships after the miniboss launcher within 1 1/2 seconds of them spawning.
        """,
        "TORM (Episode 2) - Ship Fleeing Dragon Secret": """
            One plane will stick around long enough for a dragon to fly towards it. Shoot it as it starts to flee.
        """,
        "SAWBLADES (Episode 3) - SuperCarrot Secret Drop": """
            Throughout the level, carrot-shaped ships will fly towards you.
            Destroy all of them, and the last will yield this item.
        """,
        "TYRIAN X (Episode 3) - First U-Ship Secret": """
            Wait for the first pair of U-Ship formations to start heading upwards.
        """,
        "TYRIAN X (Episode 3) - Second Secret, Same as the First": """
            As with the first U-Ship secret, wait for the second pair of U-Ship formations to start heading upwards.
        """,
        "SURFACE (Episode 4) - WINDY Warp Orb": """
            Destroy all four waves of ships flying in a V formation at the start of the level.
            One of the ships flying through arches later on will then yield this item.
        """,
        "DESERTRUN (Episode 4) - Afterburner Smooth Flying": """
            Fly through all the arches in the Afterburner section. The oasis will then throw out this item.
        """,
        "EYESPY (Episode 4) - Billiard Break Secret": """
            Near the end of the level, eyes will line up in a formation that resembles a rack of 9-ball, and then
            be hit by a green eye that breaks them up.
            Wait until the eyes get broken up, and the topmost one will yield this item.
        """
    }
