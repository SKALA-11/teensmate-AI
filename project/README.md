# NewMate AI 🏦💡

> 청소년을 위한 AI 경제 교육 챗봇 - LangChain/LangGraph Multi-Agent RAG System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129.0-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43.2-red.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2.10-yellow.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.55-orange.svg)](https://www.langchain.com/langgraph)

## 📖 소개

NewMate AI는 청소년이 경제, 투자, 금융을 쉽게 이해할 수 있도록 돕는 AI 기반 교육 챗봇입니다. LangChain/LangGraph를 사용한 Multi-Agent 시스템으로 구현되어 있으며, RAG (Retrieval-Augmented Generation)를 통해 정확하고 최신의 경제 정보를 제공합니다.

### 주요 기능

- 💬 **AI 채팅**: 경제 용어, 투자 개념을 쉽게 설명
- 🏭 **밸류체인 분석**: 제품/산업의 가치사슬 분석, 이미지 인식 지원
- 📊 **주식 시뮬레이션**: 한국투자증권 API 기반 실시간 주식 데이터 체험
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
   cd teensmate-AI/project
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

#### 로컬 실행 (권장 - run_dev.sh 사용)

```bash
# project/ 디렉토리에서 실행
./run_dev.sh
# Backend:  http://localhost:8000/docs
# Frontend: http://localhost:8501
```

#### 개별 실행

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
./run_docker.sh
# 또는
docker-compose up --build
# Backend:  http://localhost:8000
# Frontend: http://localhost:8501
```

## ⚙️ 환경변수

`.env` 파일에 다음 환경변수를 설정하세요 (`.env.example` 참고):

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

### 선택 (주식 시뮬레이션)

```bash
# 한국투자증권 API (주식 실시간 데이터)
KIS_HTS_ID=your-hts-id
KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret

# Naver API (뉴스 크롤링)
NAVER_CLIENT_ID=your-client-id
NAVER_CLIENT_SECRET=your-client-secret
```

## 📚 프로젝트 구조

```
project/
├── .env                     # 환경변수 (git 제외)
├── .env.example             # 환경변수 샘플
├── .python-version          # Python 버전 고정 (3.12)
├── .streamlit/
│   └── config.toml          # Streamlit 설정
├── pyproject.toml           # 프로젝트 메타데이터 & 의존성
├── uv.lock                  # 의존성 잠금 파일
├── run_dev.sh               # 로컬 개발 실행 스크립트
├── run_docker.sh            # Docker 실행 스크립트
├── Dockerfile               # Docker 이미지 빌드
├── docker-compose.yml       # Docker Compose 설정
│
├── config/                  # 환경 설정
│   ├── __init__.py
│   ├── settings.py          # Pydantic Settings (환경변수 로드)
│   └── logging.py           # 로깅 설정
│
├── prompts/                 # AI 프롬프트 템플릿
│   ├── __init__.py
│   ├── base.py
│   ├── economic_educator.py
│   ├── investment_analyst.py
│   └── value_chain_analyst.py
│
├── agents/                  # LangGraph 에이전트
│   ├── __init__.py
│   ├── orchestrator.py      # Multi-Agent 오케스트레이터 (LangGraph)
│   ├── router.py            # 쿼리 라우터
│   ├── education.py         # 경제 교육 에이전트
│   ├── news.py              # 뉴스 에이전트
│   ├── report.py            # 리포트 에이전트
│   ├── value_chain.py       # 밸류체인 분석 에이전트
│   └── llm.py               # LLM 클라이언트 설정
│
├── tools/                   # ReAct 도구
│   ├── __init__.py
│   ├── vector_search.py     # ChromaDB 벡터 검색 도구
│   └── image_analyzer.py    # 이미지 분석 도구 (Azure OpenAI Vision)
│
├── rag/                     # RAG 컴포넌트
│   ├── __init__.py
│   ├── vector_store.py      # ChromaDB 관리 (읽기 전용)
│   ├── retriever.py         # 하이브리드 검색 (BM25 + Vector)
│   ├── chunker.py           # 텍스트 청킹
│   └── embeddings.py        # 임베딩 (Azure OpenAI)
│
├── stock/                   # 주식 데이터 모듈
│   ├── __init__.py
│   ├── models.py            # 주식 데이터 모델 (Pydantic)
│   └── kis_client.py        # 한국투자증권 API 클라이언트
│
├── backend/                 # FastAPI 백엔드
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   └── routers/
│       ├── __init__.py
│       ├── chat.py          # 채팅 API 라우터
│       └── health.py        # 헬스체크 라우터
│
├── frontend/                # Streamlit 프론트엔드
│   ├── __init__.py
│   ├── app.py               # Streamlit 메인 앱 (멀티페이지)
│   ├── components/          # 공용 UI 컴포넌트
│   └── pages/
│       ├── __init__.py
│       ├── chat.py          # AI 채팅 페이지
│       ├── value_chain.py   # 밸류체인 분석 페이지
│       └── stock_simulation.py  # 주식 시뮬레이션 페이지
│
└── logs/                    # 애플리케이션 로그
```

## 🎯 주요 기술 스택

| 분류 | 기술 |
|------|------|
| **LLM** | Azure OpenAI (GPT-4o, GPT-4o-mini) |
| **Agent Framework** | LangChain, LangGraph |
| **Vector DB** | ChromaDB (읽기 전용) |
| **검색** | BM25 + Vector Hybrid Search |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **주식 데이터** | 한국투자증권(KIS) API |
| **패키지 관리** | uv |
| **배포** | Docker, Docker Compose |

## 🔒 데이터 보호

**기존 ChromaDB는 읽기 전용으로 보호됩니다:**
- `VectorStoreManager`는 기본적으로 `read_only=True`
- `add_documents()` 호출 시 `PermissionError` 발생
- 기존 데이터(`chroma_edu_db`, `chroma_valchain_db` 등)는 안전하게 보존

## 📖 API 문서

Backend 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/chat` | 일반 채팅 |
| `POST` | `/api/v1/chat/stream` | 스트리밍 채팅 |
| `POST` | `/api/v1/chat/image` | 이미지 포함 채팅 |
| `DELETE` | `/api/v1/chat/session/{id}` | 세션 초기화 |
| `GET` | `/api/v1/health` | 헬스 체크 |

## 🤝 기여

이 프로젝트는 청소년 경제 교육을 위한 오픈소스 프로젝트입니다. 기여는 언제나 환영합니다!

## 📄 라이선스

MIT License

---

Made with ❤️ for teenagers learning economics