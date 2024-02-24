# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import Optional, Dict, Union, List

from BaseClasses import Location
from BaseClasses import LocationProgressType as LP

from .Logic import RequirementList

class LevelRegion:
    # I don't really like the distribution I was getting from just doing random.triangular, so
    # instead we have multiple different types of random prices that can get generated, and we choose
    # which one we want randomly (based on the level we're generating it for).
    # Appending an "!" makes the shop location prioritized.
    # Appending a "#" makes the shop location excluded.
    base_shop_setup_list = {
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

    completion_reqs: Union[str, RequirementList, None]
    locations: Dict[str, Optional[RequirementList]]
    base_id: int # Should match ID in lvlmast.c
    shop_setups: List[str] # See base_shop_setups_list above

    def __init__(self, base_id: int, locations: Dict[str, Optional[RequirementList]],
          completion_reqs: Optional[RequirementList] = None,
          shop_setups: List[str] = ["F", "H", "K", "L"]):
        self.base_id = base_id
        self.locations = locations
        self.completion_reqs = completion_reqs
        self.shop_setups = shop_setups

    def items(self):
        return self.locations.items()

    def keys(self):
        return self.locations.keys()

    # Gets a random price based on this level's shop setups, and assigns it to the locaton.
    # Also changes location to prioritized/excluded automatically based on the setup rolled.
    def set_random_shop_price(self, world, location: Location) -> None:
        setup_choice = world.random.choice(self.shop_setups)
        if len(setup_choice) > 1:
            location.progress_type = LP.PRIORITY if setup_choice[-1] == "!" else LP.EXCLUDED
        location.shop_price = min(world.random.randrange(*self.base_shop_setup_list[setup_choice[0]]), 65535)


class LevelLocationData:

    # Note: completion_reqs="Boss" is a shorthand for "Whatever (levelname) - Boss requires"
    level_regions: Dict[str, LevelRegion] = {

        # =============================================================================================
        # EPISODE 1 - ESCAPE
        # =============================================================================================

        "TYRIAN (Episode 1)": LevelRegion(base_id=0, locations={
            # The hard variant of Tyrian is similarly designed, just with more enemies, so it shares checks.
            "TYRIAN (Episode 1) - First U-Ship Secret": None,
            "TYRIAN (Episode 1) - Early Spinner Formation": None,
            "TYRIAN (Episode 1) - Lander near BUBBLES Rock": None,
            "TYRIAN (Episode 1) - BUBBLES Warp Rock": None,
            "TYRIAN (Episode 1) - HOLES Warp Orb": None,
            "TYRIAN (Episode 1) - Ships Between Platforms": None,
            "TYRIAN (Episode 1) - First Line of Tanks": None,
            "TYRIAN (Episode 1) - Tank Turn-and-fire Secret": RequirementList(obscure=True),
            "TYRIAN (Episode 1) - SOH JIN Warp Orb": None,
            "TYRIAN (Episode 1) - Boss": None,
        }, completion_reqs=None,
        # Make sure to put especially low prices in the shops of all episode start levels
        shop_setups=["A#", "B", "C", "D", "D", "E", "F", "F", "G", "I!"]),

        "BUBBLES (Episode 1)": LevelRegion(base_id=10, locations={
            "BUBBLES (Episode 1) - Orbiting Bubbles": None,
            # Because of the way the bubbles surround this one, you need a surprising amount of power to kill it
            # (Or have the ability to pierce)
            "BUBBLES (Episode 1) - Shooting Bubbles": RequirementList(["SideHighDPS"], ["Power5"], ["AnyPierces"]),
            # These three are in a speed-up section
            "BUBBLES (Episode 1) - Coin Rain 1": RequirementList(["SideHighDPS"], ["Power3"]),
            "BUBBLES (Episode 1) - Coin Rain 2": RequirementList(["SideHighDPS"], ["Power3"]),
            "BUBBLES (Episode 1) - Coin Rain 3": RequirementList(["SideHighDPS"], ["Power3"]),
            "BUBBLES (Episode 1) - Final Bubble Line": None,
        }, completion_reqs=None,
        shop_setups=["C", "D", "E", "G", "I"]),

        "HOLES (Episode 1)": LevelRegion(base_id=20, locations={
            "HOLES (Episode 1) - U-Ship Formation 1": None,
            "HOLES (Episode 1) - U-Ship Formation 2": None,
            "HOLES (Episode 1) - Lander After Spinners": RequirementList(["Power3", "AnyDefensive"]),
            "HOLES (Episode 1) - U-Ships after Wandering Boss": RequirementList(["Power3", "AnyDefensive"]),
            "HOLES (Episode 1) - Before Speed Up Section": RequirementList(["Power3", "AnyDefensive"]),
        }, completion_reqs=RequirementList(["Power3", "AnyDefensive"]),
        shop_setups=["C", "D", "D", "E", "F", "F", "H"]),

        "SOH JIN (Episode 1)": LevelRegion(base_id=30, locations={
            "SOH JIN (Episode 1) - Starting Alcove": None,
            "SOH JIN (Episode 1) - Walled-in Orb Launcher": None,
            "SOH JIN (Episode 1) - Triple Diagonal Launchers": None,
            "SOH JIN (Episode 1) - Checkerboard Pattern": None,
            "SOH JIN (Episode 1) - Triple Orb Launchers": None,
            "SOH JIN (Episode 1) - Double Orb Launcher Line": None,
            "SOH JIN (Episode 1) - Next to Double Point Items": None,
        }, completion_reqs=None,
        shop_setups=["F", "H", "H", "J", "J", "T"]),

        "ASTEROID1 (Episode 1)": LevelRegion(base_id=40, locations={
            "ASTEROID1 (Episode 1) - Shield Ship in Asteroid Field": None,
            "ASTEROID1 (Episode 1) - Railgunner 1": None,
            "ASTEROID1 (Episode 1) - Railgunner 2": RequirementList(
                  ["Power2"], ["AnyHighDPS"], ["AnyDefensive"]),
            "ASTEROID1 (Episode 1) - Railgunner 3": RequirementList(
                  ["Power2"], ["AnyHighDPS"], ["AnyDefensive"]),
            "ASTEROID1 (Episode 1) - ASTEROID? Warp Orb": RequirementList(
                  ["Power2"], ["AnyHighDPS"], ["AnyDefensive"]),
            "ASTEROID1 (Episode 1) - Maneuvering Missiles": RequirementList(
                  ["Power2"], ["AnyHighDPS"], ["AnyDefensive"]),
            "ASTEROID1 (Episode 1) - Boss": RequirementList(
                  ["Power2"], ["AnyHighDPS"], ["AnyDefensive"]),
        }, completion_reqs="Boss",
        shop_setups=["E", "F", "F", "F", "G"]),

        "ASTEROID2 (Episode 1)": LevelRegion(base_id=50, locations={
            "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1": None, # Game's hints tell you about this one
            "ASTEROID2 (Episode 1) - First Tank Squadron": RequirementList(["Power2"], ["AnyHighDPS"]),
            "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2": RequirementList(
                  ["Power2"], ["AnyHighDPS"], obscure=True),
            "ASTEROID2 (Episode 1) - Second Tank Squadron": RequirementList(["Power2"], ["AnyHighDPS"]),
            "ASTEROID2 (Episode 1) - Tank Bridge": RequirementList(["Power2"], ["AnyHighDPS"]),
            "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret": RequirementList(
                  ["Power2"], ["AnyHighDPS"], obscure=True),
            "ASTEROID2 (Episode 1) - MINEMAZE Warp Orb": RequirementList(["Power2"], ["AnyHighDPS"]),
            "ASTEROID2 (Episode 1) - Boss": RequirementList(["Power2"], ["AnyHighDPS"]),
        }, completion_reqs="Boss",
        shop_setups=["E", "F", "F", "F", "G"]),

        "ASTEROID? (Episode 1)": LevelRegion(base_id=60, locations={
            "ASTEROID? (Episode 1) - Welcoming Launchers 1": RequirementList(["Power4", "Generator2"]),
            "ASTEROID? (Episode 1) - Welcoming Launchers 2": RequirementList(["Power4", "Generator2"]),
            "ASTEROID? (Episode 1) - Boss Launcher": RequirementList(["Power4", "Generator2"]),
            "ASTEROID? (Episode 1) - WINDY Warp Orb": RequirementList(["Power4", "Generator2"], obscure=True),

            "ASTEROID? (Episode 1) - Quick Shot 1": RequirementList(
                  ["FrontHighDPS", "Power7", "Generator3"]),
            "ASTEROID? (Episode 1) - Quick Shot 2": RequirementList(
                  ["FrontHighDPS", "Power7", "Generator3"])
        }, completion_reqs=RequirementList(["Power4", "Generator2"]),
        shop_setups=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]),

        "MINEMAZE (Episode 1)": LevelRegion(base_id=70, locations={
            "MINEMAZE (Episode 1) - Starting Gate": None,
            "MINEMAZE (Episode 1) - Lone Orb": None,
            "MINEMAZE (Episode 1) - Right Path Gate": None,
            "MINEMAZE (Episode 1) - That's not a Strawberry": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"]),
            "MINEMAZE (Episode 1) - ASTEROID? Warp Orb": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"]),
            "MINEMAZE (Episode 1) - Ships Behind Central Gate": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"])
        }, completion_reqs=RequirementList(["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"]),
        shop_setups=["E", "F", "F", "F", "G"]),

        "WINDY (Episode 1)": LevelRegion(base_id=80, locations={
            # Embedded in a wall
            "WINDY (Episode 1) - Central Question Mark": RequirementList(
                  ["Invulnerability", "SideHighDPS", "Power5", "Armor7"], # The sane way
                  ["Invulnerability", "Power8", "Armor7"], # Alternative (high weapon power)
                  ["Armor14", "Power9"], # The less sane way (just taking the damage -- OOF)
            obscure=True)
        }, completion_reqs=RequirementList(["Power5"], ["SideHighDPS"], require_all=["Armor7"]),
        shop_setups=["F", "G", "I"]),

        "SAVARA (Episode 1)": LevelRegion(base_id=90, locations={
            # This is the variant of Savara on Easy or Medium.
            "SAVARA (Episode 1) - White Formation Leader 1": None, # Needs conditions
            "SAVARA (Episode 1) - White Formation Leader 2": None, # Needs conditions
            "SAVARA (Episode 1) - Green Plane Line": None, # Needs conditions
            "SAVARA (Episode 1) - Brown Plane Breaking Formation": None, # Needs conditions
            "SAVARA (Episode 1) - Large Plane Speeding By": None, # Needs conditions
            "SAVARA (Episode 1) - Vulcan Plane Group": None, # Needs conditions
            "SAVARA (Episode 1) - Boss": None, # Needs conditions
        }, completion_reqs=None,
        shop_setups=["E", "H", "L", "P"]),

        "SAVARA II (Episode 1)": LevelRegion(base_id=100, locations={
            # This is the variant of Savara on Hard or above.
            "SAVARA II (Episode 1) - Launched Planes 1": None, # Needs conditions
            "SAVARA II (Episode 1) - Green Plane Sequence 1": None, # Needs conditions
            "SAVARA II (Episode 1) - Large Plane Amidst Turrets": None, # Needs conditions
            "SAVARA II (Episode 1) - Vulcan Planes Near Blimp": None, # Needs conditions
            "SAVARA II (Episode 1) - Launched Planes 2": None, # Needs conditions
            "SAVARA II (Episode 1) - Green Plane Sequence 2": None, # Needs conditions
            "SAVARA II (Episode 1) - Boss": None, # Needs conditions
        }, completion_reqs=None,
        shop_setups=["E", "H", "L", "P"]),

        "BONUS (Episode 1)": LevelRegion(base_id=110, locations={
            # Nothing here to give checks for.
        }, completion_reqs=RequirementList(["Power4"], ["AnyHighDPS", "Power2"], ["AnyDefensive", "Power2"]),
        shop_setups=["J", "J", "J", "K", "K", "L"]),

        "MINES (Episode 1)": LevelRegion(base_id=120, locations={
            "MINES (Episode 1) - Regular Spinning Orbs": RequirementList(
                  ["Power3"], ["Power2", "FrontHighDPS"], ["SideHighDPS"], ["SpecialHighDPS"], ["AnyPierces"]),
            "MINES (Episode 1) - Blue Mine": None,

            # Speed up section makes regular shots not quite cut it
            "MINES (Episode 1) - Repulsor Spinning Orbs":  RequirementList(
                  ["Power3", "FrontHighDPS"], ["SideHighDPS"], ["SpecialHighDPS"], ["AnyPierces"]),
            "MINES (Episode 1) - Absolutely Free": None, # Literally just out in the open at the end of the level
            "MINES (Episode 1) - But Wait There's More": None, # See above
        }, completion_reqs=None,
        shop_setups=["E", "F", "G", "H", "J"]),

        "DELIANI (Episode 1)": LevelRegion(base_id=130, locations={
            "DELIANI (Episode 1) - Turret Wave 1": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"], ["SpecialHighDPS", "Power2"]),
            "DELIANI (Episode 1) - Turret Wave 2": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"], ["SpecialHighDPS", "Power2"]),

            # This is the turret on rails that goes into a difficult to hit position if you wait too long
            "DELIANI (Episode 1) - Tricky Rail Turret": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"], ["SpecialHighDPS", "Power2"]),

            "DELIANI (Episode 1) - Turret Wave 3": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"], ["SpecialHighDPS", "Power2"]),
            "DELIANI (Episode 1) - Turret Wave 4": RequirementList(
                  ["Power3"], ["FrontHighDPS", "Power2"], ["SideHighDPS"], ["SpecialHighDPS", "Power2"]),

            # Earlier checks don't require much but you need decent survivability past this point
            "DELIANI (Episode 1) - Ambush": RequirementList(
                  ["Power7"], ["AnyHighDPS"], require_all=["Armor6", "Power4"]),
            "DELIANI (Episode 1) - Last Cross Formation": RequirementList(
                  ["Power7"], ["AnyHighDPS"], require_all=["Armor6", "Power4"]),
            "DELIANI (Episode 1) - Boss": RequirementList(
                  ["Power7"], ["AnyHighDPS"], require_all=["Armor6", "Power4"]),
        }, completion_reqs="Boss",
        shop_setups=["K", "M", "O", "P", "Q"]),

        "SAVARA V (Episode 1)": LevelRegion(base_id=140, locations={
            "SAVARA V (Episode 1) - Green Plane Sequence": RequirementList(["Power5"]),
            "SAVARA V (Episode 1) - Flying Between Blimps": RequirementList(["Power5"]),
            "SAVARA V (Episode 1) - Brown Plane Sequence": RequirementList(["Power5"]),
            "SAVARA V (Episode 1) - Flying Alongside Green Planes": RequirementList(["Power5"]),

            # This is the blimp that spams bubbles at an abnormally fast rate
            "SAVARA V (Episode 1) - Super Blimp": RequirementList(["AnyHighDPS", "Power8", "Generator3"]),

            # There's so little actually attacking you here that you can just freely shoot at the mid-boss
            # without any actual difficulty!
            "SAVARA V (Episode 1) - Mid-Boss": RequirementList(["Power5"]),

            # This boss heals if you wait too long to kill it. Power 5 is about the sweet spot.
            "SAVARA V (Episode 1) - Boss": RequirementList(["Power5"])
        }, completion_reqs="Boss",
        shop_setups=["E", "H", "L", "P"]),

        "ASSASSIN (Episode 1)": LevelRegion(base_id=150, locations={
            "ASSASSIN (Episode 1) - Boss": RequirementList(
                  ["Power8"], ["AnyHighDPS"], require_all=["Armor7", "Generator2", "Power5"]),
        }, completion_reqs="Boss",
        shop_setups=["S"]),
        # Event: "Episode 1 (Escape) Complete"

        # =============================================================================================
        # EPISODE 2 - TREACHERY
        # =============================================================================================

        "TORM (Episode 2)": LevelRegion(base_id=160, locations={
            "TORM (Episode 2) - Ship Fleeing Dragon Secret": None,
            "TORM (Episode 2) - Boss": None,
        }, completion_reqs=RequirementList(["Armor4"]) ),

        "GYGES (Episode 2)": LevelRegion(base_id=170, locations={
            "GYGES (Episode 2) - Circled Shapeshifting Turret 1": None, # Needs conditions
            "GYGES (Episode 2) - Wide Waving Worm": None, # Needs conditions
            "GYGES (Episode 2) - Orb Snake": None, # Needs conditions
            "GYGES (Episode 2) - Upper Shapeshifters in Afterburner Section": None, # Needs conditions
            "GYGES (Episode 2) - GEM WAR Warp Orb": None, # Needs conditions
            "GYGES (Episode 2) - Circled Shapeshifting Turret 2": None, # Needs conditions
            "GYGES (Episode 2) - Last Set of Worms": None, # Needs conditions
            "GYGES (Episode 2) - Boss": None, # Needs conditions
        }, completion_reqs="Boss"),

        "BONUS 1 (Episode 2)": LevelRegion(base_id=180, locations={
            # There's nothing here to give checks for.
        }, completion_reqs=None),

        "ASTCITY (Episode 2)": LevelRegion(base_id=190, locations={
            "ASTCITY (Episode 2) - Shield Ships in V Formations": None, # Needs conditions
            "ASTCITY (Episode 2) - Plasma Turrets Going Uphill": None, # Needs conditions
            "ASTCITY (Episode 2) - Warehouse 92": None, # Needs conditions
            "ASTCITY (Episode 2) - Shield Ships Going Downhill": None, # Needs conditions
            "ASTCITY (Episode 2) - MISTAKES Warp Orb": None, # Needs conditions
            "ASTCITY (Episode 2) - Ending Turret Group": None, # Needs conditions
        }, completion_reqs=None),

        "BONUS 2 (Episode 2)": LevelRegion(base_id=200, locations={
            # There's nothing here to give checks for.
        }, completion_reqs=None),

        "GEM WAR (Episode 2)": LevelRegion(base_id=210, locations={
        }, completion_reqs=None),

        "MARKERS (Episode 2)": LevelRegion(base_id=220, locations={
        }, completion_reqs=None),

        "MISTAKES (Episode 2)": LevelRegion(base_id=230, locations={
            "MISTAKES (Episode 2) - Start - Trigger Enemy 1": None,
            "MISTAKES (Episode 2) - Start - Trigger Enemy 2": None,
            "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 1": None,
            "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 2": RequirementList(obscure=True),
            "MISTAKES (Episode 2) - Claws - Trigger Enemy 1": None,
            "MISTAKES (Episode 2) - Claws - Trigger Enemy 2": RequirementList(obscure=True),
            "MISTAKES (Episode 2) - Drills - Trigger Enemy 1": None,
            "MISTAKES (Episode 2) - Drills - Trigger Enemy 2": None,
            "MISTAKES (Episode 2) - Super Bubble Spawner": RequirementList(obscure=True),
            "MISTAKES (Episode 2) - Anti-Softlock": RequirementList(obscure=True),
        }, completion_reqs=None,
        shop_setups=["B", "D", "J", "K", "L", "O", "V", "Z!"]),

        "SOH JIN (Episode 2)": LevelRegion(base_id=240, locations={
        }, completion_reqs=None),

        "BOTANY A (Episode 2)": LevelRegion(base_id=250, locations={
            "BOTANY A (Episode 2) - Retreating Mobile Turret": None, # Needs condition
            "BOTANY A (Episode 2) - Mobile Turret Approaching Head-On": None, # Needs condition
            "BOTANY A (Episode 2) - Boss": None,
        }, completion_reqs="Boss"),

        "BOTANY B (Episode 2)": LevelRegion(base_id=260, locations={
            "BOTANY B (Episode 2) - Starting Platform Sensor": RequirementList(
                  ["Armor7"], ["AnyDefensive"], require_all=["Power5", "Generator2"]),
            "BOTANY B (Episode 2) - Main Platform First Sensor": RequirementList(
                  ["Armor7"], ["AnyDefensive"], require_all=["Power5", "Generator2"]),
            "BOTANY B (Episode 2) - Main Platform Second Sensor": RequirementList(
                  ["Armor7"], ["AnyDefensive"], require_all=["Power5", "Generator2"]),
            "BOTANY B (Episode 2) - Main Platform Last Sensor": RequirementList(
                  ["Armor7"], ["AnyDefensive"], require_all=["Power5", "Generator2"]),
            "BOTANY B (Episode 2) - Super-Turret on Bridge": RequirementList(
                  ["Armor7"], ["AnyDefensive"], require_all=["Power5", "Generator2"]),
            "BOTANY B (Episode 2) - Boss": None,
        }, completion_reqs="Boss"),

        "GRYPHON (Episode 2)": LevelRegion(base_id=270, locations={
            "GRYPHON (Episode 2) - Pulse-Turret Wave Mid-Spikes": None,
            "GRYPHON (Episode 2) - Swooping Pulse-Turrets": None,
            "GRYPHON (Episode 2) - Sweeping Pulse-Turrets": None,
            "GRYPHON (Episode 2) - Spike From Behind": None,
            "GRYPHON (Episode 2) - Breaking Formation 1": None,
            "GRYPHON (Episode 2) - Breaking Formation 2": None,
            "GRYPHON (Episode 2) - Breaking Formation 3": None,
            "GRYPHON (Episode 2) - Breaking Formation 4": None,
            "GRYPHON (Episode 2) - Breaking Formation 5": None,
            "GRYPHON (Episode 2) - Boss": None,
        }, completion_reqs="Boss"),
        # Event: "Episode 2 (Treachery) Complete"

        # =============================================================================================
        # EPISODE 3 - MISSION: SUICIDE
        # =============================================================================================

        "GAUNTLET (Episode 3)": LevelRegion(base_id=280, locations={
        }, completion_reqs=None),

        "IXMUCANE (Episode 3)": LevelRegion(base_id=290, locations={
            "IXMUCANE (Episode 3) - Boss": None, # Needs conditions
        }, completion_reqs=None),

        "BONUS (Episode 3)": LevelRegion(base_id=300, locations={
            "BONUS (Episode 3) - First Lone Turret": RequirementList(["Power5"]),
            "BONUS (Episode 3) - Behind First Onslaught": RequirementList(["Power9", "Armor7", "Generator3"]),
            "BONUS (Episode 3) - Behind Second Onslaught": RequirementList(["Power9", "Armor7", "Generator3"]),
            "BONUS (Episode 3) - Second Lone Turret": RequirementList(["Power9", "Armor7", "Generator3"]),

            # Invulnerability does not last long enough to pass this section on its own.
            "BONUS (Episode 3) - Sonic Wave Hell Turret": RequirementList(
                  ["Repulsor", "Power9", "Armor7", "Generator3"], # The only way this is remotely feasible
                  ["Armor14", "Power11", "Generator5"], # Basically require everything, absurdly difficult
            obscure=True), # Excessively difficult
        }, completion_reqs=RequirementList(
              ["Repulsor", "Power9", "Armor7", "Generator3"], # The only way this is remotely feasible
              ["Armor14", "Power11", "Generator5"], obscure=True), # Excessively difficult
        shop_setups=["G", "G"]),

        "STARGATE (Episode 3)": LevelRegion(base_id=310, locations={
            "STARGATE (Episode 3) - First Bubbleway": RequirementList(["Power3"]),
            "STARGATE (Episode 3) - First Bubble Spawner": RequirementList(["Power3"]),
            "STARGATE (Episode 3) - AST. CITY Warp Orb 1": RequirementList(["Power3"]),
            "STARGATE (Episode 3) - AST. CITY Warp Orb 2": RequirementList(["Power3"]),
            "STARGATE (Episode 3) - SAWBLADES Warp Orb 1": RequirementList(["Power3"]),
            "STARGATE (Episode 3) - SAWBLADES Warp Orb 2": RequirementList(["Power3"]),
            "STARGATE (Episode 3) - Super Bubble Spawner": RequirementList(["Power3"]),
        }, completion_reqs=RequirementList(["Power3"]) ),

        "AST. CITY (Episode 3)": LevelRegion(base_id=320, locations={
        }, completion_reqs=None),

        "SAWBLADES (Episode 3)": LevelRegion(base_id=330, locations={
            "SAWBLADES (Episode 3) - FoodShip Nine Drop": None # Needs conditions
        }, completion_reqs=None),

        "CAMANIS (Episode 3)": LevelRegion(base_id=340, locations={
            "CAMANIS (Episode 3) - Boss": None, # Needs conditions
        }, completion_reqs="Boss"),

        "MACES (Episode 3)": LevelRegion(base_id=350, locations={
            # Nothing in this level is destructible. It's entirely a test of dodging.
            # Therefore nothing is actually required to complete it or get any check.
            "MACES (Episode 3) - Third Mace": None,
            "MACES (Episode 3) - Sixth Mace": None,
            "MACES (Episode 3) - Mace Reprieve 1": None,
            "MACES (Episode 3) - Mace Reprieve 2": None,
            "MACES (Episode 3) - Mace Reprieve 3": None,
        }, completion_reqs=None),

        "TYRIAN X (Episode 3)": LevelRegion(base_id=360, locations={
            "TYRIAN X (Episode 3) - First U-Ship Secret": None, # Needs conditions
            "TYRIAN X (Episode 3) - Second Secret, Same as the First": None, # Needs conditions
            "TYRIAN X (Episode 3) - Side-flying Ship Near Landers": None, # Needs conditions
            "TYRIAN X (Episode 3) - Platform Spinner Sequence": None, # Needs conditions
            "TYRIAN X (Episode 3) - Tank Near Purple Structure": None, # Needs conditions
            "TYRIAN X (Episode 3) - Tank Turn-and-fire Secret": None, # Needs conditions
            "TYRIAN X (Episode 3) - Boss": None, # Needs conditions
        }, completion_reqs=None),

        "SAVARA Y (Episode 3)": LevelRegion(base_id=370, locations={
            "SAVARA Y (Episode 3) - Boss": None,
        }, completion_reqs=None),

        "NEW DELI (Episode 3)": LevelRegion(base_id=380, locations={
            "NEW DELI (Episode 3) - Turret Wave 1": None, # Needs conditions
            "NEW DELI (Episode 3) - Turret Wave 2": None, # Needs conditions
            "NEW DELI (Episode 3) - Turret Wave 3": None, # Needs conditions
            "NEW DELI (Episode 3) - Turret Wave 4": None, # Needs conditions
            "NEW DELI (Episode 3) - Turret Wave 5": None, # Needs conditions
            "NEW DELI (Episode 3) - Turret Wave 6": None, # Needs conditions
            "NEW DELI (Episode 3) - Boss": None, # Needs conditions
        }, completion_reqs="Boss"),

        "FLEET (Episode 3)": LevelRegion(base_id=390, locations={
            "FLEET (Episode 3) - Attractor Crane 1": None, # Needs conditions
            "FLEET (Episode 3) - Attractor Crane 2": None, # Needs conditions
            "FLEET (Episode 3) - Boss": None, # Needs conditions
        }, completion_reqs="Boss"),
        # Event: "Episode 3 (Mission: Suicide) Complete"

        # =============================================================================================
        # EPISODE 4 - AN END TO FATE
        # =============================================================================================

        "SURFACE (Episode 4)": LevelRegion(base_id=400, locations={
            "SURFACE (Episode 4) - WINDY Warp Orb": RequirementList(obscure=True), # Needs conditions
            "SURFACE (Episode 4) - Triple V Formation": None, # Needs conditions
        }, completion_reqs=None),

        "WINDY (Episode 4)": LevelRegion(base_id=410, locations={
        }, completion_reqs=None),

        "LAVA RUN (Episode 4)": LevelRegion(base_id=420, locations={
            "LAVA RUN (Episode 4) - Second Laser Shooter": None, # Needs conditions
            "LAVA RUN (Episode 4) - Left Side Missile Launcher": None, # Needs conditions
            "LAVA RUN (Episode 4) - Boss": RequirementList(["Power4", "Generator2", "SideDefensive"]),
        }, completion_reqs=RequirementList(["Power4", "Generator2", "SideDefensive"]) ),

        "CORE (Episode 4)": LevelRegion(base_id=430, locations={
            "CORE (Episode 4) - Boss": None, # Needs conditions

            # Can time out (leads to a failure exit, actually; the only such path split in the game)
        }, completion_reqs=None),

        "LAVA EXIT (Episode 4)": LevelRegion(base_id=440, locations={
            "LAVA EXIT (Episode 4) - Central Lightning Shooter": None, # Needs conditions
            "LAVA EXIT (Episode 4) - Lava Bubble Wave 1": None, # Needs conditions
            "LAVA EXIT (Episode 4) - Lava Bubble Wave 2": None, # Needs conditions
            "LAVA EXIT (Episode 4) - DESERTRUN Warp Orb": None, # Needs conditions
            "LAVA EXIT (Episode 4) - Final Lava Bubble Assault 1": None, # Needs conditions
            "LAVA EXIT (Episode 4) - Final Lava Bubble Assault 2": None, # Needs conditions
            "LAVA EXIT (Episode 4) - Boss": None, # Needs conditions
        }, completion_reqs=None),

        "DESERTRUN (Episode 4)": LevelRegion(base_id=450, locations={
            "DESERTRUN (Episode 4) - Afterburner Smooth Flying": None, # Needs conditions
            "DESERTRUN (Episode 4) - Ending Slalom 1": None, # Needs conditions
            "DESERTRUN (Episode 4) - Ending Slalom 2": None, # Needs conditions
            "DESERTRUN (Episode 4) - Ending Slalom 3": None, # Needs conditions
            "DESERTRUN (Episode 4) - Ending Slalom 4": None, # Needs conditions
            "DESERTRUN (Episode 4) - Ending Slalom 5": None, # Needs conditions
        }, completion_reqs=None),

        "SIDE EXIT (Episode 4)": LevelRegion(base_id=460, locations={
            "SIDE EXIT (Episode 4) - Waving X-shaped Enemies 1": None,
            "SIDE EXIT (Episode 4) - Third Laser Shooter": None, # Needs conditions
            "SIDE EXIT (Episode 4) - Waving X-shaped Enemies 2": None,
            "SIDE EXIT (Episode 4) - Final Laser Shooter Onslaught": None, # Needs conditions
        }, completion_reqs=None),

        "?TUNNEL? (Episode 4)": LevelRegion(base_id=470, locations={
            # Only a boss fight
            "?TUNNEL? (Episode 4) - Boss": None, # Needs conditions
        }, completion_reqs="Boss"),

        "ICE EXIT (Episode 4)": LevelRegion(base_id=480, locations={
            "ICE EXIT (Episode 4) - ICESECRET Orb": None, # Needs conditions
            "ICE EXIT (Episode 4) - Boss": None, # Needs conditions
        }, completion_reqs=None),

        "ICESECRET (Episode 4)": LevelRegion(base_id=490, locations={
            "ICESECRET (Episode 4) - Large U-Ship Mini-Boss": None, # Needs conditions
            "ICESECRET (Episode 4) - MegaLaser Dual Drop": None, # Needs conditions
            "ICESECRET (Episode 4) - Boss": None, # Needs conditions
        }, completion_reqs=None),

        "HARVEST (Episode 4)": LevelRegion(base_id=500, locations={
            "HARVEST (Episode 4) - High Speed V Formation": RequirementList(
                  ["SideHighDPS"], ["FrontHighDPS"], ["Power10"], require_all=["Power7", "Generator2"]),
            "HARVEST (Episode 4) - Shooter with Gravity Orbs": None, # Needs conditions
            "HARVEST (Episode 4) - Shooter with Clone Bosses": None, # Needs conditions
            "HARVEST (Episode 4) - Grounded Shooter 1": None, # Needs conditions
            "HARVEST (Episode 4) - Grounded Shooter 2": None, # Needs conditions
            "HARVEST (Episode 4) - Ending V Formation": None, # Needs conditions
            "HARVEST (Episode 4) - Boss": None, # Needs conditions
        }, completion_reqs="Boss"),

        "UNDERDELI (Episode 4)": LevelRegion(base_id=510, locations={
            "UNDERDELI (Episode 4) - Boss's Red Eye": None, # Needs conditions
            "UNDERDELI (Episode 4) - Boss": None, # Needs conditions

            # You can technically time this boss out, but it's really, really slow
        }, completion_reqs=None),

        "APPROACH (Episode 4)": LevelRegion(base_id=520, locations={
        }, completion_reqs=None),

        "SAVARA IV (Episode 4)": LevelRegion(base_id=530, locations={
            "SAVARA IV (Episode 4) - Early Breakaway V Formation": RequirementList(["Power5", "Generator2"]),
            "SAVARA IV (Episode 4) - First Drunk Plane": RequirementList(["Power5", "Generator2"]),
            "SAVARA IV (Episode 4) - Last Breakaway V Formation": RequirementList(["Power5", "Generator2"]),
            "SAVARA IV (Episode 4) - Second Drunk Plane": RequirementList(["Power5", "Generator2"]),
            "SAVARA IV (Episode 4) - Boss": RequirementList(
                  ["RearSideways", "Armor7"], # Can move up to the top and hit from the side
                  ["AnyPierces"], # SDF Main Gun, piercing front weapon, etc. gets past
                  ["SideRightOnly"], # Right-only Sidekicks can be fired out
                  ["Armor9", "Power8"], # If you survive long enough, enemy planes will start dropping SuperBombs
            require_all=["Power5", "Generator2"]),

            # Can time out, but beating the boss is more likely than surviving that long
        }, completion_reqs="Boss"),

        "DREAD-NOT (Episode 4)": LevelRegion(base_id=540, locations={
            # Only a boss fight
            "DREAD-NOT (Episode 4) - Boss": RequirementList(
                  ["FrontHighDPS", "Power6", "Armor6", "Generator3"],
                  ["Power8", "Armor6", "Generator3"]),
        }, completion_reqs="Boss"),

        "EYESPY (Episode 4)": LevelRegion(base_id=550, locations={
            "EYESPY (Episode 4) - Green Exploding Eye 1": None,
            "EYESPY (Episode 4) - Blue Splitting Eye 1": None,
            "EYESPY (Episode 4) - Green Exploding Eye 2": None,
            "EYESPY (Episode 4) - Blue Splitting Eye 2": None,
            "EYESPY (Episode 4) - Blue Splitting Eye 3": None,
            "EYESPY (Episode 4) - Billiard Break Secret": RequirementList(obscure=True),
            "EYESPY (Episode 4) - Boss": None,
        }, completion_reqs="Boss"),

        "BRAINIAC (Episode 4)": LevelRegion(base_id=560, locations={
            "BRAINIAC (Episode 4) - Turret-Guarded Pathway": None, # Needs conditions
            "BRAINIAC (Episode 4) - Mid-Boss 1": None, # Needs conditions
            "BRAINIAC (Episode 4) - Mid-Boss 2": RequirementList(
                  # Stays at the bottom of the screen
                  ["RearSideways", "Power9", "Armor9", "Generator5"]),
            "BRAINIAC (Episode 4) - Boss": RequirementList(
                  ["FrontHighDPS"],
                  ["FrontPierces"],
                  ["SpecialPierces"],
                  ["SideRightOnly"],
            require_all=["Power9", "Armor9", "Generator5"]),
        }, completion_reqs="Boss"),

        "NOSE DRIP (Episode 4)": LevelRegion(base_id=570, locations={
            "NOSE DRIP (Episode 4) - Boss": RequirementList(
                  # Without a good loadout, this boss is extremely difficult, so...
                  ["FrontHighDPS"],
                  ["SideHighDPS", "AnyDefensive"],
            require_all=["Power9", "Armor11", "Generator5"]),
        }, completion_reqs="Boss",
        shop_setups=["S"]),
        # Event: "Episode 4 (An End To Fate) Complete"

        # =============================================================================================
        # EPISODE 5 - HAZUDRA FODDER
        # =============================================================================================

        "ASTEROIDS (Episode 5)": LevelRegion(base_id=580, locations={
            "ASTEROIDS (Episode 5) - Ship 1": None,
            "ASTEROIDS (Episode 5) - Railgunner 1": None,
            "ASTEROIDS (Episode 5) - Ship": None,
            "ASTEROIDS (Episode 5) - Railgunner 2": None,
            "ASTEROIDS (Episode 5) - Ship 2": None,
            "ASTEROIDS (Episode 5) - Boss": None,
        }, completion_reqs=None),

        "AST ROCK (Episode 5)": LevelRegion(base_id=590, locations={
        }, completion_reqs=None),

        "MINERS (Episode 5)": LevelRegion(base_id=600, locations={
            "MINERS (Episode 5) - Boss": None,
        }, completion_reqs=None),

        "SAVARA (Episode 5)": LevelRegion(base_id=610, locations={
            "SAVARA (Episode 5) - Green Vulcan Plane 1": None,
            "SAVARA (Episode 5) - Large Plane Formation": None,
            "SAVARA (Episode 5) - Surrounded Vulcan Plane": None,
            "SAVARA (Episode 5) - Unknown 1": None,
            "SAVARA (Episode 5) - Unknown 2": None,
            "SAVARA (Episode 5) - Boss": None,
        }, completion_reqs=None),

        "CORAL (Episode 5)": LevelRegion(base_id=620, locations={
            "CORAL (Episode 5) - Boss": None,
        }, completion_reqs=None),

        "STATION (Episode 5)": LevelRegion(base_id=630, locations={
            "STATION (Episode 5) - Pulse-Turret 1": None,
            "STATION (Episode 5) - Pulse-Turret 2": None,
            "STATION (Episode 5) - Pulse-Turret 3": None,
            "STATION (Episode 5) - Spike from Rear Corner 1": None,
            "STATION (Episode 5) - Pulse-Turret 4": None,
            "STATION (Episode 5) - Spike from Rear Corner 2": None,
            "STATION (Episode 5) - Repulsor Crane": None,
            "STATION (Episode 5) - Pulse-Turret 5": None,
            "STATION (Episode 5) - Pulse-Turret 6": None,
            "STATION (Episode 5) - Boss": None,
        }, completion_reqs=None),

        "FRUIT (Episode 5)": LevelRegion(base_id=640, locations={
            "FRUIT (Episode 5) - Apple UFO Wave": None,
            "FRUIT (Episode 5) - Boss": None,
        }, completion_reqs=None),
        # Event: "Episode 5 (Hazudra Fodder) Complete" - Isn't this episode short???
    }

    shop_regions: Dict[str, int] = {name: i for (name, i) in zip(level_regions.keys(), range(1000, 2000, 10))}

    # Events for game completion
    events: Dict[str, str] = {
        "Episode 1 (Escape) Complete":           "ASSASSIN (Episode 1)",
        "Episode 2 (Treachery) Complete":        "GRYPHON (Episode 2)",
        "Episode 3 (Mission: Suicide) Complete": "FLEET (Episode 3)",
        "Episode 4 (An End to Fate) Complete":   "NOSE DRIP (Episode 4)",
        "Episode 5 (Hazudra Fodder) Complete":   "FRUIT (Episode 5)",
    }

    @classmethod
    def get_location_name_to_id(cls, base_id: int):
        all_locs = {}
        for (level, region) in cls.level_regions.items():
            all_locs.update({name: (base_id + region.base_id + i) for (name, i) in zip(region.keys(), range(99))})

        for (level, start_id) in cls.shop_regions.items():
            all_locs.update({f"Shop ({level}) - Item {i + 1}": (base_id + start_id + i) for i in range(0, 5)})

        return all_locs

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
        "SAWBLADES (Episode 3) - FoodShip Nine Drop": """
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
