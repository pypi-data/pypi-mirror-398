#!/usr/bin/env python3

import numpy as np
from matplotlib import pyplot as plt

__all__ = [
    'plot_subplot',
    'plot_image',
    'plot_show',
]


def plot_subplot(*args):
    plt.subplot(*args)


def plot_image(image: np.ndarray):
    plt.imshow(image)


def plot_show():
    plt.show()
