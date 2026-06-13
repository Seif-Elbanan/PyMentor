---
topic: common misconceptions
difficulty: beginner
---
# Common Python Misconceptions

## Assignment versus equality
`=` assigns a value to a name. `==` compares two values and produces a Boolean. Writing
`if score = 10:` is a syntax error because a condition needs comparison rather than assignment.

## Range and indexing
Python sequence indexes start at zero. The stop argument of `range` and slicing is exclusive.
Therefore a loop over `range(len(items))` ends at `len(items) - 1`. Prefer direct iteration
over values when the index is not needed.

## Return versus print
`print(value)` displays a representation for a person. `return value` gives a value back to
the caller so another part of the program can use it. A function that only prints usually
cannot be composed in calculations.

## Mutation and aliasing
Two names can refer to the same mutable list. Mutating through either name changes the shared
object. Use `copy()` for a shallow copy when independent top-level lists are needed. The
expression `a = b` does not copy the object.
