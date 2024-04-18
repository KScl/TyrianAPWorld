# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import TYPE_CHECKING, Dict, List, Set, Tuple

from BaseClasses import LocationProgressType as LP

from .items import Episode

if TYPE_CHECKING:
    from . import TyrianWorld, TyrianLocation

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
        "Z": (65535, 65536,   1) # Always max shop price
    }

    episode: Episode
    locations: List[str]
    base_id: int # Should match ID in lvlmast.c
    shop_setups: List[str] # See base_shop_setups_list above

    def __init__(self, episode: Episode, base_id: int, locations: List[str],
          shop_setups: List[str] = ["F", "H", "K", "L"]):
        self.episode = episode
        self.base_id = base_id
        self.locations = locations
        self.shop_setups = shop_setups

    # Gets a random price based on this level's shop setups, and assigns it to the locaton.
    # Also changes location to prioritized/excluded automatically based on the setup rolled.
    def set_random_shop_price(self, world: "TyrianWorld", location: "TyrianLocation") -> None:
        setup_choice = world.random.choice(self.shop_setups)
        if len(setup_choice) > 1:
            location.progress_type = LP.PRIORITY if setup_choice[-1] == "!" else LP.EXCLUDED
        location.shop_price = min(world.random.randrange(*self.base_shop_setup_list[setup_choice[0]]), 65535)


class LevelLocationData:

    level_regions: Dict[str, LevelRegion] = {

        # =============================================================================================
        # EPISODE 1 - ESCAPE
        # =============================================================================================

        "TYRIAN (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=0, locations=[
            # The hard variant of Tyrian is similarly designed, just with more enemies, so it shares checks.
            "TYRIAN (Episode 1) - First U-Ship Secret",
            "TYRIAN (Episode 1) - Early Spinner Formation",
            "TYRIAN (Episode 1) - Lander near BUBBLES Warp Rock",
            "TYRIAN (Episode 1) - BUBBLES Warp Rock",
            "TYRIAN (Episode 1) - HOLES Warp Orb",
            "TYRIAN (Episode 1) - Ships Between Platforms",
            "TYRIAN (Episode 1) - First Line of Tanks",
            "TYRIAN (Episode 1) - Tank Turn-and-fire Secret",
            "TYRIAN (Episode 1) - SOH JIN Warp Orb",
            "TYRIAN (Episode 1) - Boss",
        ], shop_setups=["A#", "B", "C", "D", "D", "E", "F", "F", "G", "I!"]),

        "BUBBLES (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=10, locations=[
            "BUBBLES (Episode 1) - Orbiting Bubbles",
            "BUBBLES (Episode 1) - Shooting Bubbles",
            "BUBBLES (Episode 1) - Coin Rain 1",
            "BUBBLES (Episode 1) - Coin Rain 2",
            "BUBBLES (Episode 1) - Coin Rain 3",
            "BUBBLES (Episode 1) - Final Bubble Line",
        ], shop_setups=["C", "D", "E", "G", "I"]),

        "HOLES (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=20, locations=[
            "HOLES (Episode 1) - U-Ship Formation 1",
            "HOLES (Episode 1) - U-Ship Formation 2",
            "HOLES (Episode 1) - Lander after Spinners",
            "HOLES (Episode 1) - Boss Ship Fly-By 1",
            "HOLES (Episode 1) - U-Ships after Boss Fly-By",
            "HOLES (Episode 1) - Boss Ship Fly-By 2",
            "HOLES (Episode 1) - Before Speed Up Section",
        ], shop_setups=["C", "D", "D", "E", "F", "F", "H"]),

        "SOH JIN (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=30, locations=[
            "SOH JIN (Episode 1) - Starting Alcove",
            "SOH JIN (Episode 1) - Walled-in Orb Launcher",
            "SOH JIN (Episode 1) - Triple Diagonal Launchers",
            "SOH JIN (Episode 1) - Checkerboard Pattern",
            "SOH JIN (Episode 1) - Triple Orb Launchers",
            "SOH JIN (Episode 1) - Double Orb Launcher Line",
            "SOH JIN (Episode 1) - Next to Double Point Items",
        ], shop_setups=["F", "H", "H", "J", "J", "T"]),

        "ASTEROID1 (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=40, locations=[
            "ASTEROID1 (Episode 1) - Shield Ship in Asteroid Field",
            "ASTEROID1 (Episode 1) - Railgunner 1",
            "ASTEROID1 (Episode 1) - Railgunner 2",
            "ASTEROID1 (Episode 1) - Railgunner 3",
            "ASTEROID1 (Episode 1) - ASTEROID? Warp Orb",
            "ASTEROID1 (Episode 1) - Maneuvering Missiles",
            "ASTEROID1 (Episode 1) - Boss",
        ], shop_setups=["E", "F", "F", "F", "G"]),

        "ASTEROID2 (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=50, locations=[
            "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1",
            "ASTEROID2 (Episode 1) - First Tank Squadron",
            "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2",
            "ASTEROID2 (Episode 1) - Second Tank Squadron",
            "ASTEROID2 (Episode 1) - Tank Bridge",
            "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret",
            "ASTEROID2 (Episode 1) - MINEMAZE Warp Orb",
            "ASTEROID2 (Episode 1) - Boss",
        ], shop_setups=["E", "F", "F", "F", "G"]),

        "ASTEROID? (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=60, locations=[
            "ASTEROID? (Episode 1) - Welcoming Launchers 1",
            "ASTEROID? (Episode 1) - Welcoming Launchers 2",
            "ASTEROID? (Episode 1) - Boss Launcher",
            "ASTEROID? (Episode 1) - WINDY Warp Orb",
            "ASTEROID? (Episode 1) - Quick Shot 1",
            "ASTEROID? (Episode 1) - Quick Shot 2",
        ], shop_setups=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]),

        "MINEMAZE (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=70, locations=[
            "MINEMAZE (Episode 1) - Starting Gate",
            "MINEMAZE (Episode 1) - Lone Orb",
            "MINEMAZE (Episode 1) - Right Path Gate",
            "MINEMAZE (Episode 1) - That's not a Strawberry",
            "MINEMAZE (Episode 1) - ASTEROID? Warp Orb",
            "MINEMAZE (Episode 1) - Ships Behind Central Gate",
        ], shop_setups=["E", "F", "F", "F", "G"]),

        "WINDY (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=80, locations=[
            "WINDY (Episode 1) - Central Question Mark",
        ], shop_setups=["F", "G", "I"]),

        "SAVARA (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=90, locations=[
            # This is the variant of Savara on Easy or Medium.
            "SAVARA (Episode 1) - White Formation Leader 1",
            "SAVARA (Episode 1) - White Formation Leader 2",
            "SAVARA (Episode 1) - Green Plane Line",
            "SAVARA (Episode 1) - Brown Plane Breaking Formation",
            "SAVARA (Episode 1) - Huge Plane, Speeds By",
            "SAVARA (Episode 1) - Vulcan Plane",
            "SAVARA (Episode 1) - Boss",
        ], shop_setups=["E", "H", "L", "P"]),

        "SAVARA II (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=100, locations=[
            # This is the variant of Savara on Hard or above.
            "SAVARA II (Episode 1) - Launched Planes 1",
            "SAVARA II (Episode 1) - Green Plane Sequence 1",
            "SAVARA II (Episode 1) - Large Plane Amidst Turrets",
            "SAVARA II (Episode 1) - Vulcan Planes Near Blimp",
            "SAVARA II (Episode 1) - Launched Planes 2",
            "SAVARA II (Episode 1) - Green Plane Sequence 2",
            "SAVARA II (Episode 1) - Boss",
        ], shop_setups=["E", "H", "L", "P"]),

        "BONUS (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=110, locations=[
            # Empty location list
        ], shop_setups=["J", "J", "J", "K", "K", "L"]),

        "MINES (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=120, locations=[
            "MINES (Episode 1) - Regular Spinning Orbs",
            "MINES (Episode 1) - Blue Mine",
            "MINES (Episode 1) - Repulsor Spinning Orbs",
            "MINES (Episode 1) - Absolutely Free",
            "MINES (Episode 1) - But Wait There's More",
        ], shop_setups=["E", "F", "G", "H", "J"]),

        "DELIANI (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=130, locations=[
            "DELIANI (Episode 1) - First Turret Wave 1",
            "DELIANI (Episode 1) - First Turret Wave 2",
            "DELIANI (Episode 1) - Tricky Rail Turret",
            "DELIANI (Episode 1) - Second Turret Wave 1",
            "DELIANI (Episode 1) - Second Turret Wave 2",
            "DELIANI (Episode 1) - Ambush",
            "DELIANI (Episode 1) - Last Cross Formation",
            "DELIANI (Episode 1) - Boss",
        ], shop_setups=["K", "M", "O", "P", "Q"]),

        "SAVARA V (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=140, locations=[
            "SAVARA V (Episode 1) - Green Plane Sequence",
            "SAVARA V (Episode 1) - Flying Between Blimps",
            "SAVARA V (Episode 1) - Brown Plane Sequence",
            "SAVARA V (Episode 1) - Flying Alongside Green Planes",
            "SAVARA V (Episode 1) - Super Blimp",
            "SAVARA V (Episode 1) - Mid-Boss",
            "SAVARA V (Episode 1) - Boss"
        ], shop_setups=["E", "H", "L", "P"]),

        "ASSASSIN (Episode 1)": LevelRegion(episode=Episode.Escape, base_id=150, locations=[
            "ASSASSIN (Episode 1) - Boss",
        ], shop_setups=["S"]),
        # Event: "Episode 1 (Escape) Complete"

        # =============================================================================================
        # EPISODE 2 - TREACHERY
        # =============================================================================================

        "TORM (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=160, locations=[
            "TORM (Episode 2) - Jungle Ship V Formation 1",
            "TORM (Episode 2) - Ship Fleeing Dragon Secret",
            "TORM (Episode 2) - Excuse Me, You Dropped This",
            "TORM (Episode 2) - Jungle Ship V Formation 2",
            "TORM (Episode 2) - Jungle Ship V Formation 3",
            "TORM (Episode 2) - Undocking Jungle Ship",
            "TORM (Episode 2) - Boss Ship Fly-By",
            "TORM (Episode 2) - Boss",
        ], shop_setups=["A#", "B", "C", "D", "D", "E", "F", "F", "G", "I!"]),

        "GYGES (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=170, locations=[
            "GYGES (Episode 2) - Circled Shapeshifting Turret 1",
            "GYGES (Episode 2) - Wide Waving Worm",
            "GYGES (Episode 2) - Orbsnake",
            "GYGES (Episode 2) - GEM WAR Warp Orb",
            "GYGES (Episode 2) - Circled Shapeshifting Turret 2",
            "GYGES (Episode 2) - Last Set of Worms",
            "GYGES (Episode 2) - Boss",
        ]),

        "BONUS 1 (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=180, locations=[
            # Empty location list
        ]),

        "ASTCITY (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=190, locations=[
            "ASTCITY (Episode 2) - Shield Ship V Formation 1",
            "ASTCITY (Episode 2) - Shield Ship V Formation 2",
            "ASTCITY (Episode 2) - Plasma Turrets Going Uphill",
            "ASTCITY (Episode 2) - Warehouse 92",
            "ASTCITY (Episode 2) - Shield Ship V Formation 3",
            "ASTCITY (Episode 2) - Shield Ship Canyon 1",
            "ASTCITY (Episode 2) - Shield Ship Canyon 2",
            "ASTCITY (Episode 2) - Shield Ship Canyon 3",
            "ASTCITY (Episode 2) - MISTAKES Warp Orb",
            "ASTCITY (Episode 2) - Ending Turret Group",
        ]),

        "BONUS 2 (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=200, locations=[
            # Empty location list
        ]),

        "GEM WAR (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=210, locations=[
            "GEM WAR (Episode 2) - Red Gem Leader 1",
            "GEM WAR (Episode 2) - Red Gem Leader 2",
            "GEM WAR (Episode 2) - Red Gem Leader 3",
            "GEM WAR (Episode 2) - Red Gem Leader 4",
            "GEM WAR (Episode 2) - Blue Gem Boss 1",
            "GEM WAR (Episode 2) - Blue Gem Boss 2",
        ]),

        "MARKERS (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=220, locations=[
            "MARKERS (Episode 2) - Right Path Turret",
            "MARKERS (Episode 2) - Persistent Mine-Layer",
            "MARKERS (Episode 2) - Car Destroyer Secret",
            "MARKERS (Episode 2) - Left Path Turret",
            "MARKERS (Episode 2) - End Section Turret",
        ]),

        "MISTAKES (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=230, locations=[
            "MISTAKES (Episode 2) - Start - Trigger Enemy 1",
            "MISTAKES (Episode 2) - Start - Trigger Enemy 2",
            "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 1",
            "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 2",
            "MISTAKES (Episode 2) - Claws - Trigger Enemy 1",
            "MISTAKES (Episode 2) - Claws - Trigger Enemy 2",
            "MISTAKES (Episode 2) - Drills - Trigger Enemy 1",
            "MISTAKES (Episode 2) - Drills - Trigger Enemy 2",
            "MISTAKES (Episode 2) - Super Bubble Spawner",
            "MISTAKES (Episode 2) - Anti-Softlock",
        ], shop_setups=["B", "D", "J", "K", "L", "O", "V", "Z!"]),

        "SOH JIN (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=240, locations=[
            "SOH JIN (Episode 2) - Sinusoidal Missile Wave",
            "SOH JIN (Episode 2) - Second Missile Ship Set",
            "SOH JIN (Episode 2) - Paddle Destruction 1",
            "SOH JIN (Episode 2) - Paddle Destruction 2",
            "SOH JIN (Episode 2) - Last Missile Ship Set",
            "SOH JIN (Episode 2) - Boss Orbs 1",
            "SOH JIN (Episode 2) - Boss Orbs 2",
        ]),

        "BOTANY A (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=250, locations=[
            "BOTANY A (Episode 2) - Retreating Mobile Turret",
            "BOTANY A (Episode 2) - End of Path Secret 1",
            "BOTANY A (Episode 2) - Mobile Turret Approaching Head-On",
            "BOTANY A (Episode 2) - End of Path Secret 2",
            "BOTANY A (Episode 2) - Green Ship Pincer",
            "BOTANY A (Episode 2) - Boss",
        ]),

        "BOTANY B (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=260, locations=[
            "BOTANY B (Episode 2) - Starting Platform Sensor",
            "BOTANY B (Episode 2) - Main Platform Sensor 1",
            "BOTANY B (Episode 2) - Main Platform Sensor 2",
            "BOTANY B (Episode 2) - Main Platform Sensor 3",
            "BOTANY B (Episode 2) - Super-Turret on Bridge",
            "BOTANY B (Episode 2) - Boss",
        ]),

        "GRYPHON (Episode 2)": LevelRegion(episode=Episode.Treachery, base_id=270, locations=[
            "GRYPHON (Episode 2) - Pulse-Turret Wave Mid-Spikes",
            "GRYPHON (Episode 2) - Swooping Pulse-Turrets",
            "GRYPHON (Episode 2) - Sweeping Pulse-Turrets",
            "GRYPHON (Episode 2) - Spike From Behind",
            "GRYPHON (Episode 2) - Breaking Formation 1",
            "GRYPHON (Episode 2) - Breaking Formation 2",
            "GRYPHON (Episode 2) - Breaking Formation 3",
            "GRYPHON (Episode 2) - Breaking Formation 4",
            "GRYPHON (Episode 2) - Breaking Formation 5",
            "GRYPHON (Episode 2) - Boss",
        ]),
        # Event: "Episode 2 (Treachery) Complete"

        # =============================================================================================
        # EPISODE 3 - MISSION: SUICIDE
        # =============================================================================================

        "GAUNTLET (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=280, locations=[
        ]),

        "IXMUCANE (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=290, locations=[
            "IXMUCANE (Episode 3) - Boss",
        ]),

        "BONUS (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=300, locations=[
            "BONUS (Episode 3) - Lone Turret 1",
            "BONUS (Episode 3) - Behind Onslaught 1",
            "BONUS (Episode 3) - Behind Onslaught 2",
            "BONUS (Episode 3) - Lone Turret 2",
            "BONUS (Episode 3) - Sonic Wave Hell Turret",
        ], shop_setups=["G", "G"]),

        "STARGATE (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=310, locations=[
            "STARGATE (Episode 3) - The Bubbleway",
            "STARGATE (Episode 3) - First Bubble Spawner",
            "STARGATE (Episode 3) - AST. CITY Warp Orb 1",
            "STARGATE (Episode 3) - AST. CITY Warp Orb 2",
            "STARGATE (Episode 3) - SAWBLADES Warp Orb 1",
            "STARGATE (Episode 3) - SAWBLADES Warp Orb 2",
            "STARGATE (Episode 3) - Super Bubble Spawner",
        ]),

        "AST. CITY (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=320, locations=[
        ]),

        "SAWBLADES (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=330, locations=[
            "SAWBLADES (Episode 3) - SuperCarrot Drop",
        ]),

        "CAMANIS (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=340, locations=[
            "CAMANIS (Episode 3) - Ice Spitter 1",
            "CAMANIS (Episode 3) - Snowfield Ship Assault",
            "CAMANIS (Episode 3) - Ice Spitter 2",
            "CAMANIS (Episode 3) - Roaming Snowball",
            "CAMANIS (Episode 3) - Ice Spitter 3",
            "CAMANIS (Episode 3) - Boss",
        ]),

        "MACES (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=350, locations=[
            "MACES (Episode 3) - Third Mace's Path",
            "MACES (Episode 3) - Sixth Mace's Path",
            "MACES (Episode 3) - A Brief Reprieve 1",
            "MACES (Episode 3) - A Brief Reprieve 2",
            "MACES (Episode 3) - A Brief Reprieve 3",
        ]),

        "TYRIAN X (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=360, locations=[
            "TYRIAN X (Episode 3) - First U-Ship Secret",
            "TYRIAN X (Episode 3) - Second Secret, Same as the First",
            "TYRIAN X (Episode 3) - Side-flying Ship Near Landers",
            "TYRIAN X (Episode 3) - Platform Spinner Sequence",
            "TYRIAN X (Episode 3) - Ships Between Platforms",
            "TYRIAN X (Episode 3) - Tank Near Purple Structure",
            "TYRIAN X (Episode 3) - Tank Turn-and-fire Secret",
            "TYRIAN X (Episode 3) - Boss",
        ]),

        "SAVARA Y (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=370, locations=[
            "SAVARA Y (Episode 3) - Boss",
        ]),

        "NEW DELI (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=380, locations=[
            "NEW DELI (Episode 3) - First Turret Wave 1",
            "NEW DELI (Episode 3) - First Turret Wave 2",
            "NEW DELI (Episode 3) - Second Turret Wave 1",
            "NEW DELI (Episode 3) - Second Turret Wave 2",
            "NEW DELI (Episode 3) - Second Turret Wave 3",
            "NEW DELI (Episode 3) - Second Turret Wave 4",
            "NEW DELI (Episode 3) - Boss",
        ]),

        "FLEET (Episode 3)": LevelRegion(episode=Episode.MissionSuicide, base_id=390, locations=[
            "FLEET (Episode 3) - Attractor Crane 1",
            "FLEET (Episode 3) - Enemy 1",
            "FLEET (Episode 3) - Enemy 2",
            "FLEET (Episode 3) - Attractor Crane 2",
            "FLEET (Episode 3) - Boss",
        ]),
        # Event: "Episode 3 (Mission: Suicide) Complete"

        # =============================================================================================
        # EPISODE 4 - AN END TO FATE
        # =============================================================================================

        "SURFACE (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=400, locations=[
            "SURFACE (Episode 4) - WINDY Warp Orb",
            "SURFACE (Episode 4) - Triple V Formation",
        ]),

        "WINDY (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=410, locations=[
        ]),

        "LAVA RUN (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=420, locations=[
            "LAVA RUN (Episode 4) - Second Laser Shooter",
            "LAVA RUN (Episode 4) - Left Side Missile Launcher",
            "LAVA RUN (Episode 4) - Boss",
        ]),

        "CORE (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=430, locations=[
            "CORE (Episode 4) - Boss",
        ]),

        "LAVA EXIT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=440, locations=[
            "LAVA EXIT (Episode 4) - Central Lightning Shooter",
            "LAVA EXIT (Episode 4) - Lava Bubble Wave 1",
            "LAVA EXIT (Episode 4) - Lava Bubble Wave 2",
            "LAVA EXIT (Episode 4) - DESERTRUN Warp Orb",
            "LAVA EXIT (Episode 4) - Final Lava Bubble Assault 1",
            "LAVA EXIT (Episode 4) - Final Lava Bubble Assault 2",
            "LAVA EXIT (Episode 4) - Boss",
        ]),

        "DESERTRUN (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=450, locations=[
            "DESERTRUN (Episode 4) - Afterburner Smooth Flying",
            "DESERTRUN (Episode 4) - Ending Slalom 1",
            "DESERTRUN (Episode 4) - Ending Slalom 2",
            "DESERTRUN (Episode 4) - Ending Slalom 3",
            "DESERTRUN (Episode 4) - Ending Slalom 4",
            "DESERTRUN (Episode 4) - Ending Slalom 5",
        ]),

        "SIDE EXIT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=460, locations=[
            "SIDE EXIT (Episode 4) - Waving X-shaped Enemies 1",
            "SIDE EXIT (Episode 4) - Third Laser Shooter",
            "SIDE EXIT (Episode 4) - Waving X-shaped Enemies 2",
            "SIDE EXIT (Episode 4) - Final Laser Shooter Onslaught",
        ]),

        "?TUNNEL? (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=470, locations=[
            "?TUNNEL? (Episode 4) - Boss",
        ]),

        "ICE EXIT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=480, locations=[
            "ICE EXIT (Episode 4) - ICESECRET Orb",
            "ICE EXIT (Episode 4) - Boss",
        ]),

        "ICESECRET (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=490, locations=[
            "ICESECRET (Episode 4) - Large U-Ship Mini-Boss",
            "ICESECRET (Episode 4) - MegaLaser Dual Drop",
            "ICESECRET (Episode 4) - Boss",
        ]),

        "HARVEST (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=500, locations=[
            "HARVEST (Episode 4) - High Speed V Formation",
            "HARVEST (Episode 4) - Shooter with Gravity Orbs",
            "HARVEST (Episode 4) - Shooter with Clone Bosses",
            "HARVEST (Episode 4) - Grounded Shooter 1",
            "HARVEST (Episode 4) - Grounded Shooter 2",
            "HARVEST (Episode 4) - Ending V Formation",
            "HARVEST (Episode 4) - Boss",
        ]),

        "UNDERDELI (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=510, locations=[
            "UNDERDELI (Episode 4) - Boss's Red Eye",
            "UNDERDELI (Episode 4) - Boss",
        ]),

        "APPROACH (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=520, locations=[
        ]),

        "SAVARA IV (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=530, locations=[
            "SAVARA IV (Episode 4) - Early Breakaway V Formation",
            "SAVARA IV (Episode 4) - First Drunk Plane",
            "SAVARA IV (Episode 4) - Last Breakaway V Formation",
            "SAVARA IV (Episode 4) - Second Drunk Plane",
            "SAVARA IV (Episode 4) - Boss",
        ]),

        "DREAD-NOT (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=540, locations=[
            "DREAD-NOT (Episode 4) - Boss",
        ]),

        "EYESPY (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=550, locations=[
            "EYESPY (Episode 4) - Green Exploding Eye 1",
            "EYESPY (Episode 4) - Blue Splitting Eye 1",
            "EYESPY (Episode 4) - Green Exploding Eye 2",
            "EYESPY (Episode 4) - Blue Splitting Eye 2",
            "EYESPY (Episode 4) - Blue Splitting Eye 3",
            "EYESPY (Episode 4) - Billiard Break Secret",
            "EYESPY (Episode 4) - Boss",
        ]),

        "BRAINIAC (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=560, locations=[
            "BRAINIAC (Episode 4) - Turret-Guarded Pathway",
            "BRAINIAC (Episode 4) - Mid-Boss 1",
            "BRAINIAC (Episode 4) - Mid-Boss 2",
            "BRAINIAC (Episode 4) - Boss",
        ]),

        "NOSE DRIP (Episode 4)": LevelRegion(episode=Episode.AnEndToFate, base_id=570, locations=[
            "NOSE DRIP (Episode 4) - Boss"
        ], shop_setups=["S"]),
        # Event: "Episode 4 (An End To Fate) Complete"

        # =============================================================================================
        # EPISODE 5 - HAZUDRA FODDER
        # =============================================================================================

        "ASTEROIDS (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=580, locations=[
            "ASTEROIDS (Episode 5) - Ship 1",
            "ASTEROIDS (Episode 5) - Railgunner 1",
            "ASTEROIDS (Episode 5) - Ship",
            "ASTEROIDS (Episode 5) - Railgunner 2",
            "ASTEROIDS (Episode 5) - Ship 2",
            "ASTEROIDS (Episode 5) - Boss",
        ]),

        "AST ROCK (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=590, locations=[
        ]),

        "MINERS (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=600, locations=[
            "MINERS (Episode 5) - Boss",
        ]),

        "SAVARA (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=610, locations=[
            "SAVARA (Episode 5) - Green Vulcan Plane 1",
            "SAVARA (Episode 5) - Large Plane Formation",
            "SAVARA (Episode 5) - Surrounded Vulcan Plane",
            "SAVARA (Episode 5) - Unknown 1",
            "SAVARA (Episode 5) - Unknown 2",
            "SAVARA (Episode 5) - Boss",
        ]),

        "CORAL (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=620, locations=[
            "CORAL (Episode 5) - Boss",
        ]),

        # Remains here for possible future use (corresponds to unused level)
        #"CANYONRUN (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=630, locations=[
        #])

        "STATION (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=640, locations=[
            "STATION (Episode 5) - Pulse-Turret 1",
            "STATION (Episode 5) - Pulse-Turret 2",
            "STATION (Episode 5) - Pulse-Turret 3",
            "STATION (Episode 5) - Spike from Rear Corner 1",
            "STATION (Episode 5) - Pulse-Turret 4",
            "STATION (Episode 5) - Spike from Rear Corner 2",
            "STATION (Episode 5) - Repulsor Crane",
            "STATION (Episode 5) - Pulse-Turret 5",
            "STATION (Episode 5) - Pulse-Turret 6",
            "STATION (Episode 5) - Boss",
        ]),

        "FRUIT (Episode 5)": LevelRegion(episode=Episode.HazudraFodder, base_id=650, locations=[
            "FRUIT (Episode 5) - Apple UFO Wave",
            "FRUIT (Episode 5) - Boss",
        ]),
        # Event: "Episode 5 (Hazudra Fodder) Complete" - Isn't this episode short???
    }

    shop_regions: Dict[str, int] = {name: region.base_id + 1000 for (name, region) in level_regions.items()}

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
        for (level, region) in cls.level_regions.items():
            all_locs.update({name: (base_id + region.base_id + i) for (name, i) in zip(region.locations, range(99))})

        for (level, start_id) in cls.shop_regions.items():
            all_locs.update({f"Shop - {level} - Item {i + 1}": (base_id + start_id + i) for i in range(5)})

        return all_locs

    @classmethod
    def get_location_groups(cls) -> Dict[str, Set[str]]:
        # Bring all locations in a level, shop included, into a region named after the level.
        all_groups = {level: {loc for loc in region.locations} for (level, region) in cls.level_regions.items()}
        for level in cls.shop_regions.keys():
            all_groups[level].update({f"Shop - {level} - Item {i + 1}" for i in range(5)})

        return all_groups

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
        "SAWBLADES (Episode 3) - SuperCarrot Drop": """
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
