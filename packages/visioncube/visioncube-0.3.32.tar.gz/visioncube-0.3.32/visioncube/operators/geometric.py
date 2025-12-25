#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
author：yannan1
since：2023-06-16
"""
import math
import random
from typing import Tuple

import cv2
from imgaug import augmenters as iaa
import numpy as np

from ..common import AbstractSample, eval_arg, ImgaugAdapter
from ..common import DEFAULT_IMAGE_FIELD, DEFAULT_MASK_FIELD, DEFAULT_BBOX_FIELD, \
    DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD

__all__ = [
    'Rotate',
    'Affine',
    'RandomRotate',
    'RandomPerspective',
    'RandomAffine',
]

ATTRS = [DEFAULT_IMAGE_FIELD, DEFAULT_MASK_FIELD, DEFAULT_BBOX_FIELD,
         DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD]


class Rotate(ImgaugAdapter):

    def __init__(self, degree: float = 20.0, cval: int = 127, mode: str = 'constant') -> None:
        """Rotate, 旋转变换, 几何变换

        Args:
            degree: Rotate angle, 旋转角度, [-360.0, 360.0, 0.1], 20.0
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            mode: Fill mode, 填充模式, {'constant', 'edge', 'reflect'}, 'constant'
        """
        degree = eval_arg(degree, None)
        self._degree = degree
        cval = eval_arg(cval, None)
        if mode not in {'constant', 'edge', 'reflect'}:
            mode = 'constant'

        super().__init__(iaa.Rotate(rotate=degree, cval=cval, mode=mode), ATTRS)
    
    def _calculate_rotation_matrix(self, image_size: Tuple[int, int]):
        """
        计算旋转变换矩阵
        
        Args:
            angle_deg: 旋转角度(度)
            image_size: 原始图像尺寸 (height, width)
            
        Returns:
            3x3 齐次变换矩阵
        """
        h, w = image_size
        
        # 计算原始中心点
        cx_orig = w / 2.0
        cy_orig = h / 2.0

        # 构建旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D((cx_orig, cy_orig), self._degree, 1.0)
        
        # 转换为齐次矩阵
        homogeneous_matrix = np.vstack([rotation_matrix, [0, 0, 1]])
        
        return homogeneous_matrix
        
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        image_size = input_shape[:2]
        self.matrix = self._calculate_rotation_matrix(image_size)
        super()._update_transform(input_shape, output_sample)


class Affine(ImgaugAdapter):

    def __init__(
            self,
            degree: float = 20.0,
            translate_x: int = 0,
            translate_y: int = 0,
            scale: float = 1.0,
            shear_x: float = 0.0,
            shear_y: float = 0.0,
            cval: int = 0,
            mode: str = 'constant',
            fit_output: bool = False
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
            mode: Fill mode, 填充模式, {'constant', 'edge', 'reflect'}, 'constant'
            fit_output: FitOutput, 是否扩展图像尺寸, {'True', 'False'}, 'False'
        """
        self.degree = eval_arg(degree, None)
        self.translate_x = eval_arg(translate_x, int)
        self.translate_y = eval_arg(translate_y, int)
        self.scale = eval_arg(scale, None)
        self.shear_x = eval_arg(shear_x, None)
        self.shear_y = eval_arg(shear_y, None)
        self.cval = eval_arg(cval, None)
        self.fit_output = eval_arg(fit_output, None)

        super(Affine, self).__init__(
            iaa.Affine(
                translate_px={
                    'x': self.translate_x,
                    'y': self.translate_y
                },
                rotate=self.degree,
                scale=self.scale,
                shear={
                    'x': self.shear_x,
                    'y': self.shear_y
                },
                cval=self.cval,
                mode=mode,
                fit_output=self.fit_output
            ), ATTRS)
        
    def _calculate_affine_matrix(self, image_size: Tuple[int, int]):
        """
        计算仿射变换矩阵
        
        Args:
            image_size: 原始图像尺寸 (height, width)
            
        Returns:
            3x3 齐次变换矩阵
        """
        h, w = image_size
        
        # 获取随机参数值
        degree = self.degree
        tx = self.translate_x
        ty = self.translate_y
        scale = self.scale
        shear_x = self.shear_x
        shear_y = self.shear_y
        
        
        # 转换为弧度
        theta = math.radians(degree)
        sx = math.radians(shear_x)
        sy = math.radians(shear_y)
        
        # 计算中心点
        cx = w / 2.0
        cy = h / 2.0
        
        # 平移矩阵
        translate_matrix = np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ])
        
        # 中心平移矩阵
        center_matrix = np.array([
            [1, 0, cx],
            [0, 1, cy],
            [0, 0, 1]
        ])
        
        # 中心逆平移矩阵
        inv_center_matrix = np.array([
            [1, 0, -cx],
            [0, 1, -cy],
            [0, 0, 1]
        ])
        
        # 旋转矩阵
        rotation_matrix = np.array([
            [math.cos(theta), -math.sin(theta), 0],
            [math.sin(theta), math.cos(theta), 0],
            [0, 0, 1]
        ])
        
        # 错切矩阵
        shear_matrix = np.array([
            [1, math.tan(sx), 0],
            [math.tan(sy), 1, 0],
            [0, 0, 1]
        ])
        
        # 缩放矩阵
        scale_matrix = np.array([
            [scale, 0, 0],
            [0, scale, 0],
            [0, 0, 1]
        ])
        
        # 组合变换矩阵: T = T_trans * T_center * T_shear * T_scale * T_rot * T_inv_center
        transform = (
            translate_matrix @ 
            center_matrix @ 
            shear_matrix @ 
            scale_matrix @ 
            rotation_matrix @
            inv_center_matrix
        )
        
        return transform
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        image_size = input_shape[:2]
        self.matrix = self._calculate_affine_matrix(image_size)
        super()._update_transform(input_shape, output_sample)


class RandomRotate(ImgaugAdapter):

    def __init__(
            self,
            degree_min: float = -10.0,
            degree_max: float = 10.0,
            cval: int = 127,
            mode='constant'
    ) -> None:
        """RandomRotate, 随机旋转变换, 几何变换

        Args:
            degree_min: Degree minimum, 角度最小值, [-360.0, 360.0, 0.1], -10.0
            degree_max: Degree maximum, 角度最大值, [-360.0, 360.0, 0.1], 10.0
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            mode: Fill mode, 填充模式, {'constant', 'edge', 'reflect'}, 'constant'
        """
        degree_min = eval_arg(degree_min, None)
        degree_max = eval_arg(degree_max, None)
        cval = eval_arg(cval, None)
        if mode not in {'constant', 'edge', 'reflect'}:
            mode = 'constant'

        super().__init__(iaa.Rotate(rotate=(degree_min, degree_max), cval=cval, mode=mode), ATTRS)


class RandomPerspective(ImgaugAdapter):

    def __init__(
            self,
            scale_min: float = 0.0,
            scale_max: float = 0.1,
            p: float = 0.5,
            cval: int = 127,
            mode: str = "constant"
    ) -> None:
        """RandomRotate, 随机透视变换, 几何变换

        Args:
            scale_min: Scale minimum, 标准差最小值, [0.0, 0.1, 0.1], 0.0
            scale_min: Scale maximum, 标准差最大值, [0.0, 0.1, 0.1], 0.1
            p: Probability, 变换概率, [0.0, 1.0, 0.1], 0.5
            cval: Color Value, 填充颜色, [0, 255, 1], 127
            mode: Fill mode, 填充模式, {'constant', 'edge', 'reflect'}, 'constant'
        """
        scale_min = eval_arg(scale_min, None)
        scale_max = eval_arg(scale_max, None)
        cval = eval_arg(cval, None)

        if random.random() < p:
            super().__init__(
                iaa.PerspectiveTransform(scale=(scale_min, scale_max), cval=cval, mode=mode), ATTRS)
        else:
            super().__init__(iaa.Identity(), ATTRS)


class RandomAffine(ImgaugAdapter):

    def __init__(
            self,
            p_scale: float = 1.0,
            rnd_scale_min: float = None,
            rnd_scale_max: float = None,
            p_shear: float = 1.0,
            rnd_shear_x: float = None,
            rnd_shear_y: float = None,
            p_rotate: float = 1.0,
            rnd_rotate: float = 0.0,
            p_translate: float = 1.0,
            rnd_translate_x_pct: float = None,
            rnd_translate_y_pct: float = None,
            cval: int = 127,
            mode: str = 'constant',
    ) -> None:
        """RandomAffine, 随机仿射变换, 几何变换

        Args:
            p_scale: Scale probability, 缩放变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_scale_min: Scale minimum, 缩放比例最小值, [0.1, 1000.0, 0.1], None
            rnd_scale_max: Scale maximum, 缩放比例最大值, [0.1, 1000.0, 0.1], None
            p_shear: Shear probability, 错切变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_shear_x: Horizontal shear value, 水平错切, [-180.0, 180.0, 0.1], None
            rnd_shear_y: Vertical shear value, 垂直错切, [-180.0, 180.0, 0.1], None
            p_rotate: Rotate probability, 旋转变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_rotate: Rotate angle, 旋转角度, [-180.0, 180.0, 0.1], 0.0
            p_translate: Translate probability, 平移变换概率, [0.0, 1.0, 0.1], 0.5
            rnd_translate_x_pct: Horizontal translations percent, 水平平移百分比, [0.0, 1.0, 0.1], None
            rnd_translate_y_pct: Vertical translations percent, 垂直平移百分比, [0.0, 1.0, 0.1], None
            cval: Color value, 填充颜色, [0, 255, 1], 127
            mode: Fill mode, 填充模式, {'constant', 'edge', 'reflect'}, 'constant'
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

        aug_list = []

        if rnd_scale_min or rnd_scale_max:
            scale_aug = iaa.Affine(scale=(rnd_scale_min, rnd_scale_max), mode=mode, cval=cval)
            aug_list.append(iaa.Sometimes(p_scale, scale_aug))

        if rnd_shear_x or rnd_shear_y:
            shear_aug = iaa.Affine(shear={
                'x': (0 - rnd_shear_x, rnd_shear_x),
                'y': (0 - rnd_shear_y, rnd_shear_y)
            },
                mode=mode,
                cval=cval)
            aug_list.append(iaa.Sometimes(p_shear, shear_aug))

        if rnd_translate_x_pct or rnd_translate_y_pct:
            assert 0 < rnd_translate_x_pct <= 1
            assert 0 < rnd_translate_y_pct <= 1
            translate_aug = iaa.Affine(
                translate_percent={
                    'x': (0.1, rnd_translate_x_pct),
                    'y': (0.1, rnd_translate_y_pct),
                },
                mode=mode,
                cval=cval)
            aug_list.append(iaa.Sometimes(p_translate, translate_aug))

        if rnd_rotate:
            rotate_aug = iaa.Rotate((-rnd_rotate, rnd_rotate), mode=mode, cval=cval)
            aug_list.append(iaa.Sometimes(p_rotate, rotate_aug))
        super(RandomAffine, self).__init__(iaa.Sequential(aug_list), ATTRS)
