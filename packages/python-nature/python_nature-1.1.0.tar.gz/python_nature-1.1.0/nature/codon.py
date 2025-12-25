"""
Codon - Building Blocks for Genetic Programming Trees.

This module defines Codons, which are the fundamental units of genetic
programs in the nature framework. Codons are analogous to biological codons
that encode instructions, but here they encode:
- Functions (operators like Add, Sub, mathematical functions like Sin, Log)
- Terminals (constant values like Int, Float, Boolean)
- Inputs (named parameters for tree execution)
- Outputs (wrapper for return values)

Key Concepts:
- **Codon**: Base class wrapping a callable with type information
- **Type System**: Each codon declares argument types and return types for tree compatibility
- **Arity**: Number of arguments (nullary=0 for terminals, n>0 for functions)
- **Depth Constraints**: min_depth/max_depth control where codons can appear in trees
- **Bias**: Sampling weight during tree construction (higher bias = more likely)
- **Memoization**: Optional caching of codon results (memo=True)

Special Codon Types:
- **Inp**: Input parameter nodes (extract args/kwargs during execution)
- **Out**: Output wrapper (root node of expression trees)
- **Operators**: Binary functions with operator syntax (+, -, *, /)
- **Terminals**: Constant generators (Int, Float, Boolean, etc.)

Codons enable strongly-typed genetic programming where:
- Trees are valid by construction (type-checked during building)
- Mutations preserve type correctness
- Crossover only grafts compatible subtrees

Example:
    >>> from nature.codon import Add, Sub, Float, Int, Inp, Out
    >>> # Define available operations for evolving arithmetic programs
    >>> codons = [
    ...     Add(),                    # Binary addition
    ...     Sub(),                    # Binary subtraction
    ...     Float(0.0, 1.0),         # Random float constant [0, 1]
    ...     Int(1, 100),             # Random int constant [1, 100]
    ... ]
    >>> # Trees built from these codons will be valid arithmetic expressions
"""

import inspect
import math
import random
import sys
from collections import defaultdict
from hashlib import sha256
from typing import Any, Sequence, Tuple, TypeAlias, Union, cast
from uuid import uuid4

import numpy as np
from pandas import Series

from nature.analysis import analyzer
from nature.random import Random
from nature.utils import clamp, flatten, to_snake_case

# Placeholder value indicating "no constraint" for depth limits
NIL = -1

CodonHierarchy: TypeAlias = Tuple["Codon", Tuple]


class Lexicon:
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


class Codon:
    """
    Base class for genetic programming building blocks.

    A Codon wraps a callable function or value and provides type information
    that enables strongly-typed genetic programming. Each codon defines:
    - What types it accepts as inputs (arg_types)
    - What type(s) it returns (ret_types)
    - Where it can appear in trees (min_depth, max_depth)
    - How likely it is to be selected (bias)

    Codons are the "genetic alphabet" from which expression trees are built.
    During evolution, trees are constructed by randomly selecting compatible
    codons based on parent-child type constraints.

    Attributes:
        custom_func_name: Human-readable name (derived from class name if not provided)
        ret_types: Tuple of types this codon can return
        arg_types: List of type unions for each argument
        arg_names: Tuple of argument names from __call__ signature
        arity: Number of arguments (0 for terminals, >0 for functions)
        nullary: True if arity is 0 (terminal node)
        min_depth: Minimum tree depth where this codon can appear (1 = root's child)
        max_depth: Maximum tree depth where this codon can appear (-1 = no limit)
        bias: Sampling weight during tree construction (default 1.0, higher = more likely)
        memo: If True, cache and reuse result after first evaluation
        mutable: If False, protected from mutation operations
        custom_operator: Operator symbol for infix notation (+, -, *, /)
        is_terminal_like: True if all arguments must come from input nodes
        hash: Unique identifier based on function name and parameters
        ctx: Execution context dict (set during tree execution)

    Type System:
        - Type annotations from __call__ signature are automatically extracted
        - Union types like `int | float` are supported for arguments and returns
        - Custom arg_types can override inferred types (useful for polymorphic functions)
        - Trees are type-checked during construction to ensure compatibility

    Depth Constraints:
        - min_depth=1: Can appear as direct child of root
        - min_depth=3: Must appear at least 3 levels deep
        - max_depth=2: Cannot appear beyond depth 2
        - depth=N: Shorthand for min_depth=max_depth=N

    Example Subclass:
        >>> class Add(Codon):
        ...     def __init__(self, **kwargs):
        ...         super().__init__(operator="+", bias=2.0, **kwargs)
        ...     def __call__(self, a: float, b: float) -> float:
        ...         return a + b
        ...
        >>> # The Add codon will:
        >>> # - Require 2 arguments (arity=2)
        >>> # - Accept float inputs (inferred from __call__)
        >>> # - Return float (inferred from __call__)
        >>> # - Render as "a + b" (operator="+")
        >>> # - Be twice as likely to be selected (bias=2.0)
    """

    random = Random()
    anal = analyzer

    def __init__(
        self,
        min_depth: int | None = None,
        max_depth: int | None = None,
        depth: int | None = None,
        operator: str | None = None,
        out: type | str | None = None,
        arg_types: dict[str, type | str | Sequence[type | str]] | None = None,
        memo=False,
        bias: float = 1,
        func_name: str | None = None,
        params: dict | None = None,
        mutable: bool = True,
        **kwargs,
    ) -> None:
        """
        Initialize a Codon with type and depth constraints.

        Args:
            min_depth: Minimum tree depth where this codon can appear (default: 1)
            max_depth: Maximum tree depth where this codon can appear (default: no limit)
            depth: Convenience parameter to set both min and max depth
            operator: Operator symbol for infix notation (e.g., "+", "-")
            out: Override inferred return type from __call__ signature
            arg_types: Override inferred argument types (dict of {arg_name: type(s)})
            memo: Enable memoization - cache result after first evaluation
            bias: Sampling weight during tree construction (>1 = more likely, <1 = less likely)
            func_name: Custom function name (default: snake_case class name)
            params: Additional parameters stored in self.params dict
            mutable: If False, this codon is protected from mutation operations
            **kwargs: Additional parameters merged into self.params (use in_<param_name> for input type overrides)

        Raises:
            ValueError: If __call__ method lacks return type annotation
        """
        if depth is not None:
            min_depth = max_depth = depth

        self.params = params or {}
        self.params.update({k: v for k, v in kwargs.items() if not k.startswith("in_")})

        self.custom_operator = operator
        self.min_depth = min_depth if min_depth is not None else NIL
        self.max_depth = max_depth if max_depth is not None else NIL
        self.custom_ret_type = out
        self.is_terminal_like = False
        self.memo = memo
        self.custom_func_name = to_snake_case(func_name or type(self).__name__)
        self.hash = sha256(f"{self.custom_func_name}:{kwargs}".encode()).digest().hex()
        self.bias = clamp(bias, 0.01, 100)
        self.id = id(self)
        self.ctx: dict | None = None
        self.mutable = mutable

        signature = inspect.signature(self.__call__)

        # Extract return type or types
        ret_annotation = out or signature.return_annotation
        if ret_annotation == inspect._empty:
            raise ValueError(
                f"{self.custom_func_name} __call__ method" "missing return type annotation"
            )
        elif isinstance(out, str):
            self.ret_types = (out,)
        elif "Union" in type(ret_annotation).__name__:
            self.ret_types = tuple(
                sorted(
                    getattr(ret_annotation, "__args__", (ret_annotation,)),
                    key=lambda t: type(t).__name__ if isinstance(t, type) else t,
                )
            )
        else:
            self.ret_types = (ret_annotation,)

        custom_arg_types_dict = arg_types or {}
        computed_arg_types: list[tuple[type | str, ...]] = []
        arg_names: list[str] = []

        # Extract argument types
        for param in signature.parameters.values():
            if param.annotation == inspect._empty:
                continue

            if param.name in custom_arg_types_dict:
                types = tuple(flatten([custom_arg_types_dict[param.name]]))
            elif "Union" in type(param.annotation).__name__:
                types = tuple(
                    sorted(
                        getattr(
                            param.annotation,
                            "__args__",
                            (param.annotation,),
                        ),
                        key=lambda t: type(t).__name__,
                    )
                )
            elif f"in_{param.name}" in kwargs:
                type_objs = flatten(kwargs[f"in_{param.name}"])
                types = tuple(type_objs)
            else:
                types = (param.annotation,)

            computed_arg_types.append(types)
            arg_names.append(param.name)

        self.arg_names = tuple(arg_names)
        self.arg_types = list(computed_arg_types)

    def __repr__(self) -> str:
        return self.custom_func_name

    def __call__(self, *args, **kwargs) -> Any:
        raise NotImplementedError(self.__class__.__name__)

    @property
    def func_name(self) -> str:
        return self.custom_func_name

    @property
    def operator(self) -> str | None:
        return self.custom_operator

    @property
    def is_input(self) -> bool:
        return isinstance(self, Inp)

    @property
    def is_output(self) -> bool:
        return isinstance(self, Out)

    @property
    def nullary(self) -> bool:
        return not self.arity

    @property
    def arity(self) -> int:
        return len(self.arg_types)


class Inp(Codon):
    """
    Input parameter codon for tree execution.

    Inp codons act as leaf nodes that extract specific arguments passed to
    the tree during execution. They enable evolved trees to accept external
    inputs by name (for kwargs) or position (for args).

    Attributes:
        key: Argument identifier (int for positional, str for keyword)
        arg_name: Display name for visualization
        input_type: Type of the input parameter
        ret_types: Tuple containing input_type (what this codon returns)

    Example:
        >>> # Create input codon for a named parameter 'price'
        >>> price_input = Inp(key='price', arg_name='price', input_type=float)
        >>> # In a tree, this node will extract kwargs['price'] at runtime
        >>>
        >>> # Create input codon for first positional argument
        >>> pos_input = Inp(key=0, arg_name='a0', input_type=int)
        >>> # In a tree, this node will extract args[0] at runtime
    """

    def __init__(self, key: str | int, arg_name: str, input_type: type | str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.key = key
        self.arg_names = [(arg_name,)]
        self.arg_types = [(input_type,)]
        self.ret_types = (input_type,)
        self.input_type = input_type

    def __call__(self, *args, **kwargs) -> Any:
        """
        Extract the input value from args or kwargs based on key type.

        Returns:
            args[key] if key is int, kwargs[key] if key is str
        """
        if isinstance(self.key, int):
            return args[self.key]
        else:
            return kwargs[self.key]

    @property
    def arity(self) -> int:
        return 0

    @property
    def is_terminal(self) -> bool:
        return True

    @property
    def nullary(self) -> bool:
        return True


class Out(Codon):
    """
    Output wrapper codon for tree root nodes.

    Out codons serve as the root node of expression trees, defining the
    expected return type(s) of the entire program. They pass through their
    child's result unchanged, but enforce type constraints during tree building.

    Always placed at depth 0 (tree root) with exactly one child.

    Attributes:
        arg_types: Expected type(s) from the tree's main logic node
        ret_types: Same as arg_types (pass-through)
        arg_names: ["out"] - single argument name for visualization

    Example:
        >>> # Tree returning a single float value
        >>> output = Out(output_type=float)
        >>>
        >>> # Tree returning a tuple of (int, float, str)
        >>> multi_output = Out(output_type=(int, float, str))
        >>> # When called, returns tuple if multiple types, single value if one type
    """

    def __init__(self, output_type: type | str | Sequence[type | str]) -> None:
        """
        Initialize Output codon with expected return type(s).

        Args:
            output_type: Single type/symbol or sequence of types/symbols for tree's return value
        """
        super().__init__(min_depth=0, max_depth=0)
        output_type_union = output_type if np.iterable(output_type) else (output_type,)
        self.arg_types = [output_type_union]
        self.ret_types = output_type_union
        self.arg_names = ["out"]

    def __call__(self, *args, **kwargs) -> Any:
        """
        Pass through child result(s), returning tuple if multiple outputs.

        Returns:
            args (tuple) if multiple outputs expected, args[0] if single output
        """
        return args if self.arity > 1 else args[0]


class Add(Codon):
    def __init__(self, **kwargs):
        super().__init__(operator="+", **kwargs)

    def __call__(self, a: float, b: float) -> float:
        return a + b


class Sub(Codon):
    def __init__(self, **kwargs):
        super().__init__(operator="-", **kwargs)

    def __call__(self, a: float, b: float) -> float:
        return a - b


class Mul(Codon):
    def __call__(self, a: float, b: float) -> float:
        return a * b


class Div(Codon):
    def __call__(self, a: float | int, b: float | int) -> float | int:
        return a / b if b else np.nan


class Sin(Codon):
    def __call__(self, x: float | int) -> float:
        return np.sin(x, dtype=float)


class Sqrt(Codon):
    def __call__(self, x: float | int) -> float:
        return np.sqrt(x, dtype=float) if x >= 0 else np.nan


class Log(Codon):
    def __call__(self, x: float | int) -> float:
        return np.log(x, dtype=float) if x > 0 else np.nan


class Pow(Codon):
    def __init__(self, power: float, **kwargs) -> None:
        super().__init__(exp=power, **kwargs)
        self.power = power

    def __call__(self, base: float | int) -> float | int:
        return math.pow(base, self.power)


class PowN(Codon):
    def __call__(self, base: float, power: float) -> float:
        return math.pow(base, power)


class Str(Codon):
    def __init__(self, value: str, **kwargs) -> None:
        super().__init__(value=value, **kwargs)
        self.value = value

    def __call__(self) -> str:
        return self.value


class Fstr(Codon):
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


class Float(Codon):
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


class Gaussian(Codon):
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


class LogUniformFloat(Codon):
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


class ToInt(Codon):
    def __call__(self, x: int | float | bool) -> int:
        return int(x)


class ToFloat(Codon):
    def __call__(self, x: int | float | bool) -> float:
        return x


class Int(Codon):
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


class GaussianInt(Gaussian):
    def __call__(self) -> int:
        return round(super()())


class Boolean(Codon):
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


class ProbablisticBoolean(Codon):
    def __call__(self, prob: float) -> bool:
        return self.random.flip(p=prob)


class Flatten(Codon):
    def __call__(self, sequences: list) -> list:
        return list(flatten(sequences))


class Zip(Codon):
    def __call__(self, s1: list, s2: list) -> list:
        return list(zip(s2, s2))


class ToDict(Codon):
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


class ToTuple(Codon):
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


class Cast(Codon):
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
        # return f"cast_{t.__name__ if isinstance(t, type) else t}"


class CastValue(Codon):
    def __init__(self, value: Any, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def __call__(self) -> Series:
        return self.value


class CastSeries(Cast):
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
    def __init__(self, min: int = 2, **kwargs) -> None:
        super().__init__(params={"min": min}, **kwargs)
        self.min_window = min

    def __call__(self, win_base: int, mult: float) -> int:
        return int(max(self.min_window, mult * win_base))
