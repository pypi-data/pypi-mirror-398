"""
Primitive codon definitions for the nature genetic programming framework.

This module contains core primitive codons including:
- Basic arithmetic operations (Add, Sub, Mul, Div, Sin, Sqrt, Log, Pow, etc.)
- Terminal value generators (Int, Float, Boolean, Gaussian, etc.)
- Type conversions (ToInt, ToFloat, Cast)
- Logic and comparison operations (And, Or, Not, Gt, Lt, Eq, Between, etc.)
- Flow control (IfElse)
- Utility operations (Str, Fstr, Flatten, Zip, ToDict, ToTuple, Step, Round)
- Helper classes (Symbols, symbol function)
"""

import inspect
import math
import random
from typing import Any, Callable, Sequence, Tuple, TypeAlias
from uuid import uuid4

from pandas import Series

from nature.codon import Codon
from nature.random import Random
from nature.utils import clamp, flatten

NIL = -1

CodonHierarchy: TypeAlias = Tuple["Codon", Tuple]


class Symbols:
    def __init__(self) -> None:
        self._symbols: dict[str, str] = {}

    def __getattr__(self, k: str) -> str:
        return self(k)

    def __call__(self, *parts: str | Sequence[str]) -> str:
        s = "_".join(p.split("__")[0] for p in flatten(parts))
        if s not in self._symbols:
            self._symbols[s] = symbol(s)
        return self._symbols[s]


def symbol(*parts: str | Sequence[str], delim: str = "_", use_tag=True) -> str:
    s = delim.join(flatten(parts))
    tag = uuid4().hex[:4] if use_tag else ""
    return "__".join([s, tag]).strip()



# === Codon Classes ===


class Add(Codon):
    """Addition operation for numeric types."""

    def __init__(
        self,
        op1_type: type | None = None,
        op2_type: type | None = None,
        min_depth: int | None = None,
        max_depth: int | None = None,
        bias=2.0,
        **kwargs,
    ) -> None:
        super().__init__(
            min_depth=min_depth,
            max_depth=max_depth,
            arg_types={"a": op1_type or (int, float), "b": op2_type or (int, float)},
            operator="+",
            bias=bias,
            **kwargs,
        )

    def __call__(self, a: float | int, b: float | int) -> float | int:
        return a + b




class And(Codon):
    """Logical AND."""

    @property
    def operator(self) -> str:
        return "and"

    def __call__(self, a: bool, b: bool) -> bool:
        return a and b




class Between(Codon):
    """Between check with typed arguments."""

    def __init__(
        self,
        value_type: type = float,
        limit_type: type = float,
        min_depth: int | None = None,
        max_depth: int | None = None,
        memo=False,
        bias: float = 1,
        **params,
    ) -> None:
        super().__init__(
            min_depth,
            max_depth,
            arg_types={
                "x": value_type,
                "upper": limit_type,
                "lower": limit_type,
            },
            memo=memo,
            bias=bias,
            **params,
        )

    def __call__(self, x: int | float, lower: int | float, upper: int | float) -> bool:
        return x > lower and x < upper




class Boolean(Codon):
    """Random boolean with configurable probability."""

    def __init__(
        self,
        prob: float = 0.5,
        **kwargs,
    ) -> None:
        super().__init__(prob=prob, **kwargs)
        self.prob = prob
        self.const_value: bool | None = None
        if not prob:
            self.const_value = False
        elif prob == 1:
            self.const_value = True

    def __call__(self) -> bool:
        return self.const_value if self.const_value is not None else self.random.flip(p=self.prob)




class Btw(Codon):
    """Between check (exclusive)."""

    def __call__(self, x: float, l: float, u: float) -> bool:
        return x > l and x < u




class Cast(Codon):
    """Type casting operation."""

    def __init__(self, dtype: type | None = None, **kwargs):
        super().__init__(**kwargs)
        self.dtype = dtype

    def __call__(self, x: Any) -> Any:
        y = cast(Any, x)
        if self.dtype:
            if isinstance(y, Series):
                return y.astype(self.dtype)
            else:
                return self.dtype(y)
        return y

    @property
    def func_name(self):
        t = self.ret_types[0]
        return f"cast"




class CastValue(Codon):
    """Cast and return a stored value."""

    def __init__(self, value: Any, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def __call__(self) -> Series:
        return self.value




class Choice(Codon):
    """Dynamic choice from sequence."""

    def __call__(self, options: Sequence[Any], seed: int) -> Any:
        rand = Random(seed)
        return rand.np_choice(options)




class Div(Codon):
    """Division operation with NaN protection for divide-by-zero."""

    def __init__(
        self,
        op1_type: type | None = None,
        op2_type: type | None = None,
        min_depth: int | None = None,
        max_depth: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            min_depth=min_depth,
            max_depth=max_depth,
            arg_types={"a": op1_type or (int, float), "b": op2_type or (int, float)},
            operator="*",
            **kwargs,
        )

    def __call__(self, a: float | int, b: float | int) -> float | int:
        return a / b if b else np.nan




class Eq(Codon):
    """Equality comparison."""

    def __call__(self, a: float, b: float) -> bool:
        return a == b

    @property
    def operator(self) -> str:
        return "=="




class Flatten(Codon):
    """Flatten nested sequences."""

    def __call__(self, sequences: list) -> list:
        return list(flatten(sequences))




class Float(Codon):
    """Random float generator within a range."""

    def __init__(
        self,
        min: float,
        max: float,
        dec: int | None = None,
        min_depth: int | None = None,
        max_depth: int | None = None,
        out: type | str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(min_depth=min_depth, max_depth=max_depth, out=out, **kwargs)
        self.x_min = min
        self.x_max = max
        self.decimals = dec
        self.dx = self.x_max - self.x_min
        if self.x_min == self.x_max:
            self.value = self.x_min
        else:
            self.value = None

    def __call__(self) -> float:
        if self.value is not None:
            return self.value
        val = self.x_min + self.dx * self.random.random()
        return round(val, self.decimals) if self.decimals else val




class Fstr(Codon):
    """Formatted string with dynamic arguments."""

    def __init__(self, fstr: str, **kwargs):
        super().__init__(**kwargs)

        self.arg_names = arg_names = []
        self.arg_types = arg_types = []

        for k in list(kwargs.keys()):
            if k.startswith("arg_"):
                v = kwargs.pop(k)
                arg_names.append(k[4:])
                arg_types.append(flatten(v))

        self.fstr = fstr

    def __call__(self, *values) -> str:
        return self.fstr.format(**dict(zip(self.arg_names, values)))




class Gaussian(Codon):
    """Random value from a Gaussian distribution."""

    def __init__(
        self,
        mu: float,
        sigma: float,
        min: float | None = None,
        max: float | None = None,
        dec: int | None = None,
        min_depth: int | None = None,
        max_depth: int | None = None,
        out: type | str | None = None,
        bias=1.0,
    ) -> None:
        super().__init__(
            min_depth=min_depth,
            max_depth=max_depth,
            out=out,
            x_min=min,
            x_max=max,
            mu=mu,
            sigma=sigma,
            bias=bias,
            func_name="gauss",
        )
        self.x_min = min if min is not None else mu - 4 * sigma
        self.x_max = max if max is not None else mu + 4 * sigma
        self.mu = mu
        self.sigma = sigma
        self.decimals = dec

    def __call__(self) -> float:
        val = clamp(self.random.normalvariate(self.mu, self.sigma), self.x_min, self.x_max)
        return round(val, self.decimals) if self.decimals else val




class GaussianBetween(Codon):
    """Gaussian-distributed value between two bounds."""

    def __init__(
        self,
        k_sigma: float = 0.34,
        dec: int | None = None,
        step: int | None = None,
        dtype: type | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.decimals = dec
        self.k_sigma = k_sigma
        self.step = step
        self.dtype = dtype

    def __call__(self, seed: int, lower: float, upper: float) -> float | int:
        random = Random(seed)
        mu = (lower + upper) / 2
        sigma = self.k_sigma * mu
        val = clamp(random.normalvariate(mu, sigma), lower, upper)
        y = round(val, self.decimals) if self.decimals is not None else val
        if self.step:
            y = (y // self.step) * self.step
        return self.dtype(y) if self.dtype else y




class GaussianInt(Gaussian):
    """Integer-valued Gaussian random variable."""

    def __call__(self) -> int:
        return round(super()())




class Gt(Codon):
    """Greater than comparison."""

    def __call__(self, a: float, b: float) -> bool:
        return a > b

    @property
    def operator(self) -> str:
        return ">"




class IfElse(Codon):
    """Conditional branching for scalar values."""

    def __call__(self, test: bool, a: Any, b: Any) -> Any:
        return a if test else b




class InRange(Codon):
    """Check if value is in relative range."""

    def __call__(self, x: float, l: float, mult: float) -> bool:
        u = l * (1 + mult)
        return x > l and x < u




class Int(Codon):
    """Random integer generator within a range."""

    def __init__(
        self,
        min: int,
        max: int,
        multiple: int = 1,
        min_depth: int | None = None,
        max_depth: int | None = None,
        out: type | str | None = None,
        bias=1.0,
    ) -> None:
        super().__init__(min_depth=min_depth, max_depth=max_depth, out=out, bias=bias)
        self.x_min = min
        self.x_max = max
        self.x_step = multiple

    def __call__(self) -> int:
        x = self.random.randrange(self.x_min, self.x_max + self.x_step)
        return x - x % self.x_step




class IntBetween(Codon):
    """Random integer between two dynamic bounds."""

    def __init__(
        self,
        min: int | None = None,
        max: int | None = None,
        upper_exclusive: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.upper_exclusive = upper_exclusive
        self.x_max = max
        self.x_min = min

    def __call__(self, seed: int, l: int, u: int) -> int:
        random = Random(seed)
        if self.upper_exclusive:
            x = random.randrange(l, u)
        else:
            x = random.randint(l, u)
        if self.x_min is not None:
            x = max(self.x_min, x)
        if self.x_max is not None:
            x = min(self.x_max, x)
        return x




class Locator(Any):
    """Type marker for locator objects."""

    pass




class Log(Codon):
    """Natural logarithm with NaN for non-positive inputs."""

    def __call__(self, x: float | int) -> float:
        return np.log(x, dtype=float) if x > 0 else np.nan




class LogUniformFloat(Codon):
    """Log-uniform distributed random float."""

    def __init__(self, min: float, max: float, dec: int | None = None, *args, **kwargs):
        super().__init__(**kwargs)
        self.x_min = min
        self.x_max = max
        self.dec = dec

    def __call__(self) -> float:
        y = self.random.log_uniform(self.x_min, self.x_max)
        if self.dec:
            return round(y, self.dec)
        else:
            return y




class Lt(Codon):
    """Less than comparison."""

    def __call__(self, a: float, b: float) -> bool:
        return a < b

    @property
    def operator(self) -> str:
        return "<"




class Mul(Codon):
    """Multiplication operation for numeric types."""

    def __call__(self, a: float, b: float) -> float:
        return a * b




class Not(Codon):
    """Logical NOT."""

    def __call__(self, a: bool) -> bool:
        return not a




class OneOf(Codon):
    """Select one from predefined options."""

    def __init__(
        self,
        options: Sequence,
        **kwargs,
    ) -> None:
        self.options = options
        super().__init__(**kwargs)

    def __call__(self, seed: int) -> Any:
        random = Random(seed)
        return random.choice(self.options)




class Or(Codon):
    """Logical OR."""

    @property
    def operator(self) -> str:
        return "or"

    def __call__(self, a: bool, b: bool) -> bool:
        return a or b




class Pow(Codon):
    """Power function with configurable exponent."""

    def __init__(
        self,
        exp: float,
        min_depth: int | None = None,
        max_depth: int | None = None,
    ) -> None:
        super().__init__(
            min_depth=min_depth,
            max_depth=max_depth,
            exp=exp,
        )
        self.expon = exp

    def __call__(self, base: float | int) -> float | int:
        return math.pow(base, self.expon)




class Pow2(Pow):
    """Power of 2 function."""

    def __init__(self, **kwargs) -> None:
        super().__init__(2, **kwargs)




class Pow3(Pow):
    """Power of 3 function."""

    def __init__(self, **kwargs) -> None:
        super().__init__(3, **kwargs)


# === Terminal Value Generators ===




class ProbablisticBoolean(Codon):
    """Boolean with dynamic probability."""

    def __call__(self, prob: float) -> bool:
        return self.random.flip(p=prob)


# === Container Operations ===




class Round(Codon):
    """Round Series to decimals."""

    def __call__(self, x: Series, decimals: int) -> Series:
        return x.round(decimals)


# === Rolling Operations ===




class Sin(Codon):
    """Sine function."""

    def __call__(self, x: float | int) -> float:
        return np.sin(x, dtype=float)




class Sqrt(Codon):
    """Square root function with NaN for negative inputs."""

    def __call__(self, x: float | int) -> float:
        return np.sqrt(x, dtype=float) if x >= 0 else np.nan




class Step(Codon):
    """Discretize Series to step size."""

    def __call__(self, x: Series, step_size: int) -> Series:
        return (x // step_size) * step_size




class Str(Codon):
    """String literal terminal."""

    def __init__(self, value: str, **kwargs) -> None:
        super().__init__(value=value, **kwargs)
        self.value = value

    def __call__(self) -> str:
        return self.value




class Sub(Codon):
    """Subtraction operation for numeric types."""

    def __init__(
        self,
        op1_type: type | None = None,
        op2_type: type | None = None,
        min_depth: int | None = None,
        max_depth: int | None = None,
        bias=1.0,
        **kwargs,
    ) -> None:
        super().__init__(
            min_depth=min_depth,
            max_depth=max_depth,
            operator="-",
            arg_types={"a": op1_type or (int, float), "b": op2_type or (int, float)},
            bias=bias,
            **kwargs,
        )

    def __call__(self, a: float | int, b: float | int) -> float | int:
        return a - b




class Symbols:
    def __init__(self) -> None:
        self._symbols: dict[str, str] = {}

    def __getattr__(self, k: str) -> str:
        return self(k)

    def __call__(self, *parts: str | Sequence[str]) -> str:
        s = "_".join(p.split("__")[0] for p in flatten(parts))
        if s not in self._symbols:
            self._symbols[s] = symbol(s)
        return self._symbols[s]


def symbol(*parts: str | Sequence[str], delim: str = "_", use_tag=True) -> str:
    s = delim.join(flatten(parts))
    tag = uuid4().hex[:4] if use_tag else ""
    return "__".join([s, tag]).strip()


# === Codon Subclasses ===
# Base Codon class, Inp, and Out are imported from codon.py


# === Primitive Math Operations ===




class ToDict(Codon):
    """Convert values to dictionary with predefined keys."""

    def __init__(self, keys: Sequence[str], value_types: Sequence[type | str], **kwargs):
        super().__init__(keys=keys, value_types=str(value_types), **kwargs)
        self.keys = tuple(keys)
        self.value_types = value_types

        assert len(keys) == len(value_types), "keys and value types must have same length"

        arg_index = 1
        self.arg_names = []
        self.arg_types = []

        for value_type in value_types:
            self.arg_types.append((value_type,))
            self.arg_names.append(f"x{arg_index}")
            arg_index += 1

    def __call__(self, *args: Any) -> dict:
        return dict(zip(self.keys, args))




class ToFloat(Codon):
    """Type conversion to float."""

    def __call__(self, x: int | float | bool) -> float:
        return x




class ToInt(Codon):
    """Type conversion to integer."""

    def __call__(self, x: int | float | bool) -> int:
        return int(x)




class ToTuple(Codon):
    """Convert arguments to tuple."""

    def __init__(self, arg_types: Sequence[type], **kwargs):
        super().__init__(**kwargs)

        arg_index = 1
        self.arg_names = []
        self.arg_types = []

        for value_type in arg_types:
            self.arg_types.append((value_type,))
            self.arg_names.append(f"x{arg_index}")
            arg_index += 1

    def __call__(self, *args) -> tuple:
        return args




class Zip(Codon):
    """Zip two sequences together."""

    def __call__(self, s1: list, s2: list) -> list:
        return list(zip(s2, s2))



