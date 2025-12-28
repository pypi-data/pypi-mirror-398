#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Shattered Pixel Dungeon Invoke Utility.

This file is the entry point to the SpdIU task collections:

'slots', imported at the root namespace:
  Tasks for saving, loading, and managing save slots.

'display', imported at the root namespace:
  Tasks for displaying information about the game state.

'get', imported at the 'get' namespace:
  Tasks for listing and downloading game releases.

'cheats', imported at the 'cheats' namespace:
  Tasks that affect gameplay.

Usage:
'siu info' for this general documentation.
'siu info -h [collection name]' for a collection's documentation.

'siu -l' for a list of tasks.
'siu -h [task name]' for a task's full docstring.
"""

from invoke import task, Collection
from spdiu.config import SpdIUConfig

# collections imported at the root namespace
from spdiu.collections.slots import save, load, backup, clean, watch, ls

# The rest of the collections
from spdiu import collections

__name__ = "spdiu"
ns = Collection(__name__)


# Documentation helper, everything else lives in collections
@task
def info(c, config=False, help=None):
    """
    Usage and documentation. -c to display active configuration.

    It displays the docstring of a task collection.

    -h, --help [collection] displays the collection's docstring instead.
    -c, --config displays the active SpdIU configuration.

    It supplements invoke core's 'siu -h' flag, which supplies task docstrings.
    """
    if config:
        cfg = c.config.spdiu
        d_cfg = SpdIUConfig.defaults["spdiu"]

        print("Active SpdIU configuration:")
        print(f"{cfg.bullet_b}: default | {cfg.bullet_a}: overridden\n")

        for k, v in cfg.items():
            bullet = cfg.bullet_b if d_cfg[k] == v else cfg.bullet_a
            print(f"{bullet}{k}: {v}")

        return

    if help:
        if help in dir(collections):
            print(getattr(collections, help).__doc__)
            return
        else:
            print(f"Collection {help} not found. 'siu info' for general help.")
            return

    print(__doc__)
    print("'siu info -c' to display active SpdIU configuration.")
    return


ns.add_task(info)

# spdiu.collections.display tasks
ns.add_collection(collections.display)

# spdiu.collections.slots tasks
ns.add_task(save)
ns.add_task(load)
ns.add_task(backup)
ns.add_task(clean)
ns.add_task(watch)
ns.add_task(ls)

# namespaced collections
ns.add_collection(collections.get)
ns.add_collection(collections.cheats)
