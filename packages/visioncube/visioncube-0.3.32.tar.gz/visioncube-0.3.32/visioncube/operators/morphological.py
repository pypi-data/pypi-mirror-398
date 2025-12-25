#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-11-29
"""
from typing import Optional, Union, Tuple

import cv2 as cv
import numpy as np

from .color import GrayScale
from ..common import AbstractTransform

__all__ = [
    'Erode',
    'Dilate',
    'ConditionalDilate',
    'MorphOpen',
    'MorphClose',
    'MorphGradient',
    'MorphTophat',
    'MorphBlackhat',
]


def _morph(
        op,
        image: np.ndarray,
        kernel: Union[np.ndarray, int, Tuple[int, int]],
        iterations: Optional[int] = 1
) -> np.ndarray:
    return cv.morphologyEx(image, op, kernel, iterations=iterations)


def _init_morph_kernel(kernel_shape: str, kernel_size):
    if kernel_shape.lower() == 'ellipse':
        shape = cv.MORPH_ELLIPSE
    elif kernel_shape.lower() == 'rectangle':
        shape = cv.MORPH_RECT
    elif kernel_shape.lower() == 'cross':
        shape = cv.MORPH_CROSS
    else:
        raise ValueError('Wrong shape')

    return cv.getStructuringElement(shape, kernel_size)


class Erode(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 3,
            kernel_w: int = 3,
            iterations: int = 1,
    ) -> None:
        """Erode, 腐蚀, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
            iterations: Iteration times, 迭代次数, (0, 10, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))
        self.iter = iterations

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = cv.erode(sample.image, self.kernel, iterations=self.iter)
        return sample


class Dilate(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 3,
            kernel_w: int = 3,
            iterations: int = 1,
    ) -> None:
        """Dilate, 膨胀, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
            iterations: Iteration times, 迭代次数, (0, 10, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))
        self.iter = iterations

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = cv.dilate(sample.image, self.kernel, iterations=self.iter)
        return sample


class ConditionalErode(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_size: Tuple = (3, 3),
            iterations: int = 1
    ) -> None:
        """条件腐蚀

        Args:
            kernel_shape: Kernel shape, 核形状, ['rectangle', 'cross', 'ellipse'], 'ellipse'
            kernel_size: Kernel size, 核尺寸, (0, 500), [3, 3]
            iterations: Iteration times, 迭代次数, (0, 10], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, kernel_size)
        self.iter = iterations

    def _apply(self, bin_img: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        待测试！！

        在给定的前景范围内填充孔洞等
        X_k = (X_(k-1) + B) \cap A^c
        where A^c is the foreground of the image

        Args:
        """
        cnts, _ = cv.findContours(bin_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=lambda x: cv.contourArea(x), reverse=True)[0]
        foreground = np.zeros(bin_img.shape, dtype=np.uint8)
        cv.fillPoly(foreground, [cnts], color=1)

        dilate_img = cv.dilate(bin_img, self.kernel, self.iter)
        return np.logical_and(foreground, bin_img + dilate_img)


class ConditionalDilate(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 3,
            kernel_w: int = 3,
            iterations: int = 1,
    ) -> None:
        """ConditionalDilate, 条件膨胀, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
            iterations: Iteration times, 迭代次数, (0, 10, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))
        self.iter = iterations

    def _apply(self, sample):
        """
        待测试！！

        在给定的前景范围内填充孔洞等
        X_k = (X_(k-1) + B) \cap A^c
        where A^c is the foreground of the image

        Args:
        """
        if sample.image is None:
            return sample

        bin_img = sample.image
        cnts, _ = cv.findContours(bin_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=lambda x: cv.contourArea(x), reverse=True)[0]
        foreground = np.zeros(bin_img.shape, dtype=np.uint8)
        cv.fillPoly(foreground, [cnts], color=1)

        dilate_img = cv.dilate(bin_img, self.kernel, self.iter)
        res_img = np.logical_and(foreground, bin_img + dilate_img)
        sample.image = res_img
        return sample


class MorphOpen(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 21,
            kernel_w: int = 21,
            iterations=1,
    ) -> None:
        """MorphOpen, 开运算, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 21
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 21
            iterations: Iterations, 迭代次数, (0, 10, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))
        self.iter = iterations

    def _apply(self, sample):
        """notes
        平滑轮廓,切断狭窄区域,消除小的孤岛和尖刺(白点)
        """
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = _morph(cv.MORPH_OPEN, sample.image, self.kernel, self.iter)

        return sample


class MorphClose(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 3,
            kernel_w: int = 3,
            iterations: int = 1,
    ) -> None:
        """MorphClose, 闭运算, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
            iterations: Iteration times, 迭代次数, (0, 10, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))
        self.iter = iterations

    def _apply(self, sample):
        """notes
        平滑轮廓,融合狭窄间断和细长沟壑,消除小的孔洞(黑点)
        """
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = _morph(cv.MORPH_CLOSE, sample.image, self.kernel, self.iter)
        return sample


class MorphGradient(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 3,
            kernel_w: int = 3,
            iterations: int = 1,
    ) -> None:
        """MorphGradient, 形态学梯度, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
            iterations: Iteration times, 迭代次数, (0, 10, 1], 1
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))
        self.iter = iterations

    def _apply(self, sample):
        """notes
        提取轮廓
        """
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = _morph(cv.MORPH_GRADIENT, sample.image, self.kernel, self.iter)
        return sample


class MorphTophat(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 21,
            kernel_w: int = 21,
    ) -> None:
        """MorphTophat, 顶帽变换, 形态学变换
        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 21
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 21
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        tophat_img = _morph(cv.MORPH_TOPHAT, sample.image, self.kernel)
        # tophat_img = gray - tophat_img
        sample.image = tophat_img

        return sample


class MorphBlackhat(AbstractTransform):

    def __init__(
            self,
            kernel_shape: str = 'ellipse',
            kernel_h: int = 21,
            kernel_w: int = 21,
    ) -> None:
        """MorphBlackhat, 底帽变换, 形态学变换

        Args:
            kernel_shape: Kernel shape, 核形状, {'rectangle', 'cross', 'ellipse'}, 'ellipse'
            kernel_h: Kernel size, 核的高, (0, 150, 1), 21
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 21
        """
        super().__init__(use_gpu=False)

        self.kernel = _init_morph_kernel(kernel_shape, (kernel_h, kernel_w))

    def _apply(self, sample):
        """
        B_hat(f) = (f * b) - f
        用于亮背景上的暗物体
        """
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        bottom_img = _morph(cv.MORPH_BLACKHAT, sample.image, self.kernel)
        # mask = bottom_img - gray
        sample.image = bottom_img

        return sample
