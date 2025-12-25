# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
"""
Main entrypoint for the script.
"""

import argparse
import sys
from pathlib import Path
from automatic_signature_sheet.generator import generate, get_templates
from automatic_signature_sheet.reader import DefaultReader
from automatic_signature_sheet import __version__


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yass")
    parser.add_argument("--version", action="version", version=__version__)

    parser.add_argument("filename")

    parser.add_argument("-t", "--title", help="Title of the signature sheet")
    parser.add_argument(
        "-s",
        "--size",
        help="Size, in pt, of the signature box (default 50pt). Unit may not be omitted.",
    )
    parser.add_argument(
        "-f",
        "--force",
        help="Force the generation of the file even if the output file exists.",
        action="store_true",
    )
    parser.add_argument(
        "--no-sort",
        help="Prevent sorting using the alphabetical order on the last name.",
        action="store_false",
    )

    parser.add_argument(
        "-i",
        "--ignore-lines",
        type=int,
        default=1,
        help="Number of lines to ignore in the CSV (header(s)). Default: 1.",
    )

    parser.add_argument(
        "--first-name-column",
        type=int,
        default=0,
        help="Column of the first name. Default: 0.",
    )

    parser.add_argument(
        "--last-name-column",
        type=int,
        default=1,
        help="Column of the last name. Default: 1.",
    )

    parser.add_argument(
        "--person-id-column",
        type=int,
        default=2,
        help="Column of the person id.. Use a negative value to ignore person id. Default: 2.",
    )

    parser.add_argument(
        "-T",
        "--template",
        choices=get_templates(),
        default="default.tex",
        type=str,
        help="LaTeX template to use. Default: default.tex",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Force the output name. Default: input name with .pdf",
    )

    return parser


def main():
    """
    Main entrypoint for the YASS script.
    """
    parser = _create_parser()
    args = parser.parse_args()

    if args.output:
        output = Path(args.output)
    else:
        filename_no_extension = "".join(args.filename.split(".")[:-1])
        output = Path(filename_no_extension + ".pdf")

    if output.is_file() and not args.force:
        print(f"{output} already exists. Use -f to force generation.")
        sys.exit(1)

    person_id_column = args.person_id_column if args.person_id_column >= 0 else None

    reader = DefaultReader(
        args.filename,
        first_name_column=args.first_name_column,
        last_name_column=args.last_name_column,
        person_id_column=person_id_column,
        ignore_lines=args.ignore_lines,
        sort=args.no_sort,
    )

    persons = reader.read()

    generate(
        persons,
        title=args.title,
        signature_size=args.size,
        output=output,
        template_name=args.template,
    )


if __name__ == "__main__":
    main()
