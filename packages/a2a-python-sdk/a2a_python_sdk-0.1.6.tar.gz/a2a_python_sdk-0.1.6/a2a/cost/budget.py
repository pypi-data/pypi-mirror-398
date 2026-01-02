class BudgetManager:
    def __init__(self, monthly_limit_usd: float):
        self.limit = monthly_limit_usd
        self.spent = 0.0

    def allow(self, cost: float):
        if self.spent + cost > self.limit:
            raise RuntimeError("Budget exceeded")

        self.spent += cost
