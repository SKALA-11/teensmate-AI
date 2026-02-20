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
    
    st.title("💬 AI 경제·금융 상담")
    st.markdown("사회 초년생의 금융 고민, AI에게 무엇이든 여쭤보세요!")
    
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
    
    # 마지막 메시지가 사용자일 경우 답변 생성 (버튼 클릭 등으로 인한 rerun 대응)
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                try:
                    last_query = st.session_state.messages[-1]["content"]
                    response = st.session_state.orchestrator.run(
                        query=last_query,
                        session_id="streamlit_user"
                    )
                    
                    st.markdown(response)
                    
                    # AI 메시지 추가
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # 메시지 추가 후 Rerun하여 상태 반영 (필수는 아니지만 꼬임 방지)
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # 사용자 입력
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        st.rerun()
    
    # 샘플 질문
    st.markdown("---")
    st.markdown("#### 💡 이런 질문을 해보세요!")
    
    sample_questions = [
        "금리 인상이 내 주식 포트폴리오에 미치는 영향은?",
        "HBM이란 무엇이고 어떤 한국 기업이 수혜받을까요?",
        "배당주 투자 시 PER과 ROE를 어떻게 활용하나요?",
        "환율이 오를 때 달러 ETF 투자해도 괜찮나요?",
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

if __name__ == "__main__":
    main()
