# Lesion Types

Mammography 병변은 BI-RADS 어휘를 기준으로 네 가지 큰 유형으로 분류된다. 같은 4유형이 AI 탐지(detection) 모델의 클래스 구조에도 그대로 반영된다.

| 유형 | 영문 | 한 줄 요약 | AI 난이도 |
|------|------|-----------|----------|
| 종괴 | Mass | 형태+변연으로 양성/악성 감별 | 중간 |
| 미세석회화 | Microcalcification | DCIS의 90%가 이 소견으로 발견 | 중간~높음 |
| 구조왜곡 | Architectural Distortion | 종괴 없이 유선 패턴이 왜곡 | 높음 |
| 비대칭 | Asymmetry | developing asymmetry가 임상적으로 중요 | 높음 |

## 1. 종괴 (Mass)

3D 공간을 차지하는 병변. 두 뷰 모두에서 보여야 진짜 종괴로 간주한다.

### 형태 (Shape)

| 형태 | 양성/악성 경향 |
|------|--------------|
| Round | 양성 경향 (낭종·섬유선종) |
| Oval | 양성 경향 |
| Irregular | **악성 의심** |

### 변연 (Margin) — 가장 중요한 단서

| 변연 | 의미 | 악성 PPV |
|------|------|-----------|
| Circumscribed | 경계가 분명하고 매끄러움 | 낮음 (양성 경향) |
| Microlobulated | 작은 결절성 굴곡 | 중간 |
| Obscured | 인접 조직에 의해 가려짐 | 평가 보류 |
| Indistinct | 경계가 흐릿함 | 중간~높음 |
| **Spiculated** | 침상으로 뻗는 선들 | **~96%** |

스피큘레이션(spiculation)은 단일 소견 중 악성 PPV가 가장 높다. 미세석회화와 결합되면 추가 정밀진단 없이 BI-RADS 5로 직행하기도 한다.

### 밀도 (Density)

조직보다 같거나 더 밀(dense)할수록 악성 가능성이 올라간다. 지방을 포함한 종괴는 거의 양성.

## 2. 미세석회화 (Microcalcification)

직경 < 0.5 mm의 칼슘 침착. **DCIS(관상피내암, ductal carcinoma in situ)의 90%가 이 소견으로 발견**되므로 조기 발견의 핵심.

### 형태 (Morphology)

| 형태 | 양성/악성 경향 |
|------|--------------|
| Round / Punctate | 양성 경향 |
| Amorphous | 중간 |
| Coarse heterogeneous | 중간 |
| Fine pleomorphic | **악성 의심** |
| **Fine linear / branching** | **악성 의심 (악성률 ~70%)** |

미세선형/분지형은 관(duct)을 따라 형성되는 칼슘 침착으로 DCIS의 특이 소견이다.

### 분포 (Distribution)

| 분포 | 임상적 의미 |
|------|----------|
| Diffuse | 양 유방 전체 — 양성 경향 |
| Regional | 한 사분면 이상의 큰 영역 |
| Grouped (clustered) | 1 cm³ 안에 ≥5개 — 평가 필요 |
| Linear | 관을 따라 — 악성 의심 |
| Segmental | 한 관계(ductal system) 전체 — **악성 의심** |

## 3. 구조왜곡 (Architectural Distortion, AD)

종괴는 보이지 않지만 유선 패턴이 비정상적으로 수렴·왜곡되는 소견. 가장 미묘하고 가장 놓치기 쉬운 병변.

### 핵심 단서

- 별 모양으로 수렴하는 침상(spiculations) — 종괴 중심 없이
- 국소 견인(retraction)
- 비대칭과 동반될 때 의심도 ↑

### 임상적 의미

- 악성률은 케이스에 따라 10~60%로 큰 변동
- **방사상 흉터(radial scar)** — 양성이지만 영상에서 AD와 거의 구별이 안 됨 → 조직검사가 필요
- DBT(3D 토모신세시스)가 2D보다 큰 이점을 보이는 대표 케이스

## 4. 비대칭 (Asymmetry)

좌·우 또는 같은 유방 내에서 정상 패턴과 다른 영역.

### 4가지 하위 분류

| 유형 | 정의 | 악성률 |
|------|------|-------|
| Asymmetry | 한 뷰에서만 보이는 비대칭 | 낮음 (대부분 조직 겹침) |
| Global asymmetry | 한 사분면 이상의 큰 영역, 두 뷰 모두 | 낮음~중간 |
| Focal asymmetry | 작은 영역(<1사분면), 두 뷰 모두 | 중간 |
| **Developing asymmetry** | **이전 영상 대비 새로 나타나거나 커진 비대칭** | **최대 ~27%** |
