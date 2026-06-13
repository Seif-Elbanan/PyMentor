---
topic: exceptions files classes
difficulty: intermediate
---
# Exceptions, Files, and Classes

## Exception handling
Exceptions report runtime problems. Put only the operation that may fail inside `try`, catch
specific exceptions with `except`, and use `else` for code that should run after success.
`finally` runs whether an exception occurred or not. Avoid a bare `except` because it hides
unexpected programming errors.

## File handling
Use `with open(path, mode, encoding="utf-8") as file:` so the file is closed automatically.
Mode `"r"` reads, `"w"` replaces content, and `"a"` appends. File operations can raise
`FileNotFoundError`, `PermissionError`, and decoding errors, so handle only errors the program
can meaningfully recover from.

## Classes and objects
A class defines behavior and data shared by objects. `__init__` initializes an instance, and
instance methods receive the object as `self`. Encapsulation means keeping related state and
behavior together behind a clear interface. Prefer composition when one object uses another;
use inheritance only when there is a genuine substitutable "is-a" relationship.
