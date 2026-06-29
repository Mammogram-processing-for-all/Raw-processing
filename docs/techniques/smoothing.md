# Smoothing과 Denoising(잡음 제거)

!!! abstract "요약"
    Smoothing(평활화)은 이웃 픽셀을 결합해 영상의 변동을 줄이는 공간 연산(spatial
    operation)이다. 주 목적은 **잡음 제거(denoising)**지만, 동시에 엣지도 흐려져
    [MTF](../image-quality/metrics.md)가 떨어지는 트레이드오프가 있다. 이 페이지는 가장
    단순한 선형 필터(mean/Gaussian)에서 시작해, 엣지를 보존하는 비선형 필터(median,
    bilateral, anisotropic diffusion, NLM, **guided filter**, BM3D)로 **단순→정교 순서**로
    나아가고, 마지막에 유방 마스크 생성에 쓰이는 형태학적 연산(morphology)을 다룬다.

## 1. 동기 — 왜 잡음을 제거하는가

X-ray 영상의 지배적 잡음은 광자 계수의 통계적 요동인 **양자 잡음(quantum noise, Poisson
noise)**이다. 디텍터에 도달하는 광자 수가 평균 $\lambda$인 Poisson 과정을 따르므로 분산도
$\lambda$이고, 표준편차는 $\sqrt{\lambda}$다([디텍터](../foundations/detector.md) 참고).
선량이 낮은 영역(두꺼운 조직 뒤)일수록 SNR이 낮다.

$$
\mathrm{SNR} = \frac{\lambda}{\sqrt{\lambda}} = \sqrt{\lambda}
$$

잡음 특성은 [SNR/NPS(Noise Power Spectrum)](../image-quality/metrics.md)로 정량화한다.

!!! warning "근본 트레이드오프: 잡음↓ vs MTF↓"
    선형 smoothing은 고주파 성분을 줄여 잡음을 낮추지만, **엣지와 미세구조도 고주파**이므로
    함께 흐려진다. 즉 [MTF](../image-quality/metrics.md)가 떨어진다. 미세석회처럼 작고
    날카로운 구조가 진단의 핵심인 맘모그래피에서는 이 트레이드오프가 치명적이다. 이것이
    뒤의 에지보존(edge-preserving) 필터들이 등장한 이유다.

## 2. 선형 필터 (가장 단순)

선형 필터는 커널(kernel) $h$와의 컨볼루션(convolution)으로 정의된다.

$$
g(x,y) = (f * h)(x,y) = \sum_{i}\sum_{j} f(x-i,\,y-j)\,h(i,j)
$$

### 2.1 Mean / Box filter

모든 가중치가 동일한 $n\times n$ 커널. 구현이 가장 단순하고 빠르지만(적분영상으로 O(1)
박스), 엣지를 가장 심하게 뭉개고 박스 모양 아티팩트가 생긴다.

### 2.2 Gaussian filter

가중치가 가우시안을 따르는 커널. 등방성(isotropic)이고 부드러워 인공물이 적다.

$$
h(i,j) = \frac{1}{2\pi\sigma^2}\exp\!\left(-\frac{i^2+j^2}{2\sigma^2}\right)
$$

$\sigma$가 클수록 더 강하게 흐려진다(저역통과 차단주파수↓). 2D 가우시안은 **분리 가능
(separable)**하여 $h(i,j)=h_x(i)\,h_y(j)$로 1D 두 번에 나눠 적용할 수 있어, 연산량이
$O(n^2)\to O(n)$으로 준다.

```py
import cv2
blur = cv2.GaussianBlur(img, ksize=(0, 0), sigmaX=2.0)  # ksize=0이면 sigma로 자동 결정
```

### 2.3 주파수영역 저역통과 (low-pass)

컨볼루션은 주파수영역에서 곱셈이다($\mathcal{F}\{f*h\}=F\cdot H$). 가우시안 등으로 고주파를
감쇠시키는 것이 저역통과 필터링이다. 이상적(ideal) 저역통과는 ringing을 만들어 실무에서는
부드러운 차단(Gaussian, Butterworth)을 쓴다.

## 3. 비선형 / 에지보존 필터 (정교)

선형 필터의 "엣지도 흐린다" 한계를 푸는 흐름이다. 핵심은 **평활화하되 엣지는 넘어가지
않게** 하는 것.

### 3.1 Median filter

이웃의 **중앙값**으로 대체. 임펄스(salt-and-pepper) 잡음과 핫픽셀 제거에 탁월하고, 평균과
달리 엣지를 비교적 보존한다. 가우시안 잡음에는 mean보다 효율이 낮다.

### 3.2 Bilateral filter

공간 거리뿐 아니라 **휘도 차이**까지 가중에 넣어, 엣지를 가로지르는 픽셀의 기여를 줄인다.

$$
g(p) = \frac{1}{W_p}\sum_{q\in\Omega} f(q)\,
\underbrace{G_{\sigma_s}(\lVert p-q\rVert)}_{\text{공간}}\,
\underbrace{G_{\sigma_r}(\lvert f(p)-f(q)\rvert)}_{\text{휘도}}
$$

$\sigma_r$가 작으면 엣지 보존이 강해진다. 단점은 강한 엣지 근처에서 계단/만화 같은
(staircase) 효과와 비교적 높은 비용.

### 3.3 Anisotropic diffusion (Perona–Malik, 1990)

확산(diffusion)을 엣지에서 멈추도록 만든 PDE 기반 방법. 확산 계수 $c(\cdot)$가 gradient
크기에 반비례한다.

$$
\frac{\partial I}{\partial t} = \nabla\cdot\big(c(\lVert\nabla I\rVert)\,\nabla I\big),
\qquad c(s)=\exp\!\big(-(s/K)^2\big)
$$

평탄 영역은 강하게 확산(=평활), 엣지에서는 확산 억제(=보존)된다.

### 3.4 Non-Local Means (NLM, Buades 2005)

"비슷한 패치는 영상 어디에 있든 같은 신호"라는 가정으로, **패치 유사도**를 가중치로 삼아
평균한다. 반복 텍스처가 많은 영상에서 강력하지만 비용이 크다.

### 3.5 Guided filter (He, 2010)

가이드 영상 $I$(자기 자신 또는 다른 영상)에 대해 출력이 **지역적으로 선형 모델**
$q_i = a_k I_i + b_k$ ($i\in\omega_k$)를 따른다고 가정해, 각 윈도우에서 $a_k,b_k$를 최소제곱으로
구한다. bilateral과 비슷한 에지보존 효과를 내면서 **영상 크기에 대해 선형 시간(O(N), 윈도우
크기 무관)**으로 매우 빠르고, gradient 반전(halo) 아티팩트가 적다.

!!! example "프로젝트에서의 guided filter"
    본 프로젝트는 **guided filter로 영상을 평활 배경(base)과 디테일(detail)로 분해**하는 데
    사용한다. 이 base/detail 분해는 [Laplacian pyramid](multiscale.md) 분해와 함께
    톤 매핑(배경 압축 + 디테일 재증폭)의 토대가 된다. 에지보존 평활이므로 큰 구조의 경계를
    유지한 채 배경만 부드럽게 추정할 수 있다([pipeline](../pipeline/three-tier.md)).

### 3.6 BM3D (간단 언급)

Block-Matching and 3D filtering(Dabov 2007). 유사 블록을 모아 3D 변환영역에서 협업
필터링(collaborative filtering)하는 최신 고성능 denoiser. 가우시안 잡음에서 오랫동안 사실상
표준 성능을 보였으나 비용이 크다. 이후 [딥러닝 denoiser](modern-dl.md)가 이를 대체·보강한다.

## 4. 형태학적 연산 (Morphology)

이진/그레이 마스크의 형태를 다루는 비선형 연산으로, 잡음 제거보다 **마스크 정제**에 쓰인다.
구조요소(structuring element) $B$에 대해:

- **Erosion(침식)** $f\ominus B$ : 밝은 영역을 깎음 → 작은 잡음점 제거.
- **Dilation(팽창)** $f\oplus B$ : 밝은 영역을 키움 → 구멍 메움.
- **Opening(열기)** $f\circ B = (f\ominus B)\oplus B$ : 작은 돌기·잡음 제거(크기 유지).
- **Closing(닫기)** $f\bullet B = (f\oplus B)\ominus B$ : 작은 구멍·틈 메움.

```py
import cv2
import numpy as np

k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)   # 잡음 제거
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)  # 구멍 메움

# 가장 큰 연결요소(largest connected component)만 유지
n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
mask = (labels == largest).astype(np.uint8)
```

!!! example "프로젝트의 유방 마스크 생성"
    본 프로젝트는 **threshold로 1차 마스크를 만든 뒤, morphology(opening/closing)로 잡음과
    구멍을 정리하고, 가장 큰 connected component만 남겨** 유방 영역을 분리한다. 이 마스크는
    이후 [peripheral equalization](peripheral-equalization.md), CLAHE blend 등에서 처리
    범위를 한정하는 데 쓰인다([pipeline](../pipeline/three-tier.md)).

## 5. 비교표

| 필터 | 분류 | 잡음 제거 | 엣지 보존 | 계산 비용 | 비고 |
|------|------|-----------|-----------|-----------|------|
| Mean/Box | 선형 | 보통 | 나쁨 | 매우 낮음 | 가장 단순, 박스 아티팩트 |
| Gaussian | 선형 | 좋음 | 나쁨 | 낮음(separable) | 표준 저역통과 |
| Median | 비선형 | 임펄스에 탁월 | 보통 | 낮음 | salt-and-pepper |
| Bilateral | 비선형 | 좋음 | 좋음 | 높음 | staircase 가능 |
| Anisotropic diffusion | PDE | 좋음 | 매우 좋음 | 높음(반복) | 파라미터 $K$ 민감 |
| NLM | 비선형 | 매우 좋음 | 좋음 | 매우 높음 | 패치 유사도 |
| Guided filter | 선형모델 | 좋음 | 좋음 | **낮음(O(N))** | 빠름, halo 적음 |
| BM3D | 변환영역 | 매우 좋음 | 좋음 | 매우 높음 | 고전 SOTA |

## 참고문헌

- R. C. Gonzalez, R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018. (Spatial Filtering, Morphology)
- P. Perona, J. Malik, "Scale-Space and Edge Detection Using Anisotropic Diffusion," *IEEE TPAMI*, vol. 12, no. 7, pp. 629–639, 1990.
- C. Tomasi, R. Manduchi, "Bilateral Filtering for Gray and Color Images," *ICCV 1998*, pp. 839–846.
- A. Buades, B. Coll, J.-M. Morel, "A Non-Local Algorithm for Image Denoising," *CVPR 2005*, vol. 2, pp. 60–65.
- K. Dabov et al., "Image Denoising by Sparse 3-D Transform-Domain Collaborative Filtering (BM3D)," *IEEE TIP*, vol. 16, no. 8, pp. 2080–2095, 2007.
- K. He, J. Sun, X. Tang, "Guided Image Filtering," *ECCV 2010*; *IEEE TPAMI*, vol. 35, no. 6, pp. 1397–1409, 2013.
