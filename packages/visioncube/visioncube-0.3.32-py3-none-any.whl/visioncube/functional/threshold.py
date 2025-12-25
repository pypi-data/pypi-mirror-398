#!/usr/bin/env python3

from typing import Tuple

import cv2 as cv
import numpy as np

__all__ = [
    'threshold',
    'threshold_',
    'threshold_otsu',
    'threshold_otsu_',
    'threshold_in_range',
    'threshold_in_range_',
]


def threshold(
        image: np.ndarray,
        thr: int,
        max_value: int = 255,
        invert=False,
        out: np.ndarray = None
) -> np.ndarray:
    return cv.threshold(
        image,
        thresh=thr,
        maxval=max_value,
        type=cv.THRESH_BINARY if not invert else cv.THRESH_BINARY_INV,
        dst=out
    )[1]


def threshold_(image: np.ndarray, thr: int, max_value: int = 255, invert=False) -> np.ndarray:
    return threshold(image, thr, max_value, invert, image)


def threshold_otsu(
        image: np.ndarray,
        max_value: int = 255,
        out: np.ndarray = None
) -> Tuple[float, np.ndarray]:
    return cv.threshold(image, 127, maxval=max_value, type=cv.THRESH_OTSU, dst=out)


def threshold_otsu_(image: np.ndarray, max_value: int = 255) -> Tuple[float, np.ndarray]:
    return threshold_otsu(image, max_value, image)


def threshold_in_range(image: np.ndarray, lower, upper, out: np.ndarray = None) -> np.ndarray:
    return cv.inRange(image, lower, upper, dst=out)


def threshold_in_range_(image: np.ndarray, lower, upper) -> np.ndarray:
    return threshold_in_range(image, lower, upper, image)
