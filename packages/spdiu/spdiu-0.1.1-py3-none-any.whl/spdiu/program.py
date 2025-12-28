#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""siu: SpdIU's Invoke Program."""

from pathlib import Path

from invoke import Program, Argument, Collection
from invoke.util import debug
from invoke.exceptions import Exit, CollectionNotFound


class SpdIU(Program):
    """SpdIU Invoke wrapper."""

    def core_args(self):
        """Add SpdIU's extra flags to core args."""
        core_args = super().core_args()
        extra_args = [
            Argument(
                names=("install", "i"),
                kind=str,
                default="",
                optional=True,
                help="Install SpdIU instance files in the current folder.",
            ),
        ]
        return core_args + extra_args

    def parse_core(self, argv) -> None:
        """Add SpdIU's base path installation to core args."""
        super().parse_core(argv)

        if self.args.install.value:
            debug("Saw --install, generating SpdIU tasks.py")
            i_value = self.args.install.value

            p = Path(i_value).resolve() if type(i_value) is str else Path.cwd()
            self.generate_tasks_py(p)
            self.generate_spdio_yaml(p)
            raise Exit

    # NOTE: Overloaded method from invoke.Program 2.2.1,
    # in order to expand the "can't find collection" text.
    # TODO: Maybe check once in a while for changes.
    def load_collection(self) -> None:
        """
        Load a task collection based on parsed core args, or die trying.

        .. versionadded:: 1.0
        """
        start = self.args["search-root"].value
        loader = self.loader_class(  # type: ignore
            config=self.config, start=start
        )
        coll_name = self.args.collection.value

        try:
            module, parent = loader.load(coll_name)
            self.config.set_project_location(parent)
            self.config.load_project()
            self.collection = Collection.from_module(
                module,
                loaded_from=parent,
                auto_dash_names=self.config.tasks.auto_dash_names,
            )
        except CollectionNotFound as e:
            if e.name == "tasks":
                self.print_tasks_py_help()

            raise Exit("Can't find any collection named {!r}!".format(e.name))

    def print_version(self) -> None:
        """Print the version of SpdIU and the underlying Invoke."""
        print(f"SpdIU {self.version} running on Invoke {self.invoke_version}")

    def print_help(self) -> None:
        """Print SpdIU's usage and documentation."""
        usage_suffix = "task1 [--task1-opts] ... taskN [--taskN-opts]"
        if self.namespace is not None:
            usage_suffix = "<subcommand> [--subcommand-opts] ..."
        print("Usage: {} [--core-opts] {}".format(self.binary, usage_suffix))
        print("")
        print("Core options:")
        print("")
        self.print_columns(self.initial_context.help_tuples())
        if self.namespace is not None:
            self.list_tasks()

        self.print_version()

    def print_tasks_py_help(self) -> None:
        """Print help regarding configuring a base dir for an SpdIU instance."""
        print("Seems like you are not in an initialized SpdIU folder.")
        print("siu --install will initialize the current one,")
        print("siu --install [target] will initialize the one provided.")
        # TODO: tasks.py explanation, doc link

    def generate_tasks_py(self, path: Path) -> None:
        """Generate a tasks.py from spdiu/templates/tasks.py."""
        path.mkdir(parents=True, exist_ok=True)

        src = Path(__file__).parent / "templates" / "tasks.py"
        file_path = path / "tasks.py"
        file_path.write_text(src.read_text())

        print(f"Generated {file_path}")

    def generate_spdio_yaml(self, path: Path) -> None:
        """Generate a tasks.py from spdiu/templates/tasks.py."""
        path.mkdir(parents=True, exist_ok=True)
        # src = Path(__file__).parent / "templates" / "spdiu.yaml"

        file_path = path / "spdiu.yaml"
        file_path.touch()

        print(f"Generated {file_path}")

    def __init__(self, *args, invoke_version: str, **kwargs):
        """Add SpdIU variables."""
        self.invoke_version = invoke_version if invoke_version else "unknown"
        super().__init__(*args, **kwargs)
