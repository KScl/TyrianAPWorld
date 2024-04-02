# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

import json
import logging
import math
import os
from typing import TextIO, Optional, List, Dict, Set, Callable, Any

from BaseClasses import Item, Location, Region
from BaseClasses import ItemClassification as IC
from BaseClasses import LocationProgressType as LP

from .Items import LocalItemData, LocalItem, Episode
from .Locations import LevelLocationData, LevelRegion
from .Logic import DamageTables, set_level_rules
from .Options import TyrianOptions
from .Twiddles import Twiddle, generate_twiddles

from ..AutoWorld import World, WebWorld

class TyrianItem(Item):
    game = "Tyrian"

class TyrianLocation(Location):
    game = "Tyrian"
    all_access_rules: List[Callable]

    shop_price: Optional[int] # None if not a shop, price in credits if it is

    def __init__(self, player: int, name: str, address: Optional[int], parent: Region):
        super().__init__(player, name, address, parent)
        self.shop_price = 0 if name.startswith("Shop - ") else None
        self.all_access_rules = []

class TyrianWorld(World):
    """
    Follow pilot Trent Hawkins in the year 20,031 as he flies through the galaxy to defend it from the evil 
    corporation, Microsol.
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
    aptyrian_net_version = 2

    # --------------------------------------------------------------------------------------------

    goal_episodes: Set[int] = set() # Require these episodes for goal (1, 2, 3, 4, 5)
    play_episodes: Set[int] = set() # Add levels from these episodes (1, 2, 3, 4, 5)
    default_start_level: str = "" # Level we start on, gets precollected automatically

    all_levels: List[str] = [] # List of all levels available in seed
    local_itempool: List[str] = [] # Item pool for just us. Forced progression items start with !

    single_special_weapon: Optional[str] = None # For output to spoiler log only
    twiddles: List[Twiddle] = []

    weapon_costs: Dict[str, int] = {} # Costs of each weapon's upgrades (see LocalItemData.default_upgrade_costs)
    total_money_needed: int = 0 # Sum total of shop prices and max upgrades, used to calculate filler items

    damage_tables: DamageTables # Used for rule generation
    all_boss_weaknesses: Dict[int, str] = {} # Required weapon to use for each boss

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
        region_data.set_random_shop_price(self, loc)

        region.locations.append(loc)
        return loc

    def create_event(self, name: str, region: Region) -> TyrianItem:
        loc = TyrianLocation(self.player, name[0:9], None, region)
        loc.place_locked_item(TyrianItem(name, IC.progression, None, self.player))

        region.locations.append(loc)
        return loc

    # ================================================================================================================
    # Item Pool Methods
    # ================================================================================================================

    def get_dict_contents_as_items(self, target_dict: Dict[str, LocalItem]) -> List[str]:
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

    def get_random_weapon(self) -> str:
        possible_choices = [item for item in self.local_itempool if item in LocalItemData.front_ports]
        return self.random.choice(possible_choices)

    def get_starting_weapon(self) -> str:
        if not self.options.random_starting_weapon:
            return "Pulse-Cannon"

        # TODO More logic here, based on logic difficulty
        possible_choices = [item for item in self.local_itempool if item in LocalItemData.front_ports]
        return self.random.choice(possible_choices)

    # ================================================================================================================
    # Slot Data / File Output
    # ================================================================================================================

    # Game settings, user choices the game needs to know about
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
            "ShowTwiddles": bool(self.options.show_twiddle_inputs),
            "APRadar": bool(self.options.archipelago_radar),
            "Christmas": bool(self.options.christmas_mode),
            "DeathLink": bool(self.options.deathlink),
        }

    # Tell the game what we start with
    def output_start_state(self) -> Dict[str, Any]:
        start_state = {}

        def increase_state(option: str):
            nonlocal start_state
            start_state[option] = start_state.get(option, 0) + 1

        def append_state(option: str, value: str):
            nonlocal start_state
            if option not in start_state:
                start_state[option] = []
            # May as well give the game the ID number it's already expecting if it saves 5+ bytes to do so
            start_state[option].append(self.item_name_to_id[value] - self.base_id)

        def add_credits(value: str):
            nonlocal start_state
            credit_count = int(name.removesuffix(" Credits"))
            start_state["Credits"] = start_state.get("Credits", 0) + credit_count

        if self.options.starting_money > 0:
            start_state["Credits"] = self.options.starting_money.value

        for item in self.multiworld.precollected_items[self.player]:
            if item.name in LocalItemData.levels:            append_state("Items", item.name)
            elif item.name in LocalItemData.front_ports:     append_state("Items", item.name)
            elif item.name in LocalItemData.rear_ports:      append_state("Items", item.name)
            elif item.name in LocalItemData.special_weapons: append_state("Items", item.name)
            elif item.name in LocalItemData.sidekicks:       append_state("Items", item.name)
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

    # Base cost of each weapon's upgrades
    def output_weapon_cost(self) -> Dict[int, int]:
        return {self.item_name_to_id[key] - self.base_id: value for (key, value) in self.weapon_costs.items()}

    # Twiddle inputs, costs, etc.
    def output_twiddles(self) -> List[Dict[str, Any]]:
        return [twiddle.to_json() for twiddle in self.twiddles]

    # Which locations are progression (used for multiworld slot data)
    def output_progression_data(self) -> List[int]:
        return [location.address - self.base_id
              for location in self.multiworld.get_locations(self.player)
              if location.item.advancement and not location.shop_price and location.address is not None]

    # Total number of locations available (used for multiworld slot data)
    def output_location_count(self) -> int:
        return len([loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None])

    # The contents of every single location (local games only)
    def output_all_locations(self) -> Dict[int, int]:
        assert self.multiworld.players == 1

        def get_location_item(location: Location) -> str:
            return f"{'!' if location.item.advancement else ''}{location.item.code - self.base_id}"

        return {location.address - self.base_id: get_location_item(location)
              for location in self.multiworld.get_locations(self.player)
              if location.address is not None}

    # Shop prices, possibly other relevant information
    def output_shop_data(self) -> Dict[int, int]:
        def correct_shop_price(location: Location) -> int:
            # If the shop has credits, and the cost is more than you'd gain, reduce the cost.
            # Don't do this in hidden mode, though, since the player shouldn't have any idea what each item is.
            if self.options.shop_mode != "hidden" and location.item.player == self.player \
                  and location.item.name.endswith(" Credits"):
                credit_amount = int(location.item.name.removesuffix(" Credits"))
                adjusted_shop_price = location.shop_price % credit_amount
                return adjusted_shop_price if adjusted_shop_price != 0 else credit_amount
            return location.shop_price

        return {location.address - self.base_id: correct_shop_price(location)
              for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None}

    # Boss weapon/weakness list (local and/or remote, if the option is enabled)
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

        def obfuscate_char(in_chr):
            nonlocal offset
            try:
                idx = input_chars.index(in_chr) + offset
                offset += (ord(in_chr) & 0xF) + 1
            except ValueError:
                idx = input_chars.index("?") + offset
                offset += (ord(in_chr) & 0xF) + 1
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

        if self.options.twiddles:
            slot_data["TwiddleData"] = self.obfuscate_object(self.output_twiddles())
        if self.options.boss_weaknesses:
            slot_data["BossWeaknesses"] = self.obfuscate_object(self.output_boss_weaknesses())

        if local_mode: # Local mode: Output all location contents
            slot_data["LocationData"] = self.obfuscate_object(self.output_all_locations())
        else: # Remote mode: Just output a list of location IDs that contain progression
            slot_data["ProgressionData"] = self.obfuscate_object(self.output_progression_data())
            slot_data["LocationMax"] = self.output_location_count()

        if self.options.shop_mode != "none":
            slot_data["ShopData"] = self.obfuscate_object(self.output_shop_data())

        return slot_data

    # ================================================================================================================
    # Main Generation Steps
    # ================================================================================================================

    def generate_early(self):
        if not self.options.enable_tyrian_2000_support:
            self.options.episode_5.value = 0
        else:
            LocalItemData.enable_tyrian_2000_items()

        self.goal_episodes.add(1) if self.options.episode_1 == 2 else None
        self.goal_episodes.add(2) if self.options.episode_2 == 2 else None
        self.goal_episodes.add(3) if self.options.episode_3 == 2 else None
        self.goal_episodes.add(4) if self.options.episode_4 == 2 else None
        self.goal_episodes.add(5) if self.options.episode_5 == 2 else None

        self.play_episodes.add(1) if self.options.episode_1 != 0 else None
        self.play_episodes.add(2) if self.options.episode_2 != 0 else None
        self.play_episodes.add(3) if self.options.episode_3 != 0 else None
        self.play_episodes.add(4) if self.options.episode_4 != 0 else None
        self.play_episodes.add(5) if self.options.episode_5 != 0 else None

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

        self.damage_tables = DamageTables(self.options.logic_difficulty)

        # May as well generate twiddles now, if the options are set.
        if self.options.twiddles:
            self.twiddles = generate_twiddles(self, self.options.twiddles == "chaos")

    def create_regions(self):
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
                for level in self.random.sample(self.all_levels, self.options.shop_item_count):
                    items_per_shop[level] = 1

            # More than enough items to go around
            else:
                # Silently correct too many items to just cap at the max
                total_item_count = min(self.options.shop_item_count, len(self.all_levels) * 5)

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
                    new_location = self.create_shop_location(shop_loc_name, shop_region, region_data)
                    self.total_money_needed += new_location.shop_price

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

    def create_items(self):
        # Level items are added into the pool in create_regions.
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.front_ports))
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.rear_ports))
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.sidekicks))
        self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.other_items))

        if self.options.specials == 2: # Specials as MultiWorld items
            self.local_itempool.extend(self.get_dict_contents_as_items(LocalItemData.special_weapons))

        def pop_from_pool(item_name) -> Optional[str]:
            if item_name in self.local_itempool: # Regular item
                self.local_itempool.remove(item_name)
                return item_name
            return None

        precollected_level_exists = False
        precollected_weapon_exists = False

        # ----------------------------------------------------------------------------------------

        # Based on progressive items and starting inventory, add generators to the pool.
        generator_pool = ["Gravitron Pulse-Wave",
                          "Advanced MicroFusion",
                          "Standard MicroFusion",
                          "Gencore Custom MR-12",
                          "Advanced MR-12"]
        if self.options.progressive_items:
            generator_pool = ["Progressive Generator"] * 5

        self.local_itempool.extend(generator_pool)

        # ----------------------------------------------------------------------------------------

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
            self.multiworld.push_precollected(self.create_item(start_level))

        if not precollected_weapon_exists:
            # Pick a starting weapon and pull it from the pool.
            start_weapon = pop_from_pool(self.get_starting_weapon())
            self.multiworld.push_precollected(self.create_item(start_weapon))

        if self.options.specials == 1: # Get a random special, no others
            self.single_special_weapon = self.random.choice(sorted(LocalItemData.special_weapons))
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
                self.all_boss_weaknesses[episode] = self.get_random_weapon()

                # Add data cubes to the pool, too. They're considered logically required.
                self.local_itempool.append(f"Data Cube (Episode {episode})")

        # ----------------------------------------------------------------------------------------

        # I had the idea of filling the world with "Dynamic Junk" that we would go back through in post_fill and
        # replace when we have knowledge of the contents of every shop (and more importantly, their costs).
        # But infuriatingly, post_fill is run before progression balancing, and more to the point, there's
        # (seemingly deliberately) no way to have anything affect the pool after progression balancing.

        # So instead, we pre-determine all shop prices (no accounting for what winds up there), and just fill
        # the item pool immediately based on that. It's still an over-estimate because we zero out the cost
        # of "X Credits" items if they land on a shop (they just become 'Free Money!'), but good enough.

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
        minimum_needed_item_count = math.ceil(self.total_money_needed / 50000)
        if rest_item_count < minimum_needed_item_count:
            tossable_items = [name for name in self.local_itempool if not name.startswith("!")
                  and LocalItemData.get(name).tossable]
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

    def set_rules(self):

        set_level_rules(self)

        # ==============================
        # === Automatic (base) rules ===
        # ==============================

        def create_level_unlock_rule(level_name: str):
            entrance = self.multiworld.get_entrance(f"Open {level_name}", self.player)
            entrance.access_rule = lambda state: state.has(level_name, self.player)

        for level in self.all_levels:
            create_level_unlock_rule(level)

        # ------------------------------

        def create_episode_complete_rule(event_name, location_name):
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

#   def post_fill(self):
#       from Utils import visualize_regions
#       visualize_regions(self.multiworld.get_region("Menu", self.player), "my_world.puml")

    def generate_output(self, output_directory: str):
        if self.multiworld.players != 1:
            return

        # For solo seeds, output a file that can be loaded to play the seed offline.
        local_play_filename = f"{self.multiworld.get_out_file_name_base(self.player)}.aptyrian"
        with open(os.path.join(output_directory, local_play_filename), 'w') as f:
            json.dump(self.get_slot_data(local_mode=True), f)

    def write_spoiler(self, spoiler_handle: TextIO):
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

    def fill_slot_data(self) -> dict:
        slot_data = self.get_slot_data()
        return slot_data
