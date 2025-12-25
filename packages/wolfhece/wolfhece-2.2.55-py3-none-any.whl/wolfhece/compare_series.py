import numpy as np
import logging
from pathlib import Path
import pandas as pd

"""
Reference : https://hess.copernicus.org/articles/27/2397/2023/hess-27-2397-2023.html - "When best is the enemy of good – critical evaluation of performance criteria in hydrological models"

Definitions :
 - beta = mean(simulated) / mean(observed)
 - beta_n = (mean(simulated) - mean(observed)) / standard_deviation(observed)
 - alpha = standard_deviation(simulated) / standard_deviation(observed)
 - CV = standard_deviation / mean
 - gamma = CV(simulated) / CV(observed)
 - B_rel = (FDC_simulated - FDC_observed) / FDC_observed
 - B_rel_mean = mean(B_rel)
 - B_res = B_rel - B_rel_mean
 - B_area = integral(B_res)
 - r = correlation coefficient between observed and simulated data
 - r_s = Spearman rank correlation coefficient between observed and simulated data
"""

def Nash_Sutcliffe_efficiency(observed, simulated):
    """
    Calculate the Nash-Sutcliffe efficiency coefficient (NSE) between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Nash-Sutcliffe efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate the numerator and denominator for the NSE
    numerator = np.sum((observed - simulated) ** 2)
    denominator = np.sum((observed - np.mean(observed)) ** 2)

    # Calculate and return the NSE
    nse = 1 - (numerator / denominator) if denominator != 0 else np.nan

    return nse

def Kling_Gupta_efficiency(observed, simulated):
    """
    Calculate the Kling-Gupta efficiency coefficient (KGE) between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Kling-Gupta efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate the components for the KGE
    r = np.corrcoef(observed, simulated)[0, 1]
    alpha = np.std(simulated) / np.std(observed)
    beta = np.mean(simulated) / np.mean(observed)

    # Calculate and return the KGE
    kge = 1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)
    return kge

def modified_Kling_Gupta_efficiency(observed, simulated):
    """
    Calculate the modified Kling-Gupta efficiency coefficient (KGE') between observed and simulated data.

    A modified Kling-Gupta efficiency was proposed by Kling et al. (2012).
    The coefficient of variation is used instead of the standard deviation
    to ensure that bias and variability are not cross-correlated

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The modified Kling-Gupta efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate the components for the modified KGE
    r = np.corrcoef(observed, simulated)[0, 1]
    # alpha = np.std(simulated) / np.std(observed)
    beta = np.mean(simulated) / np.mean(observed)
    cv_observed = np.std(observed) / np.mean(observed)
    cv_simulated = np.std(simulated) / np.mean(simulated)

    # Calculate and return the modified KGE
    kge_prime = 1 - np.sqrt((r - 1) ** 2 + (beta - 1) ** 2 + (cv_simulated / cv_observed - 1) ** 2)
    return kge_prime

def modified_Kling_Gupta_efficiency_Spearman(observed, simulated):
    """
    Calculate the modified Kling-Gupta efficiency coefficient (KGE') between observed and simulated data.

    A modified Kling-Gupta efficiency was proposed by Kling et al. (2012).
    The coefficient of variation is used instead of the standard deviation
    to ensure that bias and variability are not cross-correlated

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The modified Kling-Gupta efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate the components for the modified KGE
    r = Spearman_Rank_Correlation_Coefficient(observed, simulated)
    # alpha = np.std(simulated) / np.std(observed)
    beta = np.mean(simulated) / np.mean(observed)
    cv_observed = np.std(observed) / np.mean(observed)
    cv_simulated = np.std(simulated) / np.mean(simulated)

    # Calculate and return the modified KGE
    kge_prime_sp = 1 - np.sqrt((r - 1) ** 2 + (beta - 1) ** 2 + (cv_simulated / cv_observed - 1) ** 2)
    return kge_prime_sp

def Normalised_Diagnostic_efficiency(observed, simulated):
    """
    Calculate the Diagnostic efficiency coefficient (DE) between observed and simulated data.

    Schwemmle et al. (2021) used Flow Duration Curve (FDC)-based parameters to account
    for variability and bias in another KGE variant: the diagnostic efficiency.
    This criterion is based on constant, dynamic, and timing errors and aims to provide
    a stronger link to hydrological processes (Schwemmle et al., 2021)

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Diagnostic efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    FDC_observed = np.sort(observed)
    FDC_simulated = np.sort(simulated)

    r = np.corrcoef(FDC_observed, FDC_simulated)[0, 1]

    B_rel = (FDC_simulated - FDC_observed) / FDC_observed
    B_rel_mean = np.mean(B_rel)
    B_res = B_rel - B_rel_mean
    B_area = np.trapz(B_res, dx=1)  # Assuming uniform spacing for simplicity

    de = 1 - np.sqrt(B_rel_mean ** 2 + (r - 1) ** 2 + B_area ** 2)

    return de

def Liu_mean_efficiency(observed, simulated):
    """
    Calculate the Liu mean efficiency coefficient (LME) between observed and simulated data.

    The Liu mean efficiency is a variant of the Nash-Sutcliffe efficiency that
    accounts for the mean of the observed data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Liu mean efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    r = np.corrcoef(observed, simulated)[0, 1]
    alpha = np.std(simulated) / np.std(observed)
    beta = np.mean(simulated) / np.mean(observed)

    lme = 1 - np.sqrt((r*alpha - 1) ** 2 + (beta - 1) ** 2)

    return lme

def Lee_Choi_mean_efficiency(observed, simulated):
    """
    Calculate the Lee-Choi mean efficiency coefficient (LCME) between observed and simulated data.

    The Lee-Choi mean efficiency is a variant of the Nash-Sutcliffe efficiency that
    accounts for the mean of the observed data and is less sensitive to outliers.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Lee-Choi mean efficiency coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    r = np.corrcoef(observed, simulated)[0, 1]
    alpha = np.std(simulated) / np.std(observed)
    beta = np.mean(simulated) / np.mean(observed)

    lcme = 1 - np.sqrt((r*alpha - 1) ** 2 + (r / alpha -1) ** 2 + (beta - 1) ** 2)

    return lcme

def Dynamic_Time_Warping_distance(series1, series2):
    """
    Calculate the Dynamic Time Warping (DTW) distance between two time series.

    The time series can be of different lengths, and DTW finds the optimal alignment
    between them by minimizing the distance.

    :param series1: First time series as a list or numpy array.
    :param series2: Second time series as a list or numpy array.
    :return: The DTW distance between the two time series.
    """
    from dtaidistance import dtw

    if isinstance(series1, pd.Series):
        series1 = series1.values

    if isinstance(series2, pd.Series):
        series2 = series2.values

    return dtw.distance_fast(series1, series2)

def Dynamic_Time_Warping_distance_normalized(series1, series2):
    """
    Calculate the normalized Dynamic Time Warping (DTW) distance between two time series.

    The DTW distance is normalized by the length of the path to provide a relative measure.

    :param series1: First time series as a list or numpy array.
    :param series2: Second time series as a list or numpy array.
    :return: The normalized DTW distance between the two time series.
    """
    from dtaidistance import dtw

    if isinstance(series1, pd.Series):
        series1 = series1.values

    if isinstance(series2, pd.Series):
        series2 = series2.values

    path, distance = dtw.warping_path_fast(series1, series2, include_distance=True)

    if len(path) == 0:
        return 0.0

    return distance / len(path)


def Root_Mean_Square_Error(observed, simulated):
    """
    Calculate the Root Mean Square Error (RMSE) between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The RMSE value.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate RMSE
    rmse = np.sqrt(np.mean((observed - simulated) ** 2))

    return rmse

def Mean_Absolute_Error(observed, simulated):
    """
    Calculate the Mean Absolute Error (MAE) between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The MAE value.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate MAE
    mae = np.mean(np.abs(observed - simulated))

    return mae

def Mean_Absolute_Percentage_Error(observed, simulated):
    """
    Calculate the Mean Absolute Percentage Error (MAPE) between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The MAPE value.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate MAPE
    mape = np.mean(np.abs((observed - simulated) / observed)) * 100

    return mape

def Pearson_Correlation_Coefficient(observed, simulated):
    """
    Calculate the Pearson correlation coefficient between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Pearson correlation coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate Pearson correlation coefficient
    r = np.corrcoef(observed, simulated)[0, 1]

    return r

def Spearman_Rank_Correlation_Coefficient(observed, simulated):
    """
    Calculate the Spearman rank correlation coefficient between observed and simulated data.

    :param observed: Array-like structure containing observed data values.
    :param simulated: Array-like structure containing simulated data values.
    :raises ValueError: If the lengths of observed and simulated data do not match.
    :return: The Spearman rank correlation coefficient.
    """

    if isinstance(observed, pd.Series):
        observed = observed.values

    if isinstance(simulated, pd.Series):
        simulated = simulated.values

    if len(observed) != len(simulated):
        raise ValueError("Observed and simulated data must have the same length.")

    # Convert to numpy arrays for calculations
    observed = np.array(observed)
    simulated = np.array(simulated)

    # Calculate Spearman rank correlation coefficient
    from scipy.stats import spearmanr
    r, _ = spearmanr(observed, simulated)

    return r

def normalize_series(series):
    """
    Normalize a time series to the range [0, 1].

    :param series: Array-like structure containing the time series data.
    :return: Normalized time series as a numpy array.
    """
    if isinstance(series, pd.Series):
        series = series.values

    series = np.array(series)
    min_val = np.min(series)
    max_val = np.max(series)

    if max_val - min_val == 0:
        return np.zeros_like(series)  # Avoid division by zero

    normalized_series = (series - min_val) / (max_val - min_val)

    return normalized_series