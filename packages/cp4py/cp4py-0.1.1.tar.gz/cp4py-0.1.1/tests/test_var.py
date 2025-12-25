from cp4py import Var


def test_var_no_indices():
    x = Var("x")
    assert x() == "x"


def test_var_single_index():
    x = Var("x")
    assert x(0) == "x_0"
    assert x(1) == "x_1"


def test_var_multiple_indices():
    x = Var("x")
    assert x(0, 1) == "x_0_1"
    assert x(2, 3, 4) == "x_2_3_4"


def test_var_name():
    x = Var("x")
    assert x.name == "x"
    y = Var("cost")
    assert y.name == "cost"


def test_var_default_bounds():
    x = Var("x")
    assert x.lb is None
    assert x.ub is None


def test_var_with_bounds():
    x = Var("x", lb=0, ub=100)
    assert x.lb == 0
    assert x.ub == 100


def test_var_with_partial_bounds():
    x = Var("x", lb=0)
    assert x.lb == 0
    assert x.ub is None
    y = Var("y", ub=10)
    assert y.lb is None
    assert y.ub == 10
