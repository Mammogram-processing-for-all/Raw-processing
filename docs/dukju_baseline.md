## baseline code
1. breast segmentation (histogram기반 + 구멍메우기)
2. log transform
3. peripheral equalization (5%) - 이 부분은 어떻게 수정할 지 고민
4. CLAHE - eq를 processing에 넣을때와 뺄때, calcification이 delineation되는지 

# breast segmentation
```python
def find_breast_threshold(raw_img, search_low=10000, search_high=30000, n_bins=1000):
    hist, bins = np.histogram(raw_img.ravel(), bins=n_bins)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    search_range = (bin_centers > search_low) & (bin_centers < search_high)
    valley_idx = np.argmin(hist[search_range])
    return bin_centers[search_range][valley_idx]

def apply_breast_threshold(raw_img, threshold):
    return raw_img < threshold

def clean_breast_mask(mask, close_kernel_size=25, open_kernel_size=15):
    mask_uint8 = mask.astype(np.uint8) * 255
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel_size, close_kernel_size))
    mask_uint8 = cv2.morphologyEx(mask_uint8, cv2.MORPH_CLOSE, kernel_close)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_kernel_size, open_kernel_size))
    mask_uint8 = cv2.morphologyEx(mask_uint8, cv2.MORPH_OPEN, kernel_open)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_uint8)
    if num_labels > 1:
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        mask_uint8 = (labels == largest).astype(np.uint8) * 255
    return ndimage.binary_fill_holes(mask_uint8 > 0).astype(bool)
```

# log transform
```python
def apply_log_transform(raw_img, breast_mask):
    """Log + 실제 min/max 기준 반전 & 정규화 (calcification 보존)"""
    output = np.zeros_like(raw_img, dtype=np.float64)
    pixels = np.clip(raw_img[breast_mask], 1, None)
    log_pixels = np.log(pixels)
    log_max = log_pixels.max()
    inverted = log_max - log_pixels
    inv_min = inverted.min()
    inv_max = np.percentile(inverted, 99.9)
    normalized = np.clip((inverted - inv_min) / (inv_max - inv_min), 0, 1)
    output[breast_mask] = normalized
    return output
```

# peripheral equalization
```python
def peripheral_equalization(log_img, breast_mask, filter_size=None):
    if filter_size is None:
        short_axis = min(log_img.shape)
        filter_size = int(short_axis * 0.05)
        if filter_size % 2 == 0:
            filter_size += 1
    breast_only = log_img.copy()
    breast_only[~breast_mask] = 0
    smoothed = uniform_filter(breast_only, size=filter_size)
    mask_smoothed = uniform_filter(breast_mask.astype(np.float64), size=filter_size)
    mask_smoothed = np.clip(mask_smoothed, 0.01, None)
    smoothed = smoothed / mask_smoothed
    output = np.zeros_like(log_img)
    valid = breast_mask & (smoothed > 0)
    output[valid] = log_img[valid] / smoothed[valid]
    if output[valid].size > 0:
        out_min = np.percentile(output[valid], 0.5)
        out_max = np.percentile(output[valid], 99.5)
        output[valid] = np.clip((output[valid] - out_min) / (out_max - out_min), 0, 1)
    output[~breast_mask] = 0
    return output
```

# CLAHE
```python
def apply_clahe(img, breast_mask, clip_limit=6.0, grid_size=8):
    breast_pixels = img[breast_mask]
    p_low = np.percentile(breast_pixels, 0.5)
    p_high = np.percentile(breast_pixels, 99.5)
    normalized = np.clip((img - p_low) / (p_high - p_low), 0, 1)
    img_uint8 = (normalized * 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
    clahe_result = clahe.apply(img_uint8)
    output = clahe_result.astype(np.float64) / 255.0
    output[~breast_mask] = 0
    return output
```

# baseline process
```python
raw_path = '...'
target_path = '...'
ds = pydicom.dcmread(target_path)
rows, cols = ds.Rows, ds.Columns
target_img = ds.pixel_array.astype(np.float64)
raw_img = np.fromfile(raw_path, dtype=np.uint16).reshape(rows, cols).astype(np.float64)

threshold = find_breast_threshold(raw_img)
breast_mask_raw = apply_breast_threshold(raw_img, threshold)
breast_mask = clean_breast_mask(breast_mask_raw)
log_img = apply_log_transform(raw_img, breast_mask)
eq_img = peripheral_equalization(log_img, breast_mask)
clahe_img = apply_clahe(eq_img, breast_mask)
```