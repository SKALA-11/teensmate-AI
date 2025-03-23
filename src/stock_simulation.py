import gradio as gr
import random
import time
import matplotlib.pyplot as plt
from typing import List
from stock import Stock
from user import User

class StockSimulation:
    def __init__(self):
        self.stocks = [
            Stock("Samsung Electronics", 70000),
            Stock("SK Hynix", 120000),
            Stock("NAVER", 200000),
            Stock("Kakao", 55000)
        ]
        self.user = User()

    def update_stock_prices(self):
        for stock in self.stocks:
            price_change = random.uniform(-0.01, 0.01)
            new_price = int(stock.price * (1 + price_change))
            stock.update_price(new_price)

    def create_interface(self):
        with gr.Blocks() as interface:
            gr.Markdown("# Stock Trading Simulation")
            
            with gr.Row():
                balance = gr.Number(label="Current Balance", value=self.user.balance)
                portfolio = gr.DataFrame(headers=["Stock", "Quantity", "Current Value"])

            with gr.Row():
                stock_select = gr.Dropdown(choices=[stock.name for stock in self.stocks], label="Select Stock")
                quantity = gr.Number(label="Quantity", value=1)

            with gr.Row():
                buy_btn = gr.Button("Buy")
                sell_btn = gr.Button("Sell")

            chart = gr.Plot(label="Stock Price History")

            def update_chart(stock_name):
                if stock_name:
                    stock = next(s for s in self.stocks if s.name == stock_name)
                    plt.figure(figsize=(10, 6))
                    plt.plot(stock.get_price_history())
                    plt.title(f"{stock_name} Price History")
                    plt.xlabel("Time")
                    plt.ylabel("Price")
                    plt.grid(True)
                    return plt

            def update_display():
                portfolio_data = []
                for stock_name, qty in self.user.portfolio.items():
                    stock = next(s for s in self.stocks if s.name == stock_name)
                    portfolio_data.append([stock_name, qty, stock.price * qty])
                
                return self.user.balance, portfolio_data

            def buy(stock_name, qty):
                stock = next(s for s in self.stocks if s.name == stock_name)
                success = self.user.buy_stock(stock, int(qty))
                return update_display()

            def sell(stock_name, qty):
                stock = next(s for s in self.stocks if s.name == stock_name)
                success = self.user.sell_stock(stock, int(qty))
                return update_display()

            buy_btn.click(buy, inputs=[stock_select, quantity], outputs=[balance, portfolio])
            sell_btn.click(sell, inputs=[stock_select, quantity], outputs=[balance, portfolio])
            stock_select.change(update_chart, inputs=[stock_select], outputs=[chart])

        return interface

    def run(self):
        interface = self.create_interface()
        interface.launch()