#!/usr/bin/env python3

import cv2 as cv
import numpy as np

__all__ = [
    'find_contours',
    'contour_area',
    'contour_bounding_rect',
    'contour_min_area_rect',
    'contour_convex_hull'
]


def find_contours(
        image: np.ndarray,
        mode: str = 'external',
        method: str = 'simple'
):
    mode_map = {
        'external': cv.RETR_EXTERNAL,
        'tree': cv.RETR_TREE,
        'list': cv.RETR_LIST
    }
    method_map = {
        'simple': cv.CHAIN_APPROX_SIMPLE,
        'none': cv.CHAIN_APPROX_NONE
    }
    assert mode in mode_map, f'mode should be one of {mode_map.keys()}.'
    assert method in method_map, f'mode should be one of {method_map.keys()}.'
    contours, hierarchy = cv.findContours(image, mode_map[mode], method_map[method])
    return [np.reshape(cnt, (-1, 2)) for cnt in contours], hierarchy[0]


def contour_area(cnt: np.ndarray) -> float:
    assert len(cnt.shape) == 2 and cnt.shape[-1] == 2
    return cv.contourArea(cnt)


def contour_bounding_rect(cnt: np.ndarray) -> np.ndarray:
    assert len(cnt.shape) == 2 and cnt.shape[-1] == 2
    x, y, w, h = cv.boundingRect(cnt)
    pts = np.array([
        [x, y],
        [x + w, y],
        [x + w, y + h],
        [x, y + h]
    ], dtype=np.int32)
    return pts


def contour_min_area_rect(cnt: np.ndarray) -> np.ndarray:
    assert len(cnt.shape) == 2 and cnt.shape[-1] == 2
    rect = cv.minAreaRect(cnt)
    pts = cv.boxPoints(rect)
    return np.array(pts, dtype=np.int32)


def contour_convex_hull(cnt: np.ndarray) -> np.ndarray:
    assert len(cnt.shape) == 2 and cnt.shape[-1] == 2
    pts = cv.convexHull(cnt)
    return np.reshape(pts, (-1, 2))
