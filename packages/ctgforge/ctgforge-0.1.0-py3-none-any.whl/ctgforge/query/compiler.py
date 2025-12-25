from dataclasses import dataclass
from typing import Union

from .expr import And, Expr, Not, Or, Term
from .specs import FieldSpec


@dataclass
class CompiledQuery:
    params: dict[str, str]  # e.g. {"query.con": "...", "filter.overallStatus": "..."}


class QueryCompilerError(ValueError):
    pass


def compile_to_params(expr: Union[Expr, None]) -> CompiledQuery:
    if expr is None:
        return CompiledQuery(params={})

    # Partition the expression into per-param subexpressions.
    groups = _split_by_param(expr)

    params: dict[str, str] = {}

    for param, subexpr in groups.items():
        # All terms in this subexpr share same param, but may have different kinds.
        # We inspect the first Term we can find to determine compilation mode.
        field_specs = _collect_field_specs(subexpr)
        if not field_specs:
            continue
        kind = next(iter(field_specs)).kind

        if kind == "query":
            params[param] = _compile_query_expr(subexpr)

        elif kind == "filter_list":
            items = _compile_filter_list(subexpr)
            params[param] = ",".join(items)

        elif kind == "filter_advanced":
            params[param] = _compile_filter_advanced(subexpr)

        else:
            raise QueryCompilerError(f"Unsupported field kind: {kind}")

    # Final step: replace spaces with '+' for URL encoding.
    for k, v in params.items():
        params[k] = v.replace(" ", "+")

    return CompiledQuery(params=params)


def _split_by_param(expr: Expr) -> dict[str, Expr]:
    """
    Returns {param_name: Expr} where each Expr contains only terms with the same param_name.
    Enforces that boolean OR does not cross params.
    """
    if isinstance(expr, Term):
        return {expr.field.param: expr}

    if isinstance(expr, And):
        left = _split_by_param(expr.left)
        right = _split_by_param(expr.right)
        return _merge_groups_and(left, right)

    if isinstance(expr, Or):
        left = _split_by_param(expr.left)
        right = _split_by_param(expr.right)

        # OR across different params cannot be represented as separate query params
        # because API combines params with AND semantics.
        if set(left.keys()) != set(right.keys()) or len(left) != 1:
            raise QueryCompilerError(
                "OR across different search parameters is not supported. "
                "Wrap OR terms within the same field (e.g., condition.in_(...)), "
                "or implement a fallback-to-query.term expert compiler."
            )

        # Merge the single param group
        (param,) = left.keys()
        return {param: Or(left[param], right[param])}

    if isinstance(expr, Not):
        inner = _split_by_param(expr.expr)
        if len(inner) != 1:
            raise QueryCompilerError("NOT across multiple parameters is not supported.")
        (param,) = inner.keys()
        return {param: Not(inner[param])}

    raise TypeError(expr)


def _collect_field_specs(expr: Expr) -> set[FieldSpec]:
    specs: set[FieldSpec] = set()

    if isinstance(expr, Term):
        specs.add(expr.field)

    elif isinstance(expr, (And, Or)):
        specs |= _collect_field_specs(expr.left)
        specs |= _collect_field_specs(expr.right)

    elif isinstance(expr, Not):
        specs |= _collect_field_specs(expr.expr)

    return specs


def _merge_groups_and(left: dict[str, Expr], right: dict[str, Expr]) -> dict[str, Expr]:
    out = dict(left)
    for param, expr in right.items():
        if param in out:
            out[param] = And(out[param], expr)
        else:
            out[param] = expr
    return out


# ----------------------
# Compilation strategies
# ----------------------


def _compile_term(t: Term) -> str:
    # For query params like query.cond / query.intr / query.spons,
    # the server interprets the string within that search area.
    # So we keep it simple and safely quoted.
    v = t.value
    if t.op == "eq":
        return f'"{v}"'
    if t.op == "contains":
        return f"({v})"
    if t.op == "in":
        values = " OR ".join(f'"{item}"' for item in v)
        return f"({values})"
    raise QueryCompilerError(f"Unsupported op for query param: {t.op}")


def _compile_query_expr(expr: Expr) -> str:
    """Compile boolean expression for query.* params as a single string."""
    if isinstance(expr, Term):
        return _compile_term(expr)
    if isinstance(expr, And):
        return f"({_compile_query_expr(expr.left)}) AND ({_compile_query_expr(expr.right)})"
    if isinstance(expr, Or):
        return f"({_compile_query_expr(expr.left)}) OR ({_compile_query_expr(expr.right)})"
    if isinstance(expr, Not):
        return f"NOT ({_compile_query_expr(expr.expr)})"
    raise TypeError(expr)


def _compile_filter_list(expr: Expr) -> list[str]:
    """
    filter.overallStatus expects a comma-separated list of values.
    We support eq(value) and in_([...]) and AND-combination (union of constraints).
    """
    items: set[str] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, Term):
            if e.op == "eq":
                items.add(str(e.value))
                return
            elif e.op == "in":
                items.update(str(v) for v in e.value)
                return
            raise QueryCompilerError(f"Unsupported op: {e.op}")
        if isinstance(e, And):
            walk(e.left)
            walk(e.right)
            return
        raise QueryCompilerError("Doesn't support OR/NOT for this search area for now.")

    walk(expr)
    return list(items)


def _compile_filter_advanced(expr: Expr) -> str:
    """
    filter.advanced accepts advanced query strings like AREA[StartDate]2022.
    For phase, we compile as "AREA[Phase]PHASE3" etc.)
    """
    parts: list[str] = []

    def walk(e: Expr) -> None:
        if isinstance(e, Term):
            if e.field.area is None:
                raise QueryCompilerError("Advanced filter term missing area.")
            if e.op == "eq":
                parts.append(f"AREA[{e.field.area}]{e.value}")
                return
            if e.op == "in":
                inner = " OR ".join(f"{v}" for v in e.value)
                parts.append(f"AREA[{e.field.area}]({inner})")
                return
            raise QueryCompilerError(f"Unsupported op: {e.op}")
        if isinstance(e, And):
            walk(e.left)
            walk(e.right)
            return
        raise QueryCompilerError("Doesn't support OR/NOT for this search area for now.")

    walk(expr)
    return " AND ".join(parts)
