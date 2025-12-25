#!/usr/bin/env python3

from typing import Union, Tuple

import cv2 as cv
import numpy as np

__all__ = [
    'gaussian_filter',
    'gaussian_filter_',
    'median_filter',
    'median_filter_',
    'bilateral_filter',
    'laplacian',
    'sobel'
]


def gaussian_filter(image: np.ndarray, kernel_size: Union[int, Tuple[int, int]]) -> np.ndarray:
    if isinstance(kernel_size, int):
        kernel_size = (kernel_size, kernel_size)
    return cv.GaussianBlur(image, kernel_size, 0)


def gaussian_filter_(image: np.ndarray, kernel_size: Union[int, Tuple[int, int]]) -> np.ndarray:
    if isinstance(kernel_size, int):
        kernel_size = (kernel_size, kernel_size)
    return cv.GaussianBlur(image, kernel_size, 0, image)


def median_filter(image: np.ndarray, kernel_size: int) -> np.ndarray:
    return cv.medianBlur(image, kernel_size)


def median_filter_(image: np.ndarray, kernel_size: int) -> np.ndarray:
    return cv.medianBlur(image, kernel_size, image)


def bilateral_filter(
        image: np.ndarray,
        d: int,
        sigma_color: float,
        sigma_space: Union[float, None] = None
) -> np.ndarray:
    if sigma_space is None:
        sigma_space = sigma_color
    return cv.bilateralFilter(image, d, sigma_color, sigma_space)


def laplacian(image: np.ndarray, kernel_size: int = 1) -> np.ndarray:
    image = cv.Laplacian(image, cv.CV_32F, ksize=kernel_size)
    np.abs(image, out=image)
    np.clip(image, 0, 255, out=image)
    return np.array(image, dtype=np.uint8)


def sobel(image: np.ndarray, kernel_size: int = 3, x: int = 1, y: int = 1) -> np.ndarray:
    edge_x = cv.Sobel(image, cv.CV_64F, x, 0, ksize=kernel_size)
    edge_y = cv.Sobel(image, cv.CV_64F, 0, y, ksize=kernel_size)
    edge = edge_x + edge_y
    return cv.convertScaleAbs(edge)
