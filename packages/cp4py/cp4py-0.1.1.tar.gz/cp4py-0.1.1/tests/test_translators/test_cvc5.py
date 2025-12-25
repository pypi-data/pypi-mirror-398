import pytest
from cp4py import Var
from cp4py.translators.cvc5 import CVC5Translator


class TestCVC5Basic:
    def test_int_variable(self):
        def model():
            yield ["int", "x", 1, 10]

        translator = CVC5Translator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_solve_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["==", "x", 5]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5


class TestCVC5Real:
    def test_real_variable(self):
        def model():
            yield ["real", "x", 0.0, 1.0]

        translator = CVC5Translator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_real_solve(self):
        def model():
            yield ["real", "x", 0.0, 10.0]
            yield ["==", "x", 3.5]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert abs(result["x"] - 3.5) < 0.001

    def test_real_constraints(self):
        def model():
            yield ["real", "x", 0.0, 10.0]
            yield [">=", "x", 2.5]
            yield ["<=", "x", 3.5]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert 2.5 <= result["x"] <= 3.5


class TestCVC5Comparison:
    def test_le(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 3]
            yield [">=", "x", 3]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3

    def test_lt_gt(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<", "x", 5]
            yield [">", "x", 3]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 4

    def test_ne(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["!=", "x", 1]
            yield ["!=", "x", 3]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2


class TestCVC5Arithmetic:
    def test_add(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["+", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3
        assert result["y"] == 4


class TestCVC5Sum:
    def test_sum_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["sum", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = CVC5Translator()
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

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2
        assert result["y"] == 3


class TestCVC5Logical:
    def test_or(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["or", ["==", "x", 3], ["==", "x", 7]]
            yield ["<", "x", 5]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3

    def test_and(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["and", [">=", "x", 3], ["<=", "x", 5]]
            yield ["==", "x", 4]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 4


class TestCVC5Alldifferent:
    def test_alldifferent(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["int", "y", 1, 3]
            yield ["int", "z", 1, 3]
            yield ["alldifferent", "x", "y", "z"]
            yield ["==", "x", 1]
            yield ["==", "y", 2]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3


class TestCVC5Objective:
    def test_minimize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield [">=", "x", 5]
            yield ["minimize", "x"]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5

    def test_maximize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 7]
            yield ["maximize", "x"]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 7

    def test_maximize_sum(self):
        def model():
            yield ["int", "x", 0, 5]
            yield ["int", "y", 0, 5]
            yield ["<=", ["+", "x", "y"], 7]
            yield ["maximize", ["sum", [2, "x"], [3, "y"]]]

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()
        # Maximize 2x + 3y subject to x + y <= 7
        # Optimal: x=0, y=5 gives 2*0 + 3*5 = 15
        # or x=2, y=5 gives 2*2 + 3*5 = 19 but x+y=7
        assert result["x"] + result["y"] <= 7
        assert 2 * result["x"] + 3 * result["y"] >= 19


class TestCVC5MagicSquare:
    def test_magic_square_3x3(self):
        def magicSquare3x3(x=Var("x")):
            for i in range(3):
                for j in range(3):
                    yield ["int", x(i, j), 1, 9]
            xx = [x(i, j) for i in range(3) for j in range(3)]
            yield ["alldifferent", *xx]
            for i in range(3):
                yield ["==", ["+", x(i, 0), x(i, 1), x(i, 2)], 15]
            for j in range(3):
                yield ["==", ["+", x(0, j), x(1, j), x(2, j)], 15]
            yield ["==", ["+", x(0, 0), x(1, 1), x(2, 2)], 15]
            yield ["==", ["+", x(0, 2), x(1, 1), x(2, 0)], 15]

        translator = CVC5Translator()
        translator.translate(magicSquare3x3())
        result = translator.solve()

        # Check all values are 1-9 and unique
        values = [result[f"x_{i}_{j}"] for i in range(3) for j in range(3)]
        assert sorted(values) == list(range(1, 10))

        # Check row sums
        for i in range(3):
            assert sum(result[f"x_{i}_{j}"] for j in range(3)) == 15

        # Check column sums
        for j in range(3):
            assert sum(result[f"x_{i}_{j}"] for i in range(3)) == 15

        # Check diagonal sums
        assert sum(result[f"x_{i}_{i}"] for i in range(3)) == 15
        assert sum(result[f"x_{i}_{2-i}"] for i in range(3)) == 15


class TestCVC5Knapsack:
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

        translator = CVC5Translator()
        translator.translate(model())
        result = translator.solve()

        selected = [i for i in range(n) if result[x(i)] == 1]
        total_weight = sum(weights[i] for i in selected)
        total_value = sum(values[i] for i in selected)

        assert total_weight <= capacity
        assert total_value == 15  # Optimal: items 0,1,3 = 3 + 4 + 8 = 15
