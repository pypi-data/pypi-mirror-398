#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-11-16
"""
import kornia as K
import torch
from torchvision import transforms
from torch.nn import functional as F

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

    def __init__(
            self,
            threshold1: float = 0.1,
            threshold2: float = 0.2,
            kernel_size: int = 5,
    ) -> None:
        """Canny, Canny边缘检测, 边缘检测

        Args:
            threshold1: Threshold1, 参数1, [0.1, 1.0, 0.1), 0.1
            threshold2: Threshold2, 参数2, [0.1, 1.0, 0.1), 0.2
            kernel_size: Kernel size, 核数, [1, 9, 1], 5
        """
        super().__init__(use_gpu=True)

        threshold1 = eval_arg(threshold1, None)
        threshold2 = eval_arg(threshold2, None)
        self.threshold1 = min(threshold1, threshold2)
        self.threshold2 = max(threshold1, threshold2)
        self.kernel_size = eval_arg(kernel_size, int)

        if self.kernel_size % 2 == 0:
            self.kernel_size += 1

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = K.filters.canny(
            sample.image.unsqueeze(0).float(),
            low_threshold=self.threshold1,
            high_threshold=self.threshold2,
            kernel_size=(self.kernel_size, self.kernel_size),
        )[0].squeeze(0).byte()

        return sample


class Laplacian(AbstractTransform):

    def __init__(
            self,
            kernel_size: int = 3,
            mode: str = "reflect",
    ) -> None:
        """Laplacian, 拉普拉斯边缘检测, 边缘检测

        Args:
            kernel_size: Kernel size, 核数, [1, 9, 1], 3
            mode: Fill mode, 填充模式, {"constant", "reflect", "replicate", "circular"}, "reflect"
        """
        super().__init__(use_gpu=True)

        self.kernel_size = eval_arg(kernel_size, int)
        self.mode = mode

        if self.kernel_size % 2 == 0:
            self.kernel_size += 1

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = K.filters.laplacian(
            sample.image.unsqueeze(0).float(),
            kernel_size=(self.kernel_size, self.kernel_size),
            border_type=self.mode,
            normalized=False,
        ).squeeze(0)

        sample.image = torch.abs(image).clip_(min=0, max=255).byte()

        return sample


class Sobel(AbstractTransform):

    def __init__(
            self,
    ) -> None:
        """Sobel, Sobel边缘检测, 边缘检测
        """
        super().__init__(use_gpu=True)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = K.filters.sobel(
            sample.image.unsqueeze(0).float(),
            normalized=False,
        ).squeeze(0).byte()

        return sample


class Roberts(AbstractTransform):

    def __init__(self):
        """Roberts, Roberts边缘检测, 边缘检测
        """
        super().__init__(use_gpu=True)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        image = sample.image.float()

        kernel_x = torch.tensor([[-1, 0], [0, 1]], dtype=torch.float32).to(sample.device)
        kernel_y = torch.tensor([[0, -1], [1, 0]], dtype=torch.float32).to(sample.device)

        kernel_x = kernel_x.view(1, 1, 2, 2)
        kernel_y = kernel_y.view(1, 1, 2, 2)
        out_x = F.conv2d(image, kernel_x)
        out_y = F.conv2d(image, kernel_y)

        sample.image = torch.sqrt(out_x ** 2 + out_y ** 2).byte()

        return sample


class Prewitt(AbstractTransform):

    def __init__(self):
        """Prewitt, Prewitt边缘检测, 边缘检测
        """
        super().__init__(use_gpu=True)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        image = sample.image.float()

        kernel_x = torch.tensor([[1, 1, 1], [0, 0, 0], [-1, -1, -1]],
                                dtype=torch.float32).to(sample.device)
        kernel_y = torch.tensor([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]],
                                dtype=torch.float32).to(sample.device)

        kernel_x = kernel_x.view(1, 1, 3, 3)
        kernel_y = kernel_y.view(1, 1, 3, 3)
        out_x = F.conv2d(image, kernel_x)
        out_y = F.conv2d(image, kernel_y)

        sample.image = torch.sqrt(out_x ** 2 + out_y ** 2).byte()

        return sample
