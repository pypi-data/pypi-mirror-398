#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-06-15
"""
import math
import random
from typing import Any

import numpy as np
from imgaug import augmenters as iaa

from ..common import AbstractSample, eval_arg, ImgaugAdapter, AbstractTransform, apply_augmenter
from ..common import DEFAULT_IMAGE_FIELD, DEFAULT_MASK_FIELD, DEFAULT_BBOX_FIELD, \
    DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD

__all__ = [
    'Resize',
    'CenterCrop',
    'Crop',
    'CropToFixedSize',
    'Pad',
    'PadToFixedSize',
    'RandomResize',
    'RandomCrop',
    'RandomResizedCrop',
]

ATTRS = [DEFAULT_IMAGE_FIELD, DEFAULT_MASK_FIELD, DEFAULT_BBOX_FIELD,
         DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD]


class Resize(ImgaugAdapter):

    def __init__(
            self,
            height: int = 224,
            width: int = 224,
            interpolation: str = "cubic"
    ) -> None:
        """Resize, 缩放变换, 尺寸变换

        Args:
            height: Height, 缩放高度, [0, 1000, 1], 224
            width: Width, 缩放宽度, [0, 1000, 1], 224
            interpolation: Interpolation, 插值模式, {"nearest", "linear", "cubic", "area"}, "cubic"
        """
        height = eval_arg(height, None)
        width = eval_arg(width, None)

        if isinstance(height, float):
            height = int(height)
        if isinstance(width, float):
            width = int(width)
        
        self.to_h = height
        self.to_w = width
        if height is None or width is None:
            super().__init__(iaa.Identity(), ATTRS)
        else:
            super().__init__(
                iaa.Resize({'height': height, 'width': width, 'interpolation': interpolation}),
                ATTRS
            )
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        h, w = input_shape[:2]
        scale_x = self.to_w / w
        scale_y = self.to_h / h
        self.matrix = np.array([
            [scale_x, 0, 0],
            [0, scale_y, 0],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class CenterCrop(ImgaugAdapter):

    def __init__(self, height: int = 224, width: int = 224) -> None:
        """CenterCrop, 中心裁剪, 尺寸变换

        Args:
            height: Height, 裁剪高度, [0, 65536, 1], 224
            width: Width, 裁剪宽度, [0, 65536, 1], 224
        """
        height = eval_arg(height, None)
        width = eval_arg(width, None)

        if isinstance(height, float):
            height = int(height)
        if isinstance(width, float):
            width = int(width)
        
        self.to_h = height
        self.to_w = width

        super().__init__(iaa.CenterCropToFixedSize(height=height, width=width), ATTRS)


class Crop(ImgaugAdapter):

    def __init__(
            self,
            top: int = 0,
            right: int = 0,
            bottom: int = 0,
            left: int = 0
    ) -> None:
        """Crop, 裁剪, 尺寸变换

        Args:
            top: Vertical distance to the top, 向上的垂直距离, [0, 1000, 1], 0
            right: Horizontal distance to the right, 向右的水平距离, [0, 1000, 1], 0
            bottom: Vertical distance to the bottom, 向下的垂直距离, [0, 1000, 1], 0
            left: Horizontal distance to the left, 向左的水平距离, [0, 1000, 1], 0
        """
        top = eval_arg(top, None)
        right = eval_arg(right, None)
        bottom = eval_arg(bottom, None)
        left = eval_arg(left, None)
        super().__init__(iaa.Crop(px=(top, right, bottom, left), keep_size=False), ATTRS)
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        h, w = input_shape[:2]
        x = (w - self.to_w) // 2
        y = (h - self.to_h) // 2
        self.matrix = np.array([
            [1, 0, -x],
            [0, 1, -y],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class CropToFixedSize(ImgaugAdapter):

    def __init__(self, height: int = 224, width: int = 224, position='center') -> None:
        """PadToFixedSize, 固定尺寸裁剪, 尺寸变换

        Args:
            height: Height, 裁剪高度, [0, 65536, 1], 224
            width: Width, 裁剪宽度, [0, 65536, 1], 224
            position: Postition, 裁剪位置, {"uniform", "normal", "center", "left-top", "left-center", "left-bottom", "center-top", "center-center", "center-bottom", "right-top", "right-center", "right-bottom"}, "center"
        """
        height = eval_arg(height, None)
        width = eval_arg(width, None)

        if isinstance(height, float):
            height = int(height)
        if isinstance(width, float):
            width = int(width)

        super().__init__(iaa.CropToFixedSize(height=height, width=width, position=position), ATTRS)    


class Pad(ImgaugAdapter):

    def __init__(
            self,
            px: Any = 1,
            pct: Any = 0.0,
            cval: int = 127,
            mode: str = 'constant'
    ) -> None:
        """Pad, 填充变换, 尺寸变换

        Args:
            px: Pixel, 填充像素, [0, 5000, 1], 1
            pct: Percentage, 填充百分比, [0.0, 1.0, 0.1], 0.0
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            mode: Fill mode, 填充模式, {"constant", "edge", "reflect"}, "constant"
        """
        px = eval_arg(px, None)
        pct = eval_arg(pct, None)

        if px is not None and pct is not None:
            pct = None

        super().__init__(iaa.Pad(
            px=px,
            percent=pct,
            pad_cval=cval,
            pad_mode=mode,
            keep_size=False
        ), ATTRS)
            
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        left = (output_sample.shape[1] - input_shape[1]) / 2
        top = (output_sample.shape[0] - input_shape[0]) / 2
        self.matrix = np.array([
            [1, 0, left],
            [0, 1, top],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class PadToFixedSize(ImgaugAdapter):
    
    def __init__(self, height: int = 224, width: int = 224, cval=255, mode='constant', position='center') -> None:
        """PadToFixedSize, 固定尺寸填充, 尺寸变换

        Args:
            height: Height, 填充高度, [0, 65536, 1], 224
            width: Width, 填充宽度, [0, 65536, 1], 224
            cval: Color Value, 填充颜色, [0, 255, 1], 255
            mode: Fill mode, 填充模式, {"constant", "edge", "reflect"}, "constant"
            position: Postition, 填充位置, {"uniform", "normal", "center", "left-top", "left-center", "left-bottom", "center-top", "center-center", "center-bottom", "right-top", "right-center", "right-bottom"}, "center"
        """
        height = eval_arg(height, None)
        width = eval_arg(width, None)

        if isinstance(height, float):
            height = int(height)
        if isinstance(width, float):
            width = int(width)

        super().__init__(iaa.PadToFixedSize(height=height, width=width, pad_mode=mode, pad_cval=cval, position=position), ATTRS)


class RandomResize(ImgaugAdapter):
    def __init__(
            self,
            rnd_resize_x: float = 0.0,
            rnd_resize_y: float = 0.0,
            interpolation: str = "linear"
    ) -> None:
        """RandomResize, 随机缩放变换, 尺寸变换

        Args:
            rnd_resize_x: Random resize x-axis ratio, x轴随机缩放比例, [0.0, 10.0, 0.1], 0.0
            rnd_resize_y: Random resize y-axis ratio, y轴随机缩放比例, [0.0, 10.0, 0.1], 0.0
            interpolation: Interpolation, 插值模式, {"nearest", "linear", "cubic", "area"}, 'linear'
        """

        assert rnd_resize_x >= 0
        assert rnd_resize_y >= 0

        rnd_resize_x = eval_arg(rnd_resize_x, None)
        rnd_resize_y = eval_arg(rnd_resize_y, None)

        super(RandomResize, self).__init__(iaa.Resize(
            {'width': (1.0, 1.0 + rnd_resize_x), 'height': (1.0, 1.0 + rnd_resize_y)},
            interpolation=interpolation
        ), ATTRS)


class RandomCrop(ImgaugAdapter):
    def __init__(
            self,
            height: int = 224,
            width: int = 224,
            cval: int = 127,
            mode: str = "constant"
    ) -> None:
        """RandomCrop, 随机裁剪, 尺寸变换

        Args:
            height: Resize height, 裁剪高度, [0, 5000, 1], 224
            width: Resize width, 裁剪宽度, [0, 5000, 1], 224
            cval: Color value, 填充颜色, [0, 255, 1], 127
            mode: Fill mode, 填充模式, {"constant", "edge", "reflect", "symmetric"}, "constant"
        """
        aug_list = [
            iaa.PadToFixedSize(
                width=width,
                height=height,
                pad_cval=cval,
                position='center',
                pad_mode=mode,
            ),
            iaa.CropToFixedSize(width=width, height=height, position='uniform')]

        super(RandomCrop, self).__init__(iaa.Sequential(aug_list), ATTRS)


class RandomResizedCrop(AbstractTransform):
    def __init__(
            self,
            height: int = 224,
            width: int = 224,
            scale_min: float = 0.08,
            scale_max: float = 1.0,
            ratio_min: float = 0.75,
            ratio_max: float = 1.33,
            interpolation: str = 'linear',
    ) -> None:
        """RandomResizedCrop, 随机裁剪缩放, 尺寸变换
        Args:
            height: Resize height, 裁剪高度, [0, 5000, 1], 224
            width: Resize width, 裁剪宽度, [0, 5000, 1], 224
            scale_min: Crop area scale minimum, 裁剪区域比例最小值, [0.08, 1.0, 0.01], 0.08
            scale_max: Crop area scale maximum, 裁剪区域比例最大值, [0.08, 1.0, 0.01], 1.0
            ratio_min: Crop ratio minimum, 裁剪纵横比最小值, [0.75, 1.33, 0.01], 0.75
            ratio_max: Crop ratio maximum, 裁剪纵横比最大值, [0.75, 1.33, 0.01], 1.33
            interpolation: Interpolation, 插值模式, {"nearest", "cubic", "linear"}, "linear"
        """
        super().__init__(use_gpu=False)

        height = eval_arg(height, None)
        width = eval_arg(width, None)
        scale_min = eval_arg(scale_min, None)
        scale_max = eval_arg(scale_max, None)
        ratio_min = eval_arg(ratio_min, None)
        ratio_max = eval_arg(ratio_max, None)

        self.size = [height, width]
        self.scale = [scale_min, scale_max]
        self.ratio = [ratio_min, ratio_max]
        self.interpolation = interpolation

    def _get_param(self, img_size):
        imh, imw = img_size[:2]
        area = imh * imw

        log_ratio = np.log(np.array(self.ratio))
        for _ in range(10):
            target_area = area * random.uniform(self.scale[0], self.scale[1])
            aspect_ratio = np.exp(random.uniform(log_ratio[0], log_ratio[1]))

            w = int(round(math.sqrt(target_area * aspect_ratio)))
            h = int(round(math.sqrt(target_area / aspect_ratio)))

            if 0 < w <= imw and 0 < h <= imh:
                i = random.randint(0, imh - h + 1)
                j = random.randint(0, imw - w + 1)
                return i, j, h, w

        # Fallback to central crop
        in_ratio = float(imw) / float(imh)
        if in_ratio < min(self.ratio):
            w = imw
            h = int(round(w / min(self.ratio)))
        elif in_ratio > max(self.ratio):
            h = imh
            w = int(round(h * max(self.ratio)))
        else:  # whole image
            w = imw
            h = imh
        i = (imh - h) // 2
        j = (imw - w) // 2
        return i, j, h, w

    def _apply(self, sample):

        if sample.image is None:
            return sample

        imh, imw = sample.shape[:2]

        top, left, h, w = self._get_param(sample.shape)
        bottom, right = max(imh - top - h, 0), max(imw - left - w, 0)

        aug = iaa.Sequential([
            iaa.Crop(px=(top, right, bottom, left), keep_size=False),
            iaa.Resize(size=self.size, interpolation=self.interpolation)
        ])

        return apply_augmenter(sample, aug, ATTRS)
