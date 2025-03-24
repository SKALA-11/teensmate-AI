# from fastapi import APIRouter, HTTPException
# import asyncio
# from app.services import kis_ws_service
# from app.core.config import settings

# router = APIRouter(prefix="/api/kis-ws", tags=["kis_ws"])


# @router.post("/connect")
# async def connect_kis_ws(stockcode: str = None, htsid: str = None):
#     """
#     Vue에서 모의투자용 KIS 웹소켓 연결을 트리거합니다.
#     요청 예시 (JSON):
#     {
#         "stockcode": "012630",
#         "htsid": "YOUR_HTS_ID"
#     }
#     """
#     try:
#         result = await asyncio.to_thread(
#             kis_ws_service.run_kis_websocket,
#             settings.KIS_APP_KEY, settings.KIS_APP_SECRET, stockcode, htsid
#         )
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))