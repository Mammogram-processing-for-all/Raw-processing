# Pixel Error — MAE / MSE / PSNR

가장 기본적인 픽셀 단위 오차.

$$
\mathrm{MAE} = \frac{1}{N} \sum_i |x_i - y_i|
\qquad
\mathrm{MSE} = \frac{1}{N} \sum_i (x_i - y_i)^2
$$

PSNR은 MSE를 데시벨로 환산해 신호 대비 잡음을 표현한다.

$$
\mathrm{PSNR} = 10 \log_{10} \frac{\mathrm{MAX}^2}{\mathrm{MSE}}
$$

`MAX`는 동적 범위 — 8비트면 255, [0,1] 정규화면 1.0, 16비트면 65535.

```python title="basic_metrics.py" linenums="1"
import numpy as np

def mae(a, b):  return float(np.mean(np.abs(a - b)))
def mse(a, b):  return float(np.mean((a - b) ** 2))

def psnr(a, b, data_range=1.0):
    m = mse(a, b)
    return float("inf") if m == 0 else 10 * np.log10(data_range ** 2 / m)
```

PSNR 만으로는 두 이미지가 "구조적으로 비슷"한지 알 수 없다. 같은 PSNR 값이라도 한쪽은 균일한 회색 노이즈, 한쪽은 선명한 에지를 가질 수 있다. 구조적 유사도는 [SSIM](ssim.md)으로 측정한다.
