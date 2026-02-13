"""
Streamlit Main Application

청소년을 위한 경제 교육 챗봇 UI
"""

import streamlit as st
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="TeensMate AI - 청소년 경제 교육",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바
with st.sidebar:
    st.title("💰 TeensMate AI")
    st.markdown("### 청소년을 위한 경제 교육 챗봇")
    st.markdown("---")
    
    # 페이지 선택
    page = st.radio(
        "페이지 선택",
        ["💬 채팅", "📈 주식 시뮬레이션", "🏭 밸류체인 분석"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("#### 📚 사용 가이드")
    st.markdown("""
    - **채팅**: AI와 경제 관련 대화
    - **주식 시뮬레이션**: 가상 투자 체험
    - **밸류체인 분석**: 제품/산업 생태계 분석
    """)
    
    st.markdown("---")
    st.info("💡 **Tip**: 이미지를 업로드하면 밸류체인을 자동으로 분석합니다!")

# 페이지 라우팅
if page == "💬 채팅":
    from frontend.pages import chat
    chat.main()
elif page == "📈 주식 시뮬레이션":
    from frontend.pages import stock_simulation
    stock_simulation.main()
elif page == "🏭 밸류체인 분석":
    from frontend.pages import value_chain
    value_chain.main()
