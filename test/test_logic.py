# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from . import TyrianTestBase
from ..logic import can_deal_damage, can_damage_with_weapon

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
        "episode_5": "on", # Should be automatically turned off
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
        damage_tables = self.multiworld.worlds[self.player].damage_tables
        generators = self.get_items_by_name(["Progressive Generator"] * 5)

        # Starting state, non-random weapons: Pulse-Cannon 1 (11.8) is the only possible weapon
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=25.0)
        self.assertEqual(active_dps_check, False, "Pulse-Cannon:1 has max DPS of 11.8, yet passed 25.0 DPS check")

        # With 10 power ups: Pulse-Cannon 11 (32.1)
        self.collect(self.get_items_by_name(["Maximum Power Up"] * 10))
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=25.0)
        self.assertEqual(active_dps_check, True, "Pulse-Cannon:11 has max DPS of 32.1, yet failed 25.0 DPS check")
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=90.0)
        self.assertEqual(active_dps_check, False, "Pulse-Cannon:11 has max DPS of 32.1, yet passed 90.0 DPS check")

        # Collected Atomic Railgun: Should not change results, Atomic RailGun isn't usable (need 25 generator power)
        self.collect(self.get_item_by_name("Atomic RailGun"))
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=90.0)
        self.assertEqual(active_dps_check, False, "Atomic RailGun:11 should not be usable with Standard MR-9")
        self.collect(generators[0:2]) # Still shouldn't be enough
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=90.0)
        self.assertEqual(active_dps_check, False, "Atomic RailGun:11 should not be usable with Gencore Custom MR-12")
        self.collect(generators[2:4]) # Advanced MicroFusion should be enough to use and thus meet target DPS
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=90.0)
        self.assertEqual(active_dps_check, True, "Atomic RailGun:11 should be usable with Advanced MicroFusion")

    def test_sideways_dps_logic(self) -> None:
        damage_tables = self.multiworld.worlds[self.player].damage_tables
        generators = self.get_items_by_name(["Progressive Generator"] * 5)
        powerups = self.get_items_by_name(["Maximum Power Up"] * 10)

        # Starting state: Nothing has sideways damage so all should fail
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, sideways=0.5)
        self.assertEqual(sideways_dps_check, False, "Passed 0.5 sideways DPS check with no weapon that can fire sideways")

        # Collected Protron (Rear): This should _still_ fail, because the front weapon will use too much energy to allow it to be used
        self.collect(self.get_item_by_name("Protron (Rear)"))
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, sideways=0.5)
        self.assertEqual(sideways_dps_check, False, "Passed 0.5 sideways DPS check while being unable to use Protron (Rear):1 due to energy requirements")

        # Collected Banana Blast (Front): Should now succeed, Banana Blast (Front):1 + Protron (Rear):1 is 9 energy
        self.collect(self.get_item_by_name("Banana Blast (Front)"))
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, sideways=0.5)
        self.assertEqual(sideways_dps_check, True, "Protron (Rear):1 has max sideways DPS of 2.9, yet failed 0.5 DPS check")
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, sideways=9.0)
        self.assertEqual(sideways_dps_check, False, "Protron (Rear):1 has max sideways DPS of 2.9, yet passed 9.0 DPS check")

        # Collected Protron Wave, max power to 4: Should be no change, because base generator doesn't have enough power to use both
        self.collect(self.get_item_by_name("Protron Wave"))
        self.collect(powerups[0:3])
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, sideways=9.0)
        self.assertEqual(sideways_dps_check, False, "Protron Wave:4 + Protron (Rear):4 should not be usable with Standard MR-9")

        # Collect one generator: Should now be able to do over 9.0 DPS (8.6 + 3.3)
        self.collect(generators[0])
        sideways_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, sideways=9.0)
        self.assertEqual(sideways_dps_check, True, "Protron Wave:4 + Protron (Rear):4 should be usable with Advanced MR-9")

    def test_mixed_dps_logic(self) -> None:
        damage_tables = self.multiworld.worlds[self.player].damage_tables
        generators = self.get_items_by_name(["Progressive Generator"] * 5)
        powerups = self.get_items_by_name(["Maximum Power Up"] * 10)
        self.collect(self.get_items_by_name(["Protron Z", "Banana Blast (Front)", "Starburst", "Sonic Wave", "Fireball"]))

        # Should succeed (Banana Blast (Front):1 + Sonic Wave:1 = 7.8 + 6.7 = 14.5
        active_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=12.0)
        self.assertEqual(active_dps_check, True, "Banana Blast (Front):1 + Sonic Wave:1 should be 14.5 DPS together, but failed 12.0")

        # Should succeed (Banana Blast (Front):1 + Starburst:1 = 0.0 + 15.3 = 15.3
        passive_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, passive=12.0)
        self.assertEqual(passive_dps_check, True, "Banana Blast (Front):1 + Starburst:1 should be 15.3 passive DPS together, but failed 12.0")

        # Should fail (No combination of weapons available can do both at once)
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=12.0, passive=12.0)
        self.assertEqual(mixed_dps_check, False, "No combination of weapons can simultaneously fulfill active 12.0 and passive 12.0")

        # Should succeed (Protron Z:1 + Starburst:1 = 14.0/0.0 + 0.0/15.3 = 14.0/15.3)
        self.collect(generators[0:3]) # To Standard MicroFusion (25 base)
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=12.0, passive=12.0)
        self.assertEqual(mixed_dps_check, True, "Protron Z:1 + Starburst:1 should be 14.0/15.3 DPS together, but failed 12.0/12.0")
        self.remove(generators[0:3]) # To Standard MR-9 (10 base)

        # Should fail (shouldn't be able to make this work with just power 1)
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=22.0, passive=5.0)
        self.assertEqual(mixed_dps_check, False, "No combination of weapons can simultaneously fulfill active 22.0 and passive 5.0")

        # Should succeed (Pulse-Cannon:3 + Fireball:2 = 18.7/0.0 + 6.0/6.0 = 24.7/6.0)
        self.collect(powerups[0:2]) # To Maximum Power 3
        mixed_dps_check = can_deal_damage(self.multiworld.state, self.player, damage_tables, active=22.0, passive=5.0)
        self.assertEqual(mixed_dps_check, True, "Pulse-Cannon:3 + Starburst:2 should be 24.7/6.0 DPS together, but failed 22.0/5.0")

    def test_solo_weapon_dps_logic(self) -> None:
        damage_tables = self.multiworld.worlds[self.player].damage_tables
        generators = self.get_items_by_name(["Progressive Generator"] * 5)
        powerups = self.get_items_by_name(["Maximum Power Up"] * 10)
        self.collect(self.get_item_by_name("Lightning Cannon"))

        # This should fail (Lightning Cannon requires at least one generator upgrade)
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 1.0)
        self.assertEqual(solo_dps_check, False, "Should not be able to use acquired Lightning Cannon, but DPS 1.0 test passed")

        # Should succeed now as one generator upgrade is all we need
        self.collect(generators[0])
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 1.0)
        self.assertEqual(solo_dps_check, True, "DPS 1.0 test with required Lightning Cannon failed despite having and being able to use")

        # Test power level closer to 7
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 20.0)
        self.assertEqual(solo_dps_check, False, "Lightning Cannon:1 should not be able to reach DPS 20.0, yet test passed")
        self.collect(powerups[0:6]) # To Maximum Power 7
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 20.0)
        self.assertEqual(solo_dps_check, True, "Lightning Cannon:7 can reach DPS 20.0, yet test failed")

        # Test extreme end
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 80.0)
        self.assertEqual(solo_dps_check, False, "Lightning Cannon:7 should not be able to reach DPS 80.0, yet test passed")
        self.collect(powerups[6:10]) # To Maximum Power 11
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 80.0)
        self.assertEqual(solo_dps_check, False, "Lightning Cannon:11 isn't usable without Gravitron Pulse-Wave, yet test passed")
        self.collect(generators[1:5]) # Gravitron Pulse-Wave
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 80.0)
        self.assertEqual(solo_dps_check, True, "Lightning Cannon:11 with Gravitron Pulse-Wave reaches 93.3 DPS, yet 80.0 DPS test failed")

        # This should obviously fail (have everything except the required weapon)
        self.remove(self.get_item_by_name("Lightning Cannon"))
        self.collect_all_but(["Lightning Cannon"])
        solo_dps_check = can_damage_with_weapon(self.multiworld.state, self.player, damage_tables, "Lightning Cannon", 1.0)
        self.assertEqual(solo_dps_check, False, "Collected all except Lightning Cannon, but test requiring Lightning Cannon passed")
