#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-11-30
"""
from typing import Union

import torch
from torch import Tensor
from torchvision import transforms

__all__ = [
    'normalize_image',
    'denormalize_image',
    'hwc_to_chw',
    'chw_to_hwc',
]

IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32) * 255
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32) * 255


def normalize_image(
        image: Tensor,
        mean: Union[Tensor, float] = IMAGENET_MEAN,
        std: Union[Tensor, float] = IMAGENET_STD,
        transpose=False
) -> Tensor:
    """Normalize image
    """
    image = image.to(torch.float32)

    if transpose:
        image = hwc_to_chw(image)

    image = transforms.Normalize(mean=mean, std=std)(image)  # need float input
    return image


def denormalize_image(
        image: Tensor,
        mean: Union[Tensor, float] = IMAGENET_MEAN,
        std: Union[Tensor, float] = IMAGENET_STD,
        transpose=False
) -> Tensor:
    """Denormalize image
    """
    image = transforms.Normalize(-mean / std, 1.0 / std)(image)

    if transpose:
        image = chw_to_hwc(image)

    image = image.to(torch.uint8)
    return image


def hwc_to_chw(image: Tensor) -> Tensor:
    """HWC channel to CHW
    """
    if len(image.shape) != 3:
        raise RuntimeError('Image should be a 3-dimensional tensor.')
    image = torch.permute(image, (2, 0, 1)).contiguous()
    return image


def chw_to_hwc(image: Tensor) -> Tensor:
    """CHW channel to HWC
    """
    if len(image.shape) != 3:
        raise RuntimeError('Image should be a 3-dimensional tensor.')
    image = torch.permute(image, (1, 2, 0)).contiguous()
    return image
