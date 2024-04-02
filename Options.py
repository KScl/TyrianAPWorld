# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

from dataclasses import dataclass

from BaseClasses import PlandoOptions
from Options import PerGameCommonOptions, Toggle, DefaultOnToggle, Choice, Range, NamedRange, TextChoice, ItemDict, \
      DeathLink

from ..AutoWorld import World

# ===================
# === Goals, etc. ===
# ===================

class EnableTyrian2000Support(Toggle):
    """
    Use Tyrian 2000's data instead of Tyrian 2.1. Turning this on is mandatory if you want to do anything with
    Episode 5. All of Tyrian 2000's weapons and new items will also be added to the item pool.
    """
    display_name = "Enable Tyrian 2000 support"

class GoalEpisode1(Choice):
    """
    Add Episode 1 (Escape) levels to the pool.
    If "goal" is chosen, you'll need to complete "ASSASSIN" (in addition to other episode goals) to win.
    """
    display_name = "Episode 1"
    option_goal = 2
    option_on = 1
    option_off = 0
    default = 2

class GoalEpisode2(Choice):
    """
    Add Episode 2 (Treachery) levels to the pool.
    If "goal" is chosen, you'll need to complete "GRYPHON" (in addition to other episode goals) to win.
    """
    display_name = "Episode 2"
    option_goal = 2
    option_on = 1
    option_off = 0
    default = 2

class GoalEpisode3(Choice):
    """
    Add Episode 3 (Mission: Suicide) levels to the pool.
    If "goal" is chosen, you'll need to complete "FLEET" (in addition to other episode goals) to win.
    """
    display_name = "Episode 3"
    option_goal = 2
    option_on = 1
    option_off = 0
    default = 2

class GoalEpisode4(Choice):
    """
    Add Episode 4 (An End to Fate) levels to the pool.
    If "goal" is chosen, you'll need to complete "NOSE DRIP" (in addition to other episode goals) to win.
    """
    display_name = "Episode 4"
    option_goal = 2
    option_on = 1
    option_off = 0
    default = 2

class GoalEpisode5(Choice):
    """
    Add Episode 5 (Hazudra Fodder) levels to the pool. This requires you to enable Tyrian 2000 support.
    If "goal" is chosen, you'll need to complete "FRUIT" (in addition to other episode goals) to win.
    """
    display_name = "Episode 5"
    option_goal = 2
    option_on = 1
    option_off = 0
    default = 0

class BossWeaknesses(Toggle):
    """
    If true, the boss of the last level of each goal episode will only be weak to one specific weapon.
    A "Data Cube" item will be added for each boss modified this way, that tells you what weapon you need to use.
    """
    display_name = "Boss Weaknesses"

# ==================================
# === Itempool / Start Inventory ===
# ==================================

class StartingMoney(Range):
    """Change the amount of money you start the seed with."""
    display_name = "Starting Money"
    range_start = 0
    range_end = 9999999
    default = 10000

class StartingMaxPower(Range):
    """
    Change the maximum power level you're allowed to upgrade weapons to when you start the seed.
    Setting this to somewhere around 5 can result in significantly more open seeds.
    """
    display_name = "Starting Maximum Power Level"
    range_start = 1
    range_end = 11
    default = 1

class RandomStartingWeapon(Toggle):
    """
    Choose whether you start with the default Pulse-Cannon or something random; how random depends on logic difficulty
    settings, among other things. In particular, adding generators to your start inventory may result in a better
    selection for lower logic difficulties.

    Note: If your start inventory contains a front weapon, you will not receive another starting weapon (and therefore,
    this option will be ignored).
    """
    display_name = "Random Starting Weapon"

class RemoveFromItemPool(ItemDict):
    """
    Allows customizing the item pool by removing unwanted items from it.

    Note: Items in starting inventory are automatically removed from the pool; you don't need to remove them here too.
    """
    display_name = "Remove From Item Pool"
    verify_item_name = True

# =======================
# === Shops and Money ===
# =======================

class ShopMode(Choice):
    """
    Determine if shops exist and how they behave.

    If 'none', shops will not exist; credits will only be used to upgrade weapons.
    If 'standard', each level will contain a shop that is accessible after clearing it. The shop will contain anywhere
    from 1 to 5 additional checks for the multiworld.
    If 'hidden', shops will behave as above, but will not tell you what you're buying until after you spend credits.
    """
    display_name = "Shop Mode"
    option_none = 0
    option_standard = 1
    option_hidden = 2
    default = 1

class ShopItemCount(NamedRange):
    """
    The number of shop location checks that will be added.
    All levels are guaranteed to have at least one shop item if there's more shop location checks than levels.
    You may also specify 'always_one', 'always_two', 'always_three', 'always_four', or 'always_five' to
    guarantee that shops will have exactly that many items.
    """
    display_name = "Shop Item Count"
    range_start = 1
    range_end = 330
    special_range_names = {
        "always_one":   -1,
        "always_two":   -2,
        "always_three": -3,
        "always_four":  -4,
        "always_five":  -5,
    }
    default = 100

    @property
    def current_option_name(self) -> str:
        if self.value <= -1:
            return ["Always One", "Always Two", "Always Three", "Always Four", "Always Five"][abs(self.value) - 1]
        return str(self.value)

class MoneyPoolScale(Range):
    """
    Change the amount of money in the pool, as a percentage.

    At 100 (100%), the total amount of money in the pool will be equal to the cost of upgrading the most expensive
    front weapon to the maximum level, plus the cost of purchasing all items from every shop.
    """
    display_name = "Money Pool Scaling"
    range_start = 20
    range_end = 400
    default = 100

class BaseWeaponCost(TextChoice):
    """
    Change the amount that weapons (and, in turn, weapon power upgrades) cost.

    If 'original', weapons will cost the same amount that they do in the original game.
    If 'balanced', prices will be changed around such that generally more powerful and typically used weapons
    (Laser, etc.) will cost more.
    If 'randomized', weapons will have random prices.
    You may also input a positive integer to force all base weapon prices to that amount.
    """
    display_name = "Base Weapon Cost"
    # This is intentionally not a named range. I want the options to be displayed on web/template.
    # Having a fixed integer value is the more obscure use case, the options are the common one.
    option_original = -1
    option_balanced = -2
    option_randomized = -3
    default = -1

    def verify(self, world: World, player_name: str, plando_options: PlandoOptions) -> None:
        if isinstance(self.value, int):
            return
        try:
            if int(self.value) >= 0:
                return
        except ValueError:
            pass # Don't include this (expected) exception in the stack trace

        raise ValueError(f"Could not find option '{self.value}' for '{self.__class__.__name__}', "
                         f"known options are {', '.join(self.options)}, <any positive integer>")

class ProgressiveItems(DefaultOnToggle):
    """
    How items with multiple tiers (in this game, only generators) should be rewarded.

    If 'off', each item can be independently picked up, letting you skip tiers. Picking up an item of a lower tier
    after an item of a higher tier does nothing.
    If 'on', each "Progressive" item will move you up to the next tier, regardless of which one you find.
    """
    display_name = "Progressive Items"

class Specials(Choice):
    """
    Enable or disable specials (extra behaviors when starting to fire).

    If 'on', your ship will have a random special from the start.
    If 'as_items', specials will be added to the item pool, and can be freely chosen once acquired.
    If 'off', specials won't be available at all.
    """
    display_name = "Specials"
    option_on = 1
    option_as_items = 2
    option_off = 0
    alias_true = 1
    alias_false = 0
    default = 2

class Twiddles(Choice):
    """
    Enable or disable twiddles (Street Fighter-esque button combinations).

    If 'on', your ship will have three random twiddles. Their button combinations will be the same as in the original
    game; as will their use costs.
    If 'chaos', your ship will have three random twiddles with new inputs. They may have new, unique behaviors; and
    they may have different use costs.
    If 'off', no twiddles will be available.
    """
    display_name = "Twiddles"
    option_on = 1
    option_chaos = 2
    option_off = 0
    alias_true = 1
    alias_false = 0
    default = 1

# ==================
# === Difficulty ===
# ==================

class LogicDifficulty(Choice):
    """
    Select how difficult the logic will be.

    If 'beginner', most secret locations will be excluded by default, and additional leeway will be provided when
    calculating damage to ensure you can destroy things required to obtain checks.
    If 'standard', only a few incredibly obscure locations will be excluded by default. There will always logically be
    a weapon loadout you can use to obtain checks that your current generator can handle (shields notwithstanding).
    If 'expert', all locations will be in logic, and it will be expected that you can manage a weapon loadout that
    creates a power drain on your current generator.
    If 'master', logic will be as in 'expert' but you will also be expected to know technical things like specific
    triggers for secrets and other minute details, and little to no leeway will be provided with damage calculation.
    """
    display_name = "Logic Difficulty"
    option_beginner = 1
    option_standard = 2
    option_expert = 3
    option_master = 4
    default = 2

class GameDifficulty(Choice):
    """
    Select the base difficulty of the game. Anything beyond Impossible is VERY STRONGLY not recommended unless you
    know what you're doing.
    """
    display_name = "Game Difficulty"
    option_easy = 1 # 75% enemy health
    option_normal = 2 # 100% enemy health
    option_hard = 3 # 120% enemy health
    option_impossible = 4 # 150% enemy health, fast firing and bullet speeds
    option_suicide = 6 # 200% enemy health, fast firing and bullet speeds
    option_lord_of_game = 8 # 400% enemy health, incredibly fast firing and bullet speeds
    alias_lord_of_the_game = option_lord_of_game
    alias_zinglon = option_lord_of_game
    default = 2

class HardContact(Toggle):
    """
    Direct contact with an enemy or anything else will completely power down your shields and deal armor damage.

    Note that this makes the game significantly harder. Additional "Enemy approaching from behind" callouts will be
    given throughout the game if this is enabled.
    """
    display_name = "Contact Bypasses Shields"

class ExcessArmor(DefaultOnToggle):
    """Twiddles, pickups, etc. can cause your ship to have more armor than its maximum armor rating."""
    display_name = "Allow Excess Armor"

# ======================================
# === Visual tweaks and other things ===
# ======================================

class ForceGameSpeed(Choice):
    """Force the game to stay at a specific speed setting, or "off" to allow it to be freely chosen."""
    display_name = "Force Game Speed"
    option_off = -1
    option_slug_mode = 0
    option_slower = 1
    option_slow = 2
    option_normal = 3
    option_turbo = 4
    default = -1

class ShowTwiddleInputs(DefaultOnToggle):
    """If twiddles are enabled, show their inputs in "Ship Info" next to the name of each twiddle."""
    display_name = "Show Twiddle Inputs"

class ArchipelagoRadar(DefaultOnToggle):
    """Shows a bright outline around any enemy that contains an Archipelago Item. Recommended for beginners."""
    display_name = "Archipelago Radar"

class Christmas(Toggle):
    """Use the Christmas set of graphics and sound effects. """
    display_name = "Christmas Mode"

# =============================================================================

@dataclass
class TyrianOptions(PerGameCommonOptions):
    remove_from_item_pool: RemoveFromItemPool

    enable_tyrian_2000_support: EnableTyrian2000Support
    episode_1: GoalEpisode1
    episode_2: GoalEpisode2
    episode_3: GoalEpisode3
    episode_4: GoalEpisode4
    episode_5: GoalEpisode5
    boss_weaknesses: BossWeaknesses

    starting_money: StartingMoney
    starting_max_power: StartingMaxPower
    random_starting_weapon: RandomStartingWeapon

    shop_mode: ShopMode
    shop_item_count: ShopItemCount
    money_pool_scale: MoneyPoolScale
    base_weapon_cost: BaseWeaponCost
    progressive_items: ProgressiveItems
    specials: Specials
    twiddles: Twiddles

    logic_difficulty: LogicDifficulty
    difficulty: GameDifficulty
    contact_bypasses_shields: HardContact
    allow_excess_armor: ExcessArmor

    force_game_speed: ForceGameSpeed
    show_twiddle_inputs: ShowTwiddleInputs
    archipelago_radar: ArchipelagoRadar
    christmas_mode: Christmas
    deathlink: DeathLink
