# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

import json
import logging
import math
import os
from typing import TYPE_CHECKING, cast, TextIO, Optional, List, Dict, Mapping, Set, Tuple, Any

from BaseClasses import Item, Location, Region
from BaseClasses import ItemClassification as IC
from BaseClasses import LocationProgressType as LP

from .items import LocalItemData, LocalItem, Episode
from .locations import LevelLocationData, LevelRegion
from .logic import DamageTables, set_level_rules
from .options import TyrianOptions
from .twiddles import Twiddle, generate_twiddles

from worlds.AutoWorld import World, WebWorld

if TYPE_CHECKING:
    from BaseClasses import MultiWorld, CollectionState

class TyrianItem(Item):
    game = "Tyrian"

class TyrianLocation(Location):
    game = "Tyrian"

    shop_price: Optional[int] # None if not a shop, price in credits if it is

    def __init__(self, player: int, name: str, address: Optional[int], parent: Region):
        super().__init__(player, name, address, parent)
        self.shop_price = None

class TyrianWorld(World):
    """
    Tyrian is a PC SHMUP originally released in 1995, and then re-released as Tyrian 2000 in 1999. Follow space pilot
    Trent Hawkins in the year 20,031 as he flies through the galaxy to defend it from the evil corporation, Microsol.
    This randomizer supports both versions of the game.
    """
    game = "Tyrian"
    options_dataclass = TyrianOptions
    options: TyrianOptions

    base_id = 20031000
    item_name_to_id = LocalItemData.get_item_name_to_id(base_id)
    item_name_groups = LocalItemData.get_item_groups()
    location_name_to_id = LevelLocationData.get_location_name_to_id(base_id)
    location_name_groups = LevelLocationData.get_location_groups()

    location_descriptions = LevelLocationData.secret_descriptions

    # Raise this to force outdated clients to update.
    aptyrian_net_version = 3

    # --------------------------------------------------------------------------------------------

    goal_episodes: Set[int] # Require these episodes for goal (1, 2, 3, 4, 5)
    play_episodes: Set[int] # Add levels from these episodes (1, 2, 3, 4, 5)

    default_start_level: str # Level we start on, gets precollected automatically
    all_levels: List[str] # List of all levels available in seed
    local_itempool: List[str] # String-based item pool for us, becomes multiworld item pool after create_items

    single_special_weapon: Optional[str] # For output to spoiler log only
    twiddles: List[Twiddle] # Twiddle/SF Code inputs and their results.

    weapon_costs: Dict[str, int] # Costs of each weapon's upgrades (see LocalItemData.default_upgrade_costs)
    total_money_needed: int # Sum total of shop prices and max upgrades, used to calculate filler items

    all_boss_weaknesses: Dict[int, str] # Required weapon to use for each boss
    damage_tables: DamageTables # Used for rule generation

    # ================================================================================================================
    # Item / Location Helpers
    # ================================================================================================================

    def create_item(self, name: str) -> TyrianItem:
        pool_data = LocalItemData.get(name)
        return TyrianItem(name, pool_data.item_class, self.item_name_to_id[name], self.player)

    def create_level_location(self, name: str, region: Region) -> TyrianLocation:
        loc = TyrianLocation(self.player, name, self.location_name_to_id[name], region)

        region.locations.append(loc)
        return loc

    def create_shop_location(self, name: str, region: Region, region_data: LevelRegion) -> TyrianLocation:
        loc = TyrianLocation(self.player, name, self.location_name_to_id[name], region)

        loc.shop_price = 0 # Give a default int value for shops
        region_data.set_random_shop_price(self, loc)
        self.total_money_needed += loc.shop_price

        region.locations.append(loc)
        return loc

    def create_event(self, name: str, region: Region) -> TyrianLocation:
        loc = TyrianLocation(self.player, name[0:9], None, region)
        loc.place_locked_item(TyrianItem(name, IC.progression, None, self.player))

        region.locations.append(loc)
        return loc

    # ================================================================================================================
    # Item Pool Methods
    # ================================================================================================================

    def get_dict_contents_as_items(self, target_dict: Mapping[str, LocalItem]) -> List[str]:
        itemList = []

        for (name, item) in target_dict.items():
            if item.count > 0:
                itemList.extend([name] * item.count)

        return itemList

    def get_junk_items(self, total_checks: int, total_money: int) -> List[str]:
        total_money = int(total_money * (self.options.money_pool_scale / 100))

        valid_money_amounts = \
              [int(name.removesuffix(" Credits")) for name in LocalItemData.other_items if name.endswith(" Credits")]

        junk_list = []

        while total_checks > 1:
            # If we've overshot the target, fill all remaining slots with SuperBombs and leave.
            if total_money <= 0:
                junk_list.extend(["SuperBomb"] * total_checks)
                return junk_list

            # We want to allow a wide range of money values early, but then tighten up our focus as we start running
            # low on items remaining. This way we get a good variety of credit values while not straying too far
            # from the target value.
            average = total_money / total_checks
            avg_divisor = total_checks / 1.5 if total_checks > 3 else 2
            possible_choices = [i for i in valid_money_amounts if i > average / avg_divisor and i < average * 5]

            # If the low end of the scale is _really_ low, include a SuperBomb as a choice.
            if average / avg_divisor < 20:
                possible_choices.append(0)

            # In case our focus is a little _too_ tight and we don't actually have any money values close enough to
            # the average, just pick the next highest one above the average. That'll help ensure we're always over
            # the target value, and never under it.
            if len(possible_choices) == 0:
                item_choice = [i for i in valid_money_amounts if i >= average][0]
            else:
                item_choice = self.random.choice(possible_choices)

            total_money -= item_choice
            total_checks -= 1
            junk_list.append(f"{item_choice} Credits" if item_choice != 0 else "SuperBomb")

        # No point being random here. Just pick the first credit value that puts us over the target value.
        if total_checks == 1:
            item_choice = [i for i in valid_money_amounts if i >= total_money][0]
            junk_list.append(f"{item_choice} Credits")

        return junk_list;

    # ================================================================================================================
    # Option Parsing Helpers
    # ================================================================================================================

    def get_weapon_costs(self) -> Dict[str, int]:
        if self.options.base_weapon_cost.current_key == "original":
            return {key: value.original for (key, value) in LocalItemData.default_upgrade_costs.items()}
        elif self.options.base_weapon_cost.current_key == "balanced":
            return {key: value.balanced for (key, value) in LocalItemData.default_upgrade_costs.items()}
        elif self.options.base_weapon_cost.current_key == "randomized":
            return {key: self.random.randrange(400, 1801, 50)
                  for key in LocalItemData.default_upgrade_costs.keys()}
        else:
            return {key: int(self.options.base_weapon_cost.current_key)
                  for key in LocalItemData.default_upgrade_costs.keys()}

    def get_boss_weapon_name(self) -> str:
        # Can this weapon be required to defeat a boss on a given difficulty
        weapon_can_appear: Dict[str, Tuple[bool, bool, bool, bool]] = {
            "Pulse-Cannon":                   (True,  True,  True,  True,  True),
            "Multi-Cannon (Front)":           (False, False, False, True,  True),
            "Mega Cannon":                    (True,  True,  True,  True,  True),
            "Laser":                          (True,  True,  True,  True,  True),
            "Zica Laser":                     (True,  True,  True,  True,  True),
            "Protron Z":                      (True,  True,  True,  True,  True),
            "Vulcan Cannon (Front)":          (True,  True,  True,  True,  True),
            "Lightning Cannon":               (True,  True,  True,  True,  True),
            "Protron (Front)":                (True,  True,  True,  True,  True),
            "Missile Launcher":               (False, False, True,  True,  True),
            "Mega Pulse (Front)":             (True,  True,  True,  True,  True),
            "Heavy Missile Launcher (Front)": (True,  True,  True,  True,  True),
            "Banana Blast (Front)":           (True,  True,  True,  True,  True),
            "HotDog (Front)":                 (True,  True,  True,  True,  True),
            "Hyper Pulse":                    (True,  True,  True,  True,  True),
            "Guided Bombs":                   (False, True,  True,  True,  True),
            "Shuriken Field":                 (True,  True,  True,  True,  True),
            "Poison Bomb":                    (True,  True,  True,  True,  True),
            "Protron Wave":                   (False, False, False, True,  True),
            "The Orange Juicer":              (False, False, True,  True,  True),
            "NortShip Super Pulse":           (False, True,  True,  True,  True),
            "Atomic RailGun":                 (True,  True,  True,  True,  True),
            "Widget Beam":                    (False, False, False, True,  True),
            "Sonic Impulse":                  (False, True,  True,  True,  True),
            "RetroBall":                      (False, False, False, True,  True),
            "Needle Laser":                   (True,  True,  True,  True,  True),
            "Pretzel Missile":                (True,  True,  True,  True,  True),
            "Dragon Frost":                   (True,  True,  True,  True,  True),
            "Dragon Flame":                   (True,  True,  True,  True,  True),
        }

        # Note that this deliberately excludes weapons you start with.
        possible_choices = [item for item in self.local_itempool if item in weapon_can_appear
              and weapon_can_appear[item][self.options.logic_difficulty.value - 1] == True]

        # List is empty: Okay, sure, this can happen if we start with every weapon.
        # Retry, and only exclude weapons that are explicitly removed from the seed.
        if len(possible_choices) == 0:
            possible_choices = [item for item in weapon_can_appear
                  if item not in self.options.remove_from_item_pool.keys()
                  and weapon_can_appear[item][self.options.logic_difficulty.value - 1] == True]

        # List is STILL empty: Fine, you're getting something at random regardless of normal requirements
        if len(possible_choices) == 0:
            possible_choices = [item for item in weapon_can_appear
                  if item not in self.options.remove_from_item_pool.keys()]

        return self.random.choice(possible_choices)

    def get_starting_weapon_name(self) -> str:
        if not self.options.random_starting_weapon:
            return "Pulse-Cannon"

        # Per difficulty relative weight of receiving each weapon
        weapon_weights: Dict[str, Tuple[int, int, int, int]] = {
            "Pulse-Cannon":                   (1, 3, 2, 1, 1),
            "Multi-Cannon (Front)":           (0, 1, 1, 1, 1), # Low damage
            "Mega Cannon":                    (1, 3, 2, 1, 1),
            "Laser":                          (1, 3, 2, 1, 1),
            "Zica Laser":                     (1, 3, 2, 1, 1),
            "Protron Z":                      (1, 3, 2, 1, 1),
            "Vulcan Cannon (Front)":          (1, 3, 2, 1, 1),
            "Lightning Cannon":               (1, 3, 2, 1, 1),
            "Protron (Front)":                (1, 3, 2, 1, 1),
            "Missile Launcher":               (0, 1, 1, 1, 1), # Low damage
            "Mega Pulse (Front)":             (1, 3, 2, 1, 1),
            "Heavy Missile Launcher (Front)": (1, 3, 2, 1, 1),
            "Banana Blast (Front)":           (1, 3, 2, 1, 1),
            "HotDog (Front)":                 (1, 3, 2, 1, 1),
            "Hyper Pulse":                    (1, 3, 2, 1, 1),
            "Guided Bombs":                   (1, 3, 2, 1, 1),
            "Shuriken Field":                 (0, 0, 2, 1, 1), # High energy cost
            "Poison Bomb":                    (0, 0, 2, 1, 1), # High energy cost
            "Protron Wave":                   (0, 1, 1, 1, 1), # Low damage
            "The Orange Juicer":              (0, 0, 0, 1, 1), # Lv.1 is sideways only
            "NortShip Super Pulse":           (0, 0, 2, 1, 1), # High energy cost
            "Atomic RailGun":                 (0, 0, 2, 1, 1), # High energy cost
            "Widget Beam":                    (0, 1, 1, 1, 1), # Low damage
            "Sonic Impulse":                  (1, 3, 2, 1, 1),
            "RetroBall":                      (0, 1, 1, 1, 1), # Low damage
            "Needle Laser":                   (1, 3, 2, 1, 1),
            "Pretzel Missile":                (1, 3, 2, 1, 1),
            "Dragon Frost":                   (1, 3, 2, 1, 1),
            "Dragon Flame":                   (1, 3, 2, 1, 1),
        }

        possible_choices: List[str] = []
        for (weapon, weight_list) in weapon_weights.items():
            if weapon in self.local_itempool:
                possible_choices.extend([weapon] * weight_list[self.options.logic_difficulty.value - 1])

        # List is empty: What did they do, remove everything that was weighted positively?
        # Pick totally randomly among everything available in the seed
        if len(possible_choices) == 0:
            possible_choices = [item for item in self.local_itempool if item in LocalItemData.front_ports]

        return self.random.choice(possible_choices)

    def get_filler_item_name(self) -> str:
        filler_items = ["50 Credits",  "75 Credits",  "100 Credits", "150 Credits",
                        "200 Credits", "300 Credits", "375 Credits", "500 Credits"]
        return self.random.choice(filler_items)

    # ================================================================================================================
    # Slot Data / File Output
    # ================================================================================================================

    # ---------- Settings -----------------------------------------------------
    # Game settings, user choices the game needs to know about
    # Present: Always.
    def output_settings(self) -> Dict[str, Any]:
        return {
            "RequireT2K": bool(self.options.enable_tyrian_2000_support),
            "Episodes": sum(1 << (i - 1) for i in self.play_episodes),
            "Goal": sum(1 << (i - 1) for i in self.goal_episodes),
            "Difficulty": int(self.options.difficulty),

            "ShopMenu": int(self.options.shop_mode),
            "SpecialMenu": (self.options.specials == 2),
            "HardContact": bool(self.options.contact_bypasses_shields),
            "ExcessArmor": bool(self.options.allow_excess_armor),
            "GameSpeed": int(self.options.force_game_speed),
            "ShowTwiddles": bool(self.options.show_twiddle_inputs),
            "APRadar": bool(self.options.archipelago_radar),
            "Christmas": bool(self.options.christmas_mode),
            "DeathLink": bool(self.options.death_link),
        }

    # ---------- StartState (obfuscated) --------------------------------------
    # Tell the game what we start with.
    # Present: Always. (Optional in theory, but in practice there will always at least be the starting level.)
    def output_start_state(self) -> Dict[str, Any]:
        start_state: Dict[str, Any] = {}

        def increase_state(option: str) -> None:
            nonlocal start_state
            start_state[option] = start_state.get(option, 0) + 1

        def append_state(option: str, value: str) -> None:
            nonlocal start_state
            if option not in start_state:
                start_state[option] = []
            # May as well give the game the ID number it's already expecting if it saves 5+ bytes to do so
            start_state[option].append(self.item_name_to_id[value] - self.base_id)

        def add_credits(value: str) -> None:
            nonlocal start_state
            credit_count = int(value.removesuffix(" Credits"))
            start_state["Credits"] = start_state.get("Credits", 0) + credit_count

        if self.options.starting_money > 0:
            start_state["Credits"] = self.options.starting_money.value

        for item in self.multiworld.precollected_items[self.player]:
            if item.name in LocalItemData.levels:            append_state("Items", item.name)
            elif item.name in LocalItemData.front_ports:     append_state("Items", item.name)
            elif item.name in LocalItemData.rear_ports:      append_state("Items", item.name)
            elif item.name in LocalItemData.special_weapons: append_state("Items", item.name)
            elif item.name in LocalItemData.sidekicks:       append_state("Items", item.name)
            elif item.name.startswith("Data Cube "):         append_state("Items", item.name)
            elif item.name == "Armor Up":                    increase_state("Armor")
            elif item.name == "Maximum Power Up":            increase_state("Power")
            elif item.name == "Shield Up":                   increase_state("Shield")
            elif item.name == "Progressive Generator":       increase_state("Generator")
            elif item.name == "Advanced MR-12":              start_state["Generator"] = 1
            elif item.name == "Gencore Custom MR-12":        start_state["Generator"] = 2
            elif item.name == "Standard MicroFusion":        start_state["Generator"] = 3
            elif item.name == "Advanced MicroFusion":        start_state["Generator"] = 4
            elif item.name == "Gravitron Pulse-Wave":        start_state["Generator"] = 5
            elif item.name == "Solar Shields":               start_state["SolarShield"] = True
            elif item.name == "SuperBomb":                   pass # Only useful if obtained in level, ignore
            elif item.name.endswith(" Credits"):             add_credits(item.name)
            else:
                raise Exception(f"Unknown item '{item.name}' in precollected items")

        return start_state

    # ---------- WeaponCost (obfuscated) --------------------------------------
    # Base cost of each weapon's upgrades
    # Present: Always.
    def output_weapon_cost(self) -> Dict[int, int]:
        return {self.item_name_to_id[key] - self.base_id: value for (key, value) in self.weapon_costs.items()}

    # ---------- TwiddleData (obfuscated) -------------------------------------
    # Twiddle inputs, costs, etc.
    # Present: If the option "Twiddles" is not set to "off".
    def output_twiddles(self) -> List[Dict[str, Any]]:
        return [twiddle.to_json() for twiddle in self.twiddles]

    # ---------- ProgressionData (obfuscated) ---------------------------------
    # Which locations contain progression items for any player.
    # Present: Only in slot_data (remote games).
    def output_progression_data(self) -> List[int]:
        return [location.address - self.base_id for location in self.multiworld.get_locations(self.player)
              if location.address is not None and location.item is not None
              and getattr(location, "shop_price", None) is None # Ignore shop items (they're scouted in game)
              and location.item.advancement]

    # ---------- LocationMax --------------------------------------------------
    # Total number of locations available.
    # Present: Only in slot_data (remote games).
    def output_location_count(self) -> int:
        return len([loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None])

    # ---------- LocationData -------------------------------------------------
    # The contents of every single location present in the player's game. Single player only.
    # Present: Only in local/offline .aptyrian files.
    def output_all_locations(self) -> Dict[int, str]:
        assert self.multiworld.players == 1

        def get_location_item(location: Location) -> str:
            assert location.item is not None and location.item.code is not None
            return f"{'!' if location.item.advancement else ''}{location.item.code - self.base_id}"

        return {location.address - self.base_id: get_location_item(location)
              for location in self.multiworld.get_locations(self.player)
              if location.address is not None and location.item is not None}

    # ---------- ShopData (obfuscated) ----------------------------------------
    # The price of every shop present in the player's world.
    # Present: If the option "Shop Mode" is not set to "none".
    def output_shop_data(self) -> Dict[int, int]:
        def correct_shop_price(location: TyrianLocation) -> int:
            assert location.shop_price is not None # Tautological

            # If the shop has credits, and the cost is more than you'd gain, reduce the cost.
            # Don't do this in hidden mode, though, since the player shouldn't have any idea what each item is.
            if self.options.shop_mode != "hidden" and location.item is not None \
                  and location.item.player == self.player and location.item.name.endswith(" Credits"):
                credit_amount = int(location.item.name.removesuffix(" Credits"))
                adjusted_shop_price = location.shop_price % credit_amount
                return adjusted_shop_price if adjusted_shop_price != 0 else credit_amount
            return location.shop_price

        return {location.address - self.base_id: correct_shop_price(cast(TyrianLocation, location))
              for location in self.multiworld.get_locations(self.player)
              if location.address is not None # Ignore events
              and getattr(location, "shop_price", None) is not None}

    # ---------- BossWeaknesses (obfuscated) ----------------------------------
    # Weapons required to defeat bosses for each goal episode.
    # Present: If the option "Boss Weaknesses" is "on".
    def output_boss_weaknesses(self) -> Dict[int, int]:
        return {episode: self.item_name_to_id[weapon_name] - self.base_id
              for (episode, weapon_name) in self.all_boss_weaknesses.items()}

    # --------------------------------------------------------------------------------------------

    def obfuscate_object(self, input_obj: Any) -> str:
        # Every character the small font can display.
        input_chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ!?.,;:'\"abcdefghijklmnopqrstuvwxyz#$%*(){}[]1234567890/|\\-+="
        # Three characters are replaced by obfuscation: Single quotes, double quotes, and backslashes.
        # They are replaced by left and right brackets, and a tilde.
        obfus_chars = "0GTi29}#{K+d O1VYr]en:zP~yAI5(,ZL/)|?.sb4l<MFU3tD6$>wp[f*q%C=o8Emgj;xuXakhW!SNHc-Q7RBJv"
        # The sole point of this is to be relatively fast and simple to encode and decode, while keeping information
        # from being visible easily from just looking at the JSON file.
        offset = 54

        input_str = json.dumps(input_obj, separators=(",", ":"))

        def obfuscate_char(in_chr: str) -> str:
            nonlocal offset
            try:
                idx = input_chars.index(in_chr) + offset
                offset += (ord(in_chr) & 0xF) + 1
            except ValueError:
                idx = input_chars.index("?") + offset
                offset += (ord("?") & 0xF) + 1
            finally:
                if idx >= 87:
                    idx -= 87
                if offset >= 87:
                    offset -= 87
            return obfus_chars[idx]

        return "".join(obfuscate_char(i) for i in input_str)

    # --------------------------------------------------------------------------------------------

    def get_slot_data(self, local_mode: bool = False) -> Dict[str, Any]:
        # local_mode: If true, return a JSON file meant to be downloaded, for offline play
        slot_data = {
            "Seed": self.multiworld.seed_name,
            "NetVersion": self.aptyrian_net_version,
            "Settings": self.output_settings(),
            "StartState": self.obfuscate_object(self.output_start_state()),
            "WeaponCost": self.obfuscate_object(self.output_weapon_cost()),
        }

        if local_mode: # Local mode: Output all location contents
            slot_data["LocationData"] = self.obfuscate_object(self.output_all_locations())
        else: # Remote mode: Just output a list of location IDs that contain progression
            slot_data["ProgressionData"] = self.obfuscate_object(self.output_progression_data())
            slot_data["LocationMax"] = self.output_location_count()

        if self.options.twiddles:
            slot_data["TwiddleData"] = self.obfuscate_object(self.output_twiddles())
        if self.options.boss_weaknesses:
            slot_data["BossWeaknesses"] = self.obfuscate_object(self.output_boss_weaknesses())
        if self.options.shop_mode != "none":
            slot_data["ShopData"] = self.obfuscate_object(self.output_shop_data())

        return slot_data

    # ================================================================================================================
    # Main Generation Steps
    # ================================================================================================================

    @classmethod
    def stage_assert_generate(cls, multiworld: "MultiWorld") -> None:
        # Import code that affects other worlds; must happen after all worlds are loaded
        # See crossgame/__init__.py for more info
        from .crossgame import alttp

    def generate_early(self) -> None:
        if not self.options.enable_tyrian_2000_support:
            self.options.episode_5.value = 0

        self.goal_episodes = set()
        self.goal_episodes.add(1) if self.options.episode_1 == 2 else None
        self.goal_episodes.add(2) if self.options.episode_2 == 2 else None
        self.goal_episodes.add(3) if self.options.episode_3 == 2 else None
        self.goal_episodes.add(4) if self.options.episode_4 == 2 else None
        self.goal_episodes.add(5) if self.options.episode_5 == 2 else None

        self.play_episodes = set()
        self.play_episodes.add(1) if self.options.episode_1 != 0 else None
        self.play_episodes.add(2) if self.options.episode_2 != 0 else None
        self.play_episodes.add(3) if self.options.episode_3 != 0 else None
        self.play_episodes.add(4) if self.options.episode_4 != 0 else None
        self.play_episodes.add(5) if self.options.episode_5 != 0 else None

        # Beta: Warn on generating seeds with incomplete logic
        def warn_incomplete_logic(episode_name: str) -> None:
            logging.warning(f"{self.multiworld.get_player_name(self.player)}: "
                            f"Logic for {episode_name} is not yet complete. "
                            f"There will probably be issues, and the seed may be impossible as a result.")

        if 3 in self.play_episodes: warn_incomplete_logic("Episode 3 (Mission: Suicide)")
        if 4 in self.play_episodes: warn_incomplete_logic("Episode 4 (An End to Fate)")
        if 5 in self.play_episodes: warn_incomplete_logic("Episode 5 (Hazudra Fodder)")

        # Default to at least playing episode 1
        if len(self.play_episodes) == 0:
            logging.warning(f"No episodes were enabled in {self.multiworld.get_player_name(self.player)}'s "
                            f"Tyrian world. Defaulting to Episode 1.")
            self.play_episodes = {1}
            self.goal_episodes = {1}

        # If no goals, make all selected episodes goals by default
        if len(self.goal_episodes) == 0:
            logging.warning(f"No episodes were marked as goals in {self.multiworld.get_player_name(self.player)}'s "
                            f"Tyrian world. Defaulting to all playable pisodes.")
            self.goal_episodes = self.play_episodes

        if 1 in self.play_episodes:   self.default_start_level = "TYRIAN (Episode 1)"
        elif 2 in self.play_episodes: self.default_start_level = "TORM (Episode 2)"
        elif 3 in self.play_episodes: self.default_start_level = "GAUNTLET (Episode 3)"
        elif 4 in self.play_episodes: self.default_start_level = "SURFACE (Episode 4)"
        else:                         self.default_start_level = "ASTEROIDS (Episode 5)"

        self.weapon_costs = self.get_weapon_costs()
        self.total_money_needed = max(self.weapon_costs.values()) * 220

        self.damage_tables = DamageTables(self.options.logic_difficulty.value)

        # May as well generate twiddles now, if the options are set.
        if self.options.twiddles:
            self.twiddles = generate_twiddles(self, self.options.twiddles == "chaos")
        else:
            self.twiddles = []

        self.single_special_weapon = None
        self.all_levels = []
        self.local_itempool = []
        self.all_boss_weaknesses = {}

    def create_regions(self) -> None:
        menu_region = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu_region)

        main_hub_region = Region("Play Next Level", self.player, self.multiworld)
        self.multiworld.regions.append(main_hub_region)
        menu_region.connect(main_hub_region)

        # ==============
        # === Levels ===
        # ==============

        for (name, region_info) in LevelLocationData.level_regions.items():
            if region_info.episode not in self.play_episodes:
                continue

            self.all_levels.append(name)
            self.local_itempool.append(name)

            # Create the region for the level and connect it to the hub
            level_region = Region(name, self.player, self.multiworld)
            main_hub_region.connect(level_region, f"Open {name}")
            self.multiworld.regions.append(level_region)

            # Create the shop region immediately, and connect it to the level (treat completion as an entrance)
            # We don't particularly care if shops are even enabled, and we'll fill in shop checks afterward
            shop_region = Region(f"Shop - {name}", self.player, self.multiworld)
            level_region.connect(shop_region, f"Can shop at {name}")
            self.multiworld.regions.append(shop_region)

            # Make all locations listed for this region
            for location_name in region_info.locations:
                self.create_level_location(location_name, level_region)

        # =============
        # === Shops ===
        # =============

        # If we have shops enabled, then let's figure out how to divvy up their locations!
        if self.options.shop_mode != "none":
            # One of the "always_x" choices, add each level shop exactly x times
            if self.options.shop_item_count <= -1:
                times_to_add = abs(self.options.shop_item_count)            
                items_per_shop = {name: times_to_add for name in self.all_levels}

            # Not enough items for one in every shop
            elif self.options.shop_item_count < len(self.all_levels):
                items_per_shop = {name: 0 for name in self.all_levels}
                for level in self.random.sample(self.all_levels, self.options.shop_item_count.value):
                    items_per_shop[level] = 1

            # More than enough items to go around
            else:
                # Silently correct too many items to just cap at the max
                total_item_count: int = min(self.options.shop_item_count.value, len(self.all_levels) * 5)

                # First guarantee every shop has at least one
                items_per_shop = {name: 1 for name in self.all_levels}
                total_item_count -= len(self.all_levels)

                # Then get a random sample of a list where every level is present four times
                # This gives us between 1 to 5 items in every level
                for level in self.random.sample(self.all_levels * 4, total_item_count):
                    items_per_shop[level] += 1

            # ------------------------------------------------------------------------------------

            for level in self.all_levels:
                # Just get the shop region we made earlier
                shop_region = self.multiworld.get_region(f"Shop - {level}", self.player)
                region_data = LevelLocationData.level_regions[level]

                for i in range(items_per_shop[level]):
                    shop_loc_name = f"Shop - {level} - Item {i + 1}"
                    self.create_shop_location(shop_loc_name, shop_region, region_data)

        # ==============
        # === Events ===
        # ==============

        all_events = []
        episode_num = 0
        for event_name in LevelLocationData.events.keys():
            episode_num += 1
            if episode_num not in self.goal_episodes:
                continue

            all_events.append(event_name)
            self.create_event(event_name, menu_region)

        # Victory condition
        self.multiworld.completion_condition[self.player] = lambda state: state.has_all(all_events, self.player)

    def create_items(self) -> None:

        def pop_from_pool(item_name: str) -> Optional[str]:
            if item_name in self.local_itempool: # Regular item
                self.local_itempool.remove(item_name)
                return item_name
            return None

        # ----------------------------------------------------------------------------------------
        # Add base items to the pool.

        LocalItemData.set_tyrian_2000_items(bool(self.options.enable_tyrian_2000_support))

        # Level items are added into the pool in create_regions.
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.front_ports))
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.rear_ports))
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.sidekicks))
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.other_items))

        if self.options.specials == "as_items":
            self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.special_weapons))

        if self.options.progressive_items:
            self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.progressive_items))
        else:
            self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.nonprogressive_items))

        # ----------------------------------------------------------------------------------------
        # Handle pre-collected items, remove requests, other options.

        precollected_level_exists = False
        precollected_weapon_exists = False

        # Remove precollected (starting inventory) items from the pool.
        for precollect in self.multiworld.precollected_items[self.player]:
            name = pop_from_pool(precollect.name)
            if name in LocalItemData.levels: # Allow starting level override (dangerous logic-wise, but whatever)
                precollected_level_exists = True
            elif name in LocalItemData.front_ports: # Allow default weapon override
                precollected_weapon_exists = True

        # Remove items we've been requested to remove from the pool.
        for (removed_item, remove_count) in self.options.remove_from_item_pool.items():
            if removed_item in LocalItemData.levels:
                raise Exception(f"Cannot remove levels from the item pool (tried to remove '{removed_item}')")
            for i in range(remove_count):
                pop_from_pool(removed_item)

        if not precollected_level_exists:
            # Precollect the default starting level and pop it from the item pool.
            start_level = pop_from_pool(self.default_start_level)
            assert start_level is not None # Tautological because of above condition (can't remove levels from pool)
            self.multiworld.push_precollected(self.create_item(start_level))

        if not precollected_weapon_exists:
            # Pick a starting weapon and pull it from the pool.
            start_weapon_name = self.get_starting_weapon_name()
            start_weapon = pop_from_pool(start_weapon_name)
            if start_weapon is not None: # Not actually tautological, this can happen if someone removes Pulse-Cannon
                self.multiworld.push_precollected(self.create_item(start_weapon))
            else:
                raise Exception(f"Starting weapon ({start_weapon_name}) not in pool")

        if self.options.specials == "on": # Get a random special, no others
            possible_specials = self.get_dict_contents_as_items(LocalItemData.special_weapons)
            self.single_special_weapon = self.random.choice(possible_specials)
            self.multiworld.push_precollected(self.create_item(self.single_special_weapon))

        # If requested, pull max power upgrades from the pool and give them to the player.
        for i in range(1, self.options.starting_max_power):
            max_power_item = pop_from_pool("Maximum Power Up")
            if max_power_item is not None:
                self.multiworld.push_precollected(self.create_item(max_power_item))

        # ----------------------------------------------------------------------------------------
        # Set boss weaknesses based on weapons that are in the pool and haven't been removed.

        if self.options.boss_weaknesses:
            for episode in self.goal_episodes:
                self.all_boss_weaknesses[episode] = self.get_boss_weapon_name()

                # Add data cubes to the pool, too. They're considered logically required.
                self.local_itempool.append(f"Data Cube (Episode {episode})")

        # ----------------------------------------------------------------------------------------
        # Automatically fill the pool with junk Credits items, enough to reach total_money_needed.

        # Subtract what we start with.
        self.total_money_needed -= self.options.starting_money.value

        # Size of itempool versus number of locations. May be negative (!), will be fixed shortly if it is.
        rest_item_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(self.local_itempool)

        # Don't spam the seed with all SuperBombs jfc
        if self.total_money_needed <= 400 * rest_item_count:
            self.total_money_needed = 400 * rest_item_count

        # We want to at least have SOME variety of credit items in the pool regardless of settings.
        # We also don't want to leave ourselves with a situation where, say, we can only place one junk item
        # so it MUST be 1,000,000 credits.

        # So, if rest_item_count doesn't allow for us to stay under an average of 50,000 credits per junk item,
        # (or, hell, if rest_item_count is negative in the first place), we'll toss stuff from the pool to make space.
        def item_is_tossable(name: str) -> bool:
            if name in self.all_boss_weaknesses.values():
                return False # Mandated by boss weaknesses, can't toss
            return LocalItemData.get(name).tossable

        minimum_needed_item_count = math.ceil(self.total_money_needed / 50000)
        if rest_item_count < minimum_needed_item_count:
            tossable_items = [name for name in self.local_itempool if item_is_tossable(name)]
            need_to_toss = minimum_needed_item_count - rest_item_count

            if need_to_toss > len(tossable_items):
                # ... Well, shit. Just toss everything we can, and hopefully it'll work out.
                need_to_toss = len(tossable_items)

            tossed = [pop_from_pool(i) for i in self.random.sample(tossable_items, need_to_toss)]
            logging.warning(f"Trimming {need_to_toss} item{'' if need_to_toss == 1 else 's'} "
                            f"from {self.multiworld.get_player_name(self.player)}'s Tyrian world.")

            rest_item_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(self.local_itempool)


        self.local_itempool.extend(self.get_junk_items(rest_item_count, self.total_money_needed))

        # ----------------------------------------------------------------------------------------

        # We're finally done, dump everything we've got into the itempool
        self.multiworld.itempool.extend(self.create_item(item) for item in self.local_itempool)

    def set_rules(self) -> None:
        # Pass off rule generation to logic.py
        set_level_rules(self)

        # ==============================
        # === Automatic (base) rules ===
        # ==============================

        def create_level_unlock_rule(level_name: str) -> None:
            entrance = self.multiworld.get_entrance(f"Open {level_name}", self.player)
            entrance.access_rule = lambda state: state.has(level_name, self.player)

        for level in self.all_levels:
            create_level_unlock_rule(level)

        # ------------------------------

        def create_episode_complete_rule(event_name: str, location_name: str) -> None:
            event = self.multiworld.find_item(event_name, self.player)
            event.access_rule = lambda state: state.can_reach(location_name, "Location", self.player)

        for (event_name, level_name) in LevelLocationData.events.items():
            region_data = LevelLocationData.level_regions[level_name]
            if (region_data.episode not in self.goal_episodes):
                continue

            create_episode_complete_rule(event_name, region_data.locations[-1])

            # If only one episode is goal, exclude anything in the shop behind the goal level.
            if len(self.goal_episodes) == 1:
                shop_locations = [loc for loc in self.multiworld.get_locations(self.player)
                      if loc.name.startswith(f"Shop - {level_name} - ")]

                for location in shop_locations:
                    location.progress_type = LP.EXCLUDED

    def generate_output(self, output_directory: str) -> None:
        if self.multiworld.players != 1:
            return

        # For solo seeds, output a file that can be loaded to play the seed offline.
        local_play_filename = f"{self.multiworld.get_out_file_name_base(self.player)}.aptyrian"
        with open(os.path.join(output_directory, local_play_filename), "w") as f:
            json.dump(self.get_slot_data(local_mode=True), f)

    def write_spoiler(self, spoiler_handle: TextIO) -> None:
        precollected_names = [item.name for item in self.multiworld.precollected_items[self.player]]
        spoiler_handle.write(f"\n\nLevel locations ({self.multiworld.player_name[self.player]}):\n\n")
        for level in self.all_levels:
            if level in precollected_names:
                spoiler_handle.write(f"{level}: Start\n")               
            else:
                level_item_location = self.multiworld.find_item(level, self.player)
                spoiler_handle.write(f"{level}: {level_item_location.name}\n")

        spoiler_handle.write(f"\n\nSpecial Weapon ({self.multiworld.player_name[self.player]}):\n")
        spoiler_handle.write(f"{self.single_special_weapon}\n")

        spoiler_handle.write(f"\n\nTwiddles ({self.multiworld.player_name[self.player]}):\n")
        if len(self.twiddles) == 0:
            spoiler_handle.write("None\n")
        else:
            for twiddle in self.twiddles:
                spoiler_handle.write(twiddle.spoiler_str())

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.get_slot_data(local_mode=False)
