#!/usr/bin/env python3

import math
from typing import *

import cv2 as cv
import numpy as np

__all__ = [
    'flip_ud',
    'flip_lr',
    'affine',
    'wrapper_affine_matrix',
    'rotate',
    'rotate90',
]


def flip_ud(image: np.ndarray) -> np.ndarray:
    return np.flip(image, 0)


def flip_lr(image: np.ndarray) -> np.ndarray:
    return np.flip(image, 1)


def affine(
        image: np.ndarray,
        mat: np.ndarray,
        output_width: Union[int, None] = None,
        output_height: Union[int, None] = None,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
        cval=0,
        mode='constant'
) -> np.ndarray:
    if not (len(mat.shape) == 2 and mat.shape[0] in {2, 3} and mat.shape[1] == 3):
        raise ValueError('`mat` should be a 3x3 or 2x3 matrix.')

    original_height, original_width = image.shape[:2]
    if output_width is None:
        output_width = original_width
    if output_height is None:
        output_height = original_height

    if isinstance(cval, (int, float)):
        cval = (cval, cval, cval)

    border_types = {
        'constant': cv.BORDER_CONSTANT,
        'edge': cv.BORDER_REPLICATE,
        'reflect': cv.BORDER_REFLECT
    }
    assert mode in border_types

    # By default, all transforms are perform wrt the top-left corner of the image, since the (0, 0) is defined there.
    # If we want to change the (0, 0) for transforms, we should slightly modify the affine matrix by applying a serials
    # of translation operations.
    mat = wrapper_affine_matrix(
        mat,
        input_width=original_width,
        input_height=original_height,
        output_width=output_width,
        output_height=output_height,
        center_x=center_x,
        center_y=center_y
    )
    return cv.warpAffine(
        image,
        mat[0:2, :] if mat.shape[0] == 3 else mat,
        dsize=(output_width, output_height),
        borderMode=border_types[mode],
        borderValue=cval
    )


def wrapper_affine_matrix(
        m: np.ndarray,
        input_width: float,
        input_height: float,
        output_width: float,
        output_height: float,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
) -> np.ndarray:
    if m.shape[0] < 3:
        m = np.concatenate([m, np.array([[0.0, 0.0, 1.0]], dtype=np.float32)], 0)
    if center_x is not None or center_y is not None:
        if center_x is None:
            center_x = 0.0
        if center_y is None:
            center_y = 0.0
        move = np.array([
            [1.0, 0.0, -center_x],
            [0.0, 1.0, -center_y],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        restore = np.array([
            [1.0, 0.0, center_x],
            [0.0, 1.0, center_y],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        m = restore @ m @ move

    if input_width != output_width or input_height != output_height:
        view = np.array([
            [1.0, 0.0, 0.5 * (output_width - input_width)],
            [0.0, 1.0, 0.5 * (output_height - input_height)],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        m = view @ m

    return m


def rotate(
        image: np.ndarray,
        degree: float = 0.0,
        width: Union[int, None] = None,
        height: Union[int, None] = None,
        cval=0,
        mode='constant',
        center=True
) -> np.ndarray:
    original_height, original_width = image.shape[:2]
    if width is None:
        width = original_width
    if height is None:
        height = original_height

    theta = degree / 180 * math.pi
    mat = np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1]
    ], dtype=np.float32)

    return affine(
        image,
        mat,
        output_width=width,
        output_height=height,
        center_x=original_width * 0.5 if center else None,
        center_y=original_height * 0.5 if center else None,
        cval=cval,
        mode=mode
    )


def rotate90(image: np.ndarray, k=1) -> np.ndarray:
    """
    Rotate the image 90 degrees
    """
    return np.rot90(image, k=k)
