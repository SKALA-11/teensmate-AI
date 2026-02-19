# TeensMate AI 프로젝트 컨텍스트 가이드

이 문서는 TeensMate AI 프로젝트의 구조, 아키텍처, 실행 방법 및 현재 상태를 요약하여, 향후 개발 세션에서 AI 에이전트가 참고할 수 있도록 작성되었습니다.

## 1. 프로젝트 개요

**TeensMate AI**는 청소년을 위한 AI 기반 경제 교육 챗봇입니다. 어려운 경제 개념, 투자 상식, 기업 분석 등을 청소년의 눈높이에 맞춰 쉽고 재미있게 설명하는 것을 목표로 합니다.

- **프로젝트 명**: `teensmate-AI` (SKALA-11)
- **주요 기능**:
  - 💬 **AI 채팅**: 경제 용어 및 개념 설명
  - 🏭 **밸류체인 분석**: 제품/산업의 가치사슬 분석 (이미지 인식 지원)
  - 📈 **주식 시뮬레이션**: 가상 투자 체험 (현재 개발 중)
  - 🔍 **RAG 검색**: 교육 자료, 뉴스, 리포트 기반의 신뢰성 있는 정보 제공

## 2. 기술 스택

### 백엔드 (Backend)
- **Language**: Python 3.12+
- **Framework**: FastAPI (REST API), Uvicorn (Server)
- **Package Manager**: `uv` (빠른 패키지 설치 및 관리)

### 프론트엔드 (Frontend)
- **Framework**: Streamlit
- **UI Components**: 채팅 인터페이스, 사이드바 네비게이션, 데이터 시각화 (Plotly 등)

### AI & 데이터 (AI Engine)
- **LLM/Embeddings**: Azure OpenAI Service (GPT-4o, GPT-4o-mini, Text-Embedding-3)
- **Orchestration**: LangChain, **LangGraph** (Multi-Agent 워크플로우 관리)
- **Vector DB**: ChromaDB (현재 읽기 전용 모드로 사전 인덱싱된 데이터 사용)
- **Search**: Hybrid Retrieval (BM25 + Vector Similarity)

## 3. 프로젝트 구조 (Directory Structure)

```bash
teensmate-AI/
├── .env                 # 환경 변수 (API 키 등)
├── run_dev.sh           # 통합 실행 스크립트 (Backend + Frontend)
├── pyproject.toml       # 프로젝트 의존성 설정 (uv)
├── agents/              # LangGraph 에이전트 로직
│   ├── orchestrator.py  # 에이전트 조율 및 워크플로우 정의 (중요)
│   ├── router.py        # 사용자 질문 의도 분류
│   ├── education.py     # 경제 교육 에이전트
│   ├── news.py          # 뉴스 분석 에이전트
│   ├── report.py        # 기업 리포트 분석 에이전트
│   └── value_chain.py   # 밸류체인 분석 에이전트
├── backend/             # FastAPI 서버
│   ├── main.py          # 앱 진입점
│   └── routers/         # API 라우터
├── frontend/            # Streamlit UI
│   ├── app.py           # 메인 앱 진입점 (사이드바, 라우팅)
│   └── pages/           # 개별 페이지 (chat, value_chain, stock_simulation)
├── rag/                 # RAG 관련 모듈
│   ├── vector_store.py  # ChromaDB 핸들러
│   └── retriever.py     # 검색 로직
├── tools/               # 유틸리티 도구
│   └── image_analyzer.py # 이미지 분석 도구
└── data/                # 데이터 처리 및 크롤러
```

## 4. 아키텍처 및 데이터 흐름

### Multi-Agent Workflow (LangGraph)
사용자의 질문은 다음과 같은 흐름으로 처리됩니다:

1.  **Router**: 질문의 의도를 분석하여 적절한 에이전트(Education, News, Report, Value Chain)로 분류합니다.
2.  **Specialized Agents**: 선택된 에이전트가 RAG를 통해 관련 정보를 검색하고 답변을 생성합니다.
3.  **Synthesizer**: (필요시) 여러 에이전트의 결과를 종합하여 최종 답변을 구성합니다.
4.  **Backend/Frontend**: FastAPI를 통해 결과를 반환하고, Streamlit UI에 표시합니다.

### 실행 방법

프로젝트 루트에서 스크립트를 사용하여 실행합니다:

```bash
# Backend와 Frontend 동시 실행
./run_dev.sh
# 메뉴에서 3번 선택
```

- **Backend Docs**: http://localhost:8000/docs
- **Web UI**: http://localhost:8501

## 5. 주요 개발 컨벤션 및 규칙

1.  **언어**: 모든 출력 및 주석은 **한국어(Korean)**를 기본으로 합니다.
2.  **패키지 관리**: `uv`를 사용합니다. (`uv add <package>`, `uv sync`)
3.  **환경 변수**: `.env` 파일에 Azure OpenAI 키(`AOAI_...`)가 설정되어 있어야 합니다.
4.  **UI 디자인**: Streamlit의 기본 컴포넌트를 활용하되, `st.set_page_config` 등으로 일관된 테마를 유지합니다.
5.  **파일 경로**: 항상 프로젝트 루트 기준의 절대 경로 또는 상대 경로를 명확히 사용합니다.

## 6. 최근 변경 사항 및 상태 (2025-02 기준)

- **인증(Auth) 수정**: Azure OpenAI API 키 인증 오류 해결 및 `AuthenticationError` 수정 완료.
- **UI 개선**:
    - `stock_simulation.py` 페이지 레이아웃 수정 ("페이지 선택" 제거, 타이틀 상단 배치).
    - `use_container_width` 파라미터 경고 해결 (→ `width` 사용).
- **빈 페이지 오류 수정**: Streamlit 라우팅 로직 수정으로 빈 화면 문제 해결.
- **크롤러 통합**: 주식 및 뉴스 데이터 실시간 확보를 위한 크롤러 모듈(`crawler/`, `stock/`) 작업 진행 중.

## 7. 참고 사항 for AI Agents

이 프로젝트를 수정하거나 분석할 때 다음 파일을 우선적으로 확인하세요:
- **로직 수정**: `agents/*.py` (특히 `orchestrator.py`의 워크플로우 정의)
- **UI 수정**: `frontend/app.py` 및 `frontend/pages/*.py`
- **의존성 추가**: `pyproject.toml`
- **에러 디버깅**: `logs/` 디렉토리 (생성된 경우) 또는 터미널 출력 확인
