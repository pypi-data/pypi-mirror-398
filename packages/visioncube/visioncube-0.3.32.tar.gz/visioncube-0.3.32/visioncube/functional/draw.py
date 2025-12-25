#!/usr/bin/env python3

"""
@author: xi
@since: 2023-11-20
"""

import cv2 as cv
import numpy as np

__all__ = [
    'draw_line',
    'draw_polygon',
    'draw_rect',
    'draw_circle'
]


def draw_line(
        image: np.ndarray,
        start_pt,
        end_pt,
        line_color,
        line_width=1,
        anti_aliased=True
) -> np.ndarray:
    return cv.line(
        image,
        start_pt,
        end_pt,
        color=line_color,
        thickness=line_width,
        lineType=cv.LINE_AA if anti_aliased else cv.LINE_8
    )


def draw_polygon(
        image: np.ndarray,
        pts: np.ndarray,
        fill_color=None,
        line_color=None,
        line_width=1,
        is_close=True,
        anti_aliased=True
) -> np.ndarray:
    if not isinstance(pts, np.ndarray):
        pts = np.array(pts)
    assert len(pts.shape) >= 2
    assert pts.shape[-1] == 2
    pts = [pts]

    if fill_color is not None:
        cv.fillPoly(
            image,
            pts=pts,
            color=fill_color,
            lineType=cv.LINE_AA if anti_aliased else cv.LINE_8
        )

    if line_color is not None and line_width > 0:
        cv.polylines(
            image,
            pts=pts,
            isClosed=is_close,
            color=line_color,
            thickness=line_width,
            lineType=cv.LINE_AA if anti_aliased else cv.LINE_8
        )
    return image


def draw_rect(
        image: np.ndarray,
        pt1,
        pt2,
        fill_color=None,
        line_color=None,
        line_width=1,
        anti_aliased=True
) -> np.ndarray:
    if fill_color is not None:
        cv.rectangle(image, pt1, pt2, fill_color, cv.FILLED, lineType=cv.LINE_AA if anti_aliased else cv.LINE_8)
    if line_color is not None and line_width > 0:
        cv.rectangle(image, pt1, pt2, line_color, line_width, lineType=cv.LINE_AA if anti_aliased else cv.LINE_8)
    return image


def draw_circle(
        image: np.ndarray,
        center,
        radius: int,
        fill_color=None,
        line_color=None,
        line_width=1,
        anti_aliased=True
) -> np.ndarray:
    if fill_color is not None:
        cv.circle(
            image,
            center,
            radius,
            color=fill_color,
            thickness=cv.FILLED,
            lineType=cv.LINE_AA if anti_aliased else cv.LINE_8
        )
    if line_color is not None and line_width > 0:
        cv.circle(
            image,
            center,
            radius,
            color=line_color,
            thickness=line_width,
            lineType=cv.LINE_AA if anti_aliased else cv.LINE_8
        )
    return image
