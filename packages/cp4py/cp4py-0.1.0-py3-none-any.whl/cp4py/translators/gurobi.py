from typing import Any, Iterable

import gurobipy as gp
from gurobipy import GRB

from cp4py.translators.base import BaseTranslator


class GurobiTranslator(BaseTranslator):
    def __init__(self):
        self.model = gp.Model()
        self.model.Params.OutputFlag = 0
        self.vars: dict[str, Any] = {}

    def translate(self, constraints: Iterable) -> None:
        for constraint in constraints:
            self._translate_constraint(constraint)
        self.model.update()

    def _translate_constraint(self, constraint: list) -> None:
        op = constraint[0]

        if op == "int":
            self._translate_int(constraint)
        elif op == "real":
            self._translate_real(constraint)
        elif op in ("<=", "<", ">=", ">", "==", "!="):
            self._translate_comparison(constraint)
        elif op == "+":
            pass
        elif op == "sum":
            pass
        elif op == "alldifferent":
            self._translate_alldifferent(constraint)
        elif op == "minimize":
            self._translate_objective(constraint, minimize=True)
        elif op == "maximize":
            self._translate_objective(constraint, minimize=False)

    def _translate_int(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = self.model.addVar(lb=lb, ub=ub, vtype=GRB.INTEGER, name=name)
        self.vars[name] = var

    def _translate_real(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = self.model.addVar(lb=lb, ub=ub, vtype=GRB.CONTINUOUS, name=name)
        self.vars[name] = var

    def _translate_comparison(self, constraint: list) -> None:
        op, lhs, rhs = constraint
        lhs_expr = self._to_expr(lhs)
        rhs_expr = self._to_expr(rhs)

        if op == "<=":
            self.model.addConstr(lhs_expr <= rhs_expr)
        elif op == "<":
            self.model.addConstr(lhs_expr <= rhs_expr - 1)
        elif op == ">=":
            self.model.addConstr(lhs_expr >= rhs_expr)
        elif op == ">":
            self.model.addConstr(lhs_expr >= rhs_expr + 1)
        elif op == "==":
            self.model.addConstr(lhs_expr == rhs_expr)
        elif op == "!=":
            self._translate_ne(lhs_expr, rhs_expr)

    def _translate_ne(self, lhs_expr, rhs_expr):
        M = 1000000
        b = self.model.addVar(vtype=GRB.BINARY)
        self.model.addConstr(lhs_expr - rhs_expr >= 1 - M * (1 - b))
        self.model.addConstr(lhs_expr - rhs_expr <= -1 + M * b)

    def _translate_alldifferent(self, constraint: list) -> None:
        var_names = constraint[1:]
        vars_list = [self.vars[name] for name in var_names]
        n = len(vars_list)
        for i in range(n):
            for j in range(i + 1, n):
                self._translate_ne(vars_list[i], vars_list[j])

    def _translate_objective(self, constraint: list, minimize: bool) -> None:
        _, expr = constraint
        obj_expr = self._to_expr(expr)
        if minimize:
            self.model.setObjective(obj_expr, GRB.MINIMIZE)
        else:
            self.model.setObjective(obj_expr, GRB.MAXIMIZE)

    def _to_expr(self, term: Any):
        if isinstance(term, (int, float)):
            return term
        elif isinstance(term, str):
            return self.vars[term]
        elif isinstance(term, list):
            op = term[0]
            if op == "+":
                return gp.quicksum(self._to_expr(arg) for arg in term[1:])
            elif op == "sum":
                return self._to_sum_expr(term)
            else:
                raise ValueError(f"Unsupported expression operator: {op}")
        else:
            raise ValueError(f"Unsupported term type: {type(term)}")

    def _to_sum_expr(self, term: list):
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

        if self.model.Status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            result = {}
            for name, var in self.vars.items():
                val = var.X
                if var.VType == GRB.INTEGER:
                    result[name] = int(round(val))
                else:
                    result[name] = val
            return result
        else:
            raise RuntimeError(f"No solution found. Status: {self.model.Status}")
