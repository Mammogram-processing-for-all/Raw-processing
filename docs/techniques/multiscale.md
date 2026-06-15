# 다중스케일 분해와 변환영역 기법

!!! abstract "요약"
    유방촬영(mammography) 영상은 미세석회화(microcalcification, 고주파)부터 종괴·조직 구조(mass, 중주파), 압박 두께에 의한 밝기 구배(저주파)까지 서로 다른 스케일(scale)의 정보를 동시에 담고 있다. 단일 스케일 처리로는 이들을 모두 최적화할 수 없으므로, 영상을 스케일별로 **분해(decomposition)** 하여 각 대역을 독립적으로 처리한 뒤 다시 **재합성(recombination)** 하는 것이 다중스케일 기법의 핵심이다. 이 문서는 가장 고전적인 가우시안/라플라시안 pyramid에서 출발하여 wavelet 변환, 임상 표준인 MUSICA, 그리고 halo가 없는 엣지보존(edge-preserving) 분해(guided filter, local Laplacian filter)까지 **단순→최신** 순으로 정리한다. 이는 [프로젝트 파이프라인](../pipeline/three-tier.md)의 3-tier 분해와 직접 연결된다.

전체 기법 지형은 [기법 개요](index.md)를 참고하라.

---

## 1. 동기: 단일 스케일 처리의 한계

[contrast enhancement](contrast-enhancement.md)의 [점 연산/CLAHE](point-operations.md)이나 단일 커널 [sharpening](sharpening.md)은 영상 전체에 동일한 변환을 적용한다. 그러나 맘모그래피에서 중요한 구조는 스케일이 극단적으로 다르다.

| 구조 | 대표 크기 | 주파수 대역 |
| --- | --- | --- |
| 미세석회화 (microcalcification) | 0.1–1 mm | 고주파 (high-pass) |
| 종괴·섬유선 구조 (mass, ductal) | 수 mm–cm | 중주파 (band-pass) |
| 압박 두께 구배·조도 불균일 | 영상 전역 | 저주파 (low-pass) |

단일 커널로 고주파를 강조하면 잡음([smoothing/denoising](smoothing.md) 대상)이 함께 증폭되고, 저주파를 평탄화하면 미세 구조가 뭉개진다. 해결책은 **스케일 분리 후 차등 처리**다.

$$
I(x) = \sum_{\ell} D_\ell(x) + R(x)
$$

여기서 $D_\ell$ 은 레벨 $\ell$ 의 대역통과(band-pass) 성분, $R$ 은 최저 해상도 잔차(residual)다. 각 $D_\ell$ 에 가중치 $w_\ell$ 을 곱해 재합성하면

$$
\hat I(x) = \sum_{\ell} w_\ell\, D_\ell(x) + w_R\, R(x)
$$

가 되어, 저주파($w_R<1$, 동적범위 압축)는 누르고 고·중주파($w_\ell>1$, 대비 강조)는 살리는 **동적범위 압축(Dynamic Range Compression, DRC)** 이 한 번에 가능해진다.

---

## 2. (고전) 가우시안/라플라시안 Pyramid — Burt & Adelson

가장 기본적인 다중스케일 표현은 Burt와 Adelson(1983)의 pyramid다[^burt].

### 2.1 가우시안 pyramid 구성

가우시안 pyramid는 가우시안 저역 필터 후 2배 다운샘플링(`pyrDown`)을 반복한다.

$$
G_0 = I,\qquad G_{\ell+1} = \text{Down}\big(g * G_\ell\big)
$$

여기서 $g$ 는 분리형 5-탭 가우시안 커널이다. 각 레벨은 점점 더 거친(coarse) 저주파 근사를 담는다.

### 2.2 라플라시안 pyramid = 대역통과

라플라시안 pyramid의 각 레벨은 인접한 두 가우시안 레벨의 차이, 즉 **대역통과(band-pass)** 성분이다.

$$
L_\ell = G_\ell - \text{Up}(G_{\ell+1}),\qquad L_n = G_n
$$

`Up`은 업샘플 후 가우시안 보간(`pyrUp`)이다. 이는 [sharpening](sharpening.md)에서 다룬 unsharp masking의 다중스케일 일반화로 볼 수 있다(단일 차분 → 여러 대역의 차분).

### 2.3 완전 재구성(perfect reconstruction)

원본은 손실 없이 복원된다.

$$
G_\ell = L_\ell + \text{Up}(G_{\ell+1}) \;\Rightarrow\; I = G_0
$$

따라서 레벨별 계수에 가중치를 곱한 뒤 재구성하면 스케일별 대비·디테일을 자유롭게 조절할 수 있다.

```py
import cv2
import numpy as np

def laplacian_pyramid(img, levels=5):
    """가우시안/라플라시안 pyramid 분해."""
    gp = [img.astype(np.float32)]
    for _ in range(levels):
        gp.append(cv2.pyrDown(gp[-1]))
    lp = []
    for i in range(levels):
        up = cv2.pyrUp(gp[i + 1], dstsize=gp[i].shape[1::-1])
        lp.append(gp[i] - up)        # 대역통과 성분
    lp.append(gp[-1])                # 최저해상도 잔차
    return lp

def reconstruct(lp, weights):
    """레벨별 가중치로 재합성 (per-level weights)."""
    img = lp[-1] * weights[-1]
    for i in range(len(lp) - 2, -1, -1):
        up = cv2.pyrUp(img, dstsize=lp[i].shape[1::-1])
        img = up + lp[i] * weights[i]   # w>1 강조, w<1 억제
    return img
```

!!! note "프로젝트의 per-level weights 방식"
    [프로젝트 파이프라인](../pipeline/three-tier.md)의 detail layer는 `image − mid`로 얻은 고주파 잔차를 Laplacian pyramid로 더 잘게 쪼갠 뒤, **레벨별 가중치**를 곱해 미세 구조를 증폭한다. 가장 미세한 레벨(잡음과 겹침)은 가중치를 보수적으로, 중간 레벨(미세석회·섬유)은 공격적으로 두어 잡음 증폭을 억제하면서 진단적 디테일을 살린다.

!!! warning "선형 분해의 halo"
    라플라시안 pyramid는 **선형(linear)** 분해라 강한 엣지 부근에서 대역통과 성분에 over/undershoot가 생긴다. 계수를 크게 증폭하면 엣지 주변에 후광(halo)·링잉(ringing)이 나타난다. 이를 해결하는 것이 아래의 비선형 엣지보존 분해다.

---

## 3. (고전) Wavelet 변환

Pyramid가 공간 도메인의 반복 필터링이라면, **wavelet 변환(wavelet transform)** 은 직교/이중직교 기저로의 변환영역(transform-domain) 표현으로, 다해상도 해석(multiresolution analysis)의 수학적 틀을 제공한다(Mallat)[^mallat].

### 3.1 이산 wavelet 변환(DWT)

2D DWT는 각 레벨에서 저역·고역 필터 쌍으로 영상을 4개 서브밴드로 분해한다.

- **LL**: 근사(approximation, 저주파) — 다음 레벨로 재귀
- **LH, HL, HH**: 수평/수직/대각 디테일(고주파)

mother wavelet $\psi$ 를 스케일 $a$ 로 늘리고 위치 $b$ 로 옮긴 기저

$$
\psi_{a,b}(x) = \frac{1}{\sqrt{a}}\,\psi\!\left(\frac{x-b}{a}\right)
$$

로 신호를 전개하며, Haar·Daubechies·biorthogonal 등 mother wavelet 선택이 결과를 좌우한다.

### 3.2 서브밴드 계수 조작

변환영역에서 계수를 직접 다루면 두 가지 처리가 자연스럽다.

- **잡음 제거**: 작은 계수는 잡음으로 보고 threshold(soft/hard thresholding). $\hat w = \text{sign}(w)\max(|w|-\lambda,0)$. 자세한 비교는 [smoothing/denoising](smoothing.md) 참고.
- **대비 향상**: 디테일 서브밴드 계수에 스케일별 비선형 이득 함수 $g(w)$ 를 곱해 강조. 작은 계수는 더 키우고 큰 계수는 덜 키우는 비선형 곡선을 쓰면 미세 구조를 선택적으로 부각한다.

맘모그래피에서 wavelet은 특히 **미세석회화 검출(microcalcification detection)** 의 전처리·특징 추출에 널리 쓰였다(고주파 서브밴드에 석회가 잘 분리됨).

??? info "왜 wavelet이 맘모에 잘 맞나"
    미세석회화는 국소적(compact support)이며 다양한 크기를 가진다. wavelet은 공간-주파수 국소성(space-frequency localization)을 동시에 제공해, 작은 점상 구조를 특정 스케일·서브밴드에 집중시켜 배경 조직과 분리하기 쉽다.

---

## 4. (임상 표준) MUSICA

**MUSICA(Multi-Scale Image Contrast Amplification)** 는 Agfa가 상용화한 다중스케일 대비 증폭 알고리즘으로, CR/DR 일반촬영과 맘모그래피의 표시(presentation) 처리에서 사실상의 임상 표준이 되었다[^musica].

핵심 아이디어는 §2–§3과 동일하다: 영상을 여러 해상도 대역으로 분해하고, 각 대역의 계수에 **비선형 이득 함수**를 적용해 작은 진폭(미세 대비)은 크게, 큰 진폭(굵은 구조·구배)은 작게 증폭한 뒤 재합성한다. 그 결과 동적범위는 압축되면서도 국소 대비는 강화되어, 두꺼운 부위와 얇은 외곽이 한 화면에 잘 표시된다.

!!! tip "임상적 위치"
    MUSICA류 처리는 검출기에서 나온 for-processing 원시 영상을 진단의가 보는 for-presentation 영상으로 바꾸는 표준 경로의 일부다. 본 프로젝트의 3-tier 분해 + 톤매핑 + [CLAHE](point-operations.md)는 동일한 목표(DRC + 국소 대비)를 오픈 구성요소로 재현한 것으로 볼 수 있다.

---

## 5. (최신) 엣지보존 다중스케일 분해

선형 분해의 halo 문제(§2.3)를 풀기 위해, **비선형 엣지보존(edge-preserving)** 분해가 등장했다. 핵심은 base(저주파, 큰 구조)와 detail(고주파)을 나눌 때 강한 엣지를 흐리지 않는 평활화를 쓰는 것이다.

### 5.1 Guided filter 기반 분해 (프로젝트 방식)

**Guided filter**(He et al., 2010)는 가이드 영상의 국소 선형 모델로 엣지를 보존하면서 평활화하는 $O(N)$ 필터다[^he]. base/detail 분리는

$$
B = \text{GF}_r(I),\qquad D = I - B
$$

로 정의되며, 반지름 $r$ 을 키우면 더 큰 구조까지 base에 포함된다. bilateral filter보다 gradient reversal과 halo가 적고 빠르다.

!!! example "프로젝트의 3-tier 분해"
    [프로젝트 파이프라인](../pipeline/three-tier.md)은 guided filter를 두 번 써서 3개 층으로 나눈다.

    - **global layer** = 큰 반지름 guided filter (전역 두께/조도 구배)
    - **regional layer** = 중간 반지름 guided filter − global (조직·종괴 스케일)
    - **detail layer** = image − mid, 이후 Laplacian pyramid로 per-level 증폭 (미세석회·텍스처)

    재합성 시 **global은 억제**(DRC), **regional+detail은 증폭**한 뒤 톤매핑과 CLAHE로 마무리한다. 비선형 base 분리 덕분에 강한 엣지(skin line, 굵은 혈관)에서 halo가 거의 생기지 않는다.

### 5.2 Local Laplacian filters — Paris 2011

**Local Laplacian filters**(Paris, Hasinoff, Kautz, 2011)는 표준 라플라시안 pyramid의 틀은 유지하되, 각 픽셀·각 레벨에서 국소적으로 원본을 비선형 리매핑(remapping)한 뒤 pyramid 계수를 다시 계산한다[^paris]. 이로써 **halo 없이** 국소 대비를 강화하거나 톤을 압축할 수 있다. 리매핑 함수의 파라미터로 디테일 강조 정도와 엣지 보존 강도를 분리 제어한다.

### 5.3 도메인 변환(domain transform)

Gastal & Oliveira(2011)의 **domain transform**은 측지 거리(geodesic distance) 기반의 실시간 엣지보존 평활화로, 반복 1D 필터링으로 큰 영상도 빠르게 처리한다[^gastal]. base/detail 분해의 또 다른 선택지다.

### 5.4 비선형 분해가 halo/ringing을 줄이는 원리

선형 저역 필터는 엣지를 가로질러 평균을 내므로 base에 엣지의 "유령"이 남고, $I-B$ 의 detail에 큰 over/undershoot가 생긴다. 엣지보존 필터는 엣지에서 평활화를 멈추므로 base가 엣지를 날카롭게 유지하고, detail에는 엣지 부근 잔차가 거의 남지 않는다. 따라서 detail을 크게 증폭해도 후광이 생기지 않는다.

---

## 6. 재합성과 톤매핑 결합 (DRC)

다중스케일 분해의 최종 목적은 단순 대비 강조가 아니라 **동적범위 압축(DRC)** 과 국소 대비 향상의 동시 달성이다.

$$
\hat I = \underbrace{w_R\, R}_{\text{저주파 압축}} + \sum_\ell \underbrace{w_\ell\, D_\ell}_{\text{고·중주파 보존/강조}},\quad w_R<1<w_\ell
$$

저주파 층의 이득을 1보다 작게(또는 톤매핑 곡선으로 비선형 압축) 두어 두꺼운/얇은 부위의 거대 밝기 차를 줄이고, 디테일 층은 보존·강조해 미세 구조를 살린다. 이후 단계의 톤 곡선은 [contrast enhancement](contrast-enhancement.md)와 [특성 곡선/톤매핑](../image-formation/characteristic-curves.md)에서 다루며, 전체 흐름은 [프로젝트 파이프라인](../pipeline/three-tier.md)에 정리되어 있다. 분해 직전의 조도/두께 평탄화는 [Peripheral Equalization](peripheral-equalization.md)에서 다룬다.

---

## 7. 방법 비교

| 방법 | 선형/비선형 | halo 위험 | 대표 용도 |
| --- | --- | --- | --- |
| 가우시안/라플라시안 pyramid | 선형 | 높음 (강한 증폭 시) | 다중스케일 unsharp, 빠른 DRC 프로토타입 |
| Wavelet (DWT) | 선형(변환) | 중간 (ringing) | 미세석회 검출, 계수 thresholding 잡음제거 |
| MUSICA | 비선형 이득 | 낮음 | 임상 표시(presentation) 표준 |
| Guided filter 분해 | 비선형(엣지보존) | 낮음 | 프로젝트 base/detail, 실시간 |
| Local Laplacian | 비선형 | 매우 낮음 | halo 없는 국소 대비/톤압축 |
| Domain transform | 비선형(엣지보존) | 낮음 | 실시간 대용량 평활화 |

---

## 참고문헌

[^burt]: Burt, P. J., & Adelson, E. H. (1983). *The Laplacian Pyramid as a Compact Image Code.* IEEE Transactions on Communications, 31(4), 532–540.
[^mallat]: Mallat, S. (1989). *A Theory for Multiresolution Signal Decomposition: The Wavelet Representation.* IEEE Transactions on Pattern Analysis and Machine Intelligence, 11(7), 674–693. 또한 Mallat, S. (2008). *A Wavelet Tour of Signal Processing* (3rd ed.). Academic Press.
[^musica]: Vuylsteke, P., & Schoeters, E. (1994). *Multiscale Image Contrast Amplification (MUSICA).* Proc. SPIE Medical Imaging, vol. 2167, 551–560.
[^he]: He, K., Sun, J., & Tang, X. (2010). *Guided Image Filtering.* ECCV 2010; 확장판 IEEE TPAMI, 35(6), 1397–1409 (2013).
[^paris]: Paris, S., Hasinoff, S. W., & Kautz, J. (2011). *Local Laplacian Filters: Edge-aware Image Processing with a Laplacian Pyramid.* ACM Transactions on Graphics (SIGGRAPH), 30(4).
[^gastal]: Gastal, E. S. L., & Oliveira, M. M. (2011). *Domain Transform for Edge-Aware Image and Video Processing.* ACM Transactions on Graphics (SIGGRAPH), 30(4).
