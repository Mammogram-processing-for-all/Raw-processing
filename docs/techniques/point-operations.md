# 점 연산: Windowing, Gamma, 히스토그램 평활화, CLAHE

!!! abstract "요약"
    점 연산(point operation, pixel-wise operation)은 **출력 픽셀값이 같은 위치의 입력
    픽셀값만의 함수**인 가장 단순한 영상 처리다. 공간 정보(이웃 픽셀)를 전혀 보지 않으므로
    [LUT](lut.md)로 가속할 수 있다. 이 페이지는 가장 단순한 선형 변환과
    [windowing](../image-formation/windowing.md)·gamma부터, 전역
    히스토그램 평활화(Histogram Equalization, HE), 그 한계를 보완한 적응형 AHE,
    그리고 잡음 과증폭을 억제한 **CLAHE (Contrast-Limited Adaptive Histogram
    Equalization)**까지 **단순→정교 순서**로 다룬다.

## 1. 점 연산이란

점 연산은 입력 영상 $f(x,y)$를 변환 함수 $T$로 매핑한다.

$$
g(x,y) = T\big(f(x,y)\big)
$$

핵심은 $T$가 **위치 $(x,y)$나 이웃에 무관**하고 오직 입력 강도 $r=f(x,y)$에만 의존한다는
점이다. 따라서 가능한 모든 입력값에 대해 $T$를 한 번씩만 계산해 [LUT](lut.md)에
저장해 두면, 영상 전체를 픽셀당 O(1) 조회로 처리할 수 있다. 16-bit 입력이면 $2^{16}=65536$
개 엔트리만 채우면 된다.

!!! note "점 연산의 본질적 한계"
    공간 정보를 보지 않기 때문에 점 연산만으로는 "이 영역은 어둡고 저 영역은 밝다" 같은
    **국소적 맥락**을 반영할 수 없다. 이 한계가 뒤에 나오는 AHE/CLAHE(국소 히스토그램)와
    공간 연산([smoothing](smoothing.md)/[sharpening](sharpening.md))의 등장 동기다.

## 2. 가장 단순한 점 연산 — 선형 변환

### 2.1 밝기/명암 선형 변환

$$
g = \alpha\, f + \beta
$$

- $\alpha$ (gain) : 명암(contrast) 조절. $\alpha>1$이면 대조도 증가.
- $\beta$ (bias) : 밝기(brightness) 조절.

가장 단순하지만 동적범위를 단순 이동·확대할 뿐이라, 포화(clipping)가 쉽게 일어난다.

### 2.2 Windowing (window/level)

표시 가능한 좁은 밝기 구간 $[L-W/2,\,L+W/2]$만 선형으로 펼치고 나머지는 포화시키는
구간별 선형 점 연산이다. 진단 시 관심 조직(예: 유선 조직 vs 지방)에 맞춰 window width
$W$와 window level(center) $L$을 조절한다.

$$
g =
\begin{cases}
0 & f \le L - W/2 \\
\dfrac{f-(L-W/2)}{W}\,(g_{\max}) & L-W/2 < f < L+W/2 \\
g_{\max} & f \ge L + W/2
\end{cases}
$$

자세한 내용과 DICOM VOI LUT 연계는 [windowing](../image-formation/windowing.md) 참고.

### 2.3 Gamma 변환

$$
g = g_{\max}\left(\frac{f}{f_{\max}}\right)^{\gamma}
$$

$\gamma<1$이면 어두운 영역을 펴고(밝게), $\gamma>1$이면 밝은 영역을 압축한다. 디스플레이의
비선형 응답 보정이나 톤 곡선(tone curve)으로 쓰인다. 필름·디텍터의 입출력 관계인
[특성 곡선](../image-formation/characteristic-curves.md)과 직접 연결된다. 본 프로젝트의
tone mapping 단계에서도 평활화된 배경(smoothed background)에 gamma를 적용한다
([contrast-enhancement](contrast-enhancement.md), [pipeline](../pipeline/three-tier.md)).

## 3. 히스토그램 평활화 (Histogram Equalization, HE)

선형/gamma 변환은 곡선을 사람이 정해야 한다. **HE는 영상 자신의 히스토그램으로부터
변환 곡선을 자동으로 만든다.** 아이디어는 출력 강도가 거의 균일(uniform)하게 분포하도록,
즉 누적분포함수(CDF)가 직선이 되도록 매핑하는 것이다.

정규화 히스토그램(확률) $p(r_j)=n_j/N$에 대해, $L$ 레벨 영상의 변환은 CDF에 비례한다.

$$
s_k = (L-1)\sum_{j=0}^{k} p(r_j),\qquad k=0,1,\dots,L-1
$$

이는 곧 누적 히스토그램을 정규화한 1D [LUT](lut.md)다.

!!! warning "HE의 장단점"
    - **장점** : 파라미터가 없고 전역 대조도를 자동으로 펼친다. 동적범위를 충분히 못 쓰는
      영상에 효과적.
    - **단점** : (1) **전역적**이므로 영상 일부의 국소 대조도는 오히려 떨어질 수 있다.
      (2) 빈도가 높은 배경 레벨이 곡선을 지배해 **잡음과 빈 영역을 과증폭**한다.
      (3) 부자연스러운 톤 점프(over-enhancement)가 생긴다. 맘모처럼 넓은 배경과 미세한
      병변이 공존하는 영상에서 특히 문제다.

## 4. 적응형 히스토그램 평활화 (AHE)

HE의 "전역" 한계를 푸는 가장 직접적인 방법은 **영상을 작은 영역(타일, tile)으로 나눠 각
영역마다 자기 히스토그램으로 HE를 수행**하는 것이다. 이것이 AHE(Adaptive HE, Pizer 1987)다.
국소 맥락을 반영하므로 국소 대조도가 크게 향상된다.

!!! warning "AHE의 치명적 약점 — 잡음 과증폭"
    균질한(거의 평탄한) 타일에서는 히스토그램이 좁은 구간에 몰려 있어, CDF 기울기가 매우
    커진다. 그 결과 작은 잡음 변동이 큰 강도 차이로 증폭된다. 균질 영역일수록 잡음이 더
    심하게 부풀려지는 역설이 생긴다.

## 5. CLAHE — Contrast-Limited Adaptive Histogram Equalization

AHE의 잡음 과증폭을 억제하기 위해 **clip limit**를 도입한 것이 CLAHE다(Pizer 1987 변형;
의료영상 표준 기법).

핵심 아이디어 두 가지:

1. **Clip limit (대조도 제한)** : 각 타일 히스토그램에서 어떤 빈(bin)의 빈도가 임계값을
   넘으면 그 초과분을 잘라내고, 잘라낸 양을 모든 빈에 고르게 재분배한다. 이렇게 하면 CDF
   기울기에 상한이 생겨, **균질 영역의 잡음 증폭이 제한**된다.
2. **타일 경계 쌍선형 보간(bilinear interpolation)** : 타일마다 독립 LUT를 쓰면 경계에서
   블록 아티팩트가 생긴다. CLAHE는 인접 4개 타일의 변환을 쌍선형 보간으로 섞어 경계를
   매끄럽게 만든다.

```mermaid
flowchart LR
    A[타일 분할] --> B[타일별 히스토그램]
    B --> C[clip limit 적용<br/>초과분 재분배]
    C --> D[타일별 CDF/LUT]
    D --> E[타일 경계<br/>쌍선형 보간]
    E --> F[출력]
```

### 5.1 맘모그래피에서의 CLAHE

Pisano 등(1998)은 치밀 유방(dense breast) 맘모그램에서 CLAHE가 **시뮬레이션된 spiculation
(방사상 구조)의 검출**을 향상시킴을 보였다. 동시에 clip limit가 너무 크면 잡음·아티팩트가
강조되어 위양성을 늘릴 수 있어, **임상에서는 약하게(보수적으로) 적용**하는 것이 통념이다.

### 5.2 Python 예시 (OpenCV)

```py
import cv2
import numpy as np

# img: uint8 또는 uint16 그레이스케일
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(img)
```

- `clipLimit` : clip limit. 클수록 대조도 강조가 강하고 잡음 증폭 위험이 커진다.
- `tileGridSize` : 타일 격자 수. 작을수록 더 국소적(=AHE에 가까움).

!!! example "프로젝트에서의 CLAHE 사용"
    본 프로젝트는 CLAHE를 **표시용(for-presentation) 단계**에서, 그것도 **유방 마스크
    내부에만 약하게 blend**하여 적용한다. 즉 배경(공기)에는 적용하지 않고, 톤 매핑된
    영상에 CLAHE 결과를 부분적으로 섞어 국소 대비를 살리되 잡음 과증폭을 피한다. 이후
    [windowing](../image-formation/windowing.md)으로 표시 범위를 정한다. 전체 흐름은
    [프로젝트 파이프라인](../pipeline/three-tier.md) 참고.

## 6. 히스토그램 매칭 / Specification

HE가 출력 히스토그램을 "균일"하게 만드는 특수한 경우라면, **히스토그램 매칭(histogram
matching, specification)**은 출력이 **임의로 지정한 목표 히스토그램**을 따르도록 매핑한다.
입력 영상의 CDF $G_{in}$와 목표 CDF $G_{ref}$에 대해 $T = G_{ref}^{-1}\circ G_{in}$로 LUT를
구성한다. 동일 장비·동일 프로토콜의 영상 간 **밝기/대조도 표준화(normalization)**나 기준
영상 톤으로의 정렬에 유용하다. 균일 분포를 목표로 하면 HE와 같아진다.

## 참고문헌

- R. C. Gonzalez, R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018. (Ch. 3: Intensity Transformations and Histogram Processing)
- S. M. Pizer et al., "Adaptive Histogram Equalization and Its Variations," *Computer Vision, Graphics, and Image Processing*, vol. 39, no. 3, pp. 355–368, 1987.
- K. Zuiderveld, "Contrast Limited Adaptive Histogram Equalization," in *Graphics Gems IV*, Academic Press, 1994, pp. 474–485.
- E. D. Pisano et al., "Contrast Limited Adaptive Histogram Equalization Image Processing to Improve the Detection of Simulated Spiculations in Dense Mammograms," *Journal of Digital Imaging*, vol. 11, no. 4, pp. 193–200, 1998.
