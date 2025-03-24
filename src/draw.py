import gradio as gr
import matplotlib.pyplot as plt
from stock_simulation import StockSimulation


class Draw:
    def __init__(self, simulation: StockSimulation):
        self._simulation = simulation

    def _create_chart(self, stock_name: str):
        if not stock_name:
            return None

        stock = self._simulation.get_stock(stock_name)
        if stock:
            plt.figure(figsize=(10, 6))
            plt.plot([float(price) for price in stock.price_history])
            plt.title(f"{stock_name} Price History")
            plt.xlabel("Time")
            plt.ylabel("Price (₩)")
            plt.grid(True)
            return plt
        return None

    def _get_portfolio_display(self):
        user = self._simulation.user
        portfolio_data = []
        for stock_name, qty in user.portfolio.items():
            stock = self._simulation.get_stock(stock_name)
            portfolio_data.append([stock_name, qty, stock.price * qty])
        return user.balance, portfolio_data

    def _handle_buy(self, stock_name: str, qty: int):
        self._simulation.buy(stock_name, qty)
        return self._get_portfolio_display()

    def _handle_sell(self, stock_name: str, qty: int):
        self._simulation.sell(stock_name, qty)
        return self._get_portfolio_display()

    def create_interface(self) -> gr.Blocks:
        with gr.Blocks() as interface:
            gr.Markdown("# Stock Trading Simulation")

            with gr.Row():
                balance = gr.Number(
                    label="Current Balance", value=self._simulation.user.balance
                )
                portfolio = gr.DataFrame(headers=["Stock", "Quantity", "Current Value"])

            with gr.Row():
                stock_select = gr.Dropdown(
                    choices=self._simulation.get_stock_names(), label="Select Stock"
                )
                quantity = gr.Number(label="Quantity", value=1, precision=0)

            with gr.Row():
                buy_btn = gr.Button("Buy")
                sell_btn = gr.Button("Sell")

            chart = gr.Plot(label="Stock Price History")

            buy_btn.click(
                self._handle_buy,
                inputs=[stock_select, quantity],
                outputs=[balance, portfolio],
            )
            sell_btn.click(
                self._handle_sell,
                inputs=[stock_select, quantity],
                outputs=[balance, portfolio],
            )
            stock_select.change(
                self._create_chart, inputs=[stock_select], outputs=[chart]
            )

        return interface

    def run(self):
        interface = self.create_interface()
        interface.launch()
