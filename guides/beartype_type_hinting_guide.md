# The Beartype Type Hinting Reference Guide

This document defines the standard syntax, structural conventions, and implementation strategies for using `beartype` to enforce runtime type safety in Python. Use this guide to write, configure, and troubleshoot `beartype`-decorated applications.

---

## General Rules

* **O(1) Performance by Default**: Vanilla `@beartype` enforces type checking in $O(1)$ constant time by using an aggressive memoization and random-sampling tree walk across nested collections.
* **Pure-Python Compatibility**: `beartype` is written entirely in Python without compilation dependencies, making it natively compatible with CPython, PyPy, Numba, Nuitka, and Pyodide.
* **Decoration Placement**: When combining decorators (such as with `@dataclass`), always list `@beartype` **before** the other decorators.
```python
@beartype
@dataclass
class MyDataclass:
    ...

```


* **Protocol Requirements**: Structural subtyping via `typing.Protocol` requires the explicit addition of the standard `@runtime_checkable` decorator to be verified by `beartype` at runtime.

---

## Core Type Hinting Cheatsheet

`beartype` handles most modern and historical Python Enhancement Proposals (PEPs) for type compliance. Below is a comprehensive categorization of supported type configurations.

### 1. Builtins and Standard Types

Annotate raw builtin classes directly. `beartype` validates standard object instances explicitly.

```python
from beartype import beartype

@beartype
def law_of_the_jungle(wolf: str, pack: dict) -> tuple:
    return (wolf, pack[wolf]) if wolf in pack else ()

```

### 2. Unions and Nullability (PEP 604 & PEP 484)

* **Python ≥ 3.10 (PEP 604)**: Use the bitwise OR operator `|`.
* **Python < 3.10 (PEP 484)**: Use `typing.Union` or `typing.Optional`.

```python
from typing import Union, Optional

# PEP 604 (Modern)
def modern_union(param: dict | tuple | None) -> float | bytes | None:
    ...

# PEP 484 (Legacy/Portable)
def legacy_union(param: Union[dict, tuple]) -> Optional[float]:
    ...

```

### 3. Subscripted Generic Collections (PEP 585 & PEP 484)

* **Python ≥ 3.9 (PEP 585)**: Use standard collection types directly (`list[str]`, `dict[str, int]`).
* **Python < 3.9 (PEP 484)**: Import capitalized variants from the `typing` module (`typing.List[str]`).

```python
from collections import abc
import typing

# PEP 585 Builtins & Abstract Base Classes
def process_sequences(data: list[str], stream: abc.MutableSequence[int]):
    ...

# PEP 484 Type Factories (Emits non-fatal deprecation warnings on Python ≥ 3.9)
def legacy_sequences(data: typing.List[int]):
    ...

```

### 4. Literals and Forward References

* **Literals (PEP 586)**: Restrict inputs to precise, explicit primitive values or Enum members.
* **Forward References**: Wrap types in strings when declaring self-referential classes or referring to objects defined later in the submodule.

```python
from typing import Literal

class MyOtherClass:
    # Relative Forward Reference
    def clone(self) -> list['MyOtherClass']:
        return [self]

    # Literal Restriction
    def set_layout(self, order: Literal['C', 'F', 'A']):
        ...

# Absolute Forward Reference (Fully-qualified string pathway)
def external_factory(param: 'my_package.my_module.MyClass'):
    ...

```

### 5. Generators and Coroutines

Annotate synchronous or asynchronous execution flows using abstract collections matching their yield and return signatures.

```python
from collections import abc

@beartype
def my_sync_generator() -> abc.Generator[int, None, None]:
    yield from range(5)

@beartype
async def my_async_generator() -> abc.AsyncGenerator[int, None]:
    yield 42

```

---

## Advanced Verification Tools

### The Beartype Cave (`beartype.cave`)

The `beartype.cave` submodule exposes performance-optimized type tuples and hard-to-access internal interpreter types.

```python
from beartype.cave import NoneType, ScalarTypes, RegexTypes, GeneratorType

# Evaluates quickly against combinations of types
def handle_scalars(val: ScalarTypes) -> NoneType:
    ...

```

### Complex Constraints via Validators (`beartype.vale`)

Using PEP 593 `typing.Annotated`, validators enforce precise internal structure and numeric data assertions via arbitrary lambda evaluations or functional descriptors.

```python
from beartype.vale import Is, IsAttr, IsEqual
from typing import Annotated
import numpy as np

# Single-expression lambda validator
NumpyArray2DFloat = Annotated[
    np.ndarray,
    Is[lambda arr: arr.ndim == 2 and arr.dtype == np.dtype(np.float64)]
]

# Composition using declarative expressions (&, |, ~)
IsNumpyArray1D = IsAttr['ndim', IsEqual[1]]
IsNumpyArrayFloat = IsAttr['dtype', IsEqual[np.dtype(np.float64)]]

NumpyArray1DFloat = Annotated[np.ndarray, IsNumpyArray1D, IsNumpyArrayFloat]

```

---

## Configuration API

To adjust type checking rules globally or locally, substitute the default decorator with a custom configuration instance constructed using `BeartypeConf`.

```python
from beartype import beartype, BeartypeConf, BeartypeStrategy

# Custom configuration generation
strict_beartype = beartype(
    conf=BeartypeConf(
        is_color=False,                  # Force disable ANSI escape sequences in exceptions
        is_debug=True,                  # Activate verbose developer debugging
        is_pep484_tower=True,           # Expand 'float' to 'float | int' implicitly
        strategy=BeartypeStrategy.O1,   # Enforce strict constant-time analysis
    )
)

@strict_beartype
def configured_function(data: list[float]):
    ...

```

---

## Automated App-Wide Enforcement (Import Hooks)

Rather than manually appending the `@beartype` decorator across thousands of callables, you can enforce comprehensive type checking across full code directories using `beartype.claw` import hooks.

```python
# Add exactly ONE of these options to the absolute top of your package's __init__.py file:

# 1. THE FAST WAY: Enforces rules on the current package and its submodules implicitly
from beartype.claw import beartype_this_package
beartype_this_package()

# 2. THE FINE-GRAINED WAY: Precison strike target subpackages explicitly
from beartype.claw import beartype_package
beartype_package('my_package.core_logic')

# 3. THE MULTI-PACKAGE WAY: Declare an iterable target array
from beartype.claw import beartype_packages
beartype_packages(('my_package.api', 'my_package.utils'))

# 4. THE NUCLEAR OPTION: Forces type checks across the entire Python ecosystem runtime
from beartype.claw import beartype_all
beartype_all()

```

### Static Analysis Mutation under Import Hooks

When active, `beartype.claw` hooks dynamically intercept package imports and mutate bytecode to apply the following alterations:

1. Automatically decorates every function, class method, and class structure with `@beartype`.
2. Appends every PEP 526 variable assignment (`my_var: int = "bad"`) with an implicit evaluation statement calling `beartype.door.die_if_unbearable()`, creating a true runtime-static hybrid safety environment.
