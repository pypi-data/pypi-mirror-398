#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
author：yannan1
since：2023-05-31
"""
from typing import Union, Sequence

import torch
import random
import kornia as K
from torch import Tensor
import torch.nn as nn
from torchvision.transforms import transforms, InterpolationMode, functional as TF

from .kmeans import KMeans
from ..common import eval_arg, AbstractTransform

__all__ = [
    'GrayScale',
    'AdjustColorLevels',
    'AdjustExposure',
    'Brightness',
    'Saturation',
    'Contrast',
    'Hue',
    'Gamma',
    'Sharpness',
    'Equalize',
    'Posterize',
    'CLAHE',
    'KMeansColor',
    'RandomBrightness',
    'RandomSaturation',
    'RandomContrast',
    'RandomColor',
    'RandomHue',
    'RandomGamma',
    'RandomSharpness',
    'RandomEqualize',
    'RandomPosterize',
    # 'RandomKMeansColor',
]


class GrayScale(AbstractTransform):

    def __init__(self):
        """GrayScale, 灰度变换, 颜色变换
        """
        super().__init__(use_gpu=True)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        if sample.shape[0] != 1:
            sample.image = transforms.Grayscale(num_output_channels=1)(sample.image)
        return sample


class AdjustColorLevels(AbstractTransform):

    def __init__(
            self,
            in_black: int = 0,
            in_white: int = 255,
            gamma: float = 1.0,
            out_black: int = 0,
            out_white: int = 255
    ) -> None:
        """AdjustColorLevels, 色阶, 颜色变换

        Args:
            in_black: Input black, 输入截止黑色, [0, 255, 1], 0
            in_white: Input white, 输入截止白色, [0, 255, 1], 255
            gamma: Gamma, Gamma值, [0.1, 3.0, 0.1], 1.0
            out_black: Output black, 输出截止黑色, [0, 255, 1], 0
            out_white: Output white, 输出截止白色, [0, 255, 1], 255
        """
        super().__init__(use_gpu=True)

        in_black = eval_arg(in_black, None)
        in_white = eval_arg(in_white, None)
        gamma = eval_arg(gamma, None)
        out_black = eval_arg(out_black, None)
        out_white = eval_arg(out_white, None)

        self.in_black = in_black
        if not isinstance(self.in_black, (int, float, Tensor)):
            self.in_black = torch.tensor(self.in_black, dtype=torch.float32).cuda()

        self.in_white = in_white
        if not isinstance(self.in_white, (int, float, Tensor)):
            self.in_white = torch.tensor(self.in_white, dtype=torch.float32).cuda()

        self.gamma = gamma
        if not isinstance(self.gamma, (int, float, Tensor)):
            self.gamma = torch.tensor(self.gamma, dtype=torch.float32).cuda()

        self.out_black = out_black
        if not isinstance(self.out_black, (int, float, Tensor)):
            self.out_black = torch.tensor(self.out_black, dtype=torch.float32).cuda()

        self.out_white = out_white
        if not isinstance(self.out_white, (int, float, Tensor)):
            self.out_white = torch.tensor(self.out_white, dtype=torch.float32).cuda()

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = sample.image.float()
        image -= self.in_black
        image /= self.in_white - self.in_black

        torch.clip(image, 0, 1, out=image)

        image = torch.pow(image, 1 / self.gamma)
        image *= self.out_white - self.out_black
        image += self.out_black
        torch.clip(image, 0, 255, out=image)

        sample.image = image.byte()

        return sample


class AdjustExposure(AbstractTransform):
    # @liying50
    def __init__(
            self,
            threshold: int = 150,
            levels: int = 10, # 高亮部灰度细节等级(0-50)，值越大高亮部分细节越丰富
            gamma: float = 0.8 # Gamma校正
    ) -> None:
        """AdjustExposure, 曝光校正, 颜色变换

        Args:
            threshold: Threshold, 图像阈值,值越大越是提取高亮部分, [0, 255, 1], 150
            levels: Levels, 细节等级,值越大高亮部分细节越丰富, [0, 255, 1], 50
            gamma: Gamms, Gamma校正系数, [0.1, 3.0, 0.1], 0.8
        """
        super().__init__(use_gpu=True)
        self.threshold = eval_arg(threshold, None)
        self.levels = eval_arg(levels, None)
        self.gamma = eval_arg(gamma, None)
    
    def _apply(self, sample):
        if sample.image is None:
            return sample
        image = sample.image.float()

        # 高亮区域检测
        mask = image > self.threshold
        if not torch.any(mask):  # 无高亮区域直接返回
            return sample
        
        # 高亮压缩和Gamma校正
        compressed = ((image[mask] - self.threshold) / ((255.0 - self.threshold)) * self.levels)
        corrected = torch.clamp((compressed ** self.gamma) + self.threshold, 0.0, 255.0)
        image[mask] = corrected

        # 均值滤波
        padded_image = transforms.Pad(padding=1, padding_mode='reflect')(image)
        smoothed_image = nn.AvgPool2d(3, stride=1)(padded_image)
        image[mask] = smoothed_image[mask]
        sample.image = image.to(torch.uint8)
        return sample


class Brightness(AbstractTransform):

    def __init__(self, factor: float = 1.0) -> None:
        """Brightness, 亮度变换, 颜色变换

        Args:
            factor: Brightness factor, 亮度系数, [0.0, 10.0, 0.1], 1.0
        """
        super().__init__(use_gpu=True)
        self.factor = eval_arg(factor, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.adjust_brightness(sample.image, brightness_factor=self.factor)

        return sample


class Saturation(AbstractTransform):

    def __init__(self, factor: float = 1.0) -> None:
        """Saturation, 饱和度变换, 颜色变换

        Args:
            factor: Saturation factor, 饱和度系数, [0.0, 10.0, 0.1], 1.0
        """
        super().__init__(use_gpu=True)
        self.factor = eval_arg(factor, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.adjust_saturation(sample.image, saturation_factor=self.factor)

        return sample


class Contrast(AbstractTransform):

    def __init__(self, factor: float = 1.0) -> None:
        """Contrast, 对比度变换, 颜色变换

        Args:
            factor: Contrast factor, 对比度系数, [0.0, 10.0, 0.1], 1.0
        """
        super().__init__(use_gpu=True)
        self.factor = eval_arg(factor, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.adjust_contrast(sample.image, contrast_factor=self.factor)

        return sample


class Sharpness(AbstractTransform):

    def __init__(self, factor: float = 1.0) -> None:
        """Sharpness, 锐度变换, 颜色变换

        Args:
            factor: Sharpness factor, 锐度系数, [0.0, 10.0, 0.1], 1.0
        """
        super().__init__(use_gpu=True)
        self.factor = eval_arg(factor, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.adjust_sharpness(sample.image, sharpness_factor=self.factor)

        return sample


class Hue(AbstractTransform):

    def __init__(self, factor: float = 0.0) -> None:
        """Hue, 色调变换, 颜色变换

        Args:
            factor: Hue factor, 色调系数, [-0.5, 0.5, 0.1], 0.0
        """
        super().__init__(use_gpu=True)
        self.factor = eval_arg(factor, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.adjust_hue(sample.image, hue_factor=self.factor)

        return sample


class Gamma(AbstractTransform):

    def __init__(
            self,
            gamma: Union[float, Sequence] = 1.0,
            gain: Union[float, Sequence] = 1.0
    ) -> None:
        """Gamma, 伽玛校正变换, 颜色变换

        Args:
            gamma: Gamma, 伽玛校正系数, [0.1, 3.0, 0.1], 1.0
            gain: Gain, 乘数, [0.1, 10, 0.1], 1.0
        """
        super().__init__(use_gpu=True)

        self.gamma = eval_arg(gamma, None)
        self.gain = eval_arg(gain, None)

    def _get_params(self):

        if isinstance(self.gamma, Sequence):
            gamma = random.uniform(self.gamma[0], self.gamma[1])
        else:
            gamma = eval_arg(self.gamma, float)

        if isinstance(self.gain, Sequence):
            gain = random.uniform(self.gain[0], self.gain[1])
        else:
            gain = eval_arg(self.gain, float)

        return gamma, gain

    def _apply(self, sample):
        if sample.image is None:
            return sample

        gamma, gain = self._get_params()
        image = sample.image.float()
        sample.image = (255 * gain * (image / 255) ** gamma).clamp(0, 255).byte()

        return sample


class Equalize(AbstractTransform):

    def __init__(self) -> None:
        """Equalize, 直方图均衡化变换, 颜色变换
        """
        super().__init__(use_gpu=True)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.equalize(sample.image)

        return sample


class Posterize(AbstractTransform):

    def __init__(self, bits: int = 2) -> None:
        """Posterize, 通道颜色变换, 颜色变换

        Args:
            bits: Channel color bits, 通道颜色位数, [1, 8, 1], 2
        """
        super().__init__(use_gpu=True)
        self.bits = eval_arg(bits, int)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = TF.posterize(sample.image, bits=self.bits)

        return sample


class KMeansColor(AbstractTransform):

    def __init__(
            self,
            n_colors: Union[int, Sequence] = 5,
            interpolation: str = 'bilinear'
    ) -> None:
        """KMeansColor, K均值颜色变换, 颜色变换

        Args:
            n_colors: Number of clusters in k-Means, 簇数, [2, 16, 1], 5
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear", "bicubic"}, "bilinear"
        """
        super().__init__(use_gpu=True)

        self.max_size = 128
        self.interpolation = InterpolationMode[interpolation.upper()]
        self.n_colors = eval_arg(n_colors, int)

    def _get_params(self):
        if isinstance(self.n_colors, Sequence):
            n_colors = random.randint(self.n_colors[0], self.n_colors[1])
        else:
            n_colors = eval_arg(self.n_colors, int)

        return n_colors

    def _apply(self, sample):
        if sample.image is None:
            return sample

        n_colors = self._get_params()
        kmeans = KMeans(n_clusters=n_colors)

        image = sample.image
        size = max(sample.shape[1], sample.shape[2])
        orig_shape = sample.shape

        if size > self.max_size:
            image = TF.resize(image, [self.max_size, self.max_size], self.interpolation)

        image = image.permute((1, 2, 0))

        X = image.view(-1, sample.shape[0])
        out = kmeans.fit_predict(X).view_as(image).permute((2, 0, 1))

        if orig_shape != out.shape:
            out = TF.resize(out, orig_shape[1:], self.interpolation)

        sample.image = out.byte()

        return sample


class CLAHE(AbstractTransform):

    def __init__(self, clip_limit: float = 1.0, gw: int = 2, gh: int = 2) -> None:
        """CLAHE, 限制对比度自适应直方图均衡, 颜色变换

        Args:
            clip_limit: Clip limit, 截止对比度, [0.1, 8.0, 0.1], 1.0
            gh: Grid width, 网格宽度, [1, 16, 1], 2
            gw: Grid height, 网格高度, [1, 16, 1], 2
        """
        super().__init__(use_gpu=True)

        self.clip_limit = eval_arg(clip_limit, float)
        self.gw = int(eval_arg(gw, int))
        self.gh = int(eval_arg(gh, int))

        if self.gw != self.gh:
            self.gw = self.gh = max(self.gh, self.gw)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = K.enhance.equalize_clahe(
            input=torch.clip(sample.image / 255, 0, 1),
            clip_limit=self.clip_limit,
            grid_size=(self.gh, self.gw)
        ) * 255
        sample.image = image.byte()

        return sample


class RandomBrightness(AbstractTransform):

    def __init__(self, factor_min: float = 0.0, factor_max: float = 2.0) -> None:
        """RandomBrightness, 随机亮度变换, 颜色变换

        Args:
            factor_min: Brightness minimum, 亮度系数最小值, [0.0, 2.0, 0.1], 0.0
            factor_max: Brightness maximum, 亮度系数最大值, [0.0, 2.0, 0.1], 2.0
        """
        super().__init__(use_gpu=True)

        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)
        self.operator = transforms.ColorJitter(brightness=(factor_min, factor_max))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomSaturation(AbstractTransform):

    def __init__(self, factor_min: float = 0.0, factor_max: float = 2.0) -> None:
        """RandomSaturation, 随机饱和度变换, 颜色变换

        Args:
            factor_min: Saturation minimum, 饱和度系数最小值, [0.0, 2.0, 0.1], 0.0
            factor_max: Saturation maximum, 饱和度系数最大值, [0.0, 2.0, 0.1], 2.0
        """
        super().__init__(use_gpu=True)

        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)

        self.operator = transforms.ColorJitter(saturation=(factor_min, factor_max))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomContrast(AbstractTransform):

    def __init__(self, factor_min: float = 0.0, factor_max: float = 2.0) -> None:
        """RandomContrast, 随机对比度变换, 颜色变换

        Args:
            factor_min: Contrast minimum, 对比度系数最小值, [0.0, 2.0, 0.1], 0.0
            factor_max: Contrast maximum, 对比度系数最大值, [0.0, 2.0, 0.1], 2.0
        """
        super().__init__(use_gpu=True)

        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)
        self.operator = transforms.ColorJitter(contrast=(factor_min, factor_max))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomSharpness(AbstractTransform):

    def __init__(self, factor: float = 1.0, p: float = 0.5) -> None:
        """RandomSharpness, 随机锐度变换, 颜色变换

        Args:
            factor: Sharpness factor, 锐度系数, [0.0, 2.0, 0.1], 1.0
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
        """
        super().__init__(use_gpu=True)

        factor = eval_arg(factor, None)
        p = eval_arg(p, None)
        self.operator = transforms.RandomAdjustSharpness(sharpness_factor=factor, p=p)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomHue(AbstractTransform):

    def __init__(self, factor_min: float = -0.5, factor_max: float = 0.5) -> None:
        """RandomHue, 随机色调变换, 颜色变换

        Args:
            factor_min: Hue minimum, 色调系数最小值, [-0.5, 0.5, 0.1], -0.5
            factor_max: Hue maximum, 色调系数最大值, [-0.5, 0.5, 0.1], 0.5
        """
        super().__init__(use_gpu=True)

        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)
        self.operator = transforms.ColorJitter(hue=(factor_min, factor_max))

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomGamma(Gamma):

    def __init__(
            self,
            gamma_min: float = 0.1,
            gamma_max: float = 3.0,
            gain_min: float = 0.1,
            gain_max: float = 10.0
    ) -> None:
        """RandomGamma, 随机伽玛校正变换, 颜色变换

        Args:
            gamma_min: Gamma minimum, 伽玛校正系数最小值, [0.1, 3.0, 0.1], 0.1
            gamma_max: Gamma maximum, 伽玛校正系数最大值, [0.1, 3.0, 0.1], 3.0
            gain_min: Gain minimum, 乘数最小值, [0.1, 10.0, 0.1], 0.1
            gain_max: Gain maximum, 乘数最大值, [0.1, 10.0, 0.1], 10.0
        """
        gamma_min = eval_arg(gamma_min, None)
        gamma_max = eval_arg(gamma_max, None)

        gain_min = eval_arg(gain_min, None)
        gain_max = eval_arg(gain_max, None)
        super().__init__(gamma=(gamma_min, gamma_max), gain=(gain_min, gain_max))


class RandomColor(AbstractTransform):

    def __init__(
            self,
            rnd_brightness: float = 0.2,
            rnd_contrast: float = 0.2,
            rnd_saturation: float = 0.2,
            rnd_hue: float = 0.05
    ) -> None:
        """RandomColor, 随机颜色变换, 颜色变换

        Args:
            rnd_brightness: Brightness factor, 亮度系数, [0.0, 2.0, 0.1], 0.2
            rnd_contrast: Contrast factor, 对比度系数, [0.0, 2.0, 0.1], 0.2
            rnd_saturation: Saturation factor, 饱和度系数, [0.0, 2.0, 0.1], 0.2
            rnd_hue: Hue factor, 色调系数, [0.0, 0.5, 0.01], 0.05
        """
        super().__init__(use_gpu=True)

        rnd_brightness = eval_arg(rnd_brightness, None)
        rnd_contrast = eval_arg(rnd_contrast, None)
        rnd_saturation = eval_arg(rnd_saturation, None)
        rnd_hue = eval_arg(rnd_hue, None)

        rnd_brightness = 0 if rnd_brightness is None else rnd_brightness
        rnd_contrast = 0 if rnd_contrast is None else rnd_contrast
        rnd_saturation = 0 if rnd_saturation is None else rnd_saturation
        rnd_hue = 0 if rnd_hue is None else rnd_hue

        self.operator = transforms.ColorJitter(
            brightness=rnd_brightness,
            contrast=rnd_contrast,
            saturation=rnd_saturation,
            hue=rnd_hue)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomEqualize(AbstractTransform):

    def __init__(self, p: float = 0.5) -> None:
        """RandomEqualize, 随机均衡直方图, 颜色变换

        Args:
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
        """
        super().__init__(use_gpu=True)

        p = eval_arg(p, None)
        self.operator = transforms.RandomEqualize(p=p)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self.operator(sample.image)
        return sample


class RandomPosterize(AbstractTransform):

    def __init__(self, bits_min: int = 1, bits_max: int = 8, p: float = 0.5) -> None:
        """RandomPosterize, 随机通道颜色变换, 颜色变换

        Args:
            bits_min: Channel color bits minimum, 通道颜色位数最小值, [1, 8, 1], 1
            bits_max: Channel color bits maximum, 通道颜色位数最大值, [1, 8, 1], 8
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
        """
        super().__init__(use_gpu=True)

        self.bits_min = eval_arg(bits_min, int)
        self.bits_max = eval_arg(bits_max, int)
        self.p = eval_arg(p, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        image = sample.image.type(torch.uint8)
        if torch.rand(1).item() < self.p:
            bits = random.randint(self.bits_min, self.bits_max)
            sample.image = TF.posterize(image, bits).float()

        return sample


class RandomKMeansColor(KMeansColor):

    def __init__(
            self,
            n_colors_min: int = 2,
            n_colors_max: int = 16,
            interpolation: str = 'nearest'
    ) -> None:
        """RandomKMeansColor, 随机K均值颜色变换, 颜色变换

        Args:
            n_colors_min: Minimum of clusters in k-Means, 簇数最小值, [2, 16, 1], 2
            n_colors_max: Maximum of clusters in k-Means, 簇数最小值, [2, 16, 1], 16
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear", "bicubic"}, "bilinear"
        """
        n_colors_min = eval_arg(n_colors_min, int)
        n_colors_max = eval_arg(n_colors_max, int)

        super().__init__(
            n_colors=(n_colors_min, n_colors_max),
            interpolation=interpolation
        )
