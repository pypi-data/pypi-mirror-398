#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2024-03-25
"""
import math

import numpy as np

from ..common import AbstractTransform

__all__ = [
    "CircularAnnulus",
]


class CircularAnnulus(AbstractTransform):

    def __init__(self, center_x, center_y, radius, ring_width):
        """
        CircularAnnulus, 圆环展开, 极坐标展开

        Args:
            center_x: Center X, 圆心的x坐标, [0, 1000, 1], 0
            center_y: Center Y, 圆心的y坐标, [0, 1000, 1], 0
            radius:  Radius, 半径, [0, 1000, 1], 0
            ring_width: Ring Width, 环的宽度, [0, 1000, 1], 0
        """
        super().__init__(use_gpu=False)

        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.ring_width = ring_width

    def _apply(self, sample):

        if sample.image is None:
            return sample

        image = sample.image

        ow = int(2 * self.radius * math.pi)
        oh = self.ring_width

        # 创建极坐标网格
        theta = np.linspace(0, 2 * math.pi, ow, endpoint=False)
        rho = np.linspace(self.radius - oh + 1, self.radius, oh)

        # 创建极坐标网格的网格化版本
        theta_grid, rho_grid = np.meshgrid(theta, rho)

        # 将极坐标转换为直角坐标
        x_grid = self.center_x + rho_grid * np.cos(theta_grid)
        y_grid = self.center_y - rho_grid * np.sin(theta_grid)

        x_grid_int = np.round(x_grid).astype(int)
        y_grid_int = np.round(y_grid).astype(int)

        # 由于x_grid和y_grid可能包含小数，我们需要将它们四舍五入到最接近的整数，
        # 并且确保它们在原始图像的边界内
        x_grid = np.clip(x_grid_int, 0, image.shape[1] - 1)
        y_grid = np.clip(y_grid_int, 0, image.shape[0] - 1)

        # 使用这些坐标从原始图像中获取像素值
        sample.image = image[y_grid, x_grid, :]

        return sample


# TODO
class EllipseAnnulus(AbstractTransform):

    def __init__(self):
        super().__init__(use_gpu=False)

    def _apply(self, sample):
        ...

