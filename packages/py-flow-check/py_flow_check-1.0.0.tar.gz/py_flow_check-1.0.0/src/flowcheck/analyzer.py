from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Optional, Set

from .models import Issue
from .reason import (
    Interval,
    VarCondition,
    parse_var_condition,
    union_intersect,
    union_subtract,
    union_is_empty,
    union_is_equal,
)


@dataclass
class BlockResult:
    initialized: Set[str]
    terminates: bool  # cannot continue past this block
    returns: bool     # terminates specifically by return


def _pos(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", 1), getattr(node, "col_offset", 0))


def _const_truth(expr: ast.expr) -> Optional[bool]:
    if isinstance(expr, ast.Constant):
        return bool(expr.value)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        inner = _const_truth(expr.operand)
        return None if inner is None else (not inner)
    return None


class LocalFacts(ast.NodeVisitor):
    """
    Collects:
      - local variable names that are assigned anywhere in the function
      - declared global/nonlocal names
      - imported names at module level and function level
    """
    def __init__(self) -> None:
        self.assigned: Set[str] = set()
        self.global_names: Set[str] = set()
        self.nonlocal_names: Set[str] = set()
        self.imported: Set[str] = set()

    def visit_Global(self, node: ast.Global) -> None:
        self.global_names |= set(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocal_names |= set(node.names)

    def visit_Import(self, node: ast.Import) -> None:
        for a in node.names:
            self.imported.add(a.asname or a.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for a in node.names:
            if a.name == "*":
                continue
            self.imported.add(a.asname or a.name)

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            self.assigned |= self._names_in_target(t)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.assigned |= self._names_in_target(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.assigned |= self._names_in_target(node.target)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.assigned |= self._names_in_target(node.target)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.assigned |= self._names_in_target(node.target)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for it in node.items:
            if it.optional_vars is not None:
                self.assigned |= self._names_in_target(it.optional_vars)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for it in node.items:
            if it.optional_vars is not None:
                self.assigned |= self._names_in_target(it.optional_vars)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.assigned.add(node.name)
        self.generic_visit(node)

    def _names_in_target(self, target: ast.AST) -> Set[str]:
        out: Set[str] = set()
        if isinstance(target, ast.Name):
            out.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                out |= self._names_in_target(e)
        return out


class FlowAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.issues: List[Issue] = []
        self._fn_name: str | None = None
        self._locals_assigned: Set[str] = set()
        self._globals: Set[str] = set()
        self._nonlocals: Set[str] = set()
        self._imports: Set[str] = set()

    def analyze_code(self, code: str) -> List[Issue]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        self.visit(tree)
        return self.issues

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_function(node)
        res = self._analyze_block(node.body, initialized=set())
        self._check_missing_return(node, res)
        self._exit_function()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_function(node)
        res = self._analyze_block(node.body, initialized=set())
        self._check_missing_return(node, res)
        self._exit_function()

    def _enter_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._fn_name = node.name

        facts = LocalFacts()
        facts.visit(node)

        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            facts.assigned.add(arg.arg)
        if node.args.vararg:
            facts.assigned.add(node.args.vararg.arg)
        if node.args.kwarg:
            facts.assigned.add(node.args.kwarg.arg)

        self._locals_assigned = facts.assigned
        self._globals = facts.global_names
        self._nonlocals = facts.nonlocal_names
        self._imports = facts.imported

    def _exit_function(self) -> None:
        self._fn_name = None
        self._locals_assigned = set()
        self._globals = set()
        self._nonlocals = set()
        self._imports = set()

    def _check_missing_return(self, node: ast.FunctionDef | ast.AsyncFunctionDef, res: BlockResult) -> None:
        has_any_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
        if has_any_return and not res.returns:
            line, col = _pos(node)
            self.issues.append(
                Issue(
                    code="missing-return",
                    message=f"Function '{node.name}' does not return on every path",
                    line=line,
                    col=col,
                    reason="Some paths can reach the end of the function without returning a value",
                )
            )

    def _analyze_block(self, stmts: list[ast.stmt], initialized: Set[str]) -> BlockResult:
        init = set(initialized)
        terminated = False
        returned = False

        for stmt in stmts:
            if terminated:
                line, col = _pos(stmt)
                self.issues.append(
                    Issue(
                        code="unreachable-code",
                        message="This code can never run",
                        line=line,
                        col=col,
                        reason="A previous statement always returns or raises",
                    )
                )
                continue

            init, terminated, returned = self._analyze_stmt(stmt, init)

        return BlockResult(init, terminated, returned)

    def _analyze_stmt(self, stmt: ast.stmt, initialized: Set[str]) -> tuple[Set[str], bool, bool]:
        if isinstance(stmt, ast.Return):
            if stmt.value:
                self._check_expr(stmt.value, initialized)
            return set(initialized), True, True

        if isinstance(stmt, ast.Raise):
            if stmt.exc:
                self._check_expr(stmt.exc, initialized)
            return set(initialized), True, False

        if isinstance(stmt, ast.Assign):
            self._check_expr(stmt.value, initialized)
            new_init = set(initialized)
            for t in stmt.targets:
                new_init |= self._names_assigned(t)
            return new_init, False, False

        if isinstance(stmt, ast.AnnAssign):
            if stmt.value:
                self._check_expr(stmt.value, initialized)
            new_init = set(initialized) | self._names_assigned(stmt.target)
            return new_init, False, False

        if isinstance(stmt, ast.AugAssign):
            self._check_expr(stmt.target, initialized)
            self._check_expr(stmt.value, initialized)
            new_init = set(initialized) | self._names_assigned(stmt.target)
            return new_init, False, False

        if isinstance(stmt, ast.Expr):
            self._check_expr(stmt.value, initialized)
            return set(initialized), False, False

        if isinstance(stmt, ast.If):
            return self._analyze_if(stmt, initialized)

        # Conservative handling for loops, try, with: still check for uninitialized usage inside them.
        self.generic_visit(stmt)
        return set(initialized), False, False

    # -------------------------
    # NEW: control-flow helpers
    # -------------------------

    def _block_always_terminates(self, stmts: list[ast.stmt]) -> bool:
        """
        Returns True if executing stmts will always terminate (return or raise).
        Conservative: returns False if unsure.
        """
        for stmt in stmts:
            if isinstance(stmt, (ast.Return, ast.Raise)):
                return True

            # If an if has both branches and both always terminate, then it always terminates.
            if isinstance(stmt, ast.If) and stmt.orelse:
                if self._block_always_terminates(stmt.body) and self._block_always_terminates(stmt.orelse):
                    return True

            # Anything else: we do not try to prove termination.
        return False

    def _check_controlflow_unreachable_in_if_elif_chain(self, node: ast.If) -> None:
        """
        NEW RULE:
        If earlier branches in an if/elif chain always terminate (return/raise),
        then later elif branches can never run.
        """
        cursor: ast.If | None = node
        prior_always_terminates = False

        while cursor is not None:
            if prior_always_terminates:
                t = cursor.test
                line, col = _pos(t)
                self.issues.append(
                    Issue(
                        code="unreachable-branch",
                        message="This branch can never run",
                        line=line,
                        col=col,
                        reason="All previous branches in this if/elif chain always return or raise",
                    )
                )
                return

            # If this branch always terminates, then any later elif is unreachable.
            if self._block_always_terminates(cursor.body):
                prior_always_terminates = True

            # Move to next elif if present
            if len(cursor.orelse) == 1 and isinstance(cursor.orelse[0], ast.If):
                cursor = cursor.orelse[0]
            else:
                cursor = None

    def _analyze_if(self, node: ast.If, initialized: Set[str]) -> tuple[Set[str], bool, bool]:
        self._check_expr(node.test, initialized)

        # NEW: first check control-flow unreachable elif branches
        self._check_controlflow_unreachable_in_if_elif_chain(node)

        # Existing: math based condition overlap checks
        self._check_if_elif_chain(node)

        truth = _const_truth(node.test)
        if truth is True:
            line, col = _pos(node.test)
            self.issues.append(
                Issue(
                    code="always-true-condition",
                    message="This condition is always true",
                    line=line,
                    col=col,
                    reason="The condition is a constant truthy value",
                )
            )
            body_res = self._analyze_block(node.body, set(initialized))
            if node.orelse:
                line2, col2 = _pos(node.orelse[0])
                self.issues.append(
                    Issue(
                        code="unreachable-branch",
                        message="This else branch can never run",
                        line=line2,
                        col=col2,
                        reason="The if condition is always true",
                    )
                )
            return body_res.initialized, body_res.terminates, body_res.returns

        if truth is False:
            line, col = _pos(node.test)
            self.issues.append(
                Issue(
                    code="always-false-condition",
                    message="This condition is always false",
                    line=line,
                    col=col,
                    reason="The condition is a constant falsy value",
                )
            )
            if node.body:
                line2, col2 = _pos(node.body[0])
                self.issues.append(
                    Issue(
                        code="unreachable-branch",
                        message="This if branch can never run",
                        line=line2,
                        col=col2,
                        reason="The if condition is always false",
                    )
                )
            else_res = self._analyze_block(node.orelse, set(initialized)) if node.orelse else BlockResult(set(initialized), False, False)
            return else_res.initialized, else_res.terminates, else_res.returns

        body_res = self._analyze_block(node.body, set(initialized))
        else_res = self._analyze_block(node.orelse, set(initialized)) if node.orelse else BlockResult(set(initialized), False, False)

        merged_init = body_res.initialized.intersection(else_res.initialized)
        terminates = bool(node.orelse) and body_res.terminates and else_res.terminates
        returns = bool(node.orelse) and body_res.returns and else_res.returns
        return merged_init, terminates, returns

    def _names_assigned(self, target: ast.AST) -> Set[str]:
        out: Set[str] = set()
        if isinstance(target, ast.Name):
            out.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                out |= self._names_assigned(e)
        return out

    def _is_real_local(self, name: str) -> bool:
        if name in self._globals or name in self._nonlocals:
            return False
        if name in self._imports:
            return False
        return name in self._locals_assigned

    def _check_expr(self, expr: ast.AST, initialized: Set[str]) -> None:
        if self._fn_name is None:
            return

        for node in ast.walk(expr):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if not self._is_real_local(node.id):
                    continue
                if node.id in initialized:
                    continue

                line, col = _pos(node)
                self.issues.append(
                    Issue(
                        code="maybe-uninitialized",
                        message=f"'{node.id}' might be used before it is assigned",
                        line=line,
                        col=col,
                        reason="This variable is not assigned on every possible execution path before this use",
                    )
                )

    def _check_if_elif_chain(self, node: ast.If) -> None:
        tests: list[ast.expr] = []
        cursor: ast.If | None = node
        while cursor is not None:
            tests.append(cursor.test)
            if len(cursor.orelse) == 1 and isinstance(cursor.orelse[0], ast.If):
                cursor = cursor.orelse[0]
            else:
                cursor = None

        parsed: list[VarCondition] = []
        for t in tests:
            vc = parse_var_condition(t)
            if vc is None:
                return
            parsed.append(vc)

        var = parsed[0].var
        if any(p.var != var for p in parsed):
            return

        remaining: list[Interval] = [Interval(None, None, False, False)]

        for idx, cond in enumerate(parsed):
            feasible = union_intersect(remaining, cond.allowed)

            if union_is_empty(feasible):
                t = tests[idx]
                line, col = _pos(t)
                self.issues.append(
                    Issue(
                        code="unreachable-condition",
                        message="This condition can never be true here",
                        line=line,
                        col=col,
                        reason="Earlier conditions already exclude all values that would make this true",
                    )
                )
            else:
                if union_is_equal(feasible, remaining):
                    t = tests[idx]
                    line, col = _pos(t)
                    self.issues.append(
                        Issue(
                            code="redundant-condition",
                            message="This condition is redundant in this if/elif chain",
                            line=line,
                            col=col,
                            reason="Given previous conditions were false, this condition is always true",
                        )
                    )

            remaining = union_subtract(remaining, cond.allowed)
            # If remaining becomes empty, later elif conditions are unreachable by math,
            # but we let the loop finish.


def analyze(code: str) -> List[Issue]:
    return FlowAnalyzer().analyze_code(code)
