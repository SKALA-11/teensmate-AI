import datetime
import gradio as gr
import matplotlib.pyplot as plt
from chatbot import ChatBot
from value_chain_chatbot import ValueChainChatBot
from stock_simulation import StockSimulation


class Draw:
    def __init__(self, simulation, chatbot, value_chain_chatbot):
        self._simulation = simulation
        self._chatbot = chatbot
        self._value_chain_chatbot = value_chain_chatbot

    def _create_chart(self, stock_name: str):
        if not stock_name:
            return None

        stock = self._simulation.get_stock(stock_name)
        if stock:
            plt.figure(figsize=(10, 6))
            plt.plot([float(price) for price in stock.price_history])
            plt.title(f"{stock_name} Price History")
            plt.xlabel(datetime.date.today())
            plt.xticks([])
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
            gr.Markdown("# AI Stock System")

            with gr.Column():
                gr.Markdown("## Stock Trading Simulation")
                with gr.Row():
                    balance = gr.Number(
                        label="Current Balance", value=self._simulation.user.balance
                    )
                    portfolio = gr.DataFrame(
                        headers=["Stock", "Quantity", "Current Value"]
                    )

                with gr.Row():
                    stock_select = gr.Dropdown(
                        choices=self._simulation.get_stock_names(), label="Select Stock"
                    )
                    quantity = gr.Number(label="Quantity", value=1, precision=0)

                with gr.Row():
                    buy_btn = gr.Button("Buy")
                    sell_btn = gr.Button("Sell")

                chart = gr.Plot(label="Stock Price History")

            with gr.Column():
                gr.Markdown("## AI 투자 도우미")
                
                with gr.Tab("도우미1"):
                    chatbot = gr.Chatbot(height=400)
                    msg = gr.Textbox(
                        label="투자 관련 질문을 입력하세요",
                        placeholder="예: SK하이닉스에 대해 알려주세요",
                    )
                    clear = gr.Button("대화 내용 지우기")
                        
                    def chatbot_input(message, history):
                        response = self._chatbot.run_query(message)
                        history.append((message, response))
                        return "", history

                    msg.submit(chatbot_input, inputs=[msg, chatbot], outputs=[msg, chatbot])
                    clear.click(lambda: None, None, chatbot, queue=False)

                with gr.Tab("도우미2"):
                    value_chain_chatbot = gr.Chatbot(height=400)
                    image = gr.Image(label="분석할 이미지를 업로드하세요", type="pil")
                    value_chain_msg = gr.Textbox(
                        label="이미지 업로드가 되지 않으면 입력하세요",
                        placeholder="예: 전기차 배터리에 대해 알려주세요",
                    )
                    value_chain_clear = gr.Button("대화 내용 지우기")
                    
                    def image_input(image, history):
                        try:
                            if image is not None:
                                response = self._value_chain_chatbot.run_query(image, "")
                                history.append(("이미지 업로드", response))
                        except Exception as e:
                            response = f"오류가 발생했습니다: {str(e)}"
                            history.append(("오류", response))
                        return None, history

                    def text_input(message, history):
                        try:
                            if message:
                                response = self._value_chain_chatbot.run_query(None, message)
                                history.append((message, response))
                            else:
                                response = "질문을 입력해주세요."
                                history.append(("", response))
                        except Exception as e:
                            response = f"오류가 발생했습니다: {str(e)}"
                            history.append(("오류", response))
                        return "", history
                    
                    image.change(
                        image_input,
                        inputs=[image, value_chain_chatbot],
                        outputs=[image, value_chain_chatbot],
                    )
                    
                    value_chain_msg.submit(
                        text_input,
                        inputs=[value_chain_msg, value_chain_chatbot],
                        outputs=[value_chain_msg, value_chain_chatbot],
                    )
                    value_chain_clear.click(
                        lambda: None, None, value_chain_chatbot, queue=False
                    )

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
            gr.Timer().tick(
                self._create_chart, inputs=[stock_select], outputs=[chart]
            )

        return interface

    def run(self):
        interface = self.create_interface()
        interface.launch()
