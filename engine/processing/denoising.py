"""노이즈 제거 (Denoising)."""

from __future__ import annotations

import cv2
import numpy as np


def denoise_gaussian(img: np.ndarray, ksize: int = 3, sigma: float = 0.5) -> np.ndarray:
    """가우시안 블러."""
    return cv2.GaussianBlur(img, (ksize, ksize), sigma)


def denoise_median(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """미디언 블러 (점잡음 제거)."""
    return cv2.medianBlur(img, ksize)
