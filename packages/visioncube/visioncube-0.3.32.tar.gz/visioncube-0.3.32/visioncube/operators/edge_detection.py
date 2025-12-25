#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-11-16
"""
import cv2 as cv
import numpy as np

from .color import GrayScale
from ..common import eval_arg, AbstractTransform

__all__ = [
    'Canny',
    'Laplacian',
    'Sobel',
    'Roberts',
    'Prewitt',
]


class Canny(AbstractTransform):

    def __init__(self, threshold1: float = 100, threshold2: float = 200) -> None:
        """Canny, Canny边缘检测, 边缘检测

        Args:
            threshold1: Threshold1, 参数1, [0, 255, 1], 100
            threshold2: Threshold2, 参数2, [0, 255, 1], 200
        """
        super().__init__(use_gpu=False)

        self.threshold1 = eval_arg(threshold1, None)
        self.threshold2 = eval_arg(threshold2, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = cv.Canny(sample.image, self.threshold1, self.threshold2)
        sample.image = np.repeat(image[..., np.newaxis], repeats=3, axis=-1)

        return sample


class Laplacian(AbstractTransform):

    def __init__(self, kernel_size: int = 1) -> None:
        """Laplacian, 拉普拉斯边缘检测, 边缘检测

        Args:
            kernel_size: Kernel size, 核数, [1, 9, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel_size = eval_arg(kernel_size, int)
        if self.kernel_size % 2 == 0:
            self.kernel_size += 1

    def _apply(self, sample):
        if sample.image is None:
            return sample

        lap = cv.Laplacian(sample.image, cv.CV_32F, ksize=self.kernel_size)
        sample.image = cv.convertScaleAbs(lap)

        return sample


class Sobel(AbstractTransform):

    def __init__(self, kernel_size: int = 3, x: int = 1, y: int = 1) -> None:
        """Sobel, Sobel边缘检测, 边缘检测

        Args:
            kernel_size: Kernel size, 核数, [1, 7, 1], 3
            x: Order of the derivative x, x方向的导数阶数, {1, 2}, 1
            y: order of the derivative y, y方向的导数阶数, {1, 2}, 1
        """
        super().__init__(use_gpu=False)

        self.x = eval_arg(x, None)
        self.y = eval_arg(y, None)
        self.kernel_size = eval_arg(kernel_size, int)

        if self.kernel_size % 2 == 0:
            self.kernel_size += 1

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = sample.image
        edge_x = cv.Sobel(image, cv.CV_64F, self.x, 0, ksize=self.kernel_size)
        edge_y = cv.Sobel(image, cv.CV_64F, 0, self.y, ksize=self.kernel_size)
        edge = edge_x + edge_y
        sample.image = cv.convertScaleAbs(edge)

        return sample


class Roberts(AbstractTransform):

    def __init__(self):
        """Roberts, Roberts边缘检测, 边缘检测
        """
        super().__init__(use_gpu=False)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        image = sample.image

        kernel_x = np.array([[-1, 0], [0, 1]], dtype=int)
        kernel_y = np.array([[0, -1], [1, 0]], dtype=int)
        x = cv.filter2D(image, cv.CV_16S, kernel_x)
        y = cv.filter2D(image, cv.CV_16S, kernel_y)

        out_x = cv.convertScaleAbs(x)
        out_y = cv.convertScaleAbs(y)
        sample.image = cv.addWeighted(out_x, 0.5, out_y, 0.5, 0)  # 0.5*out_x+0.5*out_y+0

        return sample


class Prewitt(AbstractTransform):

    def __init__(self):
        """Prewitt, Prewitt边缘检测, 边缘检测
        """
        super().__init__(use_gpu=False)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        image = sample.image

        kernel_x = np.array([[1, 1, 1], [0, 0, 0], [-1, -1, -1]], dtype=int)
        kernel_y = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=int)
        x = cv.filter2D(image, cv.CV_16S, kernel_x)
        y = cv.filter2D(image, cv.CV_16S, kernel_y)

        out_x = cv.convertScaleAbs(x)
        out_y = cv.convertScaleAbs(y)
        sample.image = cv.addWeighted(out_x, 0.5, out_y, 0.5, 0)

        return sample
