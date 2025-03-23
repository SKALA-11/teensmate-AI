DEFAULT_INITIAL_BALANCE = 10_000_000

class User:
    def __init__(self, initial_balance: int = DEFAULT_INITIAL_BALANCE):
        self.balance = initial_balance
        self.portfolio = {}  # {stock_name: quantity}

    def buy_stock(self, stock: 'Stock', quantity: int) -> bool:
        total_cost = stock.price * quantity
        if total_cost <= self.balance:
            self.balance -= total_cost
            self.portfolio[stock.name] = self.portfolio.get(stock.name, 0) + quantity
            return True
        return False

    def sell_stock(self, stock: 'Stock', quantity: int) -> bool:
        if stock.name in self.portfolio and self.portfolio[stock.name] >= quantity:
            self.balance += stock.price * quantity
            self.portfolio[stock.name] -= quantity
            if self.portfolio[stock.name] == 0:
                del self.portfolio[stock.name]
            return True
        return False