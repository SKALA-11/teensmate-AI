DEFAULT_INITIAL_PRICE = 0


class Stock:
    def __init__(
        self, name: str, tr_id: str, initial_price: int = DEFAULT_INITIAL_PRICE
    ):
        self._name = name
        self._id = tr_id
        self._price = initial_price
        self._price_history = [self._price]

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def price(self):
        return self._price

    @property
    def price_history(self):
        return self._price_history.copy()

    def update_price(self, new_price: int):
        if self._price_history[0] == DEFAULT_INITIAL_PRICE:
            self._price_history[0] = new_price
        self._price = new_price
        self._price_history.append(self._price)
