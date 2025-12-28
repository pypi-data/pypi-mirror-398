"""
MarkUs Exam Matcher: Image Transformations

Information
===============================
This module defines functions that can be used to transform an image. It
also defines a class that can be used as a pipeline to perform multiple
transformations sequentially.
"""

import math
from typing import Callable, List

import cv2
import numpy as np
from scipy import ndimage


class ImageTransform:
    """
    Defines a transformation pipeline that can be called on an image
    represented by a numpy ndarray.

    Instance Variables:
        - callbacks: List of transformation functions that should be called
                     in order on an image. Each function must take in only
                     one parameter (the np.ndarray image) and return only
                     an np.ndarray image.
    """

    callbacks: List[Callable]

    def __init__(self, callbacks: List[Callable]):
        self.callbacks = callbacks

    def perform_on(self, img):
        """
        Perform the transformation specified by this instance. The transformations
        are called in the order specified by the callbacks list.

        :param img: np.ndarray representing the image to perform the transformation
                    on.

        :return: The image as an np.ndarray after the transformations have been
                 applied.
        """
        for callback in self.callbacks:
            img = callback(img)

        return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """
    Convert an image to grayscale.

    :param img: Image to convert.
    :return: img in grayscale form.
    """
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def to_inverted(img: np.ndarray) -> np.ndarray:
    """
    Invert an image.

    :param img: Image to invert.
    :return: img after being inverted.
    """
    _, threshed = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return threshed


def to_closed(img: np.ndarray) -> np.ndarray:
    """
    Perform closing on an image. Closing is useful for "closing" small
    holes in any numbers or letters. It also slightly thickens the
    contours, which makes digits more similar to MNIST dataset digits.

    :param img: Image to close.
    :return: img after being closed.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img = cv2.dilate(img, kernel, iterations=2)
    img = cv2.erode(img, kernel, iterations=2)
    return img


def thicken_lines(img: np.ndarray) -> np.ndarray:
    """
    Thicken the lines of an inverted, grayscale image.

    :param img: Grayscale, inverted image to thicken.
    :return: img after its lines are thickened.
    """
    # Thicken lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.dilate(img, kernel, iterations=2)


def get_lines(img: np.ndarray, kernel_length: int = 50) -> np.ndarray:
    """
    Get an image containing only horizontal and vertical lines in the input image.

    :param img: Grayscale, inverted image to get lines from.
    :param kernel_length: Length of horizontal and vertical kernels. It is recommended
                          to keep this value at its default value.
    :return: Image containing only horizontal and vertical lines from the original image.
    """
    # Create structuring elements (kernels)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))

    # Apply kernels to get vertical and horizontal masks
    # These masks contain only vertical and horizontal lines, respectively
    vertical_mask = cv2.morphologyEx(img, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
    horizontal_mask = cv2.morphologyEx(img, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    # Add masks together to get new mask containing both horizontal and vertical lines
    img_mask = cv2.bitwise_or(horizontal_mask, vertical_mask)
    return img_mask


def get_best_shift(img):
    """
    Finds x and y units to shift the image by so it is centered.
    :param img: input image.
    :return: best x and y units to shift by.

    Disclaimer: Function written by the authors at https://opensourc.es/blog/tensorflow-mnist/.
    """
    cy, cx = ndimage.center_of_mass(img)

    rows, cols = img.shape
    shiftx = np.round(cols / 2.0 - cx).astype(int)
    shifty = np.round(rows / 2.0 - cy).astype(int)

    return shiftx, shifty


def shift(img, sx, sy):
    """
    Shifts the image by the given x and y units.
    :param img: input image.
    :param sx: x units to shift by.
    :param sy: y units to shift by.
    :return: shifted image.

    Disclaimer: Function written by the authors at https://opensourc.es/blog/tensorflow-mnist/.
    """
    rows, cols = img.shape
    M = np.float32([[1, 0, sx], [0, 1, sy]])
    shifted = cv2.warpAffine(img, M, (cols, rows))
    return shifted


def process_num(gray):
    """
    Process an input image of a handwritten number in the same way the MNIST dataset was processed.
    :param gray: the input grayscaled image.
    :return: the processed image.

    Disclaimer: Function written by the authors at https://opensourc.es/blog/tensorflow-mnist/.
    """
    gray = cv2.resize(gray, (28, 28))

    # strip away empty rows and columns from all sides
    while np.sum(gray[0]) == 0:
        gray = gray[1:]
    while np.sum(gray[:, 0]) == 0:
        gray = np.delete(gray, 0, 1)
    while np.sum(gray[-1]) == 0:
        gray = gray[:-1]
    while np.sum(gray[:, -1]) == 0:
        gray = np.delete(gray, -1, 1)

    # reshape image to be 20x20
    rows, cols = gray.shape
    if rows > cols:
        factor = 20.0 / rows
        rows = 20
        cols = int(round(cols * factor))
    else:
        factor = 20.0 / cols
        cols = 20
        rows = int(round(rows * factor))
    gray = cv2.resize(gray, (cols, rows))

    # pad the image to be 28x28
    colsPadding = (int(math.ceil((28 - cols) / 2.0)), int(math.floor((28 - cols) / 2.0)))
    rowsPadding = (int(math.ceil((28 - rows) / 2.0)), int(math.floor((28 - rows) / 2.0)))
    gray = np.pad(gray, (rowsPadding, colsPadding), "constant")

    # shift the image is the written number is centered
    shiftx, shifty = get_best_shift(gray)
    gray = shift(gray, shiftx, shifty)
    return gray
