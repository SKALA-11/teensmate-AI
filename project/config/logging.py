"""
로깅 설정 모듈

구조화된 로깅을 제공합니다.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console

from config.settings import settings


# Rich Console 설정
console = Console()


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    enable_file_logging: bool = True
) -> logging.Logger:
    """
    로깅을 설정합니다.
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로
        enable_file_logging: 파일 로깅 활성화 여부
        
    Returns:
        설정된 루트 로거
    """
    level = log_level or settings.log_level
    log_level_num = getattr(logging, level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_num)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Rich 콘솔 핸들러 (개발 환경)
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True if settings.debug else False,
        show_time=True,
        show_path=True if settings.debug else False
    )
    console_handler.setLevel(log_level_num)
    console_formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (프로덕션 환경)
    if enable_file_logging:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file_path = log_file or log_dir / f"{settings.app_name.lower()}.log"
        
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level_num)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거를 반환합니다.
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        설정된 로거
    """
    return logging.getLogger(name)


# 애플리케이션 시작 시 로깅 설정
setup_logging()
