#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2024-03-25
"""
import math
from typing import Tuple

import numpy as np


def circular_annulus(image: np.ndarray, center: Tuple[int, int], radius: int, ring_width: int):
    """
    圆环展开为矩形
    center: 圆环的圆心
    radius: 是外环的的半径
    ring_width: 环的宽度
    """
    # 计算输出图像的尺寸
    cx, cy = center
    ow = int(2 * radius * math.pi)
    oh = ring_width

    # 创建极坐标网格
    theta = np.linspace(0, 2 * math.pi, ow, endpoint=False)
    rho = np.linspace(radius - oh + 1, radius, oh)

    # 创建极坐标网格的网格化版本
    theta_grid, rho_grid = np.meshgrid(theta, rho)

    # 将极坐标转换为直角坐标
    x_grid = cx + rho_grid * np.cos(theta_grid)
    y_grid = cy - rho_grid * np.sin(theta_grid)

    x_grid_int = np.round(x_grid).astype(int)
    y_grid_int = np.round(y_grid).astype(int)

    # 由于x_grid和y_grid可能包含小数，我们需要将它们四舍五入到最接近的整数，
    # 并且确保它们在原始图像的边界内
    x_grid = np.clip(x_grid_int, 0, image.shape[1] - 1)
    y_grid = np.clip(y_grid_int, 0, image.shape[0] - 1)

    # 使用这些坐标从原始图像中获取像素值
    out_img = image[y_grid, x_grid, :]

    return out_img
