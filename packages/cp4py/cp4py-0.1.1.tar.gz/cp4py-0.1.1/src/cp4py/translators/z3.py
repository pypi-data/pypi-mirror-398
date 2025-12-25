from fractions import Fraction
from typing import Any, Iterable

from z3 import Int, Real, Solver, Optimize, sat, And, Or, Distinct, is_int_value, is_rational_value

from cp4py.translators.base import BaseTranslator


class Z3Translator(BaseTranslator):
    def __init__(self):
        self.vars: dict[str, Any] = {}
        self.constraints: list = []
        self.objective = None
        self.objective_type = None  # "minimize" or "maximize"

    def translate(self, constraints: Iterable) -> None:
        for constraint in constraints:
            self._translate_constraint(constraint)

    def _translate_constraint(self, constraint: list) -> None:
        op = constraint[0]

        if op == "int":
            self._translate_int(constraint)
        elif op == "real":
            self._translate_real(constraint)
        elif op in ("<=", "<", ">=", ">", "==", "!="):
            self._translate_comparison(constraint)
        elif op == "+":
            pass  # Arithmetic is handled within expressions
        elif op == "or":
            self._translate_or(constraint)
        elif op == "and":
            self._translate_and(constraint)
        elif op == "alldifferent":
            self._translate_alldifferent(constraint)
        elif op == "minimize":
            self._translate_objective(constraint, minimize=True)
        elif op == "maximize":
            self._translate_objective(constraint, minimize=False)

    def _translate_int(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = Int(name)
        self.vars[name] = var
        self.constraints.append(var >= lb)
        self.constraints.append(var <= ub)

    def _translate_real(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = Real(name)
        self.vars[name] = var
        self.constraints.append(var >= lb)
        self.constraints.append(var <= ub)

    def _translate_comparison(self, constraint: list) -> None:
        op, lhs, rhs = constraint
        lhs_expr = self._to_expr(lhs)
        rhs_expr = self._to_expr(rhs)

        if op == "<=":
            self.constraints.append(lhs_expr <= rhs_expr)
        elif op == "<":
            self.constraints.append(lhs_expr < rhs_expr)
        elif op == ">=":
            self.constraints.append(lhs_expr >= rhs_expr)
        elif op == ">":
            self.constraints.append(lhs_expr > rhs_expr)
        elif op == "==":
            self.constraints.append(lhs_expr == rhs_expr)
        elif op == "!=":
            self.constraints.append(lhs_expr != rhs_expr)

    def _translate_or(self, constraint: list) -> None:
        # ["or", expr1, expr2, ...]
        sub_constraints = [self._to_constraint(sub) for sub in constraint[1:]]
        self.constraints.append(Or(*sub_constraints))

    def _translate_and(self, constraint: list) -> None:
        # ["and", expr1, expr2, ...]
        for sub in constraint[1:]:
            self._translate_constraint(sub)

    def _translate_alldifferent(self, constraint: list) -> None:
        # ["alldifferent", var1, var2, ...]
        vars_list = [self.vars[name] for name in constraint[1:]]
        self.constraints.append(Distinct(*vars_list))

    def _translate_objective(self, constraint: list, minimize: bool) -> None:
        _, expr = constraint
        self.objective = self._to_expr(expr)
        self.objective_type = "minimize" if minimize else "maximize"

    def _to_expr(self, term: Any):
        if isinstance(term, (int, float)):
            return term
        elif isinstance(term, str):
            return self.vars[term]
        elif isinstance(term, list):
            op = term[0]
            if op == "+":
                return sum(self._to_expr(arg) for arg in term[1:])
            elif op == "sum":
                return self._to_sum_expr(term)
            else:
                raise ValueError(f"Unsupported expression operator: {op}")
        else:
            raise ValueError(f"Unsupported term type: {type(term)}")

    def _to_sum_expr(self, term: list):
        # ["sum", term1, term2, ...] where term is "x" or [coeff, "x"]
        result = 0
        for t in term[1:]:
            if isinstance(t, list) and len(t) == 2:
                coeff, var = t
                result += coeff * self._to_expr(var)
            else:
                result += self._to_expr(t)
        return result

    def _to_constraint(self, constraint: list):
        op = constraint[0]
        if op in ("<=", "<", ">=", ">", "==", "!="):
            lhs_expr = self._to_expr(constraint[1])
            rhs_expr = self._to_expr(constraint[2])
            if op == "<=":
                return lhs_expr <= rhs_expr
            elif op == "<":
                return lhs_expr < rhs_expr
            elif op == ">=":
                return lhs_expr >= rhs_expr
            elif op == ">":
                return lhs_expr > rhs_expr
            elif op == "==":
                return lhs_expr == rhs_expr
            elif op == "!=":
                return lhs_expr != rhs_expr
        elif op == "or":
            return Or(*[self._to_constraint(sub) for sub in constraint[1:]])
        elif op == "and":
            return And(*[self._to_constraint(sub) for sub in constraint[1:]])
        else:
            raise ValueError(f"Unsupported constraint operator: {op}")

    def solve(self) -> dict[str, Any]:
        if self.objective is not None:
            solver = Optimize()
            for c in self.constraints:
                solver.add(c)
            if self.objective_type == "minimize":
                solver.minimize(self.objective)
            else:
                solver.maximize(self.objective)
        else:
            solver = Solver()
            for c in self.constraints:
                solver.add(c)

        if solver.check() == sat:
            model = solver.model()
            result = {}
            for name, var in self.vars.items():
                val = model[var]
                if val is not None:
                    # Convert Z3 value to Python value
                    if is_int_value(val):
                        result[name] = val.as_long()
                    elif is_rational_value(val):
                        # Real value - use as_fraction for exact conversion
                        frac = val.as_fraction()
                        result[name] = float(Fraction(frac.numerator, frac.denominator))
                    else:
                        # Fallback
                        result[name] = float(str(val))
            return result
        else:
            raise RuntimeError("No solution found")
