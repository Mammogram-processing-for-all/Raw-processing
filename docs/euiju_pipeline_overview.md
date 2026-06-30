# 맘모그래피 전처리 파이프라인 — 아키텍처 요약

> [전체 코드](ejheo_mammo.py) | [Module A](docs/euiju_module_a_analysis.md) | [Module B](docs/euiju_module_b_analysis.md) | [Module C](docs/euiju_module_c_analysis.md)

## 1. 파이프라인 전체 흐름 (High-level Overview)

```
                         ejheo_mammo.py  전체 파이프라인
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────┐      ║
║  │  Module I/O — 데이터 적재·저장                                        │      ║
║  │  목적: RAW/DICOM 파일 쌍 적재 및 처리 결과의 DICOM 재포장                │      ║
║  │  ─────────────────────────────────────────────────────────────────  │     ║
║  │  load_mammography_data()       → RAW uint16 + DICOM 메타데이터        │     ║
║  │  save_as_presentation_dicom()  → 처리 완료 uint16 → DICOM 저장        │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║          │                                                   ▲               ║
║          ▼                                                   │               ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │  Module A — 물리 신호 선형화  (stage_for_processing)                  │     ║
║  │  목적: 지수 응답의 RAW 신호를 Beer-Lambert 기반 로그 선형화하여           │     ║
║  │       두께에 비례하는 선형 도메인으로 변환                               │     ║
║  │  ─────────────────────────────────────────────────────────────────  │     ║
║  │  ① estimate_illumination_map()       → I₀ 공간 맵                   │     ║
║  │  ② apply_log_linearization()         → log(I₀/I) uint16            │     ║
║  │  ③ get_breast_mask()                 → 이진 마스크                   │     ║
║  │  ④ compensate_peripheral_thickness() → Wedge 보정 uint16            │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║          │  compensated_raw, mask                                            ║
║          ▼                                                                   ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │  Module B — 3-Tier 주파수 분해  (stage_decomposition)                 │     ║
║  │  목적: Cascaded Guided Filter로 Global/Regional/Detail 3개 주파수    │     ║
║  │       대역으로 분해하여 독립적 톤 제어의 기반 마련                       │     ║
║  │  ─────────────────────────────────────────────────────────────────  │     ║
║  │  ① _guided_filter_masked()  ×2       → mid_layer, global_layer      │     ║
║  │  ② 차분 연산                          → regional_layer, detail_layer │     ║
║  │  ③ _build_laplacian_pyramid()        → 라플라시안 피라미드 증폭         │     ║
║  │  ④ Edge Fade                         → 경계 아티팩트 억제              │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║          │  global_layer, regional_layer, enhanced_detail                    ║
║          ▼                                                                   ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │  Module C — 톤 매핑 & 최종 렌더링  (stage_for_presentation)            │     ║
║  │  목적: 3-Tier 레이어의 선형 융합 + 비선형 톤 압축으로                     │     ║
║  │       임상 판독에 최적화된 For-Presentation 영상 생성                   │     ║
║  │  ─────────────────────────────────────────────────────────────────  │     ║
║  │  ① Global 억제 + Regional/Detail 증폭 → 선형 융합                      │     ║
║  │  ② Black Point Clipping               → 히스토그램 하단 제거           │     ║
║  │  ③ Differential Tone Compression      → 배경 감마 + 미세구조 보존      │     ║
║  │  ④ CLAHE (Masked)                     → 국소 대비 균등화              │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║          │                                                                   ║
║          ▼                                                                   ║
║      final_img (uint16) — For-Presentation DICOM 출력                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. 모듈 간 데이터 흐름 요약

| 단계 | 입력 | 출력 | 도메인 변환 |
|------|------|------|-------------|
| **I/O** | `.raw` + `.dcm` 파일 | `raw_array` (uint16, 3816×3048) | 디스크 → 메모리 |
| **Module A** | `raw_array` | `compensated_raw` (uint16), `mask` (uint8) | 지수 도메인 → 선형 도메인 (Beer-Lambert) |
| **Module B** | `compensated_raw`, `mask` | `global`, `regional`, `enhanced_detail` (float32) | 단일 신호 → 3-Tier 주파수 분해 |
| **Module C** | 3개 레이어, `mask` | `final_img` (uint16) | 선형 분해 → 비선형 톤 매핑 (판독 최적화) |

---

## 3. 모듈별 상세 분석 문서 링크

| 모듈 | 문서 | 핵심 함수 |
|------|------|-----------|
| Module A | [module_a_analysis.md](docs/euiju_module_a_analysis.md) | `stage_for_processing()` |
| Module B | [module_b_analysis.md](docs/euiju_module_b_analysis.md) | `stage_decomposition()` |
| Module C | [module_c_analysis.md](docs/euiju_module_c_analysis.md) | `stage_for_presentation()` |

---

## 4. 설계 철학: 왜 3-Tier 분해인가?

맘모그래피 판독의 핵심 과제는 **동적 범위 문제**다. 

- 유방 중앙부(두꺼운 조직)와 외곽부(얇은 조직)의 X-ray 감쇠 차이가 극도로 크다.  
- 미세석회화(Calcification)나 종괴(Mass) 같은 진단 핵심 구조는 이 거대한 두께 구배 위에 미세한 신호로 존재한다.

단순 윈도우/레벨링으로는 두께 구배를 억제하면서 동시에 미세 구조를 강조할 수 없다.  
3-Tier 분해는 이 문제를 **주파수 영역에서 해결**한다:

| Tier | 주파수 대역 | 물리적 대응 | 처리 전략 |
|------|------------|------------|----------|
| Global | 초저주파 | 유방 두께 구배 | **억제** (equalization) |
| Regional | 중간 주파수 | 국소 조직 밀도 | **증폭** (gain) |
| Detail | 고주파 | 미세석회화, 혈관벽 | **선택적 증폭** (라플라시안 피라미드) |
