
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

## Import Conventions

The following import conventions are used throughout the NumPy source and documentation:

```python
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

```

Do not abbreviate `scipy`. There is no motivating use case to abbreviate it in the real world, so we avoid it in the documentation to avoid confusion.

---

## Docstring Sections (Order is Strict)

A function/method docstring should include the following sections in this exact order. Sections (except Summary and Deprecation) use an underlined heading with hyphens (`---`).

### 1. Short Summary

A one-line summary describing what the function does. Do **not** mention the function name or parameter names here.

```python
def add(a, b):
    """The sum of two numbers."""

```

Note: If the function signature cannot be introspected automatically (e.g., C extensions), place the exact signature as the first line of the docstring followed by a blank line.

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

Note: If the combination of the function name and description creates a line that is too long, write the entry as two lines: the function name and colon on the first line, and the description on the next line indented by four spaces.

### 13. Notes

An optional section for theoretical background, mathematical algorithms, and implementation notes.

* **Math**: LaTeX equations can be added using blocks or inline syntax:



```text
.. math:: X(e^{j\omega }) = x(n)e^{-j\omega n}

```

Inline math uses `:math:`\omega``. Variable names inside math blocks should use `\mathtt{var}`. Keep math sparse for terminal readability.

* **Images**: Images are allowed but should not be central to the explanation. Include them using standard reST markup:



```text
.. image:: filename

```

where filename is relative to the reference guide source directory.

### 14. References

Lists citations or source publications referenced inside the **Notes** section.

```text
References
----------
.. [1] O. McNoleg, "The integration of GIS...", Computers & Geosciences, 1996.

```

Warning: Referencing citations (like `[1]`) within markdown/reST tables inside a numpydoc docstring will break the table markup.

### 15. Examples

An optional but highly recommended section using standard Python `doctest` format (`>>>`).

* Separate individual examples with blank lines.


* Put a blank line before and after explanatory comments.


* Use `... ` for multi-line code blocks.


* Append `#random` for non-deterministic or platform-dependent output values.


* Examples in *numpy* assume that `import numpy as np` is executed beforehand. All other imports, including `matplotlib.pyplot as plt` or the demonstrated function itself, must be explicitly imported.



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


* **Constructor (`__init__`)**: Document constructor arguments within the **Parameters** section of the *Class* docstring. Do **not** list `self`. Optionally, a docstring for `__init__` can be added to provide detailed initialization details.


* **Attributes Section**: Placed directly below the `Parameters` section to describe non-method variables.


* Attributes that are properties and have their own docstrings can be listed by name only, without a description.





```text
Attributes
----------
real : float
    The real component.
imag : float
    The imaginary component.

```

* **Methods Section**: Optional. Only use it to summarize the public API if the class has an overwhelming number of methods. Never include private methods (methods starting with `_`).


* If you need to explain a private method, refer to it in the **Extended Summary** or **Notes** section, but do not list it here.





### Method Docstrings

* Document methods exactly like other functions. Do not include `self` in the parameter list.


* If a method has an equivalent function, the method docstring should refer to it. Only include a brief summary and a **See Also** section in the method docstring, using a **Returns** or **Yields** section as appropriate.



### Documenting Class Instances

* **Single Instance**: If only a single instance of a class is exposed, document the class itself and use the instance name in examples.


* **Multiple Instances**: If multiple instances are exposed, write docstrings for each instance and assign them to the instances' `__doc__` attributes at run time. The class is documented as usual, and the exposed instances are mentioned in the **Notes** and **See Also** sections.



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

Note: Author and license information belong in source code comments, never inside the docstring.

### Constants

Constants should use the applicable function sections in this order:

1. Summary
2. Extended Summary (optional)
3. See Also (optional)
4. References (optional)
5. Examples (optional)

Note: Docstrings for constants are not visible in text terminals (as constants are of immutable types, meaning docstrings cannot be dynamically assigned to them). However, they will appear in documentation built with Sphinx.

---

## Other Points to Keep in Mind

* **array_like**: For arguments that take not only `ndarray` but also scalar or sequence types that can be converted to an ndarray, document the parameter type as `array_like`.


* **Links**: Standard links inside single backticks should render as hyperlinks. If Sphinx issues "Unknown target name" warnings in non-standard reST sections, avoid standard link target blocks. Instead, use the inline hyperlink form:


```text
`Example [http://www.example.com](http://www.example.com)`_

```
