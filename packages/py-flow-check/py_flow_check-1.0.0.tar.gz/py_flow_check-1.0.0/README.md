# py-flow-check

Static analyzer for logical flow bugs in Python.

It tries to catch:
- unreachable code after return or raise
- always true or always false conditions like `if True`
- unreachable or redundant conditions in if/elif chains (best with numeric comparisons)
- functions that do not return on every path
- variables that might be used before assignment on some paths

## Install

pip install py-flow-check

## CLI

flowcheck path/to/file.py

JSON output (useful for CI):

flowcheck --json path/to/file.py

Exit code:
- 0 if no issues
- 1 if issues found

## Python API

```python
from flowcheck import analyze

code = """
def f(flag):
    if flag:
        x = 1
    return x
"""
for issue in analyze(code):
    print(issue.format())
