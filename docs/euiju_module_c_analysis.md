# Module C — 톤 매핑 & 최종 렌더링: 4단계 원리 분석
### `stage_for_presentation()` 실행 흐름

```
global_layer  +  regional_layer  +  enhanced_detail  +  mask
   │
   ①  선형 융합 (Global 억제 + Regional/Detail 증폭)
   │     → fused_float (float32)
   │
   ②  Black Point Clipping (하위 3% 절단)
   │     → fused_norm [0, 1]
   │
   ③  Differential Tone Compression
   │     (배경 Gamma 압축 + 미세구조 1.5× 보존)
   │     → fused_norm [0, 1]
   │
   ④  CLAHE (Masked, 16-bit)
   │     → final_img_out (uint16)
   │
   ▼
final_img (uint16)  — For-Presentation DICOM 출력
  +  base_img (uint16)    — Suppressed Global 참조용
  +  for_proc_img (uint16) — For-Processing 선형 융합 참조용
```

---

## ① 선형 융합 — 3-Tier 가중합

### 수학적 표현

$$F(x,y) = (1 - \alpha)\cdot G(x,y) \;+\; g_r \cdot R(x,y) \;+\; g_d \cdot D(x,y)$$

| 파라미터 | 코드 변수 | 기본값 | 역할 |
|---------|-----------|--------|------|
| $\alpha$ | `equalization_alpha` | 0.60 | Global 억제 강도 (1이면 완전 제거) |
| $g_r$ | `regional_gain` | 1.1 | Regional 증폭 배율 |
| $g_d$ | `detail_gain` | 2.0 | Enhanced Detail 증폭 배율 |

### 각 항의 물리적 의미

```python
suppressed_global  = global_layer * (1.0 - equalization_alpha)   # 두께 구배 60% 억제
amplified_regional = regional_layer * regional_gain               # 국소 조직 밀도 1.1× 증폭
fused_float        = suppressed_global + amplified_regional + (enhanced_detail * detail_gain)
```

**Global 억제 (`1 − α`)**:  
Module B에서 분리된 global_layer는 유방 전체의 두께 구배(초저주파)를 담고 있다. 이 성분을 `(1 − α)` 배로 줄이면 두꺼운 중앙부와 얇은 외곽부의 밝기 차이가 축소된다. 이것이 맘모그래피 판독의 핵심인 **Thickness Equalization**이다.

**α = 0.60의 의미**: 두께 구배의 60%를 억제하고 40%를 보존한다. 완전 제거(α=1.0)하면 유방의 3차원적 형태 정보가 사라져 판독의 spatial context가 소실된다. 0.60은 외곽부 가시성 확보와 형태 보존의 균형점이다.

**Regional 증폭 (gain=1.1)**: 국소 유선 밀도 차이를 미세하게 강조하되, 과도한 증폭은 조직 질감이 인위적으로 보이게 하므로 1.1×로 보수적으로 설정.

**Detail 증폭 (gain=2.0)**: 이미 라플라시안 피라미드에서 주파수별 가중치가 적용된 enhanced_detail에 추가로 2×를 적용. 미세석회화 등 진단 핵심 구조의 가시성을 극대화.

---

## ② Black Point Clipping

### 왜 필요한가?

선형 융합 후 히스토그램의 하위 영역에는 마스크 경계의 잔류 노이즈, 과보정된 외곽 픽셀 등 **진단적으로 무의미한 저밝기 픽셀**이 존재한다. 이들을 정규화 범위에 포함하면 유효 동적 범위가 낭비된다.

```python
p_min, p_max = np.percentile(valid_pixels, (3, 99.5))
fused_norm = np.clip((fused_float - p_min) / (p_max - p_min + 1e-6), 0.0, 1.0)
```

### 비대칭 Percentile의 의도

| Percentile | 값 | 의도 |
|------------|-----|------|
| 하위 3% | `p_min` | 유방 가장자리의 약한 신호는 잘라도 진단 손실 최소 |
| 상위 99.5% | `p_max` | 미세석회화 등 극히 밝은 소수 픽셀의 포화(saturation) 방지 |

**p_min(3%)을 p_max(0.5%)보다 공격적으로 설정하는 이유**: 저밝기 방향의 노이즈/잔류물이 고밝기 방향의 진단 구조보다 많기 때문. 상위 0.5%를 클리핑하면 미세석회화가 손상될 수 있으므로 보수적.

---

## ③ Differential Tone Compression (DTC)

### 핵심 발상: 배경과 미세구조를 분리 압축

단순 Gamma 보정의 문제: $\text{out} = \text{in}^\gamma$ ($\gamma > 1$) 를 전체에 적용하면 배경(저주파)과 미세구조(고주파)가 **동일 비율로 압축**되어, 미세 구조의 대비가 함께 감소한다.

DTC는 이 문제를 **주파수 분리**로 해결한다:

```
fused_norm
    │
    ├─ GaussianBlur(σ=20) → smooth_bg (저주파 배경)
    │
    └─ fused_norm − smooth_bg → fine_str (고주파 미세구조)
    
smooth_bg^γ × 0.85  +  fine_str × 1.5  →  최종 합성
```

### 수학적 모델

$$\text{out}(x,y) = \underbrace{[S(x,y)]^\gamma \cdot 0.85}_{\text{배경 압축}} + \underbrace{F(x,y) \cdot 1.5}_{\text{미세구조 증폭}}$$

여기서:
- $S(x,y) = G_{\sigma=20} * \text{fused\_norm}$ (배경 저주파 성분)
- $F(x,y) = \text{fused\_norm} - S$ (미세구조 고주파 성분)

### 각 연산의 효과

```python
smooth_bg  = cv2.GaussianBlur(fused_norm, (0, 0), sigmaX=20.0)   # 저주파 추출
fine_str   = fused_norm - smooth_bg                                # 고주파 추출

smooth_bg  = np.power(np.clip(smooth_bg, 1e-6, 1.0), gamma) * 0.85  # ⬅ 배경 비선형 압축
fused_norm = np.clip(smooth_bg + fine_str * 1.5, 0.0, 1.0)          # ⬅ 미세구조 선형 증폭 후 재합성
```

| 성분 | 연산 | 효과 |
|------|------|------|
| `smooth_bg` | $x^\gamma$ ($\gamma=1.8$) | 밝은 영역 → 어둡게, 어두운 영역 → 더 어둡게. 전체 배경 톤을 낮춰 시각적 depth 형성 |
| `smooth_bg` | $\times 0.85$ | 감마 압축 후 추가로 15% 톤 강하. 배경이 과도하게 밝으면 미세구조 가시성 저하 |
| `fine_str` | $\times 1.5$ | 미세구조의 대비를 원본 대비 1.5배 증폭. 감마 압축으로 인한 미세 대비 손실을 역보상 |

**$\gamma = 1.8$의 선택**:

| $\gamma$ | 효과 |
|----------|------|
| 1.0 | 무변환 (선형) |
| 1.8 | 중간 톤에서 약 25% 어두워짐, 고밝기에서 10% 어두워짐 → 부드러운 톤 다운 |
| 2.5 | 과도한 톤 압축 → 흉벽 영역이 과하게 어두워져 구조 소실 |

코드 주석에서 `gamma 2.5→1.8`로 변경한 이력이 있는데, 이는 흉벽 부근의 두꺼운 조직이 감마 압축에 의해 과도하게 어두워지는 문제를 완화하기 위함.

---

### σ=20의 의미

가우시안 블러의 σ=20은 약 120px(≈6σ) 유효 반경에 해당한다. 이는:
- Module B의 regional 반경(50px)보다 작으므로, regional 수준의 구조는 `smooth_bg`에 포함되어 감마 압축됨
- Module B의 detail 구조(< 50px)는 `fine_str`에 포함되어 감마 압축을 회피

→ **Module B의 3-Tier 분해와 Module C의 DTC는 상이한 주파수 분리 기준을 가진다.** Module B는 증폭/억제 비율 제어를 위한 분해이고, Module C의 DTC는 비선형 톤 압축에서의 미세구조 보호를 위한 분리이다. 두 분리는 독립적으로 설계되었으며, 서로의 역할을 대체하지 않는다.

---

## ④ CLAHE (Contrast Limited Adaptive Histogram Equalization)

### 왜 전체 영상 CLAHE가 아닌가?

전체 영상에 CLAHE를 적용하면 **배경(mask=0) 영역의 히스토그램이 유방 타일과 공유**되어 경계 타일의 CDF가 왜곡된다. 또한 배경 영역에서 노이즈가 증폭된다.

### Masked ROI 적용 전략

```python
# 유방 바운딩 박스 추출
roi_ys, roi_xs = np.where(mask > 0)
y0, y1, x0, x1 = roi_ys.min(), roi_ys.max()+1, roi_xs.min(), roi_xs.max()+1

# CLAHE를 바운딩 박스 내에서만 적용
roi_patch = fused_16bit[y0:y1, x0:x1]
clahe_patch = clahe.apply(roi_patch)

# 원본과 CLAHE 결과를 블렌딩 (마스크 내부 픽셀만)
blended_patch = cv2.addWeighted(clahe_patch, clahe_blend, roi_patch, 1.0 - clahe_blend, 0)
roi_patch[roi_mask > 0] = blended_patch[roi_mask > 0]
```

### CLAHE 파라미터 분석

| 파라미터 | 값 | 의미 |
|---------|-----|------|
| `clipLimit` | 2.0 | 각 타일의 히스토그램 최대 빈 높이. 낮을수록 대비 증폭 제한 → 노이즈 억제 |
| `tileGridSize` | (16, 16) | 적응형 영역 수. 3816px 기준 ≈ 238px/타일 |
| `clahe_blend` | 0.2 | CLAHE 결과를 20%만 혼합 |

### 블렌딩의 수학

$$\text{out} = 0.2 \cdot \text{CLAHE}(I) + 0.8 \cdot I$$

**clahe_blend = 0.2의 의도**: CLAHE는 국소 대비를 균등화하지만, 동시에 글로벌 톤 구조를 파괴한다. 20%만 혼합함으로써:
- 국소 대비 향상의 이점을 취하되 (저밀도 영역의 미세 구조 가시성 향상)
- 이전 단계(DTC)에서 구축한 전체 톤 매핑을 80% 보존

**16-bit에서 CLAHE를 적용하는 이유**: 8-bit로 다운캐스트하면 256단계로 양자화되어 맘모그래피의 미세한 밝기 차이(특히 soft tissue 대비)가 손실된다. 16-bit(65536단계)에서 직접 적용하면 양자화 노이즈 없이 대비 균등화가 수행된다.

---

## 부록: 3개의 출력 영상

`stage_for_presentation()`은 세 가지 영상을 반환한다:

| 출력 | 변수 | 용도 |
|------|------|------|
| `final_img_out` | 최종 결과 | For-Presentation: DICOM 저장·판독용 |
| `base_img_out` | Suppressed Global | 디버깅: 두께 구배 억제만 적용된 결과 확인 |
| `for_proc_img_out` | 선형 융합 | 디버깅: DTC/CLAHE 이전의 선형 융합 결과 확인 |

### For-Processing vs For-Presentation의 철학적 차이

- **For-Processing** (`for_proc_img_out`): 선형 도메인에서 정규화한 결과. 후속 알고리즘(CAD 등)의 입력으로 적합하며, 인간의 시각 특성을 고려하지 않음.
- **For-Presentation** (`final_img_out`): 비선형 톤 매핑(DTC, CLAHE)을 거쳐 인간의 시각 체계에 최적화된 결과. 방사선 전문의의 판독용.

---

## 전체 톤 파이프라인 요약: 누적 효과

```
선형 융합 후 (fused_float)
│
│  [Black Point Clip]  하위 3% 잡음 제거, 유효 동적 범위 확보
│      효과: 히스토그램 좌측 꼬리 절단
│
│  [DTC - 배경 감마]   저주파 배경을 비선형 압축
│      효과: 두꺼운 중앙부 톤 다운, 얇은 외곽부와의 밝기 차이 축소
│
│  [DTC - 미세구조 증폭]  고주파 미세구조 1.5× 증폭
│      효과: 감마 압축에 의한 미세 대비 손실 역보상
│
│  [CLAHE 20% 블렌드]  국소 적응형 대비 균등화
│      효과: 밀도 차이가 큰 영역 간의 국소 대비 균일화
│
▼
final_img — 판독 최적화 완료
```
