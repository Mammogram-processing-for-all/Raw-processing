"""LUT (Look-Up Table) — 톤 매핑 및 표시용 변환."""

from __future__ import annotations

import numpy as np


def make_lut(
    mapping_func,
    input_dtype=np.uint16,
    output_dtype=np.uint8,
) -> np.ndarray:
    """매핑 함수로부터 LUT 배열을 생성. apply_lut 과 함께 사용."""
    input_range = np.arange(0, np.iinfo(input_dtype).max + 1)
    mapped = mapping_func(input_range)
    return np.clip(mapped, 0, 255).astype(output_dtype)


def apply_lut(image: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """LUT 적용 (인덱싱). image 의 값으로 lut 을 인덱싱한다."""
    return lut[image]


def create_window_lut(
    center: float, width: float, depth: int = 4096, inverse: bool = True
) -> np.ndarray:
    """DICOM Window Center/Width 기반 LUT 생성.

    inverse=True 면 MONOCHROME1 (값이 클수록 어둡게)로 반전한다.
    depth 비트 깊이(기본 12-bit, 4096) 만큼의 uint8 LUT 을 반환.
    """
    idx = np.arange(depth, dtype=np.float32)
    value = (idx - (center - 0.5)) / (width - 1) + 0.5
    value = np.clip(value, 0.0, 1.0)
    if inverse:
        value = 1.0 - value
    return (value * 255).astype(np.uint8)


# --- 매핑 함수들 (make_lut 의 mapping_func 인자로 사용) ---
def log_lut(x: np.ndarray) -> np.ndarray:
    """로그 매핑 — 다이내믹 레인지 압축."""
    x = np.log1p(x.astype(np.float32))
    return (x / x.max()) * 255


def gamma_lut(x: np.ndarray, gamma: float = 0.8) -> np.ndarray:
    """감마 매핑. gamma<1 → 어두운 영역을, gamma>1 → 밝은 영역을 강조."""
    x = x.astype(np.float32) / x.max()
    return np.power(x, gamma) * 255


def sigmoid_lut(x: np.ndarray, alpha: float = 10, beta: float = 0.5) -> np.ndarray:
    """시그모이드 매핑 — 중간 톤 대비 강화."""
    x = x.astype(np.float32) / x.max()
    return 1 / (1 + np.exp(-alpha * (x - beta))) * 255


def hologic_style_lut(x: np.ndarray, gamma: float = 0.8) -> np.ndarray:
    """Hologic 스타일: 로그 + 감마."""
    x = np.log1p(x.astype(np.float32))
    x = x / x.max()
    return np.power(x, gamma) * 255


def siemens_style_lut(x: np.ndarray, alpha: float = 12) -> np.ndarray:
    """Siemens 스타일: 로그 + 시그모이드."""
    x = np.log1p(x.astype(np.float32)) / np.log1p(np.max(x))
    return 1 / (1 + np.exp(-alpha * (x - 0.5))) * 255
