"""
MarkUs Exam Matcher: Displaying Elements

Information
===============================
This module defines functions that can be used to visually
display images and contours overlaid on images. It is
useful for debugging.

NOTE: This module requires opencv-python to be installed
instead of opencv-python-headless.
"""

from typing import Tuple

import cv2
import numpy as np


def display_img(img: np.ndarray) -> None:
    """
    Display the image img.

    :param img: Image to display.
    :return: None
    """
    cv2.imshow("Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def display_contour(
    img: np.ndarray, cnt: np.ndarray, colour: Tuple[int, int, int] = (0, 255, 0)
) -> None:
    """
    Display the contour cnt overlaid onto a grayscale image img.

    :param img: Grayscale image to overlay contour onto.
    :param cnt: Contour to display.
    :param colour: RGB tuple defining the colour of the contour.
                   Defaults to green.
    :return: None
    """
    # Display contour
    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    cv2.drawContours(img_color, [cnt], 0, colour, 3)

    # Display the image
    display_img(img_color)
