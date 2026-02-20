"""
File Utilities

파일, 이미지 처리 등 공통적인 유틸리티 기능을 제공합니다.
"""

import base64
from pathlib import Path
from typing import Optional
from config.logging import get_logger

logger = get_logger(__name__)

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    이미지 파일을 Base64로 인코딩합니다.
    
    Args:
        image_path: 이미지 파일 경로
        
    Returns:
        Base64 인코딩된 문자열, 실패 시 None
    """
    try:
        path = Path(image_path)
        if not path.exists():
            logger.error(f"이미지를 찾을 수 없습니다: {image_path}")
            return None
            
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
    except Exception as e:
        logger.error(f"이미지 인코딩 중 오류 발생: {e}", exc_info=True)
        return None

def safe_remove_file(file_path: str) -> bool:
    """
    파일을 안전하게 삭제합니다.
    
    Args:
        file_path: 삭제할 파일 경로
        
    Returns:
        삭제 성공 여부 (파일이 없어도 True)
    """
    try:
        if not file_path:
            return True
            
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug(f"임시 파일 삭제 완료: {file_path}")
        return True
    except Exception as e:
        logger.error(f"파일 삭제 오류 ({file_path}): {e}")
        return False
