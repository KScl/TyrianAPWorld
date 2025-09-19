# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import TyrianWorld


class SpecialValues(IntEnum):
    # These are specials that can be used as twiddles, with their associated internal numbers.
    AtomBomb = 38
    Attractor = 4
    AutoRepair = 43
    BananaBomb = 11
    BladeField = 7
    DualVulcan = 10
    HotDog = 25
    IceBeam = 5
    IceBlast = 42
    Invulnerability = 37
    LightningLeft = 29
    LightningUpLeft = 27
    LightningUp = 26
    LightningUpRight = 28
    LightningRight = 30
    LightningZone = 40
    MegaLaserDual = 15
    MegaLaserPierce = 18
    MineSpray = 20
    MissilePod = 19
    OrangeShield = 16
    PearlWind = 44
    ProtronField = 46
    PostItBlast = 21
    ProtronDispersal = 12
    PulseBlast = 17
    Repulsor = 1
    SeekerBombs = 39
    SoulOfZinglon = 3
    XegaBall = 14


class TwidDir(IntEnum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4
    UpFire = 5
    DownFire = 6
    LeftFire = 7
    RightFire = 8
    Neutral = 9


class Twiddle:
    name: str
    command: list[TwidDir]
    action: SpecialValues
    cost: int

    def __init__(self, name: str, action: SpecialValues,
          command: list[TwidDir] = [], shield_cost: Any = None, armor_cost: Any = None):
        self.name = name
        self.action = action
        self.command = command

        if   shield_cost == "all":    self.cost = 98
        elif shield_cost == "half":   self.cost = 99
        elif shield_cost is not None: self.cost = shield_cost
        elif armor_cost is not None:  self.cost = 100 + armor_cost
        else:                         self.cost = 0

    def spoiler_command(self) -> str:
        return ", ".join(cmd.name for cmd in self.command)

    def spoiler_cost(self) -> str:
        if   self.cost == 99: return "Half Shield"
        elif self.cost == 98: return "All Shield"
        elif self.cost <= 97: return f"{self.cost} Shield"
        elif self.cost != 0:  return f"{self.cost - 100} Armor"
        return "Nothing"

    def spoiler_str(self) -> str:
        return f"{self.name}: {self.spoiler_command()} ({self.spoiler_cost()})\n"

    def to_json(self) -> dict[str, Any]:
        return {
            "Name": self.name,
            "Action": int(self.action),
            "Command": [int(cmd) for cmd in self.command],
            "Cost": int(self.cost)
        }


vanilla_twiddle_list: list[list[Twiddle]] = [
    [
        # Due to potential conflicts, pool these commands together
        # Second Invuln input sequence is the special one for the Stalker 21.126
        Twiddle("Invulnerability", SpecialValues.Invulnerability, shield_cost="all",
              command=[TwidDir.Down, TwidDir.Up, TwidDir.Down, TwidDir.UpFire]),
        Twiddle("Invulnerability", SpecialValues.Invulnerability, shield_cost="all",
              command=[TwidDir.Up, TwidDir.Left, TwidDir.DownFire]),
        Twiddle("Atom Bomb", SpecialValues.AtomBomb, armor_cost=2,
              command=[TwidDir.Right, TwidDir.Left, TwidDir.Down, TwidDir.UpFire]),
        Twiddle("Ice Blast", SpecialValues.IceBlast, shield_cost=4,
              command=[TwidDir.Down, TwidDir.UpFire]),
    ],
    [
        Twiddle("Seeker Bombs", SpecialValues.SeekerBombs, armor_cost=3,
              command=[TwidDir.Left, TwidDir.Right, TwidDir.DownFire]),
    ],
    [
        Twiddle("Auto Repair", SpecialValues.AutoRepair, shield_cost="all",
              command=[TwidDir.DownFire, TwidDir.Down, TwidDir.DownFire]),
    ],
    [
        # Note: Original shield cost is bugged (shield_cost=30 when max shield is 28)
        Twiddle("Spin Wave", SpecialValues.ProtronDispersal, shield_cost=10,
              command=[TwidDir.DownFire, TwidDir.LeftFire, TwidDir.UpFire, TwidDir.RightFire,
                       TwidDir.DownFire, TwidDir.LeftFire, TwidDir.UpFire]),
    ],
    [
        Twiddle("Repulsor", SpecialValues.Repulsor, shield_cost=1,
              command=[TwidDir.LeftFire, TwidDir.RightFire]),
    ],
    [
        Twiddle("Protron Field", SpecialValues.ProtronField, shield_cost="half",
              command=[TwidDir.Up, TwidDir.LeftFire, TwidDir.DownFire]),
    ],
    [
        Twiddle("Minefield", SpecialValues.MineSpray, armor_cost=4,
              command=[TwidDir.RightFire, TwidDir.DownFire, TwidDir.LeftFire, TwidDir.Up]),
    ],
    [
        Twiddle("Post-It Blast", SpecialValues.PostItBlast, armor_cost=5,
              command=[TwidDir.Left, TwidDir.DownFire, TwidDir.RightFire, TwidDir.UpFire]),
    ],
    [
        Twiddle("Hot Dog Blast", SpecialValues.HotDog, armor_cost=1,
              command=[TwidDir.Up, TwidDir.DownFire]),
    ],
    [
        # Pool all lightning shots together so they don't overwhelm the other choices
        Twiddle("Lightning Up", SpecialValues.LightningUp,
              command=[TwidDir.Neutral, TwidDir.UpFire]),
        Twiddle("Lightning Up+Left", SpecialValues.LightningUpLeft,
              command=[TwidDir.Up, TwidDir.LeftFire]),
        Twiddle("Lightning Up+Right", SpecialValues.LightningUpRight,
              command=[TwidDir.Up, TwidDir.RightFire]),
        Twiddle("Lightning Left", SpecialValues.LightningLeft,
              command=[TwidDir.Neutral, TwidDir.LeftFire]),
        Twiddle("Lightning Right", SpecialValues.LightningRight,
              command=[TwidDir.Neutral, TwidDir.RightFire])
    ],
]


def generate_twiddles(world: "TyrianWorld", chaos_mode: bool = False) -> list[Twiddle]:
    random_value = world.random.randrange(100)
    if   random_value < 10: max_twiddle_count = 1
    elif random_value < 50: max_twiddle_count = 2
    else:                   max_twiddle_count = 3

    if chaos_mode:
        raise NotImplementedError("Chaos mode Twiddles: NYI")
    else:
        # Choose up to three specific twiddle pools, and then choose a twiddle from each.
        twiddle_options = len(vanilla_twiddle_list)
        twiddle_indices = world.random.sample(range(twiddle_options), max_twiddle_count)
        return [world.random.choice(vanilla_twiddle_list[idx]) for idx in twiddle_indices]
