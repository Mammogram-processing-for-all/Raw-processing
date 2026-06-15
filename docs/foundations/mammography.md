# 맘모그램의 개념과 임상적 배경

!!! abstract "요약"
    이 페이지는 유방촬영술(mammography)의 정의와 임상적 목적, 정상 유방의 방사선학적 구성, 그리고 영상에서 찾아내야 할 핵심 소견(종괴, 미세석회화, 구조 왜곡, 비대칭)을 정리한다. 표준 촬영 자세와 BI-RADS 판독 체계를 간단히 소개하고, 왜 저대조도 병변과 미세석회를 동시에 보여 주어야 하는 과제가 영상 처리(image processing)를 임상적으로 필수적인 단계로 만드는지 설명한다.

## 유방촬영술이란

유방촬영술(mammography)은 저에너지 X-ray를 이용해 유방의 연조직(soft tissue)을 영상화하는 투과 영상(projection imaging) 기법이다. 일반적인 흉부·골격 촬영과 달리 유방은 거의 전부가 연조직(지방, 섬유선조직)으로 구성되어 있어 구성 조직 간 감쇠 차이가 매우 작다. 따라서 미세한 [대조도(subject contrast)](xray-physics.md)를 끌어내기 위해 25~32 kVp 수준의 낮은 관전압과 Mo/Rh/W 계열의 특수 표적·필터 조합을 사용한다. 장비 구조의 세부는 [유방촬영 장비의 기본 구조](system.md)에서 다룬다.

목표는 임상적으로 의미 있는 두 종류의 정보를 동시에 보존하는 것이다.

- **저주파(low-frequency) 대조도**: 종괴(mass)·비대칭처럼 넓은 영역에 걸친 미묘한 밝기 차이.
- **고주파(high-frequency) 세부**: 미세석회화(microcalcification)처럼 수십~수백 µm 크기의 작은 고대비 구조.

이 두 요구가 본질적으로 상충(trade-off)하기 때문에, 단순 선형 표시로는 진단에 충분하지 않고 다중 스케일(multi-scale) 처리가 필요하다.

## 임상적 목적: 선별검사와 진단검사

=== "선별검사 (Screening)"

    무증상(asymptomatic) 인구를 대상으로 유방암을 조기 발견하기 위해 정기적으로 시행한다. 표준적으로 양측 유방에 대해 CC와 MLO 두 뷰를 촬영한다. 검출 민감도(sensitivity)와 위양성(false positive)률의 균형, 그리고 낮은 선량(low dose)이 핵심 요구 사항이다.

=== "진단검사 (Diagnostic)"

    증상이 있거나 선별검사에서 이상 소견이 발견된 환자를 대상으로, 병변을 정밀하게 특성화하기 위해 추가 뷰(확대 magnification, 압박 촬영 spot compression)나 다른 modality(초음파, MRI)와 병행해 시행한다.

!!! note "조기 발견의 임상적 가치"
    유방암은 조기에 발견될수록 생존율과 치료 선택지가 극적으로 개선된다. 특히 침윤성 병변으로 진행하기 전 단계인 관상피내암(DCIS, ductal carcinoma in situ)은 흔히 미세석회화 군집으로만 나타나며, 다른 임상적 징후가 없다. 즉 미세석회를 영상에서 안정적으로 드러내는 능력이 곧 조기 발견 능력과 직결된다.

## 정상 유방의 방사선학적 구성

유방 실질(parenchyma)은 방사선학적으로 크게 두 성분으로 환원된다.

| 조직 | 상대적 X-ray 감쇠 | 영상에서의 외관 |
| --- | --- | --- |
| 지방조직(adipose/fatty tissue) | 낮음 | 어둡게(투과 많음) 보임 — radiolucent |
| 섬유선조직(fibroglandular tissue) | 높음 | 밝게(투과 적음) 보임 — radiodense |

저에너지 대역에서 두 조직 사이의 [감쇠 계수](xray-physics.md) 차이는 작지만 0은 아니며, 이 작은 차이가 유방 실질 패턴(parenchymal pattern)으로 나타난다.

### 유방 밀도(breast density)

유방 밀도는 전체 유방 부피 중 섬유선조직이 차지하는 비율을 가리킨다. 밀도가 높을수록(dense breast) 두 가지 임상적 문제가 생긴다.

1. **마스킹 효과(masking effect)**: 밝게 보이는 섬유선조직이 같은 정도로 밝은 종괴를 가려 검출 민감도를 떨어뜨린다.
2. **위험 인자**: 높은 밀도 자체가 유방암의 독립적 위험 인자로 보고된다.

BI-RADS는 유방 밀도를 a(거의 지방)부터 d(극도로 치밀)까지 4단계로 분류한다. 밀도가 높은 유방일수록 영상 처리에서 국소 대조도(local contrast) 강조가 더 중요해진다.

## 핵심 소견(key findings)

판독 시 찾아야 할 대표적 비정상 소견은 다음과 같다.

??? info "종괴 (Mass)"
    3차원 공간을 점유하는 병변으로, 서로 다른 두 뷰에서 모두 관찰될 때 신뢰할 수 있다. 형태(shape: 원형/타원형/불규칙), 경계(margin: 경계 명확/미세분엽/침상 spiculated), 밀도로 특성화한다. 침상 경계(spiculation)는 악성을 강하게 시사한다. 종괴는 주로 **저주파~중간 주파수** 대조도 정보로 표현된다.

??? info "미세석회화 (Microcalcification)"
    칼슘 침착으로 인한 작고 밝은 점으로, 크기는 대략 **수십~수백 µm**에 불과하다. 형태(다형성 pleomorphic, 미세선상 fine linear branching)와 분포(군집 clustered, 선상 linear, 분절 segmental)가 악성 여부 판단에 핵심이다. 미세하고 고대비이므로 **고주파(high-frequency) 정보**로 표현되며, 검출은 detector의 [공간 해상도(MTF)](../image-quality/metrics.md)와 고주파 강조 처리에 결정적으로 의존한다.

??? info "구조 왜곡 (Architectural distortion)"
    뚜렷한 종괴 없이 유방 실질의 정상적인 방사상 구조가 한 점으로 끌려 들어가거나 왜곡된 상태. 미묘하고 배경 패턴에 묻히기 쉬워, 국소 대조도와 방향성 구조의 보존이 검출에 중요하다.

??? info "비대칭 (Asymmetry)"
    양측 유방을 비교하거나 한 유방 내 영역을 비교했을 때 나타나는 조직 분포의 불균형. 진성 비대칭(true asymmetry), 국소 비대칭(focal asymmetry), 발달 비대칭(developing asymmetry)으로 구분한다.

## 표준 촬영 자세(view)

선별검사의 표준 조합은 각 유방당 두 뷰이다.

- **CC (craniocaudal, 상하방향)**: 위에서 아래로 압박·촬영. 내측(medial)과 외측(lateral) 실질을 잘 보여 준다.
- **MLO (mediolateral oblique, 내외사위방향)**: 약 45° 사위 방향으로 촬영. 흉근(pectoral muscle)과 상부 외측(upper outer quadrant)을 포함해 유방 조직을 가장 넓게 포괄하는 뷰이다.

두 뷰를 함께 보는 이유는, 한 뷰에서만 보이는 소견은 조직 겹침(superimposition)에 의한 가짜 소견일 수 있으나 서로 다른 투영 방향에서 모두 확인되면 실제 병변일 가능성이 높기 때문이다.

## BI-RADS 판독 체계

BI-RADS(Breast Imaging Reporting and Data System)는 미국방사선학회(ACR)가 표준화한 보고·평가 체계로, 판독 결과를 다음 범주로 분류한다.

| 범주 | 의미 | 권고 |
| --- | --- | --- |
| 0 | 불완전 — 추가 영상 필요 | 추가 검사 |
| 1 | 음성(negative) | 정기 검진 |
| 2 | 양성(benign) 소견 | 정기 검진 |
| 3 | 양성 추정(probably benign) | 단기 추적 |
| 4 | 의심(suspicious) | 조직 검사 고려 |
| 5 | 악성 강력 시사 | 조직 검사 |
| 6 | 조직학적으로 확인된 악성 | 임상적 처치 |

BI-RADS는 또한 영상 품질과 유방 밀도 기술을 표준화하여, 영상 처리 파이프라인이 만족해야 할 일관성(consistency) 요구의 임상적 근거가 된다.

## 왜 영상 처리가 임상적으로 중요한가

원시 검출 신호(RAW)는 [Beer–Lambert 법칙](xray-physics.md)에 따라 조직 두께와 감쇠에 **지수적으로** 의존하므로, 그대로 표시하면 동적 범위(dynamic range)가 한쪽으로 치우쳐 진단 정보가 묻힌다. 임상적 과제는 다음 두 요구를 한 영상에서 동시에 만족하는 것이다.

1. 넓은 동적 범위(두꺼운 중심부 ~ 얇은 변연부)를 하나의 화면 계조로 압축.
2. 그 과정에서 저대조도 종괴와 고주파 미세석회를 **모두** 시각적으로 보존.

```mermaid
flowchart LR
    A[RAW 신호<br/>지수적 동적 범위] --> B[log 선형화]
    B --> C[다중 스케일 분해<br/>global / regional / detail]
    C --> D[톤 압축 + 국소 대조도 강조]
    D --> E[for-presentation 영상<br/>종괴 + 미세석회 동시 가시화]
```

특히 미세석회 검출이 고해상도·고주파 강조와 직결되는 이유는, 미세석회의 신호가 수십~수백 µm 규모의 작은 공간 주파수 성분에 집중되어 있어 톤 압축 과정에서 쉽게 손실되기 때문이다. 따라서 [처리 기법](../techniques/index.md)에서는 신호를 [특성 곡선](../image-formation/characteristic-curves.md)을 통해 선형화한 뒤, 다중 스케일로 분해하여 고주파 detail 계층을 별도로 강조하는 전략을 취한다.

## 참고문헌

- J. T. Bushberg, J. A. Seibert, E. M. Leidholdt, J. M. Boone, *The Essential Physics of Medical Imaging*, 3rd ed., Lippincott Williams & Wilkins, 2011.
- American College of Radiology, *ACR BI-RADS Atlas: Breast Imaging Reporting and Data System*, 5th ed., 2013.
- N. F. Boyd et al., "Mammographic Density and the Risk and Detection of Breast Cancer," *New England Journal of Medicine*, 356(3):227–236, 2007.
- M. J. Yaffe, "Mammographic density. Measurement of mammographic density," *Breast Cancer Research*, 10(3):209, 2008.
- IAEA, *Quality Assurance Programme for Digital Mammography*, IAEA Human Health Series No. 17, 2011.
