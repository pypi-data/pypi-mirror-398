#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-05-31
"""
import math
import random
from typing import Tuple, Union, Sequence, Any

import numpy as np
import torch
from torch import Tensor
from torchvision.transforms import InterpolationMode, functional as TF

from ..common import AbstractSample, AbstractTransform, eval_arg

__all__ = [
    'Resize',
    'CenterCrop',
    'Crop',
    'Pad',
    'RandomResize',
    'RandomCrop',
    'RandomResizedCrop',
]


class Resize(AbstractTransform):

    def __init__(
            self,
            height: Union[int, Sequence] = 224,
            width: Union[int, Sequence] = 224,
            interpolation: str = "bilinear"
    ) -> None:
        """Resize, 缩放变换, 尺寸变换

        Args:
            height: Height, 缩放高度, [0, 1000, 1], 224
            width: Width, 缩放宽度, [0, 1000, 1], 224
            interpolation: Interpolation, 插值模式, {"nearest", "bicubic", "bilinear"}, "bilinear"
        """
        super().__init__(use_gpu=True)

        self.to_h = eval_arg(height, None)
        self.to_w = eval_arg(width, None)
        self.interpolation = InterpolationMode[interpolation.upper()]

    def _get_params(self, img_size):

        _, imh, imw = img_size
        h, w = self.to_h, self.to_w
        if isinstance(self.to_h, Sequence):
            h = random.uniform(self.to_h[0], self.to_h[1]) * imh

        if isinstance(self.to_w, Sequence):
            w = random.uniform(self.to_w[0], self.to_w[1]) * imw

        return int(h), int(w)

    def _augment_image(self, image, to_size):
        return TF.resize(image, to_size, self.interpolation)

    @staticmethod
    def _augment_bboxes(bboxes, img_size, to_size):
        to_h, to_w = to_size
        _, imh, imw = img_size
        scale_h, scale_w = to_h / imh, to_w / imw

        bboxes[:, [0, 2]] *= scale_w
        bboxes[:, [1, 3]] *= scale_h

        return bboxes

    @staticmethod
    def _augment_keypoints(keypoints, img_size, to_size):
        to_h, to_w = to_size
        _, imh, imw = img_size
        scale_h, scale_w = to_h / imh, to_w / imw

        keypoints[:, 0] *= scale_w
        keypoints[:, 1] *= scale_h

        return keypoints

    def _apply(self, sample):

        if sample.image is None or not self.to_h or not self.to_w:
            return sample

        img_size = sample.shape
        to_size = self._get_params(sample.shape)
        sample.image = self._augment_image(sample.image, to_size)

        if sample.bboxes is not None:
            sample.bboxes = self._augment_bboxes(sample.bboxes, img_size, to_size)

        if sample.mask is not None:
            sample.mask = self._augment_image(sample.mask, to_size)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap, to_size)

        if sample.keypoints is not None:
            sample.keypoints = self._augment_keypoints(sample.keypoints, img_size, to_size)

        return sample
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        _, h, w = input_shape
        scale_x = self.to_w / w
        scale_y = self.to_h / h
        self.matrix = np.array([
            [scale_x, 0, 0],
            [0, scale_y, 0],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class CenterCrop(AbstractTransform):

    def __init__(self, height: int = 224, width: int = 224) -> None:
        """CenterCrop, 中心裁剪, 尺寸变换

        Args:
            height: Height, 裁剪高度, [0, 65536, 1], 224
            width: Width, 裁剪宽度, [0, 65536, 1], 224
        """
        super().__init__(use_gpu=True)

        self.to_h = eval_arg(height, None)
        self.to_w = eval_arg(width, None)

    def _augment_image(self, image):
        return TF.center_crop(image, [self.to_h, self.to_w])

    def _augment_bboxes(self, bboxes, img_size):
        _, imh, imw = img_size

        offset_x = imw / 2 - self.to_w / 2
        offset_y = imh / 2 - self.to_h / 2

        bboxes[:, 0].sub_(offset_x).clamp_(min=0, max=self.to_w - 1)
        bboxes[:, 1].sub_(offset_y).clamp_(min=0, max=self.to_h - 1)
        bboxes[:, 2].sub_(offset_x).clamp_(min=0, max=self.to_w - 1)
        bboxes[:, 3].sub_(offset_y).clamp_(min=0, max=self.to_h - 1)

        return bboxes

    def _augment_keypoints(self, keypoints, img_size):

        _, imh, imw = img_size

        offset_x = imw / 2 - self.to_w / 2
        offset_y = imh / 2 - self.to_h / 2

        keypoints[:, 0].sub_(offset_x).clamp_(min=0, max=self.to_w - 1)
        keypoints[:, 1].sub_(offset_y).clamp_(min=0, max=self.to_h - 1)

        return keypoints

    def _apply(self, sample):

        if sample.image is None or not self.to_h or not self.to_w:
            return sample

        img_size = sample.shape
        sample.image = self._augment_image(sample.image)

        if sample.bboxes is not None:
            sample.bboxes = self._augment_bboxes(sample.bboxes, img_size)

        if sample.mask is not None:
            sample.mask = self._augment_image(sample.mask)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap)

        if sample.keypoints is not None:
            sample.keypoints = self._augment_keypoints(sample.keypoints, img_size)

        return sample
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        _, h, w = input_shape
        x = (w - self.to_w) // 2
        y = (h - self.to_h) // 2
        self.matrix = np.array([
            [1, 0, -x],
            [0, 1, -y],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)

class Crop(AbstractTransform):

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
        super().__init__(use_gpu=True)

        self.top = eval_arg(top, None)
        self.right = eval_arg(right, None)
        self.bottom = eval_arg(bottom, None)
        self.left = eval_arg(left, None)

    def _compute_height_width(self, img_size):
        _, imh, imw = img_size

        to_h = imh - self.top - self.bottom
        to_w = imw - self.right - self.left

        return to_h, to_w

    def _augment_image(self, image, to_h, to_w):

        return TF.crop(
            image,
            top=self.top,
            left=self.left,
            height=to_h,
            width=to_w)

    def _augment_bboxes(self, bboxes, to_h, to_w):

        bboxes[:, 0].sub_(self.left).clamp_(min=0)
        bboxes[:, 1].sub_(self.top).clamp_(min=0)
        bboxes[:, 2].sub_(self.left).clamp_(min=0, max=to_w - 1)
        bboxes[:, 3].sub_(self.top).clamp_(min=0, max=to_h - 1)

        areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
        # ymax > ymin and xmax > xmin and area > 0
        mask = (bboxes[:, 2] > bboxes[:, 0]) & \
               (bboxes[:, 3] > bboxes[:, 1]) & \
               (areas > 0)

        return bboxes[mask]

    def _augment_keypoints(self, keypoints, to_h, to_w):

        keypoints[:, 0].sub_(self.left)
        keypoints[:, 1].sub_(self.top)

        mask = (keypoints[:, 0] >= 0) & (keypoints[:, 0] <= to_w) & \
               (keypoints[:, 1] >= 0) & (keypoints[:, 1] <= to_h)
        keypoints = keypoints[mask]

        return keypoints

    def _check_params(self, img_size):
        _, imh, imw = img_size

        if self.top >= imh:
            return False

        if self.right >= imw:
            return False

        if self.bottom >= imh:
            return False

        if self.left >= imw:
            return False

        return True

    def _apply(self, sample):

        if sample.image is None:
            return sample

        if not self._check_params(sample.shape):
            return sample

        to_h, to_w = self._compute_height_width(sample.shape)
        sample.image = self._augment_image(sample.image, to_h, to_w)

        if sample.bboxes is not None:
            sample.bboxes = self._augment_bboxes(sample.bboxes, to_h, to_w)

        if sample.mask is not None:
            sample.mask = self._augment_image(sample.mask, to_h, to_w)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap, to_h, to_w)

        if sample.keypoints is not None:
            sample.keypoints = self._augment_keypoints(sample.keypoints, to_h, to_w)

        return sample
        
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        x = self.left
        y = self.top
        self.matrix = np.array([
            [1, 0, -x],
            [0, 1, -y],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class Pad(AbstractTransform):

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
        super().__init__(use_gpu=True)

        self.px = eval_arg(px, None)
        self.pct = eval_arg(pct, None)
        self.cval = eval_arg(cval, None)
        self.mode = mode

    def _get_params(self, img_size):
        if self.px:
            if isinstance(self.px, Sequence):
                return [int(i) for i in self.px]
            else:
                return int(self.px)

        if self.pct:
            _, h, w = img_size
            if isinstance(self.pct, Sequence):
                return int(self.pct[0] * w), int(self.pct[1] * h)
            else:
                return int(self.pct * w), int(self.pct * h)

        _, h, w = img_size
        pct = random.uniform(0.0, 0.1)
        return int(pct * w), int(pct * h)
        # raise ValueError(f"Invalid px value {self.px} and pct value {self.pct}")

    def _augment_image(self, image, padding, cval=0):
        return TF.pad(image, padding, cval, self.mode)

    @staticmethod
    def _augment_bboxes(bboxes, padding):
        if isinstance(padding, (tuple, list)):
            bboxes[:, [0, 2]] += padding[0]
            bboxes[:, [1, 3]] += padding[1]
        else:
            bboxes.add_(padding)

        return bboxes

    @staticmethod
    def _augment_keypoints(keypoints, padding):
        if isinstance(padding, (tuple, list)):
            keypoints[:, 0] += padding[0]
            keypoints[:, 1] += padding[1]
        else:
            keypoints.add_(padding)

        return keypoints

    def _apply(self, sample):

        if sample.image is None:
            return sample

        padding = self._get_params(sample.shape)
        if padding is None:
            return sample

        sample.image = self._augment_image(sample.image, padding, self.cval)

        if sample.bboxes is not None:
            sample.bboxes = self._augment_bboxes(sample.bboxes, padding)

        if sample.mask is not None:
            sample.mask = self._augment_image(sample.mask, padding)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap, padding, self.cval)

        if sample.keypoints is not None:
            sample.keypoints = self._augment_keypoints(sample.keypoints, padding)

        return sample
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        left = (output_sample.shape[2] - input_shape[2]) / 2
        top = (output_sample.shape[1] - input_shape[1]) / 2
        self.matrix = np.array([
            [1, 0, left],
            [0, 1, top],
            [0, 0, 1]
        ])
        super()._update_transform(input_shape, output_sample)


class RandomResize(Resize):

    def __init__(
            self,
            rnd_resize_x: float = 0.0,
            rnd_resize_y: float = 0.0,
            interpolation: str = "bilinear"
    ) -> None:
        """RandomResize, 随机缩放变换, 尺寸变换

        Args:
            rnd_resize_x: Random resize x-axis ratio, x轴随机缩放比例, [0.0, 10.0, 0.1], 0.0
            rnd_resize_y: Random resize y-axis ratio, y轴随机缩放比例, [0.0, 10.0, 0.1], 0.0
            interpolation: Interpolation, 插值模式, {"nearest", "bicubic", "bilinear"}, "bilinear"
        """

        rnd_resize_x = eval_arg(rnd_resize_x, None)
        rnd_resize_y = eval_arg(rnd_resize_y, None)

        assert rnd_resize_x >= 0
        assert rnd_resize_y >= 0

        super().__init__(
            height=(1.0, 1.0 + rnd_resize_y),
            width=(1.0, 1.0 + rnd_resize_x),
            interpolation=interpolation,
        )


class RandomCrop(AbstractTransform):

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
        super().__init__(use_gpu=True)

        self.to_h = eval_arg(height, None)
        self.to_w = eval_arg(width, None)
        self.cval = eval_arg(cval, None)
        self.mode = mode

    def _get_params(self, imh: int, imw: int) -> Tuple[int, int]:

        if imw == self.to_w and imh == self.to_h:
            top, left = 0, 0
        else:
            top = torch.randint(0, imh - self.to_h + 1, size=(1,)).item()
            left = torch.randint(0, imw - self.to_w + 1, size=(1,)).item()

        return top, left

    def _apply(self, sample):

        if sample.image is None or not self.to_h or not self.to_w:
            return sample

        _, imh, imw = sample.shape

        padding = [0, 0]
        if imw < self.to_w:
            padding[0] = self.to_w - imw
        # pad the  if needed
        if imh < self.to_h:
            padding[1] = self.to_h - imh

        if max(padding) > 0:
            sample = Pad(px=padding, cval=self.cval, mode=self.mode)(sample)

        _, imh, imw = sample.shape
        top, left = self._get_params(imh, imw)
        right = imw - left - self.to_w
        bottom = imh - top - self.to_h
        sample = Crop(top=top, right=right, bottom=bottom, left=left)(sample)

        return sample


class RandomResizedCrop(AbstractTransform):
    def __init__(
            self,
            height: int = 224,
            width: int = 224,
            scale_min: float = 0.08,
            scale_max: float = 1.0,
            ratio_min: float = 0.75,
            ratio_max: float = 1.33,
            interpolation: str = 'bilinear'
    ) -> None:
        """RandomResizedCrop, 随机裁剪缩放, 尺寸变换
        Args:
            height: Resize height, 裁剪高度, [0, 5000, 1], 224
            width: Resize width, 裁剪宽度, [0, 5000, 1], 224
            scale_min: Crop area scale minimum, 裁剪区域比例最小值, [0.08, 1.0, 0.01], 0.08
            scale_max: Crop area scale maximum, 裁剪区域比例最大值, [0.08, 1.0, 0.01], 1.0
            ratio_min: Crop ratio minimum, 裁剪纵横比最小值, [0.75, 1.33, 0.01], 0.75
            ratio_max: Crop ratio maximum, 裁剪纵横比最大值, [0.75, 1.33, 0.01], 1.33
            interpolation: Interpolation, 插值模式, {"nearest", "bicubic", "bilinear"}, "bilinear"
        """
        super().__init__(use_gpu=True)

        height = eval_arg(height, None)
        width = eval_arg(width, None)
        scale_min = eval_arg(scale_min, None)
        scale_max = eval_arg(scale_max, None)
        ratio_min = eval_arg(ratio_min, None)
        ratio_max = eval_arg(ratio_max, None)

        if not height or not width:
            self.size = None
        else:
            self.size = [height, width]
        self.scale = [scale_min, scale_max]
        self.ratio = [ratio_min, ratio_max]
        self.interpolation = interpolation

    def _get_params(self, image: Tensor) -> Tuple[int, int, int, int]:
        _, imh, imw = image.size()
        area = imh * imw

        log_ratio = torch.log(torch.tensor(self.ratio))
        for _ in range(10):
            target_area = area * torch.empty(1).uniform_(self.scale[0], self.scale[1]).item()
            aspect_ratio = torch.exp(torch.empty(1).uniform_(log_ratio[0], log_ratio[1])).item()

            w = int(round(math.sqrt(target_area * aspect_ratio)))
            h = int(round(math.sqrt(target_area / aspect_ratio)))

            if 0 < w <= imw and 0 < h <= imh:
                i = torch.randint(0, imh - h + 1, size=(1,)).item()
                j = torch.randint(0, imw - w + 1, size=(1,)).item()
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

        if sample.image is None or not self.size:
            return sample

        params = self._get_params(sample.image)
        _, imh, imw = sample.shape

        top, left, to_h, to_w = params
        bottom = imh - top - to_h
        right = imw - left - to_w

        sample = Crop(top, right, bottom, left)(sample)
        sample = Resize(self.size[0], self.size[1], self.interpolation)(sample)

        return sample
