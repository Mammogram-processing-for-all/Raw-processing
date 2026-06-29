# SSIM (Structural Similarity)

지역 윈도우의 **평균·분산·공분산**을 결합해 구조적 유사도를 측정한다.

$$
\mathrm{SSIM}(x, y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}
$$

- `C1`, `C2`: 작은 분모를 안정화하는 상수 (보통 `(K1·L)^2`, `(K2·L)^2`, K1=0.01, K2=0.03, L=동적범위)
- 윈도우는 보통 7~11 픽셀 가우시안

```python title="ssim.py" linenums="1"
from skimage.metrics import structural_similarity as ssim

score = ssim(pred, target, data_range=1.0)
```

## 함정 1 — 정규화에 따라 값이 바뀐다

`data_range`를 잘못 주면 SSIM 값 자체가 의미를 잃는다. 흔한 실수: `pred`와 `target`을 각각 자신의 min/max로 **독립적으로** 0~1 정규화 → 두 이미지의 절대 밝기 차이를 SSIM이 못 본다.

```python
# 잘못된 패턴
p = (pred   - pred.min())   / (pred.max()   - pred.min()   + 1e-8)
t = (target - target.min()) / (target.max() - target.min() + 1e-8)
ssim(p, t, data_range=1.0)   # 절대 밝기 차이 손실
```

권장: **공동 동적 범위**로 정규화한다.

```python
lo = min(pred.min(), target.min())
hi = max(pred.max(), target.max())
p = (pred   - lo) / (hi - lo + 1e-8)
t = (target - lo) / (hi - lo + 1e-8)
ssim(p, t, data_range=1.0)
```

## 함정 2 — SSIM이 음수면 공간적 반전 의심

SSIM은 −1까지 떨어질 수 있다. 0은 "무관", 음수는 "구조적으로 반대로 정렬". 한쪽이 강도 극성 반전([MONOCHROME1](../preprocessing/dicom-basics.md) 미보정 등)이거나 공간 정렬이 어긋난 경우 발생한다.

미세 구조(석회화)까지 함께 평가하려면 다중 스케일 확장인 [MS-SSIM](ms-ssim.md)을 쓴다.
