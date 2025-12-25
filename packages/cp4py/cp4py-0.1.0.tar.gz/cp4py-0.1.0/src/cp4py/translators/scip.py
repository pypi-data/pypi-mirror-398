from typing import Any, Iterable

from pyscipopt import Model, quicksum

from cp4py.translators.base import BaseTranslator


class SCIPTranslator(BaseTranslator):
    def __init__(self):
        self.model = Model()
        self.model.hideOutput()
        self.vars: dict[str, Any] = {}
        self.objective = None
        self.objective_type = None

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
        elif op == "alldifferent":
            self._translate_alldifferent(constraint)
        elif op == "minimize":
            self._translate_objective(constraint, minimize=True)
        elif op == "maximize":
            self._translate_objective(constraint, minimize=False)

    def _translate_int(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = self.model.addVar(name=name, vtype="I", lb=lb, ub=ub)
        self.vars[name] = var

    def _translate_real(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = self.model.addVar(name=name, vtype="C", lb=lb, ub=ub)
        self.vars[name] = var

    def _translate_comparison(self, constraint: list) -> None:
        op, lhs, rhs = constraint
        lhs_expr = self._to_expr(lhs)
        rhs_expr = self._to_expr(rhs)

        if op == "<=":
            self.model.addCons(lhs_expr <= rhs_expr)
        elif op == "<":
            # For integers, x < y is equivalent to x <= y - 1
            # For reals, we use a small epsilon
            self.model.addCons(lhs_expr <= rhs_expr - 1)
        elif op == ">=":
            self.model.addCons(lhs_expr >= rhs_expr)
        elif op == ">":
            self.model.addCons(lhs_expr >= rhs_expr + 1)
        elif op == "==":
            self.model.addCons(lhs_expr == rhs_expr)
        elif op == "!=":
            self._translate_ne(lhs_expr, rhs_expr)

    def _translate_ne(self, lhs_expr, rhs_expr):
        # x != y: use indicator constraints
        # b = 1 => x < y, b = 0 => x > y
        b = self.model.addVar(name="", vtype="B")
        M = 1000000  # Big-M
        self.model.addCons(lhs_expr - rhs_expr >= 1 - M * (1 - b))
        self.model.addCons(lhs_expr - rhs_expr <= -1 + M * b)

    def _translate_alldifferent(self, constraint: list) -> None:
        # ["alldifferent", var1, var2, ...]
        var_names = constraint[1:]
        vars_list = [self.vars[name] for name in var_names]
        n = len(vars_list)

        # For each pair, add x_i != x_j
        for i in range(n):
            for j in range(i + 1, n):
                self._translate_ne(vars_list[i], vars_list[j])

    def _translate_objective(self, constraint: list, minimize: bool) -> None:
        _, expr = constraint
        obj_expr = self._to_expr(expr)
        if minimize:
            self.model.setObjective(obj_expr, "minimize")
        else:
            self.model.setObjective(obj_expr, "maximize")

    def _to_expr(self, term: Any):
        if isinstance(term, (int, float)):
            return term
        elif isinstance(term, str):
            return self.vars[term]
        elif isinstance(term, list):
            op = term[0]
            if op == "+":
                return quicksum(self._to_expr(arg) for arg in term[1:])
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

    def solve(self) -> dict[str, Any]:
        self.model.optimize()

        if self.model.getStatus() in ("optimal", "feasible"):
            result = {}
            for name, var in self.vars.items():
                val = self.model.getVal(var)
                # Round integer variables
                if var.vtype() == "INTEGER":
                    result[name] = int(round(val))
                else:
                    result[name] = val
            return result
        else:
            raise RuntimeError(f"No solution found. Status: {self.model.getStatus()}")
