# Windowing

## 왜 윈도잉인가

DICOM 픽셀은 보통 12~16비트(0~65535)로 저장되지만, 일반 디스플레이는 8비트(0~255)만 표시할 수 있다. 동적 범위 전체를 단순히 선형으로 축소하면, 진단상 중요한 좁은 밝기 구간이 모두 비슷한 회색으로 뭉개진다.

**윈도잉(Windowing)** 은 동적 범위 중 일부 구간만 잘라내어 디스플레이의 전체 명암으로 펼친다. 그 구간 밖은 모두 검정(0) 또는 흰색(255)으로 클리핑된다.

## WC / WW 정의

윈도잉은 두 파라미터로 정의된다.

- **WC (Window Center)** — 표시 구간의 중심 픽셀값
- **WW (Window Width)** — 표시 구간의 폭

표시 구간은 다음과 같다.

$$
[\,WC - WW/2,\; WC + WW/2\,]
$$

선형 매핑은 다음 식으로 픽셀값 $x$를 디스플레이 강도 $y \in [0, 255]$ 로 변환한다 (단순화 형태).

$$
y(x) = \begin{cases}
0 & x \le WC - \tfrac{WW}{2} \\[4pt]
255 \cdot \dfrac{x - (WC - WW/2)}{WW} & WC - \tfrac{WW}{2} < x < WC + \tfrac{WW}{2} \\[8pt]
255 & x \ge WC + \tfrac{WW}{2}
\end{cases}
$$

같은 이미지라도 WC/WW 조합에 따라 보이는 조직이 완전히 달라진다. 지방 조직, 선조직, 석회화가 각각 다른 강도 구간에 분포해 있기 때문이다.

!!! note "DICOM 정식 식"
    DICOM PS3.3 C.11.2.1.2.1의 선형 VOI LUT은 `-0.5` 오프셋과 `(WW - 1)` 분모를 사용한다.

    $$
    y(x) = \left( \frac{x - (WC - 0.5)}{WW - 1} + 0.5 \right) \cdot (y_{\max} - y_{\min}) + y_{\min}
    $$

    실용적으로는 위 단순화 식과 결과가 거의 같지만, "표준에 맞춰 구현했다"고 말하려면 정식 식을 따른다.

## DICOM 파이프라인에서의 위치

DICOM 표시 파이프라인은 단순한 한 단계가 아니다. 표준(DICOM PS3.3 Annex C.11)은 세 개의 LUT를 정의한다.

```mermaid
graph LR
  R[Raw Stored Pixel] --> M[Modality LUT]
  M --> V[VOI LUT<br/>= Windowing]
  V --> P[Presentation LUT]
  P --> D[Display]
```

| 단계 | 역할 | 입력→출력 |
|------|------|---------|
| Modality LUT | 장비 의존적 → 의미 있는 단위 (예: HU) | 저장값 → 실측값 |
| **VOI LUT** | 표시 관심 영역 강조 | **WC/WW 적용 = 윈도잉** |
| Presentation LUT | 그레이스케일 → 디스플레이 강도 | 0~1 → 0~255 |

[`lut.md`](../lut.md)에서 다룬 LUT는 주로 이 단계 중 VOI LUT/Presentation LUT에 해당한다.

## Linear vs Sigmoid VOI LUT

DICOM은 VOI LUT을 두 가지 모드로 정의한다.

### Linear (기본)

위의 선형 식을 그대로 사용. 구현이 가볍지만 윈도 경계에서 강한 클리핑이 일어난다.

### Sigmoid (`(0028,1056) VOILUTFunction = SIGMOID`)

$$
y(x) = \frac{255}{1 + \exp\!\left(-4 \cdot \dfrac{x - WC}{WW}\right)}
$$

윈도 경계가 매끄럽게 처리돼 클리핑으로 인한 정보 손실이 적다. **저대비(low contrast) 영상이 많은 mammography에서 자주 쓰인다.** sigmoid LUT를 [`lut.md`](../lut.md)에서 미리 계산해 LUT 배열로 저장해두면 픽셀당 한 번의 배열 인덱싱으로 끝나 빠르다.

## pydicom + numpy 구현

`pydicom`은 `apply_voi_lut`를 제공하지만, 디버깅이나 batch 처리를 위해 직접 구현해보면 다음과 같다.

```python title="apply_window.py" linenums="1"
import numpy as np
import pydicom


def apply_window(arr: np.ndarray, wc: float, ww: float,
                 mode: str = "linear") -> np.ndarray:
    """16-bit DICOM pixel → 8-bit display."""
    lo, hi = wc - ww / 2.0, wc + ww / 2.0

    if mode == "linear":
        out = (arr - lo) / ww
        out = np.clip(out, 0.0, 1.0)
    elif mode == "sigmoid":
        out = 1.0 / (1.0 + np.exp(-4.0 * (arr - wc) / ww))
    else:
        raise ValueError(mode)

    return (out * 255).astype(np.uint8)


def load_display(path: str) -> np.ndarray:
    dcm = pydicom.dcmread(path)
    arr = dcm.pixel_array.astype(np.float32)

    if dcm.PhotometricInterpretation == "MONOCHROME1":
        arr = arr.max() - arr  # MONOCHROME1 보정 (참고: dicom-basics.md)

    wc = float(np.atleast_1d(dcm.WindowCenter)[0])
    ww = float(np.atleast_1d(dcm.WindowWidth)[0])
    return apply_window(arr, wc, ww, mode="sigmoid")
```

`WindowCenter`/`WindowWidth`가 다중값(MultiValue)으로 저장돼 있는 DICOM이 흔하므로 첫 번째 값을 꺼내 쓴다.

## Mammography에서 자주 보는 WC/WW

일반 흉부 X-ray는 WW가 수천 단위로 넓지만, mammography는 미세한 밀도 차이를 봐야 해서 **상대적으로 좁은 WW**가 흔하다. 디바이스 제조사마다 권장 프리셋이 있고, DICOM 헤더에 함께 저장된다.

| 시나리오 | 전형적인 WC/WW | 강조되는 것 |
|---------|--------------|----------|
| Soft tissue | 중간 WC, 좁은 WW | 지방 vs 선조직 대비 |
| Calcification | 높은 WC, 더 좁은 WW | 미세석회화 |
| Skin line | 낮은 WC, 넓은 WW | 피부·유두 윤곽 |

자동 탐지 파이프라인은 보통 한 가지 표시용 WC/WW로 고정하기보다는, **raw 16비트를 그대로 모델에 넣고** 모델 내부에서 정규화하도록 한다. 표시(display)와 모델 입력(input)을 구분하는 것이 중요하다.

## 윈도잉이 충분하지 않을 때

윈도잉은 **선형(또는 sigmoid) 매핑** 한 단계다. 유방 내 지역적 대비 — 예: 치밀유방 안의 작은 종괴 — 를 따로 강조하려면 윈도잉 다음에 [CLAHE](clahe.md) 같은 지역 대비 보정을 덧붙인다. 주파수 대역별 강조가 필요하면 [Laplacian Pyramid](laplacian-pyramid.md)로 넘어간다.
