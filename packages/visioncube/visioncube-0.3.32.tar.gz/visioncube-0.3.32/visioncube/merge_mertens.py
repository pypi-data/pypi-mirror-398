#!/usr/bin/env python3

import math
from typing import Sequence

import torch
from torch.nn import functional as F

__all__ = [
    'MergeMertens',
    'merge_mertens'
]


class MergeMertens(object):

    def __init__(
            self,
            ksize: int = 5,
            sigma: float = 1.08,
            well_exposed_mean: float = 0.5,
            well_exposed_std: float = 0.2,
            weight_contrast: float = 1.0,
            weight_saturation: float = 1.0,
            weight_exposed: float = 1.0,
            num_weights_filters: int = 0,
            depth: int = None,
            dtype=torch.float32,
            device=None
    ) -> None:
        self.ksize = ksize
        self.sigma = sigma
        self.preferred_exposed = well_exposed_mean
        self.well_exposed_std = well_exposed_std
        self.weight_contrast = weight_contrast
        self.weight_saturation = weight_saturation
        self.weight_exposed = weight_exposed
        self.num_weights_filters = num_weights_filters
        self.depth = depth
        self.dtype = dtype
        self.device = device

        self.g_kernel = self._gaussian_kernel()
        self.lp_kernel = torch.as_tensor(
            [[1, 1, 1],
             [1, -8, 1],
             [1, 1, 1]],
            dtype=self.dtype,
            device=self.device
        ).div_(8).reshape((1, 1, 3, 3))

    def _gaussian_kernel(self) -> torch.Tensor:
        i = torch.arange(0, self.ksize, dtype=self.dtype, device=self.device)
        k = torch.exp(torch.neg((i - (self.ksize - 1) / 2).square() / (2 * self.sigma ** 2)))
        k *= (1 / k.sum())
        return k

    def _compute_weights(self, images: Sequence[torch.Tensor]):
        weights = []
        weights_sum = torch.zeros(images[0].shape[:2], dtype=self.dtype, device=self.device)
        for image in images:
            image = image / 255
            weight = torch.ones(image.shape[:2], dtype=self.dtype, device=self.device)

            if self.weight_contrast != 0:
                x = image.mean(2) if len(image.shape) == 3 else image
                contrast = F.conv2d(
                    F.pad(x.reshape((1, 1, *x.shape)), (1, 1, 1, 1), mode='replicate'),
                    self.lp_kernel,
                ).reshape((*x.shape[-2:],)).abs_()
                weight.mul_(contrast.pow_(self.weight_contrast))

            if self.weight_saturation != 0 and len(image.shape) == 3:
                saturation = image.mean(2).add_(1e-3)
                weight.mul_(saturation.pow_(self.weight_saturation))

            if self.weight_exposed != 0:
                well_exposed = image.add(-self.preferred_exposed).square_()
                well_exposed = well_exposed.div_(2 * self.well_exposed_std ** 2).neg_().exp_()
                well_exposed = well_exposed.prod(2, dtype=self.dtype) if len(image.shape) == 3 else well_exposed.pow_(3)
                weight.mul_(well_exposed.pow_(self.weight_exposed))

            weight.add_(1e-3)
            weights_sum.add_(weight)
            weights.append(weight)

        for i in range(len(weights)):
            weights[i].div_(weights_sum)

        if self.num_weights_filters > 0:
            weights = torch.stack(weights)
            weights = weights.unsqueeze(0)
            for _ in range(self.num_weights_filters):
                weights = self._apply_filter(weights, self.g_kernel)
            weights = weights.squeeze(0)

        return weights

    @staticmethod
    def _apply_filter(x: torch.Tensor, kernel: torch.Tensor) -> torch.Tensor:
        ch = x.shape[1]
        pad = len(kernel) // 2
        x = F.pad(x, (0, 0, pad, pad), mode='replicate')
        x = F.conv2d(x, weight=kernel.view(1, 1, -1, 1).tile(ch, 1, 1, 1), groups=ch)
        x = F.pad(x, (pad, pad, 0, 0), mode='replicate')
        x = F.conv2d(x, weight=kernel.view(1, 1, 1, -1).tile((ch, 1, 1, 1)), groups=ch)
        return x

    def _image_reduce(self, image):
        x = image
        x = x.unsqueeze(0).unsqueeze(0) if len(image.shape) == 2 else x.permute((2, 0, 1)).unsqueeze(0)

        self._apply_filter(x, self.g_kernel)
        x = F.interpolate(x, scale_factor=0.5, mode='bilinear')

        x = x.squeeze(0).squeeze(0) if len(image.shape) == 2 else x.squeeze(0).permute((1, 2, 0))
        return x

    def _image_expand(self, image, size):
        x = image
        x = x.unsqueeze(0).unsqueeze(0) if len(image.shape) == 2 else x.permute((2, 0, 1)).unsqueeze(0)

        x = F.interpolate(x, size=size, mode='bilinear')
        self._apply_filter(x, self.g_kernel)

        x = x.squeeze(0).squeeze(0) if len(image.shape) == 2 else x.squeeze(0).permute((1, 2, 0))
        return x

    def _gaussian_pyramid(self, image, depth):
        image = image.clone()
        pyramid_list = [image]
        for i in range(depth):
            image = self._image_reduce(image)
            pyramid_list.append(image)
        return pyramid_list

    def _laplacian_pyramid(self, image, depth):
        pyramid_list = self._gaussian_pyramid(image, depth)
        for i in range(depth):
            pyramid_list[i].sub_(self._image_expand(pyramid_list[i + 1], pyramid_list[i].shape[:2]))
        return pyramid_list

    def _pyramid_collapse(self, pyramid):
        depth = len(pyramid)
        collapsed = pyramid[depth - 1]
        for i in range(depth - 2, -1, -1):
            collapsed = pyramid[i].add_(self._image_expand(collapsed, pyramid[i].shape[:2]))
        return collapsed

    @torch.no_grad()
    def __call__(self, images, depth=None, avg_weights=None):
        assert isinstance(images, (tuple, list)) and len(images) >= 2
        for i in range(len(images)):
            assert images[i].shape == images[0].shape

        if depth is None:
            depth = int(math.log(min(images[0].shape[:2])) / math.log(2)) if self.depth is None else self.depth

        images = [
            torch.as_tensor(image, dtype=self.dtype, device=self.device)
            for image in images
        ]

        weights = self._compute_weights(images)

        image_pyramid_list = []
        weight_pyramid_list = []
        for image, weight in zip(images, weights):
            image_pyramid_list.append(self._laplacian_pyramid(image, depth))
            weight_pyramid_list.append(self._gaussian_pyramid(weight, depth))

        # combine pyramids with weights
        weighted_pyramid_list = []
        for i in range(depth + 1):
            weighted_pyramid = torch.zeros(image_pyramid_list[0][i].shape, dtype=self.dtype, device=self.device)
            for j in range(len(images)):
                image_pyramid = image_pyramid_list[j][i]
                weight_pyramid = weight_pyramid_list[j][i]
                if len(weight_pyramid.shape) != len(image_pyramid.shape):
                    weight_pyramid = weight_pyramid.unsqueeze(-1)
                if avg_weights is not None:
                    a = (i / depth) ** 3
                    weight_pyramid = (1 - a) * weight_pyramid + a * avg_weights[j]
                weighted_pyramid.add_(image_pyramid * weight_pyramid)
            weighted_pyramid_list.append(weighted_pyramid)

        # collapse pyramid
        fusion = self._pyramid_collapse(weighted_pyramid_list)
        fusion = fusion.clip_(0, 255).byte()
        return fusion.detach().cpu().numpy()


def merge_mertens(
        images,
        depth=None,
        avg_weights=None,
        ksize=5,
        sigma=1.08,
        well_exposed_mean=0.5,
        well_exposed_std=0.2,
        weight_contrast=1.0,
        weight_saturation=1.0,
        weight_exposed=1.0,
        num_weights_filters=0,
        dtype=torch.float32,
        device=None
):
    return MergeMertens(
        ksize=ksize,
        sigma=sigma,
        well_exposed_mean=well_exposed_mean,
        well_exposed_std=well_exposed_std,
        weight_contrast=weight_contrast,
        weight_saturation=weight_saturation,
        weight_exposed=weight_exposed,
        num_weights_filters=num_weights_filters,
        depth=depth,
        dtype=dtype,
        device=device,
    )(images, avg_weights=avg_weights)
