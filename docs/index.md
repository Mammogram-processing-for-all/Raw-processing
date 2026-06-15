# Mammogram Processing for All

유방촬영(mammography) 영상의 **전처리**와 **임상 배경**을 다루는 오픈 문서입니다.

### Preprocessing — 픽셀 단계의 모든 것

DICOM 적재부터 디스플레이·모델 입력까지의 한 줄기 흐름을 다룹니다.

- [Pipeline Overview](preprocessing/pipeline-overview.md) — 전체 단계의 연결 지도부터 보기
- [DICOM Basics](preprocessing/dicom-basics.md) — 표준, 헤더, MONOCHROME1 함정
- [Windowing](preprocessing/windowing.md), [LUT](lut.md) — 16비트를 8비트로 펴는 법
- [Breast Masking](preprocessing/masking.md) — Otsu / Multi-Otsu / 적응형
- [Histogram Matching](preprocessing/histogram-matching.md) — CDF 기반 비선형 매핑
- [CLAHE](preprocessing/clahe.md), [Denoising](preprocessing/denoising.md), [Laplacian Pyramid](preprocessing/laplacian-pyramid.md) — 대비 강화
- [RAW → DCM Restoration](preprocessing/raw-to-dcm.md) — 강도 선형화·halo 방지·톤 매핑을 묶은 복원 가이드
- [Quality Metrics](quality-metrics/index.md) — MAE/SSIM/PSNR/IoU/Tenengrad

### Clinical Background — 영상이 의미하는 것

모델이 "잘 잡았다"고 말할 수 있으려면 임상 용어를 알아야 합니다.

- [Views (CC/MLO)](clinical/views.md) — 왜 한 검사에 4장인가
- [Lesion Types](clinical/lesion-types.md) — 종괴·미세석회화·구조왜곡·비대칭
