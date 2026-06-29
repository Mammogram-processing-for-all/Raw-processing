# Tenengrad — 정답 없는 선명도 측정

비교할 참조 이미지가 없는 경우(예: RAW 단독 평가). Sobel 필터로 gradient 에너지를 계산한다.

$$
\mathrm{Tenengrad}(I) = \frac{1}{N} \sum_p \bigl( G_x(p)^2 + G_y(p)^2 \bigr)
$$

```python title="tenengrad.py" linenums="1"
import cv2
import numpy as np

def tenengrad(img: np.ndarray, mask: np.ndarray | None = None) -> float:
    rng = img.max() - img.min() + 1e-8
    img_u8 = ((img - img.min()) / rng * 255).astype(np.uint8)
    Gx = cv2.Sobel(img_u8, cv2.CV_64F, 1, 0, ksize=3)
    Gy = cv2.Sobel(img_u8, cv2.CV_64F, 0, 1, ksize=3)
    s  = Gx ** 2 + Gy ** 2
    return float(s[mask.astype(bool)].mean()) if mask is not None else float(s.mean())
```

선명한 이미지일수록 Tenengrad가 크다. 단, 노이즈 증폭으로도 커질 수 있으니 **노이즈가 없는 영역에서**만 측정한다.
