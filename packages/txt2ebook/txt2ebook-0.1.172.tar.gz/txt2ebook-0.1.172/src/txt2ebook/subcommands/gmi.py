# Copyright (c) 2021,2022,2023,2024,2025 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""gmi subcommand."""

import argparse
import logging
import sys

from txt2ebook.exceptions import InputError
from txt2ebook.formats.gmi import GmiWriter
from txt2ebook.subcommands.parse import run as parse_txt

logger = logging.getLogger(__name__)


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    gmi_parser = subparsers.add_parser(
        "gmi",
        help="generate ebook in Gemtext format",
    )

    gmi_parser.set_defaults(func=run)

    gmi_parser.add_argument(
        "input_file",
        nargs=None if sys.stdin.isatty() else "?",  # type: ignore
        type=argparse.FileType("rb"),
        default=None if sys.stdin.isatty() else sys.stdin,
        help="source text filename",
        metavar="TXT_FILENAME",
    )

    gmi_parser.add_argument(
        "output_file",
        nargs="?",
        default=None,
        help="converted ebook filename (default: 'TXT_FILENAME.md')",
        metavar="EBOOK_FILENAME",
    )

    gmi_parser.add_argument(
        "-sp",
        "--split-volume-and-chapter",
        default=False,
        action="store_true",
        dest="split_volume_and_chapter",
        help=(
            "split volume or chapter into separate file and "
            "ignore the --overwrite option"
        ),
    )

    gmi_parser.add_argument(
        "--toc",
        default=False,
        action=argparse.BooleanOptionalAction,
        dest="with_toc",
        help="add table of content",
    )

    gmi_parser.add_argument(
        "-op",
        "--open",
        default=False,
        action="store_true",
        dest="open",
        help="open the generated file using default program",
    )

    gmi_parser.add_argument(
        "-ff",
        "--filename-format",
        dest="filename_format",
        type=int,
        default=None,
        help=(
            "the output filename format "
            "(default: TXT_FILENAME [EBOOK_FILENAME])\n"
            "1 - title_authors.EBOOK_EXTENSION\n"
            "2 - authors_title.EBOOK_EXTENSION"
        ),
        metavar="FILENAME_FORMAT",
    )

    gmi_parser.add_argument(
        "-ps",
        "--paragraph_separator",
        dest="paragraph_separator",
        type=lambda value: value.encode("utf-8").decode("unicode_escape"),
        default="\n\n",
        help="paragraph separator (default: %(default)r)",
        metavar="SEPARATOR",
    )


def run(args: argparse.Namespace) -> None:
    """Run md subcommand.

    Args:
        config (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    input_sources = []

    if args.input_file:
        # File path(s) were explicitly provided on the command line
        input_sources.append(args.input_file)
    elif not sys.stdin.isatty():
        # No file path provided, check for piped input
        input_sources.append(sys.stdin)
    else:
        logger.error("No input files provided.")
        raise InputError("No input files provided.")

    if len(input_sources) > 1 and args.output_file:
        msg = (
            "Cannot specify a single output file when "
            "processing multiple input files."
        )
        logger.error(msg)
        raise InputError(msg)

    for i, current_input_stream in enumerate(input_sources):
        # ensures that `input_file` and `output_file` are correctly isolated
        current_file_args = argparse.Namespace(**vars(args))
        current_file_args.input_file = current_input_stream

        # if an explicit output_file was provided, it must apply to the first
        # input
        if i > 0 and args.output_file:
            current_file_args.output_file = None

        book, langconf = parse_txt(current_file_args)
        writer = GmiWriter(book, current_file_args, langconf)
        writer.write()

        # close the file stream if it was opened by argparse.FileType and is
        # not sys.stdin.
        if current_input_stream is not sys.stdin:
            current_input_stream.close()
