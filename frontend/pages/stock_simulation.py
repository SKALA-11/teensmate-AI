"""
Stock Simulation Page

주식 시뮬레이션 페이지 - 실시간 주가 + 모의 투자
KIS WebSocket API 연동 (한국투자증권 모의투자)
사회 초년생을 위한 실전 투자 연습
"""

import time
from datetime import datetime, time as dtime
import pytz
import threading
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from stock.models import Stock, User
from stock.kis_client import KISWebSocketClient

# 한국 장중 시간 (09:00 ~ 15:30 KST)
KST = pytz.timezone("Asia/Seoul")
MARKET_OPEN  = dtime(9, 0, 0)
MARKET_CLOSE = dtime(15, 30, 0)


def _is_market_open() -> bool:
    """현재 한국 주식 시장 장중 여부 반환"""
    now_kst = datetime.now(KST).time()
    return MARKET_OPEN <= now_kst <= MARKET_CLOSE


def _show_market_status_banner():
    """장외 시간이면 경고 배너 표시"""
    if not _is_market_open():
        now_kst = datetime.now(KST).strftime("%H:%M")
        st.warning(
            f"⚠️ **현재 주식 거래 시간이 아닙니다** (현재 시각 KST {now_kst})  \n"
            "실시간 체결 데이터는 **장중(평일 09:00 ~ 15:30 KST)**에만 수신됩니다.  \n"
            "WebSocket 연결은 유지되지만, 주가 업데이트가 없을 수 있습니다."
        )


# 인기 종목 리스트 (이름, 종목코드)
POPULAR_STOCKS = [
    {"name": "삼성전자",       "code": "005930"},
    {"name": "SK하이닉스",     "code": "000660"},
    {"name": "LG전자",         "code": "066570"},
    {"name": "NAVER",          "code": "035420"},
    {"name": "카카오",         "code": "035720"},
    {"name": "현대차",         "code": "005380"},
    {"name": "LG에너지솔루션", "code": "373220"},
    {"name": "삼성바이오로직스","code": "207940"},
]


# ─── 헬퍼 함수 ────────────────────────────────────────────────────────────────

def _init_session():
    """세션 상태 초기화 (최초 1회)"""
    if "sim_initialized" not in st.session_state:
        st.session_state.sim_initialized = True
        st.session_state.stocks: list[Stock] = []
        st.session_state.user: User | None = None
        st.session_state.ws_client: KISWebSocketClient | None = None
        st.session_state.is_running: bool = False
        st.session_state.buy_msg: str = ""
        st.session_state.sell_msg: str = ""


def _start_websocket(stocks: list[Stock]):
    """KIS WebSocket 백그라운드 스레드 시작"""
    client = KISWebSocketClient(stocks)
    client.start()
    st.session_state.ws_client = client


def _stop_websocket():
    """KIS WebSocket 중지"""
    if st.session_state.ws_client:
        st.session_state.ws_client.stop()
        st.session_state.ws_client = None


def _create_chart(stocks: list[Stock]) -> go.Figure:
    """실시간 주가 차트 생성 (Plotly)"""
    n = len(stocks)
    fig = make_subplots(
        rows=n,
        cols=1,
        subplot_titles=[f"{s.name} ({s.code})" for s in stocks],
        vertical_spacing=0.10,
    )

    colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63"]

    for idx, stock in enumerate(stocks, 1):
        history = stock.price_history
        color = colors[(idx - 1) % len(colors)]

        if len(history) > 1:
            fig.add_trace(
                go.Scatter(
                    y=history,
                    mode="lines",
                    name=stock.name,
                    line=dict(color=color, width=2),
                    fill="tozeroy",
                    fillcolor=color.replace(")", ", 0.1)").replace("rgb", "rgba"),
                ),
                row=idx,
                col=1,
            )
        else:
            # 데이터 없음 안내
            fig.add_annotation(
                text="데이터 수신 대기 중...",
                xref="paper",
                yref=f"y{idx}" if idx > 1 else "y",
                x=0.5,
                y=0,
                showarrow=False,
                font=dict(size=12, color="gray"),
                row=idx,
                col=1,
            )

        fig.update_yaxes(title_text="가격 (원)", row=idx, col=1)

    fig.update_layout(
        height=max(280 * n, 300),
        showlegend=False,
        title_text="📈 실시간 주가 차트",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.02)",
    )
    return fig


def _portfolio_df(user: User, stocks: list[Stock]) -> pd.DataFrame:
    """포트폴리오 데이터프레임 생성"""
    rows = []
    for stock_name, qty in user.portfolio.items():
        stock = next((s for s in stocks if s.name == stock_name), None)
        price = stock.price if stock else 0
        rows.append({
            "종목명": stock_name,
            "보유 수량": qty,
            "현재가 (원)": f"{price:,}" if price > 0 else "-",
            "평가액 (원)": f"{price * qty:,}" if price > 0 else "-",
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["종목명", "보유 수량", "현재가 (원)", "평가액 (원)"]
    )


# ─── 메인 ────────────────────────────────────────────────────────────────────

def main():
    """주식 시뮬레이션 페이지"""

    st.title("📈 실시간 주식 시세 & 모의 투자")
    st.markdown("한국투자증권 WebSocket API 기반 실시간 주가 · 사회 초년생을 위한 모의 투자 체험")

    _show_market_status_banner()
    _init_session()

    # ── 종목 선택 구역 ─────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 종목 선택")

    stock_options = [f"{s['name']} ({s['code']})" for s in POPULAR_STOCKS]
    selected = st.multiselect(
        "조회할 종목을 선택하세요 (최대 4개)",
        options=stock_options,
        default=[stock_options[0]],
        max_selections=4,
        disabled=st.session_state.is_running,
    )

    if not selected:
        st.warning("⚠️ 종목을 선택해주세요.")
        return

    # 선택 종목 파싱
    selected_info = []
    for item in selected:
        code = item.split("(")[1].rstrip(")")
        name = item.split(" (")[0]
        selected_info.append({"name": name, "code": code})

    # ── 시작/중지 버튼 ─────────────────────────────────────
    col_start, col_stop, _ = st.columns([1, 1, 4])

    with col_start:
        if st.button("🚀 시작", width="stretch", disabled=st.session_state.is_running):
            # Stock 객체 생성 (공유 참조 — WebSocket이 직접 업데이트)
            stocks = [Stock(name=s["name"], code=s["code"]) for s in selected_info]
            st.session_state.stocks = stocks
            st.session_state.user = User()
            st.session_state.is_running = True
            st.session_state.buy_msg = ""
            st.session_state.sell_msg = ""
            _start_websocket(stocks)
            st.rerun()

    with col_stop:
        if st.button("⏹️ 중지", width="stretch", disabled=not st.session_state.is_running):
            _stop_websocket()
            st.session_state.is_running = False
            st.rerun()

    # ── 실행 중 화면 ───────────────────────────────────────
    if not st.session_state.is_running:
        st.markdown("---")
        st.info("🚀 시작 버튼을 눌러 실시간 주가 조회를 시작하세요!")
        st.markdown("""
        **주요 기능:**
        - 📡 한국투자증권 WebSocket API 실시간 연동
        - 📈 다중 종목 실시간 차트
        - 💰 모의 매수/매도 연습 (초기 잔고 1,000만원)
        
        > ℹ️ 실시간 체결 데이터는 **평일 장중(09:00 ~ 15:30 KST)**에만 수신됩니다.
        """)
        return

    stocks: list[Stock] = st.session_state.stocks
    user: User = st.session_state.user
    client: KISWebSocketClient = st.session_state.ws_client

    # 연결 상태 표시
    if client and client.is_connected:
        st.success("✅ KIS WebSocket 연결됨 — 실시간 데이터 수신 중")
    else:
        st.warning("⏳ KIS WebSocket 연결 중... (잠시 기다려주세요)")

    st.markdown("---")

    # ── 좌/우 2열 레이아웃 ────────────────────────────────
    left, right = st.columns([3, 2])

    # === 왼쪽: 실시간 차트 ===
    with left:
        st.markdown("#### 📊 실시간 현황")

        # 현재가 테이블
        price_data = [
            {
                "종목명": s.name,
                "종목코드": s.code,
                "현재가 (원)": f"{s.price:,}" if s.price > 0 else "수신 대기",
                "데이터 수": len(s.price_history),
            }
            for s in stocks
        ]
        st.dataframe(pd.DataFrame(price_data), width="stretch", hide_index=True)

        # 실시간 차트
        chart_placeholder = st.empty()
        chart_placeholder.plotly_chart(
            _create_chart(stocks),
            width="stretch",
            key="realtime_chart",
        )

    # === 오른쪽: 매수/매도 + 계좌 정보 ===
    with right:
        st.markdown("#### 🛒 주식 거래")

        # 종목 선택 드롭다운
        stock_names = [s.name for s in stocks]
        selected_stock_name = st.selectbox("거래할 종목", options=stock_names)
        selected_stock = next(s for s in stocks if s.name == selected_stock_name)
        qty = st.number_input("거래 수량", min_value=1, value=1, step=1)

        buy_col, sell_col = st.columns(2)
        with buy_col:
            if st.button("📈 매수", width="stretch"):
                if selected_stock.price == 0:
                    st.session_state.buy_msg = "❌ 아직 현재가 데이터가 없습니다."
                else:
                    ok = user.buy_stock(selected_stock_name, selected_stock.price, int(qty))
                    if ok:
                        cost = selected_stock.price * int(qty)
                        st.session_state.buy_msg = (
                            f"✅ {selected_stock_name} {int(qty)}주 매수 완료\n"
                            f"   ({selected_stock.price:,}원 × {int(qty)}주 = {cost:,}원)"
                        )
                    else:
                        st.session_state.buy_msg = (
                            f"❌ 잔고 부족\n"
                            f"   필요: {selected_stock.price * int(qty):,}원 / 보유: {user.balance:,}원"
                        )
                st.rerun()

        with sell_col:
            if st.button("📉 매도", width="stretch"):
                if selected_stock.price == 0:
                    st.session_state.sell_msg = "❌ 아직 현재가 데이터가 없습니다."
                else:
                    ok = user.sell_stock(selected_stock_name, selected_stock.price, int(qty))
                    if ok:
                        gain = selected_stock.price * int(qty)
                        st.session_state.sell_msg = (
                            f"✅ {selected_stock_name} {int(qty)}주 매도 완료\n"
                            f"   수익: +{gain:,}원"
                        )
                    else:
                        st.session_state.sell_msg = (
                            f"❌ 보유 수량 부족\n"
                            f"   보유: {user.portfolio.get(selected_stock_name, 0)}주"
                        )
                st.rerun()

        # 거래 메시지 표시
        if st.session_state.buy_msg:
            if st.session_state.buy_msg.startswith("✅"):
                st.success(st.session_state.buy_msg)
            else:
                st.error(st.session_state.buy_msg)

        if st.session_state.sell_msg:
            if st.session_state.sell_msg.startswith("✅"):
                st.success(st.session_state.sell_msg)
            else:
                st.error(st.session_state.sell_msg)

        # 계좌 정보
        st.markdown("---")
        st.markdown("#### 💰 계좌 정보")
        st.metric("보유 현금", f"{user.balance:,} 원")

        st.markdown("**📋 포트폴리오**")
        portfolio_df = _portfolio_df(user, stocks)
        if portfolio_df.empty:
            st.info("보유 종목 없음")
        else:
            st.dataframe(portfolio_df, width="stretch", hide_index=True)

    # ── 자동 갱신 (3초마다 rerun) ─────────────────────────
    time.sleep(3)
    st.rerun()


if __name__ == "__main__":
    main()
