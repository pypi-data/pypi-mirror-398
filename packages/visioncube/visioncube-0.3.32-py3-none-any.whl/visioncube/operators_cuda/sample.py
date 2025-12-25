#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1, anpc1
since：2023-09-22
update：2023-09-22
: description: Sample 增加tensor支持

"""
import torch
import cv2 as cv
import numpy as np

from ..common import AbstractSample
from ..functional_cuda.imageio import hwc_to_chw, chw_to_hwc


class Sample(AbstractSample):

    def __init__(self, doc, device=None, output_tensor=False, use_homography=False):
        if isinstance(device, torch.device):
            self.device = device
        else:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.output_tensor = output_tensor
        super().__init__(doc, use_homography=use_homography)

    def _handle_image(self, image):
        if not isinstance(image, torch.Tensor):
            image = torch.from_numpy(image)
        
        if image.device != self.device:
            image = image.to(self.device)
        image = hwc_to_chw(image)

        return image

    def _handle_mask(self, mask):
        if isinstance(mask, torch.Tensor):
            if mask.device != self.device:
                mask = mask.to(self.device)
            return mask
        
        if isinstance(mask, bytes):
            mask = cv.imdecode(np.frombuffer(mask, np.byte), cv.IMREAD_GRAYSCALE)
        if not isinstance(mask, torch.Tensor):  
            mask = torch.from_numpy(mask)
        mask = mask.unsqueeze(0)
        if mask.device != self.device:
            mask = mask.to(self.device)
        return mask

    def _handle_bboxes(self, bboxes):
        if isinstance(bboxes, torch.Tensor):
            if bboxes.device != self.device:
                bboxes = bboxes.to(self.device)
            return bboxes

        return torch.tensor(bboxes).to(self.device)

    def _handle_heatmap(self, heatmap):
        if isinstance(heatmap, torch.Tensor):
            heatmap = torch.from_numpy(heatmap)
        if heatmap.device != self.device:
            heatmap = heatmap.to(self.device)
        heatmap = hwc_to_chw(heatmap)

        return heatmap

    def _handle_keypoints(self, keypoints):
        if isinstance(keypoints, torch.Tensor):
            if keypoints.device != self.device:
                keypoints = keypoints.to(self.device)
            return keypoints
        return torch.tensor(keypoints).to(self.device)

    def _out_image(self):
        if self.output_tensor:
            return chw_to_hwc(self.image)
        return chw_to_hwc(self.image).cpu().numpy()

    def _out_mask(self):
        if self.output_tensor:
            return self.mask.squeeze(0).to(torch.uint8)
        return self.mask.squeeze(0).to(torch.uint8).cpu().numpy()

    def _out_bboxes(self):
        if self.output_tensor:
            return self.bboxes
        return self.bboxes.cpu().numpy()

    def _out_heatmap(self):
        if self.output_tensor:
            return chw_to_hwc(self.heatmap)
        return chw_to_hwc(self.heatmap).cpu().numpy()

    def _out_keypoints(self):
        if self.output_tensor:
            return self.keypoints
        return self.keypoints.cpu().numpy()
