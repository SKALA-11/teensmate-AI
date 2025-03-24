#! /usr/bin/env python3
import time
import threading
from draw import Draw
from stock_simulation import StockSimulation


def update_prices(simulation):
    while True:
        simulation.update_stock_prices()
        time.sleep(1)


def main():
    simulation = StockSimulation()
    drawer = Draw(simulation)

    price_update_thread = threading.Thread(target=update_prices, args=(simulation,))
    price_update_thread.daemon = True
    price_update_thread.start()

    drawer.run()


if __name__ == "__main__":
    main()
