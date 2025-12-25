#!/usr/bin/env python3

"""
@author: xi, liying50
"""

import math
from dataclasses import dataclass, field
from typing import *

import cv2 as cv
import numpy as np
from shapely.geometry import Point, Polygon
import torch
import torchvision

import visioncube as cube


@dataclass
class AlignmentOutput(object):
    """Alignment output base class
    """
    aligned_image: np.ndarray = field(default=None)
    homography: np.ndarray = field(default=None)
    confidence: float = field(default=None)
    train_pts: np.ndarray = field(default=None)
    query_pts: np.ndarray = field(default=None)


class AbstractAlignment(object):
    """Abstract alignment
    """

    def __call__(self, image: np.ndarray) -> AlignmentOutput:
        raise NotImplementedError()


class TemplateMatching(AbstractAlignment):
    """Template matching class
    """

    def __init__(
            self,
            template: np.ndarray,
            ignore_list: Sequence[Sequence],
            scale: Optional[float] = None,
            inter=cv.INTER_AREA,
            match_method=cv.TM_SQDIFF_NORMED   # cv.TM_CCOEFF_NORMED  #cv.TM_CCORR_NORMED
    ) -> None:
        self.template = template
        self.scale = scale
        self.inter = inter
        self.match_method = match_method

        self.template = self._pre_process(self.template)
        self.ignore_mask = self.generate_mask(ignore_list)

    def _pre_process(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            if image.shape[-1] != 3:
                raise ValueError(f'Invalid image shape {image.shape}.')
            image = cube.rgb_to_gray(image)
        elif len(image.shape) != 2:
            raise ValueError(f'Invalid image shape {image.shape}.')
        if self.scale is not None:
            image = cube.resize(image, width=self.scale, height=self.scale, interpolation=self.inter)
        return image

    def generate_mask(self, ignore_list: Sequence[Sequence]):
        mask = np.ones_like(self.template)
        for ignore_array in ignore_list:
            ignore_array = np.asarray(ignore_array, dtype=np.int64).reshape((-1, 2))
            cv.fillPoly(mask, [ignore_array], color=0)
            assert isinstance(ignore_array, np.ndarray)
            assert len(ignore_array.shape) == 2 and ignore_array.shape[1] == 2
        return mask

    def __call__(self, image: np.ndarray):
        image_gray = self._pre_process(image)
        res = cv.matchTemplate(image_gray, self.template, method=self.match_method, mask=self.ignore_mask)
        min_value, max_value, min_loc, max_loc = cv.minMaxLoc(res)
        if self.match_method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
            confidence = 1 - min_value
            x1, y1 = min_loc
        else:
            confidence = max_value
            x1, y1 = max_loc
        h, w = self.template.shape[:2]
        x2, y2 = x1 + w, y1 + h

        if self.scale is not None:
            x1 = int(x1 / self.scale)
            y1 = int(y1 / self.scale)
            x2 = int(x2 / self.scale)
            y2 = int(y2 / self.scale)

        y1 = min(max(0, y1), image.shape[0])
        y2 = min(max(0, y2), image.shape[0])
        x1 = min(max(0, x1), image.shape[1])
        x2 = min(max(0, x2), image.shape[1])

        # bbox = (x1, y1, x2, y2)
        matched = image[y1:y2, x1:x2, ...]

        return AlignmentOutput(
            aligned_image=matched,
            homography=np.array([
                [1, 0, x1],
                [0, 1, y1],
                [0, 0, 1]
            ], np.float32),
            confidence=confidence
        )


class RotateTemplateMatching(AbstractAlignment):
    """Template matching with angle
    """

    def __init__(
            self,
            train_image: np.ndarray,
            ignore_list: Sequence[Sequence],
            size=224,
            # num_angles=20,
            # n=18,
            degree=10,  # 正负旋转角度范围
            n = 5
    ):
        self.train_image = train_image
        self.size = size
        # self.num_angles = num_angles
        self.degree = degree
        self.n = n
        self.scale = None
        self.templates = []
        self._init_templates(ignore_list)

    def _init_templates(self, ignore_list):
        image = cube.rgb_to_gray(self.train_image) if len(self.train_image.shape) != 2 else self.train_image

        h, w = image.shape[:2]
        self.scale = self.size / ((h * h + w * w) ** 0.5)

        mask = np.ones((*image.shape[:2], 1), dtype=np.uint8)
        image = cube.resize(image, width=self.scale, height=self.scale, interpolation='area')
        mask = cv.resize(mask, None, fx=self.scale, fy=self.scale, interpolation=cv.INTER_AREA)
        self.scale = image.shape[0] / h

        for ignore_array in ignore_list:
            ignore_array = np.asarray(ignore_array, dtype=np.int64).reshape((-1, 2))
            cv.fillPoly(mask, [ignore_array], color=0)
            assert isinstance(ignore_array, np.ndarray)
            assert len(ignore_array.shape) == 2 and ignore_array.shape[1] == 2

        # image = np.concatenate([image, 255 * np.ones((*image.shape[:2], 1), dtype=np.uint8)], -1)
        # image = iaa.CenterPadToFixedSize(self.size, self.size)(image=image)
        # mask = iaa.CenterPadToFixedSize(self.size, self.size)(image=mask)
        image = cube.pad_to_square(image, self.size)
        mask = cube.pad_to_square(mask, self.size)

        # num_angles = self.num_angles * self.n
        # for i in range(num_angles):
        #     self.templates.append((
        #         cube.rotate(image, i * 360 / num_angles, cval=0),  # template
        #         cube.rotate(mask, i * 360 / num_angles, cval=0),  # mask
        #         i  # angle index
        #     ))

        for i in range(-self.degree, self.degree + 1):
            self.templates.append((
                cube.rotate(image, i, cval=0),  # template
                cube.rotate(mask, i, cval=0),  # mask
                i  # angle
            ))

    def _match(self, image_gray, start, end, step):
        matches = []
        for i in range(start, end, step):
            template, mask, _ = self.templates[i]
            res = cv.matchTemplate(image_gray, template, cv.TM_CCOEFF, mask=mask)
            _, confidence, _, max_loc = cv.minMaxLoc(res)
            x1, y1 = max_loc
            matches.append((
                confidence,
                (x1, y1),
                i
            ))
        return max(matches, key=lambda _m: _m[0])

    def __call__(self, query_image):
        query_h, query_w = query_image.shape[:2]
        query_image = cube.pad_to_square(query_image, max(query_h, query_w) * 2)
        padded_query_h, padded_query_w = query_image.shape[:2]
        image_gray = cube.rgb_to_gray(query_image)
        image_gray = cube.resize(image_gray, width=self.scale, height=self.scale, interpolation='area')
        self.scale = image_gray.shape[0] / query_image.shape[0]
        # i = self._match(image_gray, 0, len(self.templates), self.n)[-1]  # 在resize之后的图像上去匹配
        _idx = self._match(image_gray, 0, len(self.templates) - 1, self.n)[-1]  # 在resize之后的图像上去匹配
        confidence, (x1, y1), _idx = self._match(image_gray, _idx - self.n - 1, _idx + self.n, 1)  # (x1, y1)相对于resize之后图像的坐标
        tx = x1 / self.scale - (padded_query_w - query_w) / 2
        ty = y1 / self.scale - (padded_query_h - query_h) / 2  # 相对于原图的坐标
        translate1 = np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ])

        x1, y1 = int(x1 / self.scale), int(y1 / self.scale)  # (x1, y1)相对于原图的坐标
        x2 = x1 + int(self.templates[0][0].shape[1] / self.scale)
        y2 = y1 + int(self.templates[0][0].shape[0] / self.scale)

        # image_ = cube.rotate(query_image[y1:y2, x1:x2], -i * 360 / (self.num_angles * self.n))  # 裁剪匹配到的部分并旋转
        i = _idx - self.degree
        image_ = cube.rotate(query_image[y1:y2, x1:x2], -i)  # 裁剪匹配到的部分并旋转
        rotated_img_h, rotated_img_w = image_.shape[:2]
        c_x = rotated_img_w / 2
        c_y = rotated_img_h / 2
        # theta = i * np.pi * 2 / (self.num_angles * self.n)
        theta = i * np.pi * 2 / 360
        rotate = np.array([
            [math.cos(theta), -math.sin(theta), (1 - math.cos(theta)) * c_x + math.sin(theta) * c_y],
            [math.sin(theta), math.cos(theta), (1 - math.cos(theta)) * c_y - math.sin(theta) * c_x],
            [0, 0, 1]
        ])
        image_ = cube.crop_to_fix_size(image_, width=self.train_image.shape[1], height=self.train_image.shape[0])
        cropped_img_h, cropped_img_w = image_.shape[:2]
        translate2 = np.array([
            [1, 0, (rotated_img_w - cropped_img_w) / 2],
            [0, 1, (rotated_img_h - cropped_img_h) / 2],
            [0, 0, 1]
        ])
        return AlignmentOutput(
            aligned_image=image_,
            homography=translate1 @ rotate @ translate2,
            confidence=confidence
        )


class FeatureBasedAlignment(AbstractAlignment):
    """Image alignment class
    """

    def __init__(
            self,
            train_image: np.ndarray,
            ignore_list: Sequence[Sequence],
            use_grayscale=False,
            bilateral_filter=(3, 50),
            feature_type: str = 'orb',
            use_bf_matcher=False,
            cross_check=True,
            reproj_threshold=3.0,
            use_translate=True,
            use_rotate=True,
            use_scale=True
    ):
        self.train_image = train_image
        self.use_grayscale = use_grayscale
        self.bilateral_filter = bilateral_filter
        self.desc_type = feature_type
        self.use_bf_matcher = use_bf_matcher
        self.cross_check = cross_check
        self.reproj_threshold = reproj_threshold
        self.use_translate = use_translate
        self.use_rotate = use_rotate
        self.use_scale = use_scale
        self.ignore_list = ignore_list

        self.feature_extractor = self._create_feature_extractor()
        self.matcher = self._create_matcher()

        self.train_image = self._prepare_for_align(self.train_image)
        self.train_kps, self.train_descs = self._extract_features(image=self.train_image)

    def _create_feature_extractor(self):
        if self.desc_type == 'sift' and hasattr(cv, 'SIFT_create'):
            ret = cv.SIFT_create(10000)
        elif self.desc_type == 'orb' and hasattr(cv, 'ORB_create'):
            ret = cv.ORB_create(5000)
            ret.setFastThreshold(0)
        elif self.desc_type == 'brisk' and hasattr(cv, 'BRISK_create'):
            ret = cv.BRISK_create()
        elif self.desc_type == 'aka' and hasattr(cv, 'AKAZE_create'):
            ret = cv.AKAZE_create()
        else:
            raise RuntimeError(f'Invalid descriptors extractor {self.desc_type}.')
        return ret

    def _create_matcher(self):
        if self.use_bf_matcher:
            return cv.BFMatcher(
                normType=cv.NORM_L2 if self.desc_type == 'sift' else cv.NORM_HAMMING,
                crossCheck=self.cross_check
            )
        else:
            FLANN_INDEX_KDTREE = 1
            FLANN_INDEX_LSH = 6
            index_params = dict(
                algorithm=FLANN_INDEX_LSH,
                table_number=6,
                key_size=12,
                multi_probe_level=1,
            ) if self.desc_type != 'sift' else dict(
                algorithm=FLANN_INDEX_KDTREE,
                trees=5
            )
            search_params = dict(checks=50)
            return cv.FlannBasedMatcher(index_params, search_params)

    def _prepare_for_align(self, image: np.ndarray):
        if self.use_grayscale:
            image = cube.rgb_to_gray(image)
        return image

    def _extract_features(self, image):
        return self.feature_extractor.detectAndCompute(image=image, mask=None)

    def __call__(self, image: np.ndarray) -> AlignmentOutput:
        query_image = self._prepare_for_align(image)
        train_image = self.train_image

        # query_h, query_w = query_image.shape[:2]
        train_h, train_w = train_image.shape[:2]

        query_kps, query_descs = self._extract_features(image=query_image)
        train_kps, train_descs = self.train_kps, self.train_descs

        matches = self.matcher.match(query_descs, train_descs)

        matches = cv.xfeatures2d.matchGMS(
            query_image.shape[:2],
            train_image.shape[:2],
            query_kps,
            train_kps,
            matches,
            withScale=True,
            withRotation=True,
            thresholdFactor=9,
        )

        good_match_len = min(int(len(matches) * 0.4), 10000)
        matches = sorted(matches, key=lambda _m: _m.distance)[:good_match_len]
        query_pts = np.array([query_kps[m.queryIdx].pt for m in matches], dtype=np.float32)
        train_pts = np.array([train_kps[m.trainIdx].pt for m in matches], dtype=np.float32)

        for ignore_array in self.ignore_list:
            polygon = Polygon(ignore_array)
            for i in range(len(query_pts) - 1, 0, -1):
                if polygon.contains(Point(query_pts[i])):
                    query_pts = np.delete(query_pts, i, axis=0)
                    train_pts = np.delete(train_pts, i, axis=0)

        mat = estimate_homography(
            query_pts=query_pts,
            train_pts=train_pts,
            allow_translate=self.use_translate,
            allow_rotate=self.use_rotate,
            allow_scale=self.use_scale,
            reproj_threshold=self.reproj_threshold
        )
        aligned_image = cv.warpAffine(image, mat[:2, :], (train_w, train_h), borderMode=cv.BORDER_REPLICATE)

        train_pts = train_pts.astype(np.int32)
        query_pts = query_pts.astype(np.int32)

        return AlignmentOutput(
            aligned_image=aligned_image,
            homography=np.linalg.inv(mat) if np.linalg.det(mat) != 0 else -mat,
            confidence=0,
            train_pts=train_pts,
            query_pts=query_pts
        )


def estimate_homography(
        query_pts: np.ndarray,
        train_pts: np.ndarray,
        allow_translate: bool = True,
        allow_rotate: bool = True,
        allow_scale: bool = True,
        reproj_threshold: float = None
) -> np.ndarray:
    mat, _ = cv.estimateAffinePartial2D(query_pts, train_pts, ransacReprojThreshold=reproj_threshold)

    translate = np.array([
        [1, 0, mat[0, -1]],
        [0, 1, mat[1, -1]],
        [0, 0, 1],
    ])
    theta = math.atan2(mat[1, 0], mat[0, 0])
    rotate = np.array([
        [math.cos(theta), -math.sin(theta), 0],
        [math.sin(theta), math.cos(theta), 0],
        [0, 0, 1],
    ])
    scale = np.array([
        [math.sqrt(mat[0, 0] ** 2 + mat[1, 0] ** 2), 0, 0],
        [0, math.sqrt(mat[0, 1] ** 2 + mat[1, 1] ** 2), 0],
        [0, 0, 1],
    ])

    new_mat = np.eye(3, dtype=np.float32)
    if allow_translate:
        new_mat = new_mat @ translate
    if allow_rotate:
        new_mat = new_mat @ rotate
    if allow_scale:
        new_mat = new_mat @ scale
    return new_mat


def compute_corners_on_train(
        query_image: np.ndarray,
        homography: np.ndarray
) -> np.ndarray:
    h, w = query_image.shape[:2]
    corners = np.array([
        [0, 0, 1],
        [w, 0, 1],
        [w, h, 1],
        [0, h, 1]
    ], np.float32)
    corners = corners @ homography[:2, :].T
    corners = np.floor(corners + 0.5).astype(np.int64)
    return corners


def compute_corners_on_query(
        aligned_image: np.ndarray,
        homography: np.ndarray,
        homography_inv: np.ndarray = None
) -> np.ndarray:
    h, w = aligned_image.shape[:2]
    if homography_inv is None:
        homography_inv = np.linalg.inv(homography)
    corners = np.array([
        [0, 0, 1],
        [w, 0, 1],
        [w, h, 1],
        [0, h, 1]
    ], np.float32)
    corners = corners @ homography_inv[:2, :].T
    corners = np.floor(corners + 0.5).astype(np.int64)
    return corners


def restore_image(
        aligned_image: np.ndarray,
        homography: np.ndarray,
        image: np.ndarray
) -> np.ndarray:
    img_h, img_w = image.shape[:2]
    mask = np.zeros_like(aligned_image)
    warp_aligned_image = cv.warpPerspective(aligned_image, homography, (img_w, img_h))
    warp_mask = cv.warpPerspective(mask, homography, (img_w, img_h), borderValue=(1, 1, 1))
    return image * warp_mask + warp_aligned_image


def coord_transform(
        pts: List[List[int]],
        homography: np.ndarray,
) -> List[List[int]]:
    pts = np.float32([pts])
    dst_pts = cv.perspectiveTransform(pts, homography)[0]
    return dst_pts.astype(int)


@dataclass
class LocalizationConfig:
    roi_list: Sequence[Sequence] = field(default_factory=list)  # [[(x1, y1), (x2, y2)], ...]
    target_list: Sequence[str] = field(default_factory=list)
    ignore_list: Sequence[Sequence] = field(default_factory=list)  # [[(x1, y1), (x2, y2), ...], ...]
    match_ignore_list: Sequence[Sequence] = field(default_factory=list)  # [[(x1, y1), (x2, y2), ...], ...]
    focus_list: Sequence[Sequence] = field(default_factory=list)  # [[(x1, y1), (x2, y2), ...], ...]
    template_size: int = field(default=224)  # only used when RotateTemplateMatching is utilized
    allow_rotate: bool = field(default=False)
    allow_scale: bool = field(default=False)
    degree: int = field(default=30)  # 旋转角度, (0-180°)
    multiple: bool = field(default=False)  # 一个候选区内是否有多个目标,当其为True时,threshold和expand_ratio可调
    threshold: float = field(default=0.5)  # 判断是否是目标的阈值, (0-1)
    expand_ratio: float = field(default=0.2)  # 目标扩充率, (0-1)
    nms_threshold: float = field(default=0.5) # 目标扩充之后根据iou进行过滤的阈值, (0-1)


@dataclass
class LocalizationOutput(object):
    """Localization output base class
    """
    crop: np.ndarray = field(default=None)  # 图像
    roi: np.ndarray = field(default=None)  # 坐标点
    homography: np.ndarray = field(default=None)


class Localization:
    """Localization
    """

    def __init__(self, config: LocalizationConfig):
        self.config = config

        self.roi_list = []
        for bbox in self.config.roi_list:
            try:
                bbox_np = np.asarray(bbox, dtype=np.int64).reshape((2, 2))
            except:
                raise ValueError(f'Invalid ROI definition {bbox}.')
            self.roi_list.append(bbox_np)

        self.target_list = [
            cube.read_image(image_or_path, grayscale=True)
            for image_or_path in self.config.target_list
        ]
        self.template_list = self.target_list.copy()

        self.ignore_list = []
        for poly in self.config.ignore_list:
            try:
                poly_np = np.asarray(poly, dtype=np.int64).reshape((-1, 2))
            except:
                raise ValueError(f'Invalid "ignore area" definition {poly}.')
            self.ignore_list.append(poly_np)

        self.focus_list = []
        for poly in self.config.focus_list:
            poly_np = np.asarray(poly, dtype=np.int64)
            if len(poly_np.shape) != 2 or poly_np.shape[-1] != 2:
                raise ValueError(f'Invalid "focus area" definition {poly}.')
            self.focus_list.append(poly_np)

        if self.config.allow_rotate:
            if len(self.target_list) > 1:
                raise RuntimeError('There should be only one template image when `rotate` or `scale` enabled.')
            if self.config.allow_scale:
                self.target_list: List[AbstractAlignment] = [
                    FeatureBasedAlignment(
                        target,
                        config.match_ignore_list,
                        use_rotate=self.config.allow_rotate,
                        use_scale=self.config.allow_scale
                    )
                    for target in self.target_list
                ]
            else:
                self.target_list: List[AbstractAlignment] = [
                    RotateTemplateMatching(
                        target,
                        config.match_ignore_list,
                        size=self.config.template_size,
                        degree=self.config.degree
                    )
                    for target in self.target_list
                ]
        else:
            self.target_list: List[AbstractAlignment] = [
                TemplateMatching(target, config.match_ignore_list)
                for target in self.target_list
            ]

    def _crop_from_roi(self, image: np.ndarray, roi_coord: Optional[np.ndarray] = None) -> LocalizationOutput:
        if roi_coord is not None:
            x1, y1, x2, y2 = roi_coord.ravel().tolist()
            y1 = min(max(0, y1), image.shape[0])
            y2 = min(max(0, y2), image.shape[0])
            x1 = min(max(0, x1), image.shape[1])
            x2 = min(max(0, x2), image.shape[1])
            # if y2 < y1:
            #     y1, y2 = y2, y1
            # if x2 < x1:
            #     x1, x2 = x2, x1
            y1, y2 = min(y1, y2), max(y1, y2)
            x1, x2 = min(x1, x2), max(x1, x2)
            roi = image[y1:y2, x1:x2, ...]
        else:
            x1, y1 = 0, 0
            # y2, x2 = image.shape[:2]
            roi = image

        result = LocalizationOutput()
        if len(self.target_list) == 0:  # 没有得到匹配结果
            result.crop = roi
            result.homography = np.array([
                [1, 0, x1],
                [0, 1, y1],
                [0, 0, 1]
            ], np.float32)
        else:
            output_list = [target(roi) for target in self.target_list]
            output = max(output_list, key=lambda _output: _output.confidence)
            result.crop = output.aligned_image
            result.homography = output.homography
            result.homography[0, 2] += x1
            result.homography[1, 2] += y1
        pts = [
            [0, 0],
            [0, result.crop.shape[0]],
            [result.crop.shape[1], result.crop.shape[0]],
            [result.crop.shape[1], 0]
        ]

        result.roi = coord_transform(pts, result.homography)
        result.crop = self.masking_image(result.crop, self.ignore_list, self.focus_list)
        if len(self.focus_list) == 1:  # 当仅有1个保留区时, 把保留区外接矩形的图像内容crop出来
            poly = self.focus_list[0]
            poly_x1, poly_x2 = np.min(poly[:, 0]), np.max(poly[:, 0])
            poly_y1, poly_y2 = np.min(poly[:, 1]), np.max(poly[:, 1])
            result.homography[0, 2] += poly_x1
            result.homography[1, 2] += poly_y1
            result.crop = result.crop[poly_y1: poly_y2, poly_x1: poly_x2]
        return result

    @staticmethod
    def masking_image(
            image: np.ndarray,
            ignore_list: List[np.ndarray],
            focus_list: List[np.ndarray]
    ) -> np.ndarray:
        masks = []

        if ignore_list is not None and len(ignore_list) > 0:
            mask_0 = np.ones(image.shape[:2], dtype=np.uint8)
            for poly in ignore_list:
                assert isinstance(poly, np.ndarray)
                assert len(poly.shape) == 2 and poly.shape[1] == 2
                cv.fillPoly(mask_0, [poly], color=0)
            masks.append(mask_0)

        if focus_list is not None and len(focus_list) > 0:
            mask_1 = np.zeros(image.shape[:2], dtype=np.uint8)
            for poly in focus_list:
                assert isinstance(poly, np.ndarray)
                assert len(poly.shape) == 2 and poly.shape[1] == 2
                cv.fillPoly(mask_1, [poly], color=1)
            masks.append(mask_1)

        if len(masks) == 0:
            return image
        else:
            mask = np.logical_and(masks[0], masks[1]) if len(masks) > 1 else masks[0]
            if len(image.shape) == 3:
                mask = np.stack([mask] * 3, axis=-1)
            return image * mask

    def multiple_target(self, image: np.ndarray):
        img_h, img_w, _ = image.shape
        image_gray = cube.rgb_to_gray(image)
        coords_list = []
        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        for idx, roi_coord in enumerate(self.roi_list):
            (x1, y1), (x2, y2) = roi_coord
            mask[y1:y2, x1:x2] = 1
            # template = self.template_list[idx]  # 灰度图  # 当单个候选区内有多个目标时，每个候选区内都需要提供模板
            template = self.template_list[0]  # 灰度图  # 当多个候选区内都有多个目标时，每个候选区内复用一个模板，默认目标相同
            t_h, t_w = template.shape
            res = cv.matchTemplate(image_gray * mask, template, cv.TM_CCOEFF_NORMED)
            mask[y1:y2, x1:x2] = 0
            location = np.where( res >= self.config.threshold) #(yx)
            bboxes = []
            scores = []
            _ratio = self.config.expand_ratio
            for pt in zip(*location[::-1]):  # pt是左上角坐标
                start_x = max(int(pt[0] - _ratio * t_w), 0)
                start_y = max(int(pt[1] - _ratio * t_h), 0)
                end_x = min(int(pt[0] + t_w + _ratio * t_w), img_w)
                end_y = min(int(pt[1] + t_h + _ratio * t_h), img_h)
                # start_x = max(int(pt[0] - _ratio * t_w), min(roi_coord[:, 0]))
                # start_y = max(int(pt[1] - _ratio * t_h), min(roi_coord[:, 1]))
                # end_x = min(int(pt[0] + t_w + _ratio * t_w), max(roi_coord[:, 0]))
                # end_y = min(int(pt[1] + t_h + _ratio * t_h), max(roi_coord[:, 1]))
                bboxes.append([start_x, start_y, end_x, end_y])
                scores.append(res[pt[1], pt[0]])
            if len(bboxes) > 0:
                tensor_bboxes = torch.from_numpy(np.array(bboxes, np.float32))
                _scores = torch.from_numpy(np.array(scores, np.float32))
                _index = torchvision.ops.nms(tensor_bboxes, _scores, iou_threshold=self.config.nms_threshold)
                coords_list.append(np.asarray(tensor_bboxes[_index], dtype=np.int64))
        return coords_list

    def __call__(self, image: np.ndarray) -> List[LocalizationOutput]:
        results = []
        if self.roi_list:
            if self.config.multiple:
                coords_list = self.multiple_target(image) # [np.array, ...]
                t_h, t_w = self.template_list[0].shape
                if coords_list:
                    for coords in coords_list:
                        for coord in coords:
                            if int(coord[3] - coord[1]) >= t_h and int(coord[2] - coord[0]) >= t_w:
                                try:
                                    results.append(self._crop_from_roi(image, coord))
                                except Exception as e:
                                    print(e)                           
            else:
                for roi_coord in self.roi_list:
                    results.append(self._crop_from_roi(image, roi_coord))
        else:
            results.append(self._crop_from_roi(image))
        return results
