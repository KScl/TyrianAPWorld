# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from enum import IntEnum

class ComboInput:
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    UP_FIRE = 5
    DOWN_FIRE = 6
    LEFT_FIRE = 7
    RIGHT_FIRE = 8
    NEUTRAL = 9

class Twiddle:
    default_twiddles = {
        "Invulnerability": ['Down', 'Up', 'Down', 'Up+Fire'], # All Shield
        "Atom Bomb": ['Right', 'Left', 'Down', 'Up+Fire'], # 2 Armor
        "Seeker Bombs": ['Left', 'Right', 'Down+Fire'] # 3 Armor
        "Ice Blast": ['Down', 'Up+Fire'] # 4 Shield
        "Auto Repair": ['Down+Fire', 'Down', 'Down+Fire'] # All Shield
        "Spin Wave": ['Down+Fire', 'Left+Fire', 'Up+Fire', 'Right+Fire', 'Down+Fire', 'Left+Fire', 'Up+Fire'] # 30 shield (bugged?)
        "Repulsor": ['Left+Fire', 'Right+Fire'] # 1 shield
        "Protron Field": ['Up', 'Left+Fire', 'Down+Fire'] # half shield
        "Minefield": ['Right+Fire', 'Down+Fire', 'Left+Fire', 'Up'] # 4 armor
        "Post-It Blast": ['Left', 'Down+Fire', 'Right+Fire', 'Up+Fire'] # 5 armor
        "Hot Dog": ['Up', 'Down+Fire'] # 1 armor
        "Lightning": ['Neutral', 'Up+Fire'] # Free
    }
