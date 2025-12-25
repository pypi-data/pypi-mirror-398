#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
author：yannan1
since：2023-06-16
"""
import random
from typing import Union, Sequence

import cv2 as cv
import numpy as np
from imgaug import augmenters as iaa

from ..common import AbstractTransform, ImgaugAdapter, eval_arg, DEFAULT_IMAGE_FIELD

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
    'KMeansColor',
    # 'CLAHE',
    'RandomBrightness',
    'RandomSaturation',
    'RandomContrast',
    'RandomColor',
    'RandomHue',
    'RandomSharpness',
    'RandomGamma',
    'RandomEqualize',
    'RandomPosterize',
    'RandomKMeansColor',
]

ATTRS = [DEFAULT_IMAGE_FIELD]


class GrayScale(ImgaugAdapter):

    def __init__(self):
        """GrayScale, 灰度变换, 颜色变换
        """
        super().__init__(iaa.Grayscale(), ATTRS)


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
        super().__init__(use_gpu=False)

        in_black = eval_arg(in_black, None)
        in_white = eval_arg(in_white, None)
        gamma = eval_arg(gamma, None)
        out_black = eval_arg(out_black, None)
        out_white = eval_arg(out_white, None)

        self.in_black = in_black
        if not isinstance(self.in_black, (int, float, np.ndarray)):
            self.in_black = np.array(self.in_black, dtype=np.float32)

        self.in_white = in_white
        if not isinstance(self.in_white, (int, float, np.ndarray)):
            self.in_white = np.array(self.in_white, dtype=np.float32)

        self.gamma = gamma
        if not isinstance(self.gamma, (int, float, np.ndarray)):
            self.gamma = np.array(self.gamma, dtype=np.float32)

        self.out_black = out_black
        if not isinstance(self.out_black, (int, float, np.ndarray)):
            self.out_black = np.array(self.out_black, dtype=np.float32)

        self.out_white = out_white
        if not isinstance(self.out_white, (int, float, np.ndarray)):
            self.out_white = np.array(self.out_white, dtype=np.float32)

    def _apply(self, sample):

        if sample.image is None:
            return sample

        x = np.array(sample.image, dtype=np.float32)

        x -= self.in_black
        x /= self.in_white - self.in_black
        np.clip(x, 0, 1, x)

        x **= 1 / self.gamma
        x *= self.out_white - self.out_black
        x += self.out_black
        np.clip(x, 0, 255, x)

        sample.image = np.array(x, dtype=np.uint8)

        return sample


class AdjustExposure(AbstractTransform):
    def __init__(
            self,
            min_value: int = 170,
            max_value: int = 255,
            algorithm: str = "ns",
            radius: int = 3,
    ) -> None:
        """AdjustExposure, 曝光矫正, 颜色变换

        Args:
            min_value: Lower bound, 图像阈值下限, [0, 255, 1], 170
            max_value: Upper bound, 图像阈值上限, [0, 255, 1], 255
            algorithm: Inpaint algorithm, 图像修复算法, {"telea", "ns"}, "ns"
            radius: Inpaint Radius, 修复邻域半径, [1, 10, 1], 3
        """
        super().__init__(use_gpu=False)
        self.min_value = eval_arg(min_value, None)
        self.max_value = eval_arg(max_value, None)
        self.algorithm = algorithm
        self.radius = eval_arg(radius, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample
        
        lab = cv.cvtColor(sample.image, cv.COLOR_BGR2LAB)
        l_channel, _, _ = cv.split(lab)

        _, mask = cv.threshold(l_channel, self.min_value, self.max_value, cv.THRESH_BINARY)
        mask = cv.GaussianBlur(mask, (5,5), 0)
        if np.sum(mask) != 0:
            if self.algorithm == "telea":
                algo_flag = cv.INPAINT_TELEA
            elif self.algorithm == "ns":
                algo_flag = cv.INPAINT_NS
            adjust_result = cv.inpaint(sample.image, mask, inpaintRadius=self.radius, flags=algo_flag)
            sample.image = adjust_result

        return sample


class Brightness(ImgaugAdapter):

    def __init__(self, factor: float = 1.0) -> None:
        """Brightness, 亮度变换, 颜色变换

        Args:
            factor: Brightness factor, 亮度系数, [0.0, 10.0, 0.1], 1.0
        """
        factor = eval_arg(factor, None)
        super().__init__(iaa.MultiplyBrightness(
            mul=factor,
            to_colorspace=iaa.CSPACE_HSV,
        ), ATTRS)


class Saturation(ImgaugAdapter):

    def __init__(self, factor=1.0):
        """Saturation, 饱和度变换, 颜色变换

        Args:
            factor: Saturation factor, 饱和度系数, [0.0, 10.0, 0.1], 1.0
        """
        factor = eval_arg(factor, None)
        super().__init__(iaa.MultiplySaturation(factor), ATTRS)


class Contrast(ImgaugAdapter):

    def __init__(self, factor: float = 1.0) -> None:
        """Contrast, 对比度变换, 颜色变换

        Args:
            factor: Contrast factor, 对比度系数, [0.0, 10.0, 0.1], 1.0
        """
        factor = eval_arg(factor, None)
        super().__init__(iaa.LinearContrast(alpha=factor), ATTRS)


class Hue(ImgaugAdapter):

    def __init__(self, factor: float = 0.0) -> None:
        """Hue, 色调变换, 颜色变换

        Args:
            factor: Hue factor, 色调系数, [-0.5, 0.5, 0.1], 0.0
        """
        factor = eval_arg(factor, None)
        factor = int(factor * 255)

        super().__init__(iaa.AddToHue(factor), ATTRS)


class Sharpness(AbstractTransform):

    def __init__(self, factor: float = 1.0) -> None:
        """Sharpness, 锐度变换, 颜色变换

        Args:
            factor: Sharpness factor, 锐度系数, [0.0, 10.0, 0.1], 1.0
        """
        super().__init__(use_gpu=False)
        self.factor = eval_arg(factor, None)

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = iaa.pillike.enhance_sharpness(sample.image, factor=self.factor)
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
            gain: Gain, 乘数, [0.1, 10.0, 0.1], 1.0
        """
        super().__init__(use_gpu=False)

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
        image = (255 * gain * (sample.image / 255) ** gamma)
        sample.image = np.clip(image, 0, 255).astype(np.uint8)

        return sample


class Equalize(ImgaugAdapter):

    def __init__(self) -> None:
        """Equalize, 直方图均衡化变换, 颜色变换
        """
        super().__init__(iaa.HistogramEqualization(), ATTRS)


class Posterize(ImgaugAdapter):

    def __init__(self, bits: int = 2) -> None:
        """Posterize, 通道颜色变换, 颜色变换

        Args:
            bits: Channel color bits, 通道颜色位数, [1, 8, 1], 2
        """
        bits = eval_arg(bits, int)
        super().__init__(iaa.Posterize(nb_bits=bits), ATTRS)


class KMeansColor(ImgaugAdapter):

    def __init__(self, n_colors: int = 5, interpolation: str = 'nearest') -> None:
        """KMeansColor, K均值颜色变换, 颜色变换

        Args:
            n_colors: Number of clusters in k-Means, 簇数, [2, 16, 1], 5
            interpolation: Interpolation, 插值模式, {"nearest", "linear", "cubic", "area"}, "nearest"
        """
        n_colors = eval_arg(n_colors, int)
        super().__init__(
            iaa.KMeansColorQuantization(n_colors=n_colors,
                                        from_colorspace=iaa.CSPACE_RGB,
                                        to_colorspace=iaa.CSPACE_RGB,
                                        interpolation=interpolation), ATTRS)


class CLAHE(AbstractTransform):

    def __init__(self, clip_limit: float = 1.0, gw: int = 2, gh: int = 2) -> None:
        """CLAHE, 限制对比度自适应直方图均衡, 颜色变换

        Args:
            clip_limit: Clip limit, 截止对比度, [0.1, 8.0, 0.1], 1.0
            gh: Grid width, 网格宽度, [1, 16, 1], 2
            gw: Grid height, 网格高度, [1, 16, 1], 2
        """
        super().__init__(use_gpu=False)

        clip_limit = eval_arg(clip_limit, None)
        gw = eval_arg(gw, int)
        gh = eval_arg(gh, int)
        self.impl = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=(gw, gh))

    def _apply(self, sample):

        if sample.image is None:
            return sample

        if len(sample.image.shape) > 2:
            img_yuv = cv.cvtColor(sample.image, cv.COLOR_BGR2YUV)
            img_yuv[:, :, 0] = self.impl.apply(img_yuv[:, :, 0])
            sample.image = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR)
        else:
            sample.image = self.impl.apply(sample.image)

        return sample


class RandomSaturation(ImgaugAdapter):

    def __init__(self, factor_min: float = 0.0, factor_max: float = 2.0) -> None:
        """RandomSaturation, 随机饱和度变换, 颜色变换

        Args:
            factor_min: Saturation minimum, 饱和度系数最小值, [0.0, 3.0, 0.1], 0.0
            factor_max: Saturation maximum, 饱和度系数最大值, [0.0, 3.0, 0.1], 2.0
        """
        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)
        super().__init__(iaa.MultiplySaturation((factor_min, factor_max)), ATTRS)


class RandomColor(ImgaugAdapter):

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
            rnd_hue: Hue factor, 色调系数, [-0.5, 0.5, 0.01], 0.05
        """
        rnd_brightness = eval_arg(rnd_brightness, None)
        rnd_contrast = eval_arg(rnd_contrast, None)
        rnd_saturation = eval_arg(rnd_saturation, None)
        rnd_hue = eval_arg(rnd_hue, None)

        if isinstance(rnd_hue, float):
            h = (-int(rnd_hue * 255), int(rnd_hue * 255))
        elif rnd_hue is None:
            h = None
        else:
            raise RuntimeError(f'Invalid hue_shift {rnd_hue}.')

        if isinstance(rnd_saturation, float):
            s = (max(1.0 - rnd_saturation, 0), 1.0 + rnd_saturation)
        elif rnd_saturation is None:
            s = None
        else:
            raise RuntimeError(f'Invalid saturation_factor {rnd_saturation}.')

        if isinstance(rnd_brightness, float):
            v = (max(1.0 - rnd_brightness, 0), 1.0 + rnd_brightness)
        elif rnd_brightness is None:
            v = None
        else:
            raise RuntimeError(f'Invalid brightness_factor {rnd_brightness}.')

        if isinstance(rnd_contrast, float):
            c = (max(1.0 - rnd_contrast, 0), 1.0 + rnd_contrast)
        elif rnd_contrast is None:
            c = None
        else:
            raise RuntimeError(f'Invalid contrast_factor {rnd_contrast}.')

        super(RandomColor, self).__init__(
            iaa.Sequential([
                iaa.WithColorspace(from_colorspace=iaa.CSPACE_RGB,
                                   to_colorspace=iaa.CSPACE_HSV,
                                   children=iaa.Sequential([
                                       iaa.WithChannels(0, iaa.Add(h)) if h else iaa.Identity(),
                                       iaa.WithChannels(1,
                                                        iaa.Multiply(s)) if s else iaa.Identity(),
                                       iaa.WithChannels(2, iaa.Multiply(v)) if v else iaa.Identity()
                                   ])) if (h and s and v) else iaa.Identity(),
                iaa.LinearContrast(c) if c else iaa.Identity()
            ]), ATTRS)


class RandomBrightness(ImgaugAdapter):

    def __init__(self, factor_min: float = 0.0, factor_max: float = 2.0) -> None:
        """RandomBrightness, 随机亮度变换, 颜色变换

        Args:
            factor_min: Brightness minimum, 亮度系数最小值, [0.0, 2.0, 0.1], 0.0
            factor_max: Brightness maximum, 亮度系数最大值, [0.0, 2.0, 0.1], 2.0
        """
        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)

        super().__init__(iaa.MultiplyBrightness(
            mul=(factor_min, factor_max),
            to_colorspace=iaa.CSPACE_HSV,
        ), ATTRS)


class RandomContrast(ImgaugAdapter):

    def __init__(self, factor_min: float = 0.0, factor_max: float = 2.0) -> None:
        """RandomContrast, 随机对比度变换, 颜色变换

        Args:
            factor_min: Contrast minimum, 对比度系数最小值, [0.0, 2.0, 0.1], 0.0
            factor_max: Contrast maximum, 对比度系数最大值, [0.0, 2.0, 0.1], 2.0
        """
        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)
        super().__init__(iaa.LinearContrast(alpha=(factor_min, factor_max)), ATTRS)


class RandomHue(ImgaugAdapter):

    def __init__(self, factor_min: float = -0.5, factor_max: float = 0.5) -> None:
        """RandomHue, 随机色调变换, 颜色变换

        Args:
            factor_min: Hue minimum, 色调系数最小值, [-0.5, 0.5, 0.1], -0.5
            factor_max: Hue maximum, 色调系数最大值, [-0.5, 0.5, 0.1], 0.5
        """
        factor_min = eval_arg(factor_min, None)
        factor_max = eval_arg(factor_max, None)
        factor = (int(factor_min * 255), int(factor_max * 255))

        super().__init__(iaa.AddToHue(value=factor), ATTRS)


class RandomSharpness(Sharpness):

    def __init__(self, factor: float = 1.0, p: float = 0.5) -> None:
        """RandomSharpness, 随机锐度变换, 颜色变换

        Args:
            factor: Sharpness factor, 锐度系数, [0.0, 2.0, 0.1], 1.0
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
        """
        self.p = eval_arg(p, None)
        factor = eval_arg(factor, None)
        super().__init__(factor)

    def _apply(self, sample):
        if random.random() < self.p:
            sample = super()._apply(sample)

        return sample


class RandomGamma(Gamma):

    def __init__(
            self,
            gamma_min: float = 0.1,
            gamma_max: float = 3.0,
            gain_min: float = 0.1,
            gain_max: float = 10
    ) -> None:
        """RandomGamma, 随机伽玛校正变换, 颜色变换

        Args:
            gamma_min: Gamma minimum, 伽玛校正系数最小值, [0.1, 3.0, 0.1], 1.0
            gamma_max: Gamma maximum, 伽玛校正系数最大值, [0.1, 3.0, 0.1], 3.0
            gain_min: Gain minimum, 乘数最小值, [0.1, 10.0, 0.1], 0.1
            gain_max: Gain maximum, 乘数最大值, [0.1, 10.0, 0.1], 10.0
        """
        gamma_min = eval_arg(gamma_min, None)
        gamma_max = eval_arg(gamma_max, None)

        gain_min = eval_arg(gain_min, None)
        gain_max = eval_arg(gain_max, None)
        super().__init__(gamma=(gamma_min, gamma_max), gain=(gain_min, gain_max))


class RandomEqualize(ImgaugAdapter):

    def __init__(self, p: float = 0.5) -> None:
        """RandomEqualize, 随机均衡直方图, 颜色变换

        Args:
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
        """
        p = eval_arg(p, None)
        super().__init__(
            iaa.HistogramEqualization() if np.random.rand(1) < p else iaa.Identity(),
            ATTRS
        )


class RandomPosterize(ImgaugAdapter):

    def __init__(self, bits_min: int = 1, bits_max: int = 8, p: float = 0.5) -> None:
        """RandomPosterize, 随机通道颜色变换, 颜色变换

        Args:
            bits_min: Channel color bits minimum, 通道颜色位数最小值, [1, 8, 1], 1
            bits_max: Channel color bits maximum, 通道颜色位数最大值, [1, 8, 1], 8
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
        """
        bits_min = eval_arg(bits_min, int)
        bits_max = eval_arg(bits_max, int)
        p = eval_arg(p, None)
        super().__init__(iaa.Posterize(nb_bits=(bits_min, bits_max)) if np.random.rand(
            1) < p else iaa.Identity(), ATTRS)


class RandomKMeansColor(ImgaugAdapter):

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
            interpolation: Interpolation, 插值模式, {"nearest", "linear", "cubic", "area"}, "nearest"
        """
        k_min = eval_arg(n_colors_min, int)
        k_max = eval_arg(n_colors_max, int)

        super().__init__(
            iaa.KMeansColorQuantization(
                n_colors=(k_min, k_max),
                from_colorspace=iaa.CSPACE_RGB,
                to_colorspace=iaa.CSPACE_RGB,
                interpolation=interpolation),
            ATTRS,
        )
