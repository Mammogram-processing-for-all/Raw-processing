## breast parenchyma는 밝고 skin layer는 어두운 것이 문제
1. skin layer detection
2. skin boost + parenchyma gemma

```python
# --- Auto Skin Depth Detection ---
def find_skin_depth(processed_img, breast_mask, band_width=5, max_search=100,
                     drop_ratio=0.3):
    dist = distance_transform_edt(breast_mask)
    band_data = []
    for d_start in range(0, max_search, band_width):
        d_end = d_start + band_width
        band = breast_mask & (dist > d_start) & (dist <= d_end)
        if band.sum() > 100:
            band_data.append((d_start + band_width / 2, processed_img[band].mean()))
    if len(band_data) < 4:
        return 25
    distances = [d for d, m in band_data]
    means = [m for d, m in band_data]
    grads = []
    for i in range(len(means) - 1):
        grads.append((distances[i], means[i+1] - means[i]))
    max_grad = max(g for _, g in grads[:3])
    threshold = max_grad * drop_ratio
    skin_depth = distances[-1]
    passed_peak = False
    for d, g in grads:
        if g >= max_grad * 0.8:
            passed_peak = True
        if passed_peak and g <= threshold:
            skin_depth = d + band_width / 2
            break
    return skin_depth
```

```python
# --- Skin Boost + Parenchyma Gamma ---
def skin_add_inner_gamma(img, breast_mask, skin_depth,
                          inner_gamma=1.8, skin_boost=0.30):
    dist = distance_transform_edt(breast_mask)
    output = img.copy()
    inner_zone = breast_mask & (dist > skin_depth)
    if inner_zone.any():
        max_dist = dist[breast_mask].max()
        beta = np.clip((dist[inner_zone] - skin_depth) / (max_dist - skin_depth + 1), 0, 1)
        gamma_values = 1.0 + beta * (inner_gamma - 1.0)
        output[inner_zone] = np.power(np.clip(img[inner_zone], 1e-6, 1), gamma_values)
    skin_zone = breast_mask & (dist <= skin_depth)
    if skin_zone.any():
        alpha = 1.0 - dist[skin_zone] / skin_depth
        boost = skin_boost * alpha
        output[skin_zone] = np.clip(img[skin_zone] + boost, 0, 1)
    output_smooth = gaussian_filter(output, sigma=2)
    transition = breast_mask & (dist > skin_depth * 0.8) & (dist <= skin_depth * 1.2)
    output[transition] = output_smooth[transition]
    output[~breast_mask] = 0
    return output
```

```python
# data load
raw_path = '/content/drive/MyDrive/mammogram/Data/1/1.raw'
target_path = '/content/drive/MyDrive/mammogram/Data/1/1_target.dcm'
ds = pydicom.dcmread(target_path)
rows, cols = ds.Rows, ds.Columns
target_img = ds.pixel_array.astype(np.float64)
raw_img = np.fromfile(raw_path, dtype=np.uint16).reshape(rows, cols).astype(np.float64)
```

```python
# Pipeline 실행

# Step 1: Segmentation
threshold = find_breast_threshold(raw_img)
breast_mask_raw = apply_breast_threshold(raw_img, threshold)
breast_mask = clean_breast_mask(breast_mask_raw)

# Step 2: Log Transform
log_img = apply_log_transform(raw_img, breast_mask)

# Step 3: Peripheral EQ (5%)
eq_img = peripheral_equalization(log_img, breast_mask)

# Step 4: CLAHE
clahe_img = apply_clahe(eq_img, breast_mask)

# Step 5: Auto skin detection + region tone mapping
skin_depth = find_skin_depth(clahe_img, breast_mask)
final_img = skin_add_inner_gamma(clahe_img, breast_mask, skin_depth, inner_gamma=1.8, skin_boost=0.30)
```

## 하나의 특정 raw image에 대해서는 잘 처리되나 다른 raw image에 적용했을 때 문제점이 생김
## 특히 fatty breast에서 peripery가 과하게 밝음