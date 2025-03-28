# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from . import TyrianTestBase

# =============================================================================
# Testing Option: Data Cube Hunt
# =============================================================================


class TestDataCubeHuntAbsolute(TyrianTestBase):
    options = {
        "episode_1": "on",
        "episode_2": "on",
        "episode_3": "on",
        "episode_4": "goal",
        "data_cube_hunt": True,
        "data_cubes_required": 28,
        "data_cubes_total": 34,
    }

    # Goal levels shouldn't be in the item pool.
    def test_goal_level_not_in_pool(self) -> None:
        goal_level = self.get_items_by_name("NOSE DRIP (Episode 4)")
        self.assertEqual(len(goal_level), 0, msg="Goal level present in Data Cube Hunt mode")

    # Data cube count should match data_cubes_total.
    def test_all_data_cubes_present(self) -> None:
        data_cubes = self.get_items_by_name("Data Cube")
        self.assertEqual(len(data_cubes), 34, msg="Number of data cubes present does not equal data_cubes_total")

    # At least data_cubes_required number of data cubes should be necessary to beat the seed.
    def test_data_cubes_required(self) -> None:
        self.collect(self.get_item_by_name("Sonic Wave"))
        self.collect(self.get_item_by_name("Atomic RailGun"))
        self.collect(self.get_items_by_name("Maximum Power Up"))
        self.collect(self.get_items_by_name("Armor Up"))
        self.collect(self.get_items_by_name("Progressive Generator"))
        self.assertBeatable(False)

        data_cubes = self.get_items_by_name("Data Cube")
        self.collect(data_cubes[0:26])
        self.assertBeatable(False)
        self.collect(data_cubes[26])
        self.assertBeatable(False)
        self.collect(data_cubes[27])
        self.assertBeatable(True)

# =============================================================================
# Testing Option: Shops
# =============================================================================


class TestShopsNormal(TyrianTestBase):
    options = {
        "shop_mode": "standard",
        "shop_item_count": 80,
    }

    # No shop should be left empty if there's more shop items than levels.
    def test_all_shops_have_at_least_one_item(self) -> None:
        # Get all shop locations, split out "Shop - " and " - Item #", and store in a set.
        # When done iterating, this should always contain the same number of items as world.all_levels.
        unique_shop_levels = {location.name.split("-")[1] for location in self.multiworld.get_locations(self.player)
              if getattr(location, "shop_price", None) is not None}
        self.assertEqual(len(unique_shop_levels), len(self.world.all_levels), msg="Found level with no shop items")

    # There should always be shop_item_count amount of locations to check.
    def test_shop_item_count_matches(self) -> None:
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, "shop_price", None) is not None]
        self.assertEqual(len(shop_locations), 80, msg="Shop item count doesn't match number of locations added")


class TestShopsLow(TyrianTestBase):
    options = {
        "shop_mode": "standard",
        "shop_item_count": 16,
    }

    # Shops should have either zero or one items if there's more levels than shop items.
    def test_all_shops_have_zero_or_one_item(self) -> None:
        # Get all shop locations, split out "Shop - " and " - Item #", and store in a set.
        # When done iterating, this should always match shop_item_count (16).
        unique_shop_levels = {location.name.split("-")[1] for location in self.multiworld.get_locations(self.player)
              if getattr(location, "shop_price", None) is not None}
        self.assertEqual(len(unique_shop_levels), 16, msg="Some shops contain more than one item")

    # There should always be shop_item_count amount of locations to check.
    def test_shop_item_count_matches(self) -> None:
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, "shop_price", None) is not None]
        self.assertEqual(len(shop_locations), 16, msg="Shop item count doesn't match number of locations added")


class TestShopsOff(TyrianTestBase):
    options = {
        "shop_mode": "none",
    }

    # Obviously, no shop locations should exist at all.
    def test_no_shop_locations_present(self) -> None:
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, "shop_price", None) is not None]
        self.assertEqual(len(shop_locations), 0, msg="Shop items present when shop_mode is none")


class TestShopsOnly(TyrianTestBase):
    # this mode is, by design, extremely restrictive.
    # it is designed for "no logic" mode, but we want to make sure it can still function with some logic settings.
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "shop_mode": "shops_only",
        "shop_item_count": "always_five",
        "logic_difficulty": "master",
        "logic_boss_timeout": "on"
    }

    def test_locations_in_level_only_have_credits(self) -> None:
        level_locations = [location for location in self.multiworld.get_locations(self.player)
              if location.address is not None and getattr(location, "shop_price", None) is None]
        locations_with_credits = [location for location in level_locations
              if location.item and location.item.name.endswith(" Credits")]
        self.assertEqual(len(locations_with_credits), len(level_locations), msg="Some in-level locations contain non-Credits items")

# =============================================================================
# Testing Option: Remove from Item Pool
# =============================================================================


class TestRemovedItems(TyrianTestBase):
    options = {
        "episode_1": "on",
        "episode_2": "on",
        "episode_3": "on",
        "episode_4": "goal",
        "specials": "as_items",
        "remove_from_item_pool": {
            "Atom Bombs": 1,
            "Atomic RailGun": 1,
            "MISTAKES (Episode 2)": 1,
        }
    }

    # Items present multiple times should allow partial removal
    def test_removing_partial_from_pool(self) -> None:
        removed_items = self.get_items_by_name("Atom Bombs")
        self.assertEqual(len(removed_items), 1, msg="Wrong amount of removed item present in item pool (expected 1 removed, 1 remaining)")

    # Progression items should still be allowed to be removed
    def test_removing_progression_from_pool(self) -> None:
        removed_items = self.get_items_by_name("Atomic RailGun")
        self.assertEqual(len(removed_items), 0, msg="Progression weapon is still present despite requested removal")

    # Levels should be allowed to be removed; their locations should also be removed
    def test_removing_level_from_pool(self) -> None:
        removed_items = self.get_items_by_name("MISTAKES (Episode 2)")
        self.assertEqual(len(removed_items), 0, msg="Level is still present despite requested removal")

        level_locations = [location for location in self.multiworld.get_locations(self.player)
              if "MISTAKES (Episode 2)" in location.name]
        self.assertEqual(len(level_locations), 0, msg="Locations of removed level still present")
