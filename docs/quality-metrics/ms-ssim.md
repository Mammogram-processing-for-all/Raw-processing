# MS-SSIM

[SSIM](ssim.md)을 **3~5단계 다운샘플**에서 각각 계산해 가중합한다.

```python title="ms_ssim.py" linenums="1"
import torch.nn.functional as F
# 단일 스케일 SSIM 구현은 별도로 필요 (예: torchmetrics.functional.ssim,
# kornia.metrics.ssim, 또는 직접 구현). 아래는 다중 스케일 구조만 보여준다.

def ms_ssim_loss(pred, target, ssim_single, weights=(0.5, 0.3, 0.2)):
    total = 0.0
    for i, w in enumerate(weights):
        if i > 0:
            pred   = F.avg_pool2d(pred,   2)
            target = F.avg_pool2d(target, 2)
        total += w * (1 - ssim_single(pred, target))
    return total
```

- 단일 스케일 SSIM은 전체 구조에 강하지만 미세 구조(석회화)에 둔감하다
- 가중치는 고해상도 쪽에 더 크게 — 미세 구조에 더 큰 페널티
- 학습 손실로 쓸 때는 `1 - SSIM` 형태로 사용
