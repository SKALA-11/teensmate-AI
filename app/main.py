# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api.routes import kis_ws

# app = FastAPI(
#     title="한국투자증권 실시간 주가 조회 API (모의투자)",
#     version="1.0.0",
#     description=(
#         "모의투자 환경에서 한국투자증권 API를 통해 주가 정보를 조회하고, "
#         "WebSocket을 통한 실시간 업데이트도 제공합니다.\n\n"
#         "각 API 엔드포인트에 대한 자세한 설명은 Swagger UI (/docs) 및 ReDoc (/redoc)를 참고하세요."
#     ),
#     docs_url="/docs",          # Swagger UI 경로 (기본값)
#     redoc_url="/redoc",        # ReDoc 문서 경로 (기본값)
#     openapi_url="/openapi.json"  # OpenAPI 스펙 경로
# )

# origins = [
#     "http://localhost:3000",  # Vue 개발 서버 (필요 시 추가)
#     "http://localhost:8080"
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# app.include_router(kis_ws.router)
