#!/usr/bin/env python3


from typing import Union, Optional, Sequence

import cv2 as cv
import numpy as np

__all__ = [
    'resize',
    'pad',
    'pad_to_fix_size',
    'pad_to_square',
    'crop',
    'crop_to_fix_size',
    'crop_to_square',
    'crop_roi',
]


def resize(
        image: np.ndarray,
        width: Union[int, float, None] = None,
        height: Union[int, float, None] = None,
        longer_side: Union[int, float, None] = None,
        shorter_side: Union[int, float, None] = None,
        interpolation='cubic'
) -> np.ndarray:
    original_height, original_width = image.shape[:2]

    wh_mode = width is not None or height is not None
    ls_mode = longer_side is not None or shorter_side is not None

    if wh_mode and ls_mode:
        raise RuntimeError('Only one of `width-height` or `longer-shorter` mode should be chosen.')

    if ls_mode:
        if original_width >= original_height:
            width = longer_side
            height = shorter_side
        else:
            width = shorter_side
            height = longer_side

    if width is None and height is None:
        return image

    if isinstance(width, float):
        width = int(width * original_width)
    if isinstance(height, float):
        height = int(height * original_height)

    if width is None:
        width = int(height * (original_width / original_height))
    if height is None:
        height = int(width * (original_height / original_width))

    cv_inter = {
        'cubic': cv.INTER_CUBIC,
        'linear': cv.INTER_LINEAR,
        'area': cv.INTER_AREA,
        'nearest': cv.INTER_NEAREST
    }
    assert interpolation in cv_inter

    return cv.resize(
        image,
        dsize=(width, height),
        interpolation=cv_inter[interpolation]
    )


def pad(
        image: np.ndarray,
        top: Union[int, float] = 0,
        right: Union[int, float] = 0,
        bottom: Union[int, float] = 0,
        left: Union[int, float] = 0,
        cval=0,
        mode='constant'
) -> np.ndarray:
    height, width = image.shape[:2]
    if isinstance(top, float):
        top = int(height * top)
    if isinstance(right, float):
        right = int(width * right)
    if isinstance(bottom, float):
        bottom = int(height * bottom)
    if isinstance(left, float):
        left = int(width * left)

    if isinstance(cval, (int, float)):
        cval = (cval, cval, cval)

    border_types = {
        'constant': cv.BORDER_CONSTANT,
        'edge': cv.BORDER_REPLICATE,
        'reflect': cv.BORDER_REFLECT
    }
    assert mode in border_types

    return cv.copyMakeBorder(
        image,
        top=top,
        bottom=bottom,
        left=left,
        right=right,
        borderType=border_types[mode],
        value=cval
    )


def pad_to_fix_size(
        image: np.ndarray,
        width: int,
        height: int,
        cval=0,
        mode='constant'
) -> np.ndarray:
    image_height, image_width = image.shape[0:2]
    if width < image_width:
        raise ValueError(f'Image width ({image_width}) larger than output width ({width}).')
    if height < image_height:
        raise ValueError(f'Image height ({image_height}) larger than output height ({height}).')

    top = (height - image_height) // 2
    right = (width - image_width) // 2
    bottom = height - image_height - top
    left = width - image_width - right

    return pad(image, top, right, bottom, left, cval, mode)


def pad_to_square(
        image: np.ndarray,
        size: Union[int, None] = None,
        cval=0,
        mode='constant'
) -> np.ndarray:
    return pad_to_fix_size(image, size, size, cval, mode)


def crop(
        image: np.ndarray,
        top: Union[int, float] = 0,
        right: Union[int, float] = 0,
        bottom: Union[int, float] = 0,
        left: Union[int, float] = 0
) -> np.ndarray:
    height, width = image.shape[0:2]
    if top + bottom >= height:
        raise ValueError(f'Crop top ({top}) + bottom ({bottom}) should less than image height ({height}).')
    if left + right >= width:
        raise ValueError(f'Crop left ({left}) + right ({right}) should less than image width ({width}).')
    return np.array(image[top:-bottom, left:-bottom, ...])


def crop_to_fix_size(
        image: np.ndarray,
        width: int,
        height: int
) -> np.ndarray:
    image_height, image_width = image.shape[0:2]
    if width > image_width:
        raise ValueError(f'Crop width ({width}) should less than image width ({image_width}).')
    if width > image_width:
        raise ValueError(f'Crop height ({height}) should less than image height ({image_height}).')

    top = (image_height - height) // 2
    right = (image_width - width) // 2
    bottom = image_height - height - top
    left = image_width - width - right

    return crop(image, top, right, bottom, left)


def crop_to_square(image: np.ndarray, size: int) -> np.ndarray:
    return crop_to_fix_size(image, size, size)


def crop_roi(image: np.ndarray, roi_coord: Optional[Union[np.ndarray, Sequence]] = None) -> np.ndarray:
    if roi_coord is None:
        return image
    if isinstance(roi_coord, np.ndarray):
        roi_coord = roi_coord.ravel().tolist()
    if not isinstance(roi_coord, Sequence):
        raise TypeError('roi_coord type error')

    x1, y1, x2, y2 = roi_coord
    y1 = min(max(0, y1), image.shape[0])
    y2 = min(max(0, y2), image.shape[0])
    x1 = min(max(0, x1), image.shape[1])
    x2 = min(max(0, x2), image.shape[1])
    y1, y2 = min(y1, y2), max(y1, y2)
    x1, x2 = min(x1, x2), max(x1, x2)
    roi = image[y1:y2, x1:x2, ...]

    return roi
