import pytest
from cp4py import Var
from cp4py.translators.cplex import CPLEXTranslator


class TestCPLEXBasic:
    def test_int_variable(self):
        def model():
            yield ["int", "x", 1, 10]

        translator = CPLEXTranslator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_solve_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["==", "x", 5]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5


class TestCPLEXReal:
    def test_real_variable(self):
        def model():
            yield ["real", "x", 0.0, 1.0]

        translator = CPLEXTranslator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_real_solve(self):
        def model():
            yield ["real", "x", 0.0, 10.0]
            yield ["==", "x", 3.5]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert abs(result["x"] - 3.5) < 0.001

    def test_real_constraints(self):
        def model():
            yield ["real", "x", 0.0, 10.0]
            yield [">=", "x", 2.5]
            yield ["<=", "x", 3.5]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert 2.5 <= result["x"] <= 3.5


class TestCPLEXComparison:
    def test_le(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 3]
            yield [">=", "x", 3]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3

    def test_lt_gt(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<", "x", 5]
            yield [">", "x", 3]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 4

    def test_ne(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["!=", "x", 1]
            yield ["!=", "x", 3]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2


class TestCPLEXArithmetic:
    def test_add(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["+", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3
        assert result["y"] == 4


class TestCPLEXSum:
    def test_sum_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["sum", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3
        assert result["y"] == 4

    def test_sum_with_coefficients(self):
        def model():
            yield ["int", "x", 0, 10]
            yield ["int", "y", 0, 10]
            yield ["==", ["sum", [2, "x"], [3, "y"]], 13]
            yield ["==", "x", 2]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2
        assert result["y"] == 3


class TestCPLEXAlldifferent:
    def test_alldifferent(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["int", "y", 1, 3]
            yield ["int", "z", 1, 3]
            yield ["alldifferent", "x", "y", "z"]
            yield ["==", "x", 1]
            yield ["==", "y", 2]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3


class TestCPLEXObjective:
    def test_minimize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield [">=", "x", 5]
            yield ["minimize", "x"]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5

    def test_maximize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 7]
            yield ["maximize", "x"]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 7

    def test_maximize_sum(self):
        def model():
            yield ["int", "x", 0, 5]
            yield ["int", "y", 0, 5]
            yield ["<=", ["+", "x", "y"], 7]
            yield ["maximize", ["sum", [2, "x"], [3, "y"]]]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()
        # Maximize 2x + 3y subject to x + y <= 7
        assert result["x"] + result["y"] <= 7
        assert 2 * result["x"] + 3 * result["y"] >= 19


class TestCPLEXKnapsack:
    def test_knapsack(self):
        weights = [2, 3, 4, 5, 9]
        values = [3, 4, 5, 8, 10]
        capacity = 10
        n = len(weights)
        x = Var("x")

        def model():
            for i in range(n):
                yield ["int", x(i), 0, 1]
            yield ["<=", ["sum"] + [[weights[i], x(i)] for i in range(n)], capacity]
            yield ["maximize", ["sum"] + [[values[i], x(i)] for i in range(n)]]

        translator = CPLEXTranslator()
        translator.translate(model())
        result = translator.solve()

        selected = [i for i in range(n) if result[x(i)] == 1]
        total_weight = sum(weights[i] for i in selected)
        total_value = sum(values[i] for i in selected)

        assert total_weight <= capacity
        assert total_value == 15  # Optimal: items 0,1,3 = 3 + 4 + 8 = 15
