# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from ..logic import DPS, can_deal_damage, has_specific_loadout
from . import TyrianTestBase

# =============================================================================
# Testing Tyrian 2000 specific things
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
    def test_tyrian_2000_items_in_pool(self) -> None:
        tyrian_2000_items = ["Needle Laser", "Pretzel Missile", "Dragon Frost", "Dragon Flame", "People Pretzels",
                             "Super Pretzel", "Dragon Lightning", "Bubble Gum-Gun", "Flying Punch"]
        items_in_pool = self.get_items_by_name(tyrian_2000_items)
        self.assertNotEqual(len(items_in_pool), 0, msg="Tyrian 2000 items not in Tyrian 2000 enabled world")

    def test_episode_5_required(self) -> None:
        self.assertBeatable(False)
        self.collect_all_but(["FRUIT (Episode 5)", "Episode 5 (Hazudra Fodder) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("FRUIT (Episode 5)"))
        self.assertBeatable(True)

# =============================================================================
# Testing base game things
# =============================================================================


class TestTyrianData(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": False,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "on",  # Should be automatically turned off
    }

    # No Tyrian 2000 items should ever be in the pool -- Tyrian 2.1 data cannot support them.
    def test_no_tyrian_2000_items_in_pool(self) -> None:
        # Weapons
        tyrian_2000_items = ["Needle Laser", "Pretzel Missile", "Dragon Frost", "Dragon Flame", "People Pretzels",
                             "Super Pretzel", "Dragon Lightning", "Bubble Gum-Gun", "Flying Punch"]
        items_in_pool = self.get_items_by_name(tyrian_2000_items)
        self.assertEqual(len(items_in_pool), 0, msg="Tyrian 2000 items placed in non-Tyrian 2000 world")

        # Levels
        tyrian_2000_items = ["ASTEROIDS (Episode 5)", "AST ROCK (Episode 5)", "MINERS (Episode 5)",
                             "SAVARA (Episode 5)", "CORAL (Episode 5)", "STATION (Episode 5)", "FRUIT (Episode 5)"]
        items_in_pool = self.get_items_by_name(tyrian_2000_items)
        self.assertEqual(len(items_in_pool), 0, msg="Tyrian 2000 levels placed in non-Tyrian 2000 world")

    def test_episode_1_required(self) -> None:
        self.assertBeatable(False)
        self.collect_all_but(["ASSASSIN (Episode 1)", "Episode 1 (Escape) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("ASSASSIN (Episode 1)"))
        self.assertBeatable(True)

    def test_episode_2_required(self) -> None:
        self.assertBeatable(False)
        self.collect_all_but(["GRYPHON (Episode 2)", "Episode 2 (Treachery) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("GRYPHON (Episode 2)"))
        self.assertBeatable(True)

    def test_episode_3_required(self) -> None:
        self.assertBeatable(False)
        self.collect_all_but(["FLEET (Episode 3)", "Episode 3 (Mission: Suicide) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("FLEET (Episode 3)"))
        self.assertBeatable(True)

    def test_episode_4_required(self) -> None:
        self.assertBeatable(False)
        self.collect_all_but(["NOSE DRIP (Episode 4)", "Episode 4 (An End to Fate) Complete"])
        self.assertBeatable(False)
        self.collect(self.get_item_by_name("NOSE DRIP (Episode 4)"))
        self.assertBeatable(True)

    # -------------------------------------------------------------------------

    def test_active_dps_logic(self) -> None:
        generators = self.get_items_by_name("Progressive Generator")

        dps_test_setups = [
            DPS(active=25.0),
            DPS(active=90.0)
        ]

        # Starting state, non-random weapons: Pulse-Cannon 1 (11.8) is the only possible weapon
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(active_dps_check, False, "Pulse-Cannon:1 has max DPS of 11.8, yet passed 25.0 DPS check")

        # With 10 power ups: Pulse-Cannon 11 (32.1)
        self.collect(self.get_items_by_name("Maximum Power Up"))
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(active_dps_check, True, "Pulse-Cannon:11 has max DPS of 32.1, yet failed 25.0 DPS check")
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(active_dps_check, False, "Pulse-Cannon:11 has max DPS of 32.1, yet passed 90.0 DPS check")

        # Collected Atomic RailGun: Should not change results, Atomic RailGun isn't usable (need 25 generator power)
        self.collect(self.get_item_by_name("Atomic RailGun"))
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(active_dps_check, False, "Atomic RailGun:11 should not be usable with Standard MR-9")
        self.collect(generators[0:2])  # Still shouldn't be enough
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(active_dps_check, False, "Atomic RailGun:11 should not be usable with Gencore Custom MR-12")
        self.collect(generators[2:4])  # Advanced MicroFusion should be enough to use and thus meet target DPS
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(active_dps_check, True, "Atomic RailGun:11 should be usable with Advanced MicroFusion")

    def test_sideways_dps_logic(self) -> None:
        generators = self.get_items_by_name("Progressive Generator")
        powerups = self.get_items_by_name("Maximum Power Up")

        dps_test_setups = [
            DPS(sideways=0.5),
            DPS(sideways=9.0)
        ]

        # Starting state: Nothing has sideways damage so all should fail
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(sideways_dps_check, False, "Passed 0.5 sideways DPS check with no weapon that can fire sideways")

        # Collected Protron (Rear): This should _still_ fail, because the front weapon will use too much energy to allow it to be used
        self.collect(self.get_item_by_name("Protron (Rear)"))
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(sideways_dps_check, False, "Passed 0.5 sideways DPS check while being unable to use Protron (Rear):1 due to energy requirements")

        # Collected Banana Blast (Front): Should now succeed, Banana Blast (Front):1 + Protron (Rear):1 is 9 energy
        self.collect(self.get_item_by_name("Banana Blast (Front)"))
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(sideways_dps_check, True, "Protron (Rear):1 has max sideways DPS of 2.9, yet failed 0.5 DPS check")
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(sideways_dps_check, False, "Protron (Rear):1 has max sideways DPS of 2.9, yet passed 9.0 DPS check")

        # Collected Protron Wave, max power to 4: Should be no change, because base generator doesn't have enough power to use both
        self.collect(self.get_item_by_name("Protron Wave"))
        self.collect(powerups[0:3])
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(sideways_dps_check, False, "Protron Wave:4 + Protron (Rear):4 should not be usable with Standard MR-9")

        # Collect one generator: Should now be able to do over 9.0 DPS (8.6 + 3.3)
        self.collect(generators[0])
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(sideways_dps_check, True, "Protron Wave:4 + Protron (Rear):4 should be usable with Advanced MR-9")

    def test_mixed_dps_logic(self) -> None:
        generators = self.get_items_by_name("Progressive Generator")
        powerups = self.get_items_by_name("Maximum Power Up")
        self.collect(self.get_items_by_name(["Protron Z", "Banana Blast (Front)", "Starburst", "Sonic Wave", "Fireball"]))

        dps_test_setups = [
            DPS(active=12.0),
            DPS(passive=12.0),
            DPS(active=12.0, passive=12.0),
            DPS(active=22.0, passive=5.0),
            DPS(active=40.0, passive=50.0)
        ]

        # Should succeed (Banana Blast (Front):1 + Sonic Wave:1 = 7.8 + 6.7 = 14.5
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(active_dps_check, True, "Banana Blast (Front):1 + Sonic Wave:1 should be 14.5 DPS together, but failed 12.0")

        # Should succeed (Banana Blast (Front):1 + Starburst:1 = 0.0 + 15.3 = 15.3
        passive_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(passive_dps_check, True, "Banana Blast (Front):1 + Starburst:1 should be 15.3 passive DPS together, but failed 12.0")

        # Should fail (No combination of weapons available can do both at once)
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[2])
        self.assertEqual(mixed_dps_check, False, "No combination of weapons can simultaneously fulfill active 12.0 and passive 12.0")

        # Should succeed (Protron Z:1 + Starburst:1 = 14.0/0.0 + 0.0/15.3 = 14.0/15.3)
        self.collect(generators[0:3])  # To Standard MicroFusion (25 base)
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[2])
        self.assertEqual(mixed_dps_check, True, "Protron Z:1 + Starburst:1 should be 14.0/15.3 DPS together, but failed 12.0/12.0")
        self.remove(generators[0:3])  # To Standard MR-9 (10 base)

        # Should fail (shouldn't be able to make this work with just power 1)
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[3])
        self.assertEqual(mixed_dps_check, False, "No combination of weapons can simultaneously fulfill active 22.0 and passive 5.0")

        # Should succeed (Pulse-Cannon:3 + Fireball:2 = 18.7/0.0 + 6.0/6.0 = 24.7/6.0)
        self.collect(powerups[0:2])  # To Maximum Power 3
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[3])
        self.assertEqual(mixed_dps_check, True, "Pulse-Cannon:3 + Starburst:2 should be 24.7/6.0 DPS together, but failed 22.0/5.0")

        # Should succeed (Pulse-Cannon:11 + Fireball:11 = 32.1/15.5 + 15.2/39.7 = 47.3/55.2)
        # This is why there's weighting applied to distance in DPS.meets_requirements
        # Without weighting active over passive, Banana Blast (Front):11 will get picked over Pulse-Cannon:11
        # because it satisfies significantly more passive DPS than the Pulse-Cannon does, but if it does pick that
        # then it can't satisfy the 40.0 active DPS requirement
        self.collect(powerups[2:10])  # To Maximum Power 11
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[4])
        self.assertEqual(mixed_dps_check, True, "Pulse-Cannon:11 + Starburst:2 should be 47.3/55.2 DPS together, but failed 40.0/50.0")

    def test_excluded_weapon_logic(self) -> None:
        self.collect(self.get_items_by_name("Progressive Generator"))
        self.collect(self.get_items_by_name("Maximum Power Up"))

        dps_test_setups = [
            DPS(active=0.2),
            DPS(active=120.0)
        ]

        # Should succeed (Pulse-Cannon:11 obviously provides more than 0.2 active)
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0])
        self.assertEqual(active_dps_check, True, "Pulse-Cannon:11 has max active DPS of 32.1, yet failed 0.2 DPS check")

        # Should fail (all weapons are excluded)
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[0], exclude=["Pulse-Cannon"])
        self.assertEqual(active_dps_check, False, "Passed 0.2 DPS check with all collected weapons excluded")

        self.collect(self.get_item_by_name("Atomic RailGun"))

        # Should succeed (Atomic RailGun + all generators + all power ups easily clears 120 active on its own)
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1])
        self.assertEqual(active_dps_check, True, "Atomic RailGun:11 has max active DPS of 140.0, yet failed 120.0 DPS check")

        # Should fail (with Atomic RailGun excluded, only Pulse-Cannon remains, and it cannot reach 120 active)
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, dps_test_setups[1], exclude=["Atomic RailGun"])
        self.assertEqual(active_dps_check, False, "Passed 120.0 DPS check despite excluding collected Atomic RailGun from test")

    def test_specific_weapon_logic(self) -> None:
        generators = self.get_items_by_name("Progressive Generator")
        powerups = self.get_items_by_name("Maximum Power Up")
        self.collect(generators[0:5])  # To Gravitron Pulse-Wave (50 base)

        # Should succeed (we start with Pulse-Cannon and power level 1, and it's usable on the starting generator)
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Pulse-Cannon", 1))
        self.assertEqual(success_check, True, "Failed Pulse-Cannon:1 check despite starting with it")

        # Should fail (we outright don't have the Multi-Cannon (Rear))
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Pulse-Cannon", 1), rear_weapon=("Multi-Cannon (Rear)", 1))
        self.assertEqual(success_check, False, "Passed Pulse-Cannon:1 + Multi-Cannon (Rear):1 without having the latter weapon")

        self.collect(self.get_item_by_name("Multi-Cannon (Rear)"))

        # Should fail (we don't have power level 3 yet for the rear weapon)
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Pulse-Cannon", 1), rear_weapon=("Multi-Cannon (Rear)", 3))
        self.assertEqual(success_check, False, "Passed Pulse-Cannon:1 + Multi-Cannon (Rear):3 with only max power level 1")

        # Should fail (as above, but flipped, so the requirement is on the front weapon)
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Pulse-Cannon", 3), rear_weapon=("Multi-Cannon (Rear)", 1))
        self.assertEqual(success_check, False, "Passed Pulse-Cannon:3 + Multi-Cannon (Rear):1 with only max power level 1")

        self.collect(powerups[0:2])  # To Maximum Power 3

        # Should succeed (we now have the required power level)
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Pulse-Cannon", 3), rear_weapon=("Multi-Cannon (Rear)", 1))
        self.assertEqual(success_check, True, "Failed Pulse-Cannon:3 + Multi-Cannon (Rear):1 despite having all required items")

        self.collect(self.get_item_by_name("Atomic RailGun"))
        self.collect(self.get_item_by_name("Mega Pulse (Rear)"))

        # Should fail (we don't have power level 11 yet)
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Atomic RailGun", 11), rear_weapon=("Mega Pulse (Rear)", 11))
        self.assertEqual(success_check, False, "Passed Atomic RailGun:11 + Mega Pulse (Rear):11 without having enough power levels")

        self.collect(powerups[2:10])  # To Maximum Power 11
        self.remove(generators[4])  # To Advanced MicroFusion (30 base)

        # Should fail, because we don't actually have a generator that can use this weapon combination
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Atomic RailGun", 11), rear_weapon=("Mega Pulse (Rear)", 11))
        self.assertEqual(success_check, False, "Passed Atomic RailGun:11 + Mega Pulse (Rear):11 without having a generator that can support it")

        self.collect(generators[4])  # To Gravitron Pulse-Wave (50 base)

        # Should succeed (we have everything required to use this loadout now)
        success_check = has_specific_loadout(self.multiworld.state, self.player, front_weapon=("Atomic RailGun", 11), rear_weapon=("Mega Pulse (Rear)", 11))
        self.assertEqual(success_check, True, "Failed Atomic RailGun:11 + Mega Pulse (Rear):11 despite having all required items")

# =============================================================================
# Test each logic difficulty for generation
# =============================================================================


class TestGenerationBeginnerLogic(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "logic_difficulty": "beginner",
    }


class TestGenerationStandardLogic(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "logic_difficulty": "standard",
    }


class TestGenerationExpertLogic(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "logic_difficulty": "expert",
    }


class TestGenerationMasterLogic(TyrianTestBase):
    options = {
        "enable_tyrian_2000_support": True,
        "episode_1": "goal",
        "episode_2": "goal",
        "episode_3": "goal",
        "episode_4": "goal",
        "episode_5": "goal",
        "logic_difficulty": "master",
    }
