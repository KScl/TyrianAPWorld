# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from typing import Optional, List

from .Items import LocalItemData
from ..AutoWorld import LogicMixin

class RequirementList:
    # Requirements, in general, are based off of a Hard difficulty game.
    # "Power2" - "Power11" requires that max weapon power level.
    # "Armor6" - "Armor14" requires that maximum armor.
    # "Generator2" - "Generator6" requires that level of generator.
    # "Front###", "Rear###", "Side###", "Special###" requires a front/rear/side/special with that tag.
    # "Repulsor" and "Invulnerability" are specials (and/or twiddles) with significant game effects.

    requirements: List[List[str]] # [ [x and y] or [foo and baz] ]
    obscure: bool # If requires specific game knowledge / is unduly difficult
    boss: bool

    def __init__(self, *reqs, require_all: Optional[List[str]] = None, obscure: bool = False):
        self.obscure = obscure
        self.requirements = list(reqs)
        if require_all is not None:
            for condition_list in self.requirements:
                condition_list.extend(require_all)

class TyrianLogic(LogicMixin):
    def _tyrian_has_armor_level(self, player: int, armor_level: int):
        return True if armor_level <= 5 else self.has("Armor Up", player, armor_level - 5)

    def _tyrian_has_power_level(self, player: int, power_level: int):
        return True if power_level <= 1 else self.has("Maximum Power Up", player, power_level - 1)

    def _tyrian_has_generator_level(self, player: int, gen_level: int):
        base_gen_level = 1
        if self.has("Gravitron Pulse-Wave", player):   return True
        elif self.has("Advanced MicroFusion", player): base_gen_level = 5
        elif self.has("Standard MicroFusion", player): base_gen_level = 4
        elif self.has("Gencore Custom MR-12", player): base_gen_level = 3
        elif self.has("Advanced MR-12", player):       base_gen_level = 2

        return gen_level <= base_gen_level \
              or self.has("Progressive Generator", player, gen_level - base_gen_level)

    def _tyrian_has_twiddle(self, player: int, action: str):
        return False # TODO NYI

    def _tyrian_requirement_satisfied(self, player: int, requirements_list: Optional[RequirementList]):
        # Pass by default
        if requirements_list is None or len(requirements_list.requirements) == 0:
            return True

        # Any one of the 'condition_list's needs to test truthy
        # For a 'condition_list' to test truthy, all 'condition's inside it must test truthy
        for condition_list in requirements_list.requirements:
            pass_count = 0

            for condition in condition_list:
                if condition.startswith("Armor"):
                    if not self._tyrian_has_armor_level(player, int(condition[5:])):
                        break
                elif condition.startswith("Power"):
                    if not self._tyrian_has_power_level(player, int(condition[5:])):
                        break
                elif condition.startswith("Generator"):
                    if not self._tyrian_has_generator_level(player, int(condition[9:])):
                        break
                elif condition.startswith("Front"):
                    if not self.has_any(LocalItemData.front_ports_by_tag(condition[5:]), player):
                        break
                elif condition.startswith("Rear"):
                    if not self.has_any(LocalItemData.rear_ports_by_tag(condition[4:]), player):
                        break
                elif condition.startswith("Special"):
                    if not self.has_any(LocalItemData.specials_by_tag(condition[7:]), player):
                        break
                elif condition.startswith("Side"):
                    if not self.has_any(LocalItemData.sidekicks_by_tag(condition[4:]), player):
                        break
                elif condition.startswith("Any"):
                    if not self.has_any(LocalItemData.all_by_tag(condition[3:]), player):
                        break
                elif condition == "Repulsor":
                    if not (self.has("Repulsor", player) \
                          or self._tyrian_has_twiddle(player, "Repulsor")):
                        break
                elif condition == "Invulnerability":
                    if not (self.has("Invulnerability", player) \
                          or self._tyrian_has_twiddle(player, "Invulnerability")):
                        break
                else:
                    raise Exception(f"Invalid condition '{condition}' specified")

                pass_count += 1

            # If all conditions passed, the requirement is satisfied
            if pass_count == len(condition_list):
                return True

        # No condition_list passed
        return False
