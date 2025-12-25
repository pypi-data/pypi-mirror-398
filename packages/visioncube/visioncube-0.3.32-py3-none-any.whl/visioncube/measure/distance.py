#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：liying50
since：2025-11-12
"""
from typing import List

import cv2 as cv
import numpy as np

from ..common import AbstractTransform

__all__ = [
    "SparseLineDistance",
]


class SparseLineDistance(AbstractTransform):

    def __init__(self, poly_vertices=None):
        """SparseLineDistance, 稀线测量, 测量

        Args:
            poly_vertices: Polygon vertices, 候选区点集, [], []
        """
        super().__init__(use_gpu=False)
        if poly_vertices is None:
            poly_vertices = []
        self.poly_vertices = np.array(poly_vertices, np.int32)

    @staticmethod    
    def calculate_line_distance(image):
        # @shaoxy6
        if image.ndim == 3 and image.shape[-1] == 3:
            image = cv.cvtColor(image, cv.COLOR_RGB2GRAY)
        binary_image = cv.adaptiveThreshold(
            image, 255,
            cv.ADAPTIVE_THRESH_MEAN_C,  # 均值法
            cv.THRESH_BINARY,           # 二值化类型
            blockSize=5,                # 核大小（11x11的邻域）
            C=0                   # 常数（从均值中减去）
        )
        contours,_ = cv.findContours(
            binary_image, 
            mode=cv.RETR_EXTERNAL,  # 适合提取线的外轮廓（忽略内部细节）
            method=cv.CHAIN_APPROX_NONE  # 简化轮廓，减少点数量
        )
        H,W = binary_image.shape
        mean = []
        maxx = []
        for _, cnt in enumerate(contours):
            area = cv.contourArea(cnt)
            if area < W:
                continue
            dis = []
            dic = dict()
            for l in cnt:
                if l[0][0] not in dic:
                    dic[l[0][0]] = []
                dic[l[0][0]].append(l[0][1])
            for _,value in dic.items():
                dis.append(max(value) - min(value) +1)
            mean.append(np.mean(dis))
            maxx.append(np.max(dis))
        return np.mean(mean),np.max(maxx)

    def _apply(self, sample):
        if sample.image is None:
            return sample
        image = sample.image

        if self.poly_vertices:
            # 转换为 numpy 数组
            contour = np.array(self.poly_vertices)
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
            patch = image[min_y: max_y, min_x: max_x]
        else:
            patch = image
        mean_distance, max_distance = self.calculate_line_distance(patch)
        return (mean_distance, max_distance)
