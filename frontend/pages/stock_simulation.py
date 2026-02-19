"""
Stock Simulation Page

주식 시뮬레이션 페이지 - 실시간 주가 그래프
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime

from stock.models import Stock
from stock.kis_client import KISWebSocketClient


# 인기 종목 리스트
POPULAR_STOCKS = [
    {"name": "삼성전자", "code": "005930"},
    {"name": "SK하이닉스", "code": "000660"},
    {"name": "NAVER", "code": "035420"},
    {"name": "카카오", "code": "035720"},
    {"name": "현대차", "code": "005380"},
    {"name": "LG에너지솔루션", "code": "373220"},
    {"name": "삼성바이오로직스", "code": "207940"},
    {"name": "셀트리온", "code": "068270"},
]


def create_price_chart(stocks):
    """
    실시간 주가 차트 생성
    
    Args:
        stocks: Stock 객체 리스트
        
    Returns:
        Plotly Figure
    """
    fig = make_subplots(
        rows=len(stocks), 
        cols=1,
        subplot_titles=[f"{s.name} ({s.code})" for s in stocks],
        vertical_spacing=0.08
    )
    
    for idx, stock in enumerate(stocks, 1):
        history = stock.price_history
        
        # 가격 히스토리가 있는 경우만 표시
        if len(history) > 1:
            fig.add_trace(
                go.Scatter(
                    y=history,
                    mode='lines',
                    name=stock.name,
                    line=dict(color='#1f77b4', width=2)
                ),
                row=idx,
                col=1
            )
        
        # Y축 레이블
        fig.update_yaxes(title_text="가격 (원)", row=idx, col=1)
    
    fig.update_layout(
        height=300 * len(stocks),
        showlegend=False,
        title_text="실시간 주가 차트",
        hovermode='x unified'
    )
    
    return fig


def main():
    """주식 시뮬레이션 페이지"""
    
    st.title("📈 실시간 주식 시세")
    st.markdown("사회 초년생을 위한 실전 주식 시세 조회 — 한국투자증권 API 연동")
    
    # 세션 상태 초기화
    if "ws_client" not in st.session_state:
        st.session_state.ws_client = None
        st.session_state.stocks = []
        st.session_state.is_running = False
    
    # 종목 선택
    st.markdown("---")
    st.markdown("#### 📊 종목 선택")
    
    selected_stocks = st.multiselect(
        "조회할 종목을 선택하세요 (최대 4개)",
        options=[f"{s['name']} ({s['code']})" for s in POPULAR_STOCKS],
        default=[f"{POPULAR_STOCKS[0]['name']} ({POPULAR_STOCKS[0]['code']})"],
        max_selections=4
    )
    
    if not selected_stocks:
        st.warning("⚠️ 종목을 선택해주세요.")
        return
    
    # 선택된 종목 파싱
    selected_codes = []
    for item in selected_stocks:
        # "삼성전자 (005930)" 형식에서 코드 추출
        code = item.split("(")[1].split(")")[0]
        name = item.split(" (")[0]
        selected_codes.append({"name": name, "code": code})
    
    # 시작/중지 버튼
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("🚀 시작", width='stretch', disabled=st.session_state.is_running):
            # Stock 객체 생성
            st.session_state.stocks = [
                Stock(name=s["name"], code=s["code"])
                for s in selected_codes
            ]
            st.session_state.is_running = True
            st.success("실시간 데이터 수신 시작!")
            st.rerun()
    
    with col2:
        if st.button("⏹️ 중지", width='stretch', disabled=not st.session_state.is_running):
            st.session_state.is_running = False
            st.session_state.ws_client = None
            st.info("데이터 수신 중지")
            st.rerun()
    
    # 실시간 데이터 표시
    if st.session_state.is_running and st.session_state.stocks:
        st.markdown("---")
        st.markdown("#### 📊 실시간 현황")
        
        # 현재가 표시 (테이블)
        stock_data = []
        for stock in st.session_state.stocks:
            stock_data.append({
                "종목명": stock.name,
                "종목코드": stock.code,
                "현재가": f"{stock.price:,}원" if stock.price > 0 else "-",
                "데이터 개수": len(stock.price_history)
            })
        
        df = pd.DataFrame(stock_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # 실시간 차트
        if any(len(s.price_history) > 1 for s in st.session_state.stocks):
            st.markdown("#### 📈 가격 추이")
            chart = create_price_chart(st.session_state.stocks)
            st.plotly_chart(chart, width='stretch')
        else:
            st.info("⏳ 데이터 수신 중... 잠시만 기다려주세요.")
        
        # WebSocket 클라이언트 실행 (비동기)
        # 주의: Streamlit은 비동기를 직접 지원하지 않으므로 별도 스레드 필요
        st.markdown("---")
        st.markdown("#### ⚠️ 주의사항")
        st.warning("""
        **실시간 WebSocket 연결은 별도 백엔드 서버가 필요합니다.**
        
        현재는 데모 UI만 표시되며, 실제 데이터 수신을 위해서는:
        1. FastAPI 백엔드에서 WebSocket 엔드포인트 구현
        2. Streamlit에서 HTTP API로 데이터 폴링
        또는
        3. 별도 WebSocket 서버 실행 후 상태 공유
        
        **권장 구조:**
        - Backend: WebSocket 클라이언트 실행, 실시간 데이터 저장
        - Frontend: Backend API를 통해 주기적으로 데이터 조회
        """)
    
    else:
        st.markdown("---")
        st.info("🚀 시작 버튼을 눌러 실시간 주가 조회를 시작하세요!")
        
        # 샘플 차트
        st.markdown("#### 📊 샘플 차트 (데모)")
        
        import numpy as np
        
        # 랜덤 데이터 생성
        sample_data = pd.DataFrame({
            "삼성전자": np.random.randint(70000, 75000, 20),
            "SK하이닉스": np.random.randint(180000, 190000, 20),
            "NAVER": np.random.randint(195000, 205000, 20),
        })
        
        st.line_chart(sample_data)
        
        st.markdown("---")
        st.markdown("#### 💡 사용 방법")
        st.markdown("""
        1. 위에서 조회할 종목을 선택하세요 (최대 4개)
        2. **시작** 버튼을 클릭하여 실시간 데이터 수신
        3. 실시간 차트와 현재가를 확인하세요
        4. **중지** 버튼으로 수신을 중단할 수 있습니다
        
        **주요 기능:**
        - 📈 실시간 주가 차트
        - 📊 현재가 및 가격 추이
        - 🔄 다중 종목 동시 조회
        """)

if __name__ == "__main__":
    main()
