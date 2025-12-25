#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2024-03-22
"""
from typing import List

import cv2 as cv
import numpy as np

from ..common import AbstractTransform

__all__ = [
    "ColorMeasurement",
    "WidthHeigtMeasurement"
]


class ColorMeasurement(AbstractTransform):

    def __init__(self, poly_vertices=None):
        """ColorMeasurement, 颜色测量, 测量

        Args:
            poly_vertices: Polygon vertices, 候选区点集, [], []
        """
        super().__init__(use_gpu=False)
        if poly_vertices is None:
            poly_vertices = []
        self.poly_vertices = np.array(poly_vertices, np.int32)

    def _apply(self, sample):
        if sample.image is None:
            return sample
        image = sample.image

        if self.poly_vertices:
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            mask = cv.fillPoly(mask, pts=[self.poly_vertices], color=1)

            non_zero_indices = np.nonzero(mask)
            candidate = image[non_zero_indices]
        else:
            candidate = image

        sample.color_measure = {
            "mean": np.mean(candidate),
            "median": np.median(candidate),
            "max": np.max(candidate),
            "min": np.min(candidate),
            "std": np.std(candidate),
        }

        return sample


class WidthHeightMeasurement():
    
    def __init__(self):
        """WidthHeightMeasurement, 宽度高度测量, 测量"""
        # super().__init__(use_gpu=False)
        pass

    def __call__(self, poly_vertices=None):
        """
        计算物体在水平方向上的最小宽度和最大宽度的差值。

        参数:
            contour: 输入轮廓点集，格式应为 (n, 1, 2) 或 (n, 2)，支持 OpenCV 轮廓格式。

        返回:
            float: 最大宽度与最小宽度的差值。
        """

        # 转换为 numpy 数组
        contour = np.array(poly_vertices)
        if contour.size == 0:
            return (0, 0)

        # 处理 OpenCV 的 (n, 1, 2) 格式
        if contour.ndim == 3 and contour.shape[1] == 1:
            contour = contour.reshape(-1, 2)

        # 检查格式是否为 (n, 2)
        if contour.ndim != 2 or contour.shape[1] != 2:
            raise ValueError("输入的轮廓点集格式应为 (n, 2) 或 (n, 1, 2)")

        # 获取轮廓的边界框
        x_coords = contour[:, 0]
        y_coords = contour[:, 1]
        min_x, max_x = x_coords.min(), x_coords.max()
        min_y, max_y = y_coords.min(), y_coords.max()

        # 创建掩膜图像
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        mask = np.zeros((height, width), dtype=np.uint8)

        # 将轮廓点转换为相对于掩膜左上角的坐标
        shifted_contour = contour - [min_x, min_y]
        shifted_contour = shifted_contour.astype(np.int32)

        # 填充轮廓
        cv.fillPoly(mask, [shifted_contour], 255)

        # 收集每一行的宽度
        widths = []
        for y in range(height):
            row = mask[y, :]
            if np.any(row > 0):
                x_indices = np.where(row > 0)[0]
                left = x_indices[0]
                right = x_indices[-1]
                _width = right - left + 1  # 包含左右边界
                widths.append(_width)

        # 收集每一列的高度
        heights = []
        for x in range(width):
            col = mask[:, x]
            if np.any(col > 0):
                y_indices = np.where(col > 0)[0]
                top = y_indices[0]
                bottom = y_indices[-1]
                _height = bottom - top + 1  # 包含上下边界
                heights.append(_height)

        # 处理边缘情况
        width_diff = 0
        height_diff = 0

        if len(widths) > 1:
            width_diff = max(widths) - min(widths)


        if len(heights) > 1:
            height_diff = max(heights) - min(heights)

        return (width_diff, height_diff)
