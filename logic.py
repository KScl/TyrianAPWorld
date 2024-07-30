# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from itertools import product
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, Union

from BaseClasses import LocationProgressType as LPType

from worlds.generic.Rules import add_rule

from .items import Episode
from .options import GameDifficulty, LogicDifficulty
from .twiddles import SpecialValues

if TYPE_CHECKING:
    from BaseClasses import CollectionState

    from . import TyrianWorld


class DPS:
    _type_active: bool
    _type_passive: bool
    _type_sideways: bool
    _type_piercing: bool
    active: float
    passive: float
    sideways: float
    piercing: float

    def __init__(self, active: float = 0.0, passive: float = 0.0, sideways: float = 0.0, piercing: float = 0.0):
        self.active = active
        self.passive = passive
        self.sideways = sideways
        self.piercing = piercing
        self._type_active = (active > 0.0)
        self._type_passive = (passive > 0.0)
        self._type_sideways = (sideways > 0.0)
        self._type_piercing = (piercing > 0.0)

    def __sub__(self, other: "DPS") -> "DPS":
        new_dps = DPS.__new__(DPS)
        new_dps.active = max(self.active - other.active, 0.0)
        new_dps.passive = max(self.passive - other.passive, 0.0)
        new_dps.sideways = max(self.sideways - other.sideways, 0.0)
        new_dps.piercing = max(self.piercing - other.piercing, 0.0)
        new_dps._type_active = (new_dps.active > 0.0)
        new_dps._type_passive = (new_dps.passive > 0.0)
        new_dps._type_sideways = (new_dps.sideways > 0.0)
        new_dps._type_piercing = (new_dps.piercing > 0.0)
        return new_dps

    def meets_requirements(self, requirements: "DPS") -> Tuple[bool, float]:
        distance = 0.0

        # Apply some weighting to distance
        # Rear weapons can easily take care of passive and sideways requirements
        # But active is much harder, and piercing is entirely impossible
        if requirements._type_piercing and self.piercing < requirements.piercing:
            return (False, 99999.0)
        if requirements._type_active and self.active < requirements.active:
            distance += (requirements.active - self.active) * 4.0
        if requirements._type_passive and self.passive < requirements.passive:
            distance += (requirements.passive - self.passive) * 0.8
        if requirements._type_sideways and self.sideways < requirements.sideways:
            distance += (requirements.sideways - self.sideways) * 1.8

        return ((distance < 0.0001), distance)

    # As above, but doesn't check for distance and early-outs on failure.
    def fast_meets_requirements(self, requirements: "DPS") -> bool:
        return (
              not (requirements._type_active and self.active < requirements.active)
              and not (requirements._type_passive and self.passive < requirements.passive)
              and not (requirements._type_sideways and self.sideways < requirements.sideways)
              and not (requirements._type_piercing and self.piercing < requirements.piercing)
        )


class DamageTables:
    # Local versions, used when instantiated, holds all rules for a given logic difficulty merged together
    local_power_provided: List[int]
    local_weapon_dps: Dict[str, List[DPS]]

    # Multiplier for all target values, based on options.logic_difficulty
    logic_difficulty_multiplier: float

    # ================================================================================================================
    # Maximum amount of generator power use we expect for each logic difficulty
    generator_power_provided: Dict[int, List[int]] = {
        # Difficulty --------------Power  Non MR9 M12 C12 SMF AMF GPW
        LogicDifficulty.option_beginner: [  0,  9, 12, 16, 21, 25, 41],  # -1, -2, -3, -4, -5, -9 (for shield recharge)
        LogicDifficulty.option_standard: [  0, 10, 14, 19, 25, 30, 50],  # Base power levels of each generator
        LogicDifficulty.option_expert:   [  0, 11, 16, 21, 28, 33, 55],  # +1, +2, +2, +3, +3, +5
        LogicDifficulty.option_master:   [  0, 12, 17, 23, 30, 35, 58],  # +2, +3, +4, +5, +5, +8
        LogicDifficulty.option_no_logic: [ 99, 99, 99, 99, 99, 99, 99],
    }

    # ================================================================================================================
    # Generator break-even points (demand == production)
    # For reference: Basic shield break-even point is 9 power
    generator_power_required: Dict[str, List[int]] = {
        # Front Weapons ----------- Power  --1- --2- --3- --4- --5- --6- --7- --8- --9- -10- -11-
        "Pulse-Cannon":                   [  8,   6,   6,   6,   5,   5,   5,   5,   5,   5,   5],
        "Multi-Cannon (Front)":           [ 10,  10,   8,   8,   7,   7,   7,   7,   7,   7,   7],
        "Mega Cannon":                    [ 13,  13,  13,  13,  13,  13,  13,  13,  13,  13,  13],
        "Laser":                          [ 20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20],
        "Zica Laser":                     [  9,  10,  10,  11,  11,  11,  11,  13,  13,  11,  11],
        "Protron Z":                      [ 14,  12,  14,  14,  12,  14,  14,  14,  14,  14,  14],
        "Vulcan Cannon (Front)":          [ 10,  10,  10,  10,  10,  10,   7,   7,   7,  10,  20],
        "Lightning Cannon":               [ 12,  12,  12,  12,  12,  12,  12,  12,  12,  23,  35],
        "Protron (Front)":                [ 10,   8,   8,   7,   7,   7,   7,   7,   7,   7,   7],
        "Missile Launcher":               [  6,   5,   5,   4,   4,   4,   4,   4,   4,   4,   4],
        "Mega Pulse (Front)":             [ 15,  20,  12,  15,  20,  10,  10,  10,  10,  10,  10],
        "Heavy Missile Launcher (Front)": [ 10,  13,  18,   8,  10,  13,  18,  15,  13,  11,   9],
        "Banana Blast (Front)":           [  3,   3,   4,   4,   4,   5,   4,   4,   3,   4,   5],
        "HotDog (Front)":                 [ 10,  13,   8,  10,   8,  10,   8,   7,   7,   6,   6],
        "Hyper Pulse":                    [ 17,  12,  17,  12,  17,  17,  12,  12,  10,  10,  12],
        "Shuriken Field":                 [ 14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14],
        "Poison Bomb":                    [  9,  11,  13,  13,  17,  17,  20,  15,  20,  20,  20],
        "Protron Wave":                   [  8,   5,   6,   6,   6,   6,   6,   6,   6,   6,   6],
        "Guided Bombs":                   [  8,  10,  12,  10,   6,   6,   6,   8,   4,   4,   4],
        "The Orange Juicer":              [  6,   7,   7,   7,   7,   5,   5,   6,   7,   6,   6],
        "NortShip Super Pulse":           [ 12,  12,  12,  12,  12,  12,  12,  12,  12,  12,  12],
        "Atomic RailGun":                 [ 25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25],
        "Widget Beam":                    [ 13,  13,  10,  10,  10,  10,  10,  10,  10,  10,  10],
        "Sonic Impulse":                  [ 12,  17,  12,  12,  12,  17,  12,  12,  12,  12,  12],
        "RetroBall":                      [ 10,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10],
        "Needle Laser":                   [  6,   7,   7,   6,   6,   6,   6,   6,   6,   6,   6],
        "Pretzel Missile":                [  8,   8,   8,   8,   8,   8,   8,   8,   8,   8,   8],
        "Dragon Frost":                   [  6,   5,   4,   4,   4,   4,   3,   3,   3,   3,   2],
        "Dragon Flame":                   [  8,   8,  10,   7,  10,   7,   8,  10,   5,   7,   4],
        # Rear Weapons ------------ Power  --1- --2- --3- --4- --5- --6- --7- --8- --9- -10- -11-
        "Starburst":                      [  7,   7,  10,  10,   7,   7,  10,  10,   7,   5,   7],
        "Multi-Cannon (Rear)":            [  8,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6],
        "Sonic Wave":                     [  7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7],
        "Protron (Rear)":                 [  6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6],
        "Wild Ball":                      [  7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7],
        "Vulcan Cannon (Rear)":           [  7,   7,   5,   5,   7,   7,  10,   7,   7,   7,  10],
        "Fireball":                       [  4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4],
        "Heavy Missile Launcher (Rear)":  [ 10,  13,  10,  11,  10,  13,  11,  13,  15,  13,  15],
        "Mega Pulse (Rear)":              [ 30,  22,  17,  15,  13,  13,  13,  13,  13,  13,  13],
        "Banana Blast (Rear)":            [  4,   4,   4,   4,   4,   1,   1,   1,   1,   1,   1],
        "HotDog (Rear)":                  [ 13,  10,  10,  10,  10,   8,   8,   8,   7,   6,   6],
        "Guided Micro Bombs":             [  4,   5,   5,   5,   5,   5,   5,   6,   6,   6,   6],
        "Heavy Guided Bombs":             [  4,   4,   4,   4,   4,   4,   4,   4,   4,   5,   4],
        "Scatter Wave":                   [  8,   8,   7,   7,   7,   7,   7,   7,   7,   7,   7],
        "NortShip Spreader":              [ 12,  12,  12,  12,  12,  12,  12,  12,  12,  12,  12],
        "NortShip Spreader B":            [ 15,  10,  10,  10,  10,  10,  10,  10,  10,  10,  10],
        "People Pretzels":                [  6,   7,   8,  10,  10,   7,   5,   4,   4,   3,   3],
    }

    # ================================================================================================================
    # Damage focused on single direct target
    base_active: Dict[int, Dict[str, List[float]]] = {
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
            "Needle Laser":                   [ 5.7, 10.0,  6.7, 10.5, 11.7, 11.7, 17.5, 20.5,  29.4,  17.5,  23.4],
            "Pretzel Missile":                [ 7.8, 11.7, 15.6, 11.7, 11.7, 11.7, 23.7, 23.7,  31.2,  35.1,  35.1],
            "Dragon Frost":                   [ 8.8,    0,  5.8,  9.2,  5.0,  7.5,  7.5,  7.5,   9.7,   9.5,   9.3],
            "Dragon Flame":                   [ 7.7,  7.7,  9.3, 10.0,  9.3, 16.7, 19.8, 23.3,  36.4,  46.7,  22.8],
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Sonic Wave":                     [ 6.7, 10.0,  6.7,  6.7,  6.7, 20.0, 20.0, 20.0,  20.0,  20.0,  20.0],
            "Wild Ball":                      [ 5.0,  5.0,  5.0,  7.5,  7.5,  7.5,    0,  5.0,     0,  18.2,  18.2],
            "Fireball":                       [ 3.0,  6.0,    0,    0,  4.0,  8.0,  6.7,  8.0,  15.2,  15.2,  15.2],
            "Mega Pulse (Rear)":              [   0,    0,    0,    0,    0,    0,  6.7,    0,     0,     0,  40.0],
            "Banana Blast (Rear)":            [   0,    0,    0,    0,    0, 35.0, 35.0, 25.0,  25.0,  35.0,  45.0],
            "HotDog (Rear)":                  [   0,    0,    0,    0,    0,    0,    0,    0,     0,   6.7,     0],
            "Scatter Wave":                   [   0,    0,    0,  3.8,  3.8,  1.9,    0,  3.8,   7.5,     0,     0],
            "NortShip Spreader B":            [   0,    0,    0,    0,    0,    0,    0,  2.3,     0,   2.3,   2.3],
            "People Pretzels":                [   0,  3.5,  2.5,  1.8,  1.8,  2.5,  3.2,  3.4,   5.5,   4.5,   3.8],
        },

        # Expert level: Assumes getting up closer to an enemy so more bullets can hit
        LogicDifficulty.option_expert: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Mega Cannon":                    [ 7.8, 15.2, 14.1,  7.8, 15.2, 16.0, 16.0, 16.0,  26.0,  26.0,  26.0],
            "Zica Laser":                     [16.3, 23.4, 28.8, 38.2, 49.0, 52.0, 56.4, 96.7, 106.7, 110.0, 127.5],
            "Protron Z":                      [14.0, 19.0, 14.0, 23.3, 23.5, 37.3, 46.7, 60.7,  51.3,  60.7,  37.3],
            "Vulcan Cannon (Front)":          [11.7, 11.7, 11.7, 11.7, 10.2, 10.2, 15.6, 15.6,  13.7,  20.0,  40.0],
            "Protron (Front)":                [ 9.3, 11.5, 11.5, 10.0, 13.3, 13.3, 20.0, 33.3,  33.3,  26.7,  43.3],
            "Banana Blast (Front)":           [ 7.8, 15.6, 14.0,  9.3, 28.0, 11.8, 18.7, 28.0,  31.2,  37.3,  47.0],
            "Hyper Pulse":                    [ 7.8, 11.6, 15.6, 17.5, 23.5, 31.1, 29.2, 35.0,  23.3,  28.0,  29.0],
            "Protron Wave":                   [ 4.7,  5.9,  6.7,  6.7,  6.7,  6.7, 13.3, 13.3,  13.3,  20.0,  26.7],
            "Guided Bombs":                   [10.7, 13.3, 10.4, 26.7, 18.2, 13.0, 11.0, 11.0,  17.3,  12.0,  19.3],
            "The Orange Juicer":              [10.0, 11.4, 11.4, 22.8, 22.8, 17.0, 17.0, 20.0,  23.0,  30.0,  40.0],
            "Widget Beam":                    [ 7.8, 15.3, 11.7, 17.4, 11.7, 17.4, 17.4, 11.8,  11.8,  17.4,  17.5],
            "Sonic Impulse":                  [11.6, 10.5, 29.2, 17.5, 23.2, 21.8, 23.1, 23.3,  23.3,  30.0,  30.0],
            "RetroBall":                      [ 9.3,  9.3,  9.3,  9.3,  9.3,  9.3, 14.0, 14.0,  18.7,  18.7,  18.7],
            "Pretzel Missile":                [ 7.8, 11.7, 15.6, 11.7, 15.8, 19.2, 23.7, 27.5,  31.2,  35.1,  35.1],
        },

        # Master level: Assumes abuse of mechanics (e.g.: using mode switch to reset weapon state)
        LogicDifficulty.option_master: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Vulcan Cannon (Front)":          [11.7, 11.7, 11.7, 11.7, 11.7, 11.7, 15.6, 15.6,  15.6,  23.3,  46.7],
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Fireball":                       [ 6.0,  6.0,    0,    0,  8.0,  8.0,  9.3, 11.6,  15.2,  15.2,  15.2],
            "People Pretzels":                [   0,  4.5,  4.0,  2.5,  2.5,  3.5,  3.2,  3.4,   5.5,   4.5,   3.8],
        },
    }

    # ================================================================================================================
    # Damage aimed away from the above single target, used to get a general idea of how defensive a build can be
    base_passive: Dict[int, Dict[str, List[float]]] = {
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
            "Needle Laser":                   [   0,    0,    0,    0,    0,    0,    0,    0,     0,   5.8,  11.5],
            "Pretzel Missile":                [   0,    0,    0,    0,  3.8,  7.6,    0,  7.6,   7.6,  15.5,  23.1],
            "Dragon Frost":                   [   0, 14.0, 11.5, 11.2, 16.7, 15.8, 23.1, 27.5,  13.0,  19.0,  30.0],
            "Dragon Flame":                   [   0,    0,    0,    0,    0,    0,    0,    0,     0,     0,  22.8],
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
            "People Pretzels":                [ 8.5,  6.5,  9.5,  8.0,  6.7, 10.2, 11.8, 13.1,  22.0,  21.5,  23.3],
        }
    }

    # ================================================================================================================
    # Damage focused at a 90 degree, or close to 90 degree angle
    base_sideways: Dict[int, Dict[str, List[float]]] = {
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
            "People Pretzels":                [   0,    0,  2.5,  2.0,  1.8,  2.7,  3.0,  3.3,   5.5,   4.8,  10.0],
        },

        # Expert level: May need to move in closer to deal damage
        LogicDifficulty.option_expert: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "The Orange Juicer":              [10.0,    0,    0,    0,    0,    0, 14.0, 14.0,  14.0,  28.0,  28.0],
        },

        # Master level: Assumes abuse of mechanics (e.g.: using mode switch to reset weapon state)
        LogicDifficulty.option_master: {
            # Rear Weapons ------------ Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Starburst":                      [10.0, 10.0, 14.3, 14.3, 15.8, 15.8, 23.3, 23.3,  31.2,  35.6,  46.8],
            "Mega Pulse (Rear)":              [ 5.4,  5.8,  9.3,  7.8, 13.3, 16.7, 16.7, 13.3,  10.0,  33.3,  33.3],
            "Heavy Guided Bombs":             [   0,  2.3,  2.3,  5.8,  5.8,  5.8,  8.2,  5.8,   8.2,  13.3,  26.6],
            "People Pretzels":                [   0,    0, 11.7, 13.6, 13.6, 10.0,  7.8,  6.5,   5.5,   4.8,  10.0],
        },
    }

    # ================================================================================================================
    # Similar to active, but assumes that the projectile has already passed through a solid object
    base_piercing: Dict[int, Dict[str, List[float]]] = {
        LogicDifficulty.option_beginner: {
            # Front Weapons ----------- Power  --1-- --2-- --3-- --4-- --5-- --6-- --7-- --8-- ---9-- --10-- --11--
            "Mega Cannon":                    [ 5.3,  5.3, 10.0,  5.3, 10.0, 10.0, 10.0, 10.2,  21.1,  21.1,  21.2],
            "Sonic Impulse":                  [11.6,  7.6, 11.6, 17.5, 23.2, 10.2, 11.6, 11.5,  11.8,  11.6,  11.8],
            "Needle Laser":                   [ 5.7, 10.0,  6.7, 10.5, 11.7, 11.7, 17.5, 20.5,  29.4,  17.5,  23.4],
            "Dragon Frost":                   [   0,    0,    0,    0,    0,    0,    0,    0,   9.7,   9.5,   9.3],
            "Dragon Flame":                   [   0,    0,    0,    0,    0,    0,    0,    0,  36.4,  46.7,  22.8],
        }
    }

    # ================================================================================================================

    def __init__(self, logic_difficulty: int):
        # Combine every difficulty up to logic_difficulty into one table.
        temp_active = {}
        temp_passive = {}
        temp_sideways = {}
        temp_piercing = {}

        # Default all weapons in all temp tables to 0.0 at all power levels
        # generator_power_required is guaranteed to have every single weapon in it, so we use the keys of it here
        for weapon in self.generator_power_required.keys():
            temp_active[weapon] = [0.0] * 11
            temp_passive[weapon] = [0.0] * 11
            temp_sideways[weapon] = [0.0] * 11
            temp_piercing[weapon] = [0.0] * 11

        for difficulty in range(logic_difficulty + 1):
            temp_active.update(self.base_active.get(difficulty, {}))
            temp_passive.update(self.base_passive.get(difficulty, {}))
            temp_sideways.update(self.base_sideways.get(difficulty, {}))
            temp_piercing.update(self.base_piercing.get(difficulty, {}))

        # From the temporary tables above, create a final table with DPS class objects
        self.local_dps = {}
        for weapon in self.generator_power_required.keys():
            self.local_dps[weapon] = [DPS(active=temp_active[weapon][i],
                                          passive=temp_passive[weapon][i],
                                          sideways=temp_sideways[weapon][i],
                                          piercing=temp_piercing[weapon][i])
                                      for i in range(11)]

        # ---------------------------------------------------------------------

        self.local_power_provided = self.generator_power_provided[logic_difficulty]

        if logic_difficulty == LogicDifficulty.option_beginner:   self.logic_difficulty_multiplier = 1.25
        elif logic_difficulty == LogicDifficulty.option_standard: self.logic_difficulty_multiplier = 1.1
        elif logic_difficulty == LogicDifficulty.option_expert:   self.logic_difficulty_multiplier = 1.1
        else:                                                     self.logic_difficulty_multiplier = 1.0

    def can_meet_dps(self, target_dps: DPS, weapons: List[str],
          max_power_level: int = 11, rest_energy: int = 99) -> bool:
        for (weapon, power) in product(weapons, range(max_power_level)):
            if self.generator_power_required[weapon][power] > rest_energy:
                continue

            if self.local_dps[weapon][power].fast_meets_requirements(target_dps):
                return True
        return False

    def get_dps_shot_types(self, target_dps: DPS, weapons: List[str],
          max_power_level: int = 11, rest_energy: int = 99) -> Union[bool, Dict[int, DPS]]:
        best_distances: Dict[int, float] = {}  # energy required: distance
        best_dps: Dict[int, DPS] = {}  # energy required: best DPS object

        for (weapon, power) in product(weapons, range(max_power_level)):
            cur_energy_req = self.generator_power_required[weapon][power]
            if cur_energy_req > rest_energy:
                continue

            cur_dps = self.local_dps[weapon][power]
            success, distance = cur_dps.meets_requirements(target_dps)

            if success:  # Target DPS has been met, abandon further searching
                return True
            elif distance < best_distances.get(cur_energy_req, 512.0):
                best_distances[cur_energy_req] = distance
                best_dps[cur_energy_req] = cur_dps

        # Nothing is usable. This only happens if we either have none of the required weapons,
        # or if piercing is a requirement and nothing provides enough of it.
        if not best_distances:
            return False

        return {energy: target_dps - cur_dps for (energy, cur_dps) in best_dps.items()}

    # Makes a DPS object that is scaled based on difficulty.
    def make_dps(self, active: float = 0.0, passive: float = 0.0, sideways: float = 0.0, piercing: float = 0.0) -> DPS:
        return DPS(active=active * self.logic_difficulty_multiplier,
                   passive=passive * self.logic_difficulty_multiplier,
                   sideways=sideways * self.logic_difficulty_multiplier,
                   piercing=piercing * self.logic_difficulty_multiplier)


# =================================================================================================


def scale_health(world: "TyrianWorld", health: int, adjust_difficulty: int = 0) -> int:
    health_scale: Dict[int, Callable[[int], int]] = {
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


def get_difficulty_armor_choice(world: "TyrianWorld",
      base: Tuple[int, int, int, int], hard_contact: Optional[Tuple[int, int, int, int]] = None):
    if world.options.logic_difficulty == "no_logic":
        return 5
    if hard_contact is not None and world.options.contact_bypasses_shields:
        return hard_contact[world.options.logic_difficulty.value - 1]
    return base[world.options.logic_difficulty.value - 1]


# =================================================================================================


# If piercing is in a DPS requirement at ALL, we use this order for front weapons.
# As an optimization, only the five front weapons that can actually pierce are here, because rear can't help with this.
ordered_front_table_piercing = [
    "Needle Laser", "Sonic Impulse", "Mega Cannon", "Dragon Frost", "Dragon Flame"
]


# If active is in a DPS requirement, we use this order for front weapons.
ordered_front_table_active = [
    "Atomic RailGun", "Zica Laser", "Laser", "Lightning Cannon", "Poison Bomb", "Mega Pulse (Front)", "Protron Z",
    "NortShip Super Pulse", "Pulse-Cannon", "Heavy Missile Launcher (Front)", "HotDog (Front)", "Hyper Pulse",
    "Guided Bombs", "The Orange Juicer", "Dragon Flame", "Pretzel Missile", "Vulcan Cannon (Front)",
    "Missile Launcher", "Needle Laser", "Mega Cannon", "Shuriken Field", "Widget Beam", "Banana Blast (Front)",
    "Protron (Front)", "Multi-Cannon (Front)", "Sonic Impulse", "Dragon Frost", "RetroBall", "Protron Wave"
]


# Otherwise, we use this order.
ordered_front_table_other = [
    "Shuriken Field", "NortShip Super Pulse", "Banana Blast (Front)", "Multi-Cannon (Front)", "Dragon Frost",
    "Poison Bomb", "Sonic Impulse", "Protron (Front)", "The Orange Juicer", "Hyper Pulse", "Guided Bombs",
    "Lightning Cannon", "Heavy Missile Launcher (Front)", "RetroBall", "HotDog (Front)", "Mega Cannon",
    "Mega Pulse (Front)", "Widget Beam", "Missile Launcher", "Protron Wave", "Pretzel Missile", "Protron Z",
    "Vulcan Cannon (Front)", "Zica Laser", "Pulse-Cannon", "Needle Laser", "Dragon Flame", "Laser"
]


def get_front_weapon_state(state: "CollectionState", player: int, target_dps: DPS) -> List[str]:
    keys = state.prog_items[player].keys()
    if target_dps._type_piercing:
        return [name for name in ordered_front_table_piercing if name in keys]
    elif target_dps._type_active:
        return [name for name in ordered_front_table_active if name in keys]
    else:
        return [name for name in ordered_front_table_other if name in keys]


# =================================================================================================


# If sideways is in a DPS requirement, we use this order for rear weapons.
# If we've gotten to this point, we NEED sideways DPS, so we can exclude rear weapons which don't give it.
ordered_rear_table_sideways = [
    "Starburst", "Scatter Wave", "Mega Pulse (Rear)", "Multi-Cannon (Rear)", "Sonic Wave", "Protron (Rear)",
    "Heavy Guided Bombs", "Banana Blast (Rear)", "NortShip Spreader", "People Pretzels", "Guided Micro Bombs"
]


# If passive is in a DPS requirement, we use this order for rear weapons.
ordered_rear_table_passive = [
    "NortShip Spreader", "Starburst", "Mega Pulse (Rear)", "NortShip Spreader B", "HotDog (Rear)",
    "Heavy Missile Launcher (Rear)", "Protron (Rear)", "Multi-Cannon (Rear)", "Sonic Wave", "Scatter Wave",
    "Vulcan Cannon (Rear)", "Banana Blast (Rear)", "Fireball", "Wild Ball", "Heavy Guided Bombs",
    "Guided Micro Bombs", "People Pretzels"
]


# Otherwise, we use this order.
# Again, the only possible way we get here is if only active is remaining, so we can exclude weapons that can't help.
ordered_rear_table_other = [
    "Banana Blast (Rear)", "Sonic Wave", "Wild Ball", "Fireball", "People Pretzels", "Mega Pulse (Rear)",
    "Scatter Wave", "NortShip Spreader B", "HotDog (Rear)"
]


def get_rear_weapon_state(state: "CollectionState", player: int, target_dps: DPS) -> List[str]:
    keys = state.prog_items[player].keys()
    if target_dps._type_sideways:
        return [name for name in ordered_rear_table_sideways if name in keys]
    elif target_dps._type_passive:
        return [name for name in ordered_rear_table_passive if name in keys]
    else:
        return [name for name in ordered_rear_table_other if name in keys]


# =================================================================================================


def get_generator_level(state: "CollectionState", player: int) -> int:
    # Handle progressive and non-progressive generators independently
    # Otherwise collecting in different orders could result in different generator levels
    if state.has("Gravitron Pulse-Wave", player):   return 6
    elif state.has("Advanced MicroFusion", player): return 5
    elif state.has("Standard MicroFusion", player): return 4
    elif state.has("Gencore Custom MR-12", player): return 3
    elif state.has("Advanced MR-12", player):       return 2
    return min(6, 1 + state.count("Progressive Generator", player))


# =================================================================================================


def can_deal_damage(state: "CollectionState", player: int, damage_tables: DamageTables, target_dps: DPS) -> bool:
    owned_front = get_front_weapon_state(state, player, target_dps)
    owned_rear = get_rear_weapon_state(state, player, target_dps)
    power_level_max = min(11, 1 + state.count("Maximum Power Up", player))
    start_energy = damage_tables.local_power_provided[get_generator_level(state, player)]

    result = damage_tables.get_dps_shot_types(target_dps, owned_front, power_level_max, start_energy)

    if type(result) is bool:  # Immediate pass/fail
        return result

    for (used_energy, rest_dps) in result.items():
        rest_energy = start_energy - used_energy
        if damage_tables.can_meet_dps(rest_dps, owned_rear, power_level_max, rest_energy):
            return True
    return False


def has_armor_level(state: "CollectionState", player: int, armor_level: int) -> bool:
    return True if armor_level <= 5 else state.has("Armor Up", player, armor_level - 5)


def has_power_level(state: "CollectionState", player: int, power_level: int) -> bool:
    return True if power_level <= 1 else state.has("Maximum Power Up", player, power_level - 1)


def has_generator_level(state: "CollectionState", player: int, gen_level: int) -> bool:
    return get_generator_level(state, player) >= gen_level


def has_twiddle(state: "CollectionState", player: int, action: SpecialValues) -> bool:
    for twiddle in state.multiworld.worlds[player].twiddles:
        if action == twiddle.action:
            return True
    return False


def has_invulnerability(state: "CollectionState", player: int) -> bool:
    return state.has("Invulnerability", player) or has_twiddle(state, player, SpecialValues.Invulnerability)


def has_repulsor(state: "CollectionState", player: int) -> bool:
    return state.has("Repulsor", player) or has_twiddle(state, player, SpecialValues.Repulsor)


# =================================================================================================


def logic_entrance_rule(world: "TyrianWorld", entrance_name: str, rule: Callable[..., bool]) -> None:
    entrance = world.multiworld.get_entrance(entrance_name, world.player)
    add_rule(entrance, rule)


def logic_location_rule(world: "TyrianWorld", location_name: str, rule: Callable[..., bool]) -> None:
    location = world.multiworld.get_location(location_name, world.player)
    add_rule(location, rule)


def logic_location_exclude(world: "TyrianWorld", location_name: str) -> None:
    location = world.multiworld.get_location(location_name, world.player)
    location.progress_type = LPType.EXCLUDED


def logic_all_locations_exclude(world: "TyrianWorld", location_name_base: str) -> None:
    for location in [i for i in world.multiworld.get_locations(world.player) if i.name.startswith(location_name_base)]:
        location.progress_type = LPType.EXCLUDED


# =================================================================================================
#                                        EPISODE 1 (ESCAPE)
# =================================================================================================


def episode_1_rules(world: "TyrianWorld") -> None:
    # ===== TYRIAN ============================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "TYRIAN (Episode 1) - HOLES Warp Orb")
        logic_location_exclude(world, "TYRIAN (Episode 1) - SOH JIN Warp Orb")
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "TYRIAN (Episode 1) - Tank Turn-and-fire Secret")

    # Four trigger enemies among the starting U-Ship sets, need enough damage to clear them out
    # Below game difficulty Hard, the level layout is different
    if world.options.difficulty >= GameDifficulty.option_hard:
        dps_active = world.damage_tables.make_dps(active=scale_health(world, 19) / 2.0)
        dps_passive = world.damage_tables.make_dps(passive=scale_health(world, 19) / 1.5)
        logic_location_rule(world, "TYRIAN (Episode 1) - HOLES Warp Orb", lambda state, dps1=dps_active, dps2=dps_passive:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Rock health: 20
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 20) / 3.6)
    logic_location_rule(world, "TYRIAN (Episode 1) - BUBBLES Warp Rock", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Boss health: Unscaled 254; Wing health: 100
    dps_active = world.damage_tables.make_dps(active=(scale_health(world, 100) + 254) / 30.0)
    dps_piercing = world.damage_tables.make_dps(piercing=254 / 30.0)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=dps_active, dps2=dps_piercing:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
    else:
        wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(6, 6, 5, 5))
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=dps_active, dps2=dps_piercing, armor=wanted_armor:
              has_armor_level(state, world.player, armor)
              or has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
        logic_location_rule(world, "TYRIAN (Episode 1) - Boss", lambda state, dps1=dps_active, dps2=dps_piercing:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== BUBBLES ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_all_locations_exclude(world, "BUBBLES (Episode 1) - Coin Rain")

    # Health of red bubbles (in all cases): 20
    enemy_health = scale_health(world, 20)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 4.0)
    logic_entrance_rule(world, "BUBBLES (Episode 1) @ Pass Bubble Lines", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=enemy_health / 1.9)
    logic_entrance_rule(world, "BUBBLES (Episode 1) @ Speed Up Section", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=enemy_health / 3.0)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 4.0)
    logic_location_rule(world, "BUBBLES (Episode 1) - Orbiting Bubbles", lambda state, dps1=dps_active, dps2=dps_piercing:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    dps_active = world.damage_tables.make_dps(active=enemy_health / 1.2)
    # dps_piercing: unchanged
    logic_location_rule(world, "BUBBLES (Episode 1) - Shooting Bubbles", lambda state, dps1=dps_active, dps2=dps_piercing:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== HOLES =============================================================
    dps_mixed = world.damage_tables.make_dps(active=8.0, passive=21.0)
    wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(8, 7, 6, 5))
    logic_entrance_rule(world, "HOLES (Episode 1) @ Pass Spinner Gauntlet", lambda state, dps1=dps_mixed, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Boss ship flyby health: Unscaled 254; Wing health: 100
    dps_mixed = world.damage_tables.make_dps(active=(scale_health(world, 100) + 254) / 5.0, passive=21.0)
    logic_entrance_rule(world, "HOLES (Episode 1) @ Destroy Boss Ships", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== SOH JIN ===========================================================
    # Single wall tile: 40
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 40) / 4.6)
    logic_entrance_rule(world, "SOH JIN (Episode 1) @ Destroy Walls", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== ASTEROID1 =========================================================
    # Face rock: 25; destructible pieces before it: 5
    enemy_health = scale_health(world, 25) + (scale_health(world, 5) * 2)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 4.4)
    logic_location_rule(world, "ASTEROID1 (Episode 1) - ASTEROID? Warp Orb", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Boss dome: 100
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 100) / 30.0)
    logic_entrance_rule(world, "ASTEROID1 (Episode 1) @ Destroy Boss", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== ASTEROID2 =========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1")
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2")
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret")

    # All tanks: 30
    enemy_health = scale_health(world, 30)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 2.1)
    logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Bridge", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Tank Turn-around Secrets 1 and 2:
    # On Standard or below, assume most damage will come only after the tank secret items are active
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        dps_active = world.damage_tables.make_dps(active=enemy_health / 2.3)
        logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

        dps_active = world.damage_tables.make_dps(active=enemy_health / 3.9)
        logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Face rock containing orb: 25
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 25) / 4.4)
    logic_location_rule(world, "ASTEROID2 (Episode 1) - MINEMAZE Warp Orb", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=10.0)
    logic_entrance_rule(world, "ASTEROID2 (Episode 1) @ Destroy Boss", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== ASTEROID? =========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "ASTEROID? (Episode 1) - WINDY Warp Orb")

    # Launchers: 40
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 40) / 3.5)
    logic_entrance_rule(world, "ASTEROID? (Episode 1) @ Initial Welcome", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Secret ships: also 40
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 40) / 1.36)
    logic_entrance_rule(world, "ASTEROID? (Episode 1) @ Quick Shots", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    wanted_armor = get_difficulty_armor_choice(world, base=(6, 5, 5, 5), hard_contact=(8, 7, 7, 6))
    logic_entrance_rule(world, "ASTEROID? (Episode 1) @ Final Gauntlet", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # ===== MINEMAZE ==========================================================
    # Gates: 20
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 20) / 3.8)
    logic_entrance_rule(world, "MINEMAZE (Episode 1) @ Destroy Gates", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== WINDY =============================================================
    # Question mark block: 20
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 20) / 1.4)
    logic_location_rule(world, "WINDY (Episode 1) - Central Question Mark", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    if world.options.logic_difficulty == LogicDifficulty.option_master:
        # Always assumed reachable. Take a big bite out of your armor if you need to.
        wanted_armor = 14 if world.options.contact_bypasses_shields else 12
        logic_entrance_rule(world, "WINDY (Episode 1) @ Phase Through Walls", lambda state, armor=wanted_armor:
              has_invulnerability(state, world.player) or has_armor_level(state, world.player, armor))
    else:
        # If we don't have a way to get invulnerability, exclude the location even on expert.
        # (Ways to get it: Have specials as items, start with it in specials on, or roll an Invulnerability twiddle.)
        exclude_question_mark = (world.options.logic_difficulty <= LogicDifficulty.option_standard)
        if world.options.specials == "as_items" or has_invulnerability(world.multiworld.state, world.player):
            logic_entrance_rule(world, "WINDY (Episode 1) @ Phase Through Walls", lambda state:
                  has_invulnerability(state, world.player))
        else:
            exclude_question_mark = True
            logic_entrance_rule(world, "WINDY (Episode 1) @ Phase Through Walls", lambda state:
                  has_armor_level(state, world.player, 14))

        if exclude_question_mark:
            logic_location_exclude(world, "WINDY (Episode 1) - Central Question Mark")

    # Regular block: 10
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 10) / 1.4)
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 5, 5, 5), hard_contact=(11, 9, 8, 6))
    logic_entrance_rule(world, "WINDY (Episode 1) @ Fly Through", lambda state, dps1=dps_active, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== SAVARA ============================================================
    # Huge planes: 60
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 60) / 1.025)
    logic_location_rule(world, "SAVARA (Episode 1) - Huge Plane, Speeds By", lambda state, dps1=dps_active:
          has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Vulcan plane containing item: 14
    # The vulcan shots hurt a lot, so optimal kill would be with passive DPS if possible
    savara_vulc_passive = world.damage_tables.make_dps(passive=scale_health(world, 14) / 2.4)
    savara_vulc_active = world.damage_tables.make_dps(active=scale_health(world, 14) / 1.6)
    logic_location_rule(world, "SAVARA (Episode 1) - Vulcan Plane", lambda state, dps1=savara_vulc_passive, dps2=savara_vulc_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Damage estimate: 254 health for the boss, shooting through 15 ticks and 4 missiles
    boss_health = 254 + (scale_health(world, 6) * 15) + (scale_health(world, 10) * 4)
    savara_boss_active = world.damage_tables.make_dps(active=boss_health / 30.0)
    savara_tick_sideways = world.damage_tables.make_dps(sideways=scale_health(world, 6) / 1.2)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "SAVARA (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=savara_boss_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        logic_location_rule(world, "SAVARA (Episode 1) - Boss", lambda state, dps1=savara_boss_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

        # Also need enough damage to destroy things the boss shoots at you, when dodging isn't an option
        logic_entrance_rule(world, "SAVARA (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=savara_tick_sideways, dps2=savara_boss_active:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== SAVARA II =========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(8, 7, 6, 5))
    logic_entrance_rule(world, "SAVARA II (Episode 1) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    dps_active = world.damage_tables.make_dps(active=7.0)
    logic_entrance_rule(world, "SAVARA II (Episode 1) @ Destroy Green Planes", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Huge planes: 60 (difficulty -1 due to level)
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 60, adjust_difficulty=-1) / 2.3)
    logic_location_rule(world, "SAVARA II (Episode 1) - Huge Plane Amidst Turrets", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Same vulcan DPS as SAVARA, we re-use the DPS made for it
    logic_location_rule(world, "SAVARA II (Episode 1) - Vulcan Planes Near Blimp", lambda state, dps1=savara_vulc_passive, dps2=savara_vulc_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Same boss as SAVARA, we re-use the DPS made for it
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "SAVARA II (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=savara_boss_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        logic_location_rule(world, "SAVARA II (Episode 1) - Boss", lambda state, dps1=savara_boss_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

        # Also need enough damage to destroy things the boss shoots at you, when dodging isn't an option
        logic_entrance_rule(world, "SAVARA II (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=savara_tick_sideways, dps2=savara_boss_active:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== BONUS =============================================================
    # Temporary rule to keep this from occurring too early.
    dps_temporary = world.damage_tables.make_dps(active=10.0, passive=10.0)
    logic_entrance_rule(world, "BONUS (Episode 1) @ Destroy Patterns", lambda state, dps1=dps_temporary:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== MINES =============================================================
    # Rotating orbs: 20
    enemy_health = scale_health(world, 20)  # Rotating Orbs
    dps_active = world.damage_tables.make_dps(active=enemy_health / 1.0)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 2.7)
    logic_entrance_rule(world, "MINES (Episode 1) @ Destroy First Orb", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    dps_active = world.damage_tables.make_dps(active=enemy_health / 0.5)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 1.2)
    logic_entrance_rule(world, "MINES (Episode 1) @ Destroy Second Orb", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Blue mine has static health (does not depend on difficulty)
    dps_active = world.damage_tables.make_dps(active=30 / 3.0)
    logic_location_rule(world, "MINES (Episode 1) - Blue Mine", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== DELIANI ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "DELIANI (Episode 1) - Tricky Rail Turret")

    # Rail turret: 30
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 30) / 2.2)
    logic_location_rule(world, "DELIANI (Episode 1) - Tricky Rail Turret", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Two-tile wide turret ships: 25
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 25) / 1.6)
    wanted_armor = get_difficulty_armor_choice(world, base=(10, 9, 8, 6))
    logic_entrance_rule(world, "DELIANI (Episode 1) @ Pass Ambush", lambda state, dps1=dps_active, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Repulsor orbs: 80; boss: 200
    boss_health = (scale_health(world, 80) * 3) + scale_health(world, 200)
    dps_active = world.damage_tables.make_dps(active=boss_health / 22.0)
    logic_entrance_rule(world, "DELIANI (Episode 1) @ Destroy Boss", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== SAVARA V ==========================================================
    # Blimp: 70
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 70) / 1.5)
    logic_location_rule(world, "SAVARA V (Episode 1) - Super Blimp", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=254 / 15.0)
    logic_entrance_rule(world, "SAVARA V (Episode 1) @ Destroy Bosses", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== ASSASSIN ==========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(9, 8, 7, 5))
    dps_active = world.damage_tables.make_dps(active=508 / 20.0)
    logic_entrance_rule(world, "ASSASSIN (Episode 1) @ Destroy Boss", lambda state, dps1=dps_active, armor=wanted_armor:
          can_deal_damage(state, world.player, world.damage_tables, dps1))


# =================================================================================================
#                                      EPISODE 2 (TREACHERY)
# =================================================================================================


def episode_2_rules(world: "TyrianWorld") -> None:
    # ===== TORM ==============================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret")

    # On standard or below, require killing the dragon behind the secret ship
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        # Dragon: 40
        dps_active = world.damage_tables.make_dps(active=scale_health(world, 40) / 1.6)
        logic_location_rule(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=254 / 4.4)
    logic_location_rule(world, "TORM (Episode 2) - Boss Ship Fly-By", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Technically this boss has 254 health, but compensating for constant movement all over the screen
    dps_active = world.damage_tables.make_dps(active=(254 * 1.75) / 32.0)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "TORM (Episode 2) @ Pass Boss (can time out)", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        # The actual time out is attainable with an empty loadout
        logic_location_rule(world, "TORM (Episode 2) - Boss", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== GYGES =============================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "GYGES (Episode 2) - GEM WAR Warp Orb")

    # Orbsnakes: 10 (x6)
    dps_active = world.damage_tables.make_dps(active=(scale_health(world, 10) * 6) / 5.0)
    dps_piercing = world.damage_tables.make_dps(active=scale_health(world, 10) / 5.0)
    logic_location_rule(world, "GYGES (Episode 2) - Orbsnake", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Either the repulsor mitigates the bullets in the speed up section,
    # or you have a decent loadout and can destroy a few things to make your life easier
    dps_mixed = world.damage_tables.make_dps(active=8.0, passive=12.0)
    logic_entrance_rule(world, "GYGES (Episode 2) @ After Speed Up Section", lambda state, dps1=dps_mixed:
          has_repulsor(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=254 / 30.0)
    logic_entrance_rule(world, "GYGES (Episode 2) @ Destroy Boss", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== BONUS 1 ===========================================================
    # Temporary rule to keep this from occurring too early.
    dps_temporary = world.damage_tables.make_dps(active=10.0, passive=10.0)
    logic_entrance_rule(world, "BONUS 1 (Episode 2) @ Destroy Patterns", lambda state, dps1=dps_temporary:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== ASTCITY ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "ASTCITY (Episode 2) - MISTAKES Warp Orb")

    wanted_armor = get_difficulty_armor_choice(world, base=(7, 7, 6, 5), hard_contact=(7, 7, 6, 5))
    logic_entrance_rule(world, "ASTCITY (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # Building: 30 (difficulty -1 due to level)
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 30, adjust_difficulty=-1) / 4.0)
    logic_location_rule(world, "ASTCITY (Episode 2) - Warehouse 92", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # In all likelihood this can be obliterated with a superbomb that you obtain in the level,
    # but we don't consider superbombs logic in any way, so
    dps_mixed = world.damage_tables.make_dps(active=8.0, passive=14.0)
    logic_entrance_rule(world, "ASTCITY (Episode 2) @ Last Platform", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== BONUS 2 ===========================================================
    # (logicless - flythrough only, no items, easily doable without firing a shot)

    # ===== GEM WAR ===========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 7, 6, 5), hard_contact=(9, 9, 8, 6))
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # Red gem ship: Unscaled 254
    # We compensate for their movement, and other enemies being nearby
    wanted_passive = 20.0 if world.options.contact_bypasses_shields else 12.0
    dps_mixed = world.damage_tables.make_dps(active=(254 * 1.4) / 20.0, passive=wanted_passive)
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Red Gem Leaders Easy", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))  # 2 and 3

    dps_mixed = world.damage_tables.make_dps(active=(254 * 1.4) / 17.5, passive=wanted_passive)
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Red Gem Leaders Medium", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))  # 1

    dps_mixed = world.damage_tables.make_dps(active=(254 * 1.4) / 13.0, passive=wanted_passive)
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Red Gem Leaders Hard", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))  # 4

    # Center of boss ship: 20
    # Flanked by three ships with unscaled health 254, either destroy the one in front, or have a piercing weapon
    dps_mixed = world.damage_tables.make_dps(active=(254 + scale_health(world, 20)) / 16.0, passive=wanted_passive)
    dps_piercemix = world.damage_tables.make_dps(piercing=scale_health(world, 20) / 16.0, passive=wanted_passive)
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Blue Gem Bosses", lambda state, dps1=dps_piercemix, dps2=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== MARKERS ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "MARKERS (Episode 2) - Car Destroyer Secret")

    # Flying through this stage is relatively easy *unless* HardContact is turned on.
    wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(9, 8, 8, 6))
    logic_entrance_rule(world, "MARKERS (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # Minelayer: 30; Mine: 6 (estimated 4 mines hit)
    enemy_health = scale_health(world, 30) + (scale_health(world, 6) * 4)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 7.1)
    logic_location_rule(world, "MARKERS (Episode 2) - Persistent Mine-Layer", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Cars: 10
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 10) / 3.0)
    logic_location_rule(world, "MARKERS (Episode 2) - Car Destroyer Secret", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Turrets: 20
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 20) / 3.8)
    logic_entrance_rule(world, "MARKERS (Episode 2) @ Destroy Turrets", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== MISTAKES ==========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "MISTAKES (Episode 2) - Orbsnakes, Trigger Enemy 1")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Claws, Trigger Enemy 1")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Claws, Trigger Enemy 2")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Super Bubble Spawner")
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "MISTAKES (Episode 2) - Orbsnakes, Trigger Enemy 2")
        logic_location_exclude(world, "MISTAKES (Episode 2) - Anti-Softlock")

    wanted_armor = get_difficulty_armor_choice(world, base=(6, 5, 5, 5), hard_contact=(9, 8, 7, 5))
    logic_entrance_rule(world, "MISTAKES (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          or has_invulnerability(state, world.player))

    # Most trigger enemies: 10
    enemy_health = scale_health(world, 10)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 1.2)
    logic_entrance_rule(world, "MISTAKES (Episode 2) @ Bubble Spawner Path", lambda state, dps1=dps_piercing:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Orbsnakes: 10 (x6)
    dps_active = world.damage_tables.make_dps(active=(enemy_health * 6) / 5.5)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 5.5)
    logic_location_rule(world, "MISTAKES (Episode 2) - Orbsnakes, Trigger Enemy 1", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    dps_active = world.damage_tables.make_dps(active=(enemy_health * 6) / 0.8)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 0.8)
    logic_entrance_rule(world, "MISTAKES (Episode 2) @ Softlock Path", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== SOH JIN ===========================================================
    # Brown claw enemy: 15
    # These enemies don't contain any items, but they home in on you and are a bit more difficult to dodge because
    # of that, so lock the whole level behind being able to destroy them; it's enough DPS to get locations here
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 15) / 2.0)
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Base Requirements", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Paddle... things?: 100
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 100) / 9.0)
    dps_alternate = world.damage_tables.make_dps(active=scale_health(world, 100) / 15.0, sideways=10.0)
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Destroy Second Wave Paddles", lambda state, dps1=dps_active, dps2=dps_alternate:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Dodging these orbs is surprisingly difficult, because of the erratic vertical movement with their oscillation
    wanted_armor = get_difficulty_armor_choice(world, base=(9, 8, 7, 5), hard_contact=(11, 10, 9, 7))
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Fly Through Third Wave Orbs", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          or (
              has_invulnerability(state, world.player)
              and has_armor_level(state, world.player, armor - 2)
          ))

    dps_mixed = world.damage_tables.make_dps(active=254 / 20.0, sideways=254 / 20.0)
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Destroy Third Wave Orbs", lambda state, dps1=dps_mixed:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== BOTANY A ==========================================================
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_all_locations_exclude(world, "BOTANY A (Episode 2) - End of Path Secret")

    wanted_armor = get_difficulty_armor_choice(world, base=(9, 9, 8, 6))
    wanted_generator = 3 if world.options.logic_difficulty <= LogicDifficulty.option_standard else 2
    logic_entrance_rule(world, "BOTANY A (Episode 2) @ Beyond Starting Area", lambda state, armor=wanted_armor, generator=wanted_generator:
          has_armor_level(state, world.player, armor)
          or (
              has_repulsor(state, world.player)
              and has_generator_level(state, world.player, generator)  # For shield recovery
          ))

    # Moving turret: 15 (difficulty +1 due to level)
    enemy_health = scale_health(world, 15, adjust_difficulty=+1)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 2.0)
    logic_entrance_rule(world, "BOTANY A (Episode 2) @ Can Destroy Turrets", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=enemy_health / 1.0)
    logic_location_rule(world, "BOTANY A (Episode 2) - Mobile Turret Approaching Head-On", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # This one comes before "Beyond Starting Area"...
    dps_active = world.damage_tables.make_dps(active=enemy_health / 3.0)
    logic_location_rule(world, "BOTANY A (Episode 2) - Retreating Mobile Turret", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Green ship: 20 (difficulty +1 due to level)
    enemy_health = scale_health(world, 20, adjust_difficulty=+1)
    # The backmost ship is the one with the item, expect to destroy at least one other ship to reach it
    # (except if you can do enough piercing damage, of course)
    dps_active = world.damage_tables.make_dps(active=(enemy_health * 2) / 3.0)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 3.0)
    logic_location_rule(world, "BOTANY A (Episode 2) - Green Ship Pincer", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    botany_boss = world.damage_tables.make_dps(active=(254 * 1.8) / 24.0)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "BOTANY A (Episode 2) @ Pass Boss (can time out)", lambda state, dps1=botany_boss:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        logic_location_rule(world, "BOTANY A (Episode 2) - Boss", lambda state, dps1=botany_boss:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== BOTANY B ==========================================================
    # Destructible sensor: 6 (difficulty +1 due to level)
    # Start of level, nothing nearby dangerous, only need to destroy it
    dps_active = world.damage_tables.make_dps(scale_health(world, 6, adjust_difficulty=+1) / 4.0)
    logic_location_rule(world, "BOTANY B (Episode 2) - Starting Platform Sensor", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Turret: 15 (difficulty +1 due to level)
    enemy_health = scale_health(world, 15, adjust_difficulty=+1)  # Moving turret
    # Past this point is when the game starts demanding more of you.
    # Need enough damage to clear out the screen of turrets
    dps_active = world.damage_tables.make_dps(active=(enemy_health * 4) / 4.5)
    dps_passive = world.damage_tables.make_dps(passive=(enemy_health * 4) / 3.0)
    logic_entrance_rule(world, "BOTANY B (Episode 2) @ Beyond Starting Platform", lambda state, dps1=dps_active, dps2=dps_passive:
          has_armor_level(state, world.player, 7)
          and (
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2)
          ))

    # Same boss as BOTANY A, re-use DPS from it
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "BOTANY B (Episode 2) @ Pass Boss (can time out)", lambda state, dps1=botany_boss:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        logic_location_rule(world, "BOTANY B (Episode 2) - Boss", lambda state, dps1=botany_boss:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== GRYPHON ===========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(10, 9, 8, 7), hard_contact=(11, 10, 10, 8))
    dps_mixed = world.damage_tables.make_dps(active=22.0, passive=16.0)
    logic_entrance_rule(world, "GRYPHON (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor, dps1=dps_mixed:
          has_armor_level(state, world.player, armor)
          and has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))


# =================================================================================================
#                                   EPISODE 3 (MISSION: SUICIDE)
# =================================================================================================


def episode_3_rules(world: "TyrianWorld") -> None:
    # ===== GAUNTLET ==========================================================
    # Capsule ships: 10 (difficulty -1 due to level)
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 10, adjust_difficulty=-1) / 1.3)
    logic_location_rule(world, "GAUNTLET (Episode 3) - Capsule Ships Near Mace", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Gates: 20 (difficulty -1 due to level)
    enemy_health = scale_health(world, 20, adjust_difficulty=-1)

    dps_active = world.damage_tables.make_dps(active=(enemy_health * 2) / 4.4)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 4.4)
    logic_location_rule(world, "GAUNTLET (Episode 3) - Doubled-up Gates", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # These two use the same DPS rule, but are in different sub-regions
    dps_active = world.damage_tables.make_dps(active=enemy_health / 1.5)
    logic_location_rule(world, "GAUNTLET (Episode 3) - Split Gates, Left", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))
    logic_location_rule(world, "GAUNTLET (Episode 3) - Gate near Freebie Item", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Weak point orb: 6 (difficulty -1 due to level)
    enemy_health = scale_health(world, 6, adjust_difficulty=-1)
    dps_active = world.damage_tables.make_dps(active=enemy_health / 0.5)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 1.2)
    # Invulnerability lets you safely pass through without damaging
    logic_entrance_rule(world, "GAUNTLET (Episode 3) @ Clear Orb Tree", lambda state, dps1=dps_piercing, dps2=dps_active:
          has_invulnerability(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))
    logic_location_rule(world, "GAUNTLET (Episode 3) - Tree of Spinning Orbs", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== IXMUCANE ==========================================================
    # Minelayer: Unscaled 254, or 10 (weak point); Dropped mines: 20
    # Need sideways + active to be able to hit the weak points of the center minelayers while damaging other things,
    # Piercing to hit those weak points through other things anyway, or just a lot of active damage altogether.
    # Alternatively, Invulnerability can also fill piercing's role.
    dps_option1 = world.damage_tables.make_dps(piercing=scale_health(world, 10) / 8.0)
    dps_option2 = world.damage_tables.make_dps(active=8.0, sideways=scale_health(world, 10) / 8.0)
    dps_option3 = world.damage_tables.make_dps(active=((scale_health(world, 20) * 3) + 254) / 8.0)
    logic_entrance_rule(world, "IXMUCANE (Episode 3) @ Pass Minelayers Requirements", lambda state, dps1=dps_option1, dps2=dps_option2, dps3=dps_option3:
          has_invulnerability(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2)
          or can_deal_damage(state, world.player, world.damage_tables, dps3))

    # This boss keeps itself guarded inside an indestructible rock at almost all times, and there's a second
    # destructible target in front of the actual weak point... But none of this matters if you can pierce.
    # It also summons a mass of tiny rocks as an attack, so if we aren't cheesing it, we want at least some passive.
    boss_health = scale_health(world, 25)
    dps_option1 = world.damage_tables.make_dps(piercing=boss_health / 24.0)
    dps_option2 = world.damage_tables.make_dps(active=(enemy_health * 2) / 3.8, passive=12.0)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "IXMUCANE (Episode 3) @ Pass Boss (can time out)", lambda state, dps1=dps_option1, dps2=dps_option2:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
    else:
        # Piercing for cheese kill, or passive to destroy some rocks for safety while we wait
        dps_safety = world.damage_tables.make_dps(passive=12.0)
        logic_entrance_rule(world, "IXMUCANE (Episode 3) @ Pass Boss (can time out)", lambda state, dps1=dps_option1, dps2=dps_safety:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
        logic_location_rule(world, "IXMUCANE (Episode 3) - Boss", lambda state, dps1=dps_option1, dps2=dps_option2:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== BONUS =============================================================
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "BONUS (Episode 3) - Sonic Wave Hell Turret")
        logic_all_locations_exclude(world, "Shop - BONUS (Episode 3)")

    # Turrets have only one health; they die to any damage, but are guarded from front and back.
    dps_passive = world.damage_tables.make_dps(passive=0.2)
    dps_piercing = world.damage_tables.make_dps(piercing=0.2)
    if world.options.logic_difficulty <= LogicDifficulty.option_expert:
        logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 1", lambda state, dps1=dps_piercing, dps2=dps_passive:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state, dps1=dps_piercing, dps2=dps_passive:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Doesn't sway left/right like the other two
    logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 2", lambda state, dps1=dps_piercing, dps2=dps_passive:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # To pass the turret onslaught
    # Two-wide turret: 25; but we only need to take it down to damaged (non-firing) state
    enemy_health = scale_health(world, 25) - 10
    dps_active = world.damage_tables.make_dps(active=(enemy_health * 4) / 3.6)
    logic_entrance_rule(world, "BONUS (Episode 3) @ Pass Onslaughts", lambda state, dps1=dps_active:
          has_generator_level(state, world.player, 3)  # For shield recovery
          and has_armor_level(state, world.player, 8)
          and (
              has_repulsor(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1)
          ))

    # Do you have knowledge of the safe spot through this section? Master assumes you do, anything else doesn't.
    # If we're not assuming safe spot knowledge, we need the repulsor, or some sideways DPS and more armor.
    if world.options.logic_difficulty < LogicDifficulty.option_master:
        dps_mixed = world.damage_tables.make_dps(active=(enemy_health * 4) / 3.6, sideways=4.0)
        logic_entrance_rule(world, "BONUS (Episode 3) @ Sonic Wave Hell", lambda state, dps1=dps_mixed:
              has_repulsor(state, world.player)
              or (
                  has_armor_level(state, world.player, 12)
                  and can_deal_damage(state, world.player, world.damage_tables, dps_mixed)
              ))

    # To actually get the items from turret onslaught; two two-tile turrets, plus item ship
    enemy_health = scale_health(world, 25)
    ship_health = scale_health(world, 3)
    dps_active = world.damage_tables.make_dps(active=((enemy_health * 2) + ship_health) / 1.8)
    logic_entrance_rule(world, "BONUS (Episode 3) @ Get Items from Onslaughts", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== STARGATE ==========================================================
    # Just need some way of combating the bubble spam that happens after the last normal location
    dps_passive = world.damage_tables.make_dps(passive=7.0)
    logic_entrance_rule(world, "STARGATE (Episode 3) @ Reach Bubble Spawner", lambda state, dps1=dps_passive:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== AST. CITY =========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 6, 6, 5), hard_contact=(8, 8, 7, 5))
    logic_entrance_rule(world, "AST. CITY (Episode 3) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # Boss domes: 100 (difficulty -1 due to level)
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 100, adjust_difficulty=-1) / 4.5)
    logic_entrance_rule(world, "AST. CITY (Episode 3) @ Destroy Boss Domes", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== SAWBLADES =========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "SAWBLADES (Episode 3) - SuperCarrot Drop")

    # Periodically, tiny rocks get spammed all over the screen throughout this level.
    # We need to have some passive and some armor to be able to deal with these moments.
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 6, 6, 5), hard_contact=(10, 9, 8, 6))
    dps_mixed = world.damage_tables.make_dps(active=10.0, passive=12.0)
    logic_entrance_rule(world, "SAWBLADES (Episode 3) @ Base Requirements", lambda state, dps1=dps_mixed, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          and has_generator_level(state, world.player, 2)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Blue Sawblade: 60
    dps_mixed = world.damage_tables.make_dps(active=scale_health(world, 60) / 4.1, passive=12.0)
    logic_location_rule(world, "SAWBLADES (Episode 3) - Waving Sawblade", lambda state, dps1=dps_mixed:
        can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== CAMANIS ===========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(9, 8, 8, 6), hard_contact=(11, 10, 9, 7))
    wanted_energy = 3 if world.options.logic_difficulty <= LogicDifficulty.option_standard else 2
    dps_mixed = world.damage_tables.make_dps(active=12.0, passive=16.0)
    logic_entrance_rule(world, "CAMANIS (Episode 3) @ Base Requirements", lambda state, dps1=dps_mixed, armor=wanted_armor, energy=wanted_energy:
          has_armor_level(state, world.player, armor)
          and has_generator_level(state, world.player, energy)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_mixed = world.damage_tables.make_dps(active=(254 * 1.6) / 20.0, passive=16.0)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "CAMANIS (Episode 3) @ Pass Boss (can time out)", lambda state, dps1=dps_mixed:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        # Passive DPS requirements covered by base requirements already
        logic_location_rule(world, "CAMANIS (Episode 3) - Boss", lambda state, dps1=dps_mixed:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== MACES =============================================================
    # (logicless - purely a test of dodging skill)

    # ===== TYRIAN X ==========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "TYRIAN X (Episode 3) - First U-Ship Secret")
        logic_location_exclude(world, "TYRIAN X (Episode 3) - Second Secret, Same as the First")
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "TYRIAN X (Episode 3) - Tank Turn-and-fire Secret")

    wanted_armor = get_difficulty_armor_choice(world, base=(6, 6, 5, 5))
    logic_entrance_rule(world, "TYRIAN X (Episode 3) @ Base Requirements", lambda state, armor=wanted_armor:
          has_repulsor(state, world.player)
          or has_armor_level(state, world.player, armor))

    # Spinners: 6 (difficulty +1 due to level)
    enemy_health = scale_health(world, 6, adjust_difficulty=+1)
    dps_active = world.damage_tables.make_dps(active=(enemy_health * 6) / 1.1)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 1.1)
    logic_location_rule(world, "TYRIAN X (Episode 3) - Platform Spinner Sequence", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # Tanks: 10 (difficulty +1 due to level); purple structures: 6 (same)
    structure_health = scale_health(world, 6, adjust_difficulty=+1) * 3  # Purple structure
    enemy_health = scale_health(world, 10, adjust_difficulty=+1)  # Tank
    dps_active = world.damage_tables.make_dps(active=(structure_health + enemy_health) / 1.1)
    dps_piercing = world.damage_tables.make_dps(piercing=enemy_health / 1.1)
    logic_entrance_rule(world, "TYRIAN X (Episode 3) @ Tanks Behind Structures", lambda state, dps1=dps_piercing, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # The boss is almost identical to its appearance in Tyrian, so the conditions are the similar.
    # Only the wing's health has changed (254, instead of scaled 100)
    dps_active = world.damage_tables.make_dps(active=508 / 30.0)
    dps_piercing = world.damage_tables.make_dps(piercing=254 / 30.0)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state, dps1=dps_piercing, dps2=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
    else:
        # The armor condition from Episode 1 would always be true here, we assume a time-out can always happen
        logic_location_rule(world, "TYRIAN (Episode 1) - Boss", lambda state, dps1=dps_piercing, dps2=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== SAVARA Y ==========================================================
    # Blimp: 70
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 70) / 3.6)
    # On Master, you're expected to know how to dodge this when enemies are blocking the entire screen.
    # Otherwise, we should make you can blow up the blimp.
    if world.options.logic_difficulty <= LogicDifficulty.option_expert:
        logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Through Blimp Blockade", lambda state, dps1=dps_active:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1))

    dps_active = world.damage_tables.make_dps(active=254 / 4.4)
    logic_location_rule(world, "SAVARA Y (Episode 3) - Boss Ship Fly-By", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Vulcan planes with items: 14
    # As in Episode 1, prefer kills with passive
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 14) / 1.6)
    dps_passive = world.damage_tables.make_dps(passive=scale_health(world, 14) / 2.4)
    logic_location_rule(world, "SAVARA Y (Episode 3) - Vulcan Plane Set", lambda state, dps1=dps_passive, dps2=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or can_deal_damage(state, world.player, world.damage_tables, dps2))

    dps_active = world.damage_tables.make_dps(active=scale_health(world, 14) / 1.2)
    logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Death Plane Set", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Same boss as Episode 1 Savaras; here, though, the boss here has no patience and leaves VERY fast
    boss_health = 254 + (scale_health(world, 6) * 15) + (scale_health(world, 10) * 4)
    dps_active = world.damage_tables.make_dps(active=boss_health / 13.0)
    dps_tick = world.damage_tables.make_dps(sideways=scale_health(world, 6) / 1.2)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Pass Boss (can time out)", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))
    else:
        logic_location_rule(world, "SAVARA Y (Episode 3) - Boss", lambda state, dps1=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1))

        # Also need enough damage to destroy things the boss shoots at you, when dodging isn't an option
        logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Pass Boss (can time out)", lambda state, dps1=dps_tick, dps2=dps_active:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))

    # ===== NEW DELI ==========================================================
    # Turrets: 10
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 10) / 1.8)
    wanted_armor = get_difficulty_armor_choice(world, base=(12, 12, 11, 9))
    logic_entrance_rule(world, "NEW DELI (Episode 3) @ Base Requirements", lambda state, armor=wanted_armor, dps1=dps_active:
          (
              has_repulsor(state, world.player)
              and has_armor_level(state, world.player, armor - 3)
              and has_generator_level(state, world.player, 3)
              and can_deal_damage(state, world.player, world.damage_tables, dps1)
          ) or (
              has_armor_level(state, world.player, armor)
              and has_generator_level(state, world.player, 4)
              and can_deal_damage(state, world.player, world.damage_tables, dps1)
          ))

    # Repulsor orbs: 80
    # One pops up on the screen during all this mess. Getting it OFF the screen quickly is the goal here.
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 80) / 5.0)
    logic_entrance_rule(world, "NEW DELI (Episode 3) @ The Gauntlet Begins", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Same boss as DELIANI (Episode 1), copied from there.
    # Repulsor orbs: 80; boss: 200
    boss_health = (scale_health(world, 80) * 3) + scale_health(world, 200)
    dps_active = world.damage_tables.make_dps(active=boss_health / 22.0)
    logic_entrance_rule(world, "NEW DELI (Episode 3) @ Destroy Boss", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))

    # ===== FLEET =============================================================
    # Item ships: 20 -- These flee quickly; and using them to lock off the entire level is convenient
    wanted_armor = get_difficulty_armor_choice(world, base=(11, 10, 10, 7), hard_contact=(13, 12, 11, 9))
    wanted_energy = 4 if world.options.logic_difficulty <= LogicDifficulty.option_expert else 3
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 20) / 1.5)
    logic_entrance_rule(world, "FLEET (Episode 3) @ Base Requirements", lambda state, dps1=dps_active, armor=wanted_armor, energy=wanted_energy:
          has_armor_level(state, world.player, armor)
          and has_generator_level(state, world.player, energy)
          and can_deal_damage(state, world.player, world.damage_tables, dps1))

    # Attractor crane: 50; arms are invulnerable, damage that can be dealt to it is limited
    # Piercing option is always available for both attractor cranes
    # If you have invulnerability, you can also use that to pierce briefly.
    dps_pierceopt = world.damage_tables.make_dps(piercing=scale_health(world, 50) / 10.0)
    dps_invulnopt = world.damage_tables.make_dps(active=scale_health(world, 50) / 3.0)
    dps_active = world.damage_tables.make_dps(active=scale_health(world, 50) / 1.6)

    if world.options.logic_difficulty == LogicDifficulty.option_master:
        # You have invulnerability at the start of the level. Exploit it.
        logic_location_rule(world, "FLEET (Episode 3) - Attractor Crane, Entrance", lambda state, dps1=dps_pierceopt, dps2=dps_invulnopt:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or can_deal_damage(state, world.player, world.damage_tables, dps2))
    else:
        logic_location_rule(world, "FLEET (Episode 3) - Attractor Crane, Entrance", lambda state, dps1=dps_pierceopt, dps2=dps_invulnopt, dps3=dps_active:
              can_deal_damage(state, world.player, world.damage_tables, dps1)
              or (
                  has_invulnerability(state, world.player)
                  and can_deal_damage(state, world.player, world.damage_tables, dps2)
              )
              or can_deal_damage(state, world.player, world.damage_tables, dps3))

    logic_location_rule(world, "FLEET (Episode 3) - Attractor Crane, Mid-Fleet", lambda state, dps1=dps_pierceopt, dps2=dps_invulnopt, dps3=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1)
          or (
              has_invulnerability(state, world.player)
              and can_deal_damage(state, world.player, world.damage_tables, dps2)
          )
          or can_deal_damage(state, world.player, world.damage_tables, dps3))


    # This boss regularly heals, spams enemies across the screen, etc...
    dps_active = world.damage_tables.make_dps(active=(254 * 1.5) / 8.0)
    logic_entrance_rule(world, "FLEET (Episode 3) @ Destroy Boss", lambda state, dps1=dps_active:
          can_deal_damage(state, world.player, world.damage_tables, dps1))


# =================================================================================================
#                                    EPISODE 4 (AN END TO FATE)
# =================================================================================================


def episode_4_rules(world: "TyrianWorld") -> None:
    pass


# =================================================================================================
#                                    EPISODE 5 (HAZUDRA FODDER)
# =================================================================================================


def episode_5_rules(world: "TyrianWorld") -> None:
    pass


# =================================================================================================


def set_level_rules(world: "TyrianWorld") -> None:
    # If in no logic mode, we do none of this.
    # Notably, logic for unlocking levels functions outside of this, so you won't have self-locking levels or other
    # impossible scenarios like that. Just an assumption that you can beat anything thrown at you.
    if world.options.logic_difficulty == LogicDifficulty.option_no_logic:
        return

    if Episode.Escape in world.play_episodes:         episode_1_rules(world)
    if Episode.Treachery in world.play_episodes:      episode_2_rules(world)
    if Episode.MissionSuicide in world.play_episodes: episode_3_rules(world)
    if Episode.AnEndToFate in world.play_episodes:    episode_4_rules(world)
    if Episode.HazudraFodder in world.play_episodes:  episode_5_rules(world)
