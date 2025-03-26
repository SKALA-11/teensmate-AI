import datetime
import gradio as gr
import matplotlib.pyplot as plt


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
            plt.rcParams["font.family"] = "Malgun Gothic"
            plt.rcParams["axes.unicode_minus"] = False
            plt.figure(figsize=(10, 6))
            plt.plot([float(price) for price in stock.price_history])
            plt.title(f"{stock_name} 주가")
            plt.xlabel(f"날짜: {datetime.date.today()}")
            plt.xticks([])
            plt.ylabel("가격 (₩)")
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
        with gr.Blocks(theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🎯 청소년 주식 투자 교실")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## 💰 내 투자 현황")

                    gr.Markdown("### 🛒 주식 거래")
                    chart = gr.Plot(label="실시간 주가")

                    with gr.Row(equal_height=True):
                        with gr.Column(scale=2):
                            stock_select = gr.Dropdown(
                                choices=self._simulation.get_stock_names(),
                                label="거래할 종목 선택",
                            )
                        with gr.Column(scale=1):
                            quantity = gr.Number(
                                label="거래 수량", value=1, precision=0
                            )

                    with gr.Row():
                        buy_btn = gr.Button(
                            "매수하기 📈", variant="secondary", size="lg"
                        )
                        sell_btn = gr.Button(
                            "매도하기 📉", variant="secondary", size="lg"
                        )

                    gr.Markdown("### 📊 계좌 정보")
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1):
                            balance = gr.Number(
                                label="보유 현금",
                                value=self._simulation.user.balance,
                                container=True,
                            )
                        with gr.Column(scale=2):
                            portfolio = gr.DataFrame(
                                headers=["종목명", "보유 수량", "현재 가치"],
                                wrap=True,
                            )

                with gr.Column(scale=1):
                    gr.Markdown("## 🤖 AI 투자 상담")

                    with gr.Tab("💡 투자 도우미"):
                        chatbot = gr.Chatbot(height=400)
                        msg = gr.Textbox(
                            label="궁금한 점을 자유롭게 물어보세요!",
                            placeholder="예: SK하이닉스는 어떤 회사인가요?",
                        )
                        clear = gr.Button("대화 내용 지우기 🗑️")

                    with gr.Tab("🔍 기업 분석"):
                        value_chain_chatbot = gr.Chatbot(height=400)
                        image = gr.Image(
                            label="기업 관련 이미지를 올려주세요", type="pil"
                        )
                        value_chain_msg = gr.Textbox(
                            label="기업이나 산업에 대해 물어보세요",
                            placeholder="예: 전기차 배터리 산업을 설명해주세요",
                        )
                        value_chain_clear = gr.Button("대화 내용 지우기 🗑️")

                    def chatbot_input(message, history):
                        response = self._chatbot.run_query(message)
                        history.append((message, response))
                        return "", history

                    msg.submit(
                        chatbot_input, inputs=[msg, chatbot], outputs=[msg, chatbot]
                    )
                    clear.click(lambda: None, None, chatbot, queue=False)

                    def image_input(image, history):
                        try:
                            if image is not None:
                                response = self._value_chain_chatbot.run_query(
                                    image, ""
                                )
                                history.append(("이미지 업로드", response))
                        except Exception as e:
                            response = f"오류가 발생했습니다: {str(e)}"
                            history.append(("오류", response))
                        return history

                    def text_input(message, history):
                        try:
                            if message:
                                response = self._value_chain_chatbot.run_query(
                                    None, message
                                )
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
                        outputs=[value_chain_chatbot],
                    )

                    value_chain_msg.submit(
                        text_input,
                        inputs=[value_chain_msg, value_chain_chatbot],
                        outputs=[value_chain_msg, value_chain_chatbot],
                    )
                    value_chain_clear.click(
                        lambda: (None, None),
                        None,
                        [value_chain_chatbot, image],
                        queue=False,
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
            gr.Timer().tick(self._create_chart, inputs=[stock_select], outputs=[chart])

        return interface

    def run(self):
        interface = self.create_interface()
        interface.launch()
