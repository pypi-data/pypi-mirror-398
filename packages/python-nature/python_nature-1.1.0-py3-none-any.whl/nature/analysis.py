"""Centralized analysis functions for genetic programming codons.

This module provides a caching Analyzer class with statistical, mathematical,
and time-series analysis methods used by codons throughout the framework.
"""

from __future__ import annotations

from typing import Any, Callable
import numpy as np
import pandas as pd
from cachetools import LRUCache
from functools import wraps

try:
    from numba import jit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    # Fallback decorator that does nothing
    def jit(*args, **kwargs):
        def decorator(func):
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator


class PandasAnalyzer:
    """Provides cached statistical and mathematical analysis methods.

    This class centralizes analysis functions used by codons, with LRU caching
    to avoid redundant computations on the same data.

    Args:
        capacity: Maximum number of cached results. 0 means unlimited cache.
    """

    def __init__(self, capacity: int = 0):
        """Initialize analyzer with specified cache capacity."""
        self.capacity = capacity
        if capacity > 0:
            self._cache: dict[str, LRUCache] = {}
        else:
            self._cache = {}

    def _get_cache_key(self, *args: Any) -> int:
        """Generate O(1) cache key from arguments.

        Uses object IDs for DataFrames/Series and hash for primitives.
        """
        key_parts = []
        for arg in args:
            if isinstance(arg, (pd.DataFrame, pd.Series)):
                key_parts.append(id(arg))
            elif isinstance(arg, np.ndarray):
                key_parts.append(id(arg))
            else:
                key_parts.append(hash(arg))
        return hash(tuple(key_parts))

    def _get_method_cache(self, method_name: str) -> dict[int, Any]:
        """Get or create cache for a specific method."""
        if self.capacity > 0:
            if method_name not in self._cache:
                self._cache[method_name] = LRUCache(maxsize=self.capacity)
            return self._cache[method_name]  # type: ignore
        else:
            if method_name not in self._cache:
                self._cache[method_name] = LRUCache(maxsize=1)
            return self._cache[method_name]  # type: ignore

    # ========================================================================
    # Arithmetic Operations
    # ========================================================================

    def add(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Add two series or series and scalar."""
        return a + b

    def sub(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Subtract two series or series and scalar."""
        return a - b

    def mul(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Multiply two series or series and scalar."""
        return a * b

    def div(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Divide two series or series and scalar."""
        return a / b

    def pow(self, a: pd.Series, b: float) -> pd.Series:
        """Raise series to power."""
        return a**b

    def abs(self, a: pd.Series) -> pd.Series:
        """Absolute value of series."""
        return a.abs()

    def neg(self, a: pd.Series) -> pd.Series:
        """Negate series."""
        return -a

    # ========================================================================
    # Mathematical Functions
    # ========================================================================

    def log(self, a: pd.Series) -> pd.Series:
        """Natural logarithm."""
        return np.log(a.clip(lower=1e-10))  # type: ignore

    def exp(self, a: pd.Series) -> pd.Series:
        """Exponential function."""
        return np.exp(a.clip(upper=100))  # type: ignore

    def sin(self, a: pd.Series) -> pd.Series:
        """Sine function."""
        return np.sin(a)  # type: ignore

    def cos(self, a: pd.Series) -> pd.Series:
        """Cosine function."""
        return np.cos(a)  # type: ignore

    def tanh(self, a: pd.Series) -> pd.Series:
        """Hyperbolic tangent."""
        return np.tanh(a)  # type: ignore

    def sigmoid(self, a: pd.Series, alpha: float = 1.0) -> pd.Series:
        """Sigmoid activation function.

        Args:
            a: Input series
            alpha: Scaling factor for steepness (default 1.0)
        """
        return 1.0 / (1.0 + np.exp(-alpha * a.clip(-100, 100)))  # type: ignore

    def sqrt(self, a: pd.Series) -> pd.Series:
        """Square root."""
        return np.sqrt(a.clip(lower=0))  # type: ignore

    def log1p(self, a: pd.Series) -> pd.Series:
        """Natural logarithm of 1 + x."""
        return np.log1p(a)  # type: ignore

    # ========================================================================
    # Comparison Operations
    # ========================================================================

    def gt(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Greater than comparison."""
        return (a > b).astype(float)

    def lt(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Less than comparison."""
        return (a < b).astype(float)

    def eq(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Equality comparison."""
        return (a == b).astype(float)

    def ne(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Not equal comparison."""
        return (a != b).astype(float)

    def min(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Element-wise minimum."""
        return np.minimum(a, b)  # type: ignore

    def max(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Element-wise maximum."""
        return np.maximum(a, b)  # type: ignore

    def is_between(
        self, a: pd.Series, lower: float, upper: float, upper_inclusive: bool = True
    ) -> pd.Series:
        """Check if values are between bounds.

        Args:
            a: Input series
            lower: Lower bound (inclusive)
            upper: Upper bound
            upper_inclusive: If True, upper bound is inclusive (<=). If False, exclusive (<).
        """
        if upper_inclusive:
            return ((a >= lower) & (a <= upper)).astype(float)
        else:
            return ((a >= lower) & (a < upper)).astype(float)

    # ========================================================================
    # Logical Operations
    # ========================================================================

    def bitwise_and(self, a: pd.Series, b: pd.Series) -> pd.Series:
        """Bitwise AND of two boolean series."""
        return (a.astype(bool) & b.astype(bool)).astype(float)

    def bitwise_or(self, a: pd.Series, b: pd.Series) -> pd.Series:
        """Bitwise OR of two boolean series."""
        return (a.astype(bool) | b.astype(bool)).astype(float)

    def bitwise_not(self, a: pd.Series) -> pd.Series:
        """Bitwise NOT of boolean series."""
        return (~a.astype(bool)).astype(float)

    # ========================================================================
    # Time Series Operations
    # ========================================================================

    def diff(self, a: pd.Series, periods: int = 1) -> pd.Series:
        """First difference."""
        return a.diff(periods)

    def pct_change(self, a: pd.Series, periods: int = 1) -> pd.Series:
        """Percent change."""
        return a.pct_change(periods)

    def shift(self, a: pd.Series, periods: int = 1) -> pd.Series:
        """Shift values by periods."""
        return a.shift(periods)

    # ========================================================================
    # Rolling Window Operations
    # ========================================================================

    def rolling_mean(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling mean."""
        return a.rolling(window=window, min_periods=1).mean()

    def rolling_std(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling standard deviation."""
        return a.rolling(window=window, min_periods=1).std()

    def rolling_var(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling variance."""
        return a.rolling(window=window, min_periods=1).var()

    def rolling_min(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling minimum."""
        return a.rolling(window=window, min_periods=1).min()

    def rolling_max(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling maximum."""
        return a.rolling(window=window, min_periods=1).max()

    def rolling_median(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling median."""
        return a.rolling(window=window, min_periods=1).median()

    def rolling_sum(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling sum."""
        return a.rolling(window=window, min_periods=1).sum()

    def rolling_skew(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling skewness."""
        return a.rolling(window=window, min_periods=4).skew()

    def rolling_kurt(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling kurtosis."""
        return a.rolling(window=window, min_periods=4).kurt()

    def rolling_autocorr(self, a: pd.Series, window: int, lag: int = 1) -> pd.Series:
        """Rolling autocorrelation with specified lag.

        Uses Numba acceleration if available.
        """
        if HAS_NUMBA:
            return pd.Series(
                _numba_rolling_autocorr(a.values, window, lag), index=a.index  # type: ignore
            )
        else:

            def autocorr(x):
                if len(x) < lag + 1:
                    return np.nan
                return pd.Series(x).autocorr(lag=lag)

            return a.rolling(window=window, min_periods=lag + 1).apply(autocorr, raw=True)

    def rolling_entropy(self, a: pd.Series, window: int, bins: int = 10) -> pd.Series:
        """Rolling Shannon entropy."""

        def entropy(x):
            if len(x) < 2:
                return np.nan
            counts, _ = np.histogram(x, bins=bins)
            probs = counts / counts.sum()
            probs = probs[probs > 0]
            return -np.sum(probs * np.log(probs))

        return a.rolling(window=window, min_periods=2).apply(entropy, raw=True)

    def rolling_linear_regression(self, a: pd.Series, window: int) -> pd.Series:
        """Rolling linear regression slope."""

        def lr_slope(y):
            if len(y) < 2:
                return np.nan
            x = np.arange(len(y))
            return np.polyfit(x, y, 1)[0]

        return a.rolling(window=window, min_periods=2).apply(lr_slope, raw=True)

    # ========================================================================
    # Exponentially Weighted Moving Operations
    # ========================================================================

    def ewm_mean(self, a: pd.Series, span: int) -> pd.Series:
        """Exponentially weighted moving average."""
        return a.ewm(span=span, min_periods=1).mean()

    # ========================================================================
    # Dynamic Rolling Operations
    # ========================================================================

    def dyn_rolling(
        self, a: pd.Series, window_periods: pd.Series, stat_func: Callable[[np.ndarray], float]
    ) -> pd.Series:
        """Apply rolling statistic with dynamic window sizes.

        Args:
            a: Input series
            window_periods: Series of window sizes (one per row)
            stat_func: Statistical function to apply (e.g., np.mean, np.std)
        """
        if HAS_NUMBA:
            result = _numba_dyn_rolling_stat(
                a.values, window_periods.values.astype(np.int64), stat_func  # type: ignore
            )
            return pd.Series(result, index=a.index)
        else:
            result = np.full(len(a), np.nan)
            for i in range(len(a)):
                window = int(window_periods.iloc[i])
                if window > 0 and i >= window - 1:
                    result[i] = stat_func(a.iloc[i - window + 1 : i + 1].values)  # type: ignore
            return pd.Series(result, index=a.index)

    def dyn_rolling_mean(self, a: pd.Series, window_periods: pd.Series) -> pd.Series:
        """Dynamic rolling mean."""
        return self.dyn_rolling(a, window_periods, np.mean)

    def dyn_rolling_std(self, a: pd.Series, window_periods: pd.Series) -> pd.Series:
        """Dynamic rolling standard deviation."""
        return self.dyn_rolling(a, window_periods, np.std)

    # ========================================================================
    # Normalization
    # ========================================================================

    def minmax(self, a: pd.Series, window: int | None = None) -> pd.Series:
        """Min-max normalization to [0, 1].

        Args:
            a: Input series
            window: Rolling window size, or None for global normalization
        """
        if window is None:
            min_val = a.min()
            max_val = a.max()
            return (a - min_val) / (max_val - min_val + 1e-10)
        else:
            rolling_min = a.rolling(window=window, min_periods=1).min()
            rolling_max = a.rolling(window=window, min_periods=1).max()
            return (a - rolling_min) / (rolling_max - rolling_min + 1e-10)

    def zscore(self, a: pd.Series, window: int | None = None) -> pd.Series:
        """Z-score normalization.

        Args:
            a: Input series
            window: Rolling window size, or None for global normalization
        """
        if window is None:
            return (a - a.mean()) / (a.std() + 1e-10)
        else:
            rolling_mean = a.rolling(window=window, min_periods=1).mean()
            rolling_std = a.rolling(window=window, min_periods=1).std()
            return (a - rolling_mean) / (rolling_std + 1e-10)

    def bbands(
        self, a: pd.Series, window: int, num_std: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands.

        Returns:
            Tuple of (lower_band, middle_band, upper_band)
        """
        middle = a.rolling(window=window, min_periods=1).mean()
        std = a.rolling(window=window, min_periods=1).std()
        upper = middle + (num_std * std)
        lower = middle - (num_std * std)
        return lower, middle, upper

    def bbands_normalization(
        self, a: pd.Series, window: int, num_std: float = 2.0, k_sigma: float | None = None
    ) -> pd.Series:
        """Normalize using Bollinger Bands to [-1, 1] range.

        Values at upper band = 1, lower band = -1, middle = 0.

        Args:
            a: Input series
            window: Rolling window size
            num_std: Number of standard deviations (default 2.0)
            k_sigma: Alias for num_std for backward compatibility
        """
        # Use k_sigma if provided, otherwise use num_std
        std_multiplier = k_sigma if k_sigma is not None else num_std
        lower, middle, upper = self.bbands(a, window, std_multiplier)
        range_half = (upper - middle).replace(0, 1)  # Avoid division by zero
        return (a - middle) / range_half

    def minmax_normalization(self, a: pd.Series, window: int | None = None) -> pd.Series:
        """Alias for minmax method for backward compatibility."""
        return self.minmax(a, window)

    def zscore_normalization(self, a: pd.Series, window: int | None = None) -> pd.Series:
        """Alias for zscore method for backward compatibility."""
        return self.zscore(a, window)

    # ========================================================================
    # Technical Analysis
    # ========================================================================

    def crossed_up(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Detect when series a crosses above b."""
        if isinstance(b, (int, float)):
            b = pd.Series(b, index=a.index)
        return ((a > b) & (a.shift(1) <= b.shift(1))).astype(float)

    def crossed_down(self, a: pd.Series, b: pd.Series | float) -> pd.Series:
        """Detect when series a crosses below b."""
        if isinstance(b, (int, float)):
            b = pd.Series(b, index=a.index)
        return ((a < b) & (a.shift(1) >= b.shift(1))).astype(float)

    def sign_flipped(self, a: pd.Series, positive: bool | None = None) -> pd.Series:
        """Detect sign changes in series.

        Args:
            a: Input series
            positive: If True, only detect flips to positive. If False, only detect flips to negative.
                     If None, detect all sign changes.
        """
        sign_changed = np.sign(a) != np.sign(a.shift(1))
        if positive is True:
            # Only when current is positive and previous was not
            return (sign_changed & (np.sign(a) > 0)).astype(float)
        elif positive is False:
            # Only when current is negative and previous was not
            return (sign_changed & (np.sign(a) < 0)).astype(float)
        else:
            # All sign changes
            return sign_changed.astype(float)

    def volatility_windows(
        self,
        a: pd.Series,
        short_window: int | tuple[float, float] | None = None,
        long_window: int | str | None = None,
    ) -> pd.Series:
        """Compute volatility ratio or map volatility to window sizes.

        Two modes:
        1. Ratio mode: volatility_windows(series, short_window: int, long_window: int)
           Returns ratio of short-term to long-term volatility.

        2. Mapping mode: volatility_windows(volatility: Series, win_range: tuple, scale: str)
           Maps volatility values to window sizes in the given range.

        Args:
            a: Input series (price data in ratio mode, volatility in mapping mode)
            short_window: Short window size (int) or window range tuple (float, float)
            long_window: Long window size (int) or scaling method (str: 'linear', 'log', etc.)
        """
        if isinstance(short_window, tuple) and isinstance(long_window, str):
            # Mapping mode: map volatility to window sizes
            win_min, win_max = short_window
            scale = long_window
            volatility = a

            if scale == "linear":
                # Linear scaling from min to max
                vol_min, vol_max = volatility.min(), volatility.max()
                normalized = (volatility - vol_min) / (vol_max - vol_min + 1e-10)
                windows = win_min + normalized * (win_max - win_min)
            elif scale == "inverse":
                # Inverse scaling: high volatility -> small windows
                vol_min, vol_max = volatility.min(), volatility.max()
                normalized = (volatility - vol_min) / (vol_max - vol_min + 1e-10)
                windows = win_max - normalized * (win_max - win_min)
            else:
                # Default to linear
                vol_min, vol_max = volatility.min(), volatility.max()
                normalized = (volatility - vol_min) / (vol_max - vol_min + 1e-10)
                windows = win_min + normalized * (win_max - win_min)

            return windows.astype(int).clip(lower=int(win_min), upper=int(win_max))

        elif isinstance(short_window, int) and isinstance(long_window, int):
            # Ratio mode: compute volatility ratio
            short_vol = a.rolling(window=short_window, min_periods=1).std()
            long_vol = a.rolling(window=long_window, min_periods=1).std()
            return short_vol / (long_vol + 1e-10)
        else:
            raise ValueError(
                f"Invalid argument types: short_window={type(short_window)}, long_window={type(long_window)}"
            )

    def rsi(self, a: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index.

        Args:
            a: Input series
            window: Lookback period for RSI calculation
        """
        delta = a.diff().astype(float)
        gain = (delta.where(delta > 0, 0)).rolling(window=window, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=1).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))

    # ========================================================================
    # Weighted Average
    # ========================================================================

    def weighted_avg(self, values: pd.Series, weights: pd.Series, window: int) -> pd.Series:
        """Rolling weighted average.

        Args:
            values: Values to average
            weights: Weights for each value
            window: Rolling window size
        """

        def wavg(idx):
            if len(idx) < 1:
                return np.nan
            v = values.iloc[idx]
            w = weights.iloc[idx]
            return np.average(v, weights=w)

        return values.rolling(window=window, min_periods=1).apply(
            lambda x: wavg(x.index), raw=False
        )

    def weighted_average_columns(self, *args) -> pd.Series | float:
        """Calculate weighted average - flexible signature for backward compatibility.

        Can be called as:
        - weighted_average_columns(df, value_col, weight_col) -> float
        - weighted_average_columns(weights_tuple, values_tuple) -> Series

        Args:
            *args: Either (df, value_col, weight_col) or (weights, values)
        """
        if len(args) == 3:
            # DataFrame mode: weighted_average_columns(df, value_col, weight_col)
            df, value_col, weight_col = args
            values = df[value_col]
            weights = df[weight_col]
            return np.average(values, weights=weights)  # type: ignore
        elif len(args) == 2:
            # Direct mode: weighted_average_columns(weights_tuple, values_tuple)
            weights, values = args
            # Convert tuples to arrays if needed
            if isinstance(weights, tuple):
                weights = list(weights)
            if isinstance(values, tuple):
                values = list(values)
            # Stack the values and compute weighted average
            if isinstance(values[0], pd.Series):
                # Stack series and compute weighted average row-wise
                df_values = pd.concat(values, axis=1)
                result = df_values.mul(weights, axis=1).sum(axis=1) / sum(weights)
                return result
            else:
                # Simple scalar weighted average
                return np.average(values, weights=weights)  # type: ignore
        else:
            raise ValueError(f"Expected 2 or 3 arguments, got {len(args)}")

    # ========================================================================
    # Kalman Filter
    # ========================================================================

    def kalman_filter(
        self, a: pd.Series, process_variance: float = 1e-5, measurement_variance: float = 1e-2
    ) -> pd.Series:
        """Apply Kalman filter for smoothing noisy series.

        Args:
            a: Input series
            process_variance: Process noise covariance
            measurement_variance: Measurement noise covariance
        """
        try:
            from filterpy.kalman import KalmanFilter

            kf = KalmanFilter(dim_x=1, dim_z=1)
            kf.x = np.array([[a.iloc[0]]])
            kf.F = np.array([[1.0]])
            kf.H = np.array([[1.0]])  # type: ignore
            kf.P *= 1000.0
            kf.R = measurement_variance  # type: ignore
            kf.Q = process_variance  # type: ignore

            filtered = []
            for measurement in a.values:
                kf.predict()
                kf.update([[measurement]])
                filtered.append(kf.x[0, 0])

            return pd.Series(filtered, index=a.index)
        except ImportError:
            # Fallback to simple exponential smoothing
            return a.ewm(alpha=0.3, min_periods=1).mean()

    def kalman(
        self, a: pd.Series, process_variance: float = 1e-5, measurement_variance: float = 1e-2
    ) -> pd.Series:
        """Alias for kalman_filter for backward compatibility."""
        return self.kalman_filter(a, process_variance, measurement_variance)


# ============================================================================
# Numba-Accelerated Helper Functions
# ============================================================================

if HAS_NUMBA:

    @jit(nopython=True)
    def _numba_rolling_autocorr(values: np.ndarray, window: int, lag: int) -> np.ndarray:
        """Numba-accelerated rolling autocorrelation."""
        n = len(values)
        result = np.full(n, np.nan)

        for i in range(window - 1, n):
            start = i - window + 1
            x = values[start : i + 1]

            if len(x) < lag + 1:
                continue

            x1 = x[:-lag]
            x2 = x[lag:]

            mean1 = np.mean(x1)
            mean2 = np.mean(x2)

            cov = np.mean((x1 - mean1) * (x2 - mean2))
            std1 = np.std(x1)
            std2 = np.std(x2)

            if std1 > 0 and std2 > 0:
                result[i] = cov / (std1 * std2)

        return result

    @jit(nopython=True)
    def _numba_dyn_rolling_stat(
        values: np.ndarray, windows: np.ndarray, stat_func: Callable[[np.ndarray], float]
    ) -> np.ndarray:
        """Numba-accelerated dynamic rolling statistics."""
        n = len(values)
        result = np.full(n, np.nan)

        for i in range(n):
            window = int(windows[i])
            if window > 0 and i >= window - 1:
                start = i - window + 1
                result[i] = stat_func(values[start : i + 1])

        return result


# ============================================================================
# Global Singleton Instance
# ============================================================================

# Default analyzer with unlimited cache
analyzer = PandasAnalyzer(capacity=0)
