"""
Streamlit Main Application

사회 초년생을 위한 경제·금융 AI 가이드 UI
"""

import sys
from pathlib import Path

# 외부 환경에서 실행 시 프로젝트 루트를 모듈 경로에 추가
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="NewMate AI - 사회 초년생 경제 가이드",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바
with st.sidebar:
    st.title("💼 NewMate AI")
    st.markdown("### 사회 초년생을 위한 경제·금융 AI 가이드")
    st.markdown("---")
    
    # 페이지 선택
    page = st.radio(
        "페이지 선택",
        ["💬 채팅", "📈 주식 시뮬레이션", "🏭 밸류체인 분석"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("#### 📚 사용 가이드")
    st.markdown("""
    - **채팅**: AI와 경제·금융 상담
    - **주식 시뮬레이션**: 실시간 주가 조회
    - **밸류체인 분석**: 제품/산업 생태계 분석
    """)
    
    st.markdown("---")
    st.info("💡 **Tip**: 첫 월급, 연말정산, 주식 투자 등 무엇이든 여쭤보세요!")

# 페이지 라우팅
if page == "💬 채팅":
    from pages import chat
    chat.main()
elif page == "📈 주식 시뮬레이션":
    from pages import stock_simulation
    stock_simulation.main()
elif page == "🏭 밸류체인 분석":
    from pages import value_chain
    value_chain.main()
