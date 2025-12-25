#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2024-03-12
"""
from typing import Optional, List, Dict

import numpy as np


def easyocr(image: np.ndarray, lang: str = 'ch_sim'):
    try:
        import easyocr
    except ImportError:
        raise RuntimeError(
            'The OCR module requires "easyocr" package. '
            'You should install it by "pip install easyocr".'
        )

    reader = easyocr.Reader([lang], gpu=False)
    result = reader.readtext(image)

    ocr_out = []
    for item in result:
        ocr_out.append({
            "text": item[1],
            "text_score": item[2],
            "position": item[0],
        })

    return ocr_out


def cnocr(
        image,
        rec_root: Optional[str] = None,
        det_root: Optional[str] = None,
        rec_model_name: Optional[str] = "densenet_lite_136-gru",
        det_model_name: Optional[str] = "ch_PP-OCRv3_det"
) -> List[Dict]:
    try:
        from cnocr import CnOcr
        from cnocr.utils import data_dir
        from cnstd.utils import data_dir as det_data_dir
    except ImportError:
        raise RuntimeError(
            'The OCR module requires "cnocr" package. '
            'You should install it by "pip install cnocr[ort-gpu]".'
        )

    rec_root = rec_root or data_dir()
    det_root = det_root or det_data_dir()

    reader = CnOcr(
        rec_root=rec_root,
        det_root=det_root,
        rec_model_name=rec_model_name,
        det_model_name=det_model_name,
    )
    result = reader.ocr(image)

    ocr_out = []
    for item in result:
        ocr_out.append({
            "text": item['text'],
            "text_score": item['score'],
            "position": item["position"].astype(int).tolist(),
        })
    return ocr_out


def ocr(backend, *args, **kwargs):
    if backend == 'easyocr':
        return easyocr(*args, **kwargs)
    elif backend == 'cnocr':
        return cnocr(*args, **kwargs)
    else:
        raise ValueError(f"Unsupported backend: {backend}")
