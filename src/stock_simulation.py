from stock import Stock
from user import User
import random


class StockSimulation:
    def __init__(self):
        self._stocks = [
            Stock("Samsung Electronics", 70000),
            Stock("SK Hynix", 120000),
            Stock("NAVER", 200000),
            Stock("Kakao", 55000),
        ]
        self._user = User()

    @property
    def user(self):
        return self._user

    def get_stock(self, name: str):
        return next(stock for stock in self._stocks if stock.name == name)

    def get_stock_names(self):
        return [stock.name for stock in self._stocks]

    def update_stock_prices(self):
        for stock in self._stocks:
            price_change = random.uniform(-0.01, 0.01)
            new_price = int(stock.price * (1 + price_change))
            stock.update_price(new_price)

    def buy(self, stock_name: str, quantity: int):
        stock = self.get_stock(stock_name)
        return self._user.buy_stock(stock_name, stock.price, quantity)

    def sell(self, stock_name: str, quantity: int):
        stock = self.get_stock(stock_name)
        return self._user.sell_stock(stock_name, stock.price, quantity)
