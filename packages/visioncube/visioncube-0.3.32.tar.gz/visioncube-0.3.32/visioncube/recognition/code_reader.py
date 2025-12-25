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

from typing import Union
from types import ModuleType
from importlib import import_module

import cv2 as cv

from visioncube.common import AbstractTransform

pyzbar: Union[ModuleType, None] = None
pylibdmtx: Union[ModuleType, None] = None

__all__ = [
    'ReadQrCode',
    'ReadBarCode',
    'ReadDataMatrixCode',
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


class ReadQrCode(AbstractTransform):

    def __init__(self, filter_size: int = 0):
        """ReadQrCode, 二维码识别, 识别

        Args:
            filter_size: Kernel size of median filter, 中值滤波核大小, [0, 7, 1], 0
        """
        super().__init__(use_gpu=False)

        _ensure_pyzbar()
        self.filter_size = filter_size

    def _apply(self, sample):

        if sample.image is None:
            return sample
        image = sample.image
        if self.filter_size > 1:
            image = cv.medianBlur(image, self.filter_size)

        results = pyzbar.decode(image)
        for index, res in enumerate(results):
            x, y, w, h = res.rect
            text = res.data.decode('utf-8')
            results[index] = {'bbox': [x, y, x + w, y + h],
                              'polygon': [(pt.x, pt.y) for pt in res.polygon],
                              'text': text}

        sample.qr_code = results

        return sample


class ReadBarCode(AbstractTransform):

    def __init__(self, filter_size: int = 0):
        """ReadBarCode, 条形码识别, 识别

        Args:
            filter_size: Kernel size of median filter, 中值滤波核大小, [0, 7, 1], 0
        """
        super().__init__(use_gpu=False)

        _ensure_pyzbar()
        self.filter_size = filter_size

    def _apply(self, sample):

        if sample.image is None:
            return sample
        image = sample.image
        if self.filter_size > 1:
            image = cv.medianBlur(image, self.filter_size)

        results = pyzbar.decode(image)
        for index, res in enumerate(results):
            x, y, w, h = res.rect
            text = res.data.decode('utf-8')
            results[index] = {'bbox': [x, y, x + w, y + h],
                              'polygon': [(pt.x, pt.y) for pt in res.polygon],
                              'text': text}

        sample.bar_code = results

        return sample


class ReadDataMatrixCode(AbstractTransform):

    def __init__(self, filter_size: int = 0):
        """ReadDataMatrixCode, DataMatrix识别, 识别

        Args:
            filter_size: Kernel size of median filter, 中值滤波核大小, [0, 7, 1], 0
        """
        super().__init__(use_gpu=False)

        _ensure_pylibdmtx()
        self.filter_size = filter_size

    def _apply(self, sample):
        if sample.image is None:
            return sample
        image = sample.image
        if self.filter_size > 1:
            image = cv.medianBlur(image, self.filter_size)

        results = pylibdmtx.decode(image)
        for index, res in enumerate(results):
            x, y, w, h = res.rect
            text = res.data.decode('utf-8')
            y = image.shape[0]-y
            results[index] = {'bbox': [x, y, x+w, y-h],
                              'text': text}
        sample.data_matrix_code = results

        return sample


'''
# hanlu debug test
from dataclasses import dataclass
@dataclass
class Sample:
    image: None

if __name__ == "__main__":
    img = cv.imread("1.png")
    print(img.shape)
    func = ReadDataMatrixCode()
    doc = Sample(image=img)
    res = func._apply(doc)
    print(res.data_matrix_code)
    p1 = res.data_matrix_code[0]['bbox'][:2]
    p2 =res.data_matrix_code[0]['bbox'][2:]
    print(p1, p2)
    cv.rectangle(img, p1, p2, (0,0,255), 2)
    cv.imwrite("2.png", img)'
'''