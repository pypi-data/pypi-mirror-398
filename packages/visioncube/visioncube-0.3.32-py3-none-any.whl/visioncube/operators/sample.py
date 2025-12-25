#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-09-22
"""
import cv2 as cv
import numpy as np
from imgaug import BoundingBox, BoundingBoxesOnImage, SegmentationMapsOnImage, Keypoint, \
    KeypointsOnImage, HeatmapsOnImage

from ..common import AbstractSample, DEFAULT_IMAGE_FIELD, DEFAULT_BBOX_FIELD, DEFAULT_MASK_FIELD, \
    DEFAULT_HEATMAP_FIELD, DEFAULT_KEYPOINTS_FIELD


class Sample(AbstractSample):

    def __init__(self, doc, *args, use_homography=False, **kwargs):
        super().__init__(doc, use_homography=use_homography)

        self.default2imgaug = {
            DEFAULT_IMAGE_FIELD: 'image',
            DEFAULT_MASK_FIELD: 'segmentation_maps',
            DEFAULT_BBOX_FIELD: 'bounding_boxes',
            DEFAULT_HEATMAP_FIELD: 'heatmaps',
            DEFAULT_KEYPOINTS_FIELD: 'keypoints',
        }
        self.imgaug2default = {value: key for key, value in self.default2imgaug.items()}

    def _handle_image(self, image):
        return image

    def _handle_mask(self, mask):

        if isinstance(mask, bytes):
            mask = cv.imdecode(np.frombuffer(mask, np.byte), cv.IMREAD_GRAYSCALE)
        assert isinstance(mask, np.ndarray)

        mask_rank = len(mask.shape)
        assert mask_rank == 2 or mask_rank == 3

        return SegmentationMapsOnImage(
            arr=mask,
            shape=self.shape
        )

    def _handle_bboxes(self, bboxes):

        bbox_objs = []
        for bbox in bboxes:
            x1, y1, x2, y2, label = bbox
            bbox_obj = BoundingBox(x1, y1, x2, y2, label)
            bbox_objs.append(bbox_obj)

        return BoundingBoxesOnImage(
            bounding_boxes=bbox_objs,
            shape=self.shape
        )

    def _handle_heatmap(self, heatmap):

        heatmap = (heatmap / 255).astype('float32')
        return HeatmapsOnImage(
            arr=heatmap,  # heatmap in [0, 1], dtype=float32
            shape=self.shape
        )

    def _handle_keypoints(self, keypoints):

        kps = [Keypoint(x=kp[0], y=kp[1]) for kp in keypoints]
        return KeypointsOnImage(
            keypoints=kps,
            shape=self.shape
        )

    def get_args(self, attrs):

        aug_args = {}
        for attr_name in attrs:
            attr = getattr(self, attr_name)  # 获得属性的值
            if attr is not None:
                aug_args[self.default2imgaug[attr_name]] = attr

        return aug_args

    def set_args(self, aug_result, attrs):

        for idx, attr_name in enumerate(attrs):
            setattr(self, self.imgaug2default[attr_name], aug_result[idx])

    def _out_image(self):
        return self.image

    def _out_mask(self):
        return self.mask.arr.squeeze(-1).astype(np.uint8)

    def _out_bboxes(self):

        bbox_objs = self.bboxes.remove_out_of_image_fraction(0.8).clip_out_of_image()
        bboxes = np.empty((len(bbox_objs), 5), dtype=np.float32)

        for i, bbox_obj in enumerate(bbox_objs):
            x1, y1, x2, y2, label = bbox_obj.x1, bbox_obj.y1, bbox_obj.x2, bbox_obj.y2, bbox_obj.label
            bboxes[i] = x1, y1, x2, y2, label

        return bboxes

    def _out_heatmap(self):
        return self.heatmap.draw(size=self.heatmap.shape[:2])[0]

    def _out_keypoints(self):

        # keypoints_objs = self.keypoints.remove_out_of_image_fraction(0.8).clip_out_of_image()
        keypoints_objs = self.keypoints
        keypoints = np.empty((len(keypoints_objs), 2), dtype=np.float32)

        for i, kp in enumerate(keypoints_objs):
            keypoints[i] = kp.x, kp.y

        return keypoints
