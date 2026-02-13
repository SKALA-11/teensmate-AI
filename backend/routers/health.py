"""
Health Check Router

서버 상태 체크 API
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime

from config.settings import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health Check 응답"""
    status: str
    timestamp: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="서버 상태를 확인합니다."
)
async def health_check():
    """서버 상태 체크"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0"
    )
