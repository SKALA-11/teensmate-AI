"""
KIS WebSocket Client

한국투자증권 WebSocket 클라이언트
실시간 주가 데이터 수신
"""

import json
import asyncio
from typing import List, Callable, Optional
from base64 import b64decode

import requests
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from stock.models import Stock
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


# KIS API URLs
KIS_BASE_URL = "https://openapivts.koreainvestment.com:29443"
KIS_WS_URL = "ws://ops.koreainvestment.com:31000/tryitout"


class KISWebSocketClient:
    """
    한국투자증권 WebSocket 클라이언트
    
    실시간 주가 데이터를 수신하고 Stock 객체를 업데이트합니다.
    """
    
    def __init__(
        self,
        stocks: List[Stock],
        on_price_update: Optional[Callable[[Stock, int], None]] = None
    ):
        """
        Args:
            stocks: 구독할 주식 리스트
            on_price_update:  가격 업데이트 콜백 (stock, new_price)
        """
        self.stocks = stocks
        self.on_price_update = on_price_update
        
        # KIS API 키
        self.app_key = settings.kis_app_key
        self.secret_key = settings.kis_app_secret
        self.hts_id = settings.kis_hts_id
        
        # WebSocket 접속키
        self.connect_key: Optional[str] = None
        
        # AES 암호화 키 (체결통보용)
        self.aes_key: Optional[str] = None
        self.aes_iv: Optional[str] = None
        
        logger.info(
            f"KISWebSocketClient 초기화: {len(stocks)}개 종목 구독 준비"
        )
    
    def _aes_cbc_base64_dec(
        self, 
        key: str, 
        iv: str, 
        cipher_text: str
    ) -> str:
        """
        AES256 복호화
        
        Args:
            key: AES 키
            iv: Initial Vector
            cipher_text: 암호화된 텍스트
            
        Returns:
            복호화된 텍스트
        """
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        decrypted = cipher.decrypt(b64decode(cipher_text))
        return unpad(decrypted, AES.block_size).decode("utf-8")
    
    def _get_approval_key(self):
        """
        WebSocket 접속키 발급
        
        Raises:
            Exception: API 호출 실패 시
        """
        url = f"{KIS_BASE_URL}/oauth2/Approval"
        headers = {"Content-Type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            response.raise_for_status()
            self.connect_key = response.json()["approval_key"]
            logger.info(f"접속키 발급 완료: {self.connect_key[:10]}...")
        except Exception as e:
            logger.error(f"접속키 발급 실패: {e}")
            raise
    
    def _process_price_update(self, data: str):
        """
        주가 체결 데이터 처리
        
        Args:
            data: 체결 데이터 문자열 (^로 구분)
        """
        parts = data.split("^")
        
        if len(parts) < 3:
            logger.warning(f"잘못된 데이터 형식: {data}")
            return
        
        stock_code = parts[0]  # 종목코드
        current_price = int(parts[2])  # 현재가
        
        # 해당 종목 찾기
        stock = next(
            (s for s in self.stocks if s.code == stock_code),
            None
        )
        
        if stock:
            stock.update_price(current_price)
            logger.debug(
                f"주가 업데이트: {stock.name} ({stock.code}) = {current_price:,}원"
            )
            
            # 콜백 호출
            if self.on_price_update:
                self.on_price_update(stock, current_price)
        else:
            logger.warning(f"알 수 없는 종목코드: {stock_code}")
    
    async def connect(self):
        """
        WebSocket 연결 및 데이터 수신
        """
        # 접속키 발급
        try:
            self._get_approval_key()
        except Exception as e:
            logger.error(f"접속키 발급 실패: {e}")
            return
        
        logger.info("WebSocket 연결 시작...")
        
        try:
            async with websockets.connect(KIS_WS_URL, ping_interval=None) as ws:
                # 종목별 구독 요청
                for stock in self.stocks:
                    subscribe_msg = {
                        "header": {
                            "approval_key": self.connect_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8"
                        },
                        "body": {
                            "input": {
                                "tr_id": "H0STCNT0",
                                "tr_key": stock.code
                            }
                        }
                    }
                    
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info(f"구독 요청: {stock.name} ({stock.code})")
                
                await asyncio.sleep(0.5)
                
                # 메시지 수신 루프
                logger.info("실시간 데이터 수신 시작...")
                while True:
                    message = await ws.recv()
                    await asyncio.sleep(0.1)
                    
                    # 실시간 체결 데이터
                    if message[0] in ["0", "1"]:
                        parts = message.split("|")
                        
                        if message[0] == "0" and len(parts) >= 4:
                            # 주식 체결 데이터
                            data_cnt = int(parts[2])
                            price_data = parts[3]
                            self._process_price_update(price_data)
                    
                    # JSON 메시지 (응답, PINGPONG 등)
                    else:
                        try:
                            json_msg = json.loads(message)
                            tr_id = json_msg.get("header", {}).get("tr_id")
                            
                            if tr_id == "PINGPONG":
                                # PING에 PONG 응답
                                await ws.pong(message)
                                logger.debug("PONG 전송")
                            
                            elif tr_id in ["H0STCNI0", "H0STCNI9"]:
                                # 체결통보 암호화 키 저장
                                output = json_msg.get("body", {}).get("output", {})
                                self.aes_key = output.get("key")
                                self.aes_iv = output.get("iv")
                                logger.info(f"AES 키 수신: {tr_id}")
                            
                            else:
                                # 기타 응답 처리
                                body = json_msg.get("body", {})
                                rt_cd = body.get("rt_cd")
                                msg = body.get("msg1", "")
                                
                                if rt_cd == "0":
                                    logger.info(f"정상 응답: {msg}")
                                elif rt_cd == "1":
                                    logger.error(f"오류 응답: {msg}")
                        
                        except json.JSONDecodeError:
                            logger.warning(f"JSON 파싱 실패: {message[:100]}")
        
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket 오류: {e}")
            # 재연결
            await asyncio.sleep(1)
            logger.info("재연결 시도...")
            await self.connect()
        
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}", exc_info=True)
    
    async def run(self):
        """
        클라이언트 실행 (외부 호출용)
        """
        await self.connect()
