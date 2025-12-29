import numpy as np
import pandas as pd
from typing import Tuple, Union, Literal, Sequence, Optional, Dict, Any
from scipy import sparse
from scipy.signal import find_peaks, peak_widths, savgol_filter, peak_prominences
from scipy.sparse.linalg import spsolve

ArrayLike = Union[Sequence[float], np.ndarray, pd.Series]


def baseline_als(y, lam, p, niter=10):
  L = len(y)
  D = sparse.diags([1,-2,1],[0,-1,-2], shape=(L,L-2))
  w = np.ones(L)
  for i in range(niter):
    W = sparse.spdiags(w, 0, L, L)
    Z = W + lam * D.dot(D.transpose())
    z = spsolve(Z, w*y)
    w = p * (y > z) + (1-p) * (y < z)
  return z

    
def load_excel(file, index_col = 0):

    """
    ------------------------------------------------------------
    📌 Load Excel (multiple sheets) into dict of DataFrames
    ------------------------------------------------------------

    Parameters
    ----------
    file : str
        Excel filename (.xlsx)

    index_col : int (default=0)
        Column to use as DataFrame index for each sheet.

    ------------------------------------------------------------
    Returns
    -------
    df_res_all : dict
        { sheet_name : DataFrame }

    ------------------------------------------------------------
    Usage
    ------
    >>> df_res = load_excel("DEG_results.xlsx")
    >>> df_res.keys()
    dict_keys(['Group_A','Group_B','Group_C'])

    >>> df_res['Group_A'].head()
    # → first sheet as pandas DataFrame
    """
    
    xls = pd.ExcelFile(file)
    lst = xls.sheet_names
    df_res_all = {}
    for s in lst:
        df_res_all[s] = pd.read_excel(xls, s, index_col = index_col) 
        
    return df_res_all


def resample_spectra_to_matrix(
    spectra: Dict[str, Union[Tuple[ArrayLike, ArrayLike], pd.DataFrame]],
    x_min: float = None,
    x_max: float = None,
    step: float = None,
    x_new: ArrayLike = None,
    x_col: str = "shift",
    y_col: str = "intensity",
) -> pd.DataFrame:
    """
    Resample multiple (x, y) spectra onto a common Raman-shift axis
    and return a matrix (DataFrame) whose index is the Raman shift
    and whose columns are spectrum names.

    PARAMETERS
    ----------
    spectra : dict
        Dictionary of spectra. Keys are spectrum names (column names).
        Values can be:
          - (x, y) tuple: array-like objects of same length
          - DataFrame with columns [x_col, y_col]
    x_min : float, optional
        Minimum Raman shift of the common grid.
        If None, uses the minimum over all spectra.
    x_max : float, optional
        Maximum Raman shift of the common grid.
        If None, uses the maximum over all spectra.
    step : float, optional
        Step size of the common Raman-shift grid.
        If None and x_new is also None, the union of all x values is used
        (i.e., all unique x’s of all spectra).
    x_new : array-like, optional
        Custom x grid. If given, this is used as the common Raman-shift axis
        and x_min/x_max/step are ignored.
    x_col, y_col : str
        Column names used when each spectrum is given as a DataFrame.

    RETURNS
    -------
    df : pandas.DataFrame
        DataFrame with:
          - index : common Raman-shift axis (x_grid)
          - columns : spectrum names (keys of `spectra`)
          - values : interpolated intensities (float), NaN where out of range

    EXAMPLE
    -------
    >>> spec_dict = {
    ...     "sample1": (x1, y1),
    ...     "sample2": (x2, y2),
    ... }
    >>> df = resample_spectra_to_matrix(spec_dict, step=1.0)
    >>> print(df.head())
    """

    # ---- 1. 각 스펙트럼에서 x, y 뽑아서 모으기 ----
    all_x = []

    parsed = {}  # name -> (x_array, y_array)

    for name, xy in spectra.items():
        if isinstance(xy, pd.DataFrame):
            x = np.asarray(xy[x_col], dtype=float)
            y = np.asarray(xy[y_col], dtype=float)
        else:
            # assume tuple/list: (x, y)
            if not isinstance(xy, (tuple, list)) or len(xy) != 2:
                raise ValueError(f"Spectrum '{name}' must be (x, y) tuple or DataFrame.")
            x = np.asarray(xy[0], dtype=float)
            y = np.asarray(xy[1], dtype=float)

        if x.shape != y.shape:
            raise ValueError(f"Spectrum '{name}' has mismatched x and y lengths.")

        # 정렬 (x가 증가하는 순서로)
        order = np.argsort(x)
        x = x[order]
        y = y[order]

        parsed[name] = (x, y)
        all_x.append(x)

    all_x_concat = np.concatenate(all_x)

    # ---- 2. 공통 x-grid (Raman shift 축) 만들기 ----
    if x_new is not None:
        x_grid = np.asarray(x_new, dtype=float)
    else:
        if x_min is None:
            x_min = float(np.min(all_x_concat))
        if x_max is None:
            x_max = float(np.max(all_x_concat))

        if step is not None:
            # step 간격으로 등간격 grid
            # + step/2 는 floating point 문제로 마지막 점 포함하기 위한 트릭
            x_grid = np.arange(x_min, x_max + step / 2.0, step, dtype=float)
        else:
            # step도 x_new도 없으면: 모든 스펙트럼의 x를 union 해서 사용
            x_grid = np.unique(all_x_concat)

    # index가 예쁘게 되도록 정렬
    x_grid = np.asarray(x_grid, dtype=float)
    x_grid.sort()

    # ---- 3. 각 스펙트럼을 x_grid에 대해 보간 ----
    df = pd.DataFrame(index=x_grid)

    for name, (x, y) in parsed.items():
        # numpy.interp 는 경계 밖에서 edge 값을 그대로 사용하므로
        # 범위 밖은 NaN으로 바꾸어 주는 후처리 적용
        y_interp = np.interp(x_grid, x, y)
        mask_in_range = (x_grid >= x.min()) & (x_grid <= x.max())
        y_interp[~mask_in_range] = np.nan

        df[name] = y_interp

    df.index.name = "Raman_shift"

    return df


def detect_sers_peaks(
    x: ArrayLike,
    y: ArrayLike,
    min_prominence: float = 0.0,
    min_height: Optional[float] = None,
    min_distance_cm: Optional[float] = None,
    min_width_cm: Optional[float] = None,
    smooth: bool = True,
    smooth_window: int = 7,
    smooth_poly: int = 2,
    return_smoothed: bool = False,
    # ↓ 새로 추가된 옵션들
    score_col: str = "prominence",
    max_peaks: Optional[int] = None,
    min_peaks: int = 0,
    sample_name: str = ''
) -> Dict[str, Any]:
    """
    Detect peaks from a baseline-corrected SERS spectrum,
    and optionally keep only top-N peaks by a given score.

    PARAMETERS
    ----------
    x, y : array-like
        Raman shift (cm^-1) and baseline-corrected intensity.
    min_prominence, min_height, min_distance_cm, min_width_cm :
        Thresholds passed to scipy.signal.find_peaks (in cm^-1 space
        for distance/width).
    smooth : bool
        Whether to apply Savitzky-Golay smoothing before detection.
    smooth_window, smooth_poly :
        Parameters for Savitzky-Golay filter.
    return_smoothed : bool
        If True, include 'y_smooth' in the returned dict.

    score_col : {"prominence", "height", "intensity", ...}
        Column in the peak table to use as score for ranking.
        - "prominence" : peak strength (기본값, 추천)
        - "height"     : peak height (peak_heights)
        - "intensity"  : smoothed intensity at the peak
        등등을 사용할 수 있음.
    max_peaks : int, optional
        Keep at most this many peaks (top by score_col).
        If None, keep all.
    min_peaks : int, default 0
        Desired minimum number of peaks. If the number of detected
        peaks is smaller than min_peaks, all detected peaks are kept
        (부족한 개수를 채워 넣지는 않고, 있는 것만 반환).

    RETURNS
    -------
    result : dict
        {
          "peaks_df": DataFrame of detected peaks (possibly truncated),
          "properties": dict from scipy.signal.find_peaks,
          "x": original x (sorted),
          "y": original y (sorted),
          "y_smooth": smoothed y (if return_smoothed=True)
        }
    """

    # ---- 0. 입력 처리 ----
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.shape != y.shape:
        raise ValueError("x and y must have the same shape.")

    # x 오름차순 정렬
    if not np.all(np.diff(x) >= 0):
        order = np.argsort(x)
        x = x[order]
        y = y[order]

    # ---- 1. smoothing (선택) ----
    if smooth:
        n = len(y)
        win = min(smooth_window, n if n % 2 == 1 else n - 1)
        if win < 3:
            y_smooth = y.copy()
        else:
            if win % 2 == 0:
                win -= 1
            y_smooth = savgol_filter(
                y, window_length=win, polyorder=min(smooth_poly, win - 1)
            )
    else:
        y_smooth = y.copy()

    # ---- 2. x spacing 기반 distance/width 변환 ----
    dx = np.median(np.diff(x))

    distance_pts = None
    if min_distance_cm is not None and dx > 0:
        distance_pts = max(int(round(min_distance_cm / dx)), 1)

    width_pts = None
    if min_width_cm is not None and dx > 0:
        width_pts = max(int(round(min_width_cm / dx)), 1)

    # ---- 3. find_peaks 호출 ----
    peaks, properties = find_peaks(
        y_smooth,
        height=min_height,
        prominence=min_prominence,
        distance=distance_pts,
        width=width_pts,
    )

    # 피크가 하나도 없으면 빈 DF 리턴
    if peaks.size == 0:
        peaks_df = pd.DataFrame(
            columns=[
                "idx",
                "Raman_shift",
                "intensity",
                "prominence",
                "height",
                "left_base_x",
                "right_base_x",
                "fwhm_cm",
            ]
        )
        result = {
            "peaks_df": peaks_df,
            "properties": properties,
            "x": x,
            "y": y,
        }
        if return_smoothed:
            result["y_smooth"] = y_smooth
        return result

    # ---- 3-1. prominence 정보 보장 (키 이름: 'prominences') ----
    if "prominences" not in properties:
        prominences, left_bases, right_bases = peak_prominences(y_smooth, peaks)
        properties["prominences"] = prominences
        properties["left_bases"] = left_bases
        properties["right_bases"] = right_bases

    # ---- 4. FWHM 추정 ----
    widths_res = peak_widths(y_smooth, peaks, rel_height=0.5)
    widths_idx = widths_res[0]
    # left_ips, right_ips = widths_res[2], widths_res[3]  # 필요하면 사용

    fwhm_cm = widths_idx * dx

    # base (prominence 기준) 좌우 index → x 좌표
    left_bases_idx = properties.get(
        "left_bases", np.full(peaks.shape, np.nan)
    )
    right_bases_idx = properties.get(
        "right_bases", np.full(peaks.shape, np.nan)
    )

    left_base_x = np.where(
        np.isfinite(left_bases_idx),
        x[left_bases_idx.astype(int)],
        np.nan,
    )
    right_base_x = np.where(
        np.isfinite(right_bases_idx),
        x[right_bases_idx.astype(int)],
        np.nan,
    )

    # ---- 5. 전체 peak table 구성 ----
    peak_x = x[peaks]
    peak_y = y_smooth[peaks]

    prominences = properties.get(
        "prominences",
        np.full(peaks.shape, np.nan, dtype=float),
    )
    height = properties.get("peak_heights", peak_y)

    peaks_df = pd.DataFrame(
        {
            "idx": peaks,
            "Raman_shift": peak_x,
            "intensity": peak_y,
            "prominence": prominences,
            "height": height,
            "left_base_x": left_base_x,
            "right_base_x": right_base_x,
            "fwhm_cm": fwhm_cm,
        }
    )

    # ---- 6. score 기준으로 top-N 선택 ----
    if score_col not in peaks_df.columns:
        raise ValueError(
            f"score_col='{score_col}' not found in peaks_df columns: "
            f"{list(peaks_df.columns)}"
        )

    # score 내림차순 정렬 (score가 NaN인 것은 맨 뒤로)
    peaks_df = peaks_df.sort_values(
        by=score_col, ascending=False, na_position="last"
    ).reset_index(drop=True)

    n_detected = len(peaks_df)

    # max_peaks가 설정된 경우, 그 수만큼 자르되,
    # 실제 피크 수가 min_peaks보다 적으면 그냥 있는 것만 반환
    if max_peaks is not None and max_peaks > 0:
        # 실제로 자르는 개수
        n_keep = min(max_peaks, n_detected)
        peaks_df = peaks_df.iloc[:n_keep, :].copy()

    # min_peaks는 “최소 이 정도는 기대한다”는 의미로,
    # 실제 검출 개수가 min_peaks보다 적으면 그냥 있는 개수만 반환
    # (추가로 만들어서 채우진 않음). 필요하면 여기서 warning/log 출력 가능.
    if n_detected < min_peaks:
        print(f"Warning: only {n_detected} peaks detected in {sample_name} (< min_peaks={min_peaks})")

    # Raman shift 기준으로 다시 정렬하고 싶으면 이 줄을 쓰고,
    # score 순서 유지가 좋으면 이 줄은 주석 처리
    peaks_df = peaks_df.sort_values("Raman_shift").reset_index(drop=True)

    result = {
        "peaks_df": peaks_df,
        "properties": properties,
        "x": x,
        "y": y,
    }
    if return_smoothed:
        result["y_smooth"] = y_smooth

    return result


def detect_peaks_for_sers_matrix(
    df_sers: pd.DataFrame,
    min_prominence: float = 0.0,
    min_height: Optional[float] = None,
    min_distance_cm: Optional[float] = None,
    min_width_cm: Optional[float] = None,
    smooth: bool = True,
    smooth_window: int = 7,
    smooth_poly: int = 2,
    score_col: str = "prominence",
    max_peaks: Optional[int] = None,
    min_peaks: int = 0
) -> pd.DataFrame:
    """
    Apply detect_sers_peaks to each column of a SERS matrix.

    df_sers : DataFrame
        index: Raman_shift, columns: samples (each column is a spectrum)
    반환값 : long-format DataFrame
        columns: ['sample', 'idx', 'Raman_shift', 'intensity',
                  'prominence', 'height', 'left_base_x',
                  'right_base_x', 'fwhm_cm']
    """
    x = df_sers.index.values.astype(float)
    all_peaks = []

    for sample in df_sers.columns:
        y = df_sers[sample].values.astype(float)
        res = detect_sers_peaks(
            x, y,
            min_prominence=min_prominence,
            min_height=min_height,
            min_distance_cm=min_distance_cm,
            min_width_cm=min_width_cm,
            smooth=smooth,
            smooth_window=smooth_window,
            smooth_poly=smooth_poly,
            return_smoothed=False,
            score_col = score_col,
            max_peaks = max_peaks,
            min_peaks = min_peaks,
            sample_name = sample
        )
        df_peaks = res["peaks_df"].copy()
        df_peaks.insert(0, "sample", sample)
        all_peaks.append(df_peaks)

    if len(all_peaks) == 0:
        return pd.DataFrame(
            columns=[
                "sample", "idx", "Raman_shift", "intensity",
                "prominence", "height", "left_base_x",
                "right_base_x", "fwhm_cm",
            ]
        )

    return pd.concat(all_peaks, axis=0, ignore_index=True)


def make_peak_boolean_matrix(df_sers_matrix: pd.DataFrame,
                             df_peaks_long: pd.DataFrame,
                             tol: float = 1e-6) -> pd.DataFrame:
    """
    Create a boolean peak matrix with the same shape as df_sers_matrix.
    True at Raman shifts where a peak was detected for each sample.

    PARAMETERS
    ----------
    df_sers_matrix : DataFrame
        index: Raman_shift, columns: samples
    df_peaks_long : DataFrame
        Output from detect_peaks_for_sers_matrix()
        Required columns: ["sample", "Raman_shift"]
    tol : float
        Tolerance used when matching Raman shift positions (floating point issue)

    RETURNS
    -------
    df_peak_bool : DataFrame (boolean)
        Same shape as df_sers_matrix
        True = peak detected, False = no peak
    """

    # 초기 false matrix
    df_peak_bool = pd.DataFrame(
        False,
        index=df_sers_matrix.index,
        columns=df_sers_matrix.columns
    )

    # 각 sample에 대해 peak 위치를 True 로 설정
    for sample in df_sers_matrix.columns:
        # 해당 sample의 peak shift 값들
        df_peaks_sample = df_peaks_long[df_peaks_long["sample"] == sample]

        if len(df_peaks_sample) == 0:
            continue

        peak_positions = df_peaks_sample["Raman_shift"].values

        # float 문제 해결 위해 tolerance 기반 매칭
        for shift in peak_positions:
            # df_sers_matrix.index 와 정확히 일치하지 않을 수 있으므로 근접값 찾기
            idx_match = np.isclose(df_sers_matrix.index.values, shift, atol=tol)
            df_peak_bool.loc[idx_match, sample] = True

    return df_peak_bool


def make_peak_score_matrix(
    df_sers_matrix: pd.DataFrame,
    df_peaks_long: pd.DataFrame,
    score_col: str = "prominence",
    tol: float = 1e-6
) -> pd.DataFrame:
    """
    Create a peak score matrix with same shape as df_sers_matrix.
    Peak positions receive a score (e.g., prominence), non-peak = 0.

    PARAMETERS
    ----------
    df_sers_matrix : DataFrame
        index: Raman_shift, columns: samples
    df_peaks_long : DataFrame
        Output from detect_peaks_for_sers_matrix()
        Must contain columns: ["sample", "Raman_shift", score_col]
    score_col : str
        Which peak property to use as score ("prominence", "height", "intensity", ...)
    tol : float
        Floating-point tolerance when matching Raman_shift positions

    RETURNS
    -------
    df_peak_score : DataFrame (float)
        Same shape as df_sers_matrix
        Peak positions = score
        Non-peak = 0
    """

    # 초기 score matrix = 모두 0
    df_peak_score = pd.DataFrame(
        0.0,
        index=df_sers_matrix.index,
        columns=df_sers_matrix.columns
    )

    # sample별 peak score 채우기
    for sample in df_sers_matrix.columns:
        df_peaks_sample = df_peaks_long[df_peaks_long["sample"] == sample]

        if df_peaks_sample.empty:
            continue

        for _, row in df_peaks_sample.iterrows():
            shift = row["Raman_shift"]
            score = row[score_col]

            # Raman shift 매칭 (float tolerance 사용)
            idx_match = np.isclose(df_sers_matrix.index.values, shift, atol=tol)
            df_peak_score.loc[idx_match, sample] = score

    return df_peak_score


def broaden_peak_score_matrix(
    df_peak_score: pd.DataFrame,
    half_width_cm: float = 5.0,
    kernel_type: Literal["triangular", "gaussian", "rectangular"] = "triangular",
    sigma_cm: Optional[float] = None,
    normalize_kernel: bool = True,
) -> pd.DataFrame:
    """
    Convolve peak score matrix along Raman-shift axis to 'broaden' peaks.
    (후 보정용: 피크 주변 파수에도 score를 퍼뜨리는 함수)

    PARAMETERS
    ----------
    df_peak_score : DataFrame
        index   : Raman_shift (cm^-1, ascending)
        columns : samples
        values  : peak scores (e.g., prominence), non-peak = 0
    half_width_cm : float, default 5.0
        Convolution 반폭 (± cm^-1).
        예: 5.0이면 중심 ±5 cm^-1 범위까지 kernel이 퍼짐.
    kernel_type : {"triangular", "gaussian", "rectangular"}, default "triangular"
        사용할 커널 모양.
        - "triangular"   : 가운데가 가장 크고 양쪽으로 선형 감소
        - "gaussian"     : Gaussian kernel 사용
        - "rectangular"  : 윈도우 내에서 동일한 가중치 (boxcar / moving-average 형태)
    sigma_cm : float, optional
        Gaussian kernel 사용 시 표준편차 (cm^-1).
        None이면 half_width_cm의 약 1/2로 자동 설정.
    normalize_kernel : bool, default True
        True이면 kernel 합이 1이 되도록 정규화.
        False이면 원래 peak score가 주변으로 '퍼지면서' 총합이 커질 수 있음.

    RETURNS
    -------
    df_broadened : DataFrame
        index, columns는 df_peak_score와 동일.
        각 column에 대해 Raman_shift 축 방향으로 1D convolution 한 결과.
    """

    if df_peak_score.shape[0] < 2:
        # 한 점밖에 없으면 할 게 없음
        return df_peak_score.copy()

    x = df_peak_score.index.values.astype(float)

    # Raman shift 축 spacing 추정 (비균일해도 median spacing 사용)
    dx = np.median(np.diff(x))
    if dx <= 0:
        raise ValueError("Raman_shift index must be strictly increasing.")

    # half_width_cm 를 point 단위로 변환
    half_width_pts = max(int(round(half_width_cm / dx)), 1)
    kernel_size = 2 * half_width_pts + 1
    center = half_width_pts

    # ---- 1. kernel 생성 ----
    if kernel_type == "triangular":
        # 중앙에서 양쪽으로 선형 감소하는 삼각형 kernel
        # ex) half_width_pts=2 -> weights ~ [1,2,3,2,1]
        distances = np.abs(np.arange(kernel_size) - center)
        kernel = (half_width_pts + 1) - distances
        kernel[kernel < 0] = 0.0  # 이론상 필요 없지만 안전용

    elif kernel_type == "gaussian":
        # Gaussian kernel: exp(-0.5 * (x/sigma)^2)
        if sigma_cm is None:
            sigma_cm = half_width_cm / 2.0  # 대충 half_width의 절반 정도
        sigma_pts = sigma_cm / dx
        xs = np.arange(kernel_size) - center
        kernel = np.exp(-0.5 * (xs / sigma_pts) ** 2)

    elif kernel_type == "rectangular":
        # 윈도우 내 동일 가중치 (boxcar kernel)
        kernel = np.ones(kernel_size, dtype=float)

    else:
        raise ValueError(f"Unknown kernel_type: {kernel_type}")

    kernel = kernel.astype(float)

    if normalize_kernel:
        kernel_sum = kernel.sum()
        if kernel_sum > 0:
            kernel /= kernel_sum

    # ---- 2. 각 sample column에 대해 convolution ----
    arr = df_peak_score.values.astype(float)  # shape: (n_shift, n_samples)
    n_shift, n_samples = arr.shape

    broadened = np.zeros_like(arr)

    for j in range(n_samples):
        col = arr[:, j]
        broadened[:, j] = np.convolve(col, kernel, mode="same")

    df_broadened = pd.DataFrame(
        broadened,
        index=df_peak_score.index,
        columns=df_peak_score.columns,
    )

    return df_broadened

    
def cross_correlate_peak_bool(
    df_peak_bool: pd.DataFrame,
    sample1: str,
    sample2: str,
    max_lag: int = 10
):
    """
    Compute cross-correlation between two boolean peak vectors
    for wave-number lag = -max_lag ... +max_lag.

    PARAMETERS
    ----------
    df_peak_bool : DataFrame
        index : Raman shift (monotonic)
        columns : samples
        values : True/False (peak map)
    sample1, sample2 : str
        column names of df_peak_bool to compare
    max_lag : int, default 10
        compute correlation for shift differences from -max_lag to +max_lag

    RETURNS
    -------
    best_corr : float
        maximum correlation value
    best_lag : int
        lag (difference in index positions) giving that maximum correlation
    corr_dict : dict
        {lag: correlation_value}
    """

    # Boolean → integer (True=1, False=0)
    a = df_peak_bool[sample1].astype(float).values
    b = df_peak_bool[sample2].astype(float).values
    n = len(a)

    corr_dict = {}

    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # b shifted left
            a_seg = a[-lag:]
            b_seg = b[:n + lag]
        elif lag > 0:
            # b shifted right
            a_seg = a[:n - lag]
            b_seg = b[lag:]
        else:  # lag == 0
            a_seg = a
            b_seg = b

        if len(a_seg) == 0:
            corr = 0.0
        else:
            # simple correlation = dot product of 0/1 vectors
            corr = np.sum(a_seg * b_seg)

        corr_dict[lag] = float(corr)

    # find max correlation
    best_lag = max(corr_dict, key=lambda k: corr_dict[k])
    best_corr = corr_dict[best_lag]

    return best_corr, best_lag, corr_dict


def group_wise_peak_aggregation( df_peak_score, groups, r_th = 0.5 ):

    df_tmp = df_peak_score.copy(deep = True)
    cols = df_tmp.columns.values
    
    group_ary = np.array(groups)
    group_lst = list(set( groups ))
    group_lst.sort()

    df_rwn = pd.DataFrame( 0, index = df_tmp.index, columns = group_lst )
    
    score_rev = []
    for j, g in enumerate(group_lst):
        b = group_ary == g
    
        mnp = df_tmp.loc[:,cols[b]].median(axis = 1)
        bx = (df_tmp.loc[:,cols[b]] > 0).sum(axis = 1) >= b.sum()*r_th

        df_rwn.loc[bx, g] = mnp[bx]
        score_rev = score_rev + list(mnp[bx])
        for c in cols[b]:
            df_tmp.loc[bx, c] = mnp[bx]
            df_tmp.loc[~bx, c] = 0
    
    return df_rwn, score_rev


def get_peak_rm_shifts( df_peak_score_rev ):
    group_lst = df_peak_score_rev.columns.values.tolist()
    rm_shifts = {}
    for g in group_lst:
        b = df_peak_score_rev[g] > 0
        rm_shifts[g] = df_peak_score_rev.index.values[b].tolist()

    return rm_shifts


def peak_rm_shifts_hit_rate( df_peak_score_broadened, rm_shifts_dct ):

    group_lst = list( rm_shifts_dct.keys() )
    df_hits = pd.DataFrame( 0, index = group_lst, columns = df_peak_score_broadened.columns.values.tolist() )
    for g in group_lst:
        hits = (df_peak_score_broadened.loc[ rm_shifts_dct[g] ] > 0).mean()
        df_hits.loc[g] = hits

    return df_hits

    