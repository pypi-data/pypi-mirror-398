"""MareArts ANPR - License Plate Detection and Recognition"""

from ._version import __version__

from .marearts_anpr import (
    marearts_anpr_from_pil,
    marearts_anpr_from_image_file, 
    marearts_anpr_from_cv2
)

from .marearts_anpr_d import ma_anpr_detector
from .marearts_anpr_d_v14 import ma_anpr_detector_v14
from .marearts_anpr_r import ma_anpr_ocr
from .marearts_anpr_r_v14 import ma_anpr_ocr_v14
from .marearts_anpr_p import validate_user_key, validate_user_key_with_signature, download_anpr_ocr_v14_model

__all__ = [
    "__version__",
    "marearts_anpr_from_pil",
    "marearts_anpr_from_image_file",
    "marearts_anpr_from_cv2",
    "ma_anpr_detector",
    "ma_anpr_detector_v14",
    "ma_anpr_ocr",
    "ma_anpr_ocr_v14",
    "validate_user_key",
    "validate_user_key_with_signature",
    "download_anpr_ocr_v14_model"
]
