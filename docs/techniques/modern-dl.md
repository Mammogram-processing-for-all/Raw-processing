# 최신 동향: 학습 기반(딥러닝) 처리

!!! abstract "요약"
    앞선 문서들이 다룬 [다중스케일 분해](multiscale.md), [Peripheral Equalization](peripheral-equalization.md), [contrast enhancement](contrast-enhancement.md)는 모두 사람이 설계한(hand-crafted) 곡선·필터·파라미터에 의존한다. 최근 유방촬영(mammography) 영상 처리는 이 손수 설계를 **데이터 기반 최적화(data-driven optimization)** 로 대체·보완하는 방향으로 빠르게 이동하고 있다. 이 문서는 잡음 제거(denoising), 대비/표시 최적화, 초해상도(super-resolution), 그리고 검출·진단과의 결합까지 **고전→학습 기반** 흐름의 종착점을 정리한다. 단, 맘모그래피에서는 **환각(hallucination)** 으로 인한 가짜 미세석회 생성이 치명적이므로, 정량 평가([MTF/품질지표](../image-quality/metrics.md))와 규제 관점을 끝까지 강조한다.

전체 기법 지형은 [기법 개요](index.md)를, 본 프로젝트의 고전 파이프라인은 [프로젝트 파이프라인](../pipeline/three-tier.md)을 참고하라.

---

## 1. 전환 동기: hand-crafted에서 data-driven으로

고전 파이프라인의 한계는 분명하다.

- 특성 곡선·톤 곡선·필터 파라미터를 사람이 영상 종류·장비별로 튜닝해야 한다([특성 곡선/톤매핑](../image-formation/characteristic-curves.md)).
- 잡음 모델(Poisson+Gaussian)이 단순화돼 저선량(low-dose)에서 성능이 떨어진다.
- 국소 대비·평활화의 trade-off가 고정되어 영상 적응성이 낮다.

학습 기반 방법은 대량의 (입력, 목표) 쌍에서 매핑을 직접 학습해, 비선형성과 공간 적응성을 데이터로부터 얻는다. CNN(Convolutional Neural Network), U-Net, GAN(Generative Adversarial Network), diffusion model이 대표 도구다.

---

## 2. (denoising) 학습 기반 잡음 제거

선형 평활화나 wavelet thresholding([smoothing/denoising](smoothing.md), [다중스케일 분해](multiscale.md))을 대체하는 첫 진입점이 denoising이다.

### 2.1 지도 학습: DnCNN, U-Net

**DnCNN**(Zhang et al., 2017)은 잔차 학습(residual learning)으로 잡음 성분만 예측하는 CNN으로, 다양한 잡음 수준에 강건하다[^dncnn]. **U-Net**(Ronneberger et al., 2015)은 인코더-디코더 + skip connection 구조로, 의료영상 denoising·복원의 사실상 표준 백본이다[^unet].

### 2.2 자기지도(self-supervised): Noise2Noise, Noise2Void

깨끗한 정답(clean ground truth)을 얻기 어려운 의료영상에 핵심적이다.

- **Noise2Noise**(Lehtinen et al., 2018): 같은 장면의 서로 다른 잡음 관측 두 장만으로 학습[^n2n].
- **Noise2Void**(Krull et al., 2019): 단일 잡음 영상만으로 blind-spot 방식 학습[^n2v].

저선량 mammography denoising은 환자 피폭을 줄이려는 핵심 응용이며, 정답 없는 self-supervised 접근이 특히 유용하다.

---

## 3. (enhance) 대비/표시 최적화

CLAHE([점 연산/CLAHE](point-operations.md))와 다중스케일 톤매핑을 학습으로 대체·보강한다.

- **학습형 톤매핑/enhancement**: 입력 영상에 적응적인 곡선·국소 이득을 네트워크가 예측. 고정 CLAHE보다 영상별 최적화가 가능.
- **GAN 기반 image-to-image**(pix2pix류, Isola et al., 2017): for-processing(원시) → for-presentation(판독용) 매핑을 학습해, 장비별 표시 처리를 데이터로 재현[^pix2pix]. 본 프로젝트의 [3-tier 분해 + 톤매핑 + CLAHE](../pipeline/three-tier.md)가 수행하는 작업을 학습 모델로 대신할 수 있다.

!!! warning "GAN 표시 처리의 함정"
    GAN은 "그럴듯한" 출력을 만들도록 학습되므로, 진짜로 존재하지 않는 미세 구조를 그려 넣을 수 있다(§6). 표시 최적화는 진단 정보를 **재배치(대비/톤)** 해야지 **생성**해서는 안 된다.

---

## 4. (super-resolution) 초해상도와 MTF 복원

**초해상도(super-resolution, SR)** 는 저해상도/저선량 영상에서 고해상도 디테일을 복원한다(SRCNN, ESRGAN 계열). 신호처리 관점에서는 검출기·산란으로 손실된 고주파, 즉 **MTF(Modulation Transfer Function) 복원** 문제로 볼 수 있다([MTF/품질지표](../image-quality/metrics.md)). deconvolution의 학습 기반 일반화에 해당한다.

!!! warning "복원 vs 생성의 경계"
    SR이 "복원"하는 고주파가 실제 측정 정보의 외삽인지, 학습 사전(prior)으로 만들어낸 그럴듯한 패턴인지 구분해야 한다. 맘모에서 후자는 가짜 석회·가짜 spiculation으로 이어질 수 있다.

---

## 5. 검출/진단과의 결합 — 처리와 분석의 경계

enhancement(처리)와 detection(분석)의 경계는 학습 기반에서 흐려진다.

- **Segmentation**: U-Net 기반 유방/병변/밀도 분할.
- **Detection / Classification**: 미세석회·종괴 검출과 양·악성 분류(CAD, Computer-Aided Detection/Diagnosis).
- **DBT 재구성**: 디지털 유방 단층영상(Digital Breast Tomosynthesis) 재구성에 학습 기반 사전(deep prior) 적용.

!!! note "처리는 분석을 위한 전처리"
    enhancement의 목적은 사람 판독 또는 후단 CAD가 잘 작동하도록 정보를 보존·부각하는 것이다. 처리 단계가 정보를 왜곡하면(예: 미세석회 제거/위조) 하류 진단 전체가 무너진다.

---

## 6. 한계와 주의

| 위험 | 설명 |
| --- | --- |
| 환각(hallucination) | 존재하지 않는 미세석회·구조 생성. 맘모에서 **치명적** — 위양성/위음성 직결 |
| 도메인 시프트(domain shift) | 학습 장비·집단과 다른 데이터에서 성능 급락. 일반화 부족 |
| 설명가능성(explainability) | 블랙박스 매핑. 임상 신뢰·책임 소재 문제 |
| 규제(regulatory) | FDA / MFDS(식약처) 의료기기 인허가, 검증·시판후 감시 필요 |

특히 **정량 평가의 중요성**은 아무리 강조해도 지나치지 않다. 시각적으로 "선명한" 출력이 진단적으로 옳다는 보장은 없다. 미세석회 검출 민감도/특이도, [MTF/품질지표](../image-quality/metrics.md)(MTF, NPS, DQE, CNR), 그리고 정답과의 구조적 일치(SSIM 등)로 **정보 보존**을 검증해야 한다. 생성형 모델은 지각 품질(perceptual quality)과 충실도(fidelity)가 종종 상충하므로, fidelity 지표를 우선한다.

---

## 7. 고전 파이프라인과 딥러닝의 하이브리드 전망

가장 현실적인 방향은 **하이브리드**다.

- 물리적으로 검증 가능한 단계([log선형화](../foundations/detector.md), [peripheral equalization](peripheral-equalization.md), [다중스케일 분해](multiscale.md))는 고전·결정론적으로 유지해 정보 보존을 보장하고,
- denoising·디테일 복원처럼 데이터 이득이 큰 단계만 학습 모델로 교체하되, 출력 범위를 물리 제약·정량 지표로 가드레일(guardrail)한다.

이렇게 하면 고전 파이프라인의 **해석가능성·안전성**과 딥러닝의 **적응성·성능**을 함께 취할 수 있다. 전체 흐름의 출발점은 다시 [기법 개요](index.md)와 [프로젝트 파이프라인](../pipeline/three-tier.md)으로 돌아간다.

---

## 8. 작업별 요약 표

| 작업 | 대표 모델 | 입력 → 출력 | 주요 위험 |
| --- | --- | --- | --- |
| Denoise | DnCNN, U-Net, Noise2Noise/Void | 잡음 영상 → 잡음 제거 영상 | 과평활(미세석회 손실) |
| Enhance | 학습형 톤매핑, pix2pix(GAN) | for-processing → for-presentation | 환각, 대비 왜곡 |
| Super-resolution | SRCNN, ESRGAN | 저해상도 → 고해상도 | 가짜 고주파 생성 |
| Detect/Diagnose | U-Net(seg), CNN(classify), CAD | 영상 → 마스크/병변/라벨 | 도메인 시프트, 위양성 |

---

## 참고문헌

[^unet]: Ronneberger, O., Fischer, P., & Brox, T. (2015). *U-Net: Convolutional Networks for Biomedical Image Segmentation.* MICCAI 2015, LNCS 9351, 234–241.
[^dncnn]: Zhang, K., Zuo, W., Chen, Y., Meng, D., & Zhang, L. (2017). *Beyond a Gaussian Denoiser: Residual Learning of Deep CNN for Image Denoising (DnCNN).* IEEE Transactions on Image Processing, 26(7), 3142–3155.
[^n2n]: Lehtinen, J., et al. (2018). *Noise2Noise: Learning Image Restoration without Clean Data.* ICML 2018.
[^n2v]: Krull, A., Buchholz, T.-O., & Jug, F. (2019). *Noise2Void — Learning Denoising from Single Noisy Images.* CVPR 2019.
[^pix2pix]: Isola, P., Zhu, J.-Y., Zhou, T., & Efros, A. A. (2017). *Image-to-Image Translation with Conditional Adversarial Networks (pix2pix).* CVPR 2017.
