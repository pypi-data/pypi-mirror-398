#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-06-15
"""
from imgaug import augmenters as iaa
import numpy as np

from ..common import AbstractSample, eval_arg, ImgaugAdapter
from ..common import DEFAULT_IMAGE_FIELD, DEFAULT_MASK_FIELD, DEFAULT_BBOX_FIELD, \
    DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD

__all__ = [
    'HorizontalFlip',
    'VerticalFlip',
    'RandomHorizontalFlip',
    'RandomVerticalFlip',
]

ATTRS = [DEFAULT_IMAGE_FIELD, DEFAULT_MASK_FIELD, DEFAULT_BBOX_FIELD,
         DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD]


class HorizontalFlip(ImgaugAdapter):

    def __init__(self) -> None:
        """HorizontalFlip, 水平翻转, 翻转变换
        """
        super().__init__(iaa.Fliplr(p=1.0), ATTRS)
            
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        w = input_shape[1]
        self.matrix = np.array([
            [-1, 0, w],
            [0, 1, 0],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class VerticalFlip(ImgaugAdapter):

    def __init__(self) -> None:
        """VerticalFlip, 垂直翻转, 翻转变换
        """
        super().__init__(iaa.Flipud(p=1.0), ATTRS)
     
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        h = input_shape[0]
        self.matrix = np.array([
            [1, 0, 0],
            [0, -1, h],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class RandomHorizontalFlip(ImgaugAdapter):

    def __init__(self, p: float = 0.5) -> None:
        """RandomHorizontalFlip, 随机水平翻转, 翻转变换

        Args:
            p: Probability, 翻转概率, [0.0, 1.0, 0.1], 0.5
        """
        p = eval_arg(p, None)
        super().__init__(iaa.Fliplr(p=p), ATTRS)


class RandomVerticalFlip(ImgaugAdapter):

    def __init__(self, p: float = 1.0) -> None:
        """RandomVerticalFlip, 随机垂直翻转, 翻转变换

        Args:
            p: Probability, 翻转概率, [0.0, 1.0, 0.1], 0.5
        """
        p = eval_arg(p, None)
        super().__init__(iaa.Flipud(p=p), ATTRS)
