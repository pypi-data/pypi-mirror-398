#!/usr/bin/env python3


from typing import Union
import os

import cv2 as cv
import numpy as np

__all__ = [
    'IMAGENET_MEAN',
    'IMAGENET_STD',
    'read_image',
    'write_image',
    'normalize_image',
    'denormalize_image',
    'hwc_to_chw',
    'chw_to_hwc',
    'rgb_to_gray',
    'gray_to_rgb',
    'bgr_to_rgb',
    'rgb_to_bgr',
]

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], np.float32) * 255
IMAGENET_STD = np.array([0.229, 0.224, 0.225], np.float32) * 255


def read_image(
        path_or_data: Union[str, bytes, np.ndarray],
        grayscale: bool = False
) -> np.ndarray:
    if isinstance(path_or_data, str):
        # Load image from file path.
        if grayscale:
            image = cv.imread(path_or_data, cv.IMREAD_GRAYSCALE)
        else:
            image = cv.imread(path_or_data, cv.IMREAD_COLOR)
            if image is None:
                raise RuntimeError(f'Failed to load image {path_or_data}')
            cv.cvtColor(image, cv.COLOR_BGR2RGB, image)  # opencv load image as BGR by default
    elif isinstance(path_or_data, bytes):
        # Load image from bytes of the image file.
        if grayscale:
            image = cv.imdecode(np.frombuffer(path_or_data, np.byte), cv.IMREAD_GRAYSCALE)
        else:
            image = cv.imdecode(np.frombuffer(path_or_data, np.byte), cv.IMREAD_COLOR)
            if image is None:
                raise RuntimeError('Failed to load image')
            cv.cvtColor(image, cv.COLOR_BGR2RGB, image)  # opencv load image as BGR by default
    elif isinstance(path_or_data, np.ndarray):
        # Image already loaded.
        image = path_or_data
        if grayscale and len(image.shape) > 2 and image.shape[-1] > 1:
            image = cv.cvtColor(image, cv.COLOR_RGB2GRAY, image)
    else:
        raise RuntimeError(f'Invalid input type {type(path_or_data)}.')
    return image


def write_image(image: np.ndarray, output_path):
    if len(image.shape) == 3:
        image = np.flip(image, 2)
    # cv.imwrite(output_path, image)
    compression_format = os.path.splitext(output_path)[-1]
    cv.imencode(compression_format, image)[1].tofile(output_path)


def normalize_image(
        image: np.ndarray,
        mean: Union[np.ndarray, float] = IMAGENET_MEAN,
        std: Union[np.ndarray, float] = IMAGENET_STD,
        transpose=False
) -> np.ndarray:
    """Normalize image
    """
    image = np.array(image, dtype=np.float32)
    image -= mean
    image /= std
    if transpose:
        image = hwc_to_chw(image)
    return image


def denormalize_image(
        image: np.ndarray,
        mean: Union[np.ndarray, float] = IMAGENET_MEAN,
        std: Union[np.ndarray, float] = IMAGENET_STD,
        transpose=False
) -> np.ndarray:
    """Denormalize image
    """
    if transpose:
        image = chw_to_hwc(image)
    image *= std
    image += mean
    np.clip(image, 0, 255, out=image)
    image = np.array(image, dtype=np.uint8)
    return image


def hwc_to_chw(image: np.ndarray) -> np.ndarray:
    """HWC channel to CHW
    """
    if len(image.shape) != 3:
        raise RuntimeError('Image should be a 3-dimensional tensor/ndarray.')
    image = np.transpose(image, (2, 0, 1))
    image = np.ascontiguousarray(image)
    return image


def chw_to_hwc(image: np.ndarray) -> np.ndarray:
    """CHW channel to HWC
    """
    if len(image.shape) != 3:
        raise RuntimeError('Image should be a 3-dimensional tensor/ndarray.')
    image = np.transpose(image, (1, 2, 0))
    image = np.ascontiguousarray(image)
    return image


def rgb_to_gray(image: np.ndarray) -> np.ndarray:
    return cv.cvtColor(image, cv.COLOR_RGB2GRAY) if len(image.shape) == 3 else image


def gray_to_rgb(image: np.ndarray) -> np.ndarray:
    return cv.cvtColor(image, cv.COLOR_GRAY2RGB) if len(image.shape) == 2 else image


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    return cv.cvtColor(image, cv.COLOR_BGR2RGB)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
    return cv.cvtColor(image, cv.COLOR_RGB2BGR)