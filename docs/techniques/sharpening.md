# Sharpening과 Edge Enhancement(에지 강조)

!!! abstract "요약"
    Sharpening(첨예화)은 고주파 성분을 강조해 경계와 미세구조를 또렷하게 만드는 공간
    연산이다. smoothing과 정반대로 **고주파를 키워** 손실된 [MTF](../image-quality/metrics.md)를
    보강하는 효과를 낸다. 이 페이지는 가장 단순한 미분 연산자(gradient, Laplacian)에서
    시작해, 고전적이면서 가장 널리 쓰이는 **unsharp masking(USM)**과 high-boost, 그리고
    엣지보존·다중스케일·주파수영역 기반의 정교한 방법까지 **단순→정교 순서**로 다룬다.
    미세석회 검출이라는 임상 목표와 halo/ringing 같은 부작용 관리를 함께 강조한다.

## 1. 동기 — 무엇을 또렷하게 하려는가

맘모그래피에서 sharpening의 임상 목표는 **미세석회(microcalcification)**와 종괴의
경계(margin) 가시성을 높이는 것이다. 미세석회는 수백 µm 크기의 작고 고대비인 구조로,
악성 군집(cluster)의 중요한 조기 징후다([맘모그램 개념](../foundations/mammography.md)).
이런 구조는 고주파 대역에 있으므로, 디텍터·산란·blur로 떨어진 고주파
[MTF](../image-quality/metrics.md)를 부분적으로 되살리는 것이 핵심이다.

!!! warning "양날의 검"
    고주파는 미세구조이기도 하지만 **잡음**이기도 하다([smoothing](smoothing.md)의 양자
    잡음 참고). 무분별한 sharpening은 잡음을 함께 증폭하고 halo/ringing 아티팩트를 만든다.
    그래서 sharpening은 항상 "어디를, 얼마나"의 적응적 제어가 관건이다.

## 2. 미분 연산자 (가장 단순)

밝기의 변화율(미분)이 큰 곳이 곧 엣지다.

### 2.1 1차 미분 — Gradient (Sobel, Prewitt)

$$
\nabla f = \left[\frac{\partial f}{\partial x},\ \frac{\partial f}{\partial y}\right],
\qquad
\lVert\nabla f\rVert = \sqrt{f_x^2 + f_y^2}
$$

Sobel·Prewitt는 차분에 평활을 결합한 $3\times3$ 커널로 $f_x,f_y$를 근사한다. 예: Sobel $x$ 커널

$$
G_x = \begin{bmatrix} -1 & 0 & 1 \\ -2 & 0 & 2 \\ -1 & 0 & 1 \end{bmatrix}
$$

### 2.2 2차 미분 — Laplacian

$$
\nabla^2 f = \frac{\partial^2 f}{\partial x^2} + \frac{\partial^2 f}{\partial y^2}
$$

이산 커널(예):

$$
\begin{bmatrix} 0 & 1 & 0 \\ 1 & -4 & 1 \\ 0 & 1 & 0 \end{bmatrix}
$$

Laplacian은 엣지에서 부호가 바뀌는(zero-crossing) 응답을 주어 가는 경계 검출에 좋다.

!!! note "엣지 검출 vs 엣지 강조"
    - **엣지 검출(edge detection)** : 미분 결과 자체를 출력(엣지 맵). Canny, zero-crossing 등.
    - **엣지 강조(edge enhancement/sharpening)** : 미분 결과를 **원본에 다시 더해** 경계를
      또렷하게 만든다. 예: $g = f - \nabla^2 f$ (Laplacian sharpening). 본 페이지의 주제는
      후자다.

## 3. Unsharp Masking (USM)과 High-boost (고전·표준)

가장 오래되고 가장 널리 쓰이는 sharpening. 원본에서 흐린 버전을 빼면 고주파(=mask)만
남고, 이를 원본에 더해 고주파를 부스트한다.

$$
g = f + \lambda\big(f - \mathrm{blur}(f)\big)
$$

여기서 $f-\mathrm{blur}(f)$가 **unsharp mask**(고주파 성분), $\lambda$가 강조량이다.

??? info "유도와 high-boost 일반화"
    $\mathrm{blur}=f*h_{\text{LP}}$(저역통과)라 하면 $f-\mathrm{blur}(f)=f*(\delta-h_{\text{LP}})$는
    고역통과(high-pass)다. 일반화한 **high-boost** 필터는
    $g = A\,f - \mathrm{blur}(f) = (A-1)f + \big(f - \mathrm{blur}(f)\big)$,
    $A\ge1$로 원본을 더 살린 형태다. $A=1$이면 순수 고역통과, $A>1$이면 원본+고주파.

파라미터(이미지 편집 툴의 USM 3요소와 동일):

- **amount** ($\lambda$) : 고주파를 얼마나 더할지. 클수록 강하지만 과증폭.
- **radius** ($\sigma$ of blur) : 어느 스케일의 디테일을 강조할지. 작으면 미세 디테일,
  크면 큰 구조의 국소 대비.
- **threshold** : 이 값 이하의 작은 차이는 강조하지 않음 → **평탄 영역 잡음 증폭 방지**.

```py
import cv2
import numpy as np

def unsharp(img, sigma=1.5, amount=1.0, threshold=0):
    blur = cv2.GaussianBlur(img.astype(np.float32), (0, 0), sigma)
    mask = img.astype(np.float32) - blur
    if threshold > 0:
        mask[np.abs(mask) < threshold] = 0
    out = img.astype(np.float32) + amount * mask
    return np.clip(out, 0, np.iinfo(img.dtype).max).astype(img.dtype)
```

!!! warning "USM의 부작용"
    - **Halo / overshoot** : 강한 엣지 양쪽에 밝은/어두운 띠(과도 강조)가 생긴다.
    - **Ringing** : 엣지 주변 진동.
    - **잡음 증폭** : 평탄 영역의 양자 잡음이 부풀려진다(threshold로 완화).
    radius/amount를 키울수록 심해지므로 보수적 설정이 안전하다.

## 4. 적응형 / 에지보존 기반 Sharpening (개선)

USM은 영상 전역에 같은 $\lambda$를 쓴다. **개선된 방법은 "엣지에서만" 또는 "잡음이 아닌
곳에서만" 강조**한다.

- **국소 대비(local contrast) 적응** : 지역 분산·gradient에 따라 $\lambda$를 가변. 평탄
  영역(=잡음 우려)에서는 약하게, 구조가 있는 영역에서는 강하게.
- **에지보존 분해 기반** : [bilateral/guided filter](smoothing.md)로 base/detail을 나누고
  **detail만 증폭**한다. 흐린 버전이 엣지를 보존하므로 halo가 크게 줄어든다. 본 프로젝트의
  guided filter base/detail 분해가 정확히 이 구조를 따른다([pipeline](../pipeline/three-tier.md)).
- **gradient 기반 게이팅** : Sobel 크기로 엣지 마스크를 만들어 그 영역에만 sharpening 적용.

## 5. 다중스케일 Unsharp (정교)

단일 $\sigma$의 USM은 한 스케일만 강조한다. **여러 $\sigma$(여러 radius)의 unsharp mask를
가중 합성**하면 미세석회(작은 σ)와 종괴 경계(큰 σ)를 동시에 강조할 수 있다.

$$
g = f + \sum_{k} \lambda_k\big(f - \mathrm{blur}_{\sigma_k}(f)\big)
$$

이것은 본질적으로 [다중스케일 분해](multiscale.md)(Laplacian pyramid)의 각 대역을 가중하는
것과 같다. MUSICA·local Laplacian으로 이어지는 자연스러운 일반화다
([contrast-enhancement](contrast-enhancement.md)).

## 6. 주파수영역 / Homomorphic Filtering (한 단락)

컨볼루션은 주파수영역의 곱이므로, sharpening은 **고역통과(high-pass)·고주파 강조(high-frequency
emphasis)** 필터로도 구현된다: $H(u,v) = a + b\,H_{\text{HP}}(u,v)$로 저주파를 남기고 고주파를
부스트한다. **Homomorphic filtering**은 영상을 조도(illumination, 저주파)와 반사(reflectance,
고주파)로 보고 $\log$ 영역에서 저주파를 누르고 고주파를 키워, **동적범위 압축과 대비 강조를
동시에** 달성한다([contrast-enhancement](contrast-enhancement.md)).

## 7. 부작용·아티팩트 관리와 검증

- **halo/overshoot** : amount/radius를 낮추거나 에지보존 분해를 쓴다.
- **잡음 증폭** : threshold, 적응형 게이팅, [denoising](smoothing.md) 선행.
- **검증** : 강조 효과는 [MTF](../image-quality/metrics.md) 상승으로, 부작용은
  [NPS/SNR](../image-quality/metrics.md)로 정량 확인한다. MTF가 1을 크게 넘으면 과증폭이고,
  잡음 영역 NPS가 급증하면 잡음을 부풀린 것이다. **임상 검증**(병변 검출률)이 최종 기준이다.

## 참고문헌

- R. C. Gonzalez, R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018. (Sharpening Spatial Filters, Frequency Domain Filtering)
- A. P. Dhawan, G. Buelloni, R. Gordon, "Enhancement of Mammographic Features by Optimal Adaptive Neighborhood Image Processing," *IEEE Transactions on Medical Imaging*, vol. 5, no. 1, pp. 8–15, 1986.
- W. M. Morrow et al., "Region-Based Contrast Enhancement of Mammograms," *IEEE Transactions on Medical Imaging*, vol. 11, no. 3, pp. 392–406, 1992.
- A. F. Laine, S. Schuler, J. Fan, W. Huda, "Mammographic Feature Enhancement by Multiscale Analysis," *IEEE Transactions on Medical Imaging*, vol. 13, no. 4, pp. 725–740, 1994.
