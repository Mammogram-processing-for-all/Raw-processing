"""대비 강화 (Contrast Enhancement)."""

from __future__ import annotations

import cv2
import numpy as np


def apply_clahe(
    img: np.ndarray, clip_limit: float = 2.0, tile_grid_size: int = 8
) -> np.ndarray:
    """CLAHE (지역 대비 강화). uint8 입력 권장."""
    clahe = cv2.createCLAHE(
        clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size)
    )
    return clahe.apply(img)


def histogram_equalization(img: np.ndarray) -> np.ndarray:
    """전역 히스토그램 평활화 (대비 강화). uint8 입력."""
    return cv2.equalizeHist(img)
