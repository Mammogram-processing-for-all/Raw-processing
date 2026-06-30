# Module B — 3-Tier 주파수 분해: 4단계 원리 분석
### `stage_decomposition()` 실행 흐름

```
compensated_raw (uint16)  +  mask (uint8)
   │
   ①  _guided_filter_masked(radius=50)    →  mid_layer (float32)
   │
   ②  _guided_filter_masked(radius=150)   →  global_layer (float32)
   │         (mid_layer를 입력으로 cascaded 적용)
   │
   ③  차분 연산
   │     regional_layer = mid_layer − global_layer
   │     detail_layer   = img_float − mid_layer
   │
   ④  Edge Fade + Laplacian Pyramid 증폭
   │     → enhanced_detail (float32)
   │
   ▼
global_layer, regional_layer, enhanced_detail  (Module C 입력)
```

---

## ① Masked Guided Filter — `_guided_filter_masked()`

### 왜 Guided Filter인가?

주파수 분해에서 핵심 요구사항은 **Edge-Preserving Smoothing**이다. 유방 내부의 조직 경계(섬유선 구조, 혈관벽)는 보존하면서 저주파 구배만 추출해야 한다.

| 대안 | 문제점 |
|------|--------|
| **가우시안 블러** | 모든 주파수를 균일하게 평활화 → 조직 경계가 흐려져 차분 레이어에 Halo 발생 |
| **Bilateral Filter** | Edge-preserving이나, 비선형이라 cascaded 적용 시 gradient reversal 아티팩트 발생 |
| **Guided Filter** | 선형(Linear) edge-preserving → cascaded 적용에 안전, O(N) 복잡도 |

---

### 표준 Guided Filter의 수학적 모델

Guided Filter는 각 윈도우 $\omega_k$ 에서 출력을 입력의 **국소 선형 변환**으로 모델링한다:

$$q_i = a_k \cdot I_i + b_k, \quad \forall i \in \omega_k$$

Self-guided (guide = source) 모드에서 최적 계수는:

$$a_k = \frac{\sigma_k^2}{\sigma_k^2 + \varepsilon}, \qquad b_k = \bar{I}_k (1 - a_k)$$

- $\bar{I}_k$: 윈도우 내 평균
- $\sigma_k^2$: 윈도우 내 분산
- $\varepsilon$: 정규화 파라미터

**$\varepsilon$의 물리적 의미**:

| 영역 | 분산 vs ε | $a_k$ | 출력 |
|------|-----------|-------|------|
| 평탄 영역 | $\sigma^2 \ll \varepsilon$ | $\approx 0$ | $q \approx \bar{I}$ (평균으로 평활화) |
| 에지 영역 | $\sigma^2 \gg \varepsilon$ | $\approx 1$ | $q \approx I$ (원본 보존) |

→ $\varepsilon$이 작을수록 더 많은 구조를 에지로 인식하여 보존, 클수록 강하게 평활화.

---

### Masked 버전의 핵심: 정규화 컨볼루션

표준 guided filter는 `boxFilter(normalize=True)`로 윈도우 통계를 계산한다. 그런데 유방-배경 경계 윈도우에서는 **배경 픽셀(값=0)이 통계에 포함**되어 평균과 분산이 심하게 왜곡된다.

```
표준 Box Filter 경계 문제:

  윈도우 내 픽셀:  [유방 0.7] [유방 0.8] [배경 0.0] [배경 0.0]
  boxFilter 평균:  (0.7 + 0.8 + 0.0 + 0.0) / 4 = 0.375   ← 실제 유방 평균(0.75)과 괴리
  → 유방-배경 경계에서 비정상적으로 낮은 base layer 형성
  → 차분 레이어(detail)가 경계에서 비정상 양수 → 밝은 Halo
```

**해결: Masked Box Filter (Normalized Convolution)**

$$\text{mean}(X) = \frac{\text{boxFilter}(X \cdot M)}{\text{boxFilter}(M)}$$

```python
N = cv2.boxFilter(mask_f, cv2.CV_32F, ksize, normalize=False)  # 윈도우 내 전경 픽셀 수
N = np.maximum(N, 1.0)                                         # 0 나눗셈 방지

mean_I  = cv2.boxFilter(I_masked, ..., normalize=False) / N    # 전경 전용 평균
mean_II = cv2.boxFilter(I_masked * img_float, ..., normalize=False) / N
```

- 분모 `N`이 윈도우 내 마스크 픽셀 수를 나타내므로, 배경 픽셀은 **분자·분모 모두에서 배제**된다.
- 경계 윈도우에서 유효 전경 샘플이 줄어 분산의 추정 정밀도는 약간 저하되지만, **계통 편향(bias)은 원천 제거**된다.

---

### 코드 구현 요약

```python
# Pass 1: 각 윈도우의 masked 통계
mean_I  = boxFilter(I·M) / N
mean_II = boxFilter(I²·M) / N            # I_masked * img_float ≡ I²·M (self-guided)
var_I   = max(mean_II − mean_I², 0)      # 수치 안정성: 음수 분산 방지

a = var_I / (var_I + eps)
b = mean_I · (1 − a)

# Pass 2: a, b의 윈도우 평균 (역시 masked)
mean_a = boxFilter(a·M) / N
mean_b = boxFilter(b·M) / N

# 최종 출력
result = mean_a · I + mean_b
result[mask == 0] = 0.0
```

**2-Pass 구조의 이유**: Pass 1에서 계산된 $(a_k, b_k)$는 각 윈도우에 종속적이다. 하나의 픽셀은 여러 겹치는 윈도우에 속하므로, Pass 2에서 모든 윈도우의 $(a_k, b_k)$를 **평균**하여 부드러운 출력을 얻는다. 이것이 guided filter의 핵심 트릭이다.

---

## ② Cascaded 분해 전략

### 직렬(Serial) 분해 구조

```
img_float ─────────────────────────────────────────┐
    │                                               │
    │  GF(r=50, ε=0.005)                            │
    ▼                                               │
 mid_layer ──────────────────────────┐              │
    │                                │              │
    │  GF(r=150, ε=0.01)            │              │
    ▼                                │              │
 global_layer                       │              │
    │                                │              │
    ▼                                ▼              ▼
 regional = mid − global    detail = img − mid
 (중간 주파수)                (고주파)
```

**왜 `img_float`에서 직접 `global`을 구하지 않는가?**

Guided Filter는 $\varepsilon$에 의해 보존할 에지의 진폭을 결정한다. 원본에서 `r=150`으로 직접 필터링하면, 큰 반경 때문에 중간 주파수 구조까지 global에 혼입된다.

대신 **mid_layer(이미 고주파가 제거된 신호)** 위에서 다시 필터링하면:
- mid_layer의 잔존 분산이 원본보다 작으므로 동일한 $\varepsilon$에서도 더 강한 평활화 효과
- Global ↔ Regional의 주파수 분리 경계가 더 깔끔해짐

이 전략은 **이중 Low-pass의 Cascaded Subtraction**으로, 라플라시안 피라미드의 연속 다운스케일과 유사한 사고방식이다.

---

### 3-Tier 분해의 주파수 대역 분할

```
주파수 축 (저 ─────────────────────────────────── 고)

├── Global ──┤── Regional ──┤──── Detail ────┤
│  (r=150)   │  (r=50~150)  │   (< r=50)     │
│ 두께 구배   │ 국소 조직 밀도 │ 미세석회화·혈관벽│
│ 억제 대상   │ 증폭 대상     │ 증폭 대상       │
```

| 레이어 | 계산식 | 물리적 대응 | 이후 처리 |
|--------|--------|------------|----------|
| `global_layer` | GF(GF(img, r=50), r=150) | 유방 전체 두께 구배 | Module C에서 `(1−α)` 곱으로 억제 |
| `regional_layer` | mid − global | 국소 유선 밀도·조직 구조 | Module C에서 gain으로 증폭 |
| `detail_layer` | img − mid | 미세석회화, 혈관벽, 섬유선 경계 | 라플라시안 피라미드로 선택적 증폭 |

---

## ③ 라플라시안 피라미드 증폭 — `_build_laplacian_pyramid()` / `_reconstruct_from_laplacian()`

### 왜 Detail Layer를 그대로 쓰지 않는가?

`detail_layer = img − mid`에는 미세석회화(~0.1mm)부터 혈관 구조(~5mm)까지 다양한 크기의 고주파 성분이 혼재한다. 이 중 진단적으로 가장 중요한 **초고주파(미세석회화)를 선택적으로 증폭**하려면, 고주파 내에서도 다시 크기별로 분리해야 한다.

### 라플라시안 피라미드 수학

가우시안 피라미드: $G_0 = \text{img}, \quad G_{l+1} = \text{pyrDown}(G_l)$

라플라시안 피라미드: $L_l = G_l - \text{pyrUp}(G_{l+1})$

- $L_0$: 최고주파 — 원본 해상도의 미세 구조 (미세석회화, 섬유선 경계)
- $L_1$: 차고주파 — 2배 다운스케일의 구조 (작은 혈관)
- $L_{l}$: 해상도가 절반씩 줄며 점점 저주파 구조
- $G_{\text{last}}$: 잔여 DC 성분

### 주파수 선택적 가중치

```python
weights = [2.0, 2.0, 1.5, 1.0, 0.5]
#          L0    L1    L2    L3    L4
#         최고주파 ─────────────── 저주파
```

| Level | 해상도 | 대응 구조 | 가중치 | 의도 |
|-------|--------|----------|--------|------|
| L0 | 원본 | 미세석회화, 섬유선 경계 | **2.0** | 최대 증폭 — 진단 핵심 |
| L1 | 1/2 | 소혈관, 미세 구조 | **2.0** | 강한 증폭 |
| L2 | 1/4 | 중소 구조 | **1.5** | 중간 증폭 |
| L3 | 1/8 | 중간 구조 | **1.0** | 원본 유지 |
| L4 | 1/16 | Regional에 근접한 저주파 | **0.5** | 억제 — Regional과 중복 방지 |

**L4의 가중치가 0.5인 이유**: 이 레벨의 구조는 이미 regional_layer와 주파수 대역이 겹친다. 증폭하면 Module C의 `regional_gain`과 이중 증폭되므로, 오히려 줄여서 대역 간 독립성을 유지한다.

### 재합성

```python
def _reconstruct_from_laplacian(lp, residual, weights):
    R = residual                         # 최저주파 잔차에서 시작
    for i in reversed(range(len(lp))):
        R = pyrUp(R) + lp[i] * weights[i]  # 업스케일 + 가중된 디테일 추가
    return R
```

저주파에서 시작하여 한 레벨씩 올라가며 가중된 고주파 디테일을 누적 합산한다. `weights[i] > 1.0`이면 해당 레벨의 구조가 원본보다 강조되고, `< 1.0`이면 억제된다.

---

## ④ Edge Fade — 경계 아티팩트 억제

### 잔존 문제: One-Sided Window

Masked Guided Filter가 배경 bias를 원천 제거하더라도, **마스크 극단 경계(~10px)**에서는 윈도우 내 전경 픽셀이 한쪽 방향으로만 존재한다. 이 one-sided 윈도우에서 계산된 통계(평균, 분산)는 실제보다 편향될 수 있다.

```
마스크 경계 근방 윈도우:

  [배경][배경][배경][유방][유방][유방]
  ← 배경(mask=0, 무시됨)    전경 →
  
  N이 작아 통계가 불안정. 분산의 추정치가 과소 → a가 과소 → 과도한 평활화
  → regional/detail 차분이 미소하게 왜곡
```

### 해결: Distance Transform 기반 Soft Fade

```python
EDGE_FADE_PX = 10.0
dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
edge_weight = np.clip(dist / EDGE_FADE_PX, 0.0, 1.0)
regional_layer = regional_layer * edge_weight
```

$$w(x, y) = \min\!\left(\frac{d(x,y)}{10}, \;1.0\right)$$

- $d(x,y)$: 마스크 경계로부터의 유클리드 거리 (L2 Distance Transform)
- 경계에서 0 → 10px 내부에서 1로 선형 증가
- Regional layer만 fade (global은 이미 저주파라 영향 미미, detail은 피라미드가 자체 평활)

**Regional만 적용하는 이유**:
- `global_layer`는 반경 150px의 극저주파 성분이므로 경계 10px의 불안정성이 실질적으로 무시 가능
- `enhanced_detail`은 라플라시안 피라미드 구조에서 다운스케일-업스케일 과정이 자체적으로 경계를 평활화
- `regional_layer`는 반경 50~150px의 중간 주파수로, 경계 one-sided 윈도우의 영향이 가장 직접적으로 나타남

---

## 부록: `test_laplacian_pyramid_only()` — 디버그 유틸리티

이 함수는 파이프라인의 일부가 아니라, 라플라시안 피라미드 증폭의 효과를 **단독으로 검증**하기 위한 테스트 도구이다.

```
compensated_raw
    │
    ├─ GF(r=50, ε=0.001) → base_layer
    │
    └─ detail = img − base
           │
           └─ Laplacian Pyramid (weights = [2.0, 1.0, 1.5, 1.0, 2.0])
                  │
                  └─ percentile(1%, 99%) 정규화 → uint16 출력
```

**본 파이프라인과의 차이점**:
- ε=0.001 (본 파이프라인: 0.005) → 더 많은 구조를 edge로 보존, base가 더 평탄
- 가중치 배열이 다름: `[2.0, 1.0, 1.5, 1.0, 2.0]` vs `[2.0, 2.0, 1.5, 1.0, 0.5]`
  - L4에 2.0을 주어 저주파 디테일까지 증폭 → 시각적 과장 효과로 디버깅 시 구조 파악 용이
