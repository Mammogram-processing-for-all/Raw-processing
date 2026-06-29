"""텍스처 / 엣지 강화 (Texture / Edge Enhancement)."""

from __future__ import annotations

import cv2
import numpy as np


def apply_gabor_filters(
    image: np.ndarray,
    ksize: int = 31,
    sigma: float = 5,
    gamma: float = 0.5,
    theta: float = 0,
    lambd: float = 10,
    psi: float = 0,
) -> np.ndarray:
    """Gabor 필터 — 미세석회화/혈관 등 텍스처 강조."""
    kernel = cv2.getGaborKernel(
        (ksize, ksize), sigma, theta, lambd, gamma, psi, ktype=cv2.CV_32F
    )
    return cv2.filter2D(image, cv2.CV_8UC3, kernel)


def combine_clahe_gabor(
    clahe_img: np.ndarray,
    gabor_img: np.ndarray,
    clahe_weight: float = 0.6,
    gabor_weight: float = 0.4,
) -> np.ndarray:
    """CLAHE 결과와 Gabor 결과를 가중 합성. float [0, 1] 반환."""
    clahe_norm = cv2.normalize(clahe_img.astype(np.float32), None, 0, 1, cv2.NORM_MINMAX)
    gabor_norm = cv2.normalize(gabor_img.astype(np.float32), None, 0, 1, cv2.NORM_MINMAX)
    return cv2.addWeighted(clahe_norm, clahe_weight, gabor_norm, gabor_weight, 0)


def unsharp_mask(
    img: np.ndarray,
    ksize: int = 5,
    sigma: float = 1.0,
    amount: float = 1.5,
) -> np.ndarray:
    """언샵 마스킹 — 엣지/선예도 강화."""
    blurred = cv2.GaussianBlur(img, (ksize, ksize), sigma)
    return cv2.addWeighted(img, amount, blurred, 1.0 - amount, 0)


def edge_enhancement(img: np.ndarray, strength: float = 0.5) -> np.ndarray:
    """라플라시안 엣지를 원본에 더해 경계를 강화."""
    edges = cv2.Laplacian(img, cv2.CV_64F)
    edges = cv2.convertScaleAbs(edges)
    return cv2.addWeighted(img, 1.0, edges, strength, 0)


def multi_frequency_decomposition(
    img: np.ndarray, sigma_list: list[int] | None = None
) -> list[np.ndarray]:
    """이미지를 여러 주파수 대역(밴드)으로 분해.

    sigma_list 길이만큼의 디테일 레이어 + 1개의 잔여 저주파 레이어를 반환한다.
    각 밴드 = (현재 영상) - (가우시안 블러).
    """
    if sigma_list is None:
        sigma_list = [1, 2, 4, 8]

    layers = []
    current = img.astype(np.float32)
    for sigma in sigma_list:
        blurred = cv2.GaussianBlur(current, (0, 0), sigmaX=sigma)
        layers.append(current - blurred)  # 디테일(고주파) 밴드
        current = blurred
    layers.append(current)  # 잔여 저주파 밴드
    return layers
