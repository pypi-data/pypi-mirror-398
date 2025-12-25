"""
Series and DataFrame codon definitions for the nature genetic programming framework.

This module contains general-purpose series/dataframe operations including:
- Series arithmetic (SAdd, SSub, SMul, SDiv, SDiff, SMax, SMean, SMin, SAbs, SNeg)
- Series transforms (SPctChange, Shift, SignSeries, NormMinMax, NormZScore)
- Series indexing (ILoc, DynILoc, SILocIdx, SLocMask, SLoc, IndexSeries, DfCol, RandomCol)
- Series boolean operations (TrueSeries, SAnd, SAll, SAny, SOr, SNot, SLogicGate, SCmpGate)
- Series comparison (SeriesGt, SeriesLt, SeriesEq, SeriesGeq, SeriesLeq)
- Difference operations (Diff, NPctChange, NDiff, ComparativeResidual, LagResidual, DeriveWindow)
- Rolling operations (Rolling, RollingMean, RollingMed, RollingStd, RollBband, RollMode, etc.)
- Series math (SSin2pi, SLog, SLog1p, SSigmoid, STanh, SPow, SDiscretize, SExp, SSqrt, SCos, SSin)
- Signal processing (WaveletTransform, CastSeries, KalmanSmoothV2)
- Aggregation (Mean, WMean, DfMean, SWMean)
- DataFrame operations (BuildDf, DfExtend, DfHStack, DfConcat)
- Advanced operations (various volatility, Bollinger bands, RSI, dynamic rolling, etc.)
"""

import math
import random
import sys
import traceback
import warnings
from collections import defaultdict
from functools import reduce
from typing import Any, Callable, Iterable, Protocol, Sequence, Tuple, cast

import numpy as np
import pandas as pd
import pywt
from pandas import DataFrame, Index, Series
from sklearn.calibration import expit

from nature.codon import Codon
from nature.codons.primitives import Cast, Locator
from nature.random import Random
from nature.utils import flatten

# NOTE: Many series operations in this module use `self.anal` for optimized operations.
# The `anal` attribute is an Analyzer instance that provides vectorized pandas operations.
# This is injected via the Codon base class in actual usage.


class BbandsChan(Codon):
    """Create Bollinger Bands channel."""

    def __call__(self, x: Series, win: int, k_sigma: float) -> tuple[Series, Series]:
        mu = self.anal.rolling_mean(x, win)
        sigma = self.anal.rolling_std(x, win)
        lower = mu - k_sigma * sigma
        upper = mu + k_sigma * sigma
        return (lower, upper)

    @property
    def func_name(self) -> str:
        return "bbands_channel"


class BuildDf(Codon):
    """Build DataFrame from multiple Series."""

    def __init__(
        self,
        col_type: type | str | Sequence[str | type] = Series,
        n_cols: int = 1,
        dtype: type | None = None,
        axis: int = 1,
        min_depth: int | None = None,
        max_depth: int | None = None,
        out: type | str = DataFrame,
        **params,
    ) -> None:
        super().__init__(min_depth, max_depth, out=out, n_columns=n_cols, **params)
        col_type = tuple(flatten(col_type))
        self.arg_types = [col_type] * n_cols
        self.arg_names = [f"x{i+1}" for i in range(n_cols)]
        self.dtype = dtype
        self.axis = axis

    def __call__(self, *series_list: Series) -> DataFrame:
        for sig in series_list:
            sig.name = None

        df = pd.concat(
            [s.astype(self.dtype or s.dtype) for s in series_list],
            axis=cast(Any, self.axis),
        )

        for i, c in enumerate(df.columns):
            df[c].attrs = series_list[i].attrs.copy()

        return df


class CastSeries(Cast):
    """Cast Series to specific dtype."""

    def __init__(self, as_type: type | None = None, **kwargs):
        super().__init__(**kwargs)
        self.as_type = as_type

    def __call__(self, x: Series) -> Series:
        y = super()(x)
        return cast(Any, y.astype(self.as_type) if self.as_type else y)

    @property
    def func_name(self):
        return "cast"


class DeriveWindow(Codon):
    """Derive a window size from base and multiplier."""

    def __init__(self, min: int = 2, **kwargs) -> None:
        super().__init__(params={"min": min}, **kwargs)
        self.min_window = min

    def __call__(self, win_base: int, mult: float) -> int:
        return int(max(self.min_window, mult * win_base))


# === DataFrame/Series Selectors ===


class DfCol(Codon):
    """Extract a column from a DataFrame by name."""

    def __init__(
        self,
        name: str | int,
        df_type: type | str = DataFrame,
        bias: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(
            bias=bias,
            col_name=name,
            arg_types={"df": kwargs.get("arg_df", df_type or DataFrame)},
            func_name=f"col_{name}",
            **kwargs,
        )
        self.col_name = name

    def __call__(self, df: DataFrame) -> Series:
        return df[self.col_name]


class DfConcat(Codon):
    """Concatenate multiple DataFrames."""

    def __init__(
        self,
        df_type: type | tuple[type, ...] = DataFrame,
        n_dfs: int = 1,
        min_depth: int | None = None,
        max_depth: int | None = None,
        out: type = DataFrame,
        **params,
    ) -> None:
        super().__init__(min_depth, max_depth, out=out, n_dfs=n_dfs, **params)
        df_type = tuple(flatten(df_type))
        self.arg_types = [df_type] * n_dfs
        self.arg_names = [f"X{i+1}" for i in range(n_dfs)]

    def __call__(self, *dfs: DataFrame) -> DataFrame:
        for sig in dfs:
            sig.name = None

        return pd.concat(dfs, axis=1)

    @property
    def func_name(self) -> str:
        return "df_concat"


class DfExtend(Codon):
    """Extend DataFrame with additional columns."""

    def __init__(self, n: int, axis: int, arg_column: str | type = Series, **kwargs):
        super().__init__(**kwargs)
        self.n = n
        self.axis = axis

        self.arg_names = ["df"]
        self.arg_types = [(kwargs.get("arg_df", DataFrame),)]
        for i in range(n):
            self.arg_names.append(f"x{i}")
            self.arg_types.append((arg_column,))

    def __call__(self, df: DataFrame, *columns: DataFrame) -> DataFrame:
        df = pd.concat(flatten([df, columns]), axis=cast(Any, self.axis))
        df.columns = list(range(df.shape[1]))
        return df


class DfHStack(Codon):
    """Horizontal stack of column collections into DataFrame."""

    def __init__(
        self, n: int = 1, column_collection_type: str | type | Sequence[str | type] = list, **kwargs
    ):
        super().__init__(**kwargs)
        self.n = n
        self.arg_names = []
        self.arg_types = []
        for i in range(n):
            self.arg_names.append(f"x{i}")
            self.arg_types.append(flatten(column_collection_type))

    def __call__(self, *column_collections: list[Series]) -> DataFrame:
        df = pd.concat(flatten(column_collections), axis=1)
        df.columns = list(range(df.shape[1]))
        return df

    @property
    def func_name(self) -> str:
        return "df_hstack"


class DfMean(Codon):
    """Mean of DataFrame along axis."""

    def __init__(
        self,
        axis: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(params={"axis": axis}, **kwargs)
        self.axis = axis

    def __call__(self, df: DataFrame) -> Series:
        return df.mean(axis=cast(Any, self.axis))

    @property
    def func_name(self):
        return f"df_mean_axis_{self.axis}"


class Diff(Codon):
    """Difference with fixed window."""

    def __init__(self, win: int, **kwargs):
        super().__init__(params={"win": win}, **kwargs)

    def __call__(self, x: Series) -> Series:
        return x.diff(self.params["win"])


class DynBbandsChan(Codon):
    """Bollinger Bands with dynamic window sizes."""

    def __call__(self, x: Series, wins: Series, k_sigma: float) -> tuple[Series, Series]:
        mu = self.anal.dyn_rolling_mean(x, wins)
        sigma = self.anal.dyn_rolling_std(x, wins)
        lower = mu - k_sigma * sigma
        upper = mu + k_sigma * sigma
        return (lower, upper)

    @property
    def func_name(self) -> str:
        return "dynamic_bbands_channel"


class DynILoc(Codon):
    """ILoc indexing with dynamic index."""

    def __call__(self, x: Series, i: int) -> Any:
        try:
            return x.iloc[i].astype(self.ret_types[0])
        except:
            traceback.print_exc()
            print("x.shape:", x.shape)
            print("i:", i)
            return np.nan

    @property
    def func_name(self):
        return f"iloc"


class DynRoll(Codon):
    """Rolling operation with dynamic window sizes."""

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        # Map string names to actual numpy functions
        self._stat_funcs = {
            "mean": np.mean,
            "std": np.std,
            "var": np.var,
            "min": np.min,
            "max": np.max,
            "median": np.median,
            "sum": np.sum,
        }

    def __call__(self, x: Series, wins: Series) -> Series:
        stat_func = self._stat_funcs.get(self.name, np.mean)
        return self.anal.dyn_rolling(x, wins, stat_func)

    @property
    def func_name(self):
        return f"dyn_rolling_{self.name}"


class ILoc(Codon):
    """ILoc indexing with fixed index."""

    def __init__(self, i: int, **kwargs) -> None:
        super().__init__(
            idx=i,
            **kwargs,
        )
        self.idx: int = i

    def __call__(self, x: Series) -> Any:
        return x.iloc[self.idx].astype(self.ret_types[0])

    @property
    def func_name(self):
        return f"iloc_{self.idx}"


class IndexSeries(Codon):
    """Index into a Series with dynamic index."""

    def __init__(
        self,
        index_type: type,
        series_type: type = Series,
        out: type = float,
        min_depth: int | None = None,
        max_depth: int | None = None,
        memo=False,
        bias: float = 1,
        **params,
    ) -> None:
        super().__init__(
            min_depth,
            max_depth,
            arg_types=dict(x=series_type, idx=index_type),
            out=out,
            memo=memo,
            bias=bias,
            **params,
        )

    def __call__(self, x: Series, idx: Any) -> Any:
        return x[idx]


class KalmanSmoothV2(Codon):
    """Kalman filter smoothing.

    Uses the simplified Kalman filter from PandasAnalyzer.
    The trans_mult parameter maps to process variance (higher = more responsive to changes).
    """

    def __call__(self, x: Series, win: int, trans_mult: float) -> Series:
        # Map trans_mult to process_variance (higher trans_mult = higher process variance)
        process_variance = trans_mult * 1e-4
        return self.anal.kalman_filter(x, process_variance=process_variance)


class LagResidual(Codon):
    """Residual relative to lagged value."""

    def __call__(self, x: Series, lag: int) -> Series:
        x_ref = x.shift(lag)
        x_ref.replace(0.0, np.nan, inplace=True)
        y = (x - x_ref) / x_ref
        return y.replace(np.inf, 0)


class Mean(Codon):
    """Mean of multiple scalar values."""

    def __init__(
        self,
        value_type: type | tuple[type, ...] = float,
        n: int | None = None,
        **params,
    ) -> None:
        super().__init__(**params)
        arg_types = []
        arg_names = []

        for i in range(n or self.arity):
            arg_names.append(f"x{i+1}")
            arg_types.append(tuple(flatten(value_type)))

        self.arg_names = arg_names
        self.arg_types = arg_types

    def __call__(self, *values: float) -> Any:
        return np.mean(values) if values else 0


class NDiff(Codon):
    """Nested difference operations."""

    def __init__(
        self,
        n: int,
        **kwargs,
    ) -> None:
        super().__init__(
            n=n,
            **kwargs,
        )
        self.n = n
        self.arg_names = ["x"] + [f"win{i}" for i in range(1, n + 1)]
        self.arg_types = [tuple(flatten(kwargs.get("arg_x", Series)))] + [
            tuple(flatten(kwargs.get("arg_win", int))) for _ in range(1, n + 1)
        ]

    def __call__(self, x: Series, *windows: int) -> Series:
        y = self.anal.diff(x, periods=windows[0])
        for win in windows[1:]:
            y = self.anal.diff(y, periods=win)
        return y

    @property
    def func_name(self):
        return f"diff_{self.n}"


class NPctChange(Codon):
    """Nested percent change operations."""

    def __init__(
        self,
        n: int,
        **kwargs,
    ) -> None:
        super().__init__(
            n=n,
            **kwargs,
        )
        self.n = n
        self.arg_names = ["x"] + [f"win{i}" for i in range(1, n + 1)]
        self.arg_types = [tuple(flatten(kwargs.get("arg_x", Series)))] + [
            tuple(flatten(kwargs.get("arg_win", int))) for _ in range(1, n + 1)
        ]

    def __call__(self, x: Series, *windows: int) -> Series:
        y = self.anal.pct_change(x, periods=windows[0])
        for win in windows[1:]:
            y = self.anal.pct_change(y, periods=win)
        return y

    @property
    def func_name(self):
        return f"pct_change_{self.n}"


class NormBbands(Codon):
    """Normalize using Bollinger Bands."""

    def __call__(self, x: Series, win: int, k_sigma: float) -> Series:
        return self.anal.bbands_normalization(x, win, k_sigma=k_sigma)

    @property
    def func_name(self) -> str:
        return "normalize_bbands"


class NormMinMax(Codon):
    """Min-max normalization of Series."""

    def __call__(self, x: Series, win: int) -> Series:
        return self.anal.minmax_normalization(x, win)

    @property
    def func_name(self) -> str:
        return "normalize_minmax"


class NormZScore(Codon):
    """Z-score normalization of Series."""

    def __init__(self, eps=1e-8, use_minmax_scale=False, **kwargs):
        super().__init__(**kwargs)
        self.use_minmax_scale = use_minmax_scale
        self.eps = eps

    def __call__(self, x: Series, win: int) -> Series:
        x_norm = self.anal.zscore_normalization(x, win)
        if getattr(self, "use_minmax_scale", False):
            x_min = x_norm.min()
            x_max = x_norm.max()
            return (x_norm - x_min) / (x_max - x_min + self.eps)
        else:
            return x_norm

    @property
    def func_name(self) -> str:
        return "normalize_zscore"


class PosInChan(Codon):
    """Position within a channel (0-1 normalized)."""

    def __call__(self, x: Series, channel: tuple[Series, Series]) -> Series:
        """
        Outputs a clipped value from 0-1, where 0 means at or below the lower
        limit and 1 means above or at the upper limit.
        """
        upper, lower = channel
        channel_width = upper - lower
        channel_width.replace([0, np.inf, -np.inf], np.nan, inplace=True)
        y = (x - upper) / channel_width
        y.replace(np.nan, 0, inplace=True)
        y.clip(0, 1, inplace=True)
        return y

    @property
    def func_name(self) -> str:
        return "position_in_channel"


class RandomCol(Codon):
    """Select a random column from a DataFrame."""

    def __init__(self, dtype: type | Iterable[type] | None = None, **kwargs) -> None:
        super().__init__(func_name="column", **kwargs)
        self.dtypes = dtype

    def __call__(self, df: DataFrame, idx: int) -> Series:
        if self.dtypes:
            filtered_df_cols = df.select_dtypes(include=cast(Any, self.dtypes)).columns
            col = (
                df[filtered_df_cols[idx % len(filtered_df_cols)]]
                if len(filtered_df_cols) > 0
                else None
            )
            assert col is not None, f"no column in df with required dtype: {self.dtypes}"
            return col
        else:
            return df[df.columns[idx % len(df.columns)]]


class RollBband(Codon):
    """Rolling Bollinger Band."""

    def __call__(self, x: Series, win: int, k: float, *args) -> Series:
        return self.anal.rolling_mean(x, win) + k * self.anal.rolling_std(x, win)

    @property
    def func_name(self) -> str:
        return "rolling_bbands"


class RollCmp(Codon):
    """Base class for rolling comparison operations."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] | None = None,
        window_type: type | tuple[type, ...] | None = None,
        out: type | None = None,
        **kwargs,
    ) -> None:
        super().__init__(out=out, **kwargs)
        if series_type is not None:
            self.arg_types[0] = tuple(flatten(series_type))
            self.arg_types[1] = tuple(flatten(series_type))
            if out is None:
                self.ret_types = self.arg_types[0]
        if window_type is not None:
            self.arg_types[2] = tuple(flatten(window_type))

    @property
    def func_name(self) -> str:
        return "rolling_comparison"


class RollDom(Codon):
    """Rolling dominance/frequency of specific value."""

    def __call__(self, x: Series, value: int, win: int) -> Series:
        return self.anal.rolling_sum(x, win) / win

    @property
    def func_name(self) -> str:
        return "rolling_dominance"


class RollEntropy(Codon):
    """Rolling entropy of Series."""

    def __call__(self, x: Series, win: int) -> Series:
        return self.anal.rolling_entropy(x, win)

    @property
    def func_name(self) -> str:
        return "rolling_entropy"


class RollLinReg(Codon):
    """Rolling linear regression slope."""

    def __call__(self, x: Series, win: int) -> Series:
        return self.anal.rolling_linear_regression(x, win)

    @property
    def func_name(self) -> str:
        return "rolling_linreg"


class RollMad(Codon):
    """Rolling median absolute deviation."""

    def __call__(self, x: Series, win: int) -> Series:
        return x.rolling(win).apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)

    @property
    def func_name(self) -> str:
        return "rolling_mad"


class RollMode(Codon):
    """Rolling mode (most frequent value)."""

    def __call__(self, x: Series, win: int) -> Series:
        def mode_fn(x):
            vals, counts = np.unique(x[~pd.isna(x)], return_counts=True)
            return vals[np.argmax(counts)] if len(vals) > 0 else np.nan

        return x.rolling(window=win).apply(mode_fn, raw=False).astype(float)

    @property
    def func_name(self) -> str:
        return "rolling_mode"


class RollZScore(Codon):
    """Rolling z-score normalization."""

    def __call__(self, x: Series, win: int) -> Series:
        return self.anal.zscore_normalization(x, win)

    @property
    def func_name(self) -> str:
        return "rolling_zscore"


class Rolling(Codon):
    """Base class for rolling window operations."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] | None = None,
        window_type: type | tuple[type, ...] | None = None,
        min_periods: int | None = None,
        out: type | str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(out=out, min_periods=min_periods, **kwargs)
        self.min_periods = min_periods
        if series_type is not None:
            self.arg_types[0] = tuple(flatten(series_type))
            if out is None:
                self.ret_types = self.arg_types[0]
        if window_type is not None:
            self.arg_types[1] = tuple(flatten(window_type))

    def __call__(self, x: Series, win: int, *args) -> Series:
        if win < 2:
            return x

        y = self.apply(x, win, *args)
        return y

    def apply(self, x: Series, win: int, *args) -> Series:
        raise NotImplementedError()


class RollingAutoCorr(Rolling):
    """Rolling autocorrelation."""

    def __call__(self, x: Series, win: int, lag: int, *args, **kwargs) -> Series:
        return super().__call__(x, win, lag)

    def apply(self, x: Series, win: int, lag: int, *args, **kwargs) -> Series:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return self.anal.rolling_autocorr(x, win, lag)


class RollingCorr(RollCmp):
    """Rolling correlation between two Series."""

    def __call__(self, x1: Series, x2: Series, window: int, exp: bool) -> Series:
        return (
            x1.ewm(window, min_periods=1).corr(x2, pairwise=False)
            if exp
            else x1.rolling(window, min_periods=1).corr(x2, pairwise=False, ddof=1)
        )


class RollingCov(RollCmp):
    """Rolling covariance between two Series."""

    def __call__(self, x1: Series, x2: Series, window: int, exp: bool) -> Series:
        return (
            x1.ewm(window, min_periods=1).cov(x2, pairwise=False)
            if exp
            else x1.rolling(window, min_periods=1).cov(x2, pairwise=False, ddof=1)
        )


class RollingKurt(Rolling):
    """Rolling kurtosis."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_kurt(x, win)


class RollingMax(Rolling):
    """Rolling maximum."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_max(x, win)


class RollingMean(Rolling):
    """Rolling mean with optional exponential weighting."""

    def __call__(self, x: Series, win: int, exp: bool, *args, **kwargs) -> Series:
        return super().__call__(x, win, exp)

    def apply(self, x: Series, win: int, exp: bool, *args, **kwargs) -> Series:
        return self.anal.ewm_mean(x, win) if exp else self.anal.rolling_mean(x, win)


class RollingMed(Rolling):
    """Rolling median."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_median(x, win)


class RollingMin(Rolling):
    """Rolling minimum."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_min(x, win)


class RollingSkew(Rolling):
    """Rolling skewness."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_skew(x, win)


class RollingStd(Rolling):
    """Rolling standard deviation."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_std(x, win)


class RollingSum(Rolling):
    """Rolling sum."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_sum(x, win)


class RollingVar(Rolling):
    """Rolling variance."""

    def apply(self, x: Series, win: int, *args) -> Series:
        return self.anal.rolling_var(x, win)


class SAbs(Codon):
    """Absolute value of Series."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] = Series,
        **kwargs,
    ) -> None:
        super().__init__(
            arg_types={"x": kwargs.get("arg_x", series_type)},
            **kwargs,
        )

    def __call__(self, x: Series) -> Series:
        return self.anal.abs(x)

    @property
    def func_name(self) -> str:
        return "series_abs"


class SAdd(Codon):
    """Element-wise addition of two Series."""

    def __init__(
        self,
        min_depth: int | None = None,
        max_depth: int | None = None,
        arg1_type: type = Series,
        arg2_type: type | tuple[type, ...] = Series,
        out: type | str = Series,
        memo=False,
        bias=1.0,
        **kwargs,
    ) -> None:
        super().__init__(
            min_depth=min_depth,
            max_depth=max_depth,
            operator="+",
            arg_types={"a": kwargs.get("arg_a", arg1_type), "b": kwargs.get("arg_b", arg2_type)},
            out=out,
            memo=memo,
            bias=bias,
            **kwargs,
        )

    def __call__(self, a: Series, b: Series) -> Series:
        return self.anal.add(a, b)

    @property
    def func_name(self):
        return "add"


class SAll(Codon):
    """AND across multiple Series."""

    def __init__(self, n: int, arg_type: type | str | Sequence[str | type], **kwargs):
        super().__init__(n=n, **kwargs)
        self.n = n
        self.arg_types = [tuple(flatten(arg_type))] * n
        self.arg_names = [f"x{i+1}" for i in range(n)]

    def __call__(
        self,
        *series: Series,
    ) -> Series:
        return reduce(lambda a, b: self.anal.bitwise_and(a, b), series)

    @property
    def func_name(self) -> str:
        return "all"


class SAnd(Codon):
    """Element-wise AND of two Series."""

    def __call__(self, a: Series, b: Series) -> Series:
        return self.anal.bitwise_and(a, b)

    @property
    def operator(self) -> str:
        return "&"

    @property
    def func_name(self) -> str:
        return "and"


class SAny(Codon):
    """OR across multiple Series."""

    def __init__(self, n: int, arg_type: type | str | Sequence[str | type], **kwargs):
        super().__init__(n=n, **kwargs)
        self.n = n
        self.arg_types = [tuple(flatten(arg_type))] * n
        self.arg_names = [f"x{i+1}" for i in range(n)]

    def __call__(
        self,
        *series: Series,
    ) -> Series:
        return reduce(lambda a, b: self.anal.bitwise_or(a, b), series)

    @property
    def func_name(self) -> str:
        return "any"


class SBtw(Codon):
    """Check if Series values are between two bounds."""

    def __call__(self, x: Series, a: float, b: float) -> Series:
        if not (isinstance(a, Series) or isinstance(b, Series)):
            min_bound, max_bound = sorted([a, b])
        else:
            min_bound, max_bound = a, b
        return self.anal.is_between(x, min_bound, max_bound, upper_inclusive=False)

    @property
    def func_name(self):
        return "btw"


class SCmpGate(Codon):
    """Base class for Series comparison operations."""

    def __call__(self, a: Series, b: Series) -> Series:
        raise NotImplementedError()

    @property
    def func_name(self) -> str:
        return "series_comparison_gate"


class SCos(Codon):
    """Cosine of Series."""

    def __call__(
        self,
        x: Series,
    ) -> Series:
        return self.anal.cos(x)

    @property
    def func_name(self):
        return "cos"


class SDiff(Codon):
    """Difference operation on Series."""

    def __call__(self, x: Series, win: int) -> Series:
        return self.anal.diff(x, max(1, win))

    @property
    def func_name(self) -> str:
        return "series_diff"


class SStep(Codon):
    """Discretize Series by division."""

    def __call__(self, x: Series, divisor: int) -> Series:
        return (x // divisor).astype(float)

    @property
    def func_name(self):
        return "step"


class SDiv(Codon):
    """Element-wise division of two Series with epsilon."""

    def __init__(self, epsilon=1e-6, **kwargs) -> None:
        super().__init__(**kwargs)
        self.epsilon = epsilon

    def __call__(self, a: Series, b: Series) -> Series:
        return self.anal.div(a, b + self.epsilon)

    @property
    def func_name(self):
        return "div"


class SExp(Codon):
    """Exponential of Series."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] = Series,
        min_depth: int | None = None,
        max_depth: int | None = None,
        **params,
    ) -> None:
        super().__init__(
            min_depth,
            max_depth,
            arg_types={"x": series_type},
            func_name="exp",
            **params,
        )

    def __call__(
        self,
        x: Series,
    ) -> Series:
        return self.anal.exp(x)

    @property
    def func_name(self) -> str:
        return "series_exp"


class SILocIdx(Codon):
    """Index into Series using iloc."""

    def __init__(self, index: int, **kwargs) -> None:
        super().__init__(index=index, **kwargs)
        self.index = index

    def __call__(self, x: Series) -> Any:
        return x.iloc[self.index]

    @property
    def func_name(self) -> str:
        return "series_iloc_index"


class SIfElse(Codon):
    """Element-wise conditional selection between two Series."""

    def __call__(self, test: Series, a: Series, b: Series) -> Series:
        test = test.reindex(a.index, method="nearest").fillna(False)
        b = b.reindex(a.index, method="nearest")

        return Series(
            np.where(test.astype(bool), cast(np.ndarray, a.values), cast(np.ndarray, b.values)),
            index=a.index,
        )

    @property
    def func_name(self) -> str:
        return "series_if_else"


# === Reducers (Logic, Comparison, Math) ===


class SLoc(Codon):
    """Loc-based Series indexing."""

    def __init__(
        self,
        series_type: type = Series,
        loc_type: type = Locator,
        **params,
    ) -> None:
        super().__init__(
            arg_types={"x": series_type, "locator": loc_type},
            **params,
        )

    def __call__(self, x: Series, locator: Locator) -> Any:
        try:
            return x.loc[locator]
        except:
            breakpoint()
            raise

    @property
    def func_name(self) -> str:
        return "series_loc"


# === Series Operations ===


class SLocMask(Codon):
    """Index into Series using loc with a mask."""

    def __init__(
        self,
        mask: int,
        **kwargs,
    ) -> None:
        super().__init__(mask_id=id(mask), **kwargs)
        self.mask = mask

    def __call__(self, x: Series) -> Any:
        return x.loc[self.mask]

    @property
    def func_name(self) -> str:
        return "series_loc_mask"


class SLog(Codon):
    """Natural logarithm of Series."""

    def __call__(
        self,
        x: Series,
    ) -> Series:
        return self.anal.log(x)

    @property
    def func_name(self):
        return "ln"


class SLog1p(Codon):
    """Log(1+x) with sign preservation."""

    def __call__(
        self,
        x: Series,
    ) -> Series:
        return self.anal.log1p(x.abs().fillna(0)) * Series(
            np.sign(x.fillna(0).to_numpy()), index=x.index
        )

    @property
    def func_name(self) -> str:
        return "series_log1p"


class SMax(Codon):
    """Element-wise maximum of two Series."""

    def __call__(self, x1: Series, x2: Series) -> Series:
        return self.anal.max(x1, x2)

    @property
    def func_name(self) -> str:
        return "series_max"


class SMean(Codon):
    """Mean of multiple Series."""

    def __init__(self, n: int, arg_x: type | str | Sequence[type | str], axis: int = 1, **kwargs):
        super().__init__(**kwargs)
        self.axis = axis
        self.n = n

        self.arg_names = [f"x{i}" for i in range(n)]
        self.arg_types = [flatten(arg_x)] * n

    def __call__(self, *X: list[Series]) -> Series:
        return pd.DataFrame(X).mean(axis=self.axis)  # type: ignore

    @property
    def func_name(self) -> str:
        return "series_mean"


class SMin(Codon):
    """Element-wise minimum of two Series."""

    def __call__(self, x1: Series, x2: Series) -> Series:
        return self.anal.min(x1, x2)

    @property
    def func_name(self) -> str:
        return "series_min"


class SMul(Codon):
    """Element-wise multiplication of two Series."""

    def __call__(self, a: Series, b: Series) -> Series:
        return self.anal.mul(a, b)

    @property
    def func_name(self) -> str:
        return "series_mul"


class SNeg(Codon):
    """Negate Series values."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] = Series,
        **kwargs,
    ) -> None:
        super().__init__(
            arg_types={"x": series_type},
            **kwargs,
        )

    def __call__(self, x: Series) -> Series:
        return self.anal.mul(x, -1)

    @property
    def func_name(self) -> str:
        return "series_negate"


class SNot(Codon):
    """Element-wise NOT of Series."""

    def __init__(self, **params) -> None:
        super().__init__(func_name="not", **params)

    def __call__(self, a: Series) -> Series:
        return self.anal.bitwise_not(a)

    @property
    def func_name(self):
        return "not"


class SOr(Codon):
    """Element-wise OR of two Series."""

    def __call__(self, a: Series, b: Series) -> Series:
        return self.anal.bitwise_or(a, b)

    @property
    def operator(self) -> str:
        return "|"

    @property
    def func_name(self) -> str:
        return "or"


class SPctChange(Codon):
    """Percent change of Series over window."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] = Series,
        span_type: type | tuple[type, ...] = int,
        **kwargs,
    ) -> None:
        super().__init__(
            arg_types={"x": series_type, "span": span_type},
            **kwargs,
        )

    def __call__(self, x: Series, span: int) -> Series:
        return self.anal.pct_change(x, max(1, span))

    @property
    def func_name(self) -> str:
        return "series_pct_change"


class SPow(Codon):
    """Element-wise power of Series."""

    def __call__(self, x: Series, power: float) -> Series:
        return self.anal.pow(x, power)

    @property
    def func_name(self):
        return "pow"


class SSigmoid(Codon):
    """Sigmoid activation for Series."""

    def __call__(self, x: Series, alpha: float) -> Series:
        return self.anal.sigmoid(x, alpha)

    @property
    def func_name(self):
        return "expit"


class SSin(Codon):
    """Sine of Series."""

    def __call__(
        self,
        x: Series,
    ) -> Series:
        return self.anal.sin(x)

    @property
    def func_name(self):
        return "sin"


class SSin2pi(Codon):
    """Sine of 2*pi*Series."""

    def __call__(
        self,
        x: Series,
    ) -> Series:
        return self.anal.sin(2 * math.pi * x)

    @property
    def func_name(self):
        return "sin2pi"


class SSqrt(Codon):
    """Square root of absolute Series values."""

    def __call__(self, x: Series) -> Series:
        return self.anal.sqrt(x.abs())

    @property
    def func_name(self):
        return "sqrt"


class SSub(Codon):
    """Element-wise subtraction of two Series."""

    def __call__(self, a: Series, b: Series) -> Series:
        y = self.anal.sub(a, b)
        return y

    @property
    def func_name(self):
        return self.custom_func_name or "sub"


class STanh(Codon):
    """Hyperbolic tangent of Series."""

    def __call__(self, x: Series) -> Series:
        return self.anal.tanh(x)

    @property
    def func_name(self) -> str:
        return "series_tanh"


class SeriesEq(Codon):
    """Element-wise equality."""

    def __call__(self, a: Series, b: Series) -> Series:
        return a == b

    @property
    def operator(self) -> str:
        return "=="

    @property
    def func_name(self):
        return "eq"


class SeriesGeq(Codon):
    """Element-wise greater than or equal."""

    def __call__(self, a: Series, b: Series) -> Series:
        return a >= b

    @property
    def operator(self) -> str:
        return ">="

    @property
    def func_name(self):
        return "geq"


class SeriesGt(Codon):
    """Element-wise greater than."""

    def __call__(self, a: Series, b: Series) -> Series:
        return a > b

    @property
    def operator(self) -> str:
        return ">"

    @property
    def func_name(self):
        return "gt"


class SeriesLeq(Codon):
    """Element-wise less than or equal."""

    def __call__(self, a: Series, b: Series) -> Series:
        return a <= b

    @property
    def operator(self) -> str:
        return "<="

    @property
    def func_name(self):
        return "leq"


class SeriesLt(Codon):
    """Element-wise less than."""

    def __call__(self, a: Series, b: Series) -> Series:
        return a < b

    @property
    def operator(self) -> str:
        return "<"

    @property
    def func_name(self):
        return "lt"


class Shift(Codon):
    """Shift Series by window size."""

    def __call__(self, x: Series, win: int) -> Series:
        y = self.anal.shift(x, max(1, win))
        return y

    @property
    def func_name(self):
        return "shift"


class Sigmoid(Codon):
    """Sigmoid activation function."""

    def __call__(
        self,
        x: float,
        alpha: float,
    ) -> float:
        return expit(alpha * x)


class SSing(Codon):
    """Sign of Series values (-1, 0, 1)."""

    def __init__(
        self,
        series_type: type | tuple[type, ...] = Series,
        min_depth: int | None = None,
        max_depth: int | None = None,
        out: type | None = None,
        memo=False,
        bias: float = 1,
        **params,
    ) -> None:
        super().__init__(
            min_depth,
            max_depth,
            memo=memo,
            bias=bias,
            arg_types={"x": series_type},
            out=out,
            **params,
        )

    def __call__(self, x: Series) -> Series:
        return cast(Series, np.sign(x))


class STrue(Codon):
    """Series filled with True values."""

    def __init__(
        self,
        index: Index,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.index: Index = self.index
        self.series = Series(True, index=self.index, dtype=bool)

    def __call__(self) -> Series:
        return self.series


class UpperDynBband(Codon):
    """Upper Bollinger Band with dynamic windows."""

    def __call__(self, x: Series, wins: Series, k_sigma: float) -> Series:
        mu = self.anal.dyn_rolling_mean(x, wins)
        sigma = self.anal.dyn_rolling_std(x, wins)
        return mu + k_sigma * sigma

    @property
    def func_name(self) -> str:
        return "upper_dynamic_bband"


class VolatilityWindows(Codon):
    """Map volatility to dynamic window sizes."""

    def __call__(self, volatility: Series, win_range: tuple[float, float], scale: str) -> Series:
        return self.anal.volatility_windows(volatility, win_range, scale)


class WaveletTransform(Codon):
    """Wavelet transformation of Series."""

    WAVELET_DB1 = "db1"
    WAVELET_DB2 = "db2"
    WAVELET_SYM2 = "sym2"
    WAVELET_TYPES = [WAVELET_DB1, WAVELET_DB2, WAVELET_SYM2]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __call__(self, x: Series, name: str = WAVELET_DB1, level: int = 1):
        # Perform wavelet decomposition
        coeffs = pywt.wavedec(x, name, level=level)

        # Concatenate all coefficients into a single array
        coeffs_flat = np.concatenate(coeffs)

        # Resize to match the original length
        n = len(x)
        if len(coeffs_flat) > n:
            coeffs_resized = coeffs_flat[:n]
        elif len(coeffs_flat) < n:
            pad_width = n - len(coeffs_flat)
            coeffs_resized = np.pad(coeffs_flat, (0, pad_width), mode="constant")
        else:
            coeffs_resized = coeffs_flat

        y = Series(coeffs_resized, index=x.index)
        return y
