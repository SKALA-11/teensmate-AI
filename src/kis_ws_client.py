import os
import json
import time
import asyncio
import logging
import requests
import websockets
from base64 import b64decode
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from stock import Stock

KIS_BASE_URL = "https://openapivts.koreainvestment.com:29443"
KIS_WS_BASE_URL = "ws://ops.koreainvestment.com:31000/tryitout"


class KisWsClient:
    def __init__(self, stocks):
        load_dotenv()
        self.app_key = os.getenv("KIS_APP_KEY")
        self.secret_key = os.getenv("KIS_APP_SECRET")
        self.connect_key = None
        self.kis_base_url = KIS_BASE_URL
        self.kis_ws_base_url = KIS_WS_BASE_URL
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self._stocks = stocks

    # --- AES256 복호화 함수 ---
    def aes_cbc_base64_dec(self, key: str, iv: str, cipher_text: str) -> str:
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        return bytes.decode(
            unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size)
        )

    # --- 웹소켓 접속키 발급 ---
    def get_approval(self):
        url = f"{self.kis_base_url}/oauth2/Approval"
        headers = {"Content-Type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key,
        }
        res = requests.post(url, headers=headers, data=json.dumps(body))
        res.raise_for_status()
        approval_key = res.json()["approval_key"]
        self.connect_key = approval_key

    # --- 국내주식체결처리 출력 포멧 ---
    def stockspurchase(self, data_cnt, data):
        print("============================================")
        menulist = "유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|시간구분코드|임의종료구분코드|정적VI발동기준가"
        menustr = menulist.split("|")
        pValue = data.split("^")
        i = 0
        for cnt in range(data_cnt):
            stock = next(stock for stock in self._stocks if stock.id == pValue[0])
            stock.update_price(int(pValue[2]))
            print("### [%d / %d]" % (cnt + 1, data_cnt))
            for _ in menustr:
                i += 1
            print("종목코드:", pValue[0])
            print("주식체결시간:", pValue[1])
            print("주식현재가:", pValue[2])
            print("전일대비부호:", pValue[3])
            print("전일대비:", pValue[4])
            print("전일대비율:", pValue[5])

    # --- 웹소켓 접속 및 데이터 처리 ---
    async def connect(self):
        print("KIS WebSocket 연결을 시작합니다.")
        try:
            self.get_approval()
            self.logger.info("approval_key 발급 성공: %s", self.connect_key)
        except Exception as e:
            print(f"approval_key 발급 실패: {e}")
            return {"error": f"approval_key 발급 실패: {e}"}

        url = self.kis_ws_base_url

        try:
            async with websockets.connect(url, ping_interval=None) as websocket:
                senddata_list = []
                for stock in self._stocks:
                    temp = (
                        '{"header":{"approval_key": "%s","custtype":"P","tr_type":"1","content-type":"utf-8"},'
                        '"body":{"input":{"tr_id":"H0STCNT0","tr_key":"%s"}}}'
                    ) % (self.connect_key, stock.id)
                    senddata_list.append(temp)

                # 요청 전송
                for senddata in senddata_list:
                    await websocket.send(senddata)

                await asyncio.sleep(0.5)

                # 메시지 수신 및 처리 루프
                while True:
                    data = await websocket.recv()
                    await asyncio.sleep(0.5)
                    print("Recev Command is :", data)

                    # 실시간 체결 데이터 처리
                    if data[0] == "0" or data[0] == "1":
                        recvstr = data.split("|")
                        if data[0] == "0":
                            print("#### 주식체결 ####")
                            data_cnt = int(recvstr[2])
                            self.stockspurchase(data_cnt, recvstr[3])
                            await asyncio.sleep(0.5)
                        elif data[0] == "1":
                            # 필요시 추가 처리 가능
                            recvstr = data.split("|")
                    else:
                        jsonObject = json.loads(data)
                        trid = jsonObject["header"]["tr_id"]

                        if trid != "PINGPONG":
                            rt_cd = jsonObject["body"]["rt_cd"]
                            if rt_cd == "1":  # 에러 처리
                                print(
                                    "### ERROR RETURN CODE [ %s ][ %s ] MSG [ %s ]"
                                    % (
                                        jsonObject["header"]["tr_key"],
                                        rt_cd,
                                        jsonObject["body"]["msg1"],
                                    )
                                )
                            elif rt_cd == "0":  # 정상 처리
                                print(
                                    "### RETURN CODE [ %s ][ %s ] MSG [ %s ]"
                                    % (
                                        jsonObject["header"]["tr_key"],
                                        rt_cd,
                                        jsonObject["body"]["msg1"],
                                    )
                                )
                                # 체결통보 관련 암호화 정보 처리
                                if trid in ["H0STCNI0", "H0STCNI9"]:
                                    aes_key = jsonObject["body"]["output"]["key"]
                                    aes_iv = jsonObject["body"]["output"]["iv"]
                                    print(
                                        "### TRID [%s] KEY[%s] IV[%s]"
                                        % (trid, aes_key, aes_iv)
                                    )
                        elif trid == "PINGPONG":
                            print("### RECV [PINGPONG] [%s]" % data)
                            await websocket.pong(data)
                            print("### SEND [PINGPONG] [%s]" % data)
        except Exception as e:
            print("Exception Raised!")
            print(e)
            print("Connect Again!")
            time.sleep(0.1)
            # 재접속
            await self.connect()

    # --- 외부에서 호출시 실행되는 함수 ---
    async def run(self):
        clearConsole = lambda: os.system("cls" if os.name in ("nt", "dos") else "clear")
        clearConsole()
        await self.connect()
