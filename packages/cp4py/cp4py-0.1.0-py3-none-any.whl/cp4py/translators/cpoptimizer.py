from typing import Any, Iterable

from docplex.cp.model import CpoModel

from cp4py.translators.base import BaseTranslator


class CPOptimizerTranslator(BaseTranslator):
    def __init__(self):
        self.model = CpoModel()
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
            pass
        elif op == "sum":
            pass
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
        var = self.model.integer_var(min=lb, max=ub, name=name)
        self.vars[name] = var

    def _translate_real(self, constraint: list) -> None:
        # CP Optimizer doesn't have continuous variables, use scaled integers
        # or raise an error
        raise NotImplementedError(
            "CP Optimizer does not support real variables. "
            "Use Z3, SCIP, or Gurobi instead."
        )

    def _translate_comparison(self, constraint: list) -> None:
        op, lhs, rhs = constraint
        lhs_expr = self._to_expr(lhs)
        rhs_expr = self._to_expr(rhs)

        if op == "<=":
            self.model.add(lhs_expr <= rhs_expr)
        elif op == "<":
            self.model.add(lhs_expr < rhs_expr)
        elif op == ">=":
            self.model.add(lhs_expr >= rhs_expr)
        elif op == ">":
            self.model.add(lhs_expr > rhs_expr)
        elif op == "==":
            self.model.add(lhs_expr == rhs_expr)
        elif op == "!=":
            self.model.add(lhs_expr != rhs_expr)

    def _translate_or(self, constraint: list) -> None:
        from docplex.cp.expression import CpoFunctionCall
        sub_constraints = [self._to_constraint_expr(sub) for sub in constraint[1:]]
        # Use logical_or
        result = sub_constraints[0]
        for c in sub_constraints[1:]:
            result = self.model.logical_or(result, c)
        self.model.add(result)

    def _translate_and(self, constraint: list) -> None:
        for sub in constraint[1:]:
            self._translate_constraint(sub)

    def _translate_alldifferent(self, constraint: list) -> None:
        vars_list = [self.vars[name] for name in constraint[1:]]
        self.model.add(self.model.all_diff(vars_list))

    def _translate_objective(self, constraint: list, minimize: bool) -> None:
        _, expr = constraint
        obj_expr = self._to_expr(expr)
        if minimize:
            self.model.minimize(obj_expr)
        else:
            self.model.maximize(obj_expr)

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
        result = 0
        for t in term[1:]:
            if isinstance(t, list) and len(t) == 2:
                coeff, var = t
                result += coeff * self._to_expr(var)
            else:
                result += self._to_expr(t)
        return result

    def _to_constraint_expr(self, constraint: list):
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
            sub_constraints = [self._to_constraint_expr(sub) for sub in constraint[1:]]
            result = sub_constraints[0]
            for c in sub_constraints[1:]:
                result = self.model.logical_or(result, c)
            return result
        elif op == "and":
            sub_constraints = [self._to_constraint_expr(sub) for sub in constraint[1:]]
            result = sub_constraints[0]
            for c in sub_constraints[1:]:
                result = self.model.logical_and(result, c)
            return result
        else:
            raise ValueError(f"Unsupported constraint operator: {op}")

    def solve(self) -> dict[str, Any]:
        solution = self.model.solve(LogVerbosity="Quiet")

        if solution:
            result = {}
            for name, var in self.vars.items():
                result[name] = solution.get_value(var)
            return result
        else:
            raise RuntimeError("No solution found")
