#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
SpdIU Display task collection.

Tasks that query and display game data.

By convention, where applicable:
-s, --slot is used to select a slot. Defaults to the active data.
-g, --game to pick a specific game in a slot, defaults to the latest modified.
"""

from time import strftime

from invoke import Collection, task, terminals

from ..util import path
from ..model import Profile, Slots


ns = Collection("display")


def tag_class(c, object_name):
    """Try to separate the class name from known namespaces.

    Returns a dict with:
    {"namespace" str, "class" str, "vanilla" bool, "icon" str}

    If the namespace was not known, the object name is returned
    as "class", and the "namespace" field is empty.
    """
    cfg = c.config.spdiu

    vanilla = "com.shatteredpixel.shatteredpixeldungeon"
    namespaces = set([vanilla])
    namespaces.add(cfg.game.ns)

    tagged = {}

    found = False
    for ns in namespaces:
        if ns in object_name:
            tagged["class"] = object_name[len(ns) + 1 :]
            tagged["namespace"] = ns

            if ns == vanilla:
                tagged["vanilla"] = True
                tagged["icon"] = cfg.i.game
            else:
                tagged["vanilla"] = False
                tagged["icon"] = cfg.i.fork
            found = True
            break

    if not found:
        tagged["class"] = object_name
        tagged["namespace"] = ""
        tagged["vanilla"] = False
        tagged["icon"] = cfg.i.unknown

        w = cfg.i.warning
        print(f"{w} Unknown namespace. Add it to your config! {w}")

    return tagged


def recurse_dump(c, dump, title, depth=None, silent=False, breadcrumb=[]):
    """
    Explore a dat file, printing merrily along the way.

    Accepts any data type, will recurse into lists and dicts.

    It returns a flat list of tuples for every value in the structure:
    (breadcrumb: list, title: str, d_type: str, game_class: str, summary: str)

    By default, it pretty prints the values. silent=True to just get the list.
    """
    cfg = c.config.spdiu

    d_breadcrumb = ".".join(breadcrumb)
    d_type = type(dump).__name__
    d_title = f"{title} <{d_type}>"
    try:
        d_icon = cfg.i[d_type]
    except KeyError:
        d_icon = cfg.i.package

    game_class = ""

    if d_type == "dict" and "__className" in dump:
        tag = tag_class(c, dump["__className"])
        summary = f"{tag['icon']} {tag['class']}, {len(dump)} values"

    elif d_type == "str" and len(dump.split(".")) >= 3 and " " not in dump:
        tag = tag_class(c, dump)
        summary = f"{tag['icon']} {tag['class']}"

    elif d_type in ("list", "dict"):
        summary = f"{len(dump)} values"

    else:
        summary = str(dump)

    results = [(breadcrumb, title, d_type, game_class, summary)]

    if not silent:
        lpad = "  " * len(breadcrumb)
        newline = "\n" if d_type in ("list", "dict") and len(dump) > 0 else ""
        print(newline + lpad + f"{d_breadcrumb} {d_title} {d_icon}: {summary}")

    breadcrumb_next = breadcrumb + [title]

    # Got our line, now to dig deeper
    if depth is not None:
        if depth == 0:
            return results
        else:
            depth += -1

    if d_type == "dict":
        for k, v in dump.items():
            results += recurse_dump(c, v, k, depth, silent, breadcrumb_next)

    elif d_type == "list":
        for idv, v in enumerate(dump):
            idv_title = f"[{str(idv)}]"
            results += recurse_dump(c, v, idv_title, depth, silent, breadcrumb_next)

    return results


@task(optional=["game"])
def dump(c, slot="", game="", file="", entity="", levels=None):
    """Display all variables in a game "dat" file recursively.

    -e, --entity [object] can narrow down the display
    to a specified entity in the dat.

    You can specify dictionaries and lists with dot syntax.
        i.e. hero.inventory.2

    -l, --levels [number] limits the depth the task will recurse.
    When unset, the task will print the whole entity requested.

    -s, --slot [slot] will pick a save slot.
    If not provided, it defaults to the active data.

    -g, --game indicates a game dat file.
    If not provided, the task will look for a user profile dat.

    It accepts an optional argument of a game name, while
    used as a flag it defaults to the latest modified game.

    -f, --file [file] will look for a filename in game or profile folder.
    It defaults to "rankings.dat" for profiles, and "game.dat" for games.
    """
    cfg = c.config.spdiu

    if not slot:
        p = Profile(path(c, cfg.game.data))
        selection = f"{cfg.i.disc_a} {p.name}"
    else:
        s = Slots(path(c, cfg.dirs.slots), ["manual", "auto", "backup"])
        p = s.get_slot(slot)
        selection = f"{cfg.i.disc_b} {p.name}"

    # --game: True means latest, "" means unset.
    if game:
        g = p.games[0] if game is True else p.get_game(game)
        file = file if file else "game.dat"
        parent = g
        selection += f" {cfg.i.game} {g.name}"

    else:
        file = file if file else "rankings.dat"
        parent = p

    try:
        dump = parent.get_dat(file)

    except FileNotFoundError:
        return

    # --entity: parse dot syntax and dig
    if not entity:
        name = f'{cfg.i.inspect} "{file}"'
        title = f"Displaying the complete {cfg.i.data} {file}"

    else:
        for item in entity.split("."):
            # Try to cast it as a list index first
            try:
                item = int(item)
                dump = dump[item]
                continue
            except IndexError:
                print(f"Index {item} out of range.")
                return
            except (ValueError, KeyError):
                pass

            try:
                dump = dump[item]
            except KeyError:
                print(f"Entity {entity} not found.")
                return

        name = f"{entity.split('.')[-1]} {cfg.i.inspect}"
        title = f"Inspecting {cfg.i.inspect} {entity} in {cfg.i.data} {file}"

    # Graphic design is my passion
    width = terminals.pty_size()[0]
    border = "<><>"
    line = "--|--"
    filler = line * int((width - (2 * len(border))) / len(line))
    rest = width % 5
    lpad = (int(rest / 2) + 1 if rest % 2 else int(rest / 2)) * " "
    separator = f"{lpad}{border}{filler}{border}"

    pad_selection = int((width - len(selection)) / 2) * " " + selection
    pad_title = int((width - len(title)) / 2) * " " + title

    print(separator)
    print(pad_title)
    print(pad_selection)
    print(separator, "\n")

    depth = int(levels) if levels else None
    recurse_dump(c, dump, name, depth)

    print()
    print(separator)
    print(pad_title)
    print(pad_selection)
    print(separator, "\n")


# Object summaries
def _summarize_record(record):
    """Print a brief summary of a rankings record.

    Accepts a dict of serialized data from a
    com.shatteredpixel.shatteredpixeldungeon.Rankings$Record.

    Only looks for 'Rankings$Record' to enable fork compatibility.
    """
    # __className <str>: Java class for ranking records
    if record["__className"].split(".")[-1] != "Rankings$Record":
        return

    # date <str> 'YY-MM-DD' completion date
    # win <bool>
    # ascending <bool>
    # depth <int>

    # class <str> Hero class
    # level <int> Hero level
    # cause <str> Cause of death, items.Amulet on win or ascension
    # score <int> Run score

    title_line = f"{record['date']}  "
    title_line += f"l{record['level']:<2} {record['class']:<10}"
    title_line += f"{record['score']:>9,}  "

    if record["win"] and record["ascending"]:
        title_line += "Ascended with the Amulet."
    elif record["win"]:
        title_line += "Obtained the Amulet."
    else:
        title_line += f"Died by {record['cause'].split('.')[-1]} "
        title_line += f"on depth {record['depth']}."

    # tier <int> 1 to 6, depending on dungeon region progress

    # daily <bool>
    # custom_seed <str> empty on random seed runs

    # version <str> Game version used for the run
    # gameID <str> some hashed identifier?

    # gameData <dict>

    print(title_line)


@task(default=True)
def slot(c, slot=None, game=None):
    """Display details for a save slot. -s [slot] or -a for the active data."""
    cfg = c.config.spdiu
    if slot is None:
        slot = cfg.default_slot

    if not slot:
        s_dir = path(c, cfg.game.data)
        p = Profile(s_dir)
        print(f"Showing {cfg.i.disc_a} Active game data")

    else:
        slots = Slots(path(c, cfg.dirs.slots), ["manual", "auto", "backup"])
        p = slots.get_slot(slot)
        print(f"Showing details for slot {cfg.i.disc_b} {slot}")

    print("\nProfile information:")

    # Settings
    settings = p.get_settings()
    print(f"{cfg.bullet_b}{len(settings)} options set.")

    # Badges
    badges = p.get_dat("badges.dat")
    if badges:
        print(f"{cfg.bullet_b}{len(badges['badges'])} badges and related unlocks.")

    # Bones
    bones = p.get_dat("bones.dat")
    if bones:
        if "hero_class" not in bones:
            print(f"{cfg.bullet_b}No character bones are set to spawn.")

        else:
            hero = bones["hero_class"]
            lvl = bones["level"]
            br = bones["branch"]

            print(f"{cfg.bullet_a}{hero} bones at level {lvl}, branch {br}.")

    # Journal
    journal = p.get_dat("journal.dat")
    if journal:
        # NOTE: Entries appear in the file only after they've been unlocked,
        #       So total numbers are not represented in the save.

        # bestiary_classes <list> [class name] bestiary class index
        # bestiary_seen <list> [all True] bestiary seen status
        # bestiary_encounters <list> [int] bestiary encounter count

        b_seen = len(journal["bestiary_seen"])
        print(f"{cfg.bullet_b}Bestiary: {b_seen} mobs seen.")

        # catalog_uses <list> 297 values.
        # catalog_seen <list> 297 values.
        # catalog_classes <list> 297 values.

        c_seen = len(journal["catalog_seen"])
        print(f"{cfg.bullet_b}Catalog: {c_seen} items seen.")

        # documents <dict>
        # {<str> CATEGORY: {<str> note name: <int> 1 unread or 2 read }}.
        doc_count = 0
        for k, v in journal["documents"].items():
            doc_count += len(v)

        print(f"{cfg.bullet_b}{doc_count} tutorials and notes discovered.")

    # Rankings
    ranks = p.get_dat("rankings.dat")
    if ranks:
        # won <int>: number of wins
        won = int(ranks["won"])
        # total <int>: total games played
        total = int(ranks["total"])

        print(f"{cfg.bullet_a}{won} games won out of {total} played.")

        # records <list> [dict Rankings$Record]
        # latest <int> index of latest game in 'records'

        # assertion: if latest is unset there's no records
        if "latest" not in ranks:
            return

        print(f"{cfg.bullet_a}{len(ranks['records'])} stored ranking records.")

        latest = ranks["records"][int(ranks["latest"])]

        print(f"{cfg.bullet_b}Latest run:")
        print("    ", end="")

        _summarize_record(latest)

        # latest_daily <dict Rankings$Record>
        # daily_history_dates <list> [int secs since epoch]
        # daily_history_scores <list> [int score]

        # assertion: no daily has ever been played
        if "latest_daily" not in ranks:
            return

        print(f"{cfg.bullet_b}Latest daily:")
        print("    ", end="")

        _summarize_record(ranks["latest_daily"])

    print(f"\n{cfg.i.game} {len(p.games)} games found:")

    for g in reversed(p.games):
        bullet = cfg.bullet_a if g == p.games[0] else cfg.bullet_b
        time = strftime(cfg.time_format, g.ts)
        print(f"{bullet} {time} {cfg.i.game} {g.name}")


ns.add_task(slot)
ns.add_task(dump)
