"""
Chat Router

채팅 API 엔드포인트
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json

from agents.orchestrator import AgentOrchestrator
from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 전역 오케스트레이터 (싱글톤)
orchestrator = AgentOrchestrator(enable_memory=True)


class ChatRequest(BaseModel):
    """채팅 요청"""
    query: str = Field(..., description="사용자 질문", min_length=1)
    session_id: str = Field(default="default", description="세션 ID")
    stream: bool = Field(default=False, description="스트리밍 응답 여부")


class ChatResponse(BaseModel):
    """채팅 응답"""
    answer: str = Field(..., description="AI 답변")
    session_id: str = Field(..., description="세션 ID")


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="채팅",
    description="사용자 질문에 대해 Multi-Agent가 답변합니다."
)
async def chat(request: ChatRequest):
    """
    채팅 API
    
    - query: 사용자 질문
    - session_id: 세션 ID (대화 히스토리 유지)
    - stream: 스트리밍 응답 여부 (기본: False)
    """
    logger.info(f"채팅 요청: {request.query} (session: {request.session_id})")
    
    try:
        # 오케스트레이터 실행
        answer = orchestrator.run(
            query=request.query,
            session_id=request.session_id
        )
        
        return ChatResponse(
            answer=answer,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"채팅 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="답변 생성 중 통신 또는 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.post(
    "/chat/stream",
    summary="스트리밍 채팅",
    description="스트리밍 방식으로 답변을 생성합니다."
)
async def chat_stream(request: ChatRequest):
    """
    스트리밍 채팅 API
    
    Server-Sent Events (SSE) 방식으로 답변을 스트리밍합니다.
    """
    logger.info(f"스트리밍 채팅 요청: {request.query} (session: {request.session_id})")
    
    async def generate():
        """스트리밍 생성기"""
        try:
            # 오케스트레이터의 스트리밍 제너레이터 사용
            async for chunk_text in orchestrator.stream(
                query=request.query,
                session_id=request.session_id
            ):
                chunk = {
                    "type": "text",
                    "content": chunk_text
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            # 완료 신호
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"스트리밍 오류: {e}", exc_info=True)
            error_chunk = {
                "type": "error",
                "content": "답변 스트리밍 중 통신 또는 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post(
    "/chat/image",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="이미지 포함 채팅",
    description="이미지와 함께 질문합니다 (밸류체인 분석 등)."
)
async def chat_with_image(
    query: str = Form(..., description="사용자 질문"),
    session_id: str = Form(default="default", description="세션 ID"),
    image: UploadFile = File(..., description="이미지 파일")
):
    """
    이미지 포함 채팅 API
    
    - query: 사용자 질문
    - session_id: 세션 ID
    - image: 이미지 파일 (JPEG, PNG 등)
    """
    logger.info(f"이미지 채팅 요청: {query} (session: {session_id})")
    
    try:
        # 파일 타입 검증
        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (JPEG/PNG만 허용)")
            
        # 파일 크기 검증 (20MB 제한)
        MAX_FILE_SIZE = 20 * 1024 * 1024
        file_content = await image.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="파일 크기가 너무 큽니다. 최대 20MB까지 업로드 가능합니다.")
        await image.seek(0)
        
        # 이미지 저장 (임시)
        import tempfile
        import shutil
        from pathlib import Path
        from utils.file_utils import safe_remove_file
        
        suffix = Path(image.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(image.file, tmp_file)
            image_path = tmp_file.name
        
        # 오케스트레이터 실행
        answer = orchestrator.run(
            query=query,
            image_path=image_path,
            session_id=session_id
        )
        
        # 임시 파일 삭제
        safe_remove_file(image_path)
        
        return ChatResponse(
            answer=answer,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"이미지 채팅 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 분석 및 답변 생성 중 통신 또는 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.delete(
    "/chat/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="세션 초기화",
    description="특정 세션의 대화 히스토리를 삭제합니다."
)
async def clear_session(session_id: str):
    """
    세션 초기화
    
    대화 히스토리를 삭제합니다.
    """
    logger.info(f"세션 초기화: {session_id}")
    
    try:
        orchestrator.clear_memory(session_id=session_id)
        return None
        
    except Exception as e:
        logger.error(f"세션 초기화 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 초기화 중 통신 또는 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
