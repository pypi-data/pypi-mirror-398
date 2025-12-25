#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-07-25
"""
import torch


def to_keypoints_on_image(boxes):
    """
    boxes:
        [[xmin, ymin, xmax, ymax], [...]]
    """
    arr = torch.zeros((len(boxes), 2 * 4), dtype=torch.float32, device=boxes.device)

    for i, box in enumerate(boxes):
        arr[i] = torch.tensor([
            box[0], box[1],
            box[2], box[1],
            box[2], box[3],
            box[0], box[3],
        ])

    return arr.reshape((-1, 2))


def invert_to_keypoints_on_image_(keypoints, bnd_num):
    """
    Args:
        keypoints: Multiples of 4
        [[x1, y1], [x2，y2], [x3, y3], [x4, y4], [x5, y5], [x6, y6], [x7, y7], [x8, y8], ...]

    Returns:
        [[xmin1, ymin1, xmax2, ymax2], [xmin3, ymin3, xmax4, ymax4]]

    """

    assert len(keypoints) == bnd_num * 4, (
            "Expected %d coordinates, got %d." % (bnd_num * 2, len(keypoints)))

    output = torch.zeros((bnd_num, 4), device=keypoints.device)
    for i in range(bnd_num):
        xx = [keypoints[4 * i + 0][0], keypoints[4 * i + 1][0],
              keypoints[4 * i + 2][0], keypoints[4 * i + 3][0]]
        yy = [keypoints[4 * i + 0][1], keypoints[4 * i + 1][1],
              keypoints[4 * i + 2][1], keypoints[4 * i + 3][1]]
        output[i] = torch.tensor([
            min(xx), min(yy), max(xx), max(yy)
        ])
    return output
