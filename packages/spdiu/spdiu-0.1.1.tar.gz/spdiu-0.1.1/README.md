<!-- Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com> -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later                    -->
# Shattered Pixel Dungeon Invoke Utility

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://github.com/tasosalvas/spdiu/LICENSES/AGPL-3.0-or-later.txt)
[![pytest](https://github.com/tasosalvas/spdiu/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/tasosalvas/spdiu/actions/workflows/test.yml)

> [SpdIU](https://pypi.org/project/spdiu/) is a collection of [Invoke](https://www.pyinvoke.org/) tasks that manage [Shattered Pixel Dungeon](https://shatteredpixel.com/) game data.

It's a library of tricks to make your SPD CLI experience as comfortable as the rest of your awesome terminal!

- Run common tasks out of the box from your console
- Hook up your own Python tasks, leveraging the `spdiu` library


# Documentation

- [Installation](https://github.com/tasosalvas/spdiu/doc/installation.md)
- [Configuration](https://github.com/tasosalvas/spdiu/doc/configuration.md)
- [Usage guide](https://github.com/tasosalvas/spdiu/doc/usage.md)
- [Task Collections reference](https://github.com/tasosalvas/spdiu/doc/tasks.md)
- [API manual](https://github.com/tasosalvas/spdiu/doc/api.md)
- [About SpdIU](https://github.com/tasosalvas/spdiu/doc/about.md)


# What does it do?

## Save and Load the game

SpdIU keeps a directory of save slots, containing copies of the game's full data folder.

- `siu save` and `load` are all the commands you need to save-scum your way to 9-challenge
- Safety backups give you a chance to un-wreck your save if you fat-finger it


## Check for updates or download older versions

On github releases, just pick your version.

Create an issue if you know of an SPD fork hosted elsewhere, and we'll try to enable that platform, too!


## Install flavors and remixes

With just a bit of configuration, you can use SpdIU to download any of the SPD forks available in the wild!


## Display Profile and Game data

Get overviews of every single thing stored in your save data.


## Cheat like it's 1989

Βless your next run with one out of a selection of care packages, or downright edit in that upgraded armor you wanted.

It's your game, after all!


# Changelog

The project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and roughly tries to abide with [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).


## [Unrelased]

> ...and currently a work in progress.

- [ ] Full pytest coverage on the current collections
  - [x] slots
  - [ ] get (hrm)
  - [ ] display
  - [ ] cheats
- [ ] A bit of logo n stuff
- [ ] Game entity summaries
- [ ] Better templates for tasks and config
- [ ] More doc


## [0.1.0] 2025-12-26

> ho ho ho: first release


### Added

- The `s[pd]iu` executable, customized wrapper for `inv[oke]`
- The SpdIU task collections:
  - `slots` manages saved states
  - `display` allows inspecting game data
  - `get` downloads and installs the game or forks
  - `cheats` identifies consumables, edits gold and energy, sets bones
- `tasks.py` deployment allows custom user tasks per game
- `spdiu.yaml` local config allows customizing every single bit of state
- _pre-commit_: ruff lint and format, whitespace fixes, REUSE
- _pytest_: Smoke test, classes and low level functions covered


[0.1.0]: https://github.com/tasosalvas/spdiu/releases/tag/v0.1.0
