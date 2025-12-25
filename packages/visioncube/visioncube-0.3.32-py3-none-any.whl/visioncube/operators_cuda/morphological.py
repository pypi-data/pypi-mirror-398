#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-11-30
"""
import torch
from torch import nn
import kornia as K

from .color import GrayScale
from ..common import AbstractTransform

__all__ = [
    'Erode',
    'Dilate',
    'MorphOpen',
    'MorphClose',
    'MorphGradient',
    'MorphTophat',
    'MorphBlackhat',
]


# class Erode(AbstractTransform):

#     def __init__(
#             self,
#             kernel_h: int = 3,
#             kernel_w: int = 3,
#     ) -> None:
#         """Erode, 腐蚀, 形态学变换

#         Args:
#             kernel_h: Kernel size, 核的高, (0, 150, 1), 3
#             kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
#         """
#         super().__init__(use_gpu=True)
#         self.kernel = torch.ones((kernel_h, kernel_w))

#     def _apply(self, sample):
#         if sample.image is None:
#             return sample

#         sample = GrayScale()(sample)
#         sample.image = K.morphology.erosion(
#             sample.image.unsqueeze(0).float(),
#             kernel=self.kernel.to(sample.device),
#         ).squeeze(0).byte()

#         return sample

class Erode(AbstractTransform):
    # update by liying50, 优化显存占用

    def __init__(self, kernel_size: int = 3) -> None:
        """Erode, 腐蚀, 形态学变换

        Args:
            kernel_size: Kernel size, 腐蚀核大小, (0, 150, 1), 3
        """
        super().__init__(use_gpu=True)
        self.max_pool = nn.MaxPool2d(
            kernel_size=kernel_size, stride=1, padding=kernel_size // 2
        )

    def _apply(self, sample):
        if sample.image is None:
            return sample

        # sample = GrayScale()(sample)
        inverted_image = 255 - sample.image  # 对图像取反
        eroded_image = self.max_pool(inverted_image.unsqueeze(0).float())
        eroded_image = (255 - eroded_image).squeeze(0)  # 再次取反得到腐蚀后的图像
        if eroded_image.shape[1] != inverted_image.shape[1]:
            _, out_h, out_w = inverted_image.shape
            resized = nn.functional.interpolate(
                eroded_image.unsqueeze(0), size=(out_h, out_w), mode="bilinear"
            )
            eroded_image = resized.squeeze(0)
        sample.image = eroded_image.byte()
        return sample


class Dilate(AbstractTransform):

    def __init__(
            self,
            kernel_h: int = 3,
            kernel_w: int = 3,
    ) -> None:
        """Dilate, 膨胀, 形态学变换

        Args:
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
        """
        super().__init__(use_gpu=True)
        self.kernel = torch.ones((kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = K.morphology.dilation(
            sample.image.unsqueeze(0).float(),
            kernel=self.kernel.to(sample.device),
        ).squeeze(0).byte()

        return sample


class MorphOpen(AbstractTransform):

    def __init__(
            self,
            kernel_h: int = 21,
            kernel_w: int = 21,
    ) -> None:
        """MorphOpen, 开运算, 形态学变换

        Args:
            kernel_h: Kernel size, 核的高, (0, 150, 1), 21
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 21
        """
        super().__init__(use_gpu=True)
        self.kernel = torch.ones((kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = K.morphology.opening(
            sample.image.unsqueeze(0).float(),
            kernel=self.kernel.to(sample.device),
        ).squeeze(0).byte()

        return sample


class MorphClose(AbstractTransform):

    def __init__(
            self,
            kernel_h: int = 3,
            kernel_w: int = 3,
    ) -> None:
        """MorphClose, 闭运算, 形态学变换

        Args:
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
        """
        super().__init__(use_gpu=True)
        self.kernel = torch.ones((kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = K.morphology.closing(
            sample.image.unsqueeze(0).float(),
            kernel=self.kernel.to(sample.device),
        ).squeeze(0).byte()

        return sample


class MorphGradient(AbstractTransform):

    def __init__(
            self,
            kernel_h: int = 3,
            kernel_w: int = 3,
    ) -> None:
        """MorphGradient, 形态学梯度, 形态学变换

        Args:
            kernel_h: Kernel size, 核的高, (0, 150, 1), 3
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 3
        """
        super().__init__(use_gpu=True)
        self.kernel = torch.ones((kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = K.morphology.gradient(
            sample.image.unsqueeze(0).float(),
            kernel=self.kernel.to(sample.device),
        ).squeeze(0).byte()

        return sample


class MorphTophat(AbstractTransform):

    def __init__(
            self,
            kernel_h: int = 21,
            kernel_w: int = 21
    ) -> None:
        """MorphTophat, 顶帽变换, 形态学变换
        Args:
            kernel_h: Kernel size, 核的高, (0, 150, 1), 21
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 21
        """
        super().__init__(use_gpu=True)
        self.kernel = torch.ones((kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = K.morphology.top_hat(
            sample.image.unsqueeze(0).float(),
            kernel=self.kernel.to(sample.device),
        ).squeeze(0).byte()

        return sample


class MorphBlackhat(AbstractTransform):

    def __init__(
            self,
            kernel_h: int = 21,
            kernel_w: int = 21
    ) -> None:
        """MorphBlackhat, 底帽变换, 形态学变换

        Args:
            kernel_h: Kernel size, 核的高, (0, 150, 1), 21
            kernel_w: Kernel size, 核的宽, (0, 150, 1), 21
        """
        super().__init__(use_gpu=True)
        self.kernel = torch.ones((kernel_h, kernel_w))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample = GrayScale()(sample)
        sample.image = K.morphology.bottom_hat(
            sample.image.unsqueeze(0).float(),
            kernel=self.kernel.to(sample.device),
        ).squeeze(0).byte()

        return sample
