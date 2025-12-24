from flowcheck import analyze


def test_unreachable_elif_condition():
    code = """
def example(x):
    if x > 10:
        return "big"
    elif x > 5:
        return "medium"
    elif x > 20:
        return "huge"
"""
    issues = analyze(code)
    assert any(
        i.code in {"unreachable-condition", "redundant-condition", "unreachable-branch"}
        for i in issues
    )




def test_unreachable_code_after_return():
    code = """
def f(x):
    if x > 0:
        return 1
        x = 2
    return 3
"""
    issues = analyze(code)
    assert any(i.code == "unreachable-code" for i in issues)


def test_missing_return_some_paths():
    code = """
def f(x):
    if x > 0:
        return 1
    else:
        x = 2
"""
    issues = analyze(code)
    assert any(i.code == "missing-return" for i in issues)


def test_maybe_uninitialized_across_branches():
    code = """
def f(flag):
    if flag:
        x = 1
    return x
"""
    issues = analyze(code)
    assert any(i.code == "maybe-uninitialized" for i in issues)


def test_constant_condition_branch_unreachable():
    code = """
def f():
    if True:
        return 1
    else:
        return 2
"""
    issues = analyze(code)
    assert any(i.code == "always-true-condition" for i in issues)
    assert any(i.code == "unreachable-branch" for i in issues)
