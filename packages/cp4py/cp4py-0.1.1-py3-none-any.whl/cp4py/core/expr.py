from typing import Any

COMPARISON_OPS = {"<=", "<", ">=", ">", "==", "!="}
ARITHMETIC_OPS = {"+"}
LOGICAL_OPS = {"or", "and"}


def validate(expr: list) -> bool:
    if not isinstance(expr, list) or len(expr) == 0:
        raise ValueError("Expression must be a non-empty list")

    op = expr[0]

    if op in ("int", "real"):
        return _validate_var_decl(expr)
    elif op in COMPARISON_OPS:
        return _validate_comparison(expr)
    elif op in ARITHMETIC_OPS:
        return _validate_arithmetic(expr)
    elif op == "sum":
        return _validate_sum(expr)
    elif op in LOGICAL_OPS:
        return _validate_logical(expr)
    elif op == "alldifferent":
        return _validate_alldifferent(expr)
    elif op in ("minimize", "maximize"):
        return _validate_objective(expr)
    else:
        raise ValueError(f"Unknown operator: {op}")


def _validate_var_decl(expr: list) -> bool:
    # ["int", name, lower, upper] or ["real", name, lower, upper]
    op = expr[0]
    if len(expr) != 4:
        raise ValueError(f"{op} requires 3 arguments: name, lower, upper")
    _, name, lower, upper = expr
    if lower > upper:
        raise ValueError(f"Invalid bounds: {lower} > {upper}")
    return True


def _validate_comparison(expr: list) -> bool:
    # [op, lhs, rhs]
    if len(expr) != 3:
        raise ValueError(f"Comparison requires 2 arguments")
    _, lhs, rhs = expr
    _validate_term(lhs)
    _validate_term(rhs)
    return True


def _validate_arithmetic(expr: list) -> bool:
    # ["+", arg1, arg2, ...]
    if len(expr) < 2:
        raise ValueError("Arithmetic requires at least 1 argument")
    for arg in expr[1:]:
        _validate_term(arg)
    return True


def _validate_sum(expr: list) -> bool:
    # ["sum", term1, term2, ...]
    # term can be: "x" (coeff=1) or [coeff, "x"]
    if len(expr) < 2:
        raise ValueError("sum requires at least 1 term")
    for term in expr[1:]:
        if isinstance(term, list) and len(term) == 2:
            # [coeff, var]
            coeff, var = term
            if not isinstance(coeff, (int, float)):
                raise ValueError(f"Coefficient must be a number: {coeff}")
            _validate_term(var)
        else:
            # var with default coeff=1
            _validate_term(term)
    return True


def _validate_logical(expr: list) -> bool:
    # ["or", expr1, expr2, ...] or ["and", expr1, expr2, ...]
    if len(expr) < 2:
        raise ValueError("Logical requires at least 1 sub-expression")
    for sub in expr[1:]:
        validate(sub)
    return True


def _validate_alldifferent(expr: list) -> bool:
    # ["alldifferent", var1, var2, ...]
    if len(expr) < 2:
        raise ValueError("alldifferent requires at least 1 variable")
    for var in expr[1:]:
        _validate_term(var)
    return True


def _validate_objective(expr: list) -> bool:
    # ["minimize", expr] or ["maximize", expr]
    if len(expr) != 2:
        raise ValueError("Objective requires exactly 1 argument")
    _validate_term(expr[1])
    return True


def _validate_term(term: Any) -> bool:
    if isinstance(term, list):
        return validate(term)
    return True
