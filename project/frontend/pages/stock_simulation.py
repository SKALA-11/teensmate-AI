"""
Stock Simulation Page

주식 시뮬레이션 페이지 - 실시간 주가 + 모의 투자
KIS WebSocket API 연동 (한국투자증권 모의투자)
사회 초년생을 위한 실전 투자 연습
"""

import sys
from pathlib import Path

# 외부 환경에서 실행 시 프로젝트 루트를 모듈 경로에 추가
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
from datetime import datetime, time as dtime
import pytz
import threading
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

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


def _build_candle_data_ts(price_with_times: list) -> dict:
    """
    (timestamp, price) 쌍 리스트를 5틱 단위 OHLC 캔들로 변환.
    x 값은 각 캔들 윈도우의 마지막 타임스탬프.
    """
    CANDLE_SIZE = 5
    xs, opens, highs, lows, closes, volumes = [], [], [], [], [], []

    if len(price_with_times) < 1:
        return {}

    step = max(CANDLE_SIZE // 2, 1)
    for i in range(0, max(len(price_with_times) - CANDLE_SIZE + 1, 1), step):
        chunk = price_with_times[i: i + CANDLE_SIZE]
        if not chunk:
            continue
        times  = [t for t, _ in chunk]
        prices = [p for _, p in chunk]
        xs.append(times[-1])          # 캔들 x = 마지막 체결 시각
        opens.append(prices[0])
        highs.append(max(prices))
        lows.append(min(prices))
        closes.append(prices[-1])
        volumes.append(max(prices) - min(prices) + 1)

    return {"x": xs, "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes}


def _create_chart(stocks: list) -> go.Figure:
    """실시간 주가 차트 — 캔들스틱 + 이동평균 + 거래량, x축=실제 시각 (Plotly)"""
    from datetime import datetime, timedelta
    n = len(stocks)

    row_heights, subplot_titles = [], []
    for stock in stocks:
        row_heights += [0.75, 0.25]
        subplot_titles += [f"{stock.name} ({stock.code})", ""]

    total_rows = n * 2
    fig = make_subplots(
        rows=total_rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
        subplot_titles=subplot_titles,
    )

    UP_COLOR   = "#EF5350"
    DOWN_COLOR = "#2196F3"

    # 전체 x축 범위를 모든 종목의 최솟값~최댓값으로 통일
    all_times = []
    all_candles = []
    for stock in stocks:
        pwt = stock.price_with_times
        c = _build_candle_data_ts(pwt)
        all_candles.append(c)
        if c and c.get("x"):
            all_times.extend(c["x"])

    if all_times:
        x_min = min(all_times)
        x_max = max(all_times) + timedelta(seconds=10)
    else:
        x_min = x_max = None

    for stock_idx, stock in enumerate(stocks):
        candle_row = stock_idx * 2 + 1
        volume_row = stock_idx * 2 + 2
        candle = all_candles[stock_idx]

        if candle and candle.get("x"):
            xs         = candle["x"]
            closes_arr = candle["close"]
            colors_bar = [
                UP_COLOR if c >= o else DOWN_COLOR
                for c, o in zip(candle["close"], candle["open"])
            ]

            # ── 캔들스틱 ──
            fig.add_trace(
                go.Candlestick(
                    x=xs,
                    open=candle["open"],
                    high=candle["high"],
                    low=candle["low"],
                    close=candle["close"],
                    name=stock.name,
                    increasing=dict(line=dict(color=UP_COLOR, width=1), fillcolor=UP_COLOR),
                    decreasing=dict(line=dict(color=DOWN_COLOR, width=1), fillcolor=DOWN_COLOR),
                    showlegend=False,
                ),
                row=candle_row, col=1,
            )

            # ── MA5 ──
            if len(closes_arr) >= 5:
                ma5 = pd.Series(closes_arr).rolling(5).mean().tolist()
                fig.add_trace(
                    go.Scatter(
                        x=xs, y=ma5, mode="lines", name="MA5",
                        line=dict(color="#FF9800", width=1.5, dash="dot"),
                        showlegend=False,
                    ),
                    row=candle_row, col=1,
                )

            # ── MA20 ──
            if len(closes_arr) >= 20:
                ma20 = pd.Series(closes_arr).rolling(20).mean().tolist()
                fig.add_trace(
                    go.Scatter(
                        x=xs, y=ma20, mode="lines", name="MA20",
                        line=dict(color="#AB47BC", width=1.5, dash="dash"),
                        showlegend=False,
                    ),
                    row=candle_row, col=1,
                )

            # ── 현재가 수평선 ──
            if stock.price > 0:
                fig.add_hline(
                    y=stock.price,
                    line_dash="dot",
                    line_color="rgba(255,255,255,0.4)",
                    line_width=1,
                    row=candle_row, col=1,
                )

            # ── 거래량 바 ──
            fig.add_trace(
                go.Bar(
                    x=xs, y=candle["volume"],
                    marker_color=colors_bar,
                    marker_line_width=0,
                    name="거래량",
                    showlegend=False,
                    opacity=0.7,
                ),
                row=volume_row, col=1,
            )

            fig.update_yaxes(title_text="가격 (원)", row=candle_row, col=1,
                             showgrid=True, gridcolor="rgba(255,255,255,0.08)",
                             tickformat=",", zeroline=False)
            fig.update_yaxes(title_text="변동폭", row=volume_row, col=1,
                             showgrid=False, zeroline=False)
        else:
            fig.add_annotation(
                text=f"<b>{stock.name}</b><br>데이터 수신 대기 중...",
                xref="paper", yref="paper",
                x=0.5,
                y=1 - (stock_idx / max(n, 1)) - 0.05,
                showarrow=False,
                font=dict(size=13, color="#aaa"),
            )

    # x축 범위 통일 + 레인지슬라이더 제거
    xaxis_common = dict(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        rangeslider=dict(visible=False),
        **({"range": [x_min, x_max]} if x_min and x_max else {}),
    )

    fig.update_layout(
        height=max(380 * n, 380),
        showlegend=False,
        title_text="📈 실시간 주가 차트",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,15,30,0.85)",
        xaxis_rangeslider_visible=False,
        font=dict(color="#ccc"),
    )
    for i in range(1, total_rows + 1):
        fig.update_xaxes(**xaxis_common, row=i, col=1)

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
    st.markdown("한국투자증권 WebSocket API 기반 실시간 주가 · 사회 초년생을 위한 모의 투자 체험  \n"
                "실시간 체결 데이터는 장중(평일 09:00 ~ 15:30 KST)에만 수신됩니다.  \n"
                "WebSocket 연결은 유지되지만, 주가 업데이트가 없을 수 있습니다."
                )

    _show_market_status_banner()
    _init_session()

    # ── 종목 선택 구역 ─────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 종목 선택")

    stock_options = [f"{s['name']} ({s['code']})" for s in POPULAR_STOCKS]
    # SK하이닉스 기본 선택 (POPULAR_STOCKS[1])
    sk_hynix_option = next(
        (f"{s['name']} ({s['code']})" for s in POPULAR_STOCKS if s['name'] == 'SK하이닉스'),
        stock_options[1]
    )
    selected = st.multiselect(
        "조회할 종목을 선택하세요 (최대 4개)",
        options=stock_options,
        default=[sk_hynix_option],
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
    if st.session_state.is_running:
        st_autorefresh(interval=3000, limit=None, key="stock_refresh")


if __name__ == "__main__":
    main()
