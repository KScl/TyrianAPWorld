# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import List, Dict, NamedTuple, Set
from enum import IntEnum

from BaseClasses import ItemClassification as IC

class Episode(IntEnum):
    Escape = 1
    Treachery = 2
    MissionSuicide = 3
    AnEndToFate = 4
    HazudraFodder = 5

class LocalItem:
    local_id: int
    count: int
    tossable: bool
    item_class: IC

    def __init__(self, local_id: int, count: int = 0, item_class: IC = IC.filler, tossable: bool = False):
        self.local_id = local_id
        self.count = count
        self.item_class = item_class
        self.tossable = (item_class != IC.progression)

class LocalLevel(LocalItem):
    episode: Episode

    def __init__(self, local_id: int, episode: Episode):
        self.local_id = local_id
        self.count = 1
        self.item_class = IC.progression
        self.episode = episode
        self.tossable = False

class LocalWeapon(LocalItem):
    tags: List[str]

    def __init__(self, local_id: int, tags: List[str] = [], count: int = 1):
        self.local_id = local_id
        self.count = count
        self.tags = tags
        self.tossable = ("Untossable" not in tags)
        if "Progression" in tags: self.item_class = IC.progression
        elif "Useful" in tags:    self.item_class = IC.useful
        else:                     self.item_class = IC.filler

class UpgradeCost(NamedTuple):
    original: int
    balanced: int

# --------------------------------------------------------------------------------------------------------------------

class LocalItemData:
    levels: Dict[str, LocalLevel] = {
        "TYRIAN (Episode 1)":    LocalLevel(  0, Episode.Escape), # Starts unlocked
        "BUBBLES (Episode 1)":   LocalLevel(  1, Episode.Escape),
        "HOLES (Episode 1)":     LocalLevel(  2, Episode.Escape),
        "SOH JIN (Episode 1)":   LocalLevel(  3, Episode.Escape),
        "ASTEROID1 (Episode 1)": LocalLevel(  4, Episode.Escape),
        "ASTEROID2 (Episode 1)": LocalLevel(  5, Episode.Escape),
        "ASTEROID? (Episode 1)": LocalLevel(  6, Episode.Escape),
        "MINEMAZE (Episode 1)":  LocalLevel(  7, Episode.Escape),
        "WINDY (Episode 1)":     LocalLevel(  8, Episode.Escape),
        "SAVARA (Episode 1)":    LocalLevel(  9, Episode.Escape),
        "SAVARA II (Episode 1)": LocalLevel( 10, Episode.Escape), # Savara Hard
        "BONUS (Episode 1)":     LocalLevel( 11, Episode.Escape),
        "MINES (Episode 1)":     LocalLevel( 12, Episode.Escape),
        "DELIANI (Episode 1)":   LocalLevel( 13, Episode.Escape),
        "SAVARA V (Episode 1)":  LocalLevel( 14, Episode.Escape),
        "ASSASSIN (Episode 1)":  LocalLevel( 15, Episode.Escape), # Goal

        "TORM (Episode 2)":      LocalLevel(100, Episode.Treachery),
        "GYGES (Episode 2)":     LocalLevel(101, Episode.Treachery),
        "BONUS 1 (Episode 2)":   LocalLevel(102, Episode.Treachery),
        "ASTCITY (Episode 2)":   LocalLevel(103, Episode.Treachery),
        "BONUS 2 (Episode 2)":   LocalLevel(104, Episode.Treachery),
        "GEM WAR (Episode 2)":   LocalLevel(105, Episode.Treachery),
        "MARKERS (Episode 2)":   LocalLevel(106, Episode.Treachery),
        "MISTAKES (Episode 2)":  LocalLevel(107, Episode.Treachery),
        "SOH JIN (Episode 2)":   LocalLevel(108, Episode.Treachery),
        "BOTANY A (Episode 2)":  LocalLevel(109, Episode.Treachery),
        "BOTANY B (Episode 2)":  LocalLevel(110, Episode.Treachery),
        "GRYPHON (Episode 2)":   LocalLevel(111, Episode.Treachery), # Goal

        "GAUNTLET (Episode 3)":  LocalLevel(200, Episode.MissionSuicide),
        "IXMUCANE (Episode 3)":  LocalLevel(201, Episode.MissionSuicide),
        "BONUS (Episode 3)":     LocalLevel(202, Episode.MissionSuicide),
        "STARGATE (Episode 3)":  LocalLevel(203, Episode.MissionSuicide),
        "AST. CITY (Episode 3)": LocalLevel(204, Episode.MissionSuicide),
        "SAWBLADES (Episode 3)": LocalLevel(205, Episode.MissionSuicide),
        "CAMANIS (Episode 3)":   LocalLevel(206, Episode.MissionSuicide),
        "MACES (Episode 3)":     LocalLevel(207, Episode.MissionSuicide),
        "TYRIAN X (Episode 3)":  LocalLevel(208, Episode.MissionSuicide),
        "SAVARA Y (Episode 3)":  LocalLevel(209, Episode.MissionSuicide),
        "NEW DELI (Episode 3)":  LocalLevel(210, Episode.MissionSuicide),
        "FLEET (Episode 3)":     LocalLevel(211, Episode.MissionSuicide), # Goal

        "SURFACE (Episode 4)":   LocalLevel(300, Episode.AnEndToFate),
        "WINDY (Episode 4)":     LocalLevel(301, Episode.AnEndToFate),
        "LAVA RUN (Episode 4)":  LocalLevel(302, Episode.AnEndToFate),
        "CORE (Episode 4)":      LocalLevel(303, Episode.AnEndToFate),
        "LAVA EXIT (Episode 4)": LocalLevel(304, Episode.AnEndToFate),
        "DESERTRUN (Episode 4)": LocalLevel(305, Episode.AnEndToFate),
        "SIDE EXIT (Episode 4)": LocalLevel(306, Episode.AnEndToFate),
        "?TUNNEL? (Episode 4)":  LocalLevel(307, Episode.AnEndToFate),
        "ICE EXIT (Episode 4)":  LocalLevel(308, Episode.AnEndToFate),
        "ICESECRET (Episode 4)": LocalLevel(309, Episode.AnEndToFate),
        "HARVEST (Episode 4)":   LocalLevel(310, Episode.AnEndToFate),
        "UNDERDELI (Episode 4)": LocalLevel(311, Episode.AnEndToFate),
        "APPROACH (Episode 4)":  LocalLevel(312, Episode.AnEndToFate),
        "SAVARA IV (Episode 4)": LocalLevel(313, Episode.AnEndToFate),
        "DREAD-NOT (Episode 4)": LocalLevel(314, Episode.AnEndToFate),
        "EYESPY (Episode 4)":    LocalLevel(315, Episode.AnEndToFate),
        "BRAINIAC (Episode 4)":  LocalLevel(316, Episode.AnEndToFate),
        "NOSE DRIP (Episode 4)": LocalLevel(317, Episode.AnEndToFate), # Goal

        # ---------- TYRIAN 2000 LINE ----------
        "ASTEROIDS (Episode 5)": LocalLevel(400, Episode.HazudraFodder),
        "AST ROCK (Episode 5)":  LocalLevel(401, Episode.HazudraFodder),
        "MINERS (Episode 5)":    LocalLevel(402, Episode.HazudraFodder),
        "SAVARA (Episode 5)":    LocalLevel(403, Episode.HazudraFodder),
        "CORAL (Episode 5)":     LocalLevel(404, Episode.HazudraFodder),
        "STATION (Episode 5)":   LocalLevel(405, Episode.HazudraFodder),
        "FRUIT (Episode 5)":     LocalLevel(406, Episode.HazudraFodder), # Goal
    }

    # ----------------------------------------------------------------------------------------------------------------

    # All Front and Rear port weapons are progression, some specific specials are too
    # All other specials and sidekicks are useful at most
    front_ports: Dict[str, LocalWeapon] = {
        "Pulse-Cannon":                   LocalWeapon(500, tags=["Progression"]), # Default starting weapon
        "Multi-Cannon (Front)":           LocalWeapon(501, tags=["Progression"]),
        "Mega Cannon":                    LocalWeapon(502, tags=["Progression", "Untossable", "Pierces"]),
        "Laser":                          LocalWeapon(503, tags=["Progression"]),
        "Zica Laser":                     LocalWeapon(504, tags=["Progression"]),
        "Protron Z":                      LocalWeapon(505, tags=["Progression"]),
        "Vulcan Cannon (Front)":          LocalWeapon(506, tags=["Progression"]),
        "Lightning Cannon":               LocalWeapon(507, tags=["Progression"]),
        "Protron (Front)":                LocalWeapon(508, tags=["Progression"]),
        "Missile Launcher":               LocalWeapon(509, tags=["Progression"]),
        "Mega Pulse (Front)":             LocalWeapon(510, tags=["Progression"]),
        "Heavy Missile Launcher (Front)": LocalWeapon(511, tags=["Progression"]),
        "Banana Blast (Front)":           LocalWeapon(512, tags=["Progression"]),
        "HotDog (Front)":                 LocalWeapon(513, tags=["Progression"]),
        "Hyper Pulse":                    LocalWeapon(514, tags=["Progression"]),
        "Guided Bombs":                   LocalWeapon(515, tags=["Progression"]),
        "Shuruiken Field":                LocalWeapon(516, tags=["Progression"]),
        "Poison Bomb":                    LocalWeapon(517, tags=["Progression"]),
        "Protron Wave":                   LocalWeapon(518, tags=["Progression"]),
        "The Orange Juicer":              LocalWeapon(519, tags=["Progression"]),
        "NortShip Super Pulse":           LocalWeapon(520, tags=["Progression"]),
        "Atomic RailGun":                 LocalWeapon(521, tags=["Progression"]),
        "Widget Beam":                    LocalWeapon(522, tags=["Progression"]),
        "Sonic Impulse":                  LocalWeapon(523, tags=["Progression", "Pierces"]),
        "RetroBall":                      LocalWeapon(524, tags=["Progression"]),
        # ---------- TYRIAN 2000 LINE ----------
        "Needle Laser":                   LocalWeapon(525, count=0, tags=["Progression", "Pierces"]),
        "Pretzel Missile":                LocalWeapon(526, count=0, tags=["Progression"]),
        "Dragon Frost":                   LocalWeapon(527, count=0, tags=["Progression"]),
        "Dragon Flame":                   LocalWeapon(528, count=0, tags=["Progression"]),
    }

    rear_ports: Dict[str, LocalWeapon] = {
        "Starburst":                     LocalWeapon(600, tags=["Progression", "Sideways"]),
        "Multi-Cannon (Rear)":           LocalWeapon(601, tags=["Progression", "Sideways"]),
        "Sonic Wave":                    LocalWeapon(602, tags=["Progression", "Untossable", "Sideways"]),
        "Protron (Rear)":                LocalWeapon(603, tags=["Progression", "Sideways"]),
        "Wild Ball":                     LocalWeapon(604, tags=["Progression"]),
        "Vulcan Cannon (Rear)":          LocalWeapon(605, tags=["Progression"]),
        "Fireball":                      LocalWeapon(606, tags=["Progression"]),
        "Heavy Missile Launcher (Rear)": LocalWeapon(607, tags=["Progression"]),
        "Mega Pulse (Rear)":             LocalWeapon(608, tags=["Progression", "Sideways"]),
        "Banana Blast (Rear)":           LocalWeapon(609, tags=["Progression"]),
        "HotDog (Rear)":                 LocalWeapon(610, tags=["Progression"]),
        "Guided Micro Bombs":            LocalWeapon(611, tags=["Progression"]),
        "Heavy Guided Bombs":            LocalWeapon(612, tags=["Progression"]),
        "Scatter Wave":                  LocalWeapon(613, tags=["Progression", "Sideways"]),
        "NortShip Spreader":             LocalWeapon(614, tags=["Progression"]),
        "NortShip Spreader B":           LocalWeapon(615, tags=["Progression", "Pierces"]),
        # ---------- TYRIAN 2000 LINE ----------
        "People Pretzels":               LocalWeapon(616, count=0, tags=["Progression"]),
    }

    special_weapons: Dict[str, LocalWeapon] = {
        "Repulsor":          LocalWeapon(700, tags=["Progression", "Untossable"]), # Specifically required for checks
        "Pearl Wind":        LocalWeapon(701),
        "Soul of Zinglon":   LocalWeapon(702),
        "Attractor":         LocalWeapon(703),
        "Ice Beam":          LocalWeapon(704),
        "Flare":             LocalWeapon(705),
        "Blade Field":       LocalWeapon(706),
        "SandStorm":         LocalWeapon(707),
        "MineField":         LocalWeapon(708),
        "Dual Vulcan":       LocalWeapon(709),
        "Banana Bomb":       LocalWeapon(710),
        "Protron Dispersal": LocalWeapon(711),
        "Astral Zone":       LocalWeapon(712),
        "Xega Ball":         LocalWeapon(713),
        "MegaLaser Dual":    LocalWeapon(714),
        "Orange Shield":     LocalWeapon(715),
        "Pulse Blast":       LocalWeapon(716),
        "MegaLaser":         LocalWeapon(717),
        "Missile Pod":       LocalWeapon(718),
        "Invulnerability":   LocalWeapon(719, tags=["Progression", "Untossable"]), # Specifically required for checks
        "Lightning Zone":    LocalWeapon(720),
        "SDF Main Gun":      LocalWeapon(721, tags=["Useful"]),
        "Protron Field":     LocalWeapon(722),
        # ---------- TYRIAN 2000 LINE ----------
        "Super Pretzel":     LocalWeapon(723, count=0),
        "Dragon Lightning":  LocalWeapon(724, count=0),
    }

    sidekicks: Dict[str, LocalWeapon] = {
        "Single Shot Option":         LocalWeapon(800, count=2),
        "Dual Shot Option":           LocalWeapon(801, count=2),
        "Charge Cannon":              LocalWeapon(802, count=2),
        "Vulcan Shot Option":         LocalWeapon(803, count=2),
        "Wobbley":                    LocalWeapon(804, count=2),
        "MegaMissile":                LocalWeapon(805, count=2, tags=["Useful"]),
        "Atom Bombs":                 LocalWeapon(806, count=2, tags=["Useful"]),
        "Phoenix Device":             LocalWeapon(807, count=2, tags=["Useful"]),
        "Plasma Storm":               LocalWeapon(808, count=2, tags=["Useful"]),
        "Mini-Missile":               LocalWeapon(809, count=2),
        "Buster Rocket":              LocalWeapon(810, count=2),
        "Zica Supercharger":          LocalWeapon(811, count=2),
        "MicroBomb":                  LocalWeapon(812, count=2),
        "8-Way MicroBomb":            LocalWeapon(813, count=2, tags=["Useful"]),
        "Post-It Mine":               LocalWeapon(814, count=2),
        "Mint-O-Ship":                LocalWeapon(815, count=2),
        "Zica Flamethrower":          LocalWeapon(816, count=2),
        "Side Ship":                  LocalWeapon(817, count=2),
        "Companion Ship Warfly":      LocalWeapon(818, count=2),
        "MicroSol FrontBlaster":      LocalWeapon(819, count=1), # Right-only (limited to 1)
        "Companion Ship Gerund":      LocalWeapon(820, count=2),
        "BattleShip-Class Firebomb":  LocalWeapon(821, count=1, tags=["Useful"]), # Right-only (limited to 1)
        "Protron Cannon Indigo":      LocalWeapon(822, count=1), # Right-only (limited to 1)
        "Companion Ship Quicksilver": LocalWeapon(823, count=2),
        "Protron Cannon Tangerine":   LocalWeapon(824, count=1, tags=["Useful"]), # Right-only (limited to 1)
        "MicroSol FrontBlaster II":   LocalWeapon(825, count=1), # Right-only (limited to 1)
        "Beno Wallop Beam":           LocalWeapon(826, count=1), # Right-only (limited to 1)
        "Beno Protron System -B-":    LocalWeapon(827, count=1, tags=["Useful"]), # Right-only (limited to 1)
        "Tropical Cherry Companion":  LocalWeapon(828, count=2),
        "Satellite Marlo":            LocalWeapon(829, count=2),
        # ---------- TYRIAN 2000 LINE ----------
        "Bubble Gum-Gun":             LocalWeapon(830, count=0),
        "Flying Punch":               LocalWeapon(831, count=0, tags=["Useful"]),
    }

    # ----------------------------------------------------------------------------------------------------------------

    other_items: Dict[str, LocalItem] = {
        "Advanced MR-12":        LocalItem(900, item_class=IC.progression),
        "Gencore Custom MR-12":  LocalItem(901, item_class=IC.progression),
        "Standard MicroFusion":  LocalItem(902, item_class=IC.progression),
        "Advanced MicroFusion":  LocalItem(903, item_class=IC.progression),
        "Gravitron Pulse-Wave":  LocalItem(904, item_class=IC.progression),
        "Progressive Generator": LocalItem(905, item_class=IC.progression),

        "Maximum Power Up":      LocalItem(906, count=10, item_class=IC.progression), # 1 -> 11
        "Armor Up":              LocalItem(907, count=9,  item_class=IC.progression), # 5 -> 14
        "Shield Up":             LocalItem(908, count=9,  item_class=IC.useful), # 5 -> 14
        "Solar Shields":         LocalItem(909, count=1,  item_class=IC.useful),

        "SuperBomb":             LocalItem(910, count=1), # More can be added in junk fill

        # All Credits items have their count set dynamically.
        "50 Credits":            LocalItem(980),
        "75 Credits":            LocalItem(981),
        "100 Credits":           LocalItem(982),
        "150 Credits":           LocalItem(983),
        "200 Credits":           LocalItem(984),
        "300 Credits":           LocalItem(985),
        "375 Credits":           LocalItem(986),
        "500 Credits":           LocalItem(987),
        "750 Credits":           LocalItem(988),
        "800 Credits":           LocalItem(989),
        "1000 Credits":          LocalItem(990),
        "2000 Credits":          LocalItem(991),
        "5000 Credits":          LocalItem(992),
        "7500 Credits":          LocalItem(993),
        "10000 Credits":         LocalItem(994),
        "20000 Credits":         LocalItem(995),
        "40000 Credits":         LocalItem(996),
        "75000 Credits":         LocalItem(997),
        "100000 Credits":        LocalItem(998),
        "1000000 Credits":       LocalItem(999), # Should only be seen in case of emergency
    }

    # ----------------------------------------------------------------------------------------------------------------

    @classmethod
    def enable_tyrian_2000_items(cls):
        cls.front_ports["Needle Laser"].count = 1
        cls.front_ports["Pretzel Missile"].count = 1
        cls.front_ports["Dragon Frost"].count = 1
        cls.front_ports["Dragon Flame"].count = 1
        cls.rear_ports["People Pretzels"].count = 1
        cls.special_weapons["Super Pretzel"].count = 1
        cls.special_weapons["Dragon Lightning"].count = 1
        cls.sidekicks["Bubble Gum-Gun"].count = 2
        cls.sidekicks["Flying Punch"].count = 2

    @classmethod
    def front_ports_by_tag(cls, tag: str) -> List[str]:
        return [name for (name, weapon) in cls.front_ports.items() if tag in weapon.tags and weapon.count > 0]

    @classmethod
    def rear_ports_by_tag(cls, tag: str) -> List[str]:
        return [name for (name, weapon) in cls.rear_ports.items() if tag in weapon.tags and weapon.count > 0]

    @classmethod
    def specials_by_tag(cls, tag: str) -> List[str]:
        return [name for (name, weapon) in cls.special_weapons.items() if tag in weapon.tags and weapon.count > 0]

    @classmethod
    def sidekicks_by_tag(cls, tag: str) -> List[str]:
        return [name for (name, weapon) in cls.sidekicks.items() if tag in weapon.tags and weapon.count > 0]

    @classmethod
    def all_by_tag(cls, tag: str) -> List[str]:
        all_weapons = []
        all_weapons.extend(cls.front_ports_by_tag(tag))
        all_weapons.extend(cls.rear_ports_by_tag(tag))
        all_weapons.extend(cls.specials_by_tag(tag))
        all_weapons.extend(cls.sidekicks_by_tag(tag))
        return all_weapons

    @classmethod
    def get_item_name_to_id(cls, base_id: int) -> Dict[str, int]:
        all_items = {}
        all_items.update({name: (base_id + item.local_id) for (name, item) in cls.levels.items()})
        all_items.update({name: (base_id + item.local_id) for (name, item) in cls.front_ports.items()})
        all_items.update({name: (base_id + item.local_id) for (name, item) in cls.rear_ports.items()})
        all_items.update({name: (base_id + item.local_id) for (name, item) in cls.special_weapons.items()})
        all_items.update({name: (base_id + item.local_id) for (name, item) in cls.sidekicks.items()})
        all_items.update({name: (base_id + item.local_id) for (name, item) in cls.other_items.items()})
        return all_items

    @classmethod
    def get_item_groups(cls) -> Dict[str, Set[str]]:
        return {
            "Levels": {name for name in cls.levels.keys()},
            "Front Weapons": {name for name in cls.front_ports.keys()},
            "Rear Weapons": {name for name in cls.rear_ports.keys()},
            "Specials": {name for name in cls.special_weapons.keys()},
            "Sidekicks": {name for name in cls.sidekicks.keys()},
            "Generators": {"Progressive Generator", "Advanced MR-12", "Gencore Custom MR-12", "Standard MicroFusion",
                  "Advanced MicroFusion", "Gravitron Pulse-Wave"},
            "Credits": {name for name in cls.other_items.keys() if name.endswith(" Credits")}
        }

    @classmethod
    def get(cls, name: str) -> LocalItem:
        if name in cls.levels:          return cls.levels[name]
        if name in cls.front_ports:     return cls.front_ports[name]
        if name in cls.rear_ports:      return cls.rear_ports[name]
        if name in cls.special_weapons: return cls.special_weapons[name]
        if name in cls.sidekicks:       return cls.sidekicks[name]
        if name in cls.other_items:     return cls.other_items[name]
        raise KeyError(f"Item {name} not found")

    # ================================================================================================================

    default_upgrade_costs: Dict[str, UpgradeCost] = {
        # To upgrade a weapon to a specific level, multiply the cost by:
        # (0x, 1x, 4x, 10x, 20x, 35x, 56x, 84x, 120x, 165x, 220x)

        # Original is the values from the original game.
        # Balanced places the Pulse-Cannon at 700, and everything balanced around compared usefulness to that.

        # Front ports
        "Pulse-Cannon":                   UpgradeCost(original=500,  balanced=700),
        "Multi-Cannon (Front)":           UpgradeCost(original=750,  balanced=600),
        "Mega Cannon":                    UpgradeCost(original=1000, balanced=1000),
        "Laser":                          UpgradeCost(original=900,  balanced=1800),
        "Zica Laser":                     UpgradeCost(original=1100, balanced=1750),
        "Protron Z":                      UpgradeCost(original=900,  balanced=1200),
        "Vulcan Cannon (Front)":          UpgradeCost(original=600,  balanced=500),
        "Lightning Cannon":               UpgradeCost(original=1000, balanced=1500),
        "Protron (Front)":                UpgradeCost(original=600,  balanced=900),
        "Missile Launcher":               UpgradeCost(original=850,  balanced=600),
        "Mega Pulse (Front)":             UpgradeCost(original=900,  balanced=1200),
        "Heavy Missile Launcher (Front)": UpgradeCost(original=1000, balanced=1000),
        "Banana Blast (Front)":           UpgradeCost(original=950,  balanced=1000),
        "HotDog (Front)":                 UpgradeCost(original=1100, balanced=950),
        "Hyper Pulse":                    UpgradeCost(original=1050, balanced=800),
        "Guided Bombs":                   UpgradeCost(original=800,  balanced=900),
        "Shuruiken Field":                UpgradeCost(original=850,  balanced=1400),
        "Poison Bomb":                    UpgradeCost(original=800,  balanced=1800),
        "Protron Wave":                   UpgradeCost(original=750,  balanced=750),
        "The Orange Juicer":              UpgradeCost(original=900,  balanced=1000),
        "NortShip Super Pulse":           UpgradeCost(original=1100, balanced=1250),
        "Atomic RailGun":                 UpgradeCost(original=1101, balanced=1750), # Yes, that's not a typo
        "Widget Beam":                    UpgradeCost(original=950,  balanced=500),
        "Sonic Impulse":                  UpgradeCost(original=1000, balanced=700), # Too fast to pierce well
        "RetroBall":                      UpgradeCost(original=1000, balanced=600),

        # Rear ports
        "Starburst":                     UpgradeCost(original=900,  balanced=800),
        "Multi-Cannon (Rear)":           UpgradeCost(original=750,  balanced=600),
        "Sonic Wave":                    UpgradeCost(original=950,  balanced=950),
        "Protron (Rear)":                UpgradeCost(original=650,  balanced=750),
        "Wild Ball":                     UpgradeCost(original=800,  balanced=600),
        "Vulcan Cannon (Rear)":          UpgradeCost(original=500,  balanced=500),
        "Fireball":                      UpgradeCost(original=1000, balanced=600),
        "Heavy Missile Launcher (Rear)": UpgradeCost(original=1000, balanced=1000),
        "Mega Pulse (Rear)":             UpgradeCost(original=900,  balanced=1200),
        "Banana Blast (Rear)":           UpgradeCost(original=1100, balanced=1400),
        "HotDog (Rear)":                 UpgradeCost(original=1100, balanced=900),
        "Guided Micro Bombs":            UpgradeCost(original=1100, balanced=800),
        "Heavy Guided Bombs":            UpgradeCost(original=1000, balanced=800),
        "Scatter Wave":                  UpgradeCost(original=900,  balanced=600),
        "NortShip Spreader":             UpgradeCost(original=1100, balanced=1500),
        "NortShip Spreader B":           UpgradeCost(original=1100, balanced=1250),

        # Tyrian 2000 stuff -- Original prices of 50 have been changed to 1000.
        "Needle Laser":    UpgradeCost(original=600,  balanced=700),
        "Pretzel Missile": UpgradeCost(original=1000, balanced=900),
        "Dragon Frost":    UpgradeCost(original=700,  balanced=900),
        "Dragon Flame":    UpgradeCost(original=1000, balanced=1100),

        "People Pretzels": UpgradeCost(original=1000, balanced=900),
    }
