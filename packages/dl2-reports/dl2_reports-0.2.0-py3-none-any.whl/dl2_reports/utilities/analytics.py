from __future__ import annotations
from typing import List
import numpy as np
import pandas as pd

def calculate_trend_coefficients(x: np.ndarray, y: np.ndarray, degree: int = 1) -> List[float]:
    """
    Calculate the coefficients of a polynomial trend line that fits the given data.

    Args:
        x: A numpy array of x values.
        y: A numpy array of y values.
        degree: The degree of the polynomial trend line.

    Returns:
        A list of coefficients for the polynomial trend line, starting from the lowest degree (intercept).
    """
    if degree < 1:
        raise ValueError("Degree must be at least 1.")
    
    def _ensure_numeric(arr):
        if np.issubdtype(arr.dtype, np.number):
            return arr
        # Try converting to datetime first, then to numeric
        try:
            return pd.to_datetime(arr).view(np.int64) // 10**9
        except:
            return pd.to_numeric(arr, errors='coerce')

    x = _ensure_numeric(x)
    y = _ensure_numeric(y)

    # Drop NaNs
    mask = ~np.isnan(x) & ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) != len(y_clean):
        raise ValueError("The length of x and y must be the same.")
    if len(x_clean) < degree + 1:
        raise ValueError(f"At least {degree + 1} valid data points are required to fit a polynomial of degree {degree}.")
    
    coefficients = np.polyfit(x_clean, y_clean, degree)
    # Reverse to return [intercept, slope, ...] (ascending order of power)
    return coefficients[::-1].tolist()
