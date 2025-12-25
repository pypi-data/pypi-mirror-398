#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-05-31
"""

import math
import random
from dataclasses import dataclass
from typing import List, Sequence, Union, Tuple

import cv2
import numpy as np
import torch
from torchvision.transforms import InterpolationMode, functional as TF

from .bbs import to_keypoints_on_image, invert_to_keypoints_on_image_
from ..common import AbstractSample, AbstractTransform, eval_arg

__all__ = [
    'Rotate',
    'Affine',
    'RandomRotate',
    'RandomPerspective',
    'RandomAffine',
]


@dataclass
class AffineParams:
    degree: float = 0.0
    translate_x: int = 0
    translate_y: int = 0
    scale: float = 1.0
    shear_x: float = 0.0
    shear_y: float = 0.0
    cval: int = 0
    interp: InterpolationMode = InterpolationMode.NEAREST
    img_size: Tuple[int] = None


@dataclass
class RotateParams:
    degree: float = 0.0
    cval: int = 0
    interp: InterpolationMode = InterpolationMode.NEAREST
    img_size: Tuple[int] = None
    expand: bool = True


class Affine(AbstractTransform):

    def __init__(
            self,
            degree: Union[float, Sequence] = 0.0,
            translate_x: int = 0,
            translate_y: int = 0,
            scale: float = 1.0,
            shear_x: float = 0.0,
            shear_y: float = 0.0,
            cval: int = 0,
            interpolation: str = "nearest",
    ) -> None:
        """Affine, 仿射变换, 几何变换

        Args:
            degree: Rotate angle, 旋转角度, [-180.0, 180.0, 0.1], 0.0
            translate_x: Horizontal translations, 水平平移像素, [0, 1000, 1], 0
            translate_y: Vertical translations, 垂直平移像素, [0, 1000, 1], 0
            scale: Overall scale, 缩放比例, [0.1, 1000.0, 0.1], 1.0
            shear_x: Horizontal shear value, 水平错切, [-180.0, 180.0, 0.1], 0.0
            shear_y: Vertical shear value, 垂直错切, [-180.0, 180.0, 0.1], 0.0
            cval: Color value, 填充颜色, [0, 255, 1], 0
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear"}, "nearest"
        """
        super().__init__(use_gpu=True)

        self.degree = eval_arg(degree, None)
        self.translate_x = eval_arg(translate_x, None)
        self.translate_y = eval_arg(translate_y, None)
        self.scale = eval_arg(scale, None)
        self.shear_x = eval_arg(shear_x, None)
        self.shear_y = eval_arg(shear_y, None)
        self.cval = eval_arg(cval, None)
        self.interp = InterpolationMode[interpolation.upper()]

    def _get_params(self, img_size):

        def random_element(item, type_=float):
            if isinstance(item, Sequence):
                value = random.uniform(item[0], item[1])
                return type_(value)

            return item

        translate_x = random_element(self.translate_x)
        if 0 < translate_x < 1:  # 如果在[0, 1]之间，就认为是百分比
            translate_x *= img_size[-1]
        translate_y = random_element(self.translate_y)
        if 0 < translate_y < 1:
            translate_y *= img_size[-2]

        return AffineParams(
            degree=random_element(self.degree),
            translate_x=translate_x,
            translate_y=translate_y,
            scale=random_element(self.scale),
            shear_x=random_element(self.shear_x),
            shear_y=random_element(self.shear_y),
            cval=self.cval,
            interp=self.interp,
            img_size=img_size,
        )

    @staticmethod
    def _augment_image(image, params):

        return TF.affine(
            image,
            angle=params.degree,
            translate=[params.translate_x, params.translate_y],
            scale=params.scale,
            shear=[params.shear_x, params.shear_y],
            interpolation=params.interp,
            fill=params.cval)

    @staticmethod
    def _get_affine_matrix(
            scale=None,
            rotation=None,
            shear=None,
            translation=None
    ):

        if scale is None:
            scale = 1
        if rotation is None:
            rotation = 0
        if shear is None:
            shear = 0
        if translation is None:
            translation = (0, 0)

        matrix = torch.tensor([
            [scale * math.cos(rotation), -scale * math.sin(rotation + shear), 0],
            [scale * math.sin(rotation), scale * math.cos(rotation + shear), 0],
            [0, 0, 1],
        ])
        matrix[0:2, 2] = torch.tensor(translation)

        return matrix

    @staticmethod
    def _get_transform_matrix(params, device='cpu'):

        translate_matrix = torch.tensor([
            [1.0, 0, params.translate_x],
            [0, 1, params.translate_y],
            [0, 0, 1]
        ], device=device)

        _, imh, imw = params.img_size
        cx, cy = imw * 0.5, imh * 0.5
        center_matrix = torch.tensor([
            [1, 0, cx],
            [0, 1, cy],
            [0, 0, 1]
        ], device=device)

        rot = math.radians(params.degree)
        sx = math.radians(params.shear_x)
        sy = math.radians(params.shear_y)

        rotate_scale_shear_matrix = torch.tensor([
            [math.cos(rot - sy) / math.cos(sy),
             -math.cos(rot - sy) * math.tan(sx) / math.cos(sy) - math.sin(rot), 0],
            [math.sin(rot - sy) / math.cos(sy),
             -math.sin(rot - sy) * math.tan(sx) / math.cos(sy) + math.cos(rot), 0],
            [0, 0, 1],
        ], device=device)
        rotate_scale_shear_matrix[:2, :2] *= params.scale

        matrix = (translate_matrix
                  @ center_matrix
                  @ rotate_scale_shear_matrix
                  @ torch.inverse(center_matrix)
                  )

        return matrix

    def _augment_bboxes(self, bboxes, params):

        boxes, labels = torch.split(bboxes, [4, 1], dim=1)
        device = boxes.device

        keypoints = to_keypoints_on_image(bboxes)
        keypoints = torch.cat([keypoints, torch.ones(keypoints.size(0), 1, device=device)], dim=1)

        transform_matrix = self._get_transform_matrix(params, device)
        dst = keypoints @ transform_matrix.t()

        ndim = 2
        dst[dst[:, ndim] == 0, ndim] = torch.finfo(torch.float).eps
        # rescale to homogeneous coordinates
        dst[:, :ndim] /= dst[:, ndim:ndim + 1]
        dst = dst[:, :ndim]

        dst = invert_to_keypoints_on_image_(dst, len(bboxes))
        output = torch.cat([dst, labels], dim=1)

        output[:, [0, 2]] = torch.clamp(output[:, [0, 2]], min=0, max=params.img_size[-1])
        output[:, [1, 3]] = torch.clamp(output[:, [1, 3]], min=0, max=params.img_size[-2])

        return output

    def _augment_keypoints(self, keypoints, params):

        device = keypoints.device
        keypoints = torch.cat([keypoints, torch.ones(keypoints.size(0), 1, device=device)], dim=1)
        transform_matrix = self._get_transform_matrix(params, device)
        dst = keypoints @ transform_matrix.t()

        ndim = 2
        dst[dst[:, ndim] == 0, ndim] = torch.finfo(torch.float).eps
        # rescale to homogeneous coordinates
        dst[:, :ndim] /= dst[:, ndim:ndim + 1]
        dst = dst[:, :ndim]

        _, imh, imw = params.img_size
        mask = (dst[:, 0] >= 0) & (dst[:, 0] <= imw) & \
               (dst[:, 1] >= 0) & (dst[:, 1] <= imh)
        dst = dst[mask]
        return dst

    def _apply(self, sample):
        if sample.image is None:
            return sample

        params = self._get_params(sample.shape)
        sample.image = self._augment_image(sample.image, params)

        if sample.bboxes is not None:
            sample.bboxes = self._augment_bboxes(sample.bboxes, params)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_image(sample.heatmap, params)

        if sample.mask is not None:
            params.cval = 0
            sample.mask = self._augment_image(sample.mask, params)

        if sample.keypoints is not None:
            sample.keypoints = self._augment_keypoints(sample.keypoints, params)

        return sample
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        params = self._get_params(input_shape)
        self.matrix = self._get_transform_matrix(params).numpy()
        super()._update_transform(input_shape, output_sample)

'''
class Rotate(Affine):

    def __init__(
            self,
            degree: float = 20.0,
            cval: int = 127,
            interpolation: str = 'nearest'
    ) -> None:
        """Rotate, 旋转变换, 几何变换

        Args:
            degree: Rotate angle, 旋转角度, [-360.0, 360.0, 0.1], 20.0
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            interpolation: Interpolation, 插值模式, {'nearest', 'bilinear'}, 'nearest'
        """
        super().__init__(
            degree=degree,
            cval=cval,
            interpolation=interpolation,
        )'''


# TODO: only for sample.image
class Rotate(AbstractTransform):

    def __init__(
            self,
            degree: float = 20.0,
            cval: int = 127,
            interpolation: str = 'nearest',
            expand: bool = False,
    ) -> None:
        """Rotate, 旋转变换, 几何变换

        Args:
            degree: Rotate angle, 旋转角度, [-360.0, 360.0, 0.1], 20.0
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            interpolation: Interpolation, 插值模式, {'nearest', 'bilinear'}, 'nearest'
            expand: Expand, 是否扩展图像尺寸（以保证所有像素完全保留）, {'True', 'False'}, 'False'
        """
        super().__init__(use_gpu=True)
        self.degree = eval_arg(degree, None)
        self.cval = eval_arg(cval, None)
        self.interp = InterpolationMode[interpolation.upper()]
        self.expand = eval_arg(expand, None)

    def _get_params(self, img_size):

        def random_element(item, type_=float):
            if isinstance(item, Sequence):
                print(item)
                value = random.uniform(item[0], item[1])
                return type_(value)

            return item

        return RotateParams(
            degree=random_element(self.degree),
            cval=self.cval,
            interp=self.interp,
            img_size=img_size,
            expand=self.expand
        )

    @staticmethod
    def _augment_image(image, params):
        
        return TF.rotate(
            image,
            angle=params.degree,
            interpolation=params.interp,
            expand=params.expand,
            fill=params.cval)
    
    def _apply(self, sample):
        if sample.image is None:
            return sample

        params = self._get_params(sample.shape)
        sample.image = self._augment_image(sample.image, params)
        return sample
        
    # def _calculate_rotation_matrix(self, image_size: Tuple[int, int]):
    #     """
    #     计算旋转变换矩阵
        
    #     Args:
    #         angle_deg: 旋转角度(度)
    #         image_size: 原始图像尺寸 (height, width)
            
    #     Returns:
    #         3x3 齐次变换矩阵
    #     """
    #     h, w = image_size
        
    #     # 计算原始中心点
    #     cx_orig = w / 2.0
    #     cy_orig = h / 2.0

    #     # 构建旋转矩阵
    #     rotation_matrix = cv2.getRotationMatrix2D((cx_orig, cy_orig), self.degree, 1.0)
        
    #     # 转换为齐次矩阵
    #     homogeneous_matrix = np.vstack([rotation_matrix, [0, 0, 1]])
        
    #     return homogeneous_matrix

    def _calculate_rotation_matrix(self, image_size: Tuple[int, int]):
        """
        计算旋转变换矩阵
        Args:
            image_size: 原始图像尺寸 (height, width)
        
        Returns:
            3x3的齐次变换矩阵
        """
        # due to current incoherence of rotation angle direction between affine and rotate implementations
        # we need to set -angle.
        angle_rad = math.radians(-self.degree)  #注意为负
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        height, width = image_size
        
        # 原图像中心点
        cx1, cy1 = width / 2, height / 2
        
        # 计算旋转后的新尺寸
        new_width = int(width * abs(cos_a) + height * abs(sin_a))
        new_height = int(width * abs(sin_a) + height * abs(cos_a))
        
        # 新图像中心点
        cx2, cy2 = new_width / 2, new_height / 2
        
        # 齐次变换矩阵：先平移到原中心 -> 旋转 -> 平移到新中心
        # T(cx2, cy2) * R * T(-cx1, -cy1)
        matrix = torch.tensor([
            [cos_a, -sin_a, cx2 - cos_a * cx1 + sin_a * cy1],
            [sin_a,  cos_a, cy2 - sin_a * cx1 - cos_a * cy1],
            [0,      0,     1]
        ], dtype=torch.float32)

        return matrix
        
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        image_size = input_shape[-2:]
        self.matrix = self._calculate_rotation_matrix(image_size).numpy()
        super()._update_transform(input_shape, output_sample)


class RandomPerspective(AbstractTransform):

    def __init__(
            self,
            scale_min: float = 0.0,
            scale_max: float = 1.0,
            p: float = 0.5,
            cval: int = 127,
            interpolation: str = 'bilinear'
    ) -> None:
        """RandomRotate, 随机透视变换, 几何变换

        Args:
            scale_min: Minimum distortion degree, 最小失真程度, [0.0, 1.0, 0.1], 0.0
            scale_max: Maximum distortion degree, 最大失真程度, [0.0, 1.0, 0.1], 1.0
            p: Probability, 变换概率, [0, 1.0, 0.1], 0.5
            cval: Color value, 填充颜色, [0, 255, 1], 127
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear"}, "nearest"
        """
        super().__init__(use_gpu=True)

        scale_min = eval_arg(scale_min, None)
        scale_max = eval_arg(scale_max, None)
        self.p = eval_arg(p, None)
        self.cval = eval_arg(cval, None)
        self.interpolation = InterpolationMode[interpolation.upper()]
        self.scale = random.uniform(scale_min, scale_max)

    def _get_params(self, img_size):
        _, imh, imw = img_size
        half_height, half_width = imh // 2, imw // 2
        top_left = [
            int(torch.randint(0, int(self.scale * half_width) + 1, size=(1,)).item()),
            int(torch.randint(0, int(self.scale * half_height) + 1, size=(1,)).item()),
        ]
        top_right = [
            int(torch.randint(imw - int(self.scale * half_width) - 1, imw, size=(1,)).item()),
            int(torch.randint(0, int(self.scale * half_height) + 1, size=(1,)).item()),
        ]
        bot_right = [
            int(torch.randint(imw - int(self.scale * half_width) - 1, imw, size=(1,)).item()),
            int(torch.randint(imh - int(self.scale * half_height) - 1, imh, size=(1,)).item()),
        ]
        bot_left = [
            int(torch.randint(0, int(self.scale * half_width) + 1, size=(1,)).item()),
            int(torch.randint(imh - int(self.scale * half_height) - 1, imh, size=(1,)).item()),
        ]
        start_points = [[0, 0], [imw - 1, 0], [imw - 1, imh - 1], [0, imh - 1]]
        end_points = [top_left, top_right, bot_right, bot_left]

        return start_points, end_points

    @staticmethod
    def _get_perspective_coeffs(start_points, end_points):

        a_matrix = torch.zeros(2 * len(start_points), 8, dtype=torch.float)

        for i, (p1, p2) in enumerate(zip(end_points, start_points)):
            a_matrix[2 * i, :] = torch.tensor(
                [p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
            a_matrix[2 * i + 1, :] = torch.tensor(
                [0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

        b_matrix = torch.tensor(start_points, dtype=torch.float).view(8)
        res = torch.linalg.lstsq(a_matrix, b_matrix, driver="gels").solution

        output: List[float] = res.tolist()

        return output

    def _augment_bboxes(self, bboxes, start_points, end_points, img_size):

        coeffs = self._get_perspective_coeffs(end_points, start_points)
        boxes, labels = torch.split(bboxes, [4, 1], dim=1)
        device = boxes.device

        keypoints = to_keypoints_on_image(boxes) + 0.5

        input_boxes = torch.cat([keypoints, torch.ones(keypoints.size(0), 1, device=device)], dim=1)

        theta1 = torch.tensor([[coeffs[0], coeffs[1], coeffs[2]],
                               [coeffs[3], coeffs[4], coeffs[5]]], device=device)
        theta2 = torch.tensor([[coeffs[6], coeffs[7], 1],
                               [coeffs[6], coeffs[7], 1]], device=device)

        dst1 = input_boxes @ theta1.t()
        dst2 = input_boxes @ theta2.t()

        dst = dst1 / dst2 - 1.0
        output_boxes = invert_to_keypoints_on_image_(dst, len(boxes))
        output_boxes[:, [0, 2]] = torch.clamp(output_boxes[:, [0, 2]], min=0, max=img_size[-1])
        output_boxes[:, [1, 3]] = torch.clamp(output_boxes[:, [1, 3]], min=0, max=img_size[-2])

        output = torch.cat([output_boxes, labels], dim=1)

        return output

    def _augment_keypoints(self, keypoints, start_points, end_points, img_size):

        coeffs = self._get_perspective_coeffs(end_points, start_points)
        device = keypoints.device

        input_boxes = torch.cat([keypoints, torch.ones(keypoints.size(0), 1, device=device)], dim=1)

        theta1 = torch.tensor([[coeffs[0], coeffs[1], coeffs[2]],
                               [coeffs[3], coeffs[4], coeffs[5]]], device=device)
        theta2 = torch.tensor([[coeffs[6], coeffs[7], 1],
                               [coeffs[6], coeffs[7], 1]], device=device)

        dst1 = input_boxes @ theta1.t()
        dst2 = input_boxes @ theta2.t()

        dst = dst1 / dst2 - 1.0
        _, imh, imw = img_size
        mask = (dst[:, 0] >= 0) & (dst[:, 0] <= imw) & \
               (dst[:, 1] >= 0) & (dst[:, 1] <= imh)
        dst = dst[mask]

        return dst

    def _augment_images(self, image, start_points, end_points, cval):

        return TF.perspective(
            image,
            start_points,
            end_points,
            fill=cval,
            interpolation=self.interpolation
        )

    def _apply(self, sample):

        if sample.image is None or torch.rand(1) >= self.p:
            return sample

        start_points, end_points = self._get_params(sample.shape)
        sample.image = self._augment_images(sample.image, start_points, end_points, self.cval)

        if sample.bboxes is not None:
            sample.bboxes = self._augment_bboxes(sample.bboxes, start_points, end_points,
                                                 sample.shape)

        if sample.mask is not None:
            sample.mask = self._augment_images(sample.mask, start_points, end_points, 0)

        if sample.heatmap is not None:
            sample.heatmap = self._augment_images(sample.heatmap, start_points, end_points,
                                                  self.cval)

        if sample.keypoints is not None:
            sample.keypoints = self._augment_keypoints(sample.keypoints, start_points, end_points,
                                                       sample.shape)

        return sample


class RandomRotate(Affine):

    def __init__(
            self,
            degree_min: float = -10.0,
            degree_max: float = 10.0,
            cval: int = 127,
            interpolation: str = 'nearest'
    ) -> None:
        """RandomRotate, 随机旋转, 几何变换

        Args:
            degree_min: Degree minimum, 角度最小值, [-360.0, 360.0, 0.1], -10.0
            degree_max: Degree maximum, 角度最大值, [-360.0, 360.0, 0.1], 10.0
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            interpolation: Interpolation, 插值模式, {'nearest', 'bilinear'}, 'nearest'
        """
        degree_min = eval_arg(degree_min, None)
        degree_max = eval_arg(degree_max, None)
        cval = eval_arg(cval, None)
        super().__init__(
            degree=(degree_min, degree_max),
            cval=cval,
            interpolation=interpolation
        )


class RandomAffine(Affine):

    def __init__(
            self,
            p_scale: float = 0.5,
            rnd_scale_min: float = None,
            rnd_scale_max: float = None,
            p_shear: float = 0.5,
            rnd_shear_x: float = None,
            rnd_shear_y: float = None,
            p_rotate: float = 0.5,
            rnd_rotate: float = 0.0,
            p_translate: float = 0.5,
            rnd_translate_x_pct: float = None,
            rnd_translate_y_pct: float = None,
            cval: int = 127,
            interpolation: str = 'nearest',
    ) -> None:
        """RandomAffine, 随机仿射变换, 几何变换

        Args:
            p_scale: Scale probability, 缩放变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_scale_min: Scale minimum, 缩放比例最小值, [0.1, 1000.0, 0.1], 0.2
            rnd_scale_max: Scale maximum, 缩放比例最大值, [0.1, 1000.0, 0.1], 0.2
            p_shear: Shear probability, 错切变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_shear_x: Horizontal shear value, 水平错切, [-180.0, 180.0, 0.1], 0.1
            rnd_shear_y: Vertical shear value, 垂直错切, [-180.0, 180.0, 0.1], 0.1
            p_rotate: Rotate probability, 旋转变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_rotate: Rotate angle, 旋转角度, [-180.0, 180.0, 0.1], 30
            p_translate: Translate probability, 平移变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_translate_x_pct: Horizontal translations percent, 水平平移百分比, [0.0, 1.0, 0.1], 0.1
            rnd_translate_y_pct: Vertical translations percent, 垂直平移百分比, [0.0, 1.0, 0.1], 0.1
            cval: Color value, 填充颜色, [0, 255, 1], 127
            interpolation: Interpolation, 插值模式, {"nearest", "bilinear"}, "nearest"
        """
        p_scale = eval_arg(p_scale, None)
        rnd_scale_min = eval_arg(rnd_scale_min, None)
        rnd_scale_max = eval_arg(rnd_scale_max, None)
        p_shear = eval_arg(p_shear, None)
        rnd_shear_x = eval_arg(rnd_shear_x, None)
        rnd_shear_y = eval_arg(rnd_shear_y, None)
        p_rotate = eval_arg(p_rotate, None)
        rnd_rotate = eval_arg(rnd_rotate, None)
        p_translate = eval_arg(p_translate, None)
        rnd_translate_x_pct = eval_arg(rnd_translate_x_pct, None)
        rnd_translate_y_pct = eval_arg(rnd_translate_y_pct, None)
        cval = eval_arg(cval, None)

        if (rnd_scale_min and rnd_scale_max) and torch.rand(1) < p_scale:
            scale = [rnd_scale_min, rnd_scale_max]
        else:
            scale = 1.0

        if torch.rand(1) < p_shear:
            shear_x = (0, rnd_shear_x) if rnd_shear_x else 0
            shear_y = (0, rnd_shear_y) if rnd_shear_y else 0
        else:
            shear_x, shear_y = 0, 0

        if torch.rand(1) < p_translate:
            translate_x = (0, rnd_translate_x_pct) if rnd_translate_x_pct else 0
            translate_y = (0, rnd_translate_y_pct) if rnd_translate_y_pct else 0
        else:
            translate_x, translate_y = 0, 0

        if rnd_rotate and torch.rand(1) < p_rotate:
            degree = (-rnd_rotate, rnd_rotate)
        else:
            degree = 0

        super().__init__(
            degree=degree,
            translate_x=translate_x,
            translate_y=translate_y,
            scale=scale,
            shear_x=shear_x,
            shear_y=shear_y,
            cval=cval,
            interpolation=interpolation,
        )
