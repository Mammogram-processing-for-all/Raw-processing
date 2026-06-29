"""영상처리 함수 패키지.

각 영상처리 단계를 주제별 모듈로 분리하고, 여기서 공개 함수를 한데 모아
re-export 한다. 사용 측에서는 ``from processing import log_inversion`` 처럼
모듈 경로를 신경 쓰지 않고 함수를 가져올 수 있다.
"""

from __future__ import annotations

from .contrast import apply_clahe, histogram_equalization
from .denoising import denoise_gaussian, denoise_median
from .enhancement import (
    apply_gabor_filters,
    combine_clahe_gabor,
    edge_enhancement,
    multi_frequency_decomposition,
    unsharp_mask,
)
from .loaders import (
    RAW_DTYPE,
    RAW_HEIGHT,
    RAW_WIDTH,
    load_dicom,
    load_raw,
)
from .log_inversion import log_inversion, sigmoid_contrast
from .lut import (
    apply_lut,
    create_window_lut,
    gamma_lut,
    hologic_style_lut,
    log_lut,
    make_lut,
    siemens_style_lut,
    sigmoid_lut,
)
from .morphology import remove_background, top_hat_filter
from .normalization import contrast_stretching, normalize, window_contrast

__all__ = [
    # loaders
    "RAW_HEIGHT",
    "RAW_WIDTH",
    "RAW_DTYPE",
    "load_raw",
    "load_dicom",
    # log inversion
    "log_inversion",
    "sigmoid_contrast",
    # normalization
    "window_contrast",
    "normalize",
    "contrast_stretching",
    # denoising
    "denoise_gaussian",
    "denoise_median",
    # contrast
    "apply_clahe",
    "histogram_equalization",
    # morphology
    "top_hat_filter",
    "remove_background",
    # enhancement
    "apply_gabor_filters",
    "combine_clahe_gabor",
    "unsharp_mask",
    "edge_enhancement",
    "multi_frequency_decomposition",
    # lut
    "make_lut",
    "apply_lut",
    "create_window_lut",
    "log_lut",
    "gamma_lut",
    "sigmoid_lut",
    "hologic_style_lut",
    "siemens_style_lut",
]
