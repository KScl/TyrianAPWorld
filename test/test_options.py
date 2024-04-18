# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from . import TyrianTestBase

# =============================================================================
# Testing Option: Boss Weaknesses
# =============================================================================

class TestBossWeaknesses(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "boss_weaknesses": True,
    }

    # All bosses should require the Data Cube for the episode, and the weapon specified in the Data Cube.
    def test_data_cube_and_weakness_weapon_required(self) -> None:
        locations = {
            1: "ASSASSIN (Episode 1) - Boss",
            2: "GRYPHON (Episode 2) - Boss",
            3: "FLEET (Episode 3) - Boss",
            4: "NOSE DRIP (Episode 4) - Boss",
            5: "FRUIT (Episode 5) - Boss",
        }

        for (episode, location) in locations.items():
            with self.subTest(episode=episode, location=location):
                data_cube = self.get_item_by_name(f"Data Cube (Episode {episode})")
                weapon = self.get_item_by_name(self.world.all_boss_weaknesses[episode])

                items = [weapon.name, data_cube.name]
                self.assertAccessDependency([location], [items], only_check_listed=True)

class TestSomeBossWeaknesses(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "on",
        "episode_3": "goal",
        "episode_4": "on",
        "episode_5": "goal",
        "boss_weaknesses": True,
    }

    @property
    def run_default_tests(self) -> bool:
        return False

    # Only episodes marked as "goal" should have boss weaknesses. Others should behave normally.
    def test_only_weaknesses_for_goal_episodes(self) -> None:
        boss_weakness_data = {
            1: ("ASSASSIN (Episode 1) - Boss", True),
            2: ("GRYPHON (Episode 2) - Boss", False),
            3: ("FLEET (Episode 3) - Boss", True),
            4: ("NOSE DRIP (Episode 4) - Boss", False),
            5: ("FRUIT (Episode 5) - Boss", True),
        }

        for episode in boss_weakness_data.keys():
            with self.subTest(episode=episode):
                location, has_weakness = boss_weakness_data[episode]
                data_cubes = self.get_items_by_name(f"Data Cube (Episode {episode})")
                if has_weakness:
                    msg = f"Episode {episode} is goal, but has no weakness"
                    self.assertEqual(len(data_cubes), 1, msg=msg)
                    self.assertIn(episode, self.world.all_boss_weaknesses, msg=msg)
                else:
                    msg = f"Episode {episode} is not goal, but has weakness"
                    self.assertEqual(len(data_cubes), 0, msg=msg)
                    self.assertNotIn(episode, self.world.all_boss_weaknesses, msg=msg)

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
              if getattr(location, 'shop_price', None) is not None}
        self.assertEqual(len(unique_shop_levels), len(self.world.all_levels), msg="Found level with no shop items")

    # There should always be shop_item_count amount of locations to check.
    def test_shop_item_count_matches(self) -> None:
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None]
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
              if getattr(location, 'shop_price', None) is not None}
        self.assertEqual(len(unique_shop_levels), 16, msg="Some shops contain more than one item")

    # There should always be shop_item_count amount of locations to check.
    def test_shop_item_count_matches(self) -> None:
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None]
        self.assertEqual(len(shop_locations), 16, msg="Shop item count doesn't match number of locations added")

class TestShopsOff(TyrianTestBase):
    options = {
        "shop_mode": "none",
    }

    # Obviously, no shop locations should exist at all.
    def test_no_shop_locations_present(self) -> None:
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None]
        self.assertEqual(len(shop_locations), 0, msg="Shop items present when shop_mode is none")

class TestShopsOnly(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "shop_mode": "shops_only",
        "shop_item_count": 228,
    }

    def test_locations_in_level_only_have_credits(self) -> None:
        level_locations = [location for location in self.multiworld.get_locations(self.player)
              if location.address is not None and getattr(location, 'shop_price', None) is None]
        locations_with_credits = [location for location in level_locations
              if location.item and location.item.name.endswith(" Credits")]
        self.assertEqual(len(locations_with_credits), len(level_locations), msg="Some in-level locations contain non-Credits items")
