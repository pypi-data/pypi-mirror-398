"""
MarkUs Exam Matcher: __main__.py

Information
===============================
Environment for top-level code (entry point into package).
"""

import os.path
import sys
from argparse import ArgumentParser, BooleanOptionalAction

from .core.char_types import CharType
from .image_processing import read_chars
from .qr_scan import scan_qr


def config_arg_parser() -> ArgumentParser:
    """
    Configure a command line argument parser.
    :return: Command line argument parser.
    """
    # Initialize parser
    parser = ArgumentParser(
        prog="run_scanner.py", description="Predict handwritten characters in rectangular grids."
    )

    # Scan type argument
    parser.add_argument("scan_type", type=str, help="Scan type to be character or QR code")

    # Positional arguments
    parser.add_argument("path", type=str, help="Path to file/directory to scan.")

    # Optional arguments
    parser.add_argument(
        "--char_type",
        choices=["digit", "letter"],
        help="Type of character to classify. Only digits and letters are supported.",
    )
    parser.add_argument(
        "--bulk",
        action=BooleanOptionalAction,
        help="Whether to enable bulk mode for scanning",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Specify whether to run program with debug mode enabled.",
    )

    return parser


if __name__ == "__main__":
    # Parse command line arguments
    parser = config_arg_parser()
    args = parser.parse_args(sys.argv[1:])

    if args.scan_type == "char":
        char_type = CharType.DIGIT if args.char_type == "digit" else CharType.LETTER

        # Make prediction
        pred = read_chars.run(args.path, char_type=char_type, debug=args.debug)
        print(pred)
    elif args.scan_type == "qr":
        if args.bulk:
            filenames = sys.stdin.read().split("\n")
            paths = [
                os.path.join(args.path, filename.strip())
                for filename in filenames
                if filename.strip()
            ]
            scan_qr.scan_qr_codes_from_pdfs(paths)
        else:
            scanned_result = scan_qr.read_qr(args.path)
            print(scanned_result)
    else:
        print("Unknown scan type.")
        sys.exit(1)
