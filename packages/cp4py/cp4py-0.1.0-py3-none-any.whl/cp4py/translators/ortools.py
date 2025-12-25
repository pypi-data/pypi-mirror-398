from typing import Any, Iterable

from ortools.sat.python import cp_model

from cp4py.translators.base import BaseTranslator


class UnsupportedConstraintError(Exception):
    """Raised when a constraint is not supported by the translator."""
    pass


class ORToolsTranslator(BaseTranslator):
    def __init__(self):
        self.model = cp_model.CpModel()
        self.vars: dict[str, cp_model.IntVar] = {}
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
            raise UnsupportedConstraintError(
                "OR-Tools CP-SAT does not support real variables. "
                "Use Z3 or SCIP translator instead."
            )
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
        self.vars[name] = self.model.NewIntVar(lb, ub, name)

    def _translate_comparison(self, constraint: list) -> None:
        op, lhs, rhs = constraint
        lhs_expr = self._to_expr(lhs)
        rhs_expr = self._to_expr(rhs)

        if op == "<=":
            self.model.Add(lhs_expr <= rhs_expr)
        elif op == "<":
            self.model.Add(lhs_expr < rhs_expr)
        elif op == ">=":
            self.model.Add(lhs_expr >= rhs_expr)
        elif op == ">":
            self.model.Add(lhs_expr > rhs_expr)
        elif op == "==":
            self.model.Add(lhs_expr == rhs_expr)
        elif op == "!=":
            self.model.Add(lhs_expr != rhs_expr)

    def _translate_or(self, constraint: list) -> None:
        # ["or", expr1, expr2, ...]
        bool_vars = []
        for sub in constraint[1:]:
            b = self.model.NewBoolVar("")
            bool_vars.append(b)
            self._add_reified_constraint(sub, b)
        self.model.AddBoolOr(bool_vars)

    def _translate_and(self, constraint: list) -> None:
        # ["and", expr1, expr2, ...]
        for sub in constraint[1:]:
            self._translate_constraint(sub)

    def _translate_alldifferent(self, constraint: list) -> None:
        # ["alldifferent", var1, var2, ...]
        vars_list = [self.vars[name] for name in constraint[1:]]
        self.model.AddAllDifferent(vars_list)

    def _translate_objective(self, constraint: list, minimize: bool) -> None:
        _, expr = constraint
        obj_expr = self._to_expr(expr)
        if minimize:
            self.model.Minimize(obj_expr)
        else:
            self.model.Maximize(obj_expr)

    def _to_expr(self, term: Any):
        if isinstance(term, int):
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

    def _add_reified_constraint(self, constraint: list, bool_var) -> None:
        op = constraint[0]
        if op in ("<=", "<", ">=", ">", "==", "!="):
            lhs_expr = self._to_expr(constraint[1])
            rhs_expr = self._to_expr(constraint[2])

            if op == "<=":
                self.model.Add(lhs_expr <= rhs_expr).OnlyEnforceIf(bool_var)
            elif op == "<":
                self.model.Add(lhs_expr < rhs_expr).OnlyEnforceIf(bool_var)
            elif op == ">=":
                self.model.Add(lhs_expr >= rhs_expr).OnlyEnforceIf(bool_var)
            elif op == ">":
                self.model.Add(lhs_expr > rhs_expr).OnlyEnforceIf(bool_var)
            elif op == "==":
                self.model.Add(lhs_expr == rhs_expr).OnlyEnforceIf(bool_var)
            elif op == "!=":
                self.model.Add(lhs_expr != rhs_expr).OnlyEnforceIf(bool_var)
        else:
            raise ValueError(f"Unsupported reified constraint: {op}")

    def solve(self) -> dict[str, Any]:
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {name: solver.Value(var) for name, var in self.vars.items()}
        else:
            raise RuntimeError(f"No solution found. Status: {status}")
