#!/usr/bin/env python3

"""
@author: xi
@since: 2023-11-28
"""

import io
from importlib import import_module
from types import ModuleType
from typing import Union, Optional

import cv2 as cv
import numpy as np
from matplotlib import cm

import visioncube as cube
from visioncube.merge_mertens import MergeMertens

tifffile: Union[ModuleType, None] = None

__all__ = [
    'read_tiff',
    'hdr_to_uint8',
    'hdr_to_rgb',
    'HDRSplitMerge',
]


def _ensure_tifffile():
    global tifffile
    if tifffile is None:
        try:
            tifffile = import_module('tifffile')
        except ImportError:
            raise RuntimeError(
                'Reading and writing TIFF file requires tifffile.'
                'You should install it by "pip install tifffile" '
            )


def read_tiff(path_or_data: Union[str, bytes, np.ndarray]) -> np.ndarray:
    if isinstance(path_or_data, np.ndarray):
        return path_or_data
    elif isinstance(path_or_data, bytes):
        path_or_data = io.BytesIO(path_or_data)
    _ensure_tifffile()
    return tifffile.imread(path_or_data)


def hdr_to_uint8(
        hdr: np.ndarray,
        min_value: Union[int, float],
        max_value: Union[int, float]
) -> np.ndarray:
    assert (len(hdr.shape) == 2) or (len(hdr.shape) == 3 and hdr.shape[-1] == 3)
    assert min_value < max_value
    x = hdr.astype(np.float32)
    np.clip(x, min_value, max_value, out=x)
    x -= min_value
    x /= ((max_value - min_value) / 255.0)
    x += 0.5
    return x.astype(np.uint8)


def hdr_to_rgb(
        hdr: np.ndarray,
        min_value: Union[int, float],
        max_value: Union[int, float],
        cmap='viridis'
) -> np.ndarray:
    assert (len(hdr.shape) == 2)
    assert min_value < max_value
    x = hdr.astype(np.float32)
    np.clip(x, min_value, max_value, out=x)
    if cmap is None:
        x -= min_value
        x /= ((max_value - min_value) / 255.0)
        x += 0.5
        return cv.cvtColor(x.astype(np.uint8), cv.COLOR_GRAY2RGB)
    else:
        x -= min_value
        x /= (max_value - min_value)
        rgb = cm.get_cmap(cmap)(x, bytes=True)
        return rgb[:, :, :3]


class HDRSplitMerge(object):

    def __init__(
            self,
            num_splits: int,
            min_value: int,
            max_value: int,
            clip_limit: Optional[int] = None,
            tile_grid_size: int = 100,
            device=None
    ) -> None:
        self.num_splits = num_splits
        self.min_value = min_value
        self.max_value = max_value
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.fusion = MergeMertens(ksize=11, device=device)

    def __call__(self, hdr: np.ndarray) -> np.ndarray:
        if self.clip_limit is not None:
            h, w = hdr.shape[:2]
            hdr = cube.clahe(hdr, self.clip_limit, w // self.tile_grid_size, h // self.tile_grid_size)

        images = []
        step = (self.max_value - self.min_value) // self.num_splits
        for i in range(self.num_splits):
            images.append(hdr_to_uint8(hdr, self.min_value + i * step, self.min_value + (i + 1) * step))

        return self.fusion(images)
