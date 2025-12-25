from fractions import Fraction
from typing import Any, Iterable

import cvc5
from cvc5 import Kind

from cp4py.translators.base import BaseTranslator


class CVC5Translator(BaseTranslator):
    def __init__(self):
        self.solver = cvc5.Solver()
        self.solver.setOption("produce-models", "true")
        self.solver.setLogic("QF_LIRA")  # Quantifier-free linear integer/real arithmetic
        self.vars: dict[str, Any] = {}
        self.int_sort = self.solver.getIntegerSort()
        self.real_sort = self.solver.getRealSort()
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
        var = self.solver.mkConst(self.int_sort, name)
        self.vars[name] = var
        lb_term = self.solver.mkInteger(lb)
        ub_term = self.solver.mkInteger(ub)
        self.solver.assertFormula(self.solver.mkTerm(Kind.GEQ, var, lb_term))
        self.solver.assertFormula(self.solver.mkTerm(Kind.LEQ, var, ub_term))

    def _translate_real(self, constraint: list) -> None:
        _, name, lb, ub = constraint
        var = self.solver.mkConst(self.real_sort, name)
        self.vars[name] = var
        lb_term = self.solver.mkReal(str(lb))
        ub_term = self.solver.mkReal(str(ub))
        self.solver.assertFormula(self.solver.mkTerm(Kind.GEQ, var, lb_term))
        self.solver.assertFormula(self.solver.mkTerm(Kind.LEQ, var, ub_term))

    def _translate_comparison(self, constraint: list) -> None:
        op, lhs, rhs = constraint
        lhs_expr = self._to_expr(lhs)
        rhs_expr = self._to_expr(rhs)

        kind_map = {
            "<=": Kind.LEQ,
            "<": Kind.LT,
            ">=": Kind.GEQ,
            ">": Kind.GT,
            "==": Kind.EQUAL,
            "!=": Kind.DISTINCT,
        }
        self.solver.assertFormula(self.solver.mkTerm(kind_map[op], lhs_expr, rhs_expr))

    def _translate_or(self, constraint: list) -> None:
        sub_terms = [self._to_constraint_term(sub) for sub in constraint[1:]]
        self.solver.assertFormula(self.solver.mkTerm(Kind.OR, *sub_terms))

    def _translate_and(self, constraint: list) -> None:
        for sub in constraint[1:]:
            self._translate_constraint(sub)

    def _translate_alldifferent(self, constraint: list) -> None:
        vars_list = [self.vars[name] for name in constraint[1:]]
        self.solver.assertFormula(self.solver.mkTerm(Kind.DISTINCT, *vars_list))

    def _translate_objective(self, constraint: list, minimize: bool) -> None:
        _, expr = constraint
        self.objective = self._to_expr(expr)
        self.objective_type = "minimize" if minimize else "maximize"

    def _to_expr(self, term: Any):
        if isinstance(term, int):
            return self.solver.mkInteger(term)
        elif isinstance(term, float):
            return self.solver.mkReal(str(term))
        elif isinstance(term, str):
            return self.vars[term]
        elif isinstance(term, list):
            op = term[0]
            if op == "+":
                args = [self._to_expr(arg) for arg in term[1:]]
                return self.solver.mkTerm(Kind.ADD, *args)
            elif op == "sum":
                return self._to_sum_expr(term)
            else:
                raise ValueError(f"Unsupported expression operator: {op}")
        else:
            raise ValueError(f"Unsupported term type: {type(term)}")

    def _to_sum_expr(self, term: list):
        args = []
        for t in term[1:]:
            if isinstance(t, list) and len(t) == 2:
                coeff, var = t
                coeff_term = self.solver.mkInteger(coeff) if isinstance(coeff, int) else self.solver.mkReal(str(coeff))
                var_term = self._to_expr(var)
                args.append(self.solver.mkTerm(Kind.MULT, coeff_term, var_term))
            else:
                args.append(self._to_expr(t))
        return self.solver.mkTerm(Kind.ADD, *args)

    def _to_constraint_term(self, constraint: list):
        op = constraint[0]
        if op in ("<=", "<", ">=", ">", "==", "!="):
            lhs_expr = self._to_expr(constraint[1])
            rhs_expr = self._to_expr(constraint[2])
            kind_map = {
                "<=": Kind.LEQ,
                "<": Kind.LT,
                ">=": Kind.GEQ,
                ">": Kind.GT,
                "==": Kind.EQUAL,
                "!=": Kind.DISTINCT,
            }
            return self.solver.mkTerm(kind_map[op], lhs_expr, rhs_expr)
        elif op == "or":
            sub_terms = [self._to_constraint_term(sub) for sub in constraint[1:]]
            return self.solver.mkTerm(Kind.OR, *sub_terms)
        elif op == "and":
            sub_terms = [self._to_constraint_term(sub) for sub in constraint[1:]]
            return self.solver.mkTerm(Kind.AND, *sub_terms)
        else:
            raise ValueError(f"Unsupported constraint operator: {op}")

    def solve(self) -> dict[str, Any]:
        if self.objective is not None:
            # Binary search for optimization
            result = self._optimize()
        else:
            if self.solver.checkSat().isSat():
                result = self._extract_solution()
            else:
                raise RuntimeError("No solution found")
        return result

    def _optimize(self) -> dict[str, Any]:
        # Simple optimization via iterative improvement
        if not self.solver.checkSat().isSat():
            raise RuntimeError("No solution found")

        best = self._extract_solution()
        best_obj_val = self._eval_objective(best)

        # Iteratively improve
        for _ in range(1000):
            if self.objective_type == "minimize":
                bound = self.solver.mkTerm(Kind.LT, self.objective,
                    self.solver.mkInteger(best_obj_val) if isinstance(best_obj_val, int) else self.solver.mkReal(str(best_obj_val)))
            else:
                bound = self.solver.mkTerm(Kind.GT, self.objective,
                    self.solver.mkInteger(best_obj_val) if isinstance(best_obj_val, int) else self.solver.mkReal(str(best_obj_val)))

            self.solver.push()
            self.solver.assertFormula(bound)
            if self.solver.checkSat().isSat():
                best = self._extract_solution()
                best_obj_val = self._eval_objective(best)
                self.solver.pop()
            else:
                self.solver.pop()
                break

        return best

    def _eval_objective(self, solution: dict) -> Any:
        """Evaluate objective value from solution."""
        val = self.solver.getValue(self.objective)
        if val.isIntegerValue():
            return val.getIntegerValue()
        elif val.isRealValue():
            frac = val.getRealValue()
            return float(Fraction(frac.numerator, frac.denominator))
        else:
            return float(str(val))

    def _extract_solution(self) -> dict[str, Any]:
        result = {}
        for name, var in self.vars.items():
            val = self.solver.getValue(var)
            if val.isIntegerValue():
                result[name] = val.getIntegerValue()
            elif val.isRealValue():
                frac = val.getRealValue()
                result[name] = float(Fraction(frac.numerator, frac.denominator))
            else:
                result[name] = float(str(val))
        return result
