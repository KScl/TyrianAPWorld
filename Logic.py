# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import TYPE_CHECKING, Callable, Any, Union, List

from BaseClasses import LocationProgressType as LP

from .Items import Episode
from .Options import LogicDifficulty, GameDifficulty

if TYPE_CHECKING:
    from BaseClasses import CollectionState
    from . import TyrianLocation, TyrianWorld

# =================================================================================================

def has_armor_level(state: "CollectionState", player: int, armor_level: int):
    return True if armor_level <= 5 else state.has("Armor Up", player, armor_level - 5)

def has_power_level(state: "CollectionState", player: int, power_level: int):
    return True if power_level <= 1 else state.has("Maximum Power Up", player, power_level - 1)

def has_generator_level(state: "CollectionState", player: int, gen_level: int):
    if state.has("Gravitron Pulse-Wave", player):   return True
    elif state.has("Advanced MicroFusion", player): base_gen_level = 5
    elif state.has("Standard MicroFusion", player): base_gen_level = 4
    elif state.has("Gencore Custom MR-12", player): base_gen_level = 3
    elif state.has("Advanced MR-12", player):       base_gen_level = 2
    else:                                           base_gen_level = 1

    return gen_level <= base_gen_level or state.has("Progressive Generator", player, gen_level - base_gen_level)

def has_twiddle(state: "CollectionState", player: int, action: str):
    return False # TODO NYI

# =================================================================================================

def all_rules_of(state: "CollectionState", location: "TyrianLocation"):
    for rule in location.all_access_rules:
        if not rule(state):
            return False
    return True

# -----------------------------------------------------------------------------

def logic_entrance_rule(world: "TyrianWorld", entrance_name: str, rule: Callable[["CollectionState"], bool]):
    entrance = world.multiworld.get_entrance(entrance_name, world.player)
    entrance.access_rule = rule

def logic_entrance_behind_location(world: "TyrianWorld", entrance_name: str, location_name: str):
    logic_entrance_rule(world, entrance_name, lambda state:
          state.can_reach(location_name, "Location", world.player))

def logic_location_rule(world: "TyrianWorld", location_name: str, rule: Callable[["CollectionState"], bool]):
    location = world.multiworld.get_location(location_name, world.player)
    location.all_access_rules.append(rule)
    location.access_rule = lambda state, location=location: all_rules_of(state, location)

def logic_location_exclude(world: "TyrianWorld", location_name: str):
    location = world.multiworld.get_location(location_name, world.player)
    location.progress_type = LP.EXCLUDED

def logic_all_locations_rule(world: "TyrianWorld", location_name_base: str, rule: Callable[["CollectionState"], bool]):
    for location in [i for i in world.multiworld.get_locations(world.player) if i.name.startswith(location_name_base)]:
        location.all_access_rules.append(rule)
        location.access_rule = lambda state, location=location: all_rules_of(state, location)

def logic_all_locations_exclude(world: "TyrianWorld", location_name_base: str):
    for location in [i for i in world.multiworld.get_locations(world.player) if i.name.startswith(location_name_base)]:
        location.progress_type = LP.EXCLUDED

def boss_timeout_in_logic(world: "TyrianWorld") -> bool:
    # This is in a function because it may change in the future to be based on a different set of logic difficulties
    # or just depend on another option entirely
    return world.options.logic_difficulty == LogicDifficulty.option_beginner

# -----------------------------------------------------------------------------

def episode_1_rules(world: "TyrianWorld"):
    # ===== TYRIAN ============================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at TYRIAN (Episode 1)", "TYRIAN (Episode 1) - Boss")
 
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "TYRIAN (Episode 1) - HOLES Warp Orb")
        logic_location_exclude(world, "TYRIAN (Episode 1) - SOH JIN Warp Orb")
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "TYRIAN (Episode 1) - Tank Turn-and-fire Secret")

    # Four trigger enemies among the starting U-Ship sets
    # Expert or below: Destroy all / Master: Assume knowledge
    if (world.options.difficulty >= GameDifficulty.option_hard
          and world.options.logic_difficulty <= LogicDifficulty.option_expert):
        logic_location_rule(world, "TYRIAN (Episode 1) - HOLES Warp Orb", lambda state:
              has_power_level(state, world.player, 2))

    # ===== BUBBLES ===========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "BUBBLES (Episode 1) - Coin Rain 1")
        logic_location_exclude(world, "BUBBLES (Episode 1) - Coin Rain 2")
        logic_location_exclude(world, "BUBBLES (Episode 1) - Coin Rain 3")

    # ===== HOLES =============================================================

    # ===== SOH JIN ===========================================================

    # ===== ASTEROID1 =========================================================
    logic_entrance_behind_location(world, "Can shop at ASTEROID1 (Episode 1)", "ASTEROID1 (Episode 1) - Boss")

    # ===== ASTEROID2 =========================================================    
    logic_entrance_behind_location(world, "Can shop at ASTEROID2 (Episode 1)", "ASTEROID2 (Episode 1) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1")
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2")
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret")

    # ===== ASTEROID? =========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "ASTEROID? (Episode 1) - WINDY Warp Orb")

    # ===== MINEMAZE ==========================================================

    # ===== WINDY =============================================================
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "WINDY (Episode 1) - Central Question Mark")

    # ===== SAVARA ============================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at SAVARA (Episode 1)", "SAVARA (Episode 1) - Boss")

    # ===== SAVARA II =========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at SAVARA II (Episode 1)", "SAVARA II (Episode 1) - Boss")

    # ===== MINES =============================================================

    # ===== DELIANI ===========================================================
    logic_entrance_behind_location(world, "Can shop at DELIANI (Episode 1)", "DELIANI (Episode 1) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "DELIANI (Episode 1) - Tricky Rail Turret")

    # ===== ASSASSIN ==========================================================
    logic_entrance_behind_location(world, "Can shop at ASSASSIN (Episode 1)", "ASSASSIN (Episode 1) - Boss")

    logic_all_locations_rule(world, "ASSASSIN (Episode 1)", lambda state:
        has_armor_level(state, world.player, 10))
    logic_location_rule(world, "ASSASSIN (Episode 1) - Boss", lambda state:
        has_power_level(state, world.player, 8))

# -----------------------------------------------------------------------------

def episode_2_rules(world: "TyrianWorld"):
    # ===== TORM ==============================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at TORM (Episode 2)", "TORM (Episode 2) - Boss")

    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret")

    # ===== GYGES =============================================================
    logic_entrance_behind_location(world, "Can shop at GYGES (Episode 2)", "GYGES (Episode 2) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "GYGES (Episode 2) - Afterburner Shapeshifters")
        logic_location_exclude(world, "GYGES (Episode 2) - GEM WAR Warp Orb")

    # ===== ASTCITY ===========================================================
    logic_entrance_behind_location(world, "Can shop at ASTCITY (Episode 2)", 
          "ASTCITY (Episode 2) - Ending Turret Group")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "ASTCITY (Episode 2) - MISTAKES Warp Orb")

    # ===== GEM WAR ===========================================================

    # ===== MARKERS ===========================================================

    # ===== MISTAKES ==========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 1")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Claws - Trigger Enemy 1")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Claws - Trigger Enemy 2")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Super Bubble Spawner")
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 2")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Anti-Softlock")

    # ===== SOH JIN ===========================================================

    # ===== BOTANY A ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at BOTANY A (Episode 2)", "BOTANY A (Episode 2) - Boss")

    # ===== BOTANY B ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at BOTANY B (Episode 2)", "BOTANY B (Episode 2) - Boss")

    # ===== GRYPHON ===========================================================
    logic_entrance_behind_location(world, "Can shop at GRYPHON (Episode 2)", "GRYPHON (Episode 2) - Boss")

# -----------------------------------------------------------------------------

def episode_3_rules(world: "TyrianWorld"):
    # ===== GAUNTLET ==========================================================

    # ===== IXMUCANE ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at IXMUCANE (Episode 3)", "IXMUCANE (Episode 3) - Boss")

    # ===== BONUS =============================================================
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "BONUS (Episode 3) - Sonic Wave Hell Turret")
        logic_all_locations_exclude(world, "Shop - BONUS (Episode 3)")

    # ===== STARGATE ==========================================================
    logic_entrance_behind_location(world, "Can shop at STARGATE (Episode 3)",
        "STARGATE (Episode 3) - Super Bubble Spawner")

    # ===== AST. CITY =========================================================

    # ===== SAWBLADES =========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "SAWBLADES (Episode 3) - SuperCarrot Drop")

    # ===== CAMANIS ===========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at CAMANIS (Episode 3)", "CAMANIS (Episode 3) - Boss")

    # ===== MACES =============================================================
    # (logicless - purely a test of dodging skill)

    # ===== TYRIAN X ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at TYRIAN X (Episode 3)", "TYRIAN X (Episode 3) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "TYRIAN X (Episode 3) - First U-Ship Secret")
        logic_location_exclude(world, "TYRIAN X (Episode 3) - Second Secret, Same as the First")
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "TYRIAN X (Episode 3) - Tank Turn-and-fire Secret")

    # ===== SAVARA Y ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at SAVARA Y (Episode 3)", "SAVARA Y (Episode 3) - Boss")

    # ===== NEW DELI ==========================================================
    logic_entrance_behind_location(world, "Can shop at NEW DELI (Episode 3)", "NEW DELI (Episode 3) - Boss")

    # ===== FLEET =============================================================
    logic_entrance_behind_location(world, "Can shop at FLEET (Episode 3)", "FLEET (Episode 3) - Boss")

# -----------------------------------------------------------------------------

def episode_4_rules(world: "TyrianWorld"):
    pass

# -----------------------------------------------------------------------------

def episode_5_rules(world: "TyrianWorld"):
    pass

# -----------------------------------------------------------------------------

def set_level_rules(world: "TyrianWorld"):
    if Episode.Escape in world.play_episodes:         episode_1_rules(world)
    if Episode.Treachery in world.play_episodes:      episode_2_rules(world)
    if Episode.MissionSuicide in world.play_episodes: episode_3_rules(world)
    if Episode.AnEndToFate in world.play_episodes:    episode_4_rules(world)
    if Episode.HazudraFodder in world.play_episodes:  episode_5_rules(world)
