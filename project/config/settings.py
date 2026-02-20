"""
환경 설정 관리 모듈

Pydantic Settings를 사용하여 환경변수를 타입 안전하게 관리합니다.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # ===== 환경변수에서 로드하는 필수 설정 =====
    
    # Azure OpenAI 설정
    aoai_endpoint: str = Field(..., env="AOAI_ENDPOINT")
    aoai_api_key: str = Field(..., env="AOAI_API_KEY")
    aoai_deploy_gpt4o_mini: str = Field(..., env="AOAI_DEPLOY_GPT4O_MINI")
    aoai_deploy_gpt4o: str = Field(..., env="AOAI_DEPLOY_GPT4O")
    aoai_deploy_embed_3_large: str = Field(..., env="AOAI_DEPLOY_EMBED_3_LARGE")
    aoai_deploy_embed_3_small: str = Field(..., env="AOAI_DEPLOY_EMBED_3_SMALL")
    aoai_deploy_embed_ada: str = Field(..., env="AOAI_DEPLOY_EMBED_ADA")
    
    # Naver API (필수)
    naver_client_id: str = Field(..., env="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(..., env="NAVER_CLIENT_SECRET")
    
    # 한국투자증권 API (필수)
    kis_hts_id: str = Field(..., env="KIS_HTS_ID")
    kis_app_key: str = Field(..., env="KIS_APP_KEY")
    kis_app_secret: str = Field(..., env="KIS_APP_SECRET")
    
    # ===== 하드코딩된 기본값 (환경변수 불필요) =====
    
    # OpenAI 호환성 (기존 코드와 호환)
    openai_api_key: Optional[str] = None
    
    # Vector Database 설정 (읽기 전용, 기존 경로 유지)
    chroma_persist_dir: str = "../crawler"
    chroma_edu_db: str = "../crawler/chroma_edu_db"
    chroma_news_db: str = "../crawler/chroma_news_db"
    chroma_report_db: str = "../crawler/chroma_report_db"
    chroma_valchain_db: str = "../crawler/chroma_valchain_db"
    
    # LLM 설정
    default_model: str = "gpt-4o"
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    
    # 애플리케이션 설정
    app_name: str = "NewMate AI"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # Backend 설정
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True
    
    # Streamlit 설정
    streamlit_host: str = "0.0.0.0"
    streamlit_port: int = 8501
    
    @validator("openai_api_key", always=True)
    def set_openai_api_key(cls, v, values):
        """AOAI_API_KEY를 OPENAI_API_KEY로도 사용"""
        if v is None and "aoai_api_key" in values:
            return values["aoai_api_key"]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스를 반환합니다."""
    return settings


# OpenAI 환경변수 설정 (기존 코드 호환성)
os.environ["OPENAI_API_KEY"] = settings.openai_api_key or settings.aoai_api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = settings.aoai_endpoint
os.environ["AZURE_OPENAI_API_KEY"] = settings.aoai_api_key

