"""
Chat Page

채팅 페이지
"""

import streamlit as st
from agents.orchestrator import AgentOrchestrator


def main():
    """채팅 페이지"""
    
    # 오케스트레이터 초기화 (세션 상태로 관리)
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = AgentOrchestrator(enable_memory=True)
    
    # 채팅 히스토리 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    st.title("💬 AI 경제 교육 챗봇")
    st.markdown("경제, 투자, 금융에 대해 무엇이든 물어보세요!")
    
    # 채팅 히스토리 초기화 버튼
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ 대화 초기화", width='stretch'):
            st.session_state.messages = []
            if "orchestrator" in st.session_state:
                st.session_state.orchestrator.clear_memory()
            st.rerun()
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                try:
                    response = st.session_state.orchestrator.run(
                        query=prompt,
                        session_id="streamlit_user"
                    )
                    
                    st.markdown(response)
                    
                    # AI 메시지 추가
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                except Exception as e:
                    error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # 샘플 질문
    st.markdown("---")
    st.markdown("#### 💡 이런 질문을 해보세요!")
    
    sample_questions = [
        "PER이란 무엇인가요?",
        "반도체 산업 최근 동향은?",
        "삼성전자 재무제표 분석해줘",
        "인플레이션이 왜 일어나나요?",
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(question, key=f"sample_{i}", width='stretch'):
                st.session_state.messages.append({
                    "role": "user",
                    "content": question
                })
                st.rerun()
