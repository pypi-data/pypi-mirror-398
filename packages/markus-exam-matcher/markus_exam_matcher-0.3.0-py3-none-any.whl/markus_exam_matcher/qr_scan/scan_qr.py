"""
MarkUs Exam Matcher: Reading QR code

Information
===============================
This module defines the function that reads the QR code.
"""

import os.path
import sys

import cv2
import numpy as np
import zxingcpp
from pdf2image import convert_from_path


def read_qr(img_path: str) -> str:
    img = cv2.imread(img_path)
    result = zxingcpp.read_barcode(
        img, try_rotate=False, try_downscale=False, formats=zxingcpp.QRCode
    )

    if result is None:
        print("Could not find any barcode.", file=sys.stderr)
        sys.exit(1)
    else:
        return result.text


def scan_qr_codes_from_pdfs(paths: list[str], dpi: int = 150, top_fraction: float = 0.2) -> None:
    """Scan QR codes from the provided single-page PDFs, checking only the top portion of each page.

    Print the QR codes scanned from each page (one per page).
    """
    for pdf_path in paths:
        pdf_filename = os.path.basename(pdf_path)
        try:
            pages = convert_from_path(pdf_path, dpi=dpi, fmt="jpeg", single_file=True)
            page = pages[0]

            # Crop top fraction of the image
            width, height = page.size
            cropped = page.crop((0, 0, width, int(height * top_fraction)))

            # Detect and decode
            data = zxingcpp.read_barcode(
                cropped, try_rotate=False, try_downscale=False, formats=zxingcpp.QRCode
            )
            if data:
                print(f'{pdf_filename},"{data.text}"')
            else:
                print(f'{pdf_filename},""')
        except Exception:
            print(f'{pdf_filename},""')
