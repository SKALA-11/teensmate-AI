DEFAULT_INITIAL_PRICE = 0


class Stock:
    def __init__(self, name: str, initial_price: int = DEFAULT_INITIAL_PRICE):
        self._name = name
        self._price = initial_price
        self._price_history = [self._price]

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self):
        return self._price

    @property
    def price_history(self):
        return self._price_history.copy()

    def update_price(self, new_price: int):
        self._price = new_price
        self._price_history.append(self._price)
