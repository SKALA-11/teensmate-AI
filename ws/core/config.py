from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 한국투자증권 API 관련 설정
    KIS_APP_KEY: str
    KIS_APP_SECRET: str
    
    # 모의투자용 REST API 기본 URL (포트 29443 사용)
    KIS_BASE_URL: str = "https://openapivts.koreainvestment.com:29443"
    KIS_BASE_URL_WS: str = "https://openapivts.koreainvestment.com:29443"
    
    # WebSocket URL (모의투자)
    KIS_WS_BASE_URL: str = "ws://ops.koreainvestment.com:31000/tryitout"
    
    # 거래 ID: ahdml 투자용
    KIS_TR_ID: str = "VTTC01010100"
    
    KIS_HTS_ID: str

    class Config:
        env_file = "env/.env"
        env_file_encoding = 'utf-8'

settings = Settings()
