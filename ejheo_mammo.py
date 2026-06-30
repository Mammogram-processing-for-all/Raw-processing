import os
import numpy as np
import matplotlib.pyplot as plt
import pydicom
import glob
import cv2

# ==========================================
# 1. 데이터 I/O 모듈
# ==========================================

def load_mammography_data(root_dir, folders_range=(0, 10)):
    """디스크에서 RAW와 DICOM 파일 쌍을 찾아 메모리에 적재."""
    RAW_HEIGHT, RAW_WIDTH = 3816, 3048
    RAW_DTYPE = np.dtype('<u2')

    dataset = {}
    for i in range(folders_range[0], folders_range[1] + 1):
        folder_name = str(i)
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        dataset[folder_name] = []
        for raw_path in glob.glob(os.path.join(folder_path, "*.raw")):
            raw_base = os.path.splitext(os.path.basename(raw_path))[0]
            matching_dcms = glob.glob(os.path.join(folder_path, f"{raw_base}*.dcm"))
            if not matching_dcms:
                continue
            try:
                dcm_data = pydicom.dcmread(matching_dcms[0])
                raw_array = np.fromfile(raw_path, dtype=RAW_DTYPE).reshape((RAW_HEIGHT, RAW_WIDTH))
                dataset[folder_name].append({
                    'name': raw_base,
                    'dcm_path': os.path.basename(matching_dcms[0]),
                    'dcm_image': dcm_data.pixel_array if hasattr(dcm_data, 'pixel_array') else None,
                    'raw_image': raw_array,
                })
            except Exception as e:
                print(f"Error reading {raw_base}: {e}")
    return dataset


def save_as_presentation_dicom(img_array, reference_dcm_path, output_path):
    """처리된 uint16 배열을 참조 DICOM 메타데이터에 주입하여 저장."""
    if reference_dcm_path is None or not os.path.exists(reference_dcm_path):
        print(f"Warning: 참조 DICOM 없음, 저장 건너뜀 ({output_path})")
        return

    dcm = pydicom.dcmread(reference_dcm_path)
    dcm.SOPInstanceUID = pydicom.uid.generate_uid()
    if hasattr(dcm, 'file_meta'):
        dcm.file_meta.MediaStorageSOPInstanceUID = dcm.SOPInstanceUID
    dcm.SeriesInstanceUID = pydicom.uid.generate_uid()
    dcm.ImageType = ['DERIVED', 'SECONDARY', 'OTHER']
    dcm.DerivationDescription = 'Mammography Enhancement Pipeline Output'

    dcm.PixelData = img_array.tobytes()
    dcm.Rows, dcm.Columns = img_array.shape

    fg_pixels = img_array[img_array > 0]
    if len(fg_pixels) > 0:
        p_min, p_max = np.percentile(fg_pixels, (2, 98))
        dcm.WindowWidth  = int(p_max - p_min)
        dcm.WindowCenter = int((p_max + p_min) / 2)
    else:
        dcm.WindowWidth, dcm.WindowCenter = 65535, 32767

    dcm.add_new([0x0028, 0x0120], 'US', 0)
    dcm.BitsAllocated = 16
    dcm.BitsStored = 16
    dcm.HighBit = 15
    dcm.PixelRepresentation = 0
    pydicom.dcmwrite(output_path, dcm)


# ==========================================
# 2. 데이터 처리 모듈
# ==========================================

# --- Phase A: 물리 신호 선형화 ---
# I₀ 추정 → log(I₀/I) 선형화 → 유방 마스크 생성

def _get_polynomial_basis(x_val, y_val, deg):
    """2D 좌표에서 다항식 기저 행렬 생성."""
    basis = [(x_val**i) * (y_val**j)
             for i in range(deg + 1)
             for j in range(deg + 1 - i)]
    return np.column_stack(basis)


def get_breast_mask(img, mask_thresh=1000):
    """임계값 이진화 + 모폴로지 + LCC(최대 연결 요소) 추출로 유방 마스크 반환."""
    thresh_input = img.astype(np.float32) if img.dtype != np.uint8 else img
    _, thresh = cv2.threshold(thresh_input, mask_thresh, 255, cv2.THRESH_BINARY)
    thresh = thresh.astype(np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh)
    if num_labels > 1:
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        return np.where(labels == largest_label, 255, 0).astype(np.uint8)
    return thresh


def estimate_illumination_map(raw_array, degree=2, grid_size=100):
    """배경 그리드 샘플링 후 다항식 피팅으로 조명 맵(I₀)을 추정."""
    h, w = raw_array.shape
    p_low, p_high = np.percentile(raw_array, (2, 98))
    norm_8bit = np.clip(
        (raw_array - p_low) / (p_high - p_low + 1e-6) * 255, 0, 255
    ).astype(np.uint8)

    _, thresh = cv2.threshold(norm_8bit, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh)
    if num_labels > 1:
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        bg_mask = (labels == largest_label).astype(np.uint8)
    else:
        bg_mask = thresh // 255

    safe_bg_mask = cv2.erode(bg_mask, np.ones((30, 30), np.uint8), iterations=1)

    sample_x, sample_y, sample_z = [], [], []
    for y in range(0, h, grid_size):
        for x in range(0, w, grid_size):
            block_mask = safe_bg_mask[y:min(y + grid_size, h), x:min(x + grid_size, w)]
            if np.mean(block_mask) > 0.9:
                z_val = np.percentile(raw_array[y:min(y + grid_size, h), x:min(x + grid_size, w)], 95)
                sample_x.append(x + grid_size / 2.0)
                sample_y.append(y + grid_size / 2.0)
                sample_z.append(z_val)

    if len(sample_x) < 10:
        print("Warning: 유효 배경 부족 — 기본 평면 반환")
        return np.full_like(raw_array, np.percentile(raw_array, 95))

    sx, sy, sz = np.array(sample_x), np.array(sample_y), np.array(sample_z)
    A = _get_polynomial_basis(sx / w, sy / h, degree)
    coeffs, _, _, _ = np.linalg.lstsq(A, sz, rcond=None)

    X, Y = np.meshgrid(np.arange(w), np.arange(h))
    full_basis = _get_polynomial_basis(X.flatten() / w, Y.flatten() / h, degree)
    i0_map = (full_basis @ coeffs).reshape(h, w)

    positive_pixels = raw_array[raw_array > 0]
    i0_floor = float(np.percentile(positive_pixels, 50)) if len(positive_pixels) > 0 else 1.0
    return np.clip(i0_map, a_min=i0_floor, a_max=None)


def apply_log_linearization(raw_array, i0_map):
    """log(I₀/I) 계산 후 [0, 65535] uint16으로 정규화."""
    EPSILON = 1.0
    linearized = np.log(np.clip(i0_map, EPSILON, None) / np.clip(raw_array, EPSILON, None))
    linearized = np.clip(linearized, 0, None)
    l_max = linearized.max()
    result = (linearized / l_max * 65535) if l_max > 0 else linearized
    return result.astype(np.uint16)


# --- Phase A.5: Peripheral Thickness 보상 ---
# 	정규화 컨볼루션으로 외곽 Wedge 효과 제거

def _estimate_thickness_map(img_f, mask, radius, downsample_factor=4):
    """
    정규화 컨볼루션으로 두께 구배 맵 추정.
    - denom 임계값 0.15로 강화: 경계부 불안정 픽셀(분모가 작아 과추정되는 구간) 제거
    - 경계 soft fade: distance transform으로 마스크 경계에서 두께 맵을 선형 감쇠하여 Halo 방지
    """
    h, w = img_f.shape
    ds = max(1, downsample_factor)
    h_ds, w_ds = max(1, h // ds), max(1, w // ds)

    img_ds  = cv2.resize(img_f, (w_ds, h_ds), interpolation=cv2.INTER_AREA)
    mask_ds = cv2.resize(mask.astype(np.float32), (w_ds, h_ds),
                         interpolation=cv2.INTER_NEAREST).astype(np.uint8)
    mask_f  = (mask_ds > 0).astype(np.float32)

    sigma_max = min(h_ds, w_ds) * 0.10
    sigma = max(min(float(radius // ds) * 0.6, sigma_max), 3.0)

    numer    = cv2.GaussianBlur(img_ds * mask_f, (0, 0), sigmaX=sigma)
    denom    = cv2.GaussianBlur(mask_f,          (0, 0), sigmaX=sigma)

    # denom 임계값 강화: 1e-6 → 0.15
    # 경계부에서 denom이 작으면 numer/denom이 폭발적으로 커져 Halo 발생
    DENOM_THRESH = 0.15
    # 불안정 경계 픽셀: 0 대신 유효 영역 중앙값으로 채워 보정 점프 방지
    # (0으로 채우면 correction = 0 - t_ref < 0 → 과보정 → Halo 발생)
    valid_vals = numer[denom > DENOM_THRESH] / (denom[denom > DENOM_THRESH] + 1e-6)
    fill_val = float(np.median(valid_vals)) if len(valid_vals) > 0 else 0.0
    thick_ds = np.where(denom > DENOM_THRESH, numer / (denom + 1e-6), fill_val).astype(np.float32)
    thick_ds[mask_ds == 0] = 0.0

    thickness_map = cv2.resize(thick_ds, (w, h), interpolation=cv2.INTER_LINEAR)
    thickness_map[mask == 0] = 0.0
    return thickness_map


def compensate_peripheral_thickness(processed_raw, mask, radius_wedge=300, downsample_factor=4):
    """
    Wedge-Compensated Linearization (Stage 0.5).
    T_map - T_ref(p90) 기준으로 외곽 얇은 영역만 상향 보정.
    """
    img_f = processed_raw.astype(np.float32) / 65535.0
    fg_pixels = img_f[mask > 0]
    if len(fg_pixels) == 0:
        return processed_raw

    thickness_map = _estimate_thickness_map(img_f, mask, radius=radius_wedge,
                                            downsample_factor=downsample_factor)
    t_ref = float(np.percentile(fg_pixels, 90))
    correction  = np.clip(thickness_map - t_ref, None, 0.0)
    compensated = np.clip(img_f - correction, 0.0, None)
    compensated[mask == 0] = 0.0
    return (compensated * 65535.0).astype(np.uint16)


def stage_for_processing(raw_array, degree=2, grid_size=100, mask_thresh=1000,
                         radius_wedge=300, eps_wedge=0.1):
    """I₀ 추정 → 로그 선형화 → 마스크 → Peripheral Thickness 보상."""
    i0_map        = estimate_illumination_map(raw_array, degree=degree, grid_size=grid_size)
    processed_raw = apply_log_linearization(raw_array, i0_map)
    mask          = get_breast_mask(processed_raw, mask_thresh=mask_thresh)
    compensated_raw = compensate_peripheral_thickness(processed_raw, mask, radius_wedge=radius_wedge)
    return compensated_raw, mask, processed_raw


# --- Phase B: 3-Tier 분해 및 합성 ---
#  Global / Regional / Enhanced-Detail 분해 + 라플라시안 증폭

def _guided_filter_masked(img_float, mask, radius, eps):
    """
    Masked Guided Filter: 전경 픽셀만으로 통계를 계산.
    배경 fill 불필요 → 경계 Halo 원천 제거.
    """
    mask_f = (mask > 0).astype(np.float32)
    ksize = (2 * radius + 1, 2 * radius + 1)

    # 각 윈도우 내 전경 픽셀 수
    N = cv2.boxFilter(mask_f, cv2.CV_32F, ksize, normalize=False)
    N = np.maximum(N, 1.0)

    I_masked = img_float * mask_f

    # Pass 1: 각 윈도우의 masked 통계 (self-guided: guide = src)
    mean_I  = cv2.boxFilter(I_masked,             cv2.CV_32F, ksize, normalize=False) / N
    mean_II = cv2.boxFilter(I_masked * img_float,  cv2.CV_32F, ksize, normalize=False) / N

    var_I = np.maximum(mean_II - mean_I * mean_I, 0.0)  # 수치 안정성

    a = var_I / (var_I + eps)
    b = mean_I * (1.0 - a)

    # Pass 2: a, b의 윈도우 평균 (역시 masked)
    mean_a = cv2.boxFilter(a * mask_f, cv2.CV_32F, ksize, normalize=False) / N
    mean_b = cv2.boxFilter(b * mask_f, cv2.CV_32F, ksize, normalize=False) / N

    result = (mean_a * img_float + mean_b).astype(np.float32)
    result[mask == 0] = 0.0
    return result


def _build_laplacian_pyramid(img, levels):
    """가우시안 피라미드로부터 라플라시안 피라미드 반환."""
    gp = [img]
    for _ in range(levels):
        gp.append(cv2.pyrDown(gp[-1]))
    lp = []
    for i in range(levels):
        size = (gp[i].shape[1], gp[i].shape[0])
        lp.append(cv2.subtract(gp[i], cv2.pyrUp(gp[i + 1], dstsize=size)))
    return lp, gp[-1]


def _reconstruct_from_laplacian(lp, residual, weights):
    """가중치 적용 라플라시안 피라미드 재합성."""
    R = residual
    for i in range(len(lp) - 1, -1, -1):
        size = (lp[i].shape[1], lp[i].shape[0])
        R = cv2.add(cv2.pyrUp(R, dstsize=size), lp[i] * weights[i])
    return R


def stage_decomposition(processed_raw, mask, pyr_levels=5,
                        radius_global=150, radius_regional=50,
                        eps_global=0.01, eps_regional=0.005):
    """
    3-Tier Cascaded Guided Filter 분해.
    - Global  : 초저주파 두께 구배
    - Regional: 중간 주파수 국소 조직 구조
    - Enhanced Detail: 고주파 미세 구조 (라플라시안 피라미드 증폭)
    """
    img_float = processed_raw.astype(np.float32) / 65535.0

    # 직렬 분해: mid 먼저, global은 mid 위에서 계산
    mid_layer    = _guided_filter_masked(img_float, mask, radius=radius_regional, eps=eps_regional)
    global_layer = _guided_filter_masked(mid_layer,  mask, radius=radius_global,   eps=eps_global)

    regional_layer = mid_layer - global_layer
    detail_layer   = img_float - mid_layer

    # 극단적 경계 안전 마진: masked guided filter로 배경 bias 제거됨,
    # 극소수 경계 픽셀의 one-sided window 통계 불안정만 처리
    EDGE_FADE_PX = 10.0
    dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    edge_weight = np.clip(dist / EDGE_FADE_PX, 0.0, 1.0).astype(np.float32)
    regional_layer = regional_layer * edge_weight

    # lp[0]=최고주파(미세석회·혈관벽) 우선 증폭, 저주파로 갈수록 완화
    weights = [2.0, 2.0, 1.5, 1.0, 0.5]
    lp, residual = _build_laplacian_pyramid(detail_layer, pyr_levels)
    enhanced_detail = _reconstruct_from_laplacian(lp, residual, weights)

    return global_layer, regional_layer, enhanced_detail


def test_laplacian_pyramid_only(processed_raw, mask, pyr_levels=5, radius=50, eps=0.001):
    """테스트용: Base Layer 제거 후 라플라시안 피라미드 증폭 결과만 단독 확인."""
    img_float    = processed_raw.astype(np.float32) / 65535.0
    base_layer   = _guided_filter_masked(img_float, mask, radius=radius, eps=eps)
    detail_layer = img_float - base_layer

    weights = [2.0, 1.0, 1.5, 1.0, 2.0]
    lp, residual = _build_laplacian_pyramid(detail_layer, pyr_levels)
    R = _reconstruct_from_laplacian(lp, residual, weights)

    detail_valid = R[mask > 0]
    if len(detail_valid) > 0:
        d_min, d_max = np.percentile(detail_valid, (1.0, 99.0))
        R = np.clip((R - d_min) / (d_max - d_min + 1e-6), 0.0, 1.0)

    out = (R * 65535.0).astype(np.uint16)
    out[mask == 0] = 0
    return out


def stage_for_presentation(global_layer, regional_layer, enhanced_detail, mask,
                           equalization_alpha=0.7, regional_gain=1.5, detail_gain=1.5,
                           gamma=2.5, clahe_clip=1.0, clahe_blend=0.1):
    """
    3-Tier 선형 억제 기반 최종 렌더링 융합.
    Global 억제 → Regional 증폭 → Black Point → Gamma → CLAHE
    CLAHE 비중 조절 테스트, clahe_blend 수치 조절 중
    """
    suppressed_global  = global_layer * (1.0 - equalization_alpha)
    amplified_regional = regional_layer * regional_gain
    fused_float        = suppressed_global + amplified_regional + (enhanced_detail * detail_gain)

    # ── For-Processing 출력 (참조용) ──
    fp_valid = fused_float[mask > 0]
    if len(fp_valid) > 0:
        fp_min, fp_max = np.percentile(fp_valid, (0.0, 100.0))
        fp_norm = np.clip((fused_float - fp_min) / (fp_max - fp_min + 1e-6), 0.0, 1.0)
    else:
        fp_norm = np.clip(fused_float, 0.0, 1.0)
    fp_norm[mask == 0] = 0
    for_proc_img_out = (fp_norm * 65535.0).astype(np.uint16)

    # ── For-Presentation 출력 ──
    valid_pixels = fused_float[mask > 0]
    if len(valid_pixels) == 0:
        zeros = np.zeros_like(global_layer, dtype=np.uint16)
        return zeros, zeros, zeros

    # B-1: Black Point Clipping (하위 3%만 클리핑하여 가장자리 신호 보존)
    p_min, p_max = np.percentile(valid_pixels, (3, 99.5))
    fused_norm = np.clip((fused_float - p_min) / (p_max - p_min + 1e-6), 0.0, 1.0)

    # B-2: Differential Tone Compression (미세 구조 보존 배경 선택 압축)
    # ─ 배경(smooth_bg) gamma 압축, 미세구조(fine_str)는 1.5배 부각시켜 합성
    smooth_bg  = cv2.GaussianBlur(fused_norm.astype(np.float32), (0, 0), sigmaX=20.0)
    fine_str   = fused_norm - smooth_bg
    smooth_bg  = np.power(np.clip(smooth_bg, 1e-6, 1.0), gamma) * 0.85  # 배경 압축 및 톤 강하
    fused_norm = np.clip(smooth_bg + fine_str * 1.5, 0.0, 1.0)          # 미세 구조 추가 증폭 및 재합성

    # B-3: CLAHE (마스크 내부 전용) - 16-bit 정밀도 유지
    fused_16bit = (fused_norm * 65535.0).astype(np.uint16)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(16, 16))
    roi_ys, roi_xs = np.where(mask > 0)
    if len(roi_ys) > 0:
        y0, y1 = roi_ys.min(), roi_ys.max() + 1
        x0, x1 = roi_xs.min(), roi_xs.max() + 1
        roi_patch = fused_16bit[y0:y1, x0:x1].copy()
        roi_mask  = mask[y0:y1, x0:x1]
        clahe_patch = clahe.apply(roi_patch)
        blended_patch = cv2.addWeighted(clahe_patch, clahe_blend, roi_patch, 1.0 - clahe_blend, 0)
        roi_patch[roi_mask > 0] = blended_patch[roi_mask > 0]
        fused_16bit[y0:y1, x0:x1] = roi_patch

    final_img_out = fused_16bit.copy()
    final_img_out[mask == 0] = 0

    # Suppressed Global 시각화용
    sg_valid = suppressed_global[mask > 0]
    if len(sg_valid) > 0:
        sg_min, sg_max = sg_valid.min(), sg_valid.max()
        sg_norm = np.clip((suppressed_global - sg_min) / (sg_max - sg_min + 1e-6), 0.0, 1.0)
    else:
        sg_norm = np.clip(suppressed_global, 0.0, 1.0)
    sg_norm[mask == 0] = 0
    base_img_out = (sg_norm * 65535.0).astype(np.uint16)

    return final_img_out, base_img_out, for_proc_img_out


def _normalize_layer(layer, mask, percentile_range=(1, 99)):
    """레이어를 마스크 내부 픽셀 기준으로 percentile 정규화 후 uint16 반환."""
    valid = layer[mask > 0]
    if len(valid) == 0:
        return np.zeros_like(layer, dtype=np.uint16)
    p_lo, p_hi = np.percentile(valid, percentile_range)
    norm = np.clip((layer - p_lo) / (p_hi - p_lo + 1e-6), 0.0, 1.0)
    norm[mask == 0] = 0
    return (norm * 65535).astype(np.uint16)


def process_mammography_dataset(dataset, base_dir, degree=2, grid_size=100, mask_thresh=1000,
                                radius_wedge=300, eps_wedge=0.1, save_dir=None):
    """dataset을 순회하며 전체 파이프라인을 실행하고 결과를 item에 저장."""
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for folder_name, items in dataset.items():
        for item in items:
            raw_array = item['raw_image']

            compensated_raw, mask, processed_raw = stage_for_processing(
                raw_array, degree, grid_size, mask_thresh,
                radius_wedge=radius_wedge, eps_wedge=eps_wedge
            )
            global_layer, regional_layer, enhanced_detail = stage_decomposition(
                compensated_raw, mask, pyr_levels=5,
                radius_global=250, radius_regional=50,   # radius_global 150→250: 주파수 분리 강화
                eps_global=0.01,  eps_regional=0.005     # eps_regional 0.001→0.005: mid_layer 스무딩 강화
            )
            final_img, base_img, for_proc_img = stage_for_presentation(
                global_layer, regional_layer, enhanced_detail, mask,
                equalization_alpha=0.60, regional_gain=1.1,  # alpha 0.70→0.60: 흉벽 두께 구배 보존
                gamma=1.8,                                   # gamma 2.5→1.8: 흉벽 톤 압축 완화
                detail_gain=2.0, clahe_clip=2.0, clahe_blend=0.2
            )
            test_detail_img = test_laplacian_pyramid_only(compensated_raw, mask)

            if save_dir and item['dcm_path'] is not None:
                ref_dcm_path = os.path.join(base_dir, folder_name, item['dcm_path'])
                save_as_presentation_dicom(
                    final_img, ref_dcm_path,
                    os.path.join(save_dir, f"processed_{folder_name}_{item['name']}.dcm")
                )
                # save_as_presentation_dicom(
                #     test_detail_img, ref_dcm_path,
                #     os.path.join(save_dir, f"test_laplacian_{folder_name}_{item['name']}.dcm")
                # )

            item.update({
                'linearized_raw':     processed_raw,
                'compensated_raw':    compensated_raw,
                'global_layer_img':   _normalize_layer(np.clip(global_layer, 0, None), mask, (0, 100)),
                'regional_layer_img': _normalize_layer(regional_layer, mask),
                'enhanced_detail_img':_normalize_layer(enhanced_detail, mask),
                'equalized_raw':      base_img,
                'for_proc_img':       for_proc_img,
                'final_img':          final_img,
            })
    return dataset


# ==========================================
# 3. 메인 실행부
# ==========================================
if __name__ == "__main__":
    BASE_DIR = r"[YOUR_PATH]\Data"
    SAVE_DIR = r"[YOUR_PATH]\Output"

    raw_dataset = load_mammography_data(BASE_DIR, (1, 10))
    processed_data = process_mammography_dataset(
        raw_dataset, base_dir=BASE_DIR,
        degree=2, grid_size=100, mask_thresh=1300,
        radius_wedge=300, eps_wedge=0.1,
        save_dir=SAVE_DIR,
    )

    PLOT_SAVE_DIR = os.path.join(SAVE_DIR, "Plots")
    os.makedirs(PLOT_SAVE_DIR, exist_ok=True)

    for folder_name, samples in processed_data.items():
        for sample in samples:
            fig, axes = plt.subplots(2, 4, figsize=(20, 10))
            axes = axes.flatten()

            panels = [
                (sample['linearized_raw'],    'Step 1: Linearized Raw (Pre-Compensation)'),
                (sample.get('compensated_raw', sample['linearized_raw']),
                                               'Step 1.5: Thickness Compensated (Strategy A)'),
                (sample['regional_layer_img'], 'Step 2b: Regional Layer (Tier 2, r=50)'),
                (sample['equalized_raw'],      'Step 2c: Base Combined (DRC Compressed)'),
                (sample['enhanced_detail_img'],'Step 2d: Enhanced Detail (Laplacian Pyr)'),
                (sample['for_proc_img'],       'Step 3: For-Processing (Linear Fusion)'),
                (sample['final_img'],          'Step 4: For-Presentation (3-Tier DRC)'),
            ]
            for ax, (img, title) in zip(axes[:7], panels):
                ax.imshow(img, cmap='gray')
                ax.set_title(title)
                ax.axis('off')

            if sample['dcm_image'] is not None:
                axes[7].imshow(sample['dcm_image'], cmap='gray')
                axes[7].set_title('Target DICOM (GT)')
            else:
                axes[7].text(0.5, 0.5, 'No DICOM found', ha='center')
            axes[7].axis('off')

            plt.suptitle(
                f'Mammography 3-Tier Pipeline ({folder_name} - {sample["name"]})',
                fontsize=13, fontweight='bold'
            )
            plt.tight_layout()

            plot_path = os.path.join(PLOT_SAVE_DIR, f"plot_{folder_name}_{sample['name']}.png")
            plt.savefig(plot_path, dpi=150)
            plt.close(fig)
            print(f"Saved plot: {plot_path}")
