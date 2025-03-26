DEFAULT_INITIAL_BALANCE = 10_000_000


class User:
    def __init__(self, initial_balance: int = DEFAULT_INITIAL_BALANCE):
        self._balance = initial_balance
        self._portfolio = {}

    @property
    def balance(self):
        return self._balance

    @property
    def portfolio(self):
        return self._portfolio.copy()

    def buy_stock(self, stock_name: str, stock_price: int, quantity: int):
        if stock_price == 0:
            return
        total_cost = stock_price * quantity
        if total_cost <= self._balance:
            self._balance -= total_cost
            self._portfolio[stock_name] = self._portfolio.get(stock_name, 0) + quantity

    def sell_stock(self, stock_name: str, stock_price: int, quantity: int):
        if stock_name in self._portfolio and self._portfolio[stock_name] >= quantity:
            self._balance += stock_price * quantity
            self._portfolio[stock_name] -= quantity
            if self._portfolio[stock_name] == 0:
                del self._portfolio[stock_name]
