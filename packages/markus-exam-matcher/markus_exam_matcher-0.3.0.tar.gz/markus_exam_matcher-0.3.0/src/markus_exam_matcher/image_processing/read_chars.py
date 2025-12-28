"""
MarkUs Exam Matcher: Reading Characters

Information
===============================
This module defines the image processing functions to extract
characters from the boxes they are contained in, and to interpret
these characters as strings.
"""

# TODO: Create debug class and set debug modes for level of verbosity.

import tempfile
from typing import List

import cv2
import numpy as np

# TODO: Ask about convention for importing this
from .._cnn.cnn import get_num
from ..core.char_types import CharType
from ..core.display_elements import display_img
from ..image_processing import image_transformation_pipelines
from ..image_processing.box_detection import get_box_contours, get_char_images


def read_img(img_path: str) -> np.ndarray:
    """
    Read an input image.

    :param img_path: Path to image.
    :return: np.ndarray representing the image specified by
             img_path.
    """
    return cv2.imread(img_path)


def predict_chars_from_images(imgs: List[np.ndarray], char_type: CharType) -> str:
    """
    Return a string representing the characters written in imgs.

    :param imgs: List of images represented as np.ndarray's, where each
                 image represents a character.
    :param char_type: The type of characters that imgs represent.
    :return: String representing the characters written in imgs. Order
             is preserved.
    """
    # Write characters to a temporary directory and run CNN on images
    # in this directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        with tempfile.TemporaryDirectory(dir=tmp_dir) as img_dir:
            _write_images_to_dir(imgs, img_dir)

            if char_type == CharType.DIGIT:
                return get_num(tmp_dir, img_dir)
            else:
                # TODO: Implement reading letters
                assert False


def run(img_path: str, char_type: CharType, debug: bool = False) -> str:
    """
    Run the prediction algorithm on the image located at img_path.

    :param img_path: Path to image to detect characters from.
    :param char_type: Specifies whether the image contains digits or
                      letters.
    :param debug: Specifies whether to run the function in debug mode.
                  Debug mode gives visuals of the algorithm at certain
                  points and checks assertions.
    :return: String representing the characters written in the image, in
             left-to-right order.

    Preconditions:
        - img_path points to an image that has the characters to be detected
          surrounded by boxes.
    """
    # Read input image
    img = read_img(img_path)

    # Perform image pre-processing pipeline on img to get img in the
    # form required by most image processing functions.
    img = image_transformation_pipelines.PREPROCESSING_PIPELINE.perform_on(img)

    if debug:
        display_img(img)

    # Get an image containing only horizontal and vertical lines of img
    lines_of_img = image_transformation_pipelines.BOX_DETECTION_PIPELINE.perform_on(img)

    if debug:
        display_img(lines_of_img)

    # Get contours
    contours, _ = cv2.findContours(lines_of_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Only get contours that represent valid boxes where students write
    box_contours = get_box_contours(contours, debug=debug)

    # Get characters in order using these sorted boxes contours
    chars = get_char_images(img, box_contours, verbose=debug)

    # Transform images to look similar to images that the CNN was trained on
    # ((E)MNIST)
    if char_type == CharType.DIGIT:
        dataset_transform_pipeline = image_transformation_pipelines.MNIST_NUM_PIPELINE
    else:
        dataset_transform_pipeline = image_transformation_pipelines.MNIST_LETTER_PIPELINE

    for i in range(len(chars)):
        chars[i] = dataset_transform_pipeline.perform_on(chars[i])

        if debug:
            display_img(chars[i])

    # Write digits to a temporary directory and run CNN on images
    # in this directory
    return predict_chars_from_images(chars, char_type)


def _write_images_to_dir(imgs: List[np.ndarray], dir: str) -> None:
    """
    Write images to a directory.

    :param imgs: List of images to write to directory.
    :param dir: Directory to write the images to.
    :return: None
    """
    for i in range(len(imgs)):
        img = imgs[i]
        # Write image to directory
        cv2.imwrite(dir + "/" + str(i).zfill(2) + ".png", img)
