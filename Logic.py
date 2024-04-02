# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import TYPE_CHECKING, Callable, Any, Union, List, Dict, NamedTuple, Optional
from collections.abc import Iterable

from BaseClasses import LocationProgressType as LP

from .Items import Episode, LocalItemData
from .Options import LogicDifficulty, GameDifficulty
from .Twiddles import SpecialValues

if TYPE_CHECKING:
    from BaseClasses import CollectionState
    from . import TyrianLocation, TyrianWorld

class DamageValues(NamedTuple):
    active: float
    passive: float
    sideways: float
    piercing: float

class DamageTables:
    # Local versions, used when instantiated, holds all rules for a given logic difficulty merged together
    active: Dict[str, List[float]]
    passive: Dict[str, List[float]]
    sideways: Dict[str, List[float]]
    piercing: Dict[str, List[float]]

    # Multiplier for all target values, based on options.logic_difficulty
    logic_difficulty_multiplier: float

    # Damage focused on single direct target
    base_active = {
        # Base level: Assumes a reasonable distance kept from enemy, and directly below (or only a slight adjustment)
        LogicDifficulty.option_beginner: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Pulse-Cannon":                   [11.8, 14.0, 18.7, 18.7, 19.5, 23.5, 23.5, 27.3,  27.3,  27.3,  32.1],
            "Multi-Cannon (Front)":           [11.8,    0,  4.7,  9.3,  3.8,  7.8,  3.8,  7.8,   3.8,   7.8,   7.8],
            "Mega Cannon":                    [ 5.3,  5.3, 10.0,  5.3, 10.0, 10.0, 10.0, 10.2,  21.1,  21.1,  21.2],
            "Laser":                          [ 7.8, 15.5, 23.3, 23.5, 35.0, 46.5, 46.8, 58.3,  81.6,  93.3, 140.0],
            "Zica Laser":                     [16.3, 23.4, 28.8, 38.2, 49.0, 52.0, 17.1, 53.3,  73.3, 110.0, 127.5],
            "Protron Z":                      [14.0, 19.0, 14.0, 23.3, 23.5, 37.3, 46.7, 60.7,  37.3,  37.3,  37.3],
            "Vulcan Cannon (Front)":          [11.7,  8.8,  5.8,  9.8,  5.7,  5.7,  7.8, 13.0,   7.8,  11.7,  23.3],
            "Lightning Cannon":               [11.5, 15.5, 19.5, 19.5, 15.5, 15.5, 23.0, 23.0,  23.0,  46.7,  93.3],
            "Protron (Front)":                [ 9.3,  7.8,  7.8,  3.3,  6.7, 13.3,  6.7, 13.3,  13.3,  10.0,  23.3],
            "Missile Launcher":               [ 5.1,  5.1,  8.4, 11.7, 14.9, 14.1, 14.1, 16.6,  30.0,  32.0,  15.0],
            "Mega Pulse (Front)":             [12.0, 15.6, 18.7, 23.2, 31.0, 19.5, 31.0, 23.0,  23.0,  31.0,  54.8],
            "Heavy Missile Launcher (Front)": [10.4, 13.3, 18.7,  8.7, 10.4, 33.3, 46.7, 22.8,  40.0,  46.0,  37.3],
            "Banana Blast (Front)":           [ 7.8,  7.8,  9.3,  6.2, 14.0,  5.6,  9.3, 14.0,  15.8,  18.7,  23.5],
            "HotDog (Front)":                 [11.6, 15.6, 18.7, 23.4, 28.0, 35.2, 28.0, 23.3,  23.8,  20.0,  26.7],
            "Hyper Pulse":                    [ 7.8,  5.8,  7.8, 11.8, 15.4, 23.3, 17.5, 23.3,  14.0,  18.7,  17.5],
            "Shuriken Field":                 [ 9.3,  9.3,  9.3,  9.3,  9.3,  9.3,  9.3,  9.3,  18.7,  18.7,  37.3],
            "Poison Bomb":                    [14.2, 17.2, 20.6, 20.6, 26.7, 26.7, 23.6, 37.4,  38.0,  58.0,  90.5],
            "Protron Wave":                   [ 4.7,  5.9,  6.7,  6.7,  6.7,  6.7, 13.3, 13.3,  13.3,  13.3,  13.3],
            "Guided Bombs":                   [10.7,  6.7,  5.3, 13.3, 13.3, 11.0,  7.8,  7.8,  15.0,  10.0,  15.0],
            "The Orange Juicer":              [   0, 11.4, 11.4, 22.8, 22.8,  9.0,  9.0,  9.0,   9.0,   9.0,   9.0],
            "NortShip Super Pulse":           [ 5.9, 11.6, 11.6, 17.6, 23.2, 28.0,  8.6,  8.6,  28.9,  14.5,  76.0],
            "Atomic RailGun":                 [17.5, 35.0, 52.5, 70.0, 81.5, 82.0, 93.6, 99.0, 105.0, 140.0, 140.0],
            "Widget Beam":                    [ 7.8, 15.3, 11.7, 17.4, 11.7, 17.4, 11.8, 11.8,  11.8,  11.8,  17.5],
            "Sonic Impulse":                  [11.6,  7.6, 11.6, 17.5, 23.2, 10.2, 11.6, 11.5,  11.8,  11.6,  11.8],
            "RetroBall":                      [ 9.3,  4.7,  4.7,  9.3,  4.7,  4.7,  9.3,  9.3,   9.3,   9.3,   9.3],
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Sonic Wave":                     [ 6.7, 10.0,  6.7,  6.7,  6.7, 20.0, 20.0, 20.0,  20.0,  20.0,  20.0],
            "Wild Ball":                      [ 5.0,  5.0,  5.0,  7.5,  7.5,  7.5,    0,  5.0,     0,  18.2,  18.2],
            "Fireball":                       [ 3.0,  6.0,    0,    0,  4.0,  8.0,  6.7,  8.0,  15.2,  15.2,  15.2],
            "Mega Pulse (Rear)":              [   0,    0,    0,    0,    0,    0,  6.7,    0,     0,     0,  40.0],
            "Banana Blast (Rear)":            [   0,    0,    0,    0,    0, 35.0, 35.0, 25.0,  25.0,  35.0,  45.0],
            "HotDog (Rear)":                  [   0,    0,    0,    0,    0,    0,    0,    0,     0,   6.7,     0],
            "Scatter Wave":                   [   0,    0,    0,  3.8,  3.8,  1.9,    0,  3.8,   7.5,     0,     0],
            "NortShip Spreader B":            [   0,    0,    0,    0,    0,    0,    0,  2.3,     0,   2.3,   2.3],
        },

        # Expert level: Assumes getting up closer to an enemy so more bullets can hit
        LogicDifficulty.option_expert: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Mega Cannon":                    [ 7.8, 15.2, 14.1,  7.8, 15.2, 16.0, 16.0, 16.0,  26.0,  26.0,  26.0],
            "Zica Laser":                     [16.3, 23.4, 28.8, 38.2, 49.0, 52.0, 56.4, 96.7, 106.7, 110.0, 127.5],
            "Protron Z":                      [14.0, 19.0, 14.0, 23.3, 23.5, 37.3, 46.7, 60.7,  51.3,  60.7,  37.3],
            "Protron (Front)":                [ 9.3, 11.5, 11.5, 10.0, 13.3, 13.3, 20.0, 33.3,  33.3,  26.7,  43.3],
            "Banana Blast (Front)":           [ 7.8, 15.6, 14.0,  9.3, 28.0, 11.8, 18.7, 28.0,  31.2,  37.3,  47.0],
            "Hyper Pulse":                    [ 7.8, 11.6, 15.6, 17.5, 23.5, 31.1, 29.2, 35.0,  23.3,  28.0,  29.0],
            "Protron Wave":                   [ 4.7,  5.9,  6.7,  6.7,  6.7,  6.7, 13.3, 13.3,  13.3,  20.0,  26.7],
            "Guided Bombs":                   [10.7, 13.3, 10.4, 26.7, 18.2, 13.0, 11.0, 11.0,  17.3,  12.0,  19.3],
            "The Orange Juicer":              [10.0, 11.4, 11.4, 22.8, 22.8, 17.0, 17.0, 20.0,  23.0,  30.0,  40.0],
            "Widget Beam":                    [ 7.8, 15.3, 11.7, 17.4, 11.7, 17.4, 17.4, 11.8,  11.8,  17.4,  17.5],
            "Sonic Impulse":                  [11.6, 10.5, 29.2, 17.5, 23.2, 21.8, 23.1, 23.3,  23.3,  30.0,  30.0],
            "RetroBall":                      [ 9.3,  9.3,  9.3,  9.3,  9.3,  9.3, 14.0, 14.0,  18.7,  18.7,  18.7],
        },

        # Master level: Assumes abuse of mechanics like using mode switch to reset weapon state
        LogicDifficulty.option_master: {
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Fireball":                       [ 6.0,  6.0,    0,    0,  8.0,  8.0,  9.3, 11.6,  15.2,  15.2,  15.2],
        },
    }

    # Damage aimed away from the above single target, used to get a general idea of how defensive a build can be
    base_passive = {
        # Base level: Damage to any other area except the above single targeted area
        LogicDifficulty.option_beginner: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Pulse-Cannon":                   [   0,    0,    0,    0,    0,    0,    0,    0,   7.8,  15.5,  15.5],
            "Multi-Cannon (Front)":           [   0, 11.8,  9.3,  9.3, 15.5, 15.5, 24.0, 24.0,  31.5,  31.5,  38.9],
            "Mega Cannon":                    [   0,  6.0,    0,  9.0, 10.0,    0, 13.0, 10.2,     0,  13.0,  20.4],
            "Zica Laser":                     [   0,    0,    0,    0,    0,    0, 39.7, 43.4,  33.3,     0,     0],
            "Protron Z":                      [   0,    0,    0,    0,    0,    0,    0,    0,  28.0,  46.7,  46.7],
            "Vulcan Cannon (Front)":          [   0,  3.3,  3.3,  2.0,  5.8,  2.8,  4.0,  2.8,   4.0,   5.8,  11.6],
            "Lightning Cannon":               [   0,    0,    0,    0, 15.1, 30.2, 15.1, 30.2,  30.2,     0,     0],
            "Protron (Front)":                [   0,  3.8,  7.8, 13.3, 13.3,  6.7, 20.0, 26.6,  30.0,  43.3,  40.0],
            "Missile Launcher":               [   0,  4.5,  4.5,  4.5,    0,  3.3,  7.3,  7.3,     0,   7.3,   9.0],
            "Mega Pulse (Front)":             [   0,    0,    0,    0,    0,  7.2,    0,    0,  11.8,  31.2,  31.2],
            "Heavy Missile Launcher (Front)": [   0,    0,    0,  8.7, 10.4,    0,    0, 18.6,  33.3,  18.0,  43.3],
            "Banana Blast (Front)":           [   0,  7.8,  9.3, 12.7, 14.0, 17.5, 28.0, 41.8,  47.6,  56.0,  69.6],
            "HotDog (Front)":                 [   0,    0,    0,    0,    0,    0, 18.6, 23.3,  23.8,  26.7,  26.7],
            "Hyper Pulse":                    [   0,  5.8,  7.8,  5.8,  7.8,  7.8, 11.7, 11.7,  23.3,  23.3,  34.9],
            "Shuriken Field":                 [   0,  9.3, 18.6, 28.0, 37.3, 46.7, 56.0, 46.7,  46.7,  56.0,  37.3],
            "Poison Bomb":                    [   0,    0,    0, 21.3, 26.7, 53.3, 31.1, 47.8,  62.1,  62.1,  62.1],
            "Protron Wave":                   [   0,    0,    0,  6.7,  6.7, 13.3,  6.7, 13.3,  13.3,  26.7,  33.3],
            "Guided Bombs":                   [   0,  6.7,  9.0, 13.3, 16.0,  8.0, 12.3, 10.3,  12.3,  16.3,  16.3],
            "The Orange Juicer":              [   0,  5.7,  5.7, 11.4, 11.4,  9.0,  9.0, 20.0,  24.0,  40.0,  50.0],
            "NortShip Super Pulse":           [ 5.9,  5.9, 11.6, 11.6, 17.4, 17.5,  5.8,  8.8,  11.8,  33.7,  23.5],
            "Widget Beam":                    [   0,    0,    0,    0,  5.8,    0,  5.8,  5.8,  11.6,  17.0,  17.5],
            "Sonic Impulse":                  [   0,  5.3, 10.6, 12.0, 16.0, 11.2, 15.9, 21.2,  21.2,  45.0,  50.0],
            "RetroBall":                      [   0,  4.7,  9.3,  9.3, 14.0, 18.7, 18.7,  9.3,   9.3,  18.7,  18.7],
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Starburst":                      [15.3, 12.0, 22.7, 18.0, 31.3, 23.8, 37.5, 34.8,  47.1,  69.8,  93.3],
            "Multi-Cannon (Rear)":            [ 4.6,  6.7, 13.3, 13.3, 20.0, 20.0, 26.7, 33.3,  46.7,  53.3,  60.0],
            "Sonic Wave":                     [ 6.7,  6.7, 13.0, 13.3, 17.5, 30.0, 43.0, 40.0,  40.0,  40.0,  58.0],
            "Protron (Rear)":                 [ 5.8, 11.6, 11.7, 17.3, 22.8, 28.4, 34.3, 40.9,  46.3,  40.9,  46.3],
            "Wild Ball":                      [   0,  4.9,  9.9,  7.7, 15.4, 20.9, 25.5, 31.4,  31.1,  18.2,  28.6],
            "Vulcan Cannon (Rear)":           [ 7.8,  7.8, 11.5, 11.5, 15.4, 15.4, 23.3, 23.5,  31.2,  31.2,  46.1],
            "Fireball":                       [ 3.0,  6.0, 19.2, 27.2,  4.0,  8.0, 11.8, 15.7,  15.2,  31.1,  39.7],
            "Heavy Missile Launcher (Rear)":  [ 8.1, 10.0, 15.2, 18.1, 30.5, 39.1, 50.7, 61.0, 102.7,  60.0,  79.5],
            "Mega Pulse (Rear)":              [15.6, 23.5, 28.5, 23.8, 40.0, 46.7, 46.7, 40.0,  38.0,  86.7,  86.7],
            "Banana Blast (Rear)":            [18.7, 18.7, 18.7, 18.7, 18.7,    0, 13.3,    0,   9.6,  13.3,  20.0],
            "HotDog (Rear)":                  [15.6, 23.1, 23.1, 23.1, 23.1, 18.7, 18.7, 18.7,  15.5,  13.3,  26.7],
            "Guided Micro Bombs":             [ 2.6,  4.0,  8.6,  8.6, 14.8, 17.3, 30.0, 24.0,  25.0,  26.0,  28.0],
            "Heavy Guided Bombs":             [ 4.6,  4.6,  9.1, 14.0, 17.3, 17.3, 22.5, 20.0,  20.0,  28.0,  36.0],
            "Scatter Wave":                   [ 9.3,  9.3, 15.5,  7.8, 15.5, 23.4, 30.8, 30.8,  30.8,  46.5,  46.5],
            "NortShip Spreader":              [11.7, 11.7, 23.4, 35.1, 46.8, 46.8, 58.5, 70.0, 105.0, 128.4, 128.4],
            "NortShip Spreader B":            [17.8, 24.6, 24.6, 24.6, 24.6, 24.6, 24.6, 24.6,  50.0,  50.0,  50.0],
        }
    }

    # Damage focused at a 90 degree, or close to 90 degree angle
    base_sideways = {
        # Base level: Assumes enough distance to react to enemy movement
        LogicDifficulty.option_beginner: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Protron Wave":                   [   0,    0,    0,  3.3,  3.3,  6.7,  3.3,  6.7,   6.7,   6.7,   3.3],
            "Guided Bombs":                   [   0,    0,  2.7,    0,  5.1,  4.0,  2.1,  2.6,   3.3,   6.7,   6.7],
            "The Orange Juicer":              [10.0,    0,    0,    0,    0,    0,    0,    0,     0,     0,     0],
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Starburst":                      [ 7.7,  7.7, 11.8, 11.8, 15.8, 15.8, 23.3, 23.3,  31.2,  35.6,  46.8],
            "Multi-Cannon (Rear)":            [ 2.3,  3.3,  6.7,  6.7, 10.0, 10.0, 13.3, 16.7,  23.3,  26.7,  30.0],
            "Sonic Wave":                     [ 3.3,  3.3,  3.3,  6.7,  6.7, 13.3, 20.0, 20.0,  20.0,  20.0,  20.0],
            "Protron (Rear)":                 [ 2.9,  5.8,  5.8,  8.6, 11.4, 14.2, 17.1, 20.4,  24.1,  20.4,  24.1],
            "Mega Pulse (Rear)":              [ 4.0,  5.8,  9.3,  7.8, 13.3, 16.7, 16.7, 13.3,  10.0,  33.3,  33.3],
            "Banana Blast (Rear)":            [ 9.3,  9.3,  9.3,  9.3,  9.3,    0,  6.7,    0,   4.0,     0,     0],
            "Guided Micro Bombs":             [   0,    0,    0,    0,    0,  4.5,  8.6,  9.3,  18.6,  16.3,  18.6],
            "Heavy Guided Bombs":             [   0,  1.1,  2.3,  5.8,  5.8,  5.8,  8.2,  5.8,   8.2,  13.3,  26.6],
            "Scatter Wave":                   [ 4.7,  4.7,  7.8,  3.9,  7.8, 11.7, 15.4, 15.4,  15.4,  23.3,  23.3],
            "NortShip Spreader":              [   0,    0,  5.8, 11.7, 11.7,    0,  5.8, 17.5,  35.0,     0,     0],
        },

        # Expert level: May need to move in closer to deal damage
        LogicDifficulty.option_expert: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "The Orange Juicer":              [10.0,    0,    0,    0,    0,    0, 14.0, 14.0,  14.0,  28.0,  28.0],   
        },

        # Master level: Assumes abuse of mechanics like using mode switch to reset weapon state
        LogicDifficulty.option_master: {
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Starburst":                      [10.0, 10.0, 14.3, 14.3, 15.8, 15.8, 23.3, 23.3,  31.2,  35.6,  46.8],
            "Mega Pulse (Rear)":              [ 5.4,  5.8,  9.3,  7.8, 13.3, 16.7, 16.7, 13.3,  10.0,  33.3,  33.3],
            "Heavy Guided Bombs":             [   0,  2.3,  2.3,  5.8,  5.8,  5.8,  8.2,  5.8,   8.2,  13.3,  26.6],
        },
    }

    # Similar to active, but assumes that the projectile has already passed through a solid object
    base_piercing = {
        LogicDifficulty.option_beginner: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Mega Cannon":                    [ 5.3,  5.3, 10.0,  5.3, 10.0, 10.0, 10.0, 10.2,  21.1,  21.1,  21.2],
            "Sonic Impulse":                  [11.6,  7.6, 11.6, 17.5, 23.2, 10.2, 11.6, 11.5,  11.8,  11.6,  11.8],
        }
    }

    def __init__(self, logic_difficulty: int):
        self.active = {}
        self.passive = {}
        self.sideways = {}
        self.piercing = {}

        for difficulty in range(logic_difficulty + 1):
            self.active.update(self.base_active.get(difficulty, {}))
            self.passive.update(self.base_passive.get(difficulty, {}))
            self.sideways.update(self.base_sideways.get(difficulty, {}))
            self.piercing.update(self.base_piercing.get(difficulty, {}))

        if logic_difficulty == LogicDifficulty.option_beginner:   self.logic_difficulty_multiplier = 1.4
        elif logic_difficulty == LogicDifficulty.option_standard: self.logic_difficulty_multiplier = 1.2
        elif logic_difficulty == LogicDifficulty.option_expert:   self.logic_difficulty_multiplier = 1.1
        else:                                                     self.logic_difficulty_multiplier = 1.0

    def avail_shot_types(self, weapons: List[str], max_power: int) -> Iterable[DamageValues]:
        if len(weapons) == 0:
            yield DamageValues(0.0, 0.0, 0.0, 0.0)
            return

        for weapon in weapons:
            this_weapon_active = self.active.get(weapon, [0.0]*11)
            this_weapon_passive = self.passive.get(weapon, [0.0]*11)
            this_weapon_sideways = self.sideways.get(weapon, [0.0]*11)
            this_weapon_piercing = self.sideways.get(weapon, [0.0]*11)

            for power in range(max_power):
                yield DamageValues(this_weapon_active[power], this_weapon_passive[power], 
                      this_weapon_sideways[power], this_weapon_piercing[power])

# =================================================================================================

def scale_health(world: "TyrianWorld", health: int, adjust_difficulty: int = 0) -> int:
    health_scale = {
        GameDifficulty.option_easy:         lambda x: int(x * 0.75) + 1,
        GameDifficulty.option_normal:       lambda x: x,
        GameDifficulty.option_hard:         lambda x: min(254, int(x * 1.2)),
        GameDifficulty.option_impossible:   lambda x: min(254, int(x * 1.5)),
        5:                                  lambda x: min(254, int(x * 1.8)),
        GameDifficulty.option_suicide:      lambda x: min(254, int(x * 2)),
        7:                                  lambda x: min(254, int(x * 3)),
        GameDifficulty.option_lord_of_game: lambda x: min(254, int(x * 4)),
        9:                                  lambda x: min(254, int(x * 8)),
        10:                                 lambda x: min(254, int(x * 8)),
    }
    difficulty = min(max(1, world.options.difficulty + adjust_difficulty), 10)
    return health_scale[difficulty](health)

def max_or_threshold(threshold: float, iterator):
    if threshold < 0.0:
        return 0.0
    cur_max = 0.0
    for result in iterator:
        if result >= threshold:
            return result
        if result > cur_max:
            cur_max = result
    return cur_max

def get_owned_weapon_state(state: "CollectionState", player: int):
    return (
        [name for name in LocalItemData.front_ports if state.has(name, player)],
        [name for name in LocalItemData.rear_ports if state.has(name, player)],
        state.count("Maximum Power Up", player) + 1
    )

# =================================================================================================

def can_deal_damage(state: "CollectionState", player: int, damage_tables: DamageTables, dps: float):
    owned_front, owned_rear, power_level_max = get_owned_weapon_state(state, player)

    total_damage = max_or_threshold(dps,
          (data.active for data in damage_tables.avail_shot_types(owned_front, power_level_max)))
    total_damage += max_or_threshold(dps - total_damage,
          (data.active for data in damage_tables.avail_shot_types(owned_rear, power_level_max)))
    return total_damage >= dps

def can_deal_passive_damage(state: "CollectionState", player: int, damage_tables: DamageTables, dps: float):
    owned_front, owned_rear, power_level_max = get_owned_weapon_state(state, player)

    total_damage = max_or_threshold(dps,
          (data.passive for data in damage_tables.avail_shot_types(owned_rear, power_level_max)))
    total_damage += max_or_threshold(dps - total_damage,
          (data.passive for data in damage_tables.avail_shot_types(owned_front, power_level_max)))
    return total_damage >= dps

def can_deal_sideways_damage(state: "CollectionState", player: int, damage_tables: DamageTables, dps: float):
    owned_front, owned_rear, power_level_max = get_owned_weapon_state(state, player)

    total_damage = max_or_threshold(dps,
          (data.sideways for data in damage_tables.avail_shot_types(owned_rear, power_level_max)))
    total_damage += max_or_threshold(dps - total_damage,
          (data.sideways for data in damage_tables.avail_shot_types(owned_front, power_level_max)))
    return total_damage >= dps

def can_deal_piercing_damage(state: "CollectionState", player: int, damage_tables: DamageTables, dps: float):
    owned_front, owned_rear, power_level_max = get_owned_weapon_state(state, player)

    total_damage = max_or_threshold(dps,
          (data.piercing for data in damage_tables.avail_shot_types(owned_rear, power_level_max)))
    total_damage += max_or_threshold(dps - total_damage,
          (data.piercing for data in damage_tables.avail_shot_types(owned_front, power_level_max)))
    return total_damage >= dps

def can_deal_mixed_damage(state: "CollectionState", player: int, damage_tables: DamageTables,
      active_dps: Optional[float] = None, passive_dps: Optional[float] = None, sideways_dps: Optional[float] = None):
    owned_front = [name for name in LocalItemData.front_ports if state.has(name, player)]
    owned_rear = [name for name in LocalItemData.rear_ports if state.has(name, player)]
    power_level_max = state.count("Maximum Power Up", player) + 1

    # For multiple simultaneous types of DPS, our search is complicated by the fact that we need to find a set of
    # weapon + power level combinations that simultaneously satisfies all, so we can't just take their maximums.
    raise NotImplementedError

def can_damage_with_weapon(state: "CollectionState", player: int, damage_tables: DamageTables,
      weapon: str, dps: float):
    if not state.has(weapon, player):
        return False

    # Workaround: We assume power 11 can defeat any boss instead of just using DPS numbers in that case
    # It may be slower than we like but it should still be possible
    power_level_max = state.count("Maximum Power Up", player) + 1
    if power_level_max == 11:
        return True

    total_damage = max_or_threshold(dps,
          (data.active for data in damage_tables.avail_shot_types([weapon], power_level_max)))
    return total_damage >= dps

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

def has_twiddle(state: "CollectionState", player: int, action: SpecialValues):
    world = state.multiworld.worlds[player]
    return action in [twiddle.action for twiddle in world.twiddles]

def has_invulnerability(state: "CollectionState", player: int):
    return state.has("Invulnerability", player) or has_twiddle(state, player, SpecialValues.Invulnerability)

def has_repulsor(state: "CollectionState", player: int):
    return state.has("Repulsor", player) or has_twiddle(state, player, SpecialValues.Repulsor)

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

    # Four trigger enemies among the starting U-Ship sets, need enough damage to clear them out
    if (world.options.difficulty >= GameDifficulty.option_hard):
        enemy_health = scale_health(world, 19) # Not tied to a specific enemy
        logic_location_rule(world, "TYRIAN (Episode 1) - HOLES Warp Orb", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, dps=health/2.0)
              or can_deal_passive_damage(state, world.player, world.damage_tables, dps=health/1.5))

    enemy_health = scale_health(world, 20) # Health of rock
    logic_location_rule(world, "TYRIAN (Episode 1) - BUBBLES Warp Rock", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/3.6))

    boss_health = scale_health(world, 100) + 254 # Health of one wing + boss
    logic_location_rule(world, "TYRIAN (Episode 1) - Boss", lambda state, health=boss_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/75.0))

    # ===== BUBBLES ===========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_all_locations_exclude(world, "BUBBLES (Episode 1) - Coin Rain")

    enemy_health = scale_health(world, 20) # Health of red bubbles (in all cases)
    logic_entrance_rule(world, "Can shop at BUBBLES (Episode 1)", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/4.0))

    logic_location_rule(world, "BUBBLES (Episode 1) - Orbiting Bubbles", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/3.0)
          or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=health/4.0))
    logic_location_rule(world, "BUBBLES (Episode 1) - Shooting Bubbles", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.2)
          or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=health/4.0))
    logic_all_locations_rule(world, "BUBBLES (Episode 1) - Coin Rain", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.9))
    logic_location_rule(world, "BUBBLES (Episode 1) - Final Bubble Line", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/4.0))

    # ===== HOLES =============================================================
    logic_entrance_rule(world, "Can shop at HOLES (Episode 1)", lambda state, health=enemy_health:
          can_deal_passive_damage(state, world.player, world.damage_tables, dps=21.0))
   
    boss_health = scale_health(world, 100) + 254 # Health of one wing + boss
    logic_location_rule(world, "HOLES (Episode 1) - Boss Ship Fly-By 1", lambda state, health=boss_health:
          has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, dps=health/5.0))
    logic_location_rule(world, "HOLES (Episode 1) - Boss Ship Fly-By 2", lambda state, health=boss_health:
          has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, dps=health/5.0))

    # TODO Use a mixed rule instead of just and-ing rules
    logic_location_rule(world, "HOLES (Episode 1) - Lander after Spinners", lambda state:
          can_deal_passive_damage(state, world.player, world.damage_tables, dps=21.0))
    logic_location_rule(world, "HOLES (Episode 1) - Boss Ship Fly-By 1", lambda state, health=boss_health:
          can_deal_passive_damage(state, world.player, world.damage_tables, dps=21.0))
    logic_location_rule(world, "HOLES (Episode 1) - U-Ships after Boss Fly-By", lambda state:
          can_deal_passive_damage(state, world.player, world.damage_tables, dps=21.0))
    logic_location_rule(world, "HOLES (Episode 1) - Boss Ship Fly-By 2", lambda state, health=boss_health:
          can_deal_passive_damage(state, world.player, world.damage_tables, dps=21.0))
    logic_location_rule(world, "HOLES (Episode 1) - Before Speed Up Section", lambda state:
          can_deal_passive_damage(state, world.player, world.damage_tables, dps=21.0))

    # ===== SOH JIN ===========================================================
    enemy_health = scale_health(world, 40) # Single wall tile
    logic_location_rule(world, "SOH JIN (Episode 1) - Walled-in Orb Launcher", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/4.6))

    # ===== ASTEROID1 =========================================================
    logic_entrance_behind_location(world, "Can shop at ASTEROID1 (Episode 1)", "ASTEROID1 (Episode 1) - Boss")

    enemy_health = scale_health(world, 25) + (scale_health(world, 5) * 2) # Face rock, plus tiles before it
    logic_location_rule(world, "ASTEROID1 (Episode 1) - ASTEROID? Warp Orb", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/4.4))

    boss_health = scale_health(world, 100) # Only the boss dome
    logic_location_rule(world, "ASTEROID1 (Episode 1) - Boss", lambda state, health=boss_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/30.0))

    # ===== ASTEROID2 =========================================================    
    logic_entrance_behind_location(world, "Can shop at ASTEROID2 (Episode 1)", "ASTEROID2 (Episode 1) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1")
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2")
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret")

    enemy_health = scale_health(world, 30) # All tanks
    logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Bridge", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/2.1))

    # Tank Turn-around Secrets 1 and 2:
    # On Standard or below, assume most damage will come only after the tank secret items are active
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, dps=health/2.3))
        logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, dps=health/3.9))

    enemy_health = scale_health(world, 25) # Only the face rock containing the orb
    logic_location_rule(world, "ASTEROID2 (Episode 1) - MINEMAZE Warp Orb", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/4.4))

    logic_location_rule(world, "ASTEROID2 (Episode 1) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, dps=10.0))

    # ===== ASTEROID? =========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "ASTEROID? (Episode 1) - WINDY Warp Orb")

    enemy_health = scale_health(world, 40) # Launchers, and the secret ships
    logic_location_rule(world, "ASTEROID? (Episode 1) - Welcoming Launchers 1", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/3.5))
    logic_location_rule(world, "ASTEROID? (Episode 1) - Welcoming Launchers 2", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/3.5))

    logic_location_rule(world, "ASTEROID? (Episode 1) - Quick Shot 1", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.36))
    logic_location_rule(world, "ASTEROID? (Episode 1) - Quick Shot 2", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.36))

    # ===== MINEMAZE ==========================================================
    enemy_health = scale_health(world, 20) # Gates
    logic_entrance_rule(world, "Can shop at MINEMAZE (Episode 1)", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/3.8))
    logic_all_locations_rule(world, "MINEMAZE (Episode 1)", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/3.8))

    # ===== WINDY =============================================================
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "WINDY (Episode 1) - Central Question Mark")

    logic_location_rule(world, "WINDY (Episode 1) - Central Question Mark", lambda state:
          has_invulnerability(state, world.player) or has_armor_level(state, world.player, 14))

    enemy_health = scale_health(world, 20) # Question mark block health
    logic_location_rule(world, "WINDY (Episode 1) - Central Question Mark", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.4))

    if (world.options.contact_bypasses_shields):
        logic_location_rule(world, "WINDY (Episode 1) - Central Question Mark", lambda state:
              has_armor_level(state, world.player, 7))

    enemy_health = scale_health(world, 10) # Regular block health
    if (world.options.contact_bypasses_shields):
        logic_entrance_rule(world, "Can shop at WINDY (Episode 1)", lambda state, health=enemy_health:
              has_armor_level(state, world.player, 7)
              and can_deal_damage(state, world.player, world.damage_tables, dps=health/1.4))
    else:
        logic_entrance_rule(world, "Can shop at WINDY (Episode 1)", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, dps=health/1.4))

    # ===== SAVARA ============================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at SAVARA (Episode 1)", "SAVARA (Episode 1) - Boss")

    enemy_health = scale_health(world, 60) # Large planes
    logic_location_rule(world, "SAVARA (Episode 1) - Huge Plane, Speeds By", lambda state, health=enemy_health:
          has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, dps=health/1.025))

    enemy_health = scale_health(world, 14) # Vulcan plane with item
    # The vulcan shots hurt a lot, so optimal kill would be with passive DPS if possible
    logic_location_rule(world, "SAVARA (Episode 1) - Vulcan Plane", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.6)
          or can_deal_passive_damage(state, world.player, world.damage_tables, dps=health/2.4))

    logic_location_rule(world, "SAVARA (Episode 1) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, dps=254/60))

    # ===== SAVARA II =========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at SAVARA II (Episode 1)", "SAVARA II (Episode 1) - Boss")

    logic_all_locations_rule(world, "SAVARA II (Episode 1)", lambda state:
          has_armor_level(state, world.player, 7)
          and has_generator_level(state, world.player, 2))

    logic_location_rule(world, "SAVARA II (Episode 1) - Green Plane Sequence 1", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, 7.0))
    logic_location_rule(world, "SAVARA II (Episode 1) - Green Plane Sequence 2", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, 7.0))

    enemy_health = scale_health(world, 60, adjust_difficulty=-1) # Large planes
    logic_location_rule(world, "SAVARA II (Episode 1) - Large Plane Amidst Turrets", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/2.3))

    enemy_health = scale_health(world, 14) # Vulcan plane with item
    # The vulcan shots hurt a lot, so optimal kill would be with passive DPS if possible
    logic_location_rule(world, "SAVARA II (Episode 1) - Vulcan Planes Near Blimp", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.6)
          or can_deal_passive_damage(state, world.player, world.damage_tables, dps=health/2.4))

    logic_location_rule(world, "SAVARA (Episode 1) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, dps=254/50))

    # ===== MINES =============================================================
    enemy_health = scale_health(world, 20) # Rotating Orbs
    logic_location_rule(world, "MINES (Episode 1) - Regular Spinning Orbs", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.0)
          or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=health/2.7))
    logic_location_rule(world, "MINES (Episode 1) - Regular Spinning Orbs", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/0.5)
          or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=health/1.2))

    # Blue mine has static health (does not depend on difficulty)
    logic_location_rule(world, "MINES (Episode 1) - Blue Mine", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, dps=30/3.0))

    # ===== DELIANI ===========================================================
    logic_entrance_behind_location(world, "Can shop at DELIANI (Episode 1)", "DELIANI (Episode 1) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "DELIANI (Episode 1) - Tricky Rail Turret")

    logic_all_locations_rule(world, "DELIANI (Episode 1)", lambda state:
          has_generator_level(state, world.player, 2))

    enemy_health = scale_health(world, 30) # Rail turret
    logic_location_rule(world, "DELIANI (Episode 1) - Tricky Rail Turret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/2.2))

    logic_location_rule(world, "DELIANI (Episode 1) - Ambush", lambda state:
          has_armor_level(state, world.player, 9))
    logic_location_rule(world, "DELIANI (Episode 1) - Last Cross Formation", lambda state:
          has_armor_level(state, world.player, 9))
    logic_location_rule(world, "DELIANI (Episode 1) - Boss", lambda state:
          has_armor_level(state, world.player, 9))

    enemy_health = scale_health(world, 25) # Two-tile wide turret ships
    logic_location_rule(world, "DELIANI (Episode 1) - Ambush", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/1.6))
    logic_location_rule(world, "DELIANI (Episode 1) - Last Cross Formation", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/1.6))

    boss_health = (scale_health(world, 80) * 3) + scale_health(world, 200) # Repulsor orbs and boss
    logic_location_rule(world, "DELIANI (Episode 1) - Boss", lambda state, health=boss_health:
          can_deal_damage(state, world.player, world.damage_tables, health/26.0))

    # ===== SAVARA V ==========================================================
    logic_entrance_behind_location(world, "Can shop at SAVARA V (Episode 1)", "SAVARA V (Episode 1) - Boss")

    logic_all_locations_rule(world, "DELIANI (Episode 1)", lambda state:
          has_generator_level(state, world.player, 2))

    enemy_health = scale_health(world, 70) # Blimp
    logic_location_rule(world, "SAVARA V (Episode 1) - Super Blimp", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/1.5))

    logic_location_rule(world, "SAVARA V (Episode 1) - Mid-Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, 254/15.0))
    logic_location_rule(world, "SAVARA V (Episode 1) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, 254/15.0))

    # ===== ASSASSIN ==========================================================
    logic_entrance_behind_location(world, "Can shop at ASSASSIN (Episode 1)", "ASSASSIN (Episode 1) - Boss")

    logic_all_locations_rule(world, "ASSASSIN (Episode 1)", lambda state:
          has_armor_level(state, world.player, 9) and has_generator_level(state, world.player, 3))

    if Episode.Escape in world.all_boss_weaknesses:
        logic_location_rule(world, "ASSASSIN (Episode 1) - Boss", lambda state:
              state.has("Data Cube (Episode 1)", world.player)
              and can_damage_with_weapon(state, world.player, world.damage_tables, world.all_boss_weaknesses[1], 25.0))
    else:
        logic_location_rule(world, "ASSASSIN (Episode 1) - Boss", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, 25.0))

# -----------------------------------------------------------------------------

def episode_2_rules(world: "TyrianWorld"):
    # ===== TORM ==============================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at TORM (Episode 2)", "TORM (Episode 2) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret")

    # On standard or below, require killing the dragon behind the secret ship
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        enemy_health = scale_health(world, 40)
        logic_location_rule(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, health/1.6))

    logic_location_rule(world, "TORM (Episode 2) - Boss Ship Fly-By", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, 254/4.4))

    # Technically this boss has 254 health, but compensating for constant movement all over the screen
    logic_location_rule(world, "TORM (Episode 2) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, (254*1.75)/32.0))

    # ===== GYGES =============================================================
    logic_entrance_behind_location(world, "Can shop at GYGES (Episode 2)", "GYGES (Episode 2) - Boss")

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "GYGES (Episode 2) - GEM WAR Warp Orb")

    enemy_health = scale_health(world, 10) * 6 # Orbsnakes
    logic_location_rule(world, "GYGES (Episode 2) - Orbsnake", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/5.0))

    logic_location_rule(world, "GYGES (Episode 2) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, 254/45.0))

    # ===== ASTCITY ===========================================================
    logic_entrance_behind_location(world, "Can shop at ASTCITY (Episode 2)", 
          "ASTCITY (Episode 2) - Ending Turret Group")

    logic_all_locations_rule(world, "ASTCITY (Episode 2)", lambda state:
          has_armor_level(state, world.player, 7))

    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "ASTCITY (Episode 2) - MISTAKES Warp Orb")

    enemy_health = scale_health(world, 30, adjust_difficulty=-1) # Building
    logic_location_rule(world, "ASTCITY (Episode 2) - Warehouse 92", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/4.0))

    # In all likelihood this can be obliterated with a superbomb that you obtain in the level, but we don't consider
    # superbombs logic in any way, so
    logic_location_rule(world, "ASTCITY (Episode 2) - Ending Turret Group", lambda state:
          can_deal_passive_damage(state, world.player, world.damage_tables, 16.0))

    # ===== GEM WAR ===========================================================

    # ===== MARKERS ===========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "MARKERS (Episode 2) - Car Destroyer Secret")

    # Flying through this stage is relatively easy *unless* HardContact is turned on.
    if (world.options.contact_bypasses_shields):
        logic_all_locations_rule(world, "MARKERS (Episode 2)", lambda state:
              has_armor_level(state, world.player, 8))
        logic_entrance_rule(world, "Can shop at MARKERS (Episode 2)", lambda state:
              has_armor_level(state, world.player, 8))

    enemy_health = scale_health(world, 30) + (scale_health(world, 6) * 4) # Minelayer + estimated 4 mines
    logic_location_rule(world, "MARKERS (Episode 2) - Persistent Mine-Layer", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/7.1))

    enemy_health = scale_health(world, 20) # Turrets
    logic_location_rule(world, "MARKERS (Episode 2) - Right Path Turret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/3.8))
    logic_location_rule(world, "MARKERS (Episode 2) - Left Path Turret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/3.8))
    logic_location_rule(world, "MARKERS (Episode 2) - End Section Turret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/3.8))

    enemy_health = scale_health(world, 10) # Cars
    logic_location_rule(world, "MARKERS (Episode 2) - Car Destroyer Secret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, health/3.0))

    # ===== MISTAKES ==========================================================
    if (world.options.logic_difficulty == LogicDifficulty.option_beginner):
        logic_location_exclude(world, "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 1")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Claws - Trigger Enemy 1")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Claws - Trigger Enemy 2")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Super Bubble Spawner")
    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 2")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Anti-Softlock")

    enemy_health = scale_health(world, 10) # Most trigger enemies
    logic_location_rule(world, "MISTAKES (Episode 2) - Claws - Trigger Enemy 2", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.2))

    enemy_health = scale_health(world, 10) * 6 # Orbsnakes
    logic_location_rule(world, "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 1", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/5.5)
          or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=(health/6)/5.5))
    logic_location_rule(world, "MISTAKES (Episode 2) - Orbsnakes - Trigger Enemy 2", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/0.8)
          or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=(health/6)/0.8))

    # ===== SOH JIN ===========================================================

    # ===== BOTANY A ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at BOTANY A (Episode 2)", "BOTANY A (Episode 2) - Boss")

    # ===== BOTANY B ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at BOTANY B (Episode 2)", "BOTANY B (Episode 2) - Boss")

    logic_all_locations_rule(world, "BOTANY B (Episode 2)", lambda state:
          has_armor_level(state, world.player, 9)
          and has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, 18.0))

    # ===== GRYPHON ===========================================================
    logic_entrance_behind_location(world, "Can shop at GRYPHON (Episode 2)", "GRYPHON (Episode 2) - Boss")

    logic_all_locations_rule(world, "GRYPHON (Episode 2)", lambda state:
          has_armor_level(state, world.player, 10)
          and has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, 22.0)
          and can_deal_passive_damage(state, world.player, world.damage_tables, 16.0))

    if Episode.Treachery in world.all_boss_weaknesses:
        logic_location_rule(world, "GRYPHON (Episode 2) - Boss", lambda state:
              state.has("Data Cube (Episode 2)", world.player)
              and can_damage_with_weapon(state, world.player, world.damage_tables, world.all_boss_weaknesses[2], 22.0))

# -----------------------------------------------------------------------------

def episode_3_rules(world: "TyrianWorld"):
    # ===== GAUNTLET ==========================================================

    # ===== IXMUCANE ==========================================================
    if (not boss_timeout_in_logic(world)):
        logic_entrance_behind_location(world, "Can shop at IXMUCANE (Episode 3)", "IXMUCANE (Episode 3) - Boss")

    # ===== BONUS =============================================================
    logic_entrance_behind_location(world, "Can shop at IXMUCANE (Episode 3)",
          "BONUS (Episode 3) - Sonic Wave Hell Turret")

    if (world.options.logic_difficulty <= LogicDifficulty.option_standard):
        logic_location_exclude(world, "BONUS (Episode 3) - Sonic Wave Hell Turret")
        logic_all_locations_exclude(world, "Shop - BONUS (Episode 3)")

    # Turrets have only one health; they die to any damage, but are guarded from front and back.
    if (world.options.logic_difficulty <= LogicDifficulty.option_expert):
        logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 1", lambda state:
            can_deal_passive_damage(state, world.player, world.damage_tables, dps=0.2)
            or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=0.2))
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state:
            can_deal_passive_damage(state, world.player, world.damage_tables, dps=0.2)
            or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=0.2))

    # Doesn't sway left/right like the other two
    logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 2", lambda state:
        can_deal_passive_damage(state, world.player, world.damage_tables, dps=0.2)
        or can_deal_piercing_damage(state, world.player, world.damage_tables, dps=0.2))

    # To pass the turret onslaught
    logic_location_rule(world, "BONUS (Episode 3) - Behind Onslaught 1", lambda state:
          has_armor_level(state, world.player, 8) and has_generator_level(state, world.player, 3))
    logic_location_rule(world, "BONUS (Episode 3) - Behind Onslaught 2", lambda state:
          has_armor_level(state, world.player, 8) and has_generator_level(state, world.player, 3))
    logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 2", lambda state:
          has_armor_level(state, world.player, 8) and has_generator_level(state, world.player, 3))

    enemy_health = ((scale_health(world, 25) - 10) * 4) # Two-wide turret, to take down to damaged (non-firing) state
    logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 2", lambda state, health=enemy_health:
          has_repulsor(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, dps=health/3.6))

    # Do you have knowledge of the safe spot through this section? Master assumes you do, anything else doesn't.
    # For Master logic apply the above to Sonic Wave Hell Turret too.
    if (world.options.logic_difficulty == LogicDifficulty.option_master):
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state:
              has_armor_level(state, world.player, 8) and has_generator_level(state, world.player, 3))
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state, health=enemy_health:
              has_repulsor(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps=health/3.6))
    else: # We need the repulsor or a sideways damage source and a lot of health.
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state:
              has_generator_level(state, world.player, 3))
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state, health=enemy_health:
              (
                  has_repulsor(state, world.player)
                  and has_armor_level(state, world.player, 8)
              ) or (
                  has_armor_level(state, world.player, 12)
                  and can_deal_damage(state, world.player, world.damage_tables, dps=health/3.6)
                  and can_deal_sideways_damage(state, world.player, world.damage_tables, dps=4.0)
              ))

    # To actually get the items from turret onslaught
    enemy_health = scale_health(world, 25) + scale_health(world, 3) # Single two-tile turret, plus item ship
    logic_location_rule(world, "BONUS (Episode 3) - Behind Onslaught 1", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.8))
    logic_location_rule(world, "BONUS (Episode 3) - Behind Onslaught 2", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, dps=health/1.8))

    # ===== STARGATE ==========================================================
    logic_entrance_behind_location(world, "Can shop at STARGATE (Episode 3)",
        "STARGATE (Episode 3) - Super Bubble Spawner")

    # Just need some way of combating the bubble spam that happens after the last normal location
    logic_location_rule(world, "STARGATE (Episode 3) - Super Bubble Spawner", lambda state:
        can_deal_passive_damage(state, world.player, world.damage_tables, 7.0))

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

    logic_location_rule(world, "FLEET (Episode 3) - Boss", lambda state:
          has_armor_level(state, world.player, 12) and has_generator_level(state, world.player, 4))
    logic_location_rule(world, "FLEET (Episode 3) - Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, dps=50.0))

    if Episode.MissionSuicide in world.all_boss_weaknesses:
        logic_location_rule(world, "FLEET (Episode 3) - Boss", lambda state:
              state.has("Data Cube (Episode 3)", world.player)
              and can_damage_with_weapon(state, world.player, world.damage_tables, world.all_boss_weaknesses[3], 30.0))

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
