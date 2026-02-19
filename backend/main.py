"""
FastAPI Main Application

Multi-Agent RAG 시스템 API 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import chat, health
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="NewMate AI API",
    description="사회 초년생을 위한 경제·금융 Multi-Agent RAG 시스템",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

logger.info("FastAPI 앱 초기화 완료")


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("NewMate AI API 서버 시작")
    logger.info(f"Docs: http://{settings.backend_host}:{settings.backend_port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행"""
    logger.info("NewMate AI API 서버 종료")
