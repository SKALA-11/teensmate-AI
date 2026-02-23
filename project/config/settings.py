"""
환경 설정 관리 모듈

Pydantic Settings를 사용하여 환경변수를 타입 안전하게 관리합니다.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


from functools import lru_cache

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
    kis_ws_url: str = Field(default="ws://ops.koreainvestment.com:31000/tryitout", env="KIS_WS_URL")
    
    # ===== 하드코딩된 기본값 (환경변수 불필요) =====
    
    # OpenAI 호환성 (기존 코드와 호환)
    openai_api_key: Optional[str] = None
    
    # Vector Database 설정 (환경변수 또는 기본 경로 사용)
    chroma_persist_dir: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIR")
    chroma_edu_db: str = Field(default="./data/chroma/edu_db", env="CHROMA_EDU_DB")
    chroma_news_db: str = Field(default="./data/chroma/news_db", env="CHROMA_NEWS_DB")
    chroma_report_db: str = Field(default="./data/chroma/report_db", env="CHROMA_REPORT_DB")
    chroma_valchain_db: str = Field(default="./data/chroma/valchain_db", env="CHROMA_VALCHAIN_DB")
    
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
    cors_allow_origins: str = Field(default="http://localhost:8501,http://127.0.0.1:8501", env="CORS_ALLOW_ORIGINS")
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


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스를 반환합니다."""
    return Settings()

# 기존 호환성 유지 및 lazy-load를 위한 SettingsProxy
class SettingsProxy:
    def __getattr__(self, name):
        return getattr(get_settings(), name)

settings = SettingsProxy()




