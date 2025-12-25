import pytest
from cp4py.core.expr import validate


class TestValidateInt:
    def test_int_valid(self):
        assert validate(["int", "x", 1, 9]) is True

    def test_int_missing_args(self):
        with pytest.raises(ValueError):
            validate(["int", "x", 1])

    def test_int_invalid_bounds(self):
        with pytest.raises(ValueError):
            validate(["int", "x", 9, 1])  # lower > upper


class TestValidateReal:
    def test_real_valid(self):
        assert validate(["real", "x", 0.0, 1.0]) is True

    def test_real_missing_args(self):
        with pytest.raises(ValueError):
            validate(["real", "x", 0.0])

    def test_real_invalid_bounds(self):
        with pytest.raises(ValueError):
            validate(["real", "x", 1.0, 0.0])  # lower > upper


class TestValidateComparison:
    def test_le(self):
        assert validate(["<=", "x", 5]) is True

    def test_lt(self):
        assert validate(["<", "x", 5]) is True

    def test_ge(self):
        assert validate([">=", "x", 5]) is True

    def test_gt(self):
        assert validate([">", "x", 5]) is True

    def test_eq(self):
        assert validate(["==", "x", 5]) is True

    def test_ne(self):
        assert validate(["!=", "x", 5]) is True


class TestValidateArithmetic:
    def test_add(self):
        assert validate(["+", "x", "y", "z"]) is True

    def test_add_nested(self):
        assert validate(["==", ["+", "x", "y"], 10]) is True


class TestValidateSum:
    def test_sum_simple(self):
        # ["sum", "x", "y", "z"] = x + y + z
        assert validate(["sum", "x", "y", "z"]) is True

    def test_sum_with_coefficients(self):
        # ["sum", [2, "x"], [3, "y"], "z"] = 2*x + 3*y + z
        assert validate(["sum", [2, "x"], [3, "y"], "z"]) is True

    def test_sum_nested(self):
        assert validate(["==", ["sum", [2, "x"], [3, "y"]], 10]) is True

    def test_sum_empty(self):
        with pytest.raises(ValueError):
            validate(["sum"])


class TestValidateLogical:
    def test_or(self):
        assert validate(["or", ["<=", "x", 5], [">=", "x", 10]]) is True

    def test_and(self):
        assert validate(["and", [">=", "x", 0], ["<=", "x", 10]]) is True

    def test_nested_logical(self):
        expr = ["or",
                ["and", [">=", "x", 0], ["<=", "x", 5]],
                ["and", [">=", "x", 10], ["<=", "x", 15]]]
        assert validate(expr) is True


class TestValidateAlldifferent:
    def test_alldifferent(self):
        assert validate(["alldifferent", "x", "y", "z"]) is True

    def test_alldifferent_empty(self):
        with pytest.raises(ValueError):
            validate(["alldifferent"])


class TestValidateObjective:
    def test_minimize(self):
        assert validate(["minimize", "x"]) is True

    def test_maximize(self):
        assert validate(["maximize", ["+", "x", "y"]]) is True

    def test_minimize_missing_arg(self):
        with pytest.raises(ValueError):
            validate(["minimize"])


class TestValidateUnknown:
    def test_unknown_operator(self):
        with pytest.raises(ValueError):
            validate(["unknown", "x"])

    def test_empty_list(self):
        with pytest.raises(ValueError):
            validate([])
