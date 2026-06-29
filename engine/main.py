"""영상처리 엔진 — 기본 파이프라인.

각 영상처리 함수는 ``processing`` 패키지에 주제별 모듈로 분리되어 있고,
여기서는 그것들을 조합하여 기본 처리 파이프라인을 구성한다.

파이프라인은 파라미터 딕셔너리(``params``)와 진행 콜백(``progress``)을 받아,
viewer 등 외부에서 파라미터 조정 및 진행률 표시에 활용할 수 있다.

입출력 규약
-----------
- RAW 적재: uint16 2D 배열 (height, width)
- 정규화/윈도잉/반전 결과: float32, 값 범위 [0, 1]
- 표시용 결과: uint8, 값 범위 [0, 255]
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from processing import (
    RAW_HEIGHT,
    RAW_WIDTH,
    apply_clahe,
    denoise_gaussian,
    edge_enhancement,
    log_inversion,
    remove_background,
)

# 파이프라인 단계 이름 (진행률 표시용)
PIPELINE_STEPS = [
    "Log inversion",
    "Denoising",
    "Local contrast (CLAHE)",
    "Background removal",
    "Edge enhancement",
]

# 파라미터 기본값. 키는 의미 단위이며, 각 영상처리 모듈 인자에 매핑된다.
DEFAULT_PARAMS: dict[str, float] = {
    "clip_percent": 90.0,   # 로그 반전: 상위 클리핑 백분위 (Direct beam 제거)
    "alpha": 15.0,          # 로그 반전: 시그모이드 대비 강도
    "beta": 30.0,           # 로그 반전: 시그모이드 중심 톤 (%) — 낮을수록 밝아짐
    "denoise_sigma": 0.5,   # 노이즈 제거: 가우시안 강도 (0 이면 건너뜀)
    "clahe_clip": 2.0,      # CLAHE: 지역 대비 한계
    "clahe_tile": 8.0,      # CLAHE: 타일 그리드 크기 (개수)
    "bg_thresh": 5.0,       # 배경 제거: 임계값 (0 이면 건너뜀)
    "edge_strength": 0.5,   # 엣지 강화: 라플라시안 가중치
}


def basic_pipeline(
    raw_array: np.ndarray,
    params: dict[str, float] | None = None,
    progress: Callable[[int, int, str], None] | None = None,
) -> np.ndarray:
    """기본 이미지 프로세싱 파이프라인.

    로그 반전 → 노이즈 제거 → CLAHE → 배경 제거 → 엣지 강화.

    Parameters
    ----------
    raw_array : np.ndarray
        원시 uint16 디텍터 영상.
    params : dict, optional
        조정할 파라미터. 누락된 키는 ``DEFAULT_PARAMS`` 로 채워진다.
    progress : callable, optional
        ``progress(step_index, total_steps, label)`` 형태로 단계별 진행을 보고.

    Returns
    -------
    np.ndarray
        uint8 [0, 255] 처리 결과.
    """
    p = {**DEFAULT_PARAMS, **(params or {})}
    total = len(PIPELINE_STEPS)

    def step(i: int) -> None:
        if progress is not None:
            progress(i, total, PIPELINE_STEPS[i])

    # 1. 로그 반전 — MONOCHROME2 → MONOCHROME1 (시작점)
    step(0)
    img = log_inversion(
        raw_array,
        clip_percent=float(p["clip_percent"]) / 100.0,
        apply_sigmoid=True,
        alpha=float(p["alpha"]),
        beta=float(p["beta"]) / 100.0,
    )

    # 2. 노이즈 제거 — 강도 0 이면 건너뜀 (ksize=0 → sigma 기반 자동 커널)
    step(1)
    sigma = float(p["denoise_sigma"])
    if sigma > 0:
        img = denoise_gaussian(img, ksize=0, sigma=sigma)

    # 3. 지역 대비 강화 (CLAHE) — uint8 변환 후 적용
    step(2)
    u8 = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    u8 = apply_clahe(
        u8,
        clip_limit=float(p["clahe_clip"]),
        tile_grid_size=max(1, int(round(p["clahe_tile"]))),
    )

    # 4. 배경 제거 — 임계값 0 이면 건너뜀
    step(3)
    thresh = int(round(p["bg_thresh"]))
    img2 = remove_background(u8, thresh_val=thresh) if thresh > 0 else u8

    # 5. 엣지 강화
    step(4)
    result = edge_enhancement(img2, strength=float(p["edge_strength"]))

    if progress is not None:
        progress(total, total, "Done")
    return result


if __name__ == "__main__":
    # 의존 데이터 없이 동작 확인용 더미 실행
    dummy = np.random.randint(0, 65535, (RAW_HEIGHT, RAW_WIDTH), dtype=np.uint16)
    out = basic_pipeline(dummy)
    print("basic_pipeline 출력:", out.shape, out.dtype)
