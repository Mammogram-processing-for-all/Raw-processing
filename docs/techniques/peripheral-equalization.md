# Peripheral Equalization과 두께 보상(Thickness Compensation), Flatten

!!! abstract "요약"
    압박된 유방은 가장자리(skin line 근처)로 갈수록 두께가 급격히 얇아진다. 두께가 얇으면 [X-ray 감쇠](../foundations/xray-physics.md)가 적어 검출기에 도달하는 선량이 많아지고(밝게, 때로 포화), 내부의 두꺼운 부위는 어둡게 표현된다. 그 결과 진단상 중요한 **외곽 조직(peripheral tissue)** 이 잘 보이지 않는다. **Peripheral equalization**(말초 균등화)은 저주파 배경(두께·조도 맵)을 추정해 외곽만 선택적으로 밝기를 보정하여 영상 전체를 한 화면에서 판독 가능하게 만드는 공간적(spatial) 보정이다. 이 문서는 고전적 두께 모델 기반 기법에서 출발하여, 본 [프로젝트 파이프라인](../pipeline/three-tier.md)이 채택한 **normalized convolution + distance-transform soft fade** 방식까지 **단순→최신** 순으로 정리한다. 이 단계는 이후 [다중스케일 분해](multiscale.md)와 [contrast enhancement](contrast-enhancement.md)의 전처리로서 결정적이다.

전체 기법 지형은 [기법 개요](index.md)를 참고하라.

---

## 1. 문제 정의: 두께 구배와 조도 불균일

### 1.1 외곽 얇아짐(peripheral thinning)

압박판 사이에서 유방은 중앙이 평평하고 외곽으로 갈수록 곡면을 이루며 얇아진다. 두께 $t(x)$ 가 얇은 외곽에서는 Beer–Lambert 법칙([X-ray 감쇠](../foundations/xray-physics.md))에 따라 투과 선량이 지수적으로 커진다.

$$
I_{\text{det}}(x) = I_0 \exp\!\left(-\int \mu\, t(x)\, dl\right)
$$

[디텍터/log선형화](../foundations/detector.md)로 log 변환하면 신호는 두께에 대략 선형이 되지만, 여전히 외곽은 매우 밝고(또는 포화) 내부는 어두운 거대한 저주파 구배가 남는다. 이 구배가 [windowing/flatten](../image-formation/windowing.md)에서 좁은 window로 외곽 조직을 가려버리는 원인이다.

### 1.2 조도 불균일(heel effect 등)

X-ray 관의 **heel effect** 때문에 양극(anode)-음극(cathode) 방향으로 입사 선량이 기울어지고, 산란선·기하학적 요인까지 더해져 빈 영역(flat field)조차 균일하지 않다. 이는 두께와 무관한 추가 저주파 구배로, 함께 보정 대상이 된다.

!!! note "flat-field 보정과의 차이"
    flat-field 보정은 **피사체 없는** 보정 영상(gain/offset)으로 검출기·조도의 고정 패턴을 제거한다(검출기 단계). Peripheral equalization은 **피사체(유방) 영상 자체**에서 두께 기인 저주파 배경을 추정해 보정한다는 점에서 다르다. 둘은 보완적이다.

---

## 2. (고전) 두께 모델 기반 vs 영상 기반 Peripheral Equalization

고전적 접근의 공통 골격은 **저주파 배경(두께/조도 맵) 추정 → 외곽만 선택적 밝기 보정**이다. 추정 방법에 따라 두 갈래로 나뉜다.

### 2.1 두께 모델 기반(model-based)

유방을 "중앙은 일정 두께(압박판 간격), 외곽은 반원/구형으로 얇아짐"으로 모델링하여 두께 $t(x)$ 를 해석적으로 추정한다. Stahl 등은 두께 분포를 추정해 보정량을 산출했고[^stahl], Byng 등은 외곽 영역의 밝기를 균등화하는 thickness equalization을 제안했으며[^byng], Snoeren & Karssemeijer는 검출기·기하 모델 기반의 thickness correction을 정식화했다[^snoeren]. 물리적 근거가 명확하나 압박 형상·환자 변이에 민감하다.

### 2.2 영상 기반(image-based)

영상 자체에서 저역 필터로 두께/조도 맵을 추정한다. 모델 가정이 적고 강건하지만, 내부의 실제 구조(저주파 성분)까지 배경으로 빨아들이지 않도록 주의해야 한다. 본 프로젝트는 영상 기반에 속한다.

---

## 3. 두께 맵 추정 방법

### 3.1 저역 필터 / 다항식 피팅

가장 단순하게는 큰 가우시안 저역 필터나 2D 다항식 surface fitting으로 배경 $B(x)$ 를 얻는다. 그러나 단순 저역 필터는 마스크 경계(공기/유방 경계)에서 공기의 어두운(또는 밝은) 값이 섞여들어 경계 근처 추정이 오염되는 치명적 문제가 있다.

### 3.2 Normalized convolution (프로젝트 방식)

**Normalized convolution**(Knutsson & Westin, 1993)은 신뢰도 마스크 $m(x)\in[0,1]$ 로 가중한 블러를 분자/분모로 정규화해, 마스크 밖(공기) 화소가 추정에 끼어들지 않게 한다[^knutsson].

$$
B(x) = \frac{\big(m\cdot I\big) * g}{\,m * g\,}
$$

분모 $m*g$ 가 유효 가중치 합을 보정하므로, **유방 마스크 내부 화소만**으로 외곽까지 매끄럽게 외삽된 두께/조도 맵을 얻는다. breast mask는 파이프라인 초반에 분리된다([프로젝트 파이프라인](../pipeline/three-tier.md)).

```py
import cv2
import numpy as np

def normalized_convolution(img, mask, sigma):
    """마스크 가중 블러의 numer/denom 정규화로 두께/조도 맵 추정."""
    g = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), sigma)
    numer = g(img * mask)
    denom = g(mask) + 1e-6        # 0 나눗셈 방지
    return numer / denom           # 마스크 밖 화소는 추정에 미기여
```

### 3.3 형태학적 배경 추정

morphological opening(또는 큰 구조요소의 grayscale opening)으로 작은 구조를 제거하고 거친 배경만 남기는 방법도 쓰인다. 미세 구조는 보존되지만 구조요소 크기 선택에 민감하다.

---

## 4. 외곽만 보정하는 트릭 (프로젝트 방식)

핵심 난제는 "외곽은 들어올리되 **내부 신호와 대비는 건드리지 않고**, 경계에 halo도 만들지 않는" 것이다.

### 4.1 reference 백분위 기준 차감

추정한 두께/조도 맵 $B(x)$ 에서, 충분히 두꺼운 내부를 대표하는 **reference 백분위(percentile)** 값 $B_{\text{ref}}$ (예: 마스크 내 상위 일정 백분위)를 기준으로 삼는다. 보정량은 각 화소가 기준보다 얼마나 "얇아서 밝은가"에 비례한다.

$$
C(x) = \max\!\big(B(x) - B_{\text{ref}},\, 0\big)
$$

$C(x)$ 를 원본에서 빼면(또는 부호 규약에 맞춰 더하면) 얇은 외곽만 reference 두께 수준으로 끌어올려진다. 내부($B(x)\le B_{\text{ref}}$)는 $C=0$ 이라 **건드리지 않아 내부 대비가 보존**된다.

### 4.2 distance-transform soft fade로 halo 방지

보정을 외곽에 급격히 적용하면 보정 영역과 비보정 영역의 경계에 인공적인 띠(halo/역대비)가 생긴다. 이를 막기 위해 breast mask의 **거리 변환(distance transform)** $d(x)$ (skin line으로부터의 거리)로 부드러운 가중치 $\alpha(x)$ 를 만든다.

$$
\alpha(x) = \text{smoothstep}\!\big(d(x);\, d_0, d_1\big),\qquad
I_{\text{out}}(x) = I(x) - \alpha(x)\,C(x)
$$

skin line 근처($d$ 작음)에서 보정을 강하게, 내부 깊숙이($d$ 큼)에서는 0으로 매끄럽게 사라지게 하여 경계 halo를 제거한다.

```py
def peripheral_equalize(img, mask, bg, ref_pct=95, d0=5, d1=80):
    ref = np.percentile(bg[mask > 0], ref_pct)
    corr = np.clip(bg - ref, 0, None)              # 얇은 외곽만 양수
    dist = cv2.distanceTransform((mask > 0).astype(np.uint8),
                                 cv2.DIST_L2, 5)
    a = np.clip((dist - d0) / (d1 - d0), 0, 1)
    fade = 1.0 - a                                 # 외곽=1, 내부=0
    return img - fade * corr
```

!!! example "프로젝트에서의 위치"
    [프로젝트 파이프라인](../pipeline/three-tier.md)에서 이 단계(peripheral thickness compensation)는 log-linearization과 breast mask 직후, [다중스케일 분해](multiscale.md) 직전에 놓인다. 두께 구배를 먼저 평탄화해야 이후 guided filter 분해의 global layer가 두께 구배가 아닌 진짜 조직 구조를 담게 된다.

---

## 5. 전역 조도 평탄화(flatten)와의 관계

"flatten"은 넓게 보면 영상에서 거대한 저주파 구배(두께+조도)를 제거해 전 영역을 비슷한 밝기 기준선 위에 올리는 작업이다. peripheral equalization은 그중 **외곽 두께 구배에 특화된 선택적 flatten**이다. 전역 flatten을 무차별로 적용하면 내부의 유용한 저주파 정보(예: 큰 종괴의 완만한 음영)까지 지워질 수 있어, §4처럼 외곽에 국한하는 것이 안전하다. window/level 관점의 flatten은 [windowing/flatten](../image-formation/windowing.md), 톤 곡선 관점은 [특성 곡선/톤매핑](../image-formation/characteristic-curves.md)을 참고하라.

이 단계의 의의는 분명하다. 외곽을 균등화해 두면

- 이후 [다중스케일 분해](multiscale.md)의 global layer가 두께가 아닌 조직 구조를 포착하고,
- [contrast enhancement](contrast-enhancement.md)·[점 연산/CLAHE](point-operations.md)의 동적범위가 한쪽(외곽 포화)에 낭비되지 않는다.

---

## 6. 부작용과 검증

!!! warning "과보정의 위험"
    - **Halo / 역대비(contrast reversal)**: 보정량이 크거나 fade가 급격하면 skin line 안쪽에 밝은/어두운 띠가 생긴다. soft fade 폭($d_0,d_1$)과 reference 백분위를 보수적으로 둔다.
    - **외곽 잡음 증폭**: 외곽은 본래 SNR이 낮은데 밝기를 올리면 잡음이 두드러진다. [smoothing/denoising](smoothing.md)과 순서·강도를 조율한다.
    - **미세석회 왜곡**: 두께 맵 추정에 작은 구조가 섞이면 외곽 미세석회가 배경으로 흡수돼 사라질 수 있다. normalized convolution의 $\sigma$ 를 충분히 크게 해 미세 구조를 배경에 넣지 않는다.

검증은 정성(외곽 조직 가시성, 경계 halo 유무)과 정량을 함께 본다. 균등화 전후의 외곽/내부 밝기 분포 일치도, 그리고 MTF/엣지 보존이 깨지지 않았는지는 [MTF/품질지표](../image-quality/metrics.md)로 점검한다.

---

## 참고문헌

[^stahl]: Stahl, M., Aach, T., & Dippel, S. (2000). *Digital radiography enhancement by nonlinear multiscale processing.* Medical Physics, 27(1), 56–65. (두께/배경 보정과 다중스케일 결합 맥락)
[^byng]: Byng, J. W., Critten, J. P., & Yaffe, M. J. (1997). *Thickness-equalization processing for mammographic images.* Radiology, 203(2), 564–568.
[^snoeren]: Snoeren, P. R., & Karssemeijer, N. (2004). *Thickness correction of mammographic images by means of a global parameter model of the compressed breast.* IEEE Transactions on Medical Imaging, 23(7), 799–806.
[^knutsson]: Knutsson, H., & Westin, C.-F. (1993). *Normalized and Differential Convolution: Methods for Interpolation and Filtering of Incomplete and Uncertain Data.* CVPR 1993, 515–523.
