#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-06-06
"""

from typing import Tuple, Optional

import numpy as np
import cv2
import paddleocr
from visioncube.common import AbstractTransform

__all__ = ["EasyOCR", "CnOCR", "PPOCR"]


class EasyOCR(AbstractTransform):

    def __init__(
        self, lang: str = "ch_sim", use_gpu=False, model_root: Optional[str] = None
    ) -> None:
        """EasyOCR, 字符识别, 识别

        Args:
            lang: Language codes, 识别语言, {"ch_sim", "en", "ko", "ja"}, "ch_sim"
            use_gpu: Whether to use gpu, 是否使用GPU, {True, False}, False
            model_root: model root path, 模型文件根目录, {}, None
        """
        super().__init__(use_gpu=False)

        try:
            import easyocr
        except ImportError:
            raise RuntimeError(
                'The OCR module requires "easyocr" package. '
                'You should install it by "pip install easyocr".'
            )

        def _reformat_input(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
            if len(image.shape) == 2:
                return np.tile(image[:, :, None], (1, 1, 3)), image
            elif len(image.shape) == 3:
                if image.shape[-1] == 1:
                    return np.tile(image, (1, 1, 3)), image[:, :, 0]
                elif image.shape[-1] == 3:
                    return image, np.mean(image, -1).astype(np.uint8)
            raise RuntimeError(f"Invalid image shape {image.shape}.")

        setattr(easyocr.easyocr, "reformat_input", _reformat_input)
        self.reader = easyocr.Reader(
            [lang], gpu=use_gpu, model_storage_directory=model_root
        )

    def _apply(self, sample):

        if sample.image is None:
            return sample

        result = self.reader.readtext(sample.image)

        ocr_out = []
        for item in result:
            ocr_out.append(
                {
                    "text": item[1],
                    "text_score": item[2],
                    "position": item[0],
                }
            )
        sample.ocr = ocr_out

        return sample


class CnOCR(AbstractTransform):

    def __init__(
        self,
        rec_root: Optional[str] = None,
        det_root: Optional[str] = None,
        rec_model_name: Optional[str] = "densenet_lite_136-gru",
        det_model_name: Optional[str] = "ch_PP-OCRv3_det",
        use_gpu: bool = False,
    ) -> None:
        """CnOCR, 光学字符识别, 识别

        Args:
            rec_root: Rec model root path, 识别模型文件根目录, {}, None
            det_root: Det model root path, 检测模型文件根目录, {}, None
            rec_model_name: Rec Model Name, 识别模型名称, {"densenet_lite_136-gru", "scene-densenet_lite_136-gru", "doc-densenet_lite_136-gru", "number-densenet_lite_136-fc", "ch_PP-OCRv3", "en_PP-OCRv3", "en_number_mobile_v2.0", "chinese_cht_PP-OCRv3"}, "densenet_lite_136-gru"
            det_model_name: Det Model Name, 检测模型名称, {"db_shufflenet_v2", "db_shufflenet_v2_small", "db_shufflenet_v2_tiny", "db_mobilenet_v3", "db_mobilenet_v3_small", "db_resnet34", "db_resnet18", "ch_PP-OCRv3_det", "ch_PP-OCRv2_det", "en_PP-OCRv3_det"}, "ch_PP-OCRv3_det"
            use_gpu: Whether to use gpu, 是否使用GPU, {True, False}, False
        """

        """
        det_model_name:
        - db_shufflenet_v2      : 简体中文、繁体英文、英文、数字
        - db_shufflenet_v2_small: 简体中文、繁体英文、英文、数字
        - db_shufflenet_v2_tiny : 简体中文、繁体英文、英文、数字
        - db_mobilenet_v3       : 简体中文、繁体英文、英文、数字
        - db_mobilenet_v3_small : 简体中文、繁体英文、英文、数字
        - db_resnet34           : 简体中文、繁体英文、英文、数字
        - db_resnet18           : 简体中文、繁体英文、英文、数字
        - ch_PP-OCRv3_det       : 简体中文、繁体英文、英文、数字
        - ch_PP-OCRv2_det       : 简体中文、繁体英文、英文、数字
        - en_PP-OCRv3_det       : 英文、数字
        - naive_det             : 排版简单的印刷体文件图片(速度快，对图片较挑剔)

        rec_model_name
        - densenet_lite_136-gru      : 简体中文、英文、数字
        - scene-densenet_lite_136-gru: 简体中文、英文、数字（场景图片，识别识别一般拍照图片中的文字）
        - doc-densenet_lite_136-gru  : 简体中文、英文、数字（文档图片，适合识别规则文档的截图图片）
        - number-densenet_lite_136-fc: 纯数字（仅包含 0~9 十个数字）
        - ch_PP-OCRv3                : 简体中文、英文、数字
        - ch_ppocr_mobile_v2.0       : 简体中文、英文、数字
        - en_PP-OCRv3                : 英文、数字
        - en_number_mobile_v2.0      : 英文、数字
        - chinese_cht_PP-OCRv3       : 繁体中文、英文、数字

        """
        super().__init__(use_gpu=False)

        try:
            from cnocr import CnOcr
            from cnocr.utils import data_dir
            from cnstd.utils import data_dir as det_data_dir
        except ImportError:
            if use_gpu:
                raise RuntimeError(
                    'The OCR module requires "cnocr" package. '
                    'You should install it by "pip install cnocr[ort-gpu]==2.3".'
                )
            else:
                raise RuntimeError(
                    'The OCR module requires "cnocr" package. '
                    'You should install it by "pip install cnocr[ort-cpu]==2.3".'
                )

        rec_root = rec_root or data_dir()
        det_root = det_root or det_data_dir()

        self.reader = CnOcr(
            rec_root=rec_root,
            det_root=det_root,
            rec_model_name=rec_model_name,
            det_model_name=det_model_name,
        )

    def _apply(self, sample):

        if sample.image is None:
            return sample

        result = self.reader.ocr(sample.image)

        ocr_out = []
        for item in result:
            ocr_out.append(
                {
                    "text": item["text"],
                    "text_score": item["score"],
                    "position": item["position"].astype(int).tolist(),
                }
            )
        sample.ocr = ocr_out

        return sample


# Ce-OCR (PaddleOCR)
class PPOCR(AbstractTransform):
    def __init__(
        self,
        use_angle_cls: bool = False,
        lang: str = "en",
        det: bool = True,
        rec: bool = False,
        use_gpu: bool = True,
        del_limit_side_len: int = 20000,
        del_limit_type: str = "max",
        slice_horizontal_stride: int = 4000,
        slice_vertical_stride: int = 1550,
        slice_merge_x_thres: int = 2300,
        slice_merge_y_thres: int = 80,
    ) -> None:
        super().__init__(use_gpu=False)

        """PaddleOCR, 光学字符识别, 识别
        Args:
            use_angle_cls: 是否使用角度分类, {True, False}, False
            lang: 识别语言, {"en", "ch", ...}, "en"
            det: 是否进行文本检测, {True, False}, True
            rec: 是否进行文本识别, {True, False}, False
            use_gpu: 是否使用GPU, {True, False}, True
            det_limit_side_len: 检测限制边长, {}, 20000
            det_limit_type: 检测限制类型, {'max', 'min'}, 'max'
            slice_horizontal_stride: 切片的水平步长, {}, 4000
            slice_vertical_stride: 切片的垂直步长, {}, 1550
            slice_merge_x_thres: x方向合并阈值, {}, 2300
            slice_merge_y_thres: y方向合并阈值, {}, 80
      """
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.det = det
        self.rec = rec
        self.use_gpu = use_gpu
        self.del_limit_side_len = del_limit_side_len
        self.del_limit_type = del_limit_type

        self.reader = None

        self.slice = {
            "horizontal_stride": slice_horizontal_stride,
            "vertical_stride": slice_vertical_stride,
            "merge_x_thres": slice_merge_x_thres,
            "merge_y_thres": slice_merge_y_thres,
        }

    def _apply(self, sample):
        if sample.image is None:
            return sample

        img_new = sample.image
        self.reader = paddleocr.PaddleOCR(
            use_angle_cls=self.use_angle_cls,
            lang=self.lang,
            # det=self.det,
            # rec=self.rec,
            use_gpu=self.use_gpu,
            del_limit_side_len=self.del_limit_side_len,
            del_limit_type=self.del_limit_type,
        )
        results = self.reader.ocr(img_new, det=self.det, rec=self.rec, slice=self.slice)
        ocr_out = []

        if results and results[0] is not None:
            for item in results:
                if self.det:
                    # 为确保接口统一，当不调用识别接口时，text设置为空字符, text_score设置为0.0
                    for coord_res, text_res in (
                        item if self.rec else zip(item, [("", 0.0)] * len(item))
                    ):
                        coord_res_np = np.array(coord_res, dtype=np.float32)  # 检测结果
                        text_content, text_score = text_res  # 识别结果
                        ocr_out.append(
                            {
                                "text": text_content,
                                "text_score": text_score,
                                "position": coord_res_np.astype(int).tolist(),
                            }
                        )
            sample.ocr = ocr_out
        else:
            sample.ocr = []
            print("未检测到字符!")

        return sample


class OCR(AbstractTransform):

    def __init__(self, backend, *args, **kwargs):
        super().__init__(use_gpu=False)

        self.engine = None
        if backend == "easyocr":
            self.engine = EasyOCR(*args, **kwargs)
        elif backend == "cnocr":
            self.engine = CnOCR(*args, **kwargs)
        elif backend == "paddleocr":
            self.engine = PPOCR(*args, **kwargs)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def _apply(self, sample):
        return self.engine(sample)
