import os
import sys
import json
import time
import requests
import asyncio
import traceback
import websockets

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

from app.core.config import settings
from app.services.kis_ws_service import connect

clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')

async def main():
    
    stockcode = "000660" # SK하이닉스
    htsid = 'H0STCNT0'  # 체결통보용 htsid 입력
    custtype = 'P'  # customer type, 개인:'P' 법인 'B'
    
    print("KIS WebSocket 연결을 시작합니다.")
    try:
        await connect(
            settings.KIS_APP_KEY, settings.KIS_APP_SECRET, stockcode, htsid, custtype
        )
        
    except Exception as e:
        print("내부 Exception 발생!")
        print(e)

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("KeyboardInterrupt Exception 발생!")
        print(traceback.format_exc())
        sys.exit(-100)

    except Exception:
        print("외부 Exception 발생!")
        print(traceback.format_exc())
        sys.exit(-200)