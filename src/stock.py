class Stock:
    def __init__(self, name: str, initial_price: int):
        self.name = name
        self.price = initial_price
        self.price_history = [initial_price]

    def update_price(self, new_price: int):
        self.price = new_price
        self.price_history.append(new_price)

    def get_price_history(self):
        return self.price_history