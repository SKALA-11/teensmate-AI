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
            detail=f"답변 생성 중 오류가 발생했습니다: {str(e)}"
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
            # 실제로는 LLM 스트리밍을 사용해야 하지만
            # 현재는 전체 답변을 생성 후 청크로 전송
            answer = orchestrator.run(
                query=request.query,
                session_id=request.session_id
            )
            
            # 답변을 단어 단위로 스트리밍
            words = answer.split()
            for word in words:
                chunk = {
                    "type": "text",
                    "content": word + " "
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)  # 스트리밍 효과
            
            # 완료 신호
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"스트리밍 오류: {e}", exc_info=True)
            error_chunk = {
                "type": "error",
                "content": str(e)
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
        # 이미지 저장 (임시)
        import tempfile
        import shutil
        from pathlib import Path
        
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
        Path(image_path).unlink(missing_ok=True)
        
        return ChatResponse(
            answer=answer,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"이미지 채팅 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"답변 생성 중 오류가 발생했습니다: {str(e)}"
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
        orchestrator.clear_memory()
        return None
        
    except Exception as e:
        logger.error(f"세션 초기화 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 초기화 중 오류가 발생했습니다: {str(e)}"
        )
