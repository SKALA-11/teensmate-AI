"""
KIS WebSocket Client (Thread-Safe)

한국투자증권 WebSocket 클라이언트
실시간 주가 데이터 수신 - 스레드 기반 실행
"""

import json
import time
import asyncio
import threading
from typing import List, Optional
from base64 import b64decode

import requests
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from stock.models import Stock
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


# KIS API URLs (모의투자/운영 전환 가능)
KIS_BASE_URL = "https://openapivts.koreainvestment.com:29443"
KIS_WS_URL = settings.kis_ws_url


class KISWebSocketClient:
    """
    한국투자증권 WebSocket 클라이언트 (스레드 안전)

    별도 스레드에서 asyncio 이벤트 루프를 실행하여
    Streamlit과 병행 동작합니다.
    """

    def __init__(self, stocks: List[Stock]):
        """
        Args:
            stocks: 구독할 주식 리스트 (공유 객체 — 가격 직접 업데이트됨)
        """
        self._stocks = stocks

        # KIS API 키
        self._app_key = settings.kis_app_key
        self._secret_key = settings.kis_app_secret

        # 상태
        self._connect_key: Optional[str] = None
        self.is_connected: bool = False
        self._stop_event = threading.Event()

        # 백그라운드 스레드
        self._thread: Optional[threading.Thread] = None

        logger.info(f"KISWebSocketClient 초기화: {len(stocks)}개 종목")

    def _aes_cbc_base64_dec(self, key: str, iv: str, cipher_text: str) -> str:
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        return unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size).decode("utf-8")

    def _get_approval_key(self):
        """WebSocket 접속키 발급"""
        url = f"{KIS_BASE_URL}/oauth2/Approval"
        headers = {"Content-Type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self._app_key,
            "secretkey": self._secret_key,
        }
        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        response.raise_for_status()
        self._connect_key = response.json()["approval_key"]
        logger.info(f"접속키 발급 완료: {self._connect_key[:10]}...")

    def _process_price_update(self, data: str):
        """주가 체결 데이터 처리"""
        parts = data.split("^")
        if len(parts) < 3:
            return

        stock_code = parts[0]   # 종목코드
        current_price = int(parts[2])  # 현재가

        stock = next((s for s in self._stocks if s.code == stock_code), None)
        if stock:
            stock.update_price(current_price)
            logger.debug(f"주가 업데이트: {stock.name} ({stock_code}) = {current_price:,}원")

    async def _run_async(self):
        """비동기 WebSocket 루프"""
        try:
            self._get_approval_key()
        except Exception as e:
            logger.error(f"접속키 발급 실패: {e}")
            self.is_connected = False
            return

        logger.info("WebSocket 연결 시작...")

        while not self._stop_event.is_set():
            try:
                async with websockets.connect(KIS_WS_URL, ping_interval=None) as ws:
                    self.is_connected = True
                    logger.info("WebSocket 연결 성공")

                    # 종목별 구독 요청
                    for stock in self._stocks:
                        subscribe_msg = json.dumps({
                            "header": {
                                "approval_key": self._connect_key,
                                "custtype": "P",
                                "tr_type": "1",
                                "content-type": "utf-8",
                            },
                            "body": {
                                "input": {
                                    "tr_id": "H0STCNT0",
                                    "tr_key": stock.code,
                                }
                            },
                        })
                        await ws.send(subscribe_msg)
                        logger.info(f"구독 요청: {stock.name} ({stock.code})")

                    await asyncio.sleep(0.5)

                    # 메시지 수신 루프
                    while not self._stop_event.is_set():
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        except asyncio.TimeoutError:
                            continue

                        # 실시간 체결 데이터
                        if message[0] in ["0", "1"]:
                            parts = message.split("|")
                            if message[0] == "0" and len(parts) >= 4:
                                self._process_price_update(parts[3])

                        # JSON 메시지 (응답, PINGPONG 등)
                        else:
                            try:
                                json_msg = json.loads(message)
                                tr_id = json_msg.get("header", {}).get("tr_id", "")

                                if tr_id == "PINGPONG":
                                    await ws.pong(message)
                                    logger.debug("PONG 전송")
                                else:
                                    body = json_msg.get("body", {})
                                    rt_cd = body.get("rt_cd")
                                    msg = body.get("msg1", "")
                                    if rt_cd == "0":
                                        logger.info(f"정상 응답: {msg}")
                                    elif rt_cd == "1":
                                        logger.error(f"오류 응답: {msg}")
                            except json.JSONDecodeError:
                                pass

            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket 오류: {e}")
                self.is_connected = False
                if not self._stop_event.is_set():
                    logger.info("재연결 대기 중 (3초)...")
                    await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"예상치 못한 오류: {e}", exc_info=True)
                self.is_connected = False
                if not self._stop_event.is_set():
                    await asyncio.sleep(3)

        self.is_connected = False
        logger.info("WebSocket 루프 종료")

    def _thread_worker(self):
        """별도 스레드에서 asyncio 이벤트 루프 실행"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run_async())
        finally:
            loop.close()

    def start(self):
        """백그라운드 스레드에서 WebSocket 클라이언트 시작"""
        if self._thread and self._thread.is_alive():
            logger.warning("이미 실행 중입니다.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._thread_worker, daemon=True)
        self._thread.start()
        logger.info("KIS WebSocket 백그라운드 스레드 시작")

    def stop(self):
        """WebSocket 클라이언트 중지"""
        self._stop_event.set()
        self.is_connected = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("KIS WebSocket 클라이언트 중지")
