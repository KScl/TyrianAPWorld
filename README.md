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

- 120 characters per line, loosely followed,
  but ignored when separating code onto a new line would negatively impact readability
  (e.g. logic conditions with long location names)
- Multi-line statements (whether if statements or otherwise) are given a six-space indent,
  to visually offset them from both the previous and following lines
