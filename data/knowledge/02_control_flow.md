---
topic: control flow
difficulty: beginner
---
# Control Flow

## Conditions
An `if` statement runs a block when its condition is truthy. Optional `elif` branches test
additional conditions, while `else` handles the remaining case. Python uses indentation to
define blocks. Comparisons include `==`, `!=`, `<`, `<=`, `>`, and `>=`. Boolean expressions
can combine conditions with `and`, `or`, and `not`.

## For loops
A `for` loop iterates over an iterable such as a string, list, or `range`. The call
`range(start, stop, step)` excludes the stop value. For example, `range(1, 4)` produces
1, 2, and 3. Use `enumerate(items)` when both the index and value are needed.

## While loops
A `while` loop repeats while its condition remains true. The loop body must normally change
state that affects the condition; otherwise the program may create an infinite loop.
`break` exits the nearest loop and `continue` skips to the next iteration. A bounded loop is
preferable when the maximum number of attempts is known.
