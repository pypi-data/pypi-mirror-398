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

"""Utility functions for file path manipulation and common operations."""

import argparse
import functools
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import av
import av.error


def handle_video_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle common video processing exceptions."""

    @functools.wraps(func)
    def wrapper(args: argparse.Namespace) -> None:
        try:
            func(args)
        except av.error.FFmpegError as e:
            logging.exception("Error processing video file: %s", e)
        except FileNotFoundError:
            logging.exception("Input file '%s' not found.", args.input_file)
        except ValueError as e:
            # Catch all unexpected ValueErrors. Log traceback if verbose is enabled.
            logging.exception(
                "A configuration or value error occurred: %s",
                e,
                exc_info=args.verbose,
            )

    return wrapper


def generate_output_filename(
    input_file: str,
    output_file: str | None,
    suffix: str,
) -> Path:
    """Generates an output filename based on the input file and a suffix,
    unless an explicit output file is provided.
    """
    if output_file is not None:
        return Path(output_file)

    input_path = Path(input_file)
    return input_path.with_stem(f"{input_path.stem}_{suffix}")
