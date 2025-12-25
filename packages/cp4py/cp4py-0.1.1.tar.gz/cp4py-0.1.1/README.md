# cp4py

Constraint Programming language and translator for Python.

## Overview

cp4py provides a unified DSL (Domain Specific Language) for constraint programming that can be translated to multiple backend solvers.

## Installation

```bash
pip install cp4py

# With specific solver backends
pip install cp4py[ortools]
pip install cp4py[z3]
pip install cp4py[scip]
pip install cp4py[cvc5]
pip install cp4py[gurobi]
pip install cp4py[cplex]
pip install cp4py[cpoptimizer]
```

## Supported Solvers

| Solver | Variable Types | License |
|--------|---------------|---------|
| OR-Tools | int | Free |
| Z3 | int, real | Free |
| SCIP | int, real | Free |
| CVC5 | int, real | Free |
| Gurobi | int, real | Commercial |
| CPLEX | int, real | Commercial |
| CP Optimizer | int | Commercial |

## Language Syntax

cp4py uses prefix notation with Python lists:

### Variable Declaration

```python
["int", "x", 1, 9]        # Integer variable x in [1, 9]
["real", "x", 0.0, 1.0]   # Real variable x in [0.0, 1.0]
```

### Comparison Operators

```python
["<=", "x", 5]    # x <= 5
["<", "x", 5]     # x < 5
[">=", "x", 5]    # x >= 5
[">", "x", 5]     # x > 5
["==", "x", 5]    # x == 5
["!=", "x", 5]    # x != 5
```

### Arithmetic

```python
["+", "x", "y", "z"]              # x + y + z
["sum", "x", "y", "z"]            # x + y + z (same as +)
["sum", [2, "x"], [3, "y"], "z"]  # 2*x + 3*y + z
```

### Logical Operators

```python
["or", ["<=", "x", 5], [">=", "x", 10]]   # x <= 5 OR x >= 10
["and", [">=", "x", 0], ["<=", "x", 10]]  # x >= 0 AND x <= 10
```

### Global Constraints

```python
["alldifferent", "x", "y", "z"]  # x, y, z are all different
```

### Objective Functions

```python
["minimize", "x"]                      # Minimize x
["maximize", ["sum", [2, "x"], "y"]]   # Maximize 2*x + y
```

## Usage

### Basic Example: Magic Square

```python
from cp4py import Var
from cp4py.translators.ortools import ORToolsTranslator

def magic_square_3x3():
    x = Var("x")

    def model():
        # Variables: 9 cells with values 1-9
        for i in range(3):
            for j in range(3):
                yield ["int", x(i, j), 1, 9]

        # All different
        yield ["alldifferent"] + [x(i, j) for i in range(3) for j in range(3)]

        # Row sums = 15
        for i in range(3):
            yield ["==", ["+", x(i, 0), x(i, 1), x(i, 2)], 15]

        # Column sums = 15
        for j in range(3):
            yield ["==", ["+", x(0, j), x(1, j), x(2, j)], 15]

        # Diagonal sums = 15
        yield ["==", ["+", x(0, 0), x(1, 1), x(2, 2)], 15]
        yield ["==", ["+", x(0, 2), x(1, 1), x(2, 0)], 15]

    translator = ORToolsTranslator()
    translator.translate(model())
    return translator.solve()

result = magic_square_3x3()
```

### Knapsack Problem

```python
from cp4py import Var
from cp4py.translators.ortools import ORToolsTranslator

def knapsack(weights, values, capacity):
    n = len(weights)
    x = Var("x")

    def model():
        for i in range(n):
            yield ["int", x(i), 0, 1]

        # Weight constraint
        yield ["<=", ["sum"] + [[weights[i], x(i)] for i in range(n)], capacity]

        # Maximize value
        yield ["maximize", ["sum"] + [[values[i], x(i)] for i in range(n)]]

    translator = ORToolsTranslator()
    translator.translate(model())
    return translator.solve()

weights = [2, 3, 4, 5, 9]
values = [3, 4, 5, 8, 10]
result = knapsack(weights, values, capacity=10)
```

### Switching Solvers

```python
from cp4py.translators.ortools import ORToolsTranslator
from cp4py.translators.z3 import Z3Translator
from cp4py.translators.scip import SCIPTranslator
from cp4py.translators.cvc5 import CVC5Translator
from cp4py.translators.gurobi import GurobiTranslator
from cp4py.translators.cplex import CPLEXTranslator
from cp4py.translators.cpoptimizer import CPOptimizerTranslator

# Use any translator
translator = Z3Translator()
translator.translate(model())
result = translator.solve()
```

## Var Helper Class

The `Var` class helps generate indexed variable names:

```python
from cp4py import Var

x = Var("x")
x()        # "x"
x(0)       # "x_0"
x(0, 1)    # "x_0_1"
x(2, 3, 4) # "x_2_3_4"

# With bounds (optional)
y = Var("y", lb=0, ub=100)
y.lb  # 0
y.ub  # 100
```

## Examples

See the `examples/` directory:

```bash
python examples/knapsack.py -ortools
python examples/knapsack.py -z3
python examples/knapsack.py -scip
python examples/knapsack.py -cvc5
python examples/knapsack.py -gurobi
python examples/knapsack.py -cplex
python examples/knapsack.py -cpoptimizer
```

## License

MIT
