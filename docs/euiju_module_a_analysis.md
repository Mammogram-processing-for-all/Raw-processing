# Module A — 물리 신호 선형화: 4단계 원리 분석
### `stage_for_processing()` 실행 흐름

```
RAW uint16
   │
   ①  estimate_illumination_map()   →  I₀ 공간 맵 (float64)
   │
   ②  apply_log_linearization()     →  log(I₀/I) → uint16
   │
   ③  get_breast_mask()             →  이진 마스크 (uint8)
   │
   ④  compensate_peripheral_thickness()  →  Wedge 보정 uint16
   │
   ▼
compensated_raw  (Module B 입력)
```

---

## ① I₀ 조명 맵 추정 — `estimate_illumination_map()`

### 왜 필요한가?

Beer-Lambert Law에서 `log(I₀/I) = μt`가 성립하려면 **`I₀`(입사 광자 세기)가 공간적으로 균일**해야 한다. 그런데 실제 맘모그래피 시스템에서는 두 가지 요인으로 `I₀`가 위치마다 다르다.

| 요인 | 설명 |
|------|------|
| **Heel Effect** | X-ray 관의 음극(cathode) 방향으로 갈수록 광자 세기가 낮아지는 물리적 현상. 음극에서 나온 전자가 텅스텐 타깃 내부를 더 길게 통과하므로 자체 흡수가 강해짐 |
| **검출기 불균일성** | FPD(Flat Panel Detector) 픽셀별 감도 차이 |

`I₀`를 상수로 가정하고 로그 변환하면, 이 공간적 조명 불균일성이 **두께 신호처럼 위장**되어 이후 모든 처리가 왜곡된다. 따라서 공기 영역(유방이 없는 배경)에서 `I₀`의 공간 분포를 역추정해야 한다.

---

### 알고리즘 흐름

```
① Otsu 이진화로 배경(공기) 픽셀 추출
      │
② 배경 마스크를 30px 침식(Erosion)하여 "안전 배경" 확보
      │
③ 100px 격자 샘플링: 블록의 90% 이상이 안전 배경인 경우만 채택
      │   → 각 블록의 95th percentile 값을 그 위치의 I₀ 추정값으로 사용
      │
④ 수집된 샘플점 (xᵢ, yᵢ, zᵢ)에 2차 다항식 회귀 (최소제곱법)
      │
⑤ 전체 픽셀 좌표에 회귀 계수 적용 → 연속 I₀ 공간 맵
      │
⑥ I₀_floor 클리핑: I₀가 RAW 중앙값보다 낮아지지 않도록 하한 설정
```

---

### 2차 다항식 회귀의 수학적 구조

좌표를 `[0, 1]`로 정규화한 뒤, degree=2에서 기저 항목은:

$$\mathbf{A} \cdot \mathbf{c} = \mathbf{z}$$

$$\mathbf{A} = \begin{bmatrix} 1 & x_1 & y_1 & x_1^2 & x_1 y_1 & y_1^2 \\ \vdots & & & & & \vdots \\ 1 & x_n & y_n & x_n^2 & x_n y_n & y_n^2 \end{bmatrix}$$

6개의 계수 벡터 $\mathbf{c}$를 `np.linalg.lstsq`로 결정 → 전체 픽셀 그리드에 적용하면 **공간적으로 부드럽게 변하는 2차 곡면** 형태의 `i0_map`이 완성된다.

```python
# 기저 행렬 생성 (degree=2: 6항)
basis = [(x**i)*(y**j) for i in range(3) for j in range(3-i)]
# → [1, x, y, x², xy, y²]

# 최소제곱 회귀
coeffs, _, _, _ = np.linalg.lstsq(A, sz, rcond=None)

# 전체 픽셀에 적용
i0_map = (full_basis @ coeffs).reshape(h, w)
```

**95th percentile 샘플링을 쓰는 이유**: 배경에는 가끔 먼지, 케이블 음영 등 국소 어두운 픽셀이 섞이므로, 평균이나 중앙값 대신 95th percentile로 "충분히 밝은 배경의 대표값"을 안전하게 채취한다.

**30px 침식의 이유**: 배경-유방 경계 근방의 픽셀은 부분 볼륨 효과(Partial Volume)로 중간 밝기를 가진다. 이를 샘플에 포함시키면 I₀가 과소 추정되므로, 경계에서 충분히 내측인 픽셀만 선택한다.

---

## ② 로그 선형화 — `apply_log_linearization()`

### Beer-Lambert Law

$$I = I_0 \cdot e^{-\mu t}$$

- $I$: 검출기 측정 신호 (= `raw_array`)
- $I_0$: 입사 세기 (= `i0_map`)  
- $\mu$: 선형 감쇠 계수 (조직 종류에 따라 다름)
- $t$: X-ray 경로상의 조직 두께

양변에 로그를 취하면:

$$\underbrace{\ln\!\left(\frac{I_0}{I}\right)}_{\text{픽셀값}} = \mu t$$

**선형화의 핵심**: 원래 픽셀값은 두께 $t$에 대해 **지수 함수적**으로 반응하지만, 로그 변환 후에는 $t$에 **선형 비례**한다. 이 도메인에서는 두꺼운 조직과 얇은 조직의 밝기 차이가 선형 스케일로 표현되어, 이후의 필터링·차분·가중합이 물리적으로 의미 있는 연산이 된다.

### 코드 구현 세부

```python
EPSILON = 1.0
linearized = np.log(
    np.clip(i0_map, EPSILON, None) /      # 분자: I₀ (최소 1.0 보장)
    np.clip(raw_array, EPSILON, None)      # 분모: I  (0 나눗셈 방지)
)
linearized = np.clip(linearized, 0, None)  # I > I₀인 픽셀(음수 로그) 제거
result = linearized / l_max * 65535        # 동적 범위 [0, 65535] 정규화
```

**`EPSILON = 1.0`의 역할**: `raw_array`가 0인 픽셀(죽은 픽셀, 패딩 영역)에서 `log(I₀/0) = ∞` 발산을 방지.

**`clip(linearized, 0, None)`의 의미**: 이론적으로 `I > I₀`는 불가능하지만, 측정 노이즈나 I₀ 추정 오차로 인해 일부 픽셀에서 `raw > i0_map`이 발생한다. 이 경우 로그값이 음수가 되는데, 물리적으로 "투과율 > 100%"는 불가능하므로 0으로 클리핑한다.

**글로벌 정규화의 함의**: `l_max`로 나누어 전체 범위를 `[0, 65535]`에 맞추므로, **절대적인 감쇠 계수 값은 상실**되고 영상 내의 상대적인 두께 차이만 보존된다. 정량적 분석보다는 판독용 영상 생성이 목적이므로 적절한 선택이다.

---

## ③ 유방 마스크 생성 — `get_breast_mask()`

### 왜 마스크가 필요한가?

로그 선형화 후에도 배경(공기) 영역은 여전히 픽셀값을 가지며, 이것이 이후 필터링에 포함되면 경계 아티팩트를 유발한다. 유방 영역만을 정확히 특정하는 이진 마스크가 필요하다.

### 3단계 마스킹 파이프라인

```
로그 선형화된 uint16
      │
   [1] 임계값 이진화 (고정 임계값 mask_thresh)
      │   → 유방 신호(높은 값)를 255, 배경을 0으로 분리
      │
   [2] 모폴로지 연산으로 노이즈 제거
      │   CLOSE(5×5 타원): 유방 내 작은 구멍(암조직 저밀도 영역) 메움
      │   OPEN (5×5 타원): 배경의 작은 돌출(케이블, 이물질) 제거
      │
   [3] LCC(Largest Connected Component) 추출
         → 복수의 연결 요소 중 면적이 가장 큰 것만 유지
         → 반대쪽 유방, 또는 아티팩트 덩어리를 자동으로 제거
```

### 타원형 커널의 선택 이유

유방의 외형은 타원에 가깝다. 정사각형 커널은 대각선 방향으로 성분이 다르게 작용하지만, 타원형 커널은 방향에 무관하게 균일한 팽창/수축을 수행하므로 유방 윤곽을 자연스럽게 처리한다.

### CLOSE → OPEN 순서의 의미

```
CLOSE (팽창 후 침식): 내부 구멍 메움   → 유방 내 저밀도 영역이 마스크에서 뚫리지 않게 보정
OPEN  (침식 후 팽창): 외부 돌기 제거   → 배경에 붙어있는 작은 아티팩트 섬을 제거
```

순서가 바뀌면 (OPEN → CLOSE) 외부 돌기를 먼저 제거하다가 경계 근방의 실제 유방 조직까지 침식될 수 있다.

### LCC 선택과 `stats[1:, ...]`

`cv2.connectedComponentsWithStats`는 label 0을 배경으로 예약한다. 따라서 `stats[1:]`로 label 1부터 슬라이싱하여 유방 후보군만 비교한 후, 가장 넓은 영역의 label을 유방으로 확정한다.

---

## ④ Peripheral Thickness Compensation — `compensate_peripheral_thickness()`

### 문제의 물리적 배경 — Wedge Effect

로그 선형화 후에도 유방 외곽부가 어두운 이유:

```
유방 단면 두께 분포

       ████████████████████
    ████████████████████████
  ██████████████████████████████
 ████████████████████████████████
────────────────────────────────────
  ←외곽(얇음)→    ←중앙(두꺼움)→   ←외곽(얇음)→
  t 작음          t 큼              t 작음
  μt 작음         μt 큼             μt 작음
  log 값 낮음     log 값 높음       log 값 낮음
```

Beer-Lambert 변환 후 `log(I₀/I) = μt`이므로 픽셀값은 두께 자체에 비례한다. 즉 **외곽의 얇은 부분은 두께가 작아서 어둡게** 나온다. 이것은 정보의 손실이 아니라 물리적으로 정확한 표현이지만, 임상적으로는 외곽 조직의 세부 구조가 어두워 판독이 어렵게 되는 문제다.

---

### 두께 맵 추정: Normalized Convolution

외곽 두께 구배를 추정하기 위해, 수학적으로 다음을 계산한다:

$$\hat{T}(x, y) = \frac{\displaystyle\sum_{(i,j)} G_\sigma(x-i, y-j)\cdot M(i,j)\cdot I(i,j)}{\displaystyle\sum_{(i,j)} G_\sigma(x-i, y-j)\cdot M(i,j)}$$

- $G_\sigma$: 표준편차 $\sigma$인 가우시안 커널 (반경 radius=300에서 $\sigma \approx 45$)
- $M(i,j)$: 마스크 (1 = 유방, 0 = 배경)
- $I$: 로그 선형화된 픽셀값

**직관**: 마스크 내부 픽셀값만을 가우시안 가중 평균한 것으로, 대형 커널(300px)을 사용하면 고주파 세부구조는 평활화되고 **저주파 두께 구배만** 남는다. 이것이 바로 두께 맵 $\hat{T}$의 추정값이다.

```python
numer = cv2.GaussianBlur(img_ds * mask_f, ...)   # Σ G·M·I (분자)
denom = cv2.GaussianBlur(mask_f,          ...)   # Σ G·M   (분모)
thick_ds = numer / (denom + 1e-6)               # Normalized Convolution
```

---

### 경계 불안정성: DENOM_THRESH = 0.15

마스크 경계 근방에서 분모 $\sum G \cdot M$이 0에 가까워진다. 가우시안 커널의 유효 범위 내에 마스크 내부 픽셀이 거의 없기 때문이다.

```
마스크 경계에서 분모(denom)의 거동:

  |마스크 내부|  경계 →  |배경|
  denom ≈ 1.0    denom → 0    denom ≈ 0
  안정             불안정       0
```

분모가 0에 가까우면 `numer/denom → ∞`로 발산하고, 이것이 경계에서 밝은 링(Halo)을 만든다.

**해결책**: `DENOM_THRESH = 0.15`보다 작은 픽셀을 "경계 불안정 픽셀"로 판정하고, 0 대신 유효 영역의 `median`값으로 채운다.

```python
DENOM_THRESH = 0.15
valid_vals = numer[denom > DENOM_THRESH] / (denom[denom > DENOM_THRESH] + 1e-6)
fill_val = float(np.median(valid_vals))   # 안전한 중앙값으로 대체
thick_ds = np.where(denom > DENOM_THRESH,
                    numer / (denom + 1e-6),   # 안정 영역: 정규화 결과
                    fill_val)                 # 불안정 경계: median으로 보간
```

**0 대신 median을 쓰는 이유**:  
`fill_val = 0`으로 하면 이후 보정식 `correction = clip(T - T_ref, None, 0)` 에서 `0 - T_ref < 0`이 되어 해당 픽셀을 지나치게 밝게 올리는 과보정(Halo)이 발생한다. median 값은 T_ref에 가깝기 때문에 correction ≈ 0이 되어 경계부에서 보정이 자연스럽게 소멸한다.

---

### 보정 방향: 단방향 클리핑

```python
t_ref = np.percentile(fg_pixels, 90)        # 두꺼운 중앙부 기준값
correction = np.clip(thickness_map - t_ref, None, 0.0)   # 음수만 허용
compensated = img_f - correction            # 음수를 빼면 밝아짐
```

보정량의 부호를 도식화하면:

```
두께(T_map) vs 기준(T_ref = p90):

  외곽부: T_map < T_ref  →  T_map - T_ref < 0  →  correction < 0
                          →  img - correction  = img + |correction|  ← 밝아짐 ✓

  중앙부: T_map ≈ T_ref  →  T_map - T_ref ≈ 0  →  correction ≈ 0
                          →  img - 0  = img (무보정)                   ✓

  T_map > T_ref          →  clip(..., None, 0) = 0  →  보정 없음       ✓
```

**T_ref를 p90으로 설정하는 이유**: 평균이나 중앙값(p50)으로 하면 유방 중앙부까지 보정 대상이 되어 과보정된다. p90은 "충분히 두꺼운 조직"을 기준으로 삼아, 그보다 **얇은 외곽 쐐기 부분만** 선택적으로 올리는 동작을 보장한다.

---

### 4배 다운샘플링 전략

```python
img_ds  = cv2.resize(img_f, (w_ds, h_ds), interpolation=cv2.INTER_AREA)
# ...
thickness_map = cv2.resize(thick_ds, (w, h), interpolation=cv2.INTER_LINEAR)
```

두께 맵은 저주파 성분만 필요하므로 1/4 해상도에서 계산해도 정밀도 손실이 없다. 반면 가우시안 블러의 연산량은 `O(hw·σ)`에 비례하므로:

- Full resolution (3816×3048, σ≈45): 약 16배 연산  
- 1/4 해상도 (954×762, σ≈11): 1배 연산  

→ **약 16배 연산 절감**, 최종 업샘플 결과는 시각적으로 동일.
