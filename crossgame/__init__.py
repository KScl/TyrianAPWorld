# Archipelago MultiWorld integration for Tyrian
#
# This file is copyright (C) Kay "Kaito" Sinclaire,
# and is released under the terms of the zlib license.
# See "LICENSE" for more details.

# Empty __init__.py for crossgame subpackage.

# =================================================================================================

# Everything in this subpackage is meant to modify (in almost all cases, append to) the data structures for other
# games' Archipelago implementations. Everything we do should be considered optional, and thus we should never throw
# anything at the end user; use logging.debug at most. Particularly, an ImportError for a world is *expected behavior*
# (if the user does not have that world loaded), and thus we need to check for it and not modify anything in that case.

# We also do not want to step on the toes of other developers. Every action that writes out to another world's data
# structures should be checking to make sure what we're writing to actually exists, so later renames and refactors
# don't suddenly cause unrelated exceptions for a different game (ours).
