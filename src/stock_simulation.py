from user import User


class StockSimulation:
    def __init__(self, stocks):
        self._stocks = stocks
        self._user = User()

    @property
    def user(self):
        return self._user

    def get_stock(self, name: str):
        return next(stock for stock in self._stocks if stock.name == name)

    def get_stock_names(self):
        return [stock.name for stock in self._stocks]

    def buy(self, stock_name: str, quantity: int):
        stock = self.get_stock(stock_name)
        return self._user.buy_stock(stock_name, stock.price, quantity)

    def sell(self, stock_name: str, quantity: int):
        stock = self.get_stock(stock_name)
        return self._user.sell_stock(stock_name, stock.price, quantity)
