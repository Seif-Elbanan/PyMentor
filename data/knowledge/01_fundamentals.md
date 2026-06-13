---
topic: python fundamentals
difficulty: beginner
---
# Python Fundamentals

## Variables and assignment
Python variables are names bound to objects. Assignment uses `=` and does not require a
type declaration. For example, `score = 10` binds the name `score` to an integer object.
A later statement can bind the same name to another object. Variable names should be
descriptive, cannot begin with a digit, and are case-sensitive.

## Core data types
Common built-in scalar types are `int`, `float`, `str`, `bool`, and `NoneType`. Use
`type(value)` when inspecting a value during learning or debugging. Conversions such as
`int("12")` and `str(12)` create values of a requested type, but invalid conversions raise
exceptions. The operators `+`, `-`, `*`, `/`, `//`, `%`, and `**` perform arithmetic.

## Input and output
`print()` displays values. `input()` always returns a string, even when the learner enters
digits. Numeric input therefore needs explicit conversion, for example
`age = int(input("Age: "))`. Programs should handle invalid input rather than assuming every
entry can be converted.
