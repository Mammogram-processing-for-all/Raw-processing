"""로그 반전 (Log Inversion) — MONOCHROME2 → MONOCHROME1.

파이프라인의 시작점. 원시 디텍터 영상을 필름 형태의 영상으로 변환한다.
"""

from __future__ import annotations

import cv2
import numpy as np


def sigmoid_contrast(
    img: np.ndarray, alpha: float = 15.0, beta: float = 0.3
) -> np.ndarray:
    """시그모이드 대비 곡선. 입력/출력 float [0, 1].

    alpha: 곡선 기울기(대비 강도), beta: 중심점(낮추면 영상이 밝아짐).
    """
    out = 1.0 / (1.0 + np.exp(-alpha * (img - beta)))
    return cv2.normalize(out, None, 0, 1, cv2.NORM_MINMAX)


def log_inversion(
    raw_array: np.ndarray,
    clip_percent: float = 0.90,
    apply_sigmoid: bool = True,
    alpha: float = 15.0,
    beta: float = 0.3,
    eps: float = 1e-3,
) -> np.ndarray:
    """원시 MONOCHROME2 영상을 필름 형태의 MONOCHROME1 영상으로 변환.

    디텍터에 도달한 X선이 많을수록(픽셀값이 클수록) 투과 경로의 조직이
    얇다는 의미이므로, 로그 반전으로 '두껍고 고밀도인 조직 = 밝게' 인
    필름 관례(MONOCHROME1)로 뒤집는다.

    단계: 상위 클리핑(Direct beam 제거) → 0~1 정규화 → -log 반전 →
    (선택) 시그모이드 대비 곡선. float32 [0, 1] 반환.
    """
    img = raw_array.astype(np.float32)

    # 1. 상위 퍼센타일 클리핑 — 공기에 직접 노출된 Direct beam 영역 제거
    clip_val = float(np.percentile(img, clip_percent * 100))
    img = np.clip(img, 0, clip_val) / (clip_val + eps)

    # 2. 로그 반전 — 신호가 클수록 어둡게 (MONOCHROME2 → MONOCHROME1)
    img_log = -np.log(img + eps)
    img_log = cv2.normalize(img_log, None, 0, 1, cv2.NORM_MINMAX)

    # 3. (선택) 시그모이드 대비 곡선 — 연산 단순화 및 중간 톤 강조
    if apply_sigmoid:
        return sigmoid_contrast(img_log, alpha=alpha, beta=beta)
    return img_log
