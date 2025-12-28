#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""SpdIU Dev tools collection."""

from invoke import task

from .display import recurse_dump


@task
def print_config(c):
    """Get a pretty recursive dump of the invoke config object."""
    print("Here's the whole invoke config as seen by the tasks:")
    recurse_dump(c, c.config.__dict__["_config"], "config")
