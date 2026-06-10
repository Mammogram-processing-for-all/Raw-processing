# IoU — segmentation 평가

유방 영역 마스크의 정확도를 평가하는 표준 지표.

$$
\mathrm{IoU}(A, B) = \frac{|A \cap B|}{|A \cup B|}
$$

```python title="iou.py" linenums="1"
import numpy as np

def iou(a, b):
    a, b = a.astype(bool), b.astype(bool)
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / union) if union else 0.0
```

[Breast Masking](../preprocessing/masking.md) 페이지에서 마스크 품질의 1차 기준으로 사용한다. 기준선은 데이터셋·해상도·작업에 따라 다르다.
