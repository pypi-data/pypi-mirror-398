#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
author：yannan1
since：2023-05-26
"""
import random
from typing import Sequence, Union

import torch
import kornia as K
import torch.nn as nn
from torch.nn import functional as F
from torchvision.transforms import transforms, InterpolationMode

from ..common import eval_arg, AbstractTransform

__all__ = [
    'GaussianBlur',
    'AverageBlur',
    'MedianBlur',
    'BilateralBlur',
    'MotionBlur',
    'RandomGaussianBlur',
    'RandomAverageBlur',
    'RandomMedianBlur',
    'RandomBilateralBlur',
    'RandomMotionBlur',
]


class GaussianBlur(AbstractTransform):

    def __init__(self, kernel_size: int = 3, sigma: float = 3.0) -> None:
        """GaussianBlur, 高斯滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 9, 1], 3
            sigma: Sigma, 标准差, [0.1, 3.0, 0.1], 3.0
        """
        super().__init__(use_gpu=True)

        kernel_size = eval_arg(kernel_size, None)
        sigma = eval_arg(sigma, None)
        if kernel_size % 2 == 0:
            kernel_size += 1

        self.operator = transforms.GaussianBlur(kernel_size=kernel_size, sigma=sigma)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class AverageBlur(AbstractTransform):

    def __init__(self, kernel_size: Union[int, Sequence] = 5) -> None:
        """AverageBlur, 均值滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 7, 1], 5
        """
        super().__init__(use_gpu=True)
        self.kernel_size = kernel_size

    def _get_params(self):

        if isinstance(self.kernel_size, Sequence):
            kernel_size = random.randint(self.kernel_size[0], self.kernel_size[1])
        else:
            kernel_size = eval_arg(self.kernel_size, int)

        if kernel_size % 2 == 0:
            kernel_size += 1

        return kernel_size

    def _apply(self, sample):
        if sample.image is None:
            return sample

        kernel_size = self._get_params()
        padding = int((kernel_size - 1) / 2)
        image = transforms.Pad(padding=padding, padding_mode='reflect')(sample.image)
        image = image.float()
        sample.image = nn.AvgPool2d(kernel_size, stride=1)(image).byte()

        return sample


class MedianBlur(AbstractTransform):

    def __init__(self, kernel_size: Union[int, Sequence] = 5) -> None:
        """MedianBlur, 中值滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 7, 1], 5
        """
        super().__init__(use_gpu=True)
        self.kernel_size = kernel_size

    def _get_params(self):

        if isinstance(self.kernel_size, Sequence):
            kernel_size = random.randint(self.kernel_size[0], self.kernel_size[1])
        else:
            kernel_size = eval_arg(self.kernel_size, int)

        if kernel_size % 2 == 0:
            kernel_size += 1

        return kernel_size

    # def _apply(self, sample):
    #     if sample.image is None:
    #         return sample
    #
    #     kernel_size = self._get_params()
    #     image = sample.image.unsqueeze(0)
    #     sample.image = K.filters.median_blur(image, kernel_size).squeeze(0)
    #
    #     return sample

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = sample.image.float()
        kernel_size = self._get_params()

        device, dtype = image.device, image.dtype
        window_range = kernel_size * kernel_size
        kernel = torch.zeros((window_range, window_range), device=device, dtype=dtype)
        idx = torch.arange(window_range, device=device)
        kernel[idx, idx] += 1.0
        kernel = kernel.view(window_range, 1, kernel_size, kernel_size)

        padding = (kernel_size - 1) // 2
        c, h, w = image.shape
        image_reshaped = image.reshape(c, 1, h, w)

        # features shape = [c, 9, h, w]
        features = F.conv2d(image_reshaped, kernel, padding=padding, stride=1)
        # features = features.view(c, -1, h, w)  # features shape = [c, 9, h, w]

        # return shape = [c, h, w]
        sample.image = features.median(dim=1)[0].byte()
        return sample


class BilateralBlur(AbstractTransform):

    def __init__(
            self,
            d: Union[int, Sequence] = 5,
            sigma: Union[float, Sequence] = 11.0,
            mode: str = 'constant'
    ) -> None:
        """BilateralBlur, 双边滤波, 滤波变换

        Args:
            d: Diameter, 直径, [1, 9, 1], 5
            sigma: Sigma, 标准差, (0.0, 100.0, 0.1], 11.0
            mode: Fill mode, 填充模式, {"constant", "reflect", "replicate", "circular"}, "reflect"
        """
        super().__init__(use_gpu=True)

        self.d = d
        self.sigma = sigma
        self.mode = mode

    def _get_params(self):
        if isinstance(self.d, Sequence):
            d = random.randint(self.d[0], self.d[1])
        else:
            d = eval_arg(self.d, int)

        if d % 2 == 0:
            d += 1

        if isinstance(self.sigma, Sequence):
            sigma = random.uniform(self.sigma[0], self.sigma[1])
        else:
            sigma = eval_arg(self.sigma, None)

        return d, sigma

    def _apply(self, sample):
        if sample.image is None:
            return sample

        d, sigma = self._get_params()
        sample.image = K.filters.bilateral_blur(
            sample.image.unsqueeze(0).float(),
            kernel_size=(d, d),
            sigma_color=sigma,
            sigma_space=(sigma, sigma),
            border_type=self.mode
        ).squeeze(0).byte()

        return sample


class MotionBlur(AbstractTransform):
    def __init__(
            self,
            kernel_size: Union[int, Sequence] = 3,
            degree: Union[float, Sequence] = 45.0,
            direction: Union[float, Sequence] = 1.0,
            mode: str = 'constant',
            interpolation: str = 'nearest',
    ) -> None:
        """MotionBlur, 物体运动滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [2, 9, 1], 3
            degree: Rotate angle, 旋转角度, [-180.0, 180.0, 0.1], 45.0
            direction: Direction, 方向, [-1.0, 1.0, 0.1], 1.0
            mode: Fill mode, 填充模式, {"constant", "reflect", "replicate", "circular"}, "constant"
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear"}, "nearest"
        """
        super().__init__(use_gpu=True)

        self.kernel_size = kernel_size
        self.degree = degree
        self.direction = direction
        self.mode = mode
        self.interpolation = InterpolationMode[interpolation.upper()]

    def _get_params(self):
        if isinstance(self.kernel_size, Sequence):
            kernel_size = random.randint(self.kernel_size[0], self.kernel_size[1])
        else:
            kernel_size = eval_arg(self.kernel_size, None)

        if kernel_size % 2 == 0:
            kernel_size += 1

        if isinstance(self.degree, Sequence):
            degree = random.uniform(self.degree[0], self.degree[1])
        else:
            degree = eval_arg(self.degree, None)

        if isinstance(self.direction, Sequence):
            direction = random.uniform(self.direction[0], self.direction[1])
        else:
            direction = eval_arg(self.direction, None)

        return kernel_size, degree, direction

    def _apply(self, sample):
        if sample.image is None:
            return sample

        kernel_size, degree, direction = self._get_params()
        sample.image = K.filters.motion_blur(
            sample.image.unsqueeze(0).float(),
            kernel_size=kernel_size,
            angle=degree,
            direction=direction
        ).squeeze(0).byte()

        return sample


class RandomGaussianBlur(AbstractTransform):

    def __init__(
            self,
            kernel_size: int = 3,
            sigma_min: float = 0.1,
            sigma_max: float = 3.0
    ) -> None:
        """RandomGaussianBlur, 随机高斯滤波, 滤波变换

        Args:
            kernel_size: Kernel size, 核数, [1, 9, 1], 3
            sigma_min: Sigma minimum, 标准差最小值, [0.1, 3.0, 0.1], 0.1
            sigma_max: Sigma maximum, 标准差最大值, [0.1, 3.0, 0.1], 3.0
        """
        super().__init__(use_gpu=True)

        self.kernel_size = eval_arg(kernel_size, int)
        self.sigma_min = eval_arg(sigma_min, float)
        self.sigma_max = eval_arg(sigma_max, float)

        if self.kernel_size % 2 == 0:
            self.kernel_size += 1

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = transforms.GaussianBlur(
            kernel_size=self.kernel_size,
            sigma=(self.sigma_min, self.sigma_max))(sample.image)
        return sample


class RandomAverageBlur(AverageBlur):

    def __init__(self, kernel_size_min: int = 1, kernel_size_max: int = 7) -> None:
        """RandomAverageBlur, 随机均值滤波, 滤波变换

        Args:
            kernel_size_min: Kernel size minimum, 核数最小值, [1, 7, 1], 1
            kernel_size_max: Kernel size maximum, 核数最大值,, [1, 7, 1], 7
        """
        kernel_size_min = eval_arg(kernel_size_min, int)
        kernel_size_max = eval_arg(kernel_size_max, int)

        super().__init__(kernel_size=(kernel_size_min, kernel_size_max))


class RandomMedianBlur(MedianBlur):

    def __init__(self, kernel_size_min: int = 1, kernel_size_max: int = 7) -> None:
        """RandomMedianBlur, 随机中值滤波, 滤波变换

        Args:
            kernel_size_min: Kernel size minimum, 核数最小值, [1, 7, 1], 1
            kernel_size_max: Kernel size maximum, 核数最大值,, [1, 7, 1], 7
        """
        kernel_size_min = eval_arg(kernel_size_min, int)
        kernel_size_max = eval_arg(kernel_size_max, int)

        super().__init__(kernel_size=(kernel_size_min, kernel_size_max))


class RandomBilateralBlur(BilateralBlur):
    def __init__(
            self,
            d_min: int = 1,
            d_max: int = 9,
            sigma_min: float = 10.0,
            sigma_max: float = 250.0,
            mode: str = 'constant'
    ) -> None:
        """RandomBilateralBlur, 随机双边滤波, 滤波变换

        Args:
            d_min: Diameter min value, 直径最小值, [1, 9, 1], 1
            d_max: Diameter max value, 直径最大值, [1, 9, 1], 9
            sigma_min: Sigma min value, 标准差最小值, [10.0, 250.0, 0.1], 10.0
            sigma_max: Sigma max value, 标准差最大值, [10.0, 250.0, 0.1], 250.0
            mode: Fill mode, 填充模式, {"constant", "reflect", "replicate", "circular"}, "reflect"
        """
        d_min = eval_arg(d_min, int)
        d_max = eval_arg(d_max, int)
        sigma_min = eval_arg(sigma_min, None)
        sigma_max = eval_arg(sigma_max, None)

        super().__init__(d=(d_min, d_max), sigma=(sigma_min, sigma_max), mode=mode)


class RandomMotionBlur(MotionBlur):

    def __init__(
            self,
            kernel_size_min: int = 3,
            kernel_size_max: int = 7,
            degree_min: float = 0.0,
            degree_max: float = 360.0,
            direction_min: float = -1.0,
            direction_max: float = 1.0,
            mode: str = 'constant',
            interpolation: str = 'nearest',
    ) -> None:
        """RandomMotionBlur, 随机物体运动滤波, 滤波变换

        Args:
            kernel_size_min: Kernel size minimum, 核数最小值, [3, 7, 1], 3
            kernel_size_max: Kernel size maximum, 核数最小值, [3, 7, 1], 7
            degree_min: Angle minimum, 角度最小值, [0.0, 360.0, 0.1], 0.0
            degree_max: Angle maximum, 角度最大值, [0.0, 360.0, 0.1], 360.0
            direction_min: Direction minimum, 方向最小值, (-1.0, 1.0, 0.1], -1.0
            direction_max: Direction maximum, 方向最大值, (-1.0, 1.0, 0.1], 1.0
            mode: Fill mode, 填充模式, {"constant", "reflect", "replicate", "circular"}, "constant"
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear"}, "nearest"
        """
        kernel_size_min = eval_arg(kernel_size_min, None)
        kernel_size_max = eval_arg(kernel_size_max, None)
        degree_min = eval_arg(degree_min, None)
        degree_max = eval_arg(degree_max, None)
        direction_min = eval_arg(direction_min, None)
        direction_max = eval_arg(direction_max, None)

        super().__init__(
            kernel_size=(kernel_size_min, kernel_size_max),
            degree=(degree_min, degree_max),
            direction=(direction_min, direction_max),
            mode=mode,
            interpolation=interpolation,
        )
