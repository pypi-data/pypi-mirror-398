"""
MarkUs Exam Matcher: CNN

Information
===============================
This module defines the structures and functions required
to run a CNN on a series of input images to predict the
characters written in the images. It is trained on the
MNIST dataset for numbers, and the EMNIST dataset for
letters.
"""

from __future__ import print_function

import os
import os.path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms

# Transformation pipeline to make images more similar to
# (E)MNIST dataset format
TRANSFORM = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ]
)


class Net(nn.Module):
    """
    Neural network architecture for reading handwritten characters.
    """

    def __init__(self, num_output):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4 * 4 * 50, 500)
        self.fc2 = nn.Linear(500, num_output)

    def forward(self, x):
        """
        Perform a forward pass.
        """
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        x = x.view(-1, 4 * 4 * 50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


def numeric_model():
    """
    Load a trained CNN for predicting numbers. CNN was trained on
    the MNIST dataset.
    :return: CNN model for predicting numbers.
    """
    model = Net(10)
    model.load_state_dict(
        torch.load(os.path.join(os.path.dirname(__file__), "model_numeric_epoch_24.pth"))
    )
    return model


def char_model():
    """
    Load a trained CNN for predicting letters. CNN was trained on
    the EMNIST dataset.
    :return: CNN model for predicting letters.
    """
    model = Net(26)
    model.load_state_dict(torch.load(os.path.join(os.path.dirname(__file__), "emnist_cnn.pt")))
    return model


def get_num(tmp_dir, img_dir):
    """
    Read a series of images from a directory and predict the
    digits in the images. The images should contain only digits.

    :return: String representing the prediction of the
    digits in the images, preserving order.
    """
    # Load numeric model
    model = numeric_model()

    # Verify image directory exists
    if not len(os.listdir(img_dir)):
        return

    # Load data to test
    test_data = datasets.ImageFolder(tmp_dir, transform=TRANSFORM)

    # Generate predictions
    out = ""
    for images, labels in test_data:
        images = images.unsqueeze(0)
        output = model(images)
        pred = output.argmax(dim=1, keepdim=True)
        out += str(pred.data[0].item())

    return out


def get_name(tmp_dir, img_dir, spaces):
    """
    Read a series of images from a directory and predict the
    letters in the images. The images should contain only
    letters.

    :return: String representing the prediction of the
    letters in the images, preserving order.
    """
    # Load letter model
    model = char_model()

    # Verify image directory exists
    if not len(os.listdir(img_dir)):
        return

    # Load data to test
    test_data = datasets.ImageFolder(tmp_dir, transform=TRANSFORM)

    # Generate predictions
    out = ""
    for images, labels in test_data:
        images = images.unsqueeze(0)
        output = model(images)
        pred = output.argmax(dim=1, keepdim=True)
        out += chr(pred.data[0].item() + 97)

    return _insert_spaces(out, spaces).upper()


def _insert_spaces(out, spaces):
    """
    Insert spaces into the string specified by out.

    :param out: String to insert spaces into.
    :param spaces: List of indices specifying where spaces
                   should go in the output string.
    :return: out with spaces added to it, removing any trailing
             spaces.
    """
    for s in spaces:
        out = out[: s - 1] + " " + out[s - 1 :]
    return out.strip()
