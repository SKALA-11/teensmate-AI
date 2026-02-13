# TeensMate AI 🏦💡

> 청소년을 위한 AI 경제 교육 챗봇 - LangChain/LangGraph Multi-Agent RAG System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129.0-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43.2-red.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2.10-yellow.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.55-orange.svg)](https://www.langchain.com/langgraph)

## 📖 소개

TeensMate AI는 청소년이 경제, 투자, 금융을 쉽게 이해할 수 있도록 돕는 AI 기반 교육 챗봇입니다. LangChain/LangGraph를 사용한 Multi-Agent 시스템으로 구현되어 있으며, RAG (Retrieval-Augmented Generation)를 통해 정확하고 최신의 경제 정보를 제공합니다.

### 주요 기능

- 💬 **AI 채팅**: 경제 용어, 투자 개념을 쉽게 설명
- 🏭 **밸류체인 분석**: 제품/산업의 가치사슬 분석, 이미지 인식 지원
- 📊 **주식 시뮬레이션**: 가상 투자 체험 (향후 추가 예정)
- 🔍 **하이브리드 검색**: BM25 + Vector Similarity 결합
- 🤖 **Multi-Agent**: Router, Education, News, Report, ValueChain 에이전트

## 🏗️ 아키텍처

```
┌─────────────────┐
│  Streamlit UI   │  ← 사용자 인터페이스
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI        │  ← REST API 백엔드
│  Backend        │
└────────┬────────┘
         │
┌────────▼────────────────────────┐
│  LangGraph Orchestrator         │  ← Multi-Agent 워크플로우
│  ┌──────────────────────────┐  │
│  │  Router Agent            │  │  쿼리 분류
│  └──────────┬───────────────┘  │
│             │                   │
│     ┌───────┴────────┐         │
│     ▼                ▼         │
│  Education      Value Chain    │  전문 에이전트
│  News           Report         │
│  └─────┬────────────┘          │
└────────┼───────────────────────┘
         │
┌────────▼────────┐
│  RAG System     │
│  ┌────────────┐ │
│  │ ChromaDB   │ │  ← Vector Store (읽기 전용)
│  │ (edu,      │ │
│  │  news,     │ │
│  │  report,   │ │
│  │  valchain) │ │
│  └────────────┘ │
│  ┌────────────┐ │
│  │ Hybrid     │ │  ← BM25 + Vector 검색
│  │ Retriever  │ │
│  └────────────┘ │
└─────────────────┘
```

## 🚀 빠른 시작

### 필수 요구사항

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (패키지 매니저)
- Azure OpenAI API 키

### 설치

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd teensmate-AI
   ```

2. **환경변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일을 열어 API 키 입력
   ```

3. **의존성 설치**
   ```bash
   uv sync
   ```

### 실행

#### 로컬 실행

```bash
# Backend (FastAPI)
uvicorn backend.main:app --reload
# → http://localhost:8000/docs

# Frontend (Streamlit)
streamlit run frontend/app.py
# → http://localhost:8501
```

#### Docker 실행

```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:8501
```

## ⚙️ 환경변수

`.env` 파일에 다음 환경변수를 설정하세요:

### 필수

```bash
# Azure OpenAI
AOAI_ENDPOINT=https://your-resource.openai.azure.com/
AOAI_API_KEY=your-api-key
AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
AOAI_DEPLOY_GPT4O=gpt-4o
AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large
AOAI_DEPLOY_EMBED_3_SMALL=text-embedding-3-small
AOAI_DEPLOY_EMBED_ADA=text-embedding-ada-002
```

### 선택 (향후 기능)

```bash
# 한국투자증권 API (주식 데이터)
KIS_HTS_ID=your-hts-id
KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret

# Naver API (뉴스 크롤링)
NAVER_CLIENT_ID=your-client-id
NAVER_CLIENT_SECRET=your-client-secret
```

## 📚 프로젝트 구조

```
teensmate-AI/
├── config/              # 환경 설정
│   ├── settings.py      # Pydantic Settings
│   └── logging.py       # 로깅 설정
├── prompts/             # AI 프롬프트 템플릿
│   ├── base.py
│   ├── economic_educator.py
│   ├── investment_analyst.py
│   └── value_chain_analyst.py
├── agents/              # LangGraph 에이전트
│   ├── router.py        # 라우터
│   ├── education.py     # 교육
│   ├── news.py          # 뉴스
│   ├── report.py        # 리포트
│   ├── value_chain.py   # 밸류체인
│   └── orchestrator.py  # 오케스트레이터
├── tools/               # ReAct Tools
│   ├── vector_search.py
│   └── image_analyzer.py
├── rag/                 # RAG 컴포넌트
│   ├── vector_store.py  # ChromaDB 관리
│   ├── retriever.py     # 하이브리드 검색
│   ├── chunker.py       # 텍스트 청킹
│   └── embeddings.py    # 임베딩
├── backend/             # FastAPI
│   ├── main.py
│   └── routers/
│       ├── health.py
│       └── chat.py
├── frontend/            # Streamlit
│   ├── app.py
│   └── pages/
│       ├── chat.py
│       ├── value_chain.py
│       └── stock_simulation.py
├── data/                # 데이터 크롤러 (향후)
│   └── crawlers/
└── crawler/             # 기존 ChromaDB (읽기 전용)
    ├── chroma_edu_db/
    ├── chroma_news_db/
    ├── chroma_report_db/
    └── chroma_valchain_db/
```

## 🎯 주요 기술 스택

- **LLM**: Azure OpenAI (GPT-4o, GPT-4o-mini)
- **Framework**: LangChain, LangGraph
- **Vector DB**: ChromaDB (읽기 전용)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Deployment**: Docker, Docker Compose

## 🔒 데이터 보호

**기존 ChromaDB는 읽기 전용으로 보호됩니다:**
- `VectorStoreManager`는 기본적으로 `read_only=True`
- `add_documents()` 호출 시 `PermissionError` 발생
- 기존 데이터(`chroma_edu_db`, `chroma_valchain_db` 등)는 안전하게 보존

## 📖 API 문서

Backend 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 주요 엔드포인트

- `POST /api/v1/chat` - 일반 채팅
- `POST /api/v1/chat/stream` - 스트리밍 채팅
- `POST /api/v1/chat/image` - 이미지 포함 채팅
- `DELETE /api/v1/chat/session/{id}` - 세션 초기화
- `GET /api/v1/health` - 헬스 체크

## 🤝 기여

이 프로젝트는 청소년 경제 교육을 위한 오픈소스 프로젝트입니다. 기여는 언제나 환영합니다!

## 📄 라이선스

MIT License

---

Made with ❤️ for teenagers learning economics