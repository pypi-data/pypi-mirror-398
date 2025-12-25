#!/usr/bin/env python3

import cv2 as cv
import numpy as np

__all__ = [
    'scale_brightness',
    'adjust_color_levels',
    'clahe',
]


def scale_brightness(image: np.ndarray, factor: float = 1.0) -> np.ndarray:
    pass


def adjust_color_levels(
        image: np.ndarray,
        in_black=0,
        in_white=255,
        gamma=1.0,
        out_black=0,
        out_white=255
) -> np.ndarray:
    x = np.array(image, dtype=np.float32)

    x -= in_black
    x /= in_white - in_black
    np.clip(x, 0, 1, x)

    x **= 1 / gamma
    x *= out_white - out_black
    x += out_black
    np.clip(x, 0, 255, x)

    return np.array(x, dtype=np.uint8)


def clahe(
        image: np.ndarray,
        clip_limit: float = 1.0,
        gw: int = 2,
        gh: int = 2
) -> np.ndarray:
    impl = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=(gw, gh))
    if len(image.shape) > 2:
        img_yuv = cv.cvtColor(image, cv.COLOR_RGB2YUV)
        img_yuv[:, :, 0] = impl.apply(img_yuv[:, :, 0])
        return cv.cvtColor(img_yuv, cv.COLOR_YUV2RGB)
    else:
        return impl.apply(image)
