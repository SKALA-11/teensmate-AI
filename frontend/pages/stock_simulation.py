"""
Stock Simulation Page

주식 시뮬레이션 페이지
"""

import streamlit as st


def main():
    """주식 시뮬레이션 페이지"""
    
    st.title("📈 주식 시뮬레이션")
    st.markdown("가상 투자를 통해 주식 거래를 체험해보세요!")
    
    # 주식 시뮬레이션 기능은 기존 코드 리팩토링 후 구현 예정
    st.info("🚧 **준비 중**: 주식 시뮬레이션 기능은 곧 추가됩니다!")
    
    st.markdown("---")
    st.markdown("#### 📊 주요 기능 (예정)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **가상 포트폴리오**
        - 초기 자본 1억원
        - 실시간 주가 반영
        - 매수/매도 시뮬레이션
        """)
    
    with col2:
        st.markdown("""
        **성과 분석**
        - 수익률 차트
        - 포트폴리오 구성
        - 거래 내역
        """)
    
    # 샘플 데이터 표시
    st.markdown("---")
    st.markdown("#### 💼 포트폴리오 예시")
    
    import pandas as pd
    
    sample_data = pd.DataFrame({
        "종목": ["삼성전자", "SK하이닉스", "NAVER", "카카오"],
        "보유수량": [10, 5, 3, 8],
        "평균단가": [70000, 180000, 200000, 45000],
        "현재가": [72000, 185000, 195000, 47000],
        "수익률": ["+2.86%", "+2.78%", "-2.50%", "+4.44%"],
    })
    
    st.dataframe(sample_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("#### 📈 주가 차트 예시")
    
    # 샘플 차트
    import numpy as np
    
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['삼성전자', 'SK하이닉스', 'NAVER']
    )
    
    st.line_chart(chart_data)
