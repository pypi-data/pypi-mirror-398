#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
author：yannan1
since：2023-06-05
"""
import random
from typing import Union, Sequence

import torch
from torchvision.transforms import functional as TF

from ..common import AbstractTransform, eval_arg

__all__ = [
    'Add',
    'Multiply',
    'Solarize',
    'AdditiveGaussianNoise',
    'AdditiveSaltPepperNoise',
    'RandomAdd',
    'RandomMultiply',
    'RandomSolarize',
]


class Add(AbstractTransform):

    def __init__(self, value: Union[float, Sequence] = 0.0) -> None:
        """Add, 加变换, 算术变换

        Args:
            value: Value, 偏移, [-255.0, 255.0, 0.1], 0.0
        """
        super().__init__(use_gpu=True)
        self.value = value

    def _get_params(self):
        if isinstance(self.value, Sequence):
            value = random.uniform(self.value[0], self.value[1])
        else:
            value = eval_arg(self.value, None)

        return value

    def _apply(self, sample):
        if sample.image is None:
            return sample

        value = self._get_params()
        sample.image = torch.clip(sample.image + value, 0, 255).byte()

        return sample


class Multiply(AbstractTransform):

    def __init__(self, mul: Union[float, Sequence] = 1.0) -> None:
        """Multiply, 乘变换, 算术变换

        Args:
            mul: mul, 系数, [0.1, 2.0, 0.1], 1.0
        """
        super().__init__(use_gpu=True)
        self.mul = mul

    def _get_params(self):
        if isinstance(self.mul, Sequence):
            mul = random.uniform(self.mul[0], self.mul[1])
        else:
            mul = eval_arg(self.mul, None)

        return mul

    def _apply(self, sample):
        if sample.image is None:
            return sample

        mul = self._get_params()
        sample.image = torch.clip(sample.image * mul, 0, 255).byte()

        return sample


class Solarize(AbstractTransform):

    def __init__(self, threshold: Union[float, Sequence] = 128.0) -> None:
        """Solarize, 反转变换, 算术变换

        Args:
            threshold: Threshold, 阈值, [0.0, 255.0, 0.1], 255.0
        """
        super().__init__(use_gpu=True)
        self.threshold = threshold

    def _get_params(self):
        if isinstance(self.threshold, Sequence):
            threshold = random.uniform(self.threshold[0], self.threshold[1])
        else:
            threshold = eval_arg(self.threshold, None)

        return threshold

    def _apply(self, sample):
        if sample.image is None:
            return sample

        threshold = self._get_params()
        sample.image = TF.solarize(sample.image, threshold=threshold)
        return sample


class AdditiveGaussianNoise(AbstractTransform):

    def __init__(self, mean: float = 0.0, std: float = 3.0) -> None:
        """AdditiveGaussianNoise, 高斯噪声, 算术变换

        Args:
            mean: Mean, 平均值, [0.0, 1.0, 0.1], 0.0
            std: Standard deviation, 标准差, [0.0, 15.0, 0.1], 3.0
        """
        super().__init__(use_gpu=True)

        self.mean = eval_arg(mean, None)
        self.std = eval_arg(std, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        gauss = torch.normal(mean=self.mean, std=self.std, size=sample.shape).to(sample.device)
        noisy_img = sample.image + gauss
        sample.image = torch.clip(noisy_img, min=0, max=255).byte()

        return sample


class AdditiveSaltPepperNoise(AbstractTransform):

    def __init__(self, p: float = 0.01) -> None:
        """AdditiveSaltPepperNoise, 椒盐噪声, 算术变换

        Args:
            p: Probability, 概率, [0.0, 0.03, 0.01], 0.01
        """
        super().__init__(use_gpu=True)
        self.p = eval_arg(p, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        _, h, w = sample.shape
        num_salt = int(self.p * h * w)
        num_salt_0 = random.randint(0, num_salt)
        num_salt_255 = num_salt - num_salt_0

        coords1 = [torch.randint(low=0, high=i - 1, size=(num_salt_0,)) for i in [h, w]]
        sample.image[:, coords1[0], coords1[1]] = 0

        coords2 = [torch.randint(low=0, high=i - 1, size=(num_salt_255,)) for i in [h, w]]
        sample.image[:, coords2[0], coords2[1]] = 255

        return sample


class RandomAdd(Add):

    def __init__(self, value_min: float = -255.0, value_max: float = 255.0) -> None:
        """RandomAdd, 随机加变换, 算术变换

        Args:
            value_min: Value minimum, 偏移最小值, [-255.0, 255.0, 0.1], -255.0
            value_max: Value maximum, 偏移最大值, [-255.0, 255.0, 0.1], 255.0
        """
        value_min = eval_arg(value_min, None)
        value_max = eval_arg(value_max, None)
        super().__init__((value_min, value_max))


class RandomMultiply(Multiply):

    def __init__(self, mul_min: float = 0.8, mul_max: float = 1.2) -> None:
        """RandomMultiply, 随机乘变换, 算术变换

        Args:
            mul_min: Multiplier minimum, 乘数最小值, [0.8, 1.2, 0.1], 0.8
            mul_max: Multiplier maximum, 乘数最大值, [0.8, 1.2, 0.1], 1.2
        """
        mul_min = eval_arg(mul_min, None)
        mul_max = eval_arg(mul_max, None)
        super().__init__((mul_min, mul_max))


class RandomSolarize(Solarize):

    def __init__(
            self,
            p: float = 0.5,
            threshold_min: float = 0.0,
            threshold_max: float = 255.0
    ) -> None:
        """RandomSolarize, 随机反转变换, 算术变换

        Args:
            p: Probability, 变换概率, [0, 1.0, 0.1], 0.5
            threshold_min: Threshold minimum, 阈值最小值, [0.0, 255.0, 0.1], 0.0
            threshold_max: Threshold maximum, 阈值最大值, [0.0, 255.0, 0.1], 255.0
        """
        self.p = eval_arg(p, None)
        threshold_min = eval_arg(threshold_min, None)
        threshold_max = eval_arg(threshold_max, None)
        super().__init__((threshold_min, threshold_max))

    def _apply(self, sample):

        if torch.rand(1) < self.p:
            sample = super()._apply(sample)

        return sample
