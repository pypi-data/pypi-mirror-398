import pytest
from cp4py import Var
from cp4py.translators.ortools import ORToolsTranslator, UnsupportedConstraintError


class TestORToolsBasic:
    def test_int_variable(self):
        def model():
            yield ["int", "x", 1, 10]

        translator = ORToolsTranslator()
        translator.translate(model())
        assert "x" in translator.vars

    def test_solve_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["==", "x", 5]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5


class TestORToolsComparison:
    def test_le(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 3]
            yield [">=", "x", 3]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3

    def test_lt_gt(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<", "x", 5]
            yield [">", "x", 3]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 4

    def test_ne(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["!=", "x", 1]
            yield ["!=", "x", 3]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2


class TestORToolsArithmetic:
    def test_add(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["+", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3
        assert result["y"] == 4

    def test_sum_simple(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["sum", "x", "y"], 7]
            yield ["==", "x", 3]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3
        assert result["y"] == 4

    def test_sum_with_coefficients(self):
        # 2*x + 3*y = 13, x = 2 => y = 3
        def model():
            yield ["int", "x", 1, 10]
            yield ["int", "y", 1, 10]
            yield ["==", ["sum", [2, "x"], [3, "y"]], 13]
            yield ["==", "x", 2]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 2
        assert result["y"] == 3


class TestORToolsLogical:
    def test_or(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["or", ["==", "x", 3], ["==", "x", 7]]
            yield ["<", "x", 5]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 3

    def test_and(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["and", [">=", "x", 3], ["<=", "x", 5]]
            yield ["==", "x", 4]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 4


class TestORToolsAlldifferent:
    def test_alldifferent(self):
        def model():
            yield ["int", "x", 1, 3]
            yield ["int", "y", 1, 3]
            yield ["int", "z", 1, 3]
            yield ["alldifferent", "x", "y", "z"]
            yield ["==", "x", 1]
            yield ["==", "y", 2]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3


class TestORToolsObjective:
    def test_minimize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield [">=", "x", 5]
            yield ["minimize", "x"]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 5

    def test_maximize(self):
        def model():
            yield ["int", "x", 1, 10]
            yield ["<=", "x", 7]
            yield ["maximize", "x"]

        translator = ORToolsTranslator()
        translator.translate(model())
        result = translator.solve()
        assert result["x"] == 7


class TestORToolsUnsupported:
    def test_real_variable_raises_error(self):
        def model():
            yield ["real", "x", 0.0, 1.0]

        translator = ORToolsTranslator()
        with pytest.raises(UnsupportedConstraintError) as exc_info:
            translator.translate(model())

        assert "real" in str(exc_info.value).lower()
        assert "OR-Tools" in str(exc_info.value) or "ortools" in str(exc_info.value).lower()

    def test_real_error_message_suggests_alternatives(self):
        def model():
            yield ["real", "x", 0.0, 1.0]

        translator = ORToolsTranslator()
        with pytest.raises(UnsupportedConstraintError) as exc_info:
            translator.translate(model())

        error_msg = str(exc_info.value)
        assert "Z3" in error_msg or "SCIP" in error_msg


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

        translator = ORToolsTranslator()
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
