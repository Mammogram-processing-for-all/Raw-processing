"""입출력 (I/O) — RAW / DICOM 적재."""

from __future__ import annotations

import numpy as np

try:
    import pydicom
    from pydicom.pixel_data_handlers.util import apply_voi_lut
except ImportError:
    pydicom = None
    apply_voi_lut = None


RAW_HEIGHT = 3816
RAW_WIDTH = 3048
RAW_DTYPE = np.dtype("<u2")  # little-endian uint16


def load_raw(path: str, height: int = RAW_HEIGHT, width: int = RAW_WIDTH) -> np.ndarray:
    """디텍터 RAW 파일을 읽어 (height, width) uint16 배열로 반환."""
    expected = height * width
    data = np.fromfile(path, dtype=RAW_DTYPE)
    if data.size < expected:
        raise ValueError(
            f"RAW size {data.size} smaller than {height}x{width} = {expected}"
        )
    return data[:expected].reshape(height, width)


def load_dicom(path: str, apply_voi: bool = False) -> np.ndarray:
    """DICOM 파일을 읽어 float32 배열로 반환.

    RescaleSlope / RescaleIntercept 를 적용하고, apply_voi=True 인 경우
    VOI LUT(밝기/대비) 까지 적용한다.
    """
    if pydicom is None:
        raise ImportError("pydicom 이 설치되어 있지 않습니다.")

    ds = pydicom.dcmread(path)
    if apply_voi and apply_voi_lut is not None:
        img = apply_voi_lut(ds.pixel_array, ds).astype(np.float32)
    else:
        img = ds.pixel_array.astype(np.float32)

    slope = float(ds.get("RescaleSlope", 1))
    intercept = float(ds.get("RescaleIntercept", 0))
    return img * slope + intercept
