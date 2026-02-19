"""
Value Chain Analysis Page

밸류체인 분석 페이지
"""

import streamlit as st
from PIL import Image
from agents.orchestrator import AgentOrchestrator


def main():
    """밸류체인 분석 페이지"""
    
    # 오케스트레이터 초기화
    if "vc_orchestrator" not in st.session_state:
        st.session_state.vc_orchestrator = AgentOrchestrator(enable_memory=False)
    
    st.title("🏭 밸류체인 분석")
    st.markdown("제품이나 기업의 가치사슬을 분석하고 한국 기업의 참여를 확인하세요!")
    
    # 입력 방식 선택
    input_method = st.radio(
        "분석 방법 선택",
        ["📝 텍스트 입력", "🖼️ 이미지 업로드"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if input_method == "📝 텍스트 입력":
        # 텍스트 입력
        st.markdown("#### 제품/산업/기업을 입력하세요")
        
        query = st.text_input(
            "예: iPhone, 전기차, 반도체 산업 등",
            placeholder="분석하고 싶은 제품이나 산업을 입력하세요..."
        )
        
        if st.button("🔍 분석 시작", type="primary", width='stretch'):
            if not query:
                st.warning("분석할 대상을 입력해주세요!")
            else:
                with st.spinner("밸류체인을 분석하고 있습니다..."):
                    try:
                        result = st.session_state.vc_orchestrator.run(
                            query=f"{query}의 밸류체인 분석해줘",
                            session_id="value_chain"
                        )
                        
                        st.markdown("### 📊 분석 결과")
                        st.markdown(result)
                        
                    except Exception as e:
                        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    else:
        # 이미지 업로드
        st.markdown("#### 제품 이미지를 업로드하세요")
        
        uploaded_file = st.file_uploader(
            "이미지 선택 (JPEG, PNG)",
            type=["jpg", "jpeg", "png"]
        )
        
        additional_query = st.text_input(
            "추가 질문 (선택)",
            placeholder="예: 어떤 한국 기업이 참여하나요?"
        )
        
        if uploaded_file is not None:
            # 이미지 표시
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                image = Image.open(uploaded_file)
                st.image(image, caption="업로드된 이미지", width='stretch')
            
            if st.button("🔍 이미지 분석 시작", type="primary", width='stretch'):
                with st.spinner("이미지를 분석하고 밸류체인을 조사하고 있습니다..."):
                    try:
                        # 임시 파일로 저장
                        import tempfile
                        from pathlib import Path
                        
                        suffix = Path(uploaded_file.name).suffix
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            image_path = tmp_file.name
                        
                        # 밸류체인 분석
                        query_text = additional_query if additional_query else "이 제품의 밸류체인을 분석해줘"
                        
                        result = st.session_state.vc_orchestrator.run(
                            query=query_text,
                            image_path=image_path,
                            session_id="value_chain"
                        )
                        
                        # 임시 파일 삭제
                        Path(image_path).unlink(missing_ok=True)
                        
                        st.markdown("### 📊 분석 결과")
                        st.markdown(result)
                        
                    except Exception as e:
                        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    # 설명 및 예시
    st.markdown("---")
    st.markdown("#### 💡 밸류체인이란?")
    
    with st.expander("자세히 보기"):
        st.markdown("""
        **밸류체인(Value Chain)**은 제품이나 서비스가 만들어지는 전 과정을 의미합니다.
        
        예를 들어, 스마트폰의 밸류체인은:
        1. **원료 채굴**: 리튬, 희토류 등
        2. **부품 제조**: 반도체, 디스플레이, 배터리 등
        3. **조립**: 완제품 조립
        4. **유통**: 판매 및 배송
        5. **서비스**: A/S, 소프트웨어 업데이트
        
        각 단계에 어떤 기업이 참여하는지 분석하면 산업 생태계를 이해할 수 있습니다!
        """)
    
    st.markdown("#### 📝 샘플 질문")
    
    samples = [
        "iPhone",
        "테슬라 전기차",
        "삼성 갤럭시",
        "반도체 산업"
    ]
    
    cols = st.columns(2)
    for i, sample in enumerate(samples):
        with cols[i % 2]:
            if st.button(sample, key=f"vc_sample_{i}", width='stretch'):
                st.session_state.vc_sample = sample
                st.rerun()

if __name__ == "__main__":
    main()
