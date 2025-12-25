#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2024-03-25
"""
from typing import List, Dict

import cv2 as cv
import numpy as np


def color_measurement(image: np.ndarray, poly_vertices: List[List]) -> Dict:
    """
    color_measurement, 颜色测量
    """
    poly_vertices = np.array(poly_vertices, np.int32)

    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    mask = cv.fillPoly(mask, pts=[poly_vertices], color=1)

    non_zero_indices = np.nonzero(mask)
    candidate = image[non_zero_indices]

    return {
        "mean": np.mean(candidate),
        "median": np.median(candidate),
        "max": np.max(candidate),
        "min": np.min(candidate),
        "std": np.std(candidate),
    }
