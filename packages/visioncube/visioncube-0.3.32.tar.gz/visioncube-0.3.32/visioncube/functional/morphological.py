#!/usr/bin/env python3
from typing import Union, Tuple

import cv2 as cv
import numpy as np

__all__ = [
    'erode',
    'dilate',
    'morph_open',
    'morph_close',
    'morph_gradient',
    'morph_tophat',
    'morph_blackhat',
]


def erode(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    if not isinstance(kernel, np.ndarray):
        ksize = (kernel, kernel) if isinstance(kernel, int) else kernel
        kernel = np.ones(ksize, np.uint8)
    return cv.erode(image, kernel, iterations=iterations)


def dilate(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    if not isinstance(kernel, np.ndarray):
        ksize = (kernel, kernel) if isinstance(kernel, int) else kernel
        kernel = np.ones(ksize, np.uint8)
    return cv.dilate(image, kernel, iterations=iterations)


def _morph(
        op,
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    if not isinstance(kernel, np.ndarray):
        ksize = (kernel, kernel) if isinstance(kernel, int) else kernel
        kernel = np.ones(ksize, np.uint8)
    return cv.morphologyEx(image, op, kernel, iterations=iterations)


def morph_open(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    return _morph(cv.MORPH_OPEN, image, kernel, iterations)


def morph_close(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    return _morph(cv.MORPH_CLOSE, image, kernel, iterations)


def morph_gradient(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    return _morph(cv.MORPH_GRADIENT, image, kernel, iterations)


def morph_tophat(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    return _morph(cv.MORPH_TOPHAT, image, kernel, iterations)


def morph_blackhat(
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: int = 1
) -> np.ndarray:
    return _morph(cv.MORPH_BLACKHAT, image, kernel, iterations)
