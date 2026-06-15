# X-ray의 성질과 감쇠

!!! abstract "요약"
    이 페이지는 X-ray의 생성 메커니즘(제동복사와 특성 X-ray), 에너지 스펙트럼과 kVp의 의미, 물질과의 상호작용(광전효과·콤프턴 산란), 그리고 감쇠의 지수 법칙(Beer–Lambert law)을 정리한다. 다색(polychromatic) 빔에서의 beam hardening과 대조도(subject contrast)의 정의를 다루며, 검출 신호가 두께·밀도에 지수적으로 변하는 이유가 어떻게 후속 처리의 log 변환 동기로 이어지는지 설명한다. 검출 측 비선형성은 [디지털 디텍터](detector.md), log 선형화의 구현은 [특성 곡선과 LUT](../image-formation/characteristic-curves.md)로 연결한다.

## X-ray의 생성

X-ray tube에서 가속된 전자가 표적(target)에 충돌하면 두 가지 기전으로 X-ray가 방출된다.

### 제동복사 (bremsstrahlung)

입사 전자가 표적 원자핵의 쿨롱장(Coulomb field)에서 감속·편향되며 에너지를 잃고, 그 손실분이 X-ray 광자로 방출된다. 광자 에너지는 0부터 입사 전자의 운동에너지(즉 관전압 $eV_{\text{tube}}$)까지 **연속 스펙트럼(continuous spectrum)**을 이룬다. 따라서 최대 광자 에너지는 kVp(kilovolt peak)로 결정된다.

### 특성 X-ray (characteristic radiation)

입사 전자가 표적 원자의 내각(inner shell) 전자를 방출시키면, 상위 각의 전자가 그 빈자리를 채우며 두 준위의 에너지 차에 해당하는 광자를 방출한다. 이 에너지는 표적 물질에 고유한 **이산 선(discrete lines)**으로 나타난다. 예를 들어 Mo 표적은 약 17.5, 19.6 keV의 특성선을 내며, 이 선들이 유방촬영용 [준단색 스펙트럼](system.md)의 핵심을 이룬다.

### 에너지 스펙트럼과 kVp

실제 빔은 제동복사 연속 성분 위에 특성선이 겹쳐진 **다색(polychromatic)** 스펙트럼이다.

- **kVp**: 스펙트럼의 최대 광자 에너지와 평균 에너지를 함께 끌어올린다. 높을수록 투과력이 커지고 대조도는 낮아진다.
- **필터(filtration)**: 저에너지 성분을 제거(beam hardening)해 평균 에너지를 높이고 환자 선량을 줄인다.

## 물질과의 상호작용

진단 X-ray 에너지 대역에서 광자는 주로 두 기전으로 물질과 상호작용한다.

### 광전효과 (photoelectric effect)

광자가 내각 전자에 모든 에너지를 넘겨 흡수되는 과정으로, 단면적은 대략

$$
\tau \propto \frac{Z^{3}}{E^{3}}
$$

로 원자번호 $Z$의 세제곱에 비례하고 광자 에너지 $E$의 세제곱에 반비례한다(근사). 유방촬영의 저에너지 대역에서 광전효과는 **대조도의 핵심 원천**이다. 에너지가 낮을수록, 그리고 조직 간 실효 원자번호 차이가 있을수록 흡수 차이가 커져 지방과 섬유선조직, 그리고 칼슘(미세석회)의 대조도가 뚜렷해진다.

!!! tip "왜 미세석회가 잘 보이는가"
    칼슘은 연조직보다 실효 원자번호가 높다. $\tau \propto Z^3$ 이므로 저에너지에서 칼슘의 광전 흡수가 두드러져, 미세석회화가 주변 연조직 대비 높은 [대조도](#subject-contrast)로 나타난다. 이것이 저 kVp 촬영이 미세석회 검출에 유리한 물리적 이유다.

### 콤프턴 산란 (Compton scattering)

광자가 외각 전자와 비탄성 충돌해 일부 에너지를 잃고 방향을 바꾸는 과정이다. 에너지·$Z$ 의존성이 약해 대조도에는 거의 기여하지 못하고, 오히려 [산란선(scatter)](system.md)으로 1차 영상 위에 배경 흐림을 더해 대조도를 떨어뜨린다. 그래서 anti-scatter grid로 제거한다.

## 감쇠의 지수 법칙: Beer–Lambert law

두께 $t$의 균일한 물질을 입사 강도 $I_0$의 단색 빔이 통과할 때, 투과 강도 $I$는 지수적으로 감쇠한다.

$$
I = I_0\, e^{-\mu t}
$$

여기서 $\mu$는 **선감쇠계수(linear attenuation coefficient)** $[\text{cm}^{-1}]$로, 물질·광자 에너지에 의존하며 위의 광전·콤프턴 등 모든 상호작용 단면적의 합으로 정해진다. 물질이 여러 층($\mu_i, t_i$)으로 이루어진 경우 지수는 합으로 누적된다.

$$
I = I_0 \exp\!\left(-\sum_i \mu_i t_i\right)
$$

!!! note "핵심: 신호는 두께에 선형이 아니라 지수적이다"
    검출되는 강도 $I$는 두께 $t$에 **선형으로 비례하지 않고 지수적으로 감소**한다. 따라서 RAW 신호를 그대로 쓰면 두꺼운 영역과 얇은 영역이 매우 비대칭한 동적 범위를 차지한다. 반대로 로그를 취하면
    $$
    \log\!\left(\frac{I_0}{I}\right) = \mu t
    $$
    로 **두께(또는 감쇠량)에 선형**인 양을 얻는다. 이것이 후속 파이프라인에서 $\log(I_0/I)$ 형태의 [log 선형화](../image-formation/characteristic-curves.md)를 수행하는 물리적 근거다.

### 다색 빔과 beam hardening

실제 빔은 다색이므로 $\mu$가 에너지에 의존하고, 식은 스펙트럼 $S(E)$에 대한 적분이 된다.

$$
I = \int S(E)\, e^{-\mu(E)\,t}\, dE
$$

저에너지 광자가 고에너지 광자보다 먼저 흡수되므로, 빔이 물질을 통과할수록 평균 에너지가 올라가는 **beam hardening**이 일어난다. 그 결과 유효 $\mu$가 두께에 따라 감소해, 단색 가정의 순수한 지수 관계에서 벗어나는 비선형 편차가 생긴다. 이는 RAW로부터 $\mu t$ 를 추정할 때의 모델 오차 원인이며, 두꺼운 중심부에서 특히 두드러진다.

## 대조도 (subject contrast)

피사체 대조도는 인접한 두 영역에서 검출 강도가 얼마나 다른가로 정의된다. 흔히 쓰는 정규화 형태는 다음과 같다.

$$
C = \frac{I_1 - I_2}{I_1 + I_2}
$$

두 영역이 각각 두께·감쇠 $\mu_1 t_1,\ \mu_2 t_2$ 를 가지면 $I_k = I_0 e^{-\mu_k t_k}$ 이므로, 대조도는 두 영역의 감쇠 차이 $\Delta(\mu t)$ 에 의해 결정된다. $\mu$가 저에너지에서 더 크게 벌어지므로(광전효과) 저 kVp일수록 $C$가 커진다 — 다만 [선량 증가](system.md)라는 대가가 따른다.

!!! abstract "물리에서 처리로 이어지는 논리"
    1. 감쇠는 지수적($I = I_0 e^{-\mu t}$) → 신호 동적 범위가 비대칭.
    2. 로그 변환 $\log(I_0/I) = \mu t$ → 감쇠량에 선형인 표현 확보.
    3. 그 위에서 톤 압축·국소 대조도 강조를 수행해야 종괴와 미세석회를 동시에 가시화.

    detector가 RAW로 내보내는 값의 비선형성(특히 두께 대비)은 [디지털 디텍터와 신호의 비선형성](detector.md)에서, 그 선형화의 구체적 구현과 LUT는 [특성 곡선](../image-formation/characteristic-curves.md)에서 다룬다.

## 참고문헌

- J. T. Bushberg, J. A. Seibert, E. M. Leidholdt, J. M. Boone, *The Essential Physics of Medical Imaging*, 3rd ed., Lippincott Williams & Wilkins, 2011.
- H. E. Johns, J. R. Cunningham, *The Physics of Radiology*, 4th ed., Charles C. Thomas, 1983.
- J. H. Hubbell, S. M. Seltzer, "Tables of X-Ray Mass Attenuation Coefficients," NIST Standard Reference Database 126.
- ICRU Report 44, *Tissue Substitutes in Radiation Dosimetry and Measurement*, 1989.
- R. Birch, M. Marshall, "Computation of bremsstrahlung X-ray spectra," *Physics in Medicine and Biology*, 24(3):505, 1979.
