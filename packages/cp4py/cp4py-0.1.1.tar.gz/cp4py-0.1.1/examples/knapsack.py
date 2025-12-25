import argparse

from cp4py import Var


def get_translator(solver: str):
    if solver == "ortools":
        from cp4py.translators.ortools import ORToolsTranslator
        return ORToolsTranslator()
    elif solver == "z3":
        from cp4py.translators.z3 import Z3Translator
        return Z3Translator()
    elif solver == "scip":
        from cp4py.translators.scip import SCIPTranslator
        return SCIPTranslator()
    elif solver == "cvc5":
        from cp4py.translators.cvc5 import CVC5Translator
        return CVC5Translator()
    elif solver == "gurobi":
        from cp4py.translators.gurobi import GurobiTranslator
        return GurobiTranslator()
    elif solver == "cplex":
        from cp4py.translators.cplex import CPLEXTranslator
        return CPLEXTranslator()
    elif solver == "cpoptimizer":
        from cp4py.translators.cpoptimizer import CPOptimizerTranslator
        return CPOptimizerTranslator()
    else:
        raise ValueError(f"Unknown solver: {solver}")


def knapsack(weights, values, capacity, solver="ortools"):
    """
    0-1 Knapsack Problem

    Args:
        weights: list of item weights
        values: list of item values
        capacity: maximum weight capacity
        solver: "ortools", "z3", or "scip"

    Returns:
        dict with selected items, total weight, and total value
    """
    n = len(weights)
    x = Var("x")

    def model():
        # Binary variables: x[i] = 1 if item i is selected
        for i in range(n):
            yield ["int", x(i), 0, 1]

        # Weight constraint: sum(w[i] * x[i]) <= capacity
        yield ["<=", ["sum"] + [[weights[i], x(i)] for i in range(n)], capacity]

        # Maximize value: sum(v[i] * x[i])
        yield ["maximize", ["sum"] + [[values[i], x(i)] for i in range(n)]]

    translator = get_translator(solver)
    translator.translate(model())
    result = translator.solve()

    selected = [i for i in range(n) if result[x(i)] == 1]
    return {
        "selected": selected,
        "total_weight": sum(weights[i] for i in selected),
        "total_value": sum(values[i] for i in selected),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="0-1 Knapsack Problem")
    parser.add_argument("-ortools", action="store_const", const="ortools", dest="solver")
    parser.add_argument("-z3", action="store_const", const="z3", dest="solver")
    parser.add_argument("-scip", action="store_const", const="scip", dest="solver")
    parser.add_argument("-cvc5", action="store_const", const="cvc5", dest="solver")
    parser.add_argument("-gurobi", action="store_const", const="gurobi", dest="solver")
    parser.add_argument("-cplex", action="store_const", const="cplex", dest="solver")
    parser.add_argument("-cpoptimizer", action="store_const", const="cpoptimizer", dest="solver")
    parser.set_defaults(solver="ortools")
    args = parser.parse_args()

    weights = [2, 3, 4, 5, 9]
    values = [3, 4, 5, 8, 10]
    capacity = 10

    print(f"Solver: {args.solver}")
    result = knapsack(weights, values, capacity, solver=args.solver)

    print(f"Selected items: {result['selected']}")
    print(f"Total weight: {result['total_weight']}")
    print(f"Total value: {result['total_value']}")
