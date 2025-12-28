#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
SpdIU Saving and Loading task collection.

By convention, where applicable:
-s --slot is used to load a save slot by name
-g --game to pick a specific game in a slot
"""

import re
from time import strftime

from invoke import task, Collection
from invoke.watchers import StreamWatcher

from .. import util
from ..util import path
from ..model import Profile, Slots


ns = Collection("slots")


# File manipulation Tasks
@task
def backup(c) -> bool:
    """Create a backup of the active data.

    Automatically called by load and clean.
    """
    cfg = c.config.spdiu
    src = path(c, cfg.game.data)
    dest = path(c, cfg.dirs.slots, "backup", cfg.backup_slot)

    try:
        util.replace(src, dest)

    except FileNotFoundError:
        print("Aborting! There seems to be no active data folder.")
        return False

    print(f"Active state backup created! {cfg.i.bak} backup.{cfg.backup_slot}")
    return True


@task(post=[backup])
def clean(c) -> bool:
    """Remove all saved states, leave a backup of the active data folder."""
    cfg = c.config.spdiu
    if not path(c, cfg.game.data).exists():
        print("Aborting! There seems to be no active data folder.")
        return False

    s = Slots(path(c, cfg.dirs.slots), ["manual", "auto", "backup"])
    for p in s.slots:
        util.remove(p.root_dir)

    print(f"{cfg.i.clean} {len(s.slots)} saved states deleted.")
    return True


@task
def save(c, slot=None) -> bool:
    """Save a copy of the current savegame folder. -s [slot] to name a slot.

    Slot names can only be alphanumeric characters.

    When saving over an existing slot, a backup of the previous state is kept
    as backup.[slot name].

    Saves are kept in the game's data folder, with their slot as an extension.
    """
    cfg = c.config.spdiu

    if slot is None:
        slot = cfg.default_slot

    if slot and not slot.isalnum():
        print("Aborting! Names can only contain alphanumeric characters.")
        return False

    src = path(c, cfg.game.data)
    dest = path(c, cfg.dirs.slots, "manual", slot)
    bak = path(c, cfg.dirs.slots, "backup", slot)

    if dest.exists():
        util.replace(dest, bak)
        print(f"Previous save preserved as {cfg.i.bak} backup.{slot}")

    try:
        util.replace(src, dest)
    except FileNotFoundError:
        print("No game data found to save!")
        return False

    print(f"State saved! {cfg.i.disc_b} {slot}")
    return True


@task
def load(c, last=False, slot=None, game=None) -> bool:
    """Load a save. -l for last save, -s [slot], -g [game] to only load a game.

    Slots provided with -s, --slot correspond to the manual saves,
    while the other categories can be accessed with dot syntax,

    i.e. 'siu load -s backup.bak' or 'auto.floor3'
    'siu load -s mysave' is in effect equivalent 'siu load -s manual.mysave'.

    If -l, --last is provided, any slot named with -s is ignored.
    The task will look for the latest save in the manual and auto folders,
    ignoring the backup folder.

    The -g, --game [game name] flag allows loading only a specific game,
    while leaving the player profile untouched (i.e. keeping unlocks).

    Loading will save a backup of the active save in the backup slot,
    unless the backup slot itself is being loaded.
    """
    cfg = c.config.spdiu
    slot_path = path(c, cfg.dirs.slots)

    if last:
        try:
            p = Slots(path(c, cfg.dirs.slots), ["manual", "auto"]).slots[0]
        except IndexError:
            print("No saves found. Make some with 'siu save [-s slot name]'")
            return False

    else:
        if slot is None:
            p = Slots(slot_path, ["manual"]).get_slot(cfg.default_slot)

        else:
            p = Slots(slot_path, ["manual", "auto", "backup"]).get_slot(slot)

    if not p:
        print(f"Invalid slot name: {slot} - 'siu ls' to list existing slots.")
        return False

    ap_path = path(c, cfg.game.data)
    # Load the requested profile and exit
    if game is None:
        if p.name != cfg.backup_slot:
            backup(c)

        util.replace(p.root_dir, ap_path)

        print(f"State loaded! {cfg.i.disc_a} {p.group}.{p.name}")
        return True

    # Get the instance of the requested game, build the destination path.
    g = p.get_game(game)
    if not g:
        print("Game not found in slot.")
        print(f"'siu show -s {slot}' to list existing games.")
        return False

    if p.name != cfg.backup_slot:
        backup(c)

    ag_path = ap_path / game
    util.replace(g.root_dir, ag_path)
    print(f"Game loaded! {cfg.i.disc_a} {p.group}.{p.name} {cfg.i.game} {game}")
    return True


# Autosaves
class AutoSaveWatcher(StreamWatcher):
    """Watch the stdout of the game, autosave on certain events."""

    def __init__(self, c):
        """Compile patterns, keep track of the log position."""
        self.c = c

        patterns = (r"\[GAME\] @@ You \S+ to (floor \d+) of the dungeon.",)

        self.patterns = [re.compile(i) for i in patterns]
        self.log_index = 0

    def autosave(self, event):
        """Create saves in the autosave directory."""
        cfg = self.c.config.spdiu

        name = event.replace(" ", "")
        dest = path(self.c, cfg.dirs.slots, "auto", name)
        src = path(self.c, cfg.game.data)

        util.replace(src, dest)
        print(f"{cfg.bullet_b}Autosave {cfg.i.auto} auto.{name}")

    def submit(self, stream):
        """Autosave if a pattern is matched.

        Gets the whole log every time there's a line,
        skips to the current log_index and updates it.
        """
        new = stream[self.log_index :]

        # Autosave triggers
        for p in self.patterns:
            match = re.search(p, new)
            if match:
                self.autosave(match.group(1))
                break

        self.log_index = len(stream)
        return ()


@task
def watch(c):
    """Run the game, autosave on certain log events."""
    cfg = c.config.spdiu

    # split the arguments and escape spaces in the command
    smash = cfg.game.cmd.split(" -")
    cmd_bin = smash[0].replace(" ", "\\ ")
    args = smash[1:] if len(smash) > 1 else []
    cmd = " -".join([cmd_bin] + args)

    w_out = AutoSaveWatcher(c)

    with c.cd(path(c, cfg.dirs.game)):
        c.run(cmd, watchers=[w_out])


@task
def ls(c) -> dict:
    """List all saved states chronologically.

    The disc icon signifies the latest data folder between all states.

    The bullet indicator signifies whether the active state is latest,
    but also displays the latest save slot, even if the active one is newer.

    The slots are sorted by time, so the latest one is always last.
    """
    cfg = c.config.spdiu
    try:
        ap = Profile(path(c, cfg.game.data))
    except FileNotFoundError:
        print(f"No active slot found at {cfg.game.data}. Play a little!")
        return False

    s = Slots(path(c, cfg.dirs.slots), ["manual", "auto", "backup"])

    # active save vars
    a_bullet = cfg.bullet_a
    a_disc = cfg.i.disc_a

    # Calculate latest save
    if s.slots:
        latest = s.slots[0]

        # adjust the active save display
        if ap.ts <= latest.ts:
            a_bullet = cfg.bullet_b
            a_disc = cfg.i.disc_b

    print(f"Displaying {len(s.slots)} save slots, oldest to newest:")
    for p in reversed(s.slots):
        bullet = cfg.bullet_a if p == latest else cfg.bullet_b

        if p.group == "backup":
            disc = cfg.i.bak
        elif p.group == "auto":
            disc = cfg.i.auto
        elif p == latest and ap.ts <= latest.ts:
            disc = cfg.i.disc_a
        else:
            disc = cfg.i.disc_b

        time = strftime(cfg.time_format, p.ts)
        prefix = "" if p.group == "manual" else p.group + "."
        print(f"{bullet}{time} {disc} {prefix}{p.name}")

    print("\nActive slot:")
    print(a_bullet + strftime(cfg.time_format, ap.ts) + f" {a_disc} {ap.name}")

    return {
        "data": ap,
        "slots": s,
    }


ns.add_task(backup)
ns.add_task(clean)
ns.add_task(save)
ns.add_task(load)
ns.add_task(watch)
ns.add_task(ls)
