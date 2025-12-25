#!/usr/bin/env python3

from ast import literal_eval
from importlib import import_module
from typing import *

from imgaug import augmenters as iaa
import numpy as np

__all__ = [
    'DEFAULT_IMAGE_FIELD',
    'DEFAULT_BBOX_FIELD',
    'DEFAULT_MASK_FIELD',
    'DEFAULT_HEATMAP_FIELD',
    'DEFAULT_KEYPOINTS_FIELD',
    'DEFAULT_OCR_FIELD',
    'DEFAULT_LABEL_FIELD',
    'DEFAULT_QR_CODE_FIELD',
    'DEFAULT_DATA_MATRIX_CODE_FIELD',
    'AbstractSample',
    'eval_arg',
    'apply_augmenter',
    'AbstractTransform',
    'ImgaugAdapter',
]

DEFAULT_IMAGE_FIELD = 'image'
DEFAULT_BBOX_FIELD = 'bboxes'
DEFAULT_MASK_FIELD = 'mask'
DEFAULT_HEATMAP_FIELD = 'heatmap'
DEFAULT_KEYPOINTS_FIELD = 'keypoints'
DEFAULT_OCR_FIELD = 'ocr'
DEFAULT_LABEL_FIELD = 'label'
DEFAULT_QR_CODE_FIELD = 'qr_code'
DEFAULT_BAR_CODE_FIELD = 'bar_code'
DEFAULT_DATA_MATRIX_CODE_FIELD = 'data_matrix_code'
DEFAULT_COLOR_MEASURE_FIELD = 'color_measure'
DEFAULT_HOMOGRAPHY_FIELD = 'homography'


def eval_arg(value, type_):
    if isinstance(value, str):
        if type_ is None:
            try:
                return literal_eval(value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                raise ValueError()
        else:
            if isinstance(value, type_):
                return value
            return type_(value)
    elif type_ is not None and not isinstance(value, type_):
        return type_(value)
    else:
        return value


def apply_augmenter(
        sample,
        augmenter: iaa.Augmenter,
        attrs: List[str],
):
    if augmenter is None:
        return sample.output()

    if not isinstance(augmenter, iaa.Augmenter):
        raise RuntimeError('Invalid augmenter.')

    if sample.image is None:
        return sample.output()

    aug_args = sample.get_args(attrs)
    aug_result = augmenter(**aug_args)

    if len(aug_args) == 1:
        aug_result = [aug_result]
    sample.set_args(aug_result, aug_args.keys())

    return sample


class AbstractSample(object):

    def __init__(self, doc, use_homography=False):
        self.doc = doc
        self._image = None
        self._mask = None
        self._bboxes = None
        self._heatmap = None
        self._keypoints = None
        self._shape = None

        self.ocr = None
        self.qr_code = None
        self.bar_code = None
        self.data_matrix_code = None
        self.color_measure = None
        self.label = doc.get(DEFAULT_LABEL_FIELD)

        self.image_changed = False
        self.mask_changed = False
        self.bboxes_changed = False
        self.heatmap_changed = False
        self.keypoints_changed = False
        self.use_homography = use_homography
        self.transform_matrix = np.eye(3)       # 累积变换矩阵
        # self.inv_transform_matrix = np.eye(3)   # 累积逆变换矩阵

    @property
    def image(self):
        if self._image is not None:
            return self._image

        image_field = self.doc.get(DEFAULT_IMAGE_FIELD)
        if image_field is not None:
            self.image_changed = True
            self._image = self._handle_image(image_field)

        return self._image

    @image.setter
    def image(self, value):
        self._image = value

    @property
    def mask(self):
        if self._mask is not None:
            return self._mask

        mask_field = self.doc.get(DEFAULT_MASK_FIELD)
        if mask_field is not None:
            self.mask_changed = True
            self._mask = self._handle_mask(mask_field)

        return self._mask

    @mask.setter
    def mask(self, value):
        self._mask = value

    @property
    def bboxes(self):
        if self._bboxes is not None:
            return self._bboxes

        bboxes_field = self.doc.get(DEFAULT_BBOX_FIELD)
        if bboxes_field is not None:
            self.bboxes_changed = True
            self._bboxes = self._handle_bboxes(bboxes_field)

        return self._bboxes

    @bboxes.setter
    def bboxes(self, value):
        self._bboxes = value

    @property
    def heatmap(self):
        if self._heatmap is not None:
            return self._heatmap

        heatmap_field = self.doc.get(DEFAULT_HEATMAP_FIELD)
        if heatmap_field is not None:
            self.heatmap_changed = True
            self._heatmap = self._handle_heatmap(heatmap_field)

        return self._heatmap

    @heatmap.setter
    def heatmap(self, value):
        self._heatmap = value

    @property
    def keypoints(self):
        if self._keypoints is not None:
            return self._keypoints

        keypoints_field = self.doc.get(DEFAULT_KEYPOINTS_FIELD)
        if keypoints_field is not None:
            self.keypoints_changed = True
            self._keypoints = self._handle_keypoints(keypoints_field)

        return self._keypoints

    @keypoints.setter
    def keypoints(self, value):
        self._keypoints = value

    @property
    def shape(self):
        self._shape = self.image.shape
        return self._shape

    def _handle_image(self, image):
        ...

    def _handle_mask(self, mask):
        ...

    def _handle_bboxes(self, bboxes):
        ...

    def _handle_heatmap(self, heatmap):
        ...

    def _handle_keypoints(self, keypoints):
        ...

    def _out_image(self):
        ...

    def _out_mask(self):
        ...

    def _out_bboxes(self):
        ...

    def _out_heatmap(self):
        ...

    def _out_keypoints(self):
        ...

    def output(self):

        if self.image_changed:
            self.doc[DEFAULT_IMAGE_FIELD] = self._out_image()

        if self.mask_changed:
            self.doc[DEFAULT_MASK_FIELD] = self._out_mask()

        if self.bboxes_changed:
            self.doc[DEFAULT_BBOX_FIELD] = self._out_bboxes()

        if self.heatmap_changed:
            self.doc[DEFAULT_HEATMAP_FIELD] = self._out_heatmap()

        if self.keypoints_changed:
            self.doc[DEFAULT_KEYPOINTS_FIELD] = self._out_keypoints()

        if self.ocr is not None:
            self.doc[DEFAULT_OCR_FIELD] = self.ocr

        if self.label is not None:
            self.doc[DEFAULT_LABEL_FIELD] = self.label

        if self.qr_code is not None:
            self.doc[DEFAULT_QR_CODE_FIELD] = self.qr_code

        if self.bar_code is not None:
            self.doc[DEFAULT_BAR_CODE_FIELD] = self.bar_code

        if self.data_matrix_code is not None:
            self.doc[DEFAULT_DATA_MATRIX_CODE_FIELD] = self.data_matrix_code

        if self.color_measure is not None:
            self.doc[DEFAULT_COLOR_MEASURE_FIELD] = self.color_measure
        if self.use_homography:
            self.doc[DEFAULT_HOMOGRAPHY_FIELD] = np.linalg.inv(self.transform_matrix)

        return self.doc


class AbstractTransform(object):

    def __init__(self, use_gpu=False):
        sample_module = "visioncube.operators_cuda" if use_gpu else "visioncube.operators"
        self._sample_type = getattr(import_module(sample_module), "Sample")
        self.matrix = np.eye(3)

    def __call__(self, doc: Union[MutableMapping, AbstractSample]) -> Union[MutableMapping, AbstractSample]:
        input_sample = doc
        need_convert = not isinstance(doc, self._sample_type)

        if need_convert:
            input_sample = self._sample_type(doc)
        
        input_shape = input_sample.shape
        output_sample = self._apply(input_sample)

        if output_sample.use_homography:
            self._update_transform(input_shape, output_sample)

        if need_convert:
            output_sample = output_sample.output()

        return output_sample

    def _apply(self, sample):
        return sample
    
    def _update_transform(self, input_shape, output_sample: AbstractSample):
        output_sample.transform_matrix = self.matrix @ output_sample.transform_matrix

class ImgaugAdapter(AbstractTransform):

    def __init__(self, augmenter: iaa.Augmenter, attrs):
        super().__init__(use_gpu=False)
        self.augmenter = augmenter
        self.attrs = attrs

    def _apply(self, sample):
        return apply_augmenter(sample, self.augmenter, self.attrs)
