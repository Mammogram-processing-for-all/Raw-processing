"""정규화 / 윈도잉 (Normalization / Windowing)."""

from __future__ import annotations

import cv2
import numpy as np


def window_contrast(
    img: np.ndarray, p_low: float = 5.0, p_high: float = 99.5
) -> np.ndarray:
    """퍼센타일 기반 대비 윈도잉. float32 [0, 1] 반환."""
    lo, hi = np.percentile(img, (p_low, p_high))
    return np.clip((img - lo) / (hi - lo + 1e-6), 0, 1).astype(np.float32)


def normalize(img: np.ndarray) -> np.ndarray:
    """min-max 정규화 후 uint8 [0, 255] 반환."""
    return cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def contrast_stretching(img: np.ndarray, use_percentile: bool = False) -> np.ndarray:
    """선형 대비 스트레칭. uint8 [0, 255] 반환.

    use_percentile=True 면 (2, 98) 퍼센타일을 양 끝으로 사용한다.
    """
    if use_percentile:
        min_val, max_val = np.percentile(img, (2, 98))
    else:
        min_val, max_val = float(np.min(img)), float(np.max(img))
    stretched = (img - min_val) * 255.0 / (max_val - min_val + 1e-6)
    return np.clip(stretched, 0, 255).astype(np.uint8)
