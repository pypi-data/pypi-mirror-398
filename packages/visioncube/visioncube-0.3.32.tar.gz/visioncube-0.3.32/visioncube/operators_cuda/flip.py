#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-05-26
"""
import numpy as np
import torch
import torchvision.transforms.functional as TF

from ..common import AbstractSample, AbstractTransform, eval_arg

__all__ = [
    'HorizontalFlip',
    'VerticalFlip',
    'RandomHorizontalFlip',
    'RandomVerticalFlip',
]


class HorizontalFlip(AbstractTransform):

    def __init__(self) -> None:
        """HorizontalFlip, 水平翻转, 翻转变换
        """
        super().__init__(use_gpu=True)

    @staticmethod
    def _augment_image(image):
        return TF.hflip(image)

    @staticmethod
    def _augment_bboxes(bboxes, imw):
        bboxes[:, [0, 2]] = imw - bboxes[:, [2, 0]]
        return bboxes

    @staticmethod
    def _augment_keypoints(keypoints, imw):
        keypoints[:, 0] = imw - keypoints[:, 0]
        return keypoints

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self._augment_image(sample.image)

        if sample.bboxes is not None:
            imw = sample.shape[-1]
            sample.bboxes = self._augment_bboxes(sample.bboxes, imw)

        if sample.mask is not None:
            sample.mask = self._augment_image(sample.mask)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap)

        if sample.keypoints is not None:
            imw = sample.shape[-1]
            sample.keypoints = self._augment_keypoints(sample.keypoints, imw)

        return sample
        
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        w = input_shape[-1]
        self.matrix = np.array([
            [-1, 0, w],
            [0, 1, 0],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class VerticalFlip(AbstractTransform):

    def __init__(self) -> None:
        """VerticalFlip, 垂直翻转, 翻转变换
        """
        super().__init__(use_gpu=True)

    @staticmethod
    def _augment_image(image):
        return TF.vflip(image)

    @staticmethod
    def _augment_bboxes(bboxes, imh):
        bboxes[:, [1, 3]] = imh - bboxes[:, [3, 1]]
        return bboxes

    @staticmethod
    def _augment_keypoints(keypoints, imh):
        keypoints[:, 1] = imh - keypoints[:, 1]
        return keypoints

    def _apply(self, sample):
        if sample.image is None:
            return sample

        sample.image = self._augment_image(sample.image)

        if sample.bboxes is not None:
            imh = sample.shape[-2]
            sample.bboxes = self._augment_bboxes(sample.bboxes, imh)

        if sample.mask is not None:
            sample.mask = self._augment_image(sample.mask)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap)

        if sample.keypoints is not None:
            imh = sample.shape[-2]
            sample.keypoints = self._augment_keypoints(sample.keypoints, imh)

        return sample
         
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        h = input_shape[-2]
        self.matrix = np.array([
            [1, 0, 0],
            [0, -1, h],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class RandomHorizontalFlip(HorizontalFlip):

    def __init__(self, p: float = 0.5) -> None:
        """RandomHorizontalFlip, 随机水平翻转, 翻转变换

        Args:
            p: Probability, 翻转概率, [0.0, 1.0, 0.1], 0.5
        """
        super().__init__()
        self.p = eval_arg(p, None)

    def _apply(self, sample):
        if torch.rand(1) < self.p:
            sample = super()._apply(sample)

        return sample


class RandomVerticalFlip(VerticalFlip):

    def __init__(self, p: float = 0.5) -> None:
        """RandomVerticalFlip, 随机垂直翻转, 翻转变换

        Args:
            p: Probability, 翻转概率, [0.0, 1.0, 0.1], 0.5
        """
        self.p = eval_arg(p, None)
        super().__init__()

    def _apply(self, sample):
        if torch.rand(1) < self.p:
            sample = super()._apply(sample)

        return sample
