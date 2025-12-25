#!/usr/bin/env python3

"""
@author: jinxj6
@since: 2024-01-12
"""

import numpy as np
import torch
from functools import lru_cache
from importlib import import_module

__all__ = [
    'read_pcd_as_tensor',
    'correct_depth_by_xy_plane_cuda',
]


@lru_cache
def _import_open3d():
    try:
        return import_module('open3d')
    except ImportError:
        raise ImportError('Processing cloud points data requires `open3d` package.')


def read_pcd_as_tensor(path: str, resolution: float = 1.0, dtype=torch.float32, device=None) -> torch.Tensor:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if not device else device

    o3d = _import_open3d()
    pcd_data = o3d.io.read_point_cloud(path)
    # pts = torch.tensor(pcd_data.points, dtype=dtype) / resolution
    pts = np.array(pcd_data.points, dtype=np.float32) / resolution
    pts = torch.from_numpy(pts)
    pts = pts.to(device)

    pts[:, 0:2] -= pts[:, 0:2].min(dim=0)[0] - 0.5
    y = pts[:, 0].long()
    x = pts[:, 1].long()
    height = torch.max(y) + 1
    width = torch.max(x) + 1
    image = torch.zeros((height, width), dtype=torch.float32).to(device)
    image[y, x] = pts[:, 2]
    return image


def correct_depth_by_xy_plane_cuda(
        image: torch.Tensor,
        num_samples: int = 4096,
        dtype=torch.float32,
        device=None
) -> torch.Tensor:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if not device else device
    image = image.to(device)
    if len(image.shape) != 2:
        raise ValueError('Expect a 2d image.')

    input_dtype = image.dtype
    if input_dtype != dtype:
        image = image.to(dtype)

    height, width = image.shape[0:2]
    num_samples = min(num_samples, height * width)

    # 1) Find the plane.
    # The plane is formulated by `m`: m0 * y + m1 * x + m2 = z
    #
    # | y0 x0 1 |               | z0 |
    # | y1 x1 1 |    | m0 |     | z1 |
    # | ...     | @  | m1 |  =  | ...|
    # | yn xn 1 |    | m2 |     | z2 |
    #
    # Solve the linear equation by inverse `yx1`.

    y = torch.randint(0, height - 1, (num_samples,), dtype=torch.long).to(device)
    x = torch.randint(0, width - 1, (num_samples,), dtype=torch.long).to(device)
    z = image[y, x]
    yx1 = torch.stack([y, x, torch.ones((num_samples,), dtype=image.dtype).to(device)], dim=-1)
    u, s, vh = torch.linalg.svd(yx1, full_matrices=False)
    m = vh @ (torch.diag(1.0 / (s + 1e-10)) @ u.t()) @ z.t()

    grid_x, grid_y = torch.meshgrid(torch.arange(width), torch.arange(height))

    # 2) Compute the plane (z) based on the (x, y) pairs.
    yx1 = torch.stack(
        [
            grid_x.permute(1, 0).to(device),
            grid_y.permute(1, 0).to(device),
            torch.ones_like(image)
        ], dim=-1)
    plane = yx1 @ m

    image = image - plane
    if input_dtype != dtype:
        image = image.to(input_dtype)
    return image
