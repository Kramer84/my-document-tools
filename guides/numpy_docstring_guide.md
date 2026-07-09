# NumPy Docstring Style Guide

This document defines the standard syntax and structure for NumPy-style docstrings. Use this guide to format, validate, and correct Python docstrings.

---

## General Rules

* **Quotes**: Surround all docstrings with triple double quotes: `"""Docstring goes here."""`
* **Line Length**: Keep docstring lines to a maximum of **75 characters** to ensure readability in text terminals.
* **Text Formatting**:
  * Use `**bold**` and `*italics*` sparingly.
  * Use **double backticks** (`` `code` ``) for inline code, variable values, or monospaced text.
  * Use **single backticks** (` `parameter` `) when referencing function parameters.

---

## Docstring Sections (Order is Strict)

A function/method docstring should include the following sections in this exact order. Sections (except Summary and Deprecation) use an underlined heading with hyphens (`---`).

### 1. Short Summary
A one-line summary describing what the function does. Do **not** mention the function name or parameter names here.

```python
def add(a, b):
    """The sum of two numbers."""

```

*Note: If the function signature cannot be introspected automatically (e.g., C extensions), place the exact signature as the first line of the docstring followed by a blank line.*

### 2. Deprecation Warning

If the object is deprecated, include a warning at the top using a clear notification block. Specify the version deprecated, when it will be removed, the reason, and the alternative.

```text
.. deprecated:: 1.6.0
   `ndobj_old` will be removed in NumPy 2.0.0. Use `ndobj_new` instead.

```

### 3. Extended Summary

An optional paragraph or two clarifying the *functionality* of the code. Do not discuss implementation details or background theory here (save those for the **Notes** section).

### 4. Parameters

Lists arguments, keywords, and their respective types.

* Format: `name : type` (Note the space before and after the colon).
* If a type is omitted, omit the colon.
* Mark optional parameters with `, optional` or `, default Value`.

```text
Parameters
----------
x : int
    Description of parameter `x`.
y : float, optional
    Description of `y` (the default is 1.0).
order : {'C', 'F', 'A'}
    Choice of layout string. Default is 'C'.
x1, x2 : array_like
    Combine identical parameters together on one line.
*args
    Leave leading stars for variable arguments and omit type.
**kwargs
    Extra keyword arguments.

```

Common NumPy type conventions: `str`, `bool`, `data-type`, `iterable object`, `int or tuple of int`, `list of str`, `array_like`.

### 5. Returns

Defines returned values and types. Similar to Parameters, but the variable name is **optional**. However, the type is **always required**.

```text
Returns
-------
int
    Description of anonymous integer return value.
err_code : int
    Explicitly named return value description.

```

### 6. Yields

Used exclusively for generator functions instead of `Returns`. Follows the same format rules as `Returns` (type is mandatory, name is optional).

```text
Yields
------
item : str
    The next string item yielded by the generator.

```

### 7. Receives

Explains parameters passed into a generator's `.send()` method. Formatted exactly like `Parameters`. If `Receives` is present, `Yields` must also be present.

### 8. Other Parameters

An optional section to document infrequently used keyword parameters to avoid cluttering the primary `Parameters` section.

### 9. Raises

Lists errors that are non-obvious or highly likely to be raised, along with the conditions.

```text
Raises
------
ValueError
    If `x` is negative.

```

### 10. Warns

Lists warnings issued by the function, formatted identically to `Raises`.

### 11. Warnings

An optional free-text section for important edge cases or user cautions.

### 12. See Also

Refers to related code or functions. Use `module.function` formatting where applicable.

```text
See Also
--------
average : Weighted average.
fft.fft2 : 2-D fast discrete Fourier transform.
func_a, func_b, func_c

```

### 13. Notes

An optional section for theoretical background, mathematical algorithms, and implementation notes.

* **Math**: LaTeX equations can be added using blocks or inline syntax:
```text
.. math:: X(e^{j\omega }) = x(n)e^{-j\omega n}

```


Inline math uses `:math:`\omega``. Variable names inside math blocks should use `\mathtt{var}`. Keep math sparse for terminal readability.

### 14. References

Lists citations or source publications referenced inside the **Notes** section.

```text
References
----------
.. [1] O. McNoleg, "The integration of GIS...", Computers & Geosciences, 1996.

```

### 15. Examples

An optional but highly recommended section using standard Python `doctest` format (`>>>`).

* Separate individual examples with blank lines.
* Put a blank line before and after explanatory comments.
* Use `... ` for multi-line code blocks.
* Append `#random` for non-deterministic or platform-dependent output values.

```text
Examples
--------
>>> np.add(1, 2)
3

Comment explaining the next multi-line block.

>>> np.add([[1, 2], [3, 4]],
...        [[5, 6], [7, 8]])
array([[ 6,  8],
       [10, 12]])

```

---

## Documenting Classes

* **Class Docstring**: Use the exact same structural sections as functions (except `Returns`).
* **Constructor (`__init__`)**: Document constructor arguments within the **Parameters** section of the *Class* docstring. Do **not** list `self`.
* **Attributes Section**: Placed directly below the `Parameters` section to describe non-method variables.
```text
Attributes
----------
real : float
    The real component.
imag : float
    The imaginary component.

```


* **Methods Section**: Optional. Only use it to summarize the public API if the class has an overwhelming number of methods. Never include private methods (methods starting with `_`).

---

## Documenting Modules & Constants

### Modules

Every module must start with a docstring containing at least a summary line. Follow this section layout order:

1. Summary
2. Extended Summary
3. Routine Listings (encouraged for large modules)
4. See Also
5. Notes
6. References
7. Examples

*Note: Author and license information belong in source code comments, never inside the docstring.*

### Constants

Document constants using applicable function sections in this order:

1. Summary
2. Extended Summary
3. See Also
4. References
5. Examples
