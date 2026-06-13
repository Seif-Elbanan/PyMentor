---
topic: collections
difficulty: beginner
---
# Python Collections

## Lists and tuples
A list is an ordered, mutable collection created with square brackets. Indexing begins at
zero, and negative indexes count from the end. Common list operations include `append`,
`extend`, `insert`, `remove`, and `pop`. A tuple is ordered but immutable, making it useful
for fixed records or values that should not change.

## Dictionaries and sets
A dictionary maps unique hashable keys to values. Accessing a missing key with square
brackets raises `KeyError`; `mapping.get(key, default)` supports a fallback. Iterate with
`items()` when both keys and values are required. A set stores unique hashable values and is
useful for membership checks and set operations such as union and intersection.

## Comprehensions
A list comprehension constructs a list from an iterable using an expression and optional
filter: `[x * x for x in numbers if x > 0]`. Comprehensions should remain short and clear.
Use a regular loop when the transformation needs multiple steps, side effects, or complex
branching.
