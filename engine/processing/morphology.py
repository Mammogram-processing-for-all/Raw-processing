"""배경 제거 / 모폴로지 (Background / Morphology)."""

from __future__ import annotations

import cv2
import numpy as np


def top_hat_filter(img: np.ndarray, ksize: int = 15) -> np.ndarray:
    """탑햇 필터 — 배경 제거 및 밝은 미세 구조 강조."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    return cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)


def remove_background(img: np.ndarray, thresh_val: int = 5) -> np.ndarray:
    """가장 큰 외곽 컨투어(유방 영역) 외부를 제거.

    입력은 float [0, 1] 또는 uint8. uint8 마스킹 결과를 반환한다.
    """
    if img.dtype != np.uint8:
        img_u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    else:
        img_u8 = img

    _, thresh = cv2.threshold(img_u8, thresh_val, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img_u8

    largest = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(img_u8)
    cv2.drawContours(mask, [largest], -1, 255, thickness=cv2.FILLED)
    return cv2.bitwise_and(img_u8, img_u8, mask=mask)
