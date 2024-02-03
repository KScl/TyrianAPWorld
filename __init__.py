# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

import json
import logging
import math
import os
from typing import TextIO, Optional, List, Dict, Set, Any

from BaseClasses import Item, Location, Region
from BaseClasses import ItemClassification as IC
from BaseClasses import LocationProgressType as LP

from .Items import LocalItemData, LocalItem
from .Locations import LevelLocationData, LevelRegion
from .Logic import RequirementList, TyrianLogic
from .Options import TyrianOptions

from ..AutoWorld import World, WebWorld

class TyrianItem(Item):
    game = "Tyrian"

class TyrianLocation(Location):
    game = "Tyrian"

    requirement_list: Optional[RequirementList]
    shop_price: Optional[int] # None if not a shop, price in credits if it is

    def __init__(self, player: int, name: str, address: Optional[int], parent: Region,
          requirement_list: Optional[RequirementList] = None):
        super().__init__(player, name, address, parent)
        self.requirement_list = requirement_list
        self.shop_price = 0 if name.startswith("Shop ") else None

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
    location_name_to_id = LevelLocationData.get_location_name_to_id(base_id)

    location_descriptions = LevelLocationData.secret_descriptions

    # Raise this to force outdated clients to update.
    aptyrian_net_version = 2

    # --------------------------------------------------------------------------------------------

    goal_episodes: Set[int] = set() # Require these episodes for goal (1, 2, 3, 4, 5)
    play_episodes: Set[int] = set() # Add levels from these episodes (1, 2, 3, 4, 5)
    starting_level: str = "" # Level we start on, gets precollected automatically

    all_levels: List[str] = [] # List of all levels available in seed
    local_itempool: List[str] = [] # Item pool for just us. Forced progression items start with !
    level_locations: List[str] = [] # Only locations in levels

    single_special_weapon: Optional[str] = None # For output to spoiler log only
    #twiddles: List[Twiddle] = []

    weapon_costs: Dict[str, int] = {} # Costs of each weapon's upgrades (see LocalItemData.default_upgrade_costs)
    total_money_needed: int = 0 # Sum total of shop prices and max upgrades, used to calculate filler items

    # ================================================================================================================
    # Item / Location Helpers
    # ================================================================================================================

    def get_random_price(self) -> int:
        # I don't really like the distribution I was getting from just doing random.triangular, so
        # instead we have ten different types of random prices that can get generated, and we choose
        # which one we want randomly.
        range_list = [
            ( 100,  1001,  1), ( 200,  3001,  2), ( 500,  5001,  5), (1000,  7501,  5), ( 2000, 10001,   5),
            (3000, 15001, 10), (4000, 20001, 10), (5000, 30001, 25), (7500, 40001, 25), (10000, 65601, 100)
        ]
        range_set = self.random.randrange(10)
        return min(self.random.randrange(*range_list[range_set]), 65535)

    def create_item(self, name: str) -> TyrianItem:
        name = name[1:] if (force_progression := name.startswith("!")) else name

        pool_data = LocalItemData.get(name)
        item_class = IC.progression if force_progression else pool_data.item_class

        return TyrianItem(name, item_class, self.item_name_to_id[name], self.player)

    def create_level_location(self, name: str, region: Region,
          requirement_list: Optional[RequirementList] = None) -> TyrianLocation:
        loc = TyrianLocation(self.player, name, self.location_name_to_id[name], region, requirement_list)

        if self.options.exclude_obscure_checks and isinstance(requirement_list, RequirementList):
            loc.progress_type = LP.EXCLUDED if requirement_list.obscure else LP.DEFAULT
        # Otherwise, always set to LP.DEFAULT by default

        region.locations.append(loc)
        return loc

    def create_shop_location(self, name: str, region: Region, region_data: LevelRegion) -> TyrianLocation:
        loc = TyrianLocation(self.player, name, self.location_name_to_id[name], region)
        region_data.set_random_shop_price(self, loc)

        # If completion is obscure, exclude the entirety of the shop
        if self.options.exclude_obscure_checks \
              and isinstance(region_data.completion_reqs, RequirementList) \
              and region_data.completion_reqs.obscure:
            loc.progress_type = LP.EXCLUDED

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
            return {key: self.random.randrange(500, 2001, 25)
                  for key in LocalItemData.default_upgrade_costs.keys()}
        else:
            return {key: int(self.options.base_weapon_cost.current_key)
                  for key in LocalItemData.default_upgrade_costs.keys()}

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
    def output_twiddles(self) -> list:
        return []

    # Which locations are progression (used for multiworld slot data)
    def output_progression_data(self) -> List[int]:
        return [location.address - self.base_id
              for location in self.multiworld.get_locations(self.player)
              if location.item.advancement and not location.shop_price and location.address is not None]

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
            slot_data["TwiddleData"]: self.obfuscate_object(self.output_twiddles())

        if local_mode: # Local mode: Output all location contents
            slot_data["LocationData"] = self.obfuscate_object(self.output_all_locations())
        else: # Remote mode: Just output a list of location IDs that contain progression
            slot_data["ProgressionData"] = self.obfuscate_object(self.output_progression_data())

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

        if 1 in self.play_episodes:   self.starting_level = "TYRIAN (Episode 1)"
        elif 2 in self.play_episodes: self.starting_level = "TORM (Episode 2)"
        elif 3 in self.play_episodes: self.starting_level = "GAUNTLET (Episode 3)"
        elif 4 in self.play_episodes: self.starting_level = "SURFACE (Episode 4)"
        else:                         self.starting_level = "ASTEROIDS (Episode 5)"

        self.weapon_costs = self.get_weapon_costs()
        self.total_money_needed = max(self.weapon_costs.values()) * 220

    def create_regions(self):
        menu_region = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu_region)

        main_hub_region = Region("Play Next Level", self.player, self.multiworld)
        self.multiworld.regions.append(main_hub_region)
        menu_region.connect(main_hub_region)

        # ==============
        # === Levels ===
        # ==============

        for (name, location_list) in LevelLocationData.level_regions.items():
            region_item_data = LocalItemData.get(name) # Unlocking items have the same name as the region
            if region_item_data.episode not in self.play_episodes:
                continue

            self.all_levels.append(name)

            if self.starting_level == name:
                # World needs a starting point, give the item for the starting level immediately
                self.multiworld.push_precollected(self.create_item(name))
            else:
                self.local_itempool.append(name)

            # Create the region for the level and connect it to the hub
            level_region = Region(name, self.player, self.multiworld)
            main_hub_region.connect(level_region, f"Open {name}")
            self.multiworld.regions.append(level_region)

            # Create the shop region immediately, and connect it to the level (treat completion as an entrance)
            # We don't particularly care if shops are even enabled, and we'll fill in shop checks afterward
            shop_region = Region(f"Shop ({name})", self.player, self.multiworld)
            level_region.connect(shop_region, f"Can shop at {name}")
            self.multiworld.regions.append(shop_region)

            # Make all locations listed for this region
            for (location_name, location_reqs) in location_list.items():
                self.level_locations.append(location_name) # Saves us time generating rules
                self.create_level_location(location_name, level_region, location_reqs)

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
                shop_region = self.multiworld.get_region(f"Shop ({level})", self.player)
                self.multiworld.regions.append(shop_region)

                # Get region data; if completion requirements exist and are marked obscure, all shop checks are too
                region_data = LevelLocationData.level_regions[level]

                for i in range(items_per_shop[level]):
                    shop_loc_name = f"Shop ({level}) - Item {i + 1}"
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
            item_name = f"!{item_name}"
            if item_name in self.local_itempool: # Item promoted to progression
                self.local_itempool.remove(item_name)
                return item_name
            return None

        def pool_item_to_progression(item_name) -> bool:
            if item_name in self.local_itempool:
                self.local_itempool.remove(item_name)
                self.local_itempool.append(f"!{item_name}")
                return True
            return False

        # ----------------------------------------------------------------------------------------

        # Remove precollected (starting inventory) items from the pool.
        for precollect in self.multiworld.precollected_items[self.player]:
            pop_from_pool(precollect.name)

        # Pull the weapon we start with out of the pool.
        starting_weapon = pop_from_pool("Pulse-Cannon")
        self.multiworld.push_precollected(self.create_item(starting_weapon))

        if self.options.specials == 1: # Get a random special, no others
            self.single_special_weapon = self.random.choice(sorted(LocalItemData.special_weapons))

            # Force it to be considered progression, just in case we get something that can be used as such.
            self.multiworld.push_precollected(self.create_item(f"!{self.single_special_weapon}"))

        # If requested, pull max power upgrades from the pool and give them to the player.
        for i in range(1, self.options.starting_max_power):
            max_power_item = pop_from_pool("Maximum Power Up")
            if max_power_item is not None:
                self.multiworld.push_precollected(self.create_item(max_power_item))

        # ----------------------------------------------------------------------------------------

        # Promote some weapons to progression based on tags.
        for weapon in self.random.sample(LocalItemData.front_ports_by_tag("HighDPS"), 2):
            pool_item_to_progression(weapon)
        for weapon in self.random.sample(LocalItemData.front_ports_by_tag("Pierces"), 1):
            pool_item_to_progression(weapon)

        for weapon in self.random.sample(LocalItemData.rear_ports_by_tag("Sideways"), 1):
            pool_item_to_progression(weapon)

        for weapon in self.random.sample(LocalItemData.sidekicks_by_tag("HighDPS"), 1):
            pool_item_to_progression(weapon)
        for weapon in self.random.sample(LocalItemData.sidekicks_by_tag("Defensive"), 1):
            pool_item_to_progression(weapon)

        if self.options.specials == 2: # Specials as MultiWorld items
            # Promote some specials to progression, as well.
            for weapon in self.random.sample(LocalItemData.specials_by_tag("Pierces"), 1):
                pool_item_to_progression(weapon)

        if self.options.contact_bypasses_shields:
            # This can hit the same sidekick that was previously promoted to progressive, and that's fine.
            defensive_sidekick = self.random.choice(LocalItemData.sidekicks_by_tag("Defensive"))
            pool_item_to_progression(defensive_sidekick)
            self.multiworld.early_items[self.player][defensive_sidekick] = 1

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
                  and LocalItemData.get(name).item_class == IC.filler]
            need_to_toss = minimum_needed_item_count - rest_item_count

            if need_to_toss > len(tossable_items):
                # ... Well, shit. Just toss everything we can, and hopefully it'll work out.
                need_to_toss = len(tossable_items)

            tossed = [pop_from_pool(i) for i in self.random.sample(tossable_items, need_to_toss)]
            logging.warning(f"Tossing {need_to_toss} item{'' if need_to_toss == 1 else 's'} "
                            f"from {self.multiworld.get_player_name(self.player)}'s Tyrian world "
                            f"due to insufficient available locations.")
            logging.warning("This is expected if only one episode is enabled, but otherwise you might want "
                            "to check your settings.")
            logging.warning(f"Tossed: {tossed}")

            rest_item_count = len(self.multiworld.get_unfilled_locations(self.player)) - len(self.local_itempool)


        self.local_itempool.extend(self.get_junk_items(rest_item_count, self.total_money_needed))

        # ----------------------------------------------------------------------------------------

        # We're finally done, dump everything we've got into the itempool
        self.multiworld.itempool.extend(self.create_item(item) for item in self.local_itempool)

    def set_rules(self):

        # ==========================
        # === Region-level rules ===
        # ==========================

        def create_level_unlock_rule(level_name: str):
            entrance = self.multiworld.get_entrance(f"Open {level_name}", self.player)
            entrance.access_rule = lambda state: state.has(level_name, self.player)

        def create_shop_rule(level_name: str):
            entrance = self.multiworld.get_entrance(f"Can shop at {level_name}", self.player)
            # Shop region is connected to the level region, so it's inherently locked by the level unlock rule
            region_access = LevelLocationData.level_regions[level].completion_reqs
            if region_access == "Boss":
                entrance.access_rule = lambda state: state.can_reach(f"{level_name} - Boss", "Location", self.player)
            else:
                entrance.access_rule = lambda state: state._tyrian_requirement_satisfied(self.player, region_access)

        for level in self.all_levels:
            create_level_unlock_rule(level)
            if self.options.shop_mode != "none":
                create_shop_rule(level)

        # ============================
        # === Location-level rules ===
        # ============================

        def create_location_rule(location_name: str):
            location = self.multiworld.get_location(location_name, self.player)
            location.access_rule = lambda state: \
                  state._tyrian_requirement_satisfied(self.player, location.requirement_list)

        for check in self.level_locations:
            create_location_rule(check)

        # ===================
        # === Event rules ===
        # ===================

        def create_episode_complete_rule(event_name, location_name):
            event = self.multiworld.find_item(event_name, self.player)
            event.access_rule = lambda state: state.can_reach(location_name, "Location", self.player)

        episode_num = 0
        for (event_name, level_name) in LevelLocationData.events.items():
            episode_num += 1
            if episode_num not in self.goal_episodes:
                continue

            create_episode_complete_rule(event_name, f"{level_name} - Boss")

            # If only one episode is goal, exclude anything in the shop behind the goal level.
            if len(self.goal_episodes) == 1:
                shop_locations = [loc for loc in self.multiworld.get_locations(self.player)
                      if loc.name.startswith(f"Shop ({level_name})")]

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
        for shop in [loc for loc in self.multiworld.get_locations(self.player) if loc.name.startswith(f"Shop (")]:
            print(f"{shop.name}: {shop.shop_price}")

        precollected_names = [item.name for item in self.multiworld.precollected_items[self.player]]

        spoiler_handle.write(f"\n\nLevel locations ({self.multiworld.player_name[self.player]}):\n\n")
        for level in self.all_levels:
            if self.starting_level == level:
                spoiler_handle.write(f"{level}: Start\n")
            elif level in precollected_names:
                spoiler_handle.write(f"{level}: Start\n")               
            else:
                level_item_location = self.multiworld.find_item(level, self.player)
                spoiler_handle.write(f"{level}: {level_item_location.name}\n")

        spoiler_handle.write(f"\n\nSpecial Weapon ({self.multiworld.player_name[self.player]}):\n")
        spoiler_handle.write(f"{self.single_special_weapon}\n")

        spoiler_handle.write(f"\n\nTwiddles ({self.multiworld.player_name[self.player]}):\n")
        spoiler_handle.write("None\n")

    def fill_slot_data(self) -> dict:
        slot_data = self.get_slot_data()
        print(slot_data)
        return slot_data
