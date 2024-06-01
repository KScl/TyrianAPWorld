# TyrianAPWorld
Archipelago Multiworld APWorld definition for Tyrian

## Automatic Builds
GitHub is configured to automatically build an APWorld from the contents of this repository when a change is pushed.
You can access and download these automated builds under [Actions](https://github.com/KScl/TyrianAPWorld/actions);
click the name of the latest commit, and "Artifacts" will contain a link to download the APWorld.

## Style
Style is as in the main Archipelago repository's
[style guide](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/style.md#python-code),
with the following exceptions:

- The line length limit is still 120 characters,
  however we only loosely follow and sometimes ignore this, for instance:
  - When splitting up lines would result in making their contents far more difficult to read
    (e.g. Logic conditions with long location names)
- Multi-line statements (whether if statements or otherwise) are either:
  - **visually aligned** with content in the prior line, or
  - given a **six space indent** to visually offset them from both the previous and following lines
- Condense large (switch statement like) blocks of if-elif statements onto **one line each**,
  if every single one can fit under the line length limit while doing so
  - Excepting a final "else" statement used as error handling
  - Vertically align the statements of each condition;
    if there's not enough room to do this then you should not be condensing everything onto one line at all
- Align table and dict contents vertically with neighboring lines
  - This goes directly against PEP 8, but I find following PEP 8 in this situation
    makes information extremely difficult to parse at a glance
