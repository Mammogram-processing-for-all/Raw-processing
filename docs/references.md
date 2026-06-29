# 참고문헌과 더 읽을거리

!!! abstract "요약"

    이 문서 전반에서 인용한 핵심 교재·표준·논문을 모았습니다. 각 페이지 하단의 `참고문헌` 절에 페이지별 출처가 함께 정리되어 있으니, 주제별 1차 출처는 해당 페이지를 함께 참고하세요.

## 교재 (Textbooks)

- Bushberg, J. T., Seibert, J. A., Leidholdt, E. M., Boone, J. M. *The Essential Physics of Medical Imaging*. Wolters Kluwer.
- Gonzalez, R. C., Woods, R. E. *Digital Image Processing*. Pearson.
- Beutel, J., Kundel, H. L., Van Metter, R. L. (eds.) *Handbook of Medical Imaging, Vol. 1: Physics and Psychophysics*. SPIE Press.
- Dougherty, G. *Digital Image Processing for Medical Applications*. Cambridge University Press.

## 표준·보고서 (Standards & Reports)

- DICOM PS3.14: *Grayscale Standard Display Function (GSDF)*. NEMA.
- DICOM PS3.3: *Information Object Definitions* (For Processing / For Presentation, Modality/VOI/Presentation LUT).
- IEC 62220-1: *Determination of the Detective Quantum Efficiency (DQE)*.
- IAEA Human Health Series No. 17: *Quality Assurance Programme for Digital Mammography*.
- ACR / EUREF: 유방촬영 정도관리(quality control) 프로토콜 및 팬텀(phantom) 기준.
- ICRU Report 54: *Medical Imaging — The Assessment of Image Quality*.

## 주요 논문 (Selected Papers)

### 영상 품질
- Barten, P. G. J. *Contrast Sensitivity of the Human Eye and Its Effects on Image Quality* (GSDF의 근거가 되는 CSF 모델).
- Dobbins, J. T. et al. DQE/MTF/NPS 측정 방법론에 관한 일련의 연구.

### 대조도·다중스케일 처리
- Pizer, S. M. et al. (1987). *Adaptive Histogram Equalization and Its Variations* (CLAHE의 기원).
- Pisano, E. D. et al. (1998). 맘모그래피에서의 CLAHE 적용 연구.
- Burt, P. J., Adelson, E. H. (1983). *The Laplacian Pyramid as a Compact Image Code*.
- Mallat, S. (1989). 다해상도(multiresolution) 웨이브렛 이론.
- Paris, S., Hasinoff, S. W., Kautz, J. (2011). *Local Laplacian Filters*.
- He, K., Sun, J., Tang, X. (2010/2013). *Guided Image Filtering*.
- MUSICA (Multi-Scale Image Contrast Amplification) — Agfa/Philips 계열 임상 처리 기법.

### 두께 보상·Peripheral Equalization
- Byng, J. W. et al.; Stahl, M. et al.; Snoeren, P. R., Karssemeijer, N. — 유방 두께 모델링 및 peripheral equalization 연구.

### 잡음 제거(에지 보존)
- Perona, P., Malik, J. (1990). *Anisotropic Diffusion*.
- Tomasi, C., Manduchi, R. (1998). *Bilateral Filtering*.
- Buades, A. et al. (2005). *Non-Local Means*.
- Dabov, K. et al. (2007). *BM3D*.

### 학습 기반(딥러닝)
- Ronneberger, O. et al. (2015). *U-Net*.
- Zhang, K. et al. (2017). *DnCNN*.
- Lehtinen, J. et al. (2018). *Noise2Noise*; Krull, A. et al. (2019). *Noise2Void*.

!!! note "인용 표기에 관하여"

    본 문서는 학습·정리 목적의 기술 문서로, 위 목록은 저자·제목·발표처·연도 수준으로만 표기했습니다. 정식 인용이 필요하면 각 1차 출처의 원문 서지정보(DOI 포함)를 직접 확인하세요.
