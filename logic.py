# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import TYPE_CHECKING, Callable, Optional, List, Dict, Tuple
from enum import IntFlag
from itertools import product

from BaseClasses import LocationProgressType as LPType
from worlds.generic.Rules import add_rule

from .items import Episode
from .options import LogicDifficulty, GameDifficulty
from .twiddles import SpecialValues

if TYPE_CHECKING:
    from BaseClasses import CollectionState
    from . import TyrianWorld


# Determined primary type of damage needed.
class DPSType(IntFlag):
    Empty    = 0b0000
    Active   = 0b0001
    Passive  = 0b0010
    Sideways = 0b0100
    Piercing = 0b1000


class DPS:
    _type: DPSType
    active: float
    passive: float
    sideways: float
    piercing: float

    def __init__(self, active: float = 0.0, passive: float = 0.0, sideways: float = 0.0, piercing: float = 0.0):
        self.active = active
        self.passive = passive
        self.sideways = sideways
        self.piercing = piercing

        self._type = DPSType.Empty
        if active > 0.0:   self._type |= DPSType.Active
        if passive > 0.0:  self._type |= DPSType.Passive
        if sideways > 0.0: self._type |= DPSType.Sideways
        if piercing > 0.0: self._type |= DPSType.Piercing

    def __sub__(self, other: "DPS") -> "DPS":
        new_active = max(self.active - other.active, 0.0)
        new_passive = max(self.passive - other.passive, 0.0)
        new_sideways = max(self.sideways - other.sideways, 0.0)
        new_piercing = max(self.piercing - other.piercing, 0.0)
        return DPS(new_active, new_passive, new_sideways, new_piercing)

    def meets_requirements(self, requirements: "DPS") -> Tuple[bool, float]:
        distance = 0.0

        # Apply some weighting to distance
        # Rear weapons can easily take care of passive and sideways requirements
        # But active is much harder, and piercing is entirely impossible
        if requirements.active > 0.0 and self.active < requirements.active:
            distance += (requirements.active - self.active) * 4.0
        if requirements.passive > 0.0 and self.passive < requirements.passive:
            distance += (requirements.passive - self.passive) * 0.8
        if requirements.sideways > 0.0 and self.sideways < requirements.sideways:
            distance += (requirements.sideways - self.sideways) * 1.8
        if requirements.piercing > 0.0 and self.piercing < requirements.piercing:
            distance += 10000.0

        if distance < 0.0001:
            return (True, 0.0)
        return (False, distance)


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

    # Used as a return result, check for equality (same instance)
    dps_result_success = DPS(0.0, 0.0, 0.0, 0.0)

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

            success, _ = self.local_dps[weapon][power].meets_requirements(target_dps)
            if success:
                return True
        return False

    def get_dps_shot_types(self, target_dps: DPS, weapons: List[str],
          max_power_level: int = 11, rest_energy: int = 99) -> Dict[int, DPS]:
        best_distances: Dict[int, float] = {}  # energy required: distance
        results: Dict[int, DPS] = {}  # energy required: full DPS info (returned)

        for (weapon, power) in product(weapons, range(max_power_level)):
            cur_energy_req = self.generator_power_required[weapon][power]
            if cur_energy_req > rest_energy:
                continue

            cur_dps = self.local_dps[weapon][power]
            success, distance = cur_dps.meets_requirements(target_dps)

            if success:  # Target DPS has been met, abandon further searching
                return {cur_energy_req: self.dps_result_success}
            elif distance < best_distances.get(cur_energy_req, 512.0):
                best_distances[cur_energy_req] = distance
                results[cur_energy_req] = target_dps - cur_dps

        return results


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

def get_front_weapon_state(state: "CollectionState", player: int, _type: DPSType) -> List[str]:
    keys = state.prog_items[player].keys()
    if _type & DPSType.Piercing:
        return [name for name in ordered_front_table_piercing if name in keys]
    elif _type & DPSType.Active:
        return [name for name in ordered_front_table_active if name in keys]
    else:
        return [name for name in ordered_front_table_other if name in keys]

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

def get_rear_weapon_state(state: "CollectionState", player: int, _type: DPSType) -> List[str]:
    keys = state.prog_items[player].keys()
    if _type & DPSType.Sideways:
        return [name for name in ordered_rear_table_sideways if name in keys]
    elif _type & DPSType.Passive:
        return [name for name in ordered_rear_table_passive if name in keys]
    else:
        return [name for name in ordered_rear_table_other if name in keys]

# =================================================================================================

def get_maximum_power_level(state: "CollectionState", player: int) -> int:
    return min(11, 1 + state.count("Maximum Power Up", player))

def get_generator_level(state: "CollectionState", player: int) -> int:
    # Handle progressive and non-progressive generators independently
    # Otherwise collecting in different orders could result in different generator levels
    if state.has("Gravitron Pulse-Wave", player):   return 6
    elif state.has("Advanced MicroFusion", player): return 5
    elif state.has("Standard MicroFusion", player): return 4
    elif state.has("Gencore Custom MR-12", player): return 3
    elif state.has("Advanced MR-12", player):       return 2
    return min(6, 1 + state.count("Progressive Generator", player))

def get_base_energy_level(state: "CollectionState", player: int, damage_tables: DamageTables) -> int:
    return damage_tables.local_power_provided[get_generator_level(state, player)]

# =================================================================================================

def can_deal_damage(state: "CollectionState", player: int, damage_tables: DamageTables,
          active: float = 0.0, passive: float = 0.0, sideways: float = 0.0, piercing: float = 0.0) -> bool:
    target_dps = DPS(active=active * damage_tables.logic_difficulty_multiplier,
                     passive=passive * damage_tables.logic_difficulty_multiplier,
                     sideways=sideways * damage_tables.logic_difficulty_multiplier,
                     piercing=piercing * damage_tables.logic_difficulty_multiplier)

    owned_front = get_front_weapon_state(state, player, target_dps._type)
    owned_rear = get_rear_weapon_state(state, player, target_dps._type)
    power_level_max = get_maximum_power_level(state, player)
    start_energy = get_base_energy_level(state, player, damage_tables)

    best_front_dps_list = damage_tables.get_dps_shot_types(target_dps, owned_front, power_level_max, start_energy)
    for (used_energy, rest_dps) in best_front_dps_list.items():
        if rest_dps == damage_tables.dps_result_success:
            return True # Found positive result from just front weapon, instant pass

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
    world = state.multiworld.worlds[player]
    return action in [twiddle.action for twiddle in world.twiddles]

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

def logic_all_locations_rule(world: "TyrianWorld", location_name_base: str, rule: Callable[..., bool]) -> None:
    for location in [i for i in world.multiworld.get_locations(world.player) if i.name.startswith(location_name_base)]:
        add_rule(location, rule)

def logic_all_locations_exclude(world: "TyrianWorld", location_name_base: str) -> None:
    for location in [i for i in world.multiworld.get_locations(world.player) if i.name.startswith(location_name_base)]:
        location.progress_type = LPType.EXCLUDED

# -----------------------------------------------------------------------------

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
        enemy_health = scale_health(world, 19) # Not tied to a specific enemy
        logic_location_rule(world, "TYRIAN (Episode 1) - HOLES Warp Orb", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/2.0)
              or can_deal_damage(state, world.player, world.damage_tables, passive=health/1.5))

    enemy_health = scale_health(world, 20) # Health of rock
    logic_location_rule(world, "TYRIAN (Episode 1) - BUBBLES Warp Rock", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.6))

    boss_health = scale_health(world, 100) + 254 # Health of one wing + boss
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/30.0)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=254/30.0))
    else:
        wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(6, 6, 5, 5))
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state, health=boss_health, armor=wanted_armor:
              has_armor_level(state, world.player, armor)
              or has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, active=health/30.0)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=254/30.0))
        logic_location_rule(world, "TYRIAN (Episode 1) - Boss", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/30.0)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=254/30.0))

    # ===== BUBBLES ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_all_locations_exclude(world, "BUBBLES (Episode 1) - Coin Rain")

    enemy_health = scale_health(world, 20) # Health of red bubbles (in all cases)
    logic_entrance_rule(world, "BUBBLES (Episode 1) @ Pass Bubble Lines", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/4.0))
    logic_entrance_rule(world, "BUBBLES (Episode 1) @ Speed Up Section", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.9))

    logic_location_rule(world, "BUBBLES (Episode 1) - Orbiting Bubbles", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.0)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/4.0))
    logic_location_rule(world, "BUBBLES (Episode 1) - Shooting Bubbles", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.2)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/4.0))

    # ===== HOLES =============================================================
    logic_entrance_rule(world, "HOLES (Episode 1) @ Pass Spinner Gauntlet", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=8.0, passive=21.0))

    wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(8, 7, 6, 5))
    logic_entrance_rule(world, "HOLES (Episode 1) @ Pass Spinner Gauntlet", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))
   
    boss_health = scale_health(world, 100) + 254 # Health of one wing + boss
    logic_entrance_rule(world, "HOLES (Episode 1) @ Destroy Boss Ships", lambda state, health=boss_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/5.0, passive=21.0))

    # ===== SOH JIN ===========================================================
    enemy_health = scale_health(world, 40) # Single wall tile
    logic_entrance_rule(world, "SOH JIN (Episode 1) @ Destroy Walls", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/4.6))

    # ===== ASTEROID1 =========================================================
    enemy_health = scale_health(world, 25) + (scale_health(world, 5) * 2) # Face rock, plus tiles before it
    logic_location_rule(world, "ASTEROID1 (Episode 1) - ASTEROID? Warp Orb", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/4.4))

    boss_health = scale_health(world, 100) # Only the boss dome
    logic_entrance_rule(world, "ASTEROID1 (Episode 1) @ Destroy Boss", lambda state, health=boss_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))

    # ===== ASTEROID2 =========================================================    
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1")
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2")
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "ASTEROID2 (Episode 1) - Tank Assault Right Tank Secret")

    enemy_health = scale_health(world, 30) # All tanks
    logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Bridge", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/2.1))

    # Tank Turn-around Secrets 1 and 2:
    # On Standard or below, assume most damage will come only after the tank secret items are active
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 1", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/2.3))
        logic_location_rule(world, "ASTEROID2 (Episode 1) - Tank Turn-around Secret 2", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/3.9))

    enemy_health = scale_health(world, 25) # Only the face rock containing the orb
    logic_location_rule(world, "ASTEROID2 (Episode 1) - MINEMAZE Warp Orb", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/4.4))

    logic_entrance_rule(world, "ASTEROID2 (Episode 1) @ Destroy Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=10.0))

    # ===== ASTEROID? =========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "ASTEROID? (Episode 1) - WINDY Warp Orb")

    enemy_health = scale_health(world, 40) # Launchers, and the secret ships
    logic_entrance_rule(world, "ASTEROID? (Episode 1) @ Initial Welcome", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.5))
    logic_entrance_rule(world, "ASTEROID? (Episode 1) @ Quick Shots", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.36))

    wanted_armor = get_difficulty_armor_choice(world, base=(6, 5, 5, 5), hard_contact=(8, 7, 7, 6))
    logic_entrance_rule(world, "ASTEROID? (Episode 1) @ Final Gauntlet", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # ===== MINEMAZE ==========================================================
    enemy_health = scale_health(world, 20) # Gates
    logic_entrance_rule(world, "MINEMAZE (Episode 1) @ Destroy Gates", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.8))

    # ===== WINDY =============================================================
    enemy_health = scale_health(world, 20) # Question mark block health
    logic_location_rule(world, "WINDY (Episode 1) - Central Question Mark", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.4))

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

    enemy_health = scale_health(world, 10) # Regular block health
    logic_entrance_rule(world, "WINDY (Episode 1) @ Fly Through", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.4))

    wanted_armor = get_difficulty_armor_choice(world, base=(7, 5, 5, 5), hard_contact=(11, 9, 8, 6))
    logic_entrance_rule(world, "WINDY (Episode 1) @ Fly Through", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # ===== SAVARA ============================================================
    enemy_health = scale_health(world, 60) # Huge planes
    logic_location_rule(world, "SAVARA (Episode 1) - Huge Plane, Speeds By", lambda state, health=enemy_health:
          has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, active=health/1.025))

    enemy_health = scale_health(world, 14) # Vulcan plane with item
    # The vulcan shots hurt a lot, so optimal kill would be with passive DPS if possible
    logic_location_rule(world, "SAVARA (Episode 1) - Vulcan Plane", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.6)
          or can_deal_damage(state, world.player, world.damage_tables, passive=health/2.4))

    # Damage estimate: 254 health for the boss, shooting through 15 ticks and 4 missiles
    boss_health = 254 + (scale_health(world, 6) * 15) + (scale_health(world, 10) * 4)
    enemy_health = scale_health(world, 6) # Homing ticks from boss
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "SAVARA (Episode 1) @ Pass Boss (can time out)", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))
    else:
        logic_location_rule(world, "SAVARA (Episode 1) - Boss", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))

        # Also need enough damage to destroy things the boss shoots at you, when dodging isn't an option
        logic_entrance_rule(world, "SAVARA (Episode 1) @ Pass Boss (can time out)", lambda state, health=boss_health, tick_health=enemy_health:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, sideways=tick_health/1.2)
              or can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))

    # ===== SAVARA II =========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(8, 7, 6, 5))
    logic_entrance_rule(world, "SAVARA II (Episode 1) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    logic_entrance_rule(world, "SAVARA II (Episode 1) @ Destroy Green Planes", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=7.0))

    enemy_health = scale_health(world, 60, adjust_difficulty=-1) # Huge planes
    logic_location_rule(world, "SAVARA II (Episode 1) - Huge Plane Amidst Turrets", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/2.3))

    enemy_health = scale_health(world, 14) # Vulcan plane with item
    # The vulcan shots hurt a lot, so optimal kill would be with passive DPS if possible
    logic_location_rule(world, "SAVARA II (Episode 1) - Vulcan Planes Near Blimp", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.6)
          or can_deal_damage(state, world.player, world.damage_tables, passive=health/2.4))

    # Damage estimate: 254 health for the boss, shooting through 15 ticks and 4 missiles
    boss_health = 254 + (scale_health(world, 6) * 15) + (scale_health(world, 10) * 4)
    enemy_health = scale_health(world, 6) # Homing ticks from boss
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "SAVARA II (Episode 1) @ Pass Boss (can time out)", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))
    else:
        logic_location_rule(world, "SAVARA II (Episode 1) - Boss", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))

        # Also need enough damage to destroy things the boss shoots at you, when dodging isn't an option
        logic_entrance_rule(world, "SAVARA II (Episode 1) @ Pass Boss (can time out)", lambda state, health=boss_health, tick_health=enemy_health:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, sideways=tick_health/1.2)
              or can_deal_damage(state, world.player, world.damage_tables, active=health/30.0))

    # ===== BONUS =============================================================
    # Temporary rule to keep this from occurring too early.
    logic_entrance_rule(world, "BONUS (Episode 1) @ Destroy Patterns", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=10.0, passive=10.0))

    # ===== MINES =============================================================
    enemy_health = scale_health(world, 20) # Rotating Orbs
    logic_entrance_rule(world, "MINES (Episode 1) @ Destroy First Orb", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.0)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/2.7))
    logic_entrance_rule(world, "MINES (Episode 1) @ Destroy Second Orb", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/0.5)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/1.2))

    # Blue mine has static health (does not depend on difficulty)
    logic_location_rule(world, "MINES (Episode 1) - Blue Mine", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=30/3.0))

    # ===== DELIANI ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "DELIANI (Episode 1) - Tricky Rail Turret")

    enemy_health = scale_health(world, 30) # Rail turret
    logic_location_rule(world, "DELIANI (Episode 1) - Tricky Rail Turret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/2.2))

    enemy_health = scale_health(world, 25) # Two-tile wide turret ships
    logic_entrance_rule(world, "DELIANI (Episode 1) @ Pass Ambush", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.6))

    wanted_armor = get_difficulty_armor_choice(world, base=(10, 9, 8, 6))
    logic_entrance_rule(world, "DELIANI (Episode 1) @ Pass Ambush", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    boss_health = (scale_health(world, 80) * 3) + scale_health(world, 200) # Repulsor orbs and boss
    logic_entrance_rule(world, "DELIANI (Episode 1) @ Destroy Boss", lambda state, health=boss_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/26.0))

    # ===== SAVARA V ==========================================================
    enemy_health = scale_health(world, 70) # Blimp
    logic_location_rule(world, "SAVARA V (Episode 1) - Super Blimp", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.5))

    logic_entrance_rule(world, "SAVARA V (Episode 1) @ Destroy Bosses", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=254/15.0))

    # ===== ASSASSIN ==========================================================
    logic_entrance_rule(world, "ASSASSIN (Episode 1) @ Destroy Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, 25.0))

    wanted_armor = get_difficulty_armor_choice(world, base=(9, 8, 7, 5))
    logic_entrance_rule(world, "ASSASSIN (Episode 1) @ Destroy Boss", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

# -----------------------------------------------------------------------------

def episode_2_rules(world: "TyrianWorld") -> None:
    # ===== TORM ==============================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret")

    # On standard or below, require killing the dragon behind the secret ship
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        enemy_health = scale_health(world, 40)
        logic_location_rule(world, "TORM (Episode 2) - Ship Fleeing Dragon Secret", lambda state, health=enemy_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/1.6))

    logic_location_rule(world, "TORM (Episode 2) - Boss Ship Fly-By", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=254/4.4))

    # Technically this boss has 254 health, but compensating for constant movement all over the screen
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "TORM (Episode 2) @ Pass Boss (can time out)", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=(254*1.75)/32.0))
    else:
        # The actual time out is attainable with an empty loadout
        logic_location_rule(world, "TORM (Episode 2) - Boss", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=(254*1.75)/32.0))


    # ===== GYGES =============================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "GYGES (Episode 2) - GEM WAR Warp Orb")

    enemy_health = scale_health(world, 10) * 6 # Orbsnakes
    logic_location_rule(world, "GYGES (Episode 2) - Orbsnake", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/5.0)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=(health/6)/5.0))

    # Either the repulsor mitigates the bullets in the speed up section,
    # or you have a decent loadout and can destroy a few things to make your life easier
    logic_entrance_rule(world, "GYGES (Episode 2) @ After Speed Up Section", lambda state:
          has_repulsor(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, active=8.0, passive=12.0))

    logic_entrance_rule(world, "GYGES (Episode 2) @ Destroy Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=254/45.0))

    # ===== BONUS 1 ===========================================================
    # Temporary rule to keep this from occurring too early.
    logic_entrance_rule(world, "BONUS 1 (Episode 2) @ Destroy Patterns", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=10.0, passive=10.0))

    # ===== ASTCITY ===========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 7, 6, 5), hard_contact=(7, 7, 6, 5))
    logic_entrance_rule(world, "ASTCITY (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "ASTCITY (Episode 2) - MISTAKES Warp Orb")

    enemy_health = scale_health(world, 30, adjust_difficulty=-1) # Building
    logic_location_rule(world, "ASTCITY (Episode 2) - Warehouse 92", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/4.0))

    # In all likelihood this can be obliterated with a superbomb that you obtain in the level,
    # but we don't consider superbombs logic in any way, so
    logic_entrance_rule(world, "ASTCITY (Episode 2) @ Last Platform", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=8.0, passive=14.0))

    # ===== BONUS 2 ===========================================================
    # (logicless - flythrough only, no items, easily doable without firing a shot)

    # ===== GEM WAR ===========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 7, 6, 5), hard_contact=(9, 9, 8, 6))
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    # Red Gem Ships have 254 health; we compensate for their movement, and other enemies being nearby
    wanted_passive = 18.0 if world.options.contact_bypasses_shields else 12.0
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Red Gem Leaders Easy", lambda state, passive=wanted_passive:
          can_deal_damage(state, world.player, world.damage_tables, active=(254*1.4)/20.0, passive=passive))  # 2 and 3
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Red Gem Leaders Medium", lambda state, passive=wanted_passive:
          can_deal_damage(state, world.player, world.damage_tables, active=(254*1.4)/17.5, passive=passive))  # 1
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Red Gem Leaders Hard", lambda state, passive=wanted_passive:
          can_deal_damage(state, world.player, world.damage_tables, active=(254*1.4)/13.0, passive=passive))  # 4

    # The boss ships are flanked by three ships with max health of 254,
    # either you need to destroy the one in front, or have a piercing weapon
    enemy_health = scale_health(world, 20) # Center of boss ship
    logic_entrance_rule(world, "GEM WAR (Episode 2) @ Blue Gem Bosses", lambda state, health=enemy_health, passive=wanted_passive:
          can_deal_damage(state, world.player, world.damage_tables, active=(254+health)/16.0, passive=passive)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/16.0, passive=passive))

    # ===== MARKERS ===========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "MARKERS (Episode 2) - Car Destroyer Secret")

    # Flying through this stage is relatively easy *unless* HardContact is turned on.
    wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(9, 8, 8, 6))
    logic_entrance_rule(world, "MARKERS (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor))

    enemy_health = scale_health(world, 30) + (scale_health(world, 6) * 4) # Minelayer + estimated 4 mines
    logic_location_rule(world, "MARKERS (Episode 2) - Persistent Mine-Layer", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/7.1))

    enemy_health = scale_health(world, 10) # Cars
    logic_location_rule(world, "MARKERS (Episode 2) - Car Destroyer Secret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.0))

    enemy_health = scale_health(world, 20) # Turrets
    logic_entrance_rule(world, "MARKERS (Episode 2) @ Destroy Turrets", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.8))

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

    enemy_health = scale_health(world, 10) # Most trigger enemies
    logic_entrance_rule(world, "MISTAKES (Episode 2) @ Bubble Spawner Path", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.2))

    enemy_health = scale_health(world, 10) * 6 # Orbsnakes
    logic_location_rule(world, "MISTAKES (Episode 2) - Orbsnakes, Trigger Enemy 1", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/5.5)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=(health/6)/5.5))
    logic_entrance_rule(world, "MISTAKES (Episode 2) @ Softlock Path", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/0.8)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=(health/6)/0.8))

    # ===== SOH JIN ===========================================================
    enemy_health = scale_health(world, 15) # Brown claw enemy

    # These enemies don't contain any items, but they home in on you and are a bit more difficult to dodge because
    # of that, so lock the whole level behind being able to destroy them; it's enough DPS to get locations here
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Base Requirements", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/2.0))

    enemy_health = scale_health(world, 100) # Paddle... things?
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Destroy Second Wave Paddles", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/9.0)
          or can_deal_damage(state, world.player, world.damage_tables, active=health/15.0, sideways=10.0))

    # Dodging these orbs is surprisingly difficult, because of the erratic vertical movement with their oscillation
    wanted_armor = get_difficulty_armor_choice(world, base=(9, 8, 7, 5), hard_contact=(11, 10, 9, 7))
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Fly Through Third Wave Orbs", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          or (
              has_invulnerability(state, world.player)
              and has_armor_level(state, world.player, armor-2)
          ))
    logic_entrance_rule(world, "SOH JIN (Episode 2) @ Destroy Third Wave Orbs", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=254/20.0, sideways=254/20.0)) 

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

    enemy_health = scale_health(world, 15, adjust_difficulty=+1) # Moving turret
    logic_entrance_rule(world, "BOTANY A (Episode 2) @ Can Destroy Turrets", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/2.0))
    logic_location_rule(world, "BOTANY A (Episode 2) - Mobile Turret Approaching Head-On", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.0))

    # This one comes before "Beyond Starting Area"...
    logic_location_rule(world, "BOTANY A (Episode 2) - Retreating Mobile Turret", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/3.0))

    # The backmost ship is the one with the item, expect to destroy at least one other ship to reach it
    # (except if you can do enough piercing damage, of course)
    enemy_health = scale_health(world, 20, adjust_difficulty=+1) # Green ship
    logic_location_rule(world, "BOTANY A (Episode 2) - Green Ship Pincer", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=(health*2)/3.0)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/3.0))

    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "BOTANY A (Episode 2) @ Pass Boss (can time out)", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=(254*1.8)/24.0))
    else:
        logic_location_rule(world, "BOTANY A (Episode 2) - Boss", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=(254*1.8)/24.0))

    # ===== BOTANY B ==========================================================
    # Start of level, nothing nearby dangerous, only need to destroy it
    enemy_health = scale_health(world, 6, adjust_difficulty=+1) # Destructible sensor
    logic_location_rule(world, "BOTANY B (Episode 2) - Starting Platform Sensor", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/4.0))

    # Past this point is when the game starts demanding more of you.
    # Need enough damage to clear out the screen of turrets
    enemy_health = scale_health(world, 15, adjust_difficulty=+1) # Moving turret
    logic_entrance_rule(world, "BOTANY B (Episode 2) @ Beyond Starting Platform", lambda state, health=enemy_health:
          has_armor_level(state, world.player, 7)
          and (
              can_deal_damage(state, world.player, world.damage_tables, active=(health*4)/4.5)
              or can_deal_damage(state, world.player, world.damage_tables, passive=(health*4)/3.0)
          ))

    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "BOTANY B (Episode 2) @ Pass Boss (can time out)", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=(254*1.8)/24.0))
    else:
        logic_location_rule(world, "BOTANY B (Episode 2) - Boss", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=(254*1.8)/24.0))

    # ===== GRYPHON ===========================================================
    wanted_armor = get_difficulty_armor_choice(world, base=(10, 9, 8, 7), hard_contact=(11, 10, 10, 8))
    logic_entrance_rule(world, "GRYPHON (Episode 2) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          and has_generator_level(state, world.player, 3)
          and can_deal_damage(state, world.player, world.damage_tables, active=22.0, passive=16.0))

# -----------------------------------------------------------------------------

def episode_3_rules(world: "TyrianWorld") -> None:
    # ===== GAUNTLET ==========================================================
    enemy_health = scale_health(world, 10, adjust_difficulty=-1) # Capsule ships
    logic_location_rule(world, "GAUNTLET (Episode 3) - Capsule Ships Near Mace", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.3))

    enemy_health = scale_health(world, 20, adjust_difficulty=-1) # Gates
    logic_location_rule(world, "GAUNTLET (Episode 3) - Doubled-up Gates", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=(health*2)/4.4)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/4.4))
    logic_location_rule(world, "GAUNTLET (Episode 3) - Split Gates, Left", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.5))
    logic_location_rule(world, "GAUNTLET (Episode 3) - Gate near Freebie Item", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.5))

    enemy_health = scale_health(world, 6, adjust_difficulty=-1) # Weak-point orb
    # Invulnerability lets you safely pass through without damaging
    logic_entrance_rule(world, "GAUNTLET (Episode 3) @ Clear Orb Tree", lambda state, health=enemy_health:
          has_invulnerability(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, active=health/0.5)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/1.2))
    logic_location_rule(world, "GAUNTLET (Episode 3) - Tree of Spinning Orbs", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/0.5)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/1.2))

    # ===== IXMUCANE ==========================================================
    # Backside of minelayers (weak point) - front has 254/max, dropped mine has double this
    enemy_health = scale_health(world, 10)

    # Sideways + active to be able to hit the weak points of the center minelayers while damaging other things,
    # Piercing to hit those weak points through other things anyway, or just a lot of active damage altogether.
    # Alternatively, Invulnerability can also fill piercing's role.
    logic_entrance_rule(world, "IXMUCANE (Episode 3) @ Pass Minelayers Requirements", lambda state, health=enemy_health:
          has_invulnerability(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, active=8.0, sideways=health/8.0)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=(health*2)/8.0)
          or can_deal_damage(state, world.player, world.damage_tables, active=((health*6)+254)/8.0))

    # This boss keeps itself guarded inside an indestructible rock at almost all times, and there's a second
    # destructible target in front of the actual weak point... But none of this matters if you can pierce.
    # It also summons a mass of tiny rocks as an attack, so if we aren't cheesing it, we want at least some passive.
    boss_health = scale_health(world, 25)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "IXMUCANE (Episode 3) @ Pass Boss (can time out)", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, piercing=health/24.0)
              or can_deal_damage(state, world.player, world.damage_tables, active=(health*2)/3.8, passive=12.0))
    else:
        # Piercing for cheese kill, or passive to destroy some rocks for safety while we wait
        logic_entrance_rule(world, "IXMUCANE (Episode 3) @ Pass Boss (can time out)", lambda state, health=boss_health:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=health/24.0)
              or can_deal_damage(state, world.player, world.damage_tables, passive=12.0))
        logic_location_rule(world, "IXMUCANE (Episode 3) - Boss", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, piercing=health/24.0)
              or can_deal_damage(state, world.player, world.damage_tables, active=(health*2)/3.8, passive=12.0))

    # ===== BONUS =============================================================
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "BONUS (Episode 3) - Sonic Wave Hell Turret")
        logic_all_locations_exclude(world, "Shop - BONUS (Episode 3)")

    # Turrets have only one health; they die to any damage, but are guarded from front and back.
    if world.options.logic_difficulty <= LogicDifficulty.option_expert:
        logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 1", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, passive=0.2)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=0.2))
        logic_location_rule(world, "BONUS (Episode 3) - Sonic Wave Hell Turret", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, passive=0.2)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=0.2))

    # Doesn't sway left/right like the other two
    logic_location_rule(world, "BONUS (Episode 3) - Lone Turret 2", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, passive=0.2)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=0.2))

    # To pass the turret onslaught
    enemy_health = (scale_health(world, 25) - 10) # Two-wide turret, to take down to damaged (non-firing) state
    logic_entrance_rule(world, "BONUS (Episode 3) @ Pass Onslaughts", lambda state, health=enemy_health:
          has_repulsor(state, world.player)
          or can_deal_damage(state, world.player, world.damage_tables, active=(health*4)/3.6))
    logic_entrance_rule(world, "BONUS (Episode 3) @ Pass Onslaughts", lambda state:
          has_generator_level(state, world.player, 3)  # For shield recovery
          and has_armor_level(state, world.player, 8)) 

    # Do you have knowledge of the safe spot through this section? Master assumes you do, anything else doesn't.
    # If we're not assuming safe spot knowledge, we need the repulsor, or some sideways DPS and more armor.
    if world.options.logic_difficulty < LogicDifficulty.option_master:
        logic_entrance_rule(world, "BONUS (Episode 3) @ Sonic Wave Hell", lambda state, health=enemy_health:
              has_repulsor(state, world.player)
              or (
                  has_armor_level(state, world.player, 12)
                  and can_deal_damage(state, world.player, world.damage_tables, active=health/3.6, sideways=4.0)
              ))

    # To actually get the items from turret onslaught
    enemy_health = (scale_health(world, 25) * 2) + scale_health(world, 3) # Two two-tile turrets, plus item ship
    logic_entrance_rule(world, "BONUS (Episode 3) @ Get Items from Onslaughts", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.8))

    # ===== STARGATE ==========================================================
    # Just need some way of combating the bubble spam that happens after the last normal location
    logic_entrance_rule(world, "STARGATE (Episode 3) @ Reach Bubble Spawner", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, passive=7.0))

    # ===== AST. CITY =========================================================
    # TODO

    # ===== SAWBLADES =========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "SAWBLADES (Episode 3) - SuperCarrot Drop")

    # Periodically, tiny rocks get spammed all over the screen throughout this level.
    # We need to have some passive and some armor to be able to deal with these moments.
    wanted_armor = get_difficulty_armor_choice(world, base=(7, 6, 6, 5), hard_contact=(10, 9, 8, 6))
    logic_entrance_rule(world, "SAWBLADES (Episode 3) @ Base Requirements", lambda state, armor=wanted_armor:
          has_armor_level(state, world.player, armor)
          and can_deal_damage(state, world.player, world.damage_tables, active=10.0, passive=12.0))

    enemy_health = scale_health(world, 60) # Blue sawblade
    logic_location_rule(world, "SAWBLADES (Episode 3) - Waving Sawblade", lambda state, health=enemy_health:
        can_deal_damage(state, world.player, world.damage_tables, active=health/4.1, passive=12.0))

    # ===== CAMANIS ===========================================================
    # TODO

    # ===== MACES =============================================================
    # (logicless - purely a test of dodging skill)

    # ===== TYRIAN X ==========================================================
    if world.options.logic_difficulty == LogicDifficulty.option_beginner:
        logic_location_exclude(world, "TYRIAN X (Episode 3) - First U-Ship Secret")
        logic_location_exclude(world, "TYRIAN X (Episode 3) - Second Secret, Same as the First")
    if world.options.logic_difficulty <= LogicDifficulty.option_standard:
        logic_location_exclude(world, "TYRIAN X (Episode 3) - Tank Turn-and-fire Secret")

    enemy_health = scale_health(world, 6, adjust_difficulty=+1)  # Spinners
    logic_location_rule(world, "TYRIAN X (Episode 3) - Platform Spinner Sequence", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=(health*6)/1.1)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/1.1))

    structure_health = scale_health(world, 6, adjust_difficulty=+1) * 3  # Purple structure
    enemy_health = scale_health(world, 10, adjust_difficulty=+1)  # Tank
    logic_entrance_rule(world, "TYRIAN X (Episode 3) @ Tanks Behind Structures", lambda state, althealth=structure_health, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=(althealth+health)/1.1)
          or can_deal_damage(state, world.player, world.damage_tables, piercing=health/1.1))

    # The boss is almost identical to its appearance in Tyrian, so the conditions are the similar.
    # Only the wing's health has changed (254, instead of scaled 100)
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=508/30.0)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=254/30.0))
    else:
        wanted_armor = get_difficulty_armor_choice(world, base=(5, 5, 5, 5), hard_contact=(6, 6, 5, 5))
        logic_entrance_rule(world, "TYRIAN (Episode 1) @ Pass Boss (can time out)", lambda state, armor=wanted_armor:
              has_armor_level(state, world.player, armor)
              or has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, active=508/30.0)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=254/30.0))
        logic_location_rule(world, "TYRIAN (Episode 1) - Boss", lambda state:
              can_deal_damage(state, world.player, world.damage_tables, active=508/30.0)
              or can_deal_damage(state, world.player, world.damage_tables, piercing=254/30.0))

    # ===== SAVARA Y ==========================================================
    enemy_health = scale_health(world, 70) # Blimp
    if world.options.logic_difficulty <= LogicDifficulty.option_expert:
        logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Through Blimp Blockade", lambda state, health=enemy_health:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, active=enemy_health/3.6))
    # Else, on Master, you're expected to know how to dodge this when enemies are blocking the entire screen.

    logic_location_rule(world, "SAVARA Y (Episode 3) - Boss Ship Fly-By", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=254/4.4))

    enemy_health = scale_health(world, 14) # Vulcan planes with items
    # As in Episode 1, prefer kills with passive
    logic_location_rule(world, "SAVARA Y (Episode 3) - Vulcan Plane Set", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.6)
          or can_deal_damage(state, world.player, world.damage_tables, passive=health/2.4))
    logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Death Plane Set", lambda state, health=enemy_health:
          can_deal_damage(state, world.player, world.damage_tables, active=health/1.2))

    # Same boss as Episode 1 Savaras; here, though, the boss here has no patience and leaves VERY fast
    boss_health = 254 + (scale_health(world, 6) * 10) + (scale_health(world, 10) * 3)
    enemy_health = scale_health(world, 6) # Homing ticks from boss
    if not world.options.logic_boss_timeout:
        logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Pass Boss (can time out)", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/15.0))
    else:
        logic_location_rule(world, "SAVARA Y (Episode 3) - Boss", lambda state, health=boss_health:
              can_deal_damage(state, world.player, world.damage_tables, active=health/15.0))

        # Also need enough damage to destroy things the boss shoots at you, when dodging isn't an option
        logic_entrance_rule(world, "SAVARA Y (Episode 3) @ Pass Boss (can time out)", lambda state, health=boss_health, tick_health=enemy_health:
              has_invulnerability(state, world.player)
              or can_deal_damage(state, world.player, world.damage_tables, sideways=tick_health/1.2)
              or can_deal_damage(state, world.player, world.damage_tables, active=health/15.0))

    # ===== NEW DELI ==========================================================
    # TODO

    # ===== FLEET =============================================================
    # TODO
    logic_entrance_rule(world, "FLEET (Episode 3) @ Destroy Boss", lambda state:
          has_armor_level(state, world.player, 12) and has_generator_level(state, world.player, 4))
    logic_entrance_rule(world, "FLEET (Episode 3) @ Destroy Boss", lambda state:
          can_deal_damage(state, world.player, world.damage_tables, active=50.0))

# -----------------------------------------------------------------------------

def episode_4_rules(world: "TyrianWorld") -> None:
    pass

# -----------------------------------------------------------------------------

def episode_5_rules(world: "TyrianWorld") -> None:
    pass

# -----------------------------------------------------------------------------

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
