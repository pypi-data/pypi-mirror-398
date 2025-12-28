"""
MarkUs Exam Matcher: Box Detection

Information
===============================
This module defines the image processing functions pertaining to
the boxes in an input image.
"""

# TODO: Move sort_contours to a different module


from typing import List

import cv2
import numpy as np

from ..core.display_elements import display_contour, display_img


def get_box_contours(contours: List[np.ndarray], debug: bool = False) -> List[np.ndarray]:
    """
    Get contours representing the boxes that surround each character.

    :param contours: Contours of the version of the original image
                     containing only horizontal and vertical lines.
    :param debug: Specifies whether assertions should be checked.
    :return: List containing box contours sorted in left-to-right order.
    """
    # Only get contours that represent valid boxes where students write
    filtered_contours = _get_box_contours(contours)

    # Sort contours in left-to-right order
    sorted_contours = _sort_contours(filtered_contours, debug=debug)

    # Remove potential erroneous box contours
    sorted_contours = _remove_erroneous_box_contours(sorted_contours)

    return sorted_contours


def get_char_images(
    img: np.ndarray, box_contours: List[np.ndarray], verbose: bool = False, buf: int = 5
) -> List[np.ndarray]:
    """
    Get images of the individual characters that are in the boxes outlined by
    box_contours.

    :param img: Image containing the boxes.
    :param box_contours: Contours of boxes.
    :param verbose: If true, displays contours and characters as they are detected.
    :param buf: Pixels to be cropped off bounding box contours. Used to prevent
                parts of the bounding box borders from being included in the
                image.
    :return: List of images of characters inside boxes (not including the boxes).

    Note: If the order of the characters is desired to be preserved, box_contours
          should be sorted in left-to-right order.
    """
    chars = []

    for contour in box_contours:
        # Get digit inside the box containing it
        x, y, w, h = cv2.boundingRect(contour)
        # TODO: This is slightly crude. Could replace with contour detection to crop edges of boxes.
        char_image = img[y + buf : y + h - buf, x + buf : x + w - buf].copy()

        # If the box is empty, skip it.
        # TODO: Make sure we don't need to handle spaces. If we do, don't just continue here.
        # TODO: If we don't, we should be able to break from the loop here.
        if is_empty_box(char_image, width=w, height=h):
            continue

        if verbose:
            display_contour(img, contour)
            display_img(char_image)

        chars.append(char_image)

    return chars


def is_empty_box(box: np.ndarray, width: int, height: int, threshold: float = 0.001) -> bool:
    """
    Given a box, return whether it is empty.

    :param box: Grayscale, inverted image representing a valid
                box for students to write in.
    :param width: Width of the box.
    :param height: Height of the box.
    :param threshold: Threshold for when normalized number of markings
                      in box causes the box to be considered empty.
    :return: Whether the given box is empty.
    """
    if width == 0 or height == 0:
        return True

    # Get number of markings in box
    markings = cv2.countNonZero(box)

    # Normalize
    normalized = markings / float(width * height)

    # Return whether this normalized amount is considered empty
    return normalized < threshold


def _get_box_contours(contours: List[np.ndarray]) -> List[np.ndarray]:
    """
    Get contours representing the boxes that surround each character.

    :param contours: Contours of the version of the original image
                     containing only horizontal and vertical lines.
    :return: List containing box contours.
    """
    epsilon = 0.1
    box_contours = []

    for contour in contours:
        # Get the dimensions of the bounding rectangle for this contour
        x, y, w, h = cv2.boundingRect(contour)

        # Error of ratio of width and height of shape being a square.
        # For squares, want width / height to be 1
        square_error = abs((float(w) / h) - 1)

        # If the bounding rectangle is approximately a square, add it
        # to the list of contours.
        if square_error < epsilon:
            box_contours.append(contour)

    return box_contours


def _sort_contours(contours: List[np.ndarray], debug: bool = False) -> List[np.ndarray]:
    """
    Sort contours in the left-to-right order in which they appear.

    :param contours: List of contours to sort.
    :param debug: Specifies whether assertions should be checked.
    :return: contours in sorted (left-to-right) order.
    """
    # Get the indices of the contours in the correct order
    sorted_indices = np.argsort([cv2.boundingRect(i)[0] for i in contours])

    # Create list of contours in the sorted order
    sorted_contours = [None] * len(sorted_indices)
    i = 0
    for index in sorted_indices:
        cnt = contours[index]
        sorted_contours[i] = cnt
        i += 1

    if debug:
        for cnt in sorted_contours:
            assert cnt is not None

    return sorted_contours


def _remove_erroneous_box_contours(box_contours: List[np.ndarray]) -> List[np.ndarray]:
    """
    Remove any box contours that should not be in the list of box contours.

    :param box_contours: List of box contours that might contain some contours
                         that are not boxes.
    :return: List of contours that are only box contours.

    Preconditions:
        - box_contours is sorted in left-to-right order.
    """
    filtered_box_contours = []

    # Remove contours that are embedded in another contour
    furthest_x = 0
    for contour in box_contours:
        x, y, w, h = cv2.boundingRect(contour)

        if x + w < furthest_x:
            continue
        else:
            filtered_box_contours.append(contour)
            furthest_x = x + w

    return filtered_box_contours
