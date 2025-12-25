import pytest
from cp4py import Var
from cp4py.translators.scip import SCIPTranslator


class TestSCIPBasic:
    def test_int_variable(self):
        def model():
            yield ["int", "x", 1, 10]

        translator = SCIPTranslator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_solve_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["==", "x", 5]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5


class TestSCIPReal:
    def test_real_variable(self):
        def model():
            yield ["real", "x", 0.0, 1.0]

        translator = SCIPTranslator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_real_solve(self):
        def model():
            yield ["real", "x", 0.0, 10.0]
            yield ["==", "x", 3.5]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert abs(result["x"] - 3.5) < 0.001

    def test_real_constraints(self):
        def model():
            yield ["real", "x", 0.0, 10.0]
            yield [">=", "x", 2.5]
            yield ["<=", "x", 3.5]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert 2.5 <= result["x"] <= 3.5


class TestSCIPComparison:
    def test_le(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 3]
            yield [">=", "x", 3]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3

    def test_lt_gt(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<", "x", 5]
            yield [">", "x", 3]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 4

    def test_ne(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["!=", "x", 1]
            yield ["!=", "x", 3]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2


class TestSCIPArithmetic:
    def test_add(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["+", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3
        assert result["y"] == 4


class TestSCIPObjective:
    def test_minimize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield [">=", "x", 5]
            yield ["minimize", "x"]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5

    def test_maximize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 7]
            yield ["maximize", "x"]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 7


class TestSCIPAlldifferent:
    def test_alldifferent(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["int", "y", 1, 3]
            yield ["int", "z", 1, 3]
            yield ["alldifferent", "x", "y", "z"]
            yield ["==", "x", 1]
            yield ["==", "y", 2]

        translator = SCIPTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3


class TestMagicSquare:
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

        translator = SCIPTranslator()
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
