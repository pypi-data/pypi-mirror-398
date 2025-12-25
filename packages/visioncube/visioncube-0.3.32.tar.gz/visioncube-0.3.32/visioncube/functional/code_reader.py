#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-10-23


## Windows
pip install pyzbar
pip install pylibdmtx

## Linux
sudo apt-get install libzbar-dev
pip install pyzbar
sudo apt-get install libdmtx0b
pip install pylibdmtx
"""

from importlib import import_module
from types import ModuleType
from typing import Union

import cv2 as cv

pyzbar: Union[ModuleType, None] = None
pylibdmtx: Union[ModuleType, None] = None

__all__ = [
    'read_qr_code',
    'read_bar_code',
    'read_data_matrix_code'
]


def _ensure_pyzbar():
    global pyzbar
    if pyzbar is None:
        try:
            pyzbar = import_module('pyzbar.pyzbar')
        except ImportError:
            raise RuntimeError(
                'Reading QR bar code requires "pyzbar" package. '
                'You should install it by "sudo apt-get install lizbar-dev; pip install pyzbar" '
                'on Linux or "pip install pyzbar" on Windows.'
            )


def _ensure_pylibdmtx():
    global pylibdmtx
    if pylibdmtx is None:
        try:
            pylibdmtx = import_module('pylibdmtx.pylibdmtx')
        except ImportError:
            raise RuntimeError(
                'Reading data matrlix code requires "pylibdmtx" package. '
                'You should install it by "sudo apt-get install libdmtx0b; pip install pylibdmtx" '
                'on Linux or "pip install pylibdmtx" on Windows.'
            )


def read_qr_code(image, filter_size: int = 0):
    """Read QR Code

    Args:
        image (np.ndarray): RGB、BGR or gray image
        filter_size: Kernel size of median filter, 中值滤波核大小, [0, 7, 1], 0

    Returns:
        list: [dict, dict]
    """
    if filter_size > 1:
        image = cv.medianBlur(image, filter_size)
    _ensure_pyzbar()
    results = pyzbar.decode(image)
    for index, res in enumerate(results):
        x, y, w, h = res.rect
        text = res.data.decode('utf-8')
        results[index] = {'bbox': [x, y, x + w, y + h],
                          'polygon': [(pt.x, pt.y) for pt in res.polygon],
                          'text': text}

    return results


def read_bar_code(image, filter_size: int = 0):
    """Read Bar Code

    Args:
        image (np.ndarray): RGB、BGR or gray image
        filter_size: Kernel size of median filter, 中值滤波核大小, [0, 7, 1], 0

    Returns:
        list: [dict, dict]
    """
    if filter_size > 1:
        image = cv.medianBlur(image, filter_size)
    _ensure_pyzbar()
    results = pyzbar.decode(image)
    for index, res in enumerate(results):
        x, y, w, h = res.rect
        text = res.data.decode('utf-8')
        results[index] = {'bbox': [x, y, x + w, y + h],
                          'polygon': [(pt.x, pt.y) for pt in res.polygon],
                          'text': text}

    return results


def read_data_matrix_code(image, filter_size: int = 0):
    """Read Data Matrix Code

    Args:
        image (np.ndarray): RGB、BGR or gray image
        filter_size: Kernel size of median filter, 中值滤波核大小, [0, 7, 1], 0

    Returns:
        list: [dict, dict]
    """
    if filter_size > 1:
        image = cv.medianBlur(image, filter_size)
    _ensure_pylibdmtx()
    results = pylibdmtx.decode(image)
    for index, res in enumerate(results):
        x, y, w, h = res.rect
        text = res.data.decode('utf-8')
        results[index] = {'bbox': [min(x, x + w), min(y, y + h), max(x, x + w), max(y, y + h)],
                          'text': text}
    return results
