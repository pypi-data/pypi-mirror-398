#!/usr/bin/env python3

from typing import Union, Iterable

import cv2 as cv
import numpy as np

__all__ = [
    'add',
    'add_',
    'subtract',
    'subtract_',
    'multiply',
    'multiply_',
    'divide',
    'divide_',
]


def _convert_value(value: Union[int, float, tuple]) -> tuple:
    if isinstance(value, (int, float)):
        value = (value, value, value, 0)
    elif isinstance(value, Iterable):
        value = (*value,)
        if len(value) == 3:
            value = (*value, 0)
    return value


def add(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.add(image, _convert_value(value))


def add_(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.add(image, _convert_value(value), image)


def subtract(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.subtract(image, _convert_value(value))


def subtract_(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.subtract(image, _convert_value(value), image)


def multiply(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.multiply(image, _convert_value(value))


def multiply_(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.multiply(image, _convert_value(value), image)


def divide(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.divide(image, _convert_value(value))


def divide_(image: np.ndarray, value: Union[int, float, tuple]) -> np.ndarray:
    return cv.divide(image, _convert_value(value), image)
