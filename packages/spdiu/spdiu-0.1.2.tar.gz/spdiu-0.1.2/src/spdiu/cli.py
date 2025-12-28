#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""siu: SpdIU's template installer and invoke wrapper."""

from importlib import metadata
from invoke.main import __version__ as invoke_version

from spdiu.config import SpdIUConfig
from spdiu.program import SpdIU


__version__ = metadata.version("spdiu")


def main() -> None:
    """Call SpdIU's custom Invoke program."""
    program = SpdIU(
        version=__version__,
        name="SpdIU",
        binary="s[pd]iu",
        binary_names=["siu", "spdiu"],
        config_class=SpdIUConfig,
        invoke_version=invoke_version,
    )

    program.run()
