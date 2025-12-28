#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
SpdIU Cheats task collection.

These tasks all work on the active game data.
Make a save before using them.

-g, --game picks a game, where applicable.
It defaults to the latest modified game if not supplied.
"""

from invoke import task, Collection

from ..model import Profile, Item
from ..util import path

ns = Collection("cheats")


@task
def gold(c, game=None, number="10000"):
    """Set your Gold! -n --number [amount], default: 10000."""
    cfg = c.config.spdiu
    ap = Profile(path(c, cfg.game.data))

    g = ap.get_game(game) if game else ap.games[0]
    gd = g.get_dat("game.dat")

    print(f"{cfg.i.disc_a} {ap.name} {cfg.i.game} {g.name}")
    print(f"Previous Gold: {gd['gold']}")

    gd["gold"] = int(number)
    g.set_dat("game.dat", gd)

    print(f"{cfg.i.data} Gold set to {number}!")


@task
def energy(c, game=None, number="1000"):
    """Set your Alchemical Energy! -n --number [amount], default: 1000."""
    cfg = c.config.spdiu
    ap = Profile(path(c, cfg.game.data))

    g = ap.get_game(game) if game else ap.games[0]
    gd = g.get_dat("game.dat")

    print(f"{cfg.i.disc_a} {ap.name} {cfg.i.game} {g.name}")
    print(f"Previous Alchemical Energy: {gd['energy']}")

    gd["energy"] = int(number)
    g.set_dat("game.dat", gd)

    print(f"{cfg.i.data} Alchemical Energy set to {number}!")


@task
def bones(c, package="", hero="", display=False):
    """Set your bones. 'siu -h cheat.bones' for options.

    -p, --package to pick your package, or you'll just get food.

    plate: Your one and only armor
    blade: Be one with the shadows
    wealth: Yog can wait
    reroll: Make your own seed
    regrowth: Stardew Pixel Dungeon
    zip: Walls are just a suggestion

    -h, --hero to pick, or a hero that fits your package will be assigned.

    i.e. WARRIOR, MAGE, ROGUE, HUNTRESS, DUELIST, CLERIC
    Classes are uppercase in game files, but you can enter them lowercase here.

    -d --display will only display the current bones without editing game files.

    Read through the task code, it's easy to adapt in your own local task.
    """
    cfg = c.config.spdiu
    ap = Profile(path(c, cfg.game.data))

    namespace = ".".join((cfg.game.ns, "items"))

    if package == "plate":
        hero_class = "WARRIOR"
        item = "armor.PlateArmor"

        # no auguments in bones :(
        # aug = 'armor.glyphs.Thorns'

        i = Item(
            {
                "__className": ".".join((namespace, item)),
                "level": 3,
                "mastery_potion_bonus": True,
            }
        )

    elif package == "blade":
        hero_class = "DUELIST"
        item = "weapon.melee.AssassinsBlade"
        i = Item(
            {
                "__className": ".".join((namespace, item)),
                "level": 3,
                "mastery_potion_bonus": True,
            }
        )

    elif package == "wealth":
        hero_class = "ROGUE"
        item = "rings.RingOfWealth"
        i = Item(
            {
                "__className": ".".join((namespace, item)),
                "level": 3,
            }
        )

    elif package == "reroll":
        hero_class = "CLERIC"
        item = "scrolls.ScrollOfTransmutation"
        i = Item(
            {
                "__className": ".".join((namespace, item)),
                "quantity": 6,
            }
        )

    elif package == "regrowth":
        hero_class = "HUNTRESS"
        item = "wands.WandOfRegrowth"
        i = Item(
            {
                "__className": ".".join((namespace, item)),
                "level": 3,
            }
        )

    elif package == "zip":
        hero_class = "ROGUE"
        item = "artifacts.EtherealChains"
        i = Item(
            {
                "__className": ".".join((namespace, item)),
            }
        )

    else:
        hero_class = "MAGE"
        item = "food.Berry"
        # item = 'food.Food'
        i = Item(
            {
                "__className": ".".join((namespace, item)),
                "quantity": 12,
            }
        )

    if hero:
        hero_class = hero.upper()

    bones = {
        "item": i.item,
        "hero_class": hero_class,
        "level": 1,
        "branch": 0,
    }

    if display:
        print(ap.get_dat("bones.dat"))
        return

    ap.set_dat("bones.dat", bones)

    print(f"{cfg.i.disc_a} {ap.name} {cfg.i.data} Profile data")
    print("A Small Package of Value Will Come to You, Shortly")


@task
def consumables(c, game=None):
    """
    Return all consumable identities. -g --game [game] to pick a game.

    Bullet indicators show whether a consumable is known or not.
    """
    cfg = c.config.spdiu
    ap = Profile(path(c, cfg.game.data))

    g = ap.get_game(game) if game else ap.games[0]
    gd = g.get_dat("game.dat")

    labels = {k: v for k, v in gd.items() if "_label" in k}
    potions = {k: v for k, v in labels.items() if "PotionOf" in k}
    rings = {k: v for k, v in labels.items() if "RingOf" in k}
    scrolls = {k: v for k, v in labels.items() if "ScrollOf" in k}

    print(f"{cfg.i.disc_a} {ap.name} {cfg.i.game} {g.name}")
    print(f"{cfg.bullet_a}: known | {cfg.bullet_b}: not known")

    print(f"\n {cfg.i.data} Potions")
    for k, v in potions.items():
        iclass = k.split("_")[0]
        known = gd[iclass + "_known"]
        name = iclass[len("PotionOf") :]
        bullet = cfg.bullet_a if known else cfg.bullet_b

        print(f"{bullet}{name}: {v}")

    print(f"\n {cfg.i.data} Rings")
    for k, v in rings.items():
        iclass = k.split("_")[0]
        known = gd[iclass + "_known"]
        name = iclass[len("RingOf") :]
        bullet = cfg.bullet_a if known else cfg.bullet_b

        print(f"{bullet}{name}: {v}")

    print(f"\n {cfg.i.data} Scrolls")
    for k, v in scrolls.items():
        iclass = k.split("_")[0]
        known = gd[iclass + "_known"]
        name = iclass[len("ScrollOf") :]
        bullet = cfg.bullet_a if known else cfg.bullet_b

        print(f"{bullet}{name}: {v}")


ns.add_task(gold)
ns.add_task(energy)
ns.add_task(bones)
ns.add_task(consumables)
