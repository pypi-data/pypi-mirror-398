class Var:
    def __init__(self, name: str, lb=None, ub=None):
        self.name = name
        self.lb = lb
        self.ub = ub

    def __call__(self, *indices) -> str:
        if not indices:
            return self.name
        return f"{self.name}_{'_'.join(map(str, indices))}"
