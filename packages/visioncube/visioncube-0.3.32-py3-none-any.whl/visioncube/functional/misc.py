#!/usr/bin/env python3

"""
@author: xi
@since: 2024-01-10
"""

from functools import lru_cache
from importlib import import_module

import numpy as np

__all__ = [
    'read_pcd_as_image',
    'correct_depth_by_xy_plane',
]


@lru_cache
def _import_open3d():
    try:
        return import_module('open3d')
    except ImportError:
        raise ImportError('Processing cloud points data requires `open3d` package.')


def read_pcd_as_image(path: str, resolution: float = 1.0, dtype=np.float32) -> np.ndarray:
    o3d = _import_open3d()

    pcd_data = o3d.io.read_point_cloud(path)

    pts = np.array(pcd_data.points, dtype=dtype) / resolution
    pts[:, 0:2] -= np.min(pts[:, 0:2], 0) - 0.5

    y = np.array(pts[:, 0], dtype=np.int32)
    x = np.array(pts[:, 1], dtype=np.int32)
    height = np.max(y) + 1
    width = np.max(x) + 1
    image = np.zeros((height, width), dtype=dtype)
    image[y, x] = pts[:, 2]

    return image


def correct_depth_by_xy_plane(
        image: np.ndarray,
        num_samples: int = 4096,
        dtype=np.float32
) -> np.ndarray:
    if len(image.shape) != 2:
        raise ValueError('Expect a 2d image.')

    input_dtype = image.dtype
    if input_dtype != dtype:
        image = image.astype(dtype)

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
    y = np.random.randint(0, height - 1, (num_samples,), dtype=np.int32)
    x = np.random.randint(0, width - 1, (num_samples,), dtype=np.int32)
    z = image[y, x]
    yx1 = np.stack([y, x, np.ones((num_samples,), dtype=image.dtype)], -1, dtype=image.dtype)
    u, s, vh = np.linalg.svd(yx1, full_matrices=False)  # Computing the pseudo inverse by SVD is faster.
    m = vh.T * (1.0 / (s + 1e-10)) @ u.T @ z
    # m = np.linalg.pinv(yx1) @ z

    # 2) Compute the plane (z) based on the (x, y) pairs.
    yx1 = np.stack([
        *reversed(np.meshgrid(range(width), range(height))),
        np.ones_like(image)
    ], -1, dtype=image.dtype)
    plane = yx1 @ m

    # 3) Correct the depth by subtracting the plane values.
    image = image - plane
    if input_dtype != dtype:
        image = image.astype(input_dtype)
    return image

# def main():
#     path = '/home/xi/Downloads/22#-1_63_001MEAJ3000001DC90500951_01091442__sidelD3-1_3D.pcd'
#     image = cube.read_pcd_as_image(path, resolution=0.05)
#
#     x = image[183:2120, 390:7718]
#     x = cube.correct_depth_by_xy_plane(x)
#
#     plt.imshow(x)
#     plt.show()
#     return 0
#
#
# if __name__ == '__main__':
#     exit(main())
