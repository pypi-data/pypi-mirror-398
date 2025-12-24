from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass(frozen=True)
class Interval:
    low: float | None
    high: float | None
    low_inclusive: bool = False
    high_inclusive: bool = False

    def is_empty(self) -> bool:
        if self.low is None or self.high is None:
            return False
        if self.low < self.high:
            return False
        if self.low > self.high:
            return True
        return not (self.low_inclusive and self.high_inclusive)

    def intersect(self, other: "Interval") -> "Interval":
        low, low_inc = self.low, self.low_inclusive
        if other.low is not None:
            if low is None or other.low > low:
                low, low_inc = other.low, other.low_inclusive
            elif other.low == low:
                low_inc = low_inc and other.low_inclusive

        high, high_inc = self.high, self.high_inclusive
        if other.high is not None:
            if high is None or other.high < high:
                high, high_inc = other.high, other.high_inclusive
            elif other.high == high:
                high_inc = high_inc and other.high_inclusive

        return Interval(low, high, low_inc, high_inc)

    def subtract(self, other: "Interval") -> List["Interval"]:
        inter = self.intersect(other)
        if inter.is_empty():
            return [self]

        out: List[Interval] = []

        left = Interval(self.low, inter.low, self.low_inclusive, not inter.low_inclusive)
        if not left.is_empty():
            out.append(left)

        right = Interval(inter.high, self.high, not inter.high_inclusive, self.high_inclusive)
        if not right.is_empty():
            out.append(right)

        return out


def _normalize_union(union: List[Interval]) -> List[Interval]:
    """
    Merge overlapping intervals. Keeps union small and stable.
    """
    if not union:
        return []

    def key(i: Interval) -> Tuple[float, int]:
        low = float("-inf") if i.low is None else i.low
        low_inc = 1 if i.low_inclusive else 0
        return (low, -low_inc)

    items = sorted(union, key=key)
    merged: List[Interval] = [items[0]]

    for cur in items[1:]:
        prev = merged[-1]

        prev_high = float("inf") if prev.high is None else prev.high
        cur_low = float("-inf") if cur.low is None else cur.low

        touches = False
        if prev.high is None or cur.low is None:
            touches = True
        else:
            if prev_high > cur_low:
                touches = True
            elif prev_high == cur_low:
                touches = prev.high_inclusive or cur.low_inclusive

        if touches:
            new_low = prev.low
            new_low_inc = prev.low_inclusive

            if prev.high is None or cur.high is None:
                new_high = None
                new_high_inc = False
            else:
                if prev.high > cur.high:
                    new_high = prev.high
                    new_high_inc = prev.high_inclusive
                elif prev.high < cur.high:
                    new_high = cur.high
                    new_high_inc = cur.high_inclusive
                else:
                    new_high = prev.high
                    new_high_inc = prev.high_inclusive or cur.high_inclusive

            merged[-1] = Interval(new_low, new_high, new_low_inc, new_high_inc)
        else:
            merged.append(cur)

    return merged


def union_intersect(a: List[Interval], b: List[Interval]) -> List[Interval]:
    out: List[Interval] = []
    for i in a:
        for j in b:
            k = i.intersect(j)
            if not k.is_empty():
                out.append(k)
    return _normalize_union(out)


def union_subtract(a: List[Interval], cut: List[Interval]) -> List[Interval]:
    remaining = list(a)
    for c in cut:
        next_union: List[Interval] = []
        for r in remaining:
            next_union.extend(r.subtract(c))
        remaining = next_union
        if not remaining:
            return []
    return _normalize_union(remaining)


def union_is_empty(u: List[Interval]) -> bool:
    return len(u) == 0


def union_is_equal(a: List[Interval], b: List[Interval]) -> bool:
    a2 = _normalize_union(list(a))
    b2 = _normalize_union(list(b))
    return a2 == b2


@dataclass(frozen=True)
class VarCondition:
    var: str
    allowed: List[Interval]


def _parse_simple_compare(expr: ast.expr) -> Optional[VarCondition]:
    """
    Parse: x > c, x >= c, x < c, x <= c, x == c, x != c
    """
    if not isinstance(expr, ast.Compare):
        return None
    if len(expr.ops) != 1 or len(expr.comparators) != 1:
        return None
    if not isinstance(expr.left, ast.Name):
        return None

    comp = expr.comparators[0]
    if not (isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float))):
        return None

    x = expr.left.id
    v = float(comp.value)
    op = expr.ops[0]

    if isinstance(op, ast.Gt):
        return VarCondition(x, [Interval(v, None, False, False)])
    if isinstance(op, ast.GtE):
        return VarCondition(x, [Interval(v, None, True, False)])
    if isinstance(op, ast.Lt):
        return VarCondition(x, [Interval(None, v, False, False)])
    if isinstance(op, ast.LtE):
        return VarCondition(x, [Interval(None, v, False, True)])
    if isinstance(op, ast.Eq):
        return VarCondition(x, [Interval(v, v, True, True)])
    if isinstance(op, ast.NotEq):
        return VarCondition(x, [Interval(None, v, False, False), Interval(v, None, False, False)])

    return None


def parse_var_condition(expr: ast.expr) -> Optional[VarCondition]:
    """
    Supports boolean expressions for the same variable:
      - (x > 10 and x < 20)
      - (x < 0 or x > 5)
    Only if all parts reference the same variable.
    """
    simple = _parse_simple_compare(expr)
    if simple:
        return VarCondition(simple.var, _normalize_union(simple.allowed))

    if isinstance(expr, ast.BoolOp):
        parts = [parse_var_condition(v) for v in expr.values]
        if any(p is None for p in parts):
            return None

        var = parts[0].var  # type: ignore[union-attr]
        if any(p.var != var for p in parts if p is not None):
            return None

        unions = [p.allowed for p in parts if p is not None]  # type: ignore[union-attr]

        if isinstance(expr.op, ast.And):
            cur = unions[0]
            for u in unions[1:]:
                cur = union_intersect(cur, u)
            return VarCondition(var, cur)

        if isinstance(expr.op, ast.Or):
            cur = []
            for u in unions:
                cur.extend(u)
            return VarCondition(var, _normalize_union(cur))

    return None
