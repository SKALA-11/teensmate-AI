#! /usr/bin/env python3
import asyncio
import time
import threading
from chatbot import ChatBot
from draw import Draw
from kis_ws_client import KisWsClient
from stock import Stock
from stock_simulation import StockSimulation

# 실시간 모의 투자 주식 종목
STOCKS = [
    Stock("Samsung Electronics", "005930"),
    Stock("LG Electronics", "066570"),
    Stock("SK Hynix", "000660"),
]


def main():
    client = KisWsClient(STOCKS)
    stock_update_thread = threading.Thread(
        target=lambda: asyncio.run(client.run()), daemon=True
    )
    stock_update_thread.start()

    simulation = StockSimulation(STOCKS)
    chatbot = ChatBot()

    drawer = Draw(simulation, chatbot)
    drawer.run()


if __name__ == "__main__":
    main()
