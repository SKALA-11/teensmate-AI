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
    
    # Azure OpenAI 설정
    aoai_endpoint: str = Field(..., env="AOAI_ENDPOINT")
    aoai_api_key: str = Field(..., env="AOAI_API_KEY")
    aoai_deploy_gpt4o_mini: str = Field(..., env="AOAI_DEPLOY_GPT4O_MINI")
    aoai_deploy_gpt4o: str = Field(..., env="AOAI_DEPLOY_GPT4O")
    aoai_deploy_embed_3_large: str = Field(..., env="AOAI_DEPLOY_EMBED_3_LARGE")
    aoai_deploy_embed_3_small: str = Field(..., env="AOAI_DEPLOY_EMBED_3_SMALL")
    aoai_deploy_embed_ada: str = Field(..., env="AOAI_DEPLOY_EMBED_ADA")
    
    # OpenAI 호환성 (기존 코드와 호환)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Naver API (뉴스 크롤링용)
    naver_client_id: Optional[str] = Field(None, env="NAVER_CLIENT_ID")
    naver_client_secret: Optional[str] = Field(None, env="NAVER_CLIENT_SECRET")
    
    # 한국투자증권 API
    kis_app_key: Optional[str] = Field(None, env="KIS_APP_KEY")
    kis_app_secret: Optional[str] = Field(None, env="KIS_APP_SECRET")
    
    # Vector Database 설정
    chroma_persist_dir: str = Field("./crawler", env="CHROMA_PERSIST_DIR")
    chroma_edu_db: str = Field("./crawler/chroma_edu_db", env="CHROMA_EDU_DB")
    chroma_news_db: str = Field("./crawler/chroma_news_db", env="CHROMA_NEWS_DB")
    chroma_report_db: str = Field("./crawler/chroma_report_db", env="CHROMA_REPORT_DB")
    chroma_valchain_db: str = Field("./crawler/chroma_valchain_db", env="CHROMA_VALCHAIN_DB")
    
    # LLM 설정
    default_model: str = Field("gpt-4o", env="DEFAULT_MODEL")
    default_temperature: float = Field(0.2, env="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(2048, env="DEFAULT_MAX_TOKENS")
    
    # 애플리케이션 설정
    app_name: str = Field("TeensMate-AI", env="APP_NAME")
    app_version: str = Field("2.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # FastAPI 설정
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_reload: bool = Field(True, env="API_RELOAD")
    
    # Streamlit 설정
    streamlit_port: int = Field(8501, env="STREAMLIT_PORT")
    
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
