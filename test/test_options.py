# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from . import TyrianTestBase
from unittest import expectedFailure

# =============================================================================
# Testing Option: Enabling (or disabling) Tyrian 2000 support
# =============================================================================

class TestTyrian2000Data(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
    }   

    # At least one Tyrian 2000 item should be in the pool.
    def test_tyrian_2000_items_in_pool(self):
        tyrian_2000_items = ["Needle Laser", "Pretzel Missile", "Dragon Frost", "Dragon Flame", "People Pretzels",
                             "Super Pretzel", "Dragon Lightning", "Bubble Gum-Gun", "Flying Punch"]
        items_in_pool = self.get_items_by_name(tyrian_2000_items)
        self.assertNotEqual(len(items_in_pool), 0, msg="Tyrian 2000 items not in Tyrian 2000 enabled world")

    def test_episode_5_required(self):
        self.assertBeatable(False)
        self.collect_all_but(["FRUIT (Episode 5)", "Episode 5 (Hazudra Fodder) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("FRUIT (Episode 5)"))
        self.assertBeatable(True)

class TestTyrianData(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": False,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
    }

    # No Tyrian 2000 items should ever be in the pool -- Tyrian 2.1 data cannot support them.
    def test_no_tyrian_2000_items_in_pool(self):
        tyrian_2000_items = ["Needle Laser", "Pretzel Missile", "Dragon Frost", "Dragon Flame", "People Pretzels",
                             "Super Pretzel", "Dragon Lightning", "Bubble Gum-Gun", "Flying Punch"]
        items_in_pool = self.get_items_by_name(tyrian_2000_items)
        self.assertEqual(len(items_in_pool), 0, msg="Tyrian 2000 items placed in non-Tyrian 2000 world")

    def test_episode_1_required(self):
        self.assertBeatable(False)
        self.collect_all_but(["ASSASSIN (Episode 1)", "Episode 1 (Escape) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("ASSASSIN (Episode 1)"))
        self.assertBeatable(True)

    def test_episode_2_required(self):
        self.assertBeatable(False)
        self.collect_all_but(["GRYPHON (Episode 2)", "Episode 2 (Treachery) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("GRYPHON (Episode 2)"))
        self.assertBeatable(True)

    def test_episode_3_required(self):
        self.assertBeatable(False)
        self.collect_all_but(["FLEET (Episode 3)", "Episode 3 (Mission: Suicide) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("FLEET (Episode 3)"))
        self.assertBeatable(True)

    def test_episode_4_required(self):
        self.assertBeatable(False)
        self.collect_all_but(["NOSE DRIP (Episode 4)", "Episode 4 (An End to Fate) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("NOSE DRIP (Episode 4)"))
        self.assertBeatable(True)

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
    @expectedFailure # Logic for Episodes 4 and 5 aren't done yet
    def test_data_cube_and_weakness_weapon_required(self):
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
    def test_only_weaknesses_for_goal_episodes(self):
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
    def test_all_shops_have_at_least_one_item(self):
        # Get all shop locations, split out "Shop - " and " - Item #", and store in a set.
        # When done iterating, this should always contain the same number of items as world.all_levels.
        unique_shop_levels = {location.name.split("-")[1] for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None}
        self.assertEqual(len(unique_shop_levels), len(self.world.all_levels), msg="Found level with no shop items")

    # There should always be shop_item_count amount of locations to check.
    def test_shop_item_count_matches(self):
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None]
        self.assertEqual(len(shop_locations), 80, msg="Shop item count doesn't match number of locations added")

class TestShopsLow(TyrianTestBase):
    options = {
        "shop_mode": "standard",
        "shop_item_count": 16,
    }

    # Shops should have either zero or one items if there's more levels than shop items.
    def test_all_shops_have_zero_or_one_item(self):
        # Get all shop locations, split out "Shop - " and " - Item #", and store in a set.
        # When done iterating, this should always match shop_item_count (16).
        unique_shop_levels = {location.name.split("-")[1] for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None}
        self.assertEqual(len(unique_shop_levels), 16, msg="Some shops contain more than one item")

    # There should always be shop_item_count amount of locations to check.
    def test_shop_item_count_matches(self):
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None]
        self.assertEqual(len(shop_locations), 16, msg="Shop item count doesn't match number of locations added")

class TestShopsOff(TyrianTestBase):
    options = {
        "shop_mode": "none",
    }

    # Obviously, no shop locations should exist at all.
    def test_no_shop_locations_present(self):
        shop_locations = [location for location in self.multiworld.get_locations(self.player)
              if getattr(location, 'shop_price', None) is not None]
        self.assertEqual(len(shop_locations), 0, msg="Shop items present when shop_mode is none")
