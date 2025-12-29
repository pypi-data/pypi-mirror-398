import numpy as np 
from scipy.stats import pearson3, gamma, norm


def pe3_std(runoff,):
    """
    Compute the Standard Runoff Index (SRI) using Pearson Type III distribution fitting.
    
    Parameters:
    -----------
    runoff : np.ndarray
        A 1D numpy array of runoff values.
    
    Returns:
    --------
    sri : np.ndarray
        A numpy array of the same shape as `runoff`, containing SRI values.
        Invalid (NaN) values in the input are preserved.
    """
    runoff = np.asarray(runoff)
    sri = np.full_like(runoff, fill_value=np.nan, dtype=float)

    # Identify valid (non-NaN) entries
    valid_mask = np.isfinite(runoff)
    valid_data = runoff[valid_mask]

    if len(valid_data) < 10:
        raise ValueError("Not enough valid data points to fit Pearson III distribution.")

    # Fit Pearson III distribution
    shape, loc, scale = pearson3.fit(valid_data)

    # Compute CDF for valid data
    cdf_vals = pearson3.cdf(runoff[valid_mask], shape, loc=loc, scale=scale)
    cdf_vals = np.clip(cdf_vals, 1e-6, 1 - 1e-6)  # Avoid -inf/inf

    # Convert CDF to standard normal
    sri[valid_mask] = norm.ppf(cdf_vals)

    return sri

def pe3_std_to_value(sri_values, runoff_data):
    """
    Convert SRI values back to runoff using inverse Pearson Type III transformation.

    Parameters:
    -----------
    sri_values : np.ndarray
        A 1D array of standard runoff index (SRI) values (can be scalar or array).
    runoff_data : np.ndarray
        A 1D array of historical runoff data used to fit the Pearson Type III distribution.

    Returns:
    --------
    runoff_estimates : np.ndarray
        A numpy array of estimated runoff values corresponding to the input SRI values.
    """

    runoff_data = np.asarray(runoff_data)
    sri_values = np.asarray(sri_values)

    # Extract valid runoff data
    valid_data = runoff_data[np.isfinite(runoff_data)]

    if len(valid_data) < 10:
        raise ValueError("Not enough valid data to fit Pearson III distribution.")

    # Fit Pearson III to runoff data
    shape, loc, scale = pearson3.fit(valid_data)

    # Convert SRI → CDF
    cdf_vals = norm.cdf(sri_values)
    cdf_vals = np.clip(cdf_vals, 1e-6, 1 - 1e-6)  # Avoid extremes

    # Convert CDF → runoff using Pearson III PPF
    runoff_estimates = pearson3.ppf(cdf_vals, shape, loc=loc, scale=scale)

    return runoff_estimates


def gamma_std(runoff):
    """
    Compute Standard Runoff Index (SRI) using Gamma distribution fitting.

    Parameters:
    -----------
    runoff : np.ndarray
        A 1D array of runoff values.

    Returns:
    --------
    sri : np.ndarray
        A numpy array of SRI values corresponding to the input runoff data.
    """
    runoff = np.asarray(runoff)
    sri = np.full_like(runoff, fill_value=np.nan, dtype=float)

    # 去除 NaN 进行拟合
    valid_mask = np.isfinite(runoff)
    valid_data = runoff[valid_mask]

    if len(valid_data) < 10:
        raise ValueError("Not enough valid data for Gamma fitting.")

    # 拟合 Gamma 分布：shape, loc, scale
    shape, loc, scale = gamma.fit(valid_data, floc=0)  # 通常 loc 固定为 0 更稳定

    # 计算 CDF
    cdf = gamma.cdf(runoff[valid_mask], shape, loc=loc, scale=scale)
    cdf = np.clip(cdf, 1e-6, 1 - 1e-6)

    # 转换为标准正态值（SRI）
    sri[valid_mask] = norm.ppf(cdf)

    return sri


def gamma_std_to_value(sri_values, runoff_data):
    """
    Convert SRI values back to runoff values using Gamma distribution fitting.

    Parameters:
    -----------
    sri_values : np.ndarray
        A scalar or 1D array of SRI values.
    runoff_data : np.ndarray
        The 1D array of historical runoff data used to fit the Gamma distribution.

    Returns:
    --------
    runoff_estimates : np.ndarray
        A numpy array of estimated runoff values corresponding to the input SRI values.
    """
    runoff_data = np.asarray(runoff_data)
    sri_values = np.asarray(sri_values)

    valid_data = runoff_data[np.isfinite(runoff_data)]
    if len(valid_data) < 10:
        raise ValueError("Not enough valid data to fit Gamma distribution.")

    # 拟合 Gamma 分布
    shape, loc, scale = gamma.fit(valid_data, floc=0)

    # 将 SRI 转换为 Gamma 的分布上对应的百分位
    cdf_vals = norm.cdf(sri_values)
    cdf_vals = np.clip(cdf_vals, 1e-6, 1 - 1e-6)

    # 百分位函数反推径流量
    runoff_estimates = gamma.ppf(cdf_vals, shape, loc=loc, scale=scale)

    return runoff_estimates






