---
topic: functions
difficulty: intermediate
---
# Functions

## Defining and calling functions
A function groups reusable behavior and is defined with `def`. Parameters receive values
from arguments. A `return` statement sends a value to the caller and stops the function.
Without an explicit return, a function returns `None`. A docstring explains purpose,
parameters, return value, and important constraints.

## Scope and arguments
Names assigned inside a function are normally local. Reading or changing global state makes
functions harder to test, so prefer parameters and return values. Default argument values are
evaluated once when the function is defined. Do not use a mutable object such as `[]` as a
default; use `None` and create the list inside the function.

## Decomposition and testing
Good functions have one clear responsibility, meaningful names, and small interfaces. Test
normal inputs, boundary values, and invalid inputs. Pure functions are especially testable
because their output depends only on arguments and they do not change external state.
