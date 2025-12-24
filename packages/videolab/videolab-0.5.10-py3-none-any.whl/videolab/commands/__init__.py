# Copyright (C) 2025 Kian-Meng, Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Discover and register subcommands."""

import argparse
import importlib
import pkgutil


def discover_and_register(subparsers: argparse._SubParsersAction) -> None:
    """Discover and register subcommands from this package."""
    for _, name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f".{name}", __name__)
        if hasattr(module, "register_subcommand"):
            module.register_subcommand(subparsers)
