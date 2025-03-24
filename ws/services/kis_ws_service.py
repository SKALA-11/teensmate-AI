import os
import json
import time
import requests
import asyncio
import logging
import pandas as pd
import numpy as np
from collections import deque, namedtuple
from io import StringIO
from threading import Thread
from enum import StrEnum

import websocket  # pip install websocket-client = 동기
import websockets # pip install websockets = 비동기
import talib as ta

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

from core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Enum 및 글로벌 변수 ---
class KIS_WSReq(StrEnum):
    BID_ASK = 'H0STASP0'   # 실시간 국내주식 호가
    CONTRACT = 'H0STCNT0'  # 실시간 국내주식 체결가
    NOTICE = 'H0STCNI0'    # 실시간 계좌체결발생통보
    
_today__ = pd.Timestamp.now().strftime("%Y%m%d")

# 전역 컨테이너 (필요시 초기화; 여기서는 REST 호출 시 사용 결과만 반환)
contract_sub_df = dict()
tr_plans = dict()

reserved_cols = ['TICK_HOUR', 'STCK_PRPR', 'ACML_VOL']
# 실시간 국내주식체결 column header
contract_cols = ['MKSC_SHRN_ISCD',
                 'TICK_HOUR',  # pandas time conversion 편의를 위해 이 필드만 이름을 통일한다
                 'STCK_PRPR',  # 현재가
                 'PRDY_VRSS_SIGN',  # 전일 대비 부호
                 'PRDY_VRSS',  # 전일 대비
                 'PRDY_CTRT',  # 전일 대비율
                 'WGHN_AVRG_STCK_PRC',  # 가중 평균 주식 가격
                 'STCK_OPRC',  # 시가
                 'STCK_HGPR',  # 고가
                 'STCK_LWPR',  # 저가
                 'ASKP1',  # 매도호가1
                 'BIDP1',  # 매수호가1
                 'CNTG_VOL',  # 체결 거래량
                 'ACML_VOL',  # 누적 거래량
                 'ACML_TR_PBMN',  # 누적 거래 대금
                 'SELN_CNTG_CSNU',  # 매도 체결 건수
                 'SHNU_CNTG_CSNU',  # 매수 체결 건수
                 'NTBY_CNTG_CSNU',  # 순매수 체결 건수
                 'CTTR',  # 체결강도
                 'SELN_CNTG_SMTN',  # 총 매도 수량
                 'SHNU_CNTG_SMTN',  # 총 매수 수량
                 'CCLD_DVSN',  # 체결구분 (1:매수(+), 3:장전, 5:매도(-))
                 'SHNU_RATE',  # 매수비율
                 'PRDY_VOL_VRSS_ACML_VOL_RATE',  # 전일 거래량 대비 등락율
                 'OPRC_HOUR',  # 시가 시간
                 'OPRC_VRSS_PRPR_SIGN',  # 시가대비구분
                 'OPRC_VRSS_PRPR',  # 시가대비
                 'HGPR_HOUR',
                 'HGPR_VRSS_PRPR_SIGN',
                 'HGPR_VRSS_PRPR',
                 'LWPR_HOUR',
                 'LWPR_VRSS_PRPR_SIGN',
                 'LWPR_VRSS_PRPR',
                 'BSOP_DATE',  # 영업 일자
                 'NEW_MKOP_CLS_CODE',  # 신 장운영 구분 코드
                 'TRHT_YN',
                 'ASKP_RSQN1',
                 'BIDP_RSQN1',
                 'TOTAL_ASKP_RSQN',
                 'TOTAL_BIDP_RSQN',
                 'VOL_TNRT',  # 거래량 회전율
                 'PRDY_SMNS_HOUR_ACML_VOL',  # 전일 동시간 누적 거래량
                 'PRDY_SMNS_HOUR_ACML_VOL_RATE',  # 전일 동시간 누적 거래량 비율
                 'HOUR_CLS_CODE',  # 시간 구분 코드(0 : 장중 )
                 'MRKT_TRTM_CLS_CODE',
                 'VI_STND_PRC']
# 실시간 국내주식호가 column eader
bid_ask_cols = ['MKSC_SHRN_ISCD',
                'TICK_HOUR',  # pandas time conversion 편의를 위해 이 필드만 이름을 통일한다
                'HOUR_CLS_CODE',  # 시간 구분 코드(0 : 장중 )
                'ASKP1',  # 매도호가1
                'ASKP2',
                'ASKP3',
                'ASKP4',
                'ASKP5',
                'ASKP6',
                'ASKP7',
                'ASKP8',
                'ASKP9',
                'ASKP10',
                'BIDP1',  # 매수호가1
                'BIDP2',
                'BIDP3',
                'BIDP4',
                'BIDP5',
                'BIDP6',
                'BIDP7',
                'BIDP8',
                'BIDP9',
                'BIDP10',
                'ASKP_RSQN1',  # 매도호가 잔량1
                'ASKP_RSQN2',
                'ASKP_RSQN3',
                'ASKP_RSQN4',
                'ASKP_RSQN5',
                'ASKP_RSQN6',
                'ASKP_RSQN7',
                'ASKP_RSQN8',
                'ASKP_RSQN9',
                'ASKP_RSQN10',
                'BIDP_RSQN1',  # 매수호가 잔량1
                'BIDP_RSQN2',
                'BIDP_RSQN3',
                'BIDP_RSQN4',
                'BIDP_RSQN5',
                'BIDP_RSQN6',
                'BIDP_RSQN7',
                'BIDP_RSQN8',
                'BIDP_RSQN9',
                'BIDP_RSQN10',
                'TOTAL_ASKP_RSQN',  # 총 매도호가 잔량
                'TOTAL_BIDP_RSQN',  # 총 매수호가 잔량
                'OVTM_TOTAL_ASKP_RSQN',
                'OVTM_TOTAL_BIDP_RSQN',
                'ANTC_CNPR',
                'ANTC_CNQN',
                'ANTC_VOL',
                'ANTC_CNTG_VRSS',
                'ANTC_CNTG_VRSS_SIGN',
                'ANTC_CNTG_PRDY_CTRT',
                'ACML_VOL',  # 누적 거래량
                'TOTAL_ASKP_RSQN_ICDC',
                'TOTAL_BIDP_RSQN_ICDC',
                'OVTM_TOTAL_ASKP_ICDC',
                'OVTM_TOTAL_BIDP_ICDC',
                'STCK_DEAL_CLS_CODE']
# 실시간 계좌체결발생통보 column header
notice_cols = ['CUST_ID',  # HTS ID
               'ACNT_NO',
               'ODER_NO',  # 주문번호
               'OODER_NO',  # 원주문번호
               'SELN_BYOV_CLS',  # 매도매수구분
               'RCTF_CLS',  # 정정구분
               'ODER_KIND',  # 주문종류(00 : 지정가,01 : 시장가,02 : 조건부지정가)
               'ODER_COND',  # 주문조건
               'STCK_SHRN_ISCD',  # 주식 단축 종목코드
               'CNTG_QTY',  # 체결 수량(체결통보(CNTG_YN=2): 체결 수량, 주문·정정·취소·거부 접수 통보(CNTG_YN=1): 주문수량의미)
               'CNTG_UNPR',  # 체결단가
               'STCK_CNTG_HOUR',  # 주식 체결 시간
               'RFUS_YN',  # 거부여부(0 : 승인, 1 : 거부)
               'CNTG_YN',  # 체결여부(1 : 주문,정정,취소,거부,, 2 : 체결 (★ 체결만 볼 경우 2번만 ))
               'ACPT_YN',  # 접수여부(1 : 주문접수, 2 : 확인 )
               'BRNC_NO',  # 지점
               'ODER_QTY',  # 주문수량
               'ACNT_NAME',  # 계좌명
               'CNTG_ISNM',  # 체결종목명
               'CRDT_CLS',  # 신용구분
               'CRDT_LOAN_DATE',  # 신용대출일자
               'CNTG_ISNM40',  # 체결종목명40
               'ODER_PRC'  # 주문가격
               ]

# --- AES256 복호화 함수 ---
def aes_cbc_base64_dec(key: str, iv: str, cipher_text: str) -> str:
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))


# --- 웹소켓 접속키 발급 (수정: REST로부터 입력받은 키 사용 대신 환경변수 또는 인자 활용) ---
def get_approval(app_key: str, secret_key: str) -> str:
    url = f"{settings.KIS_BASE_URL}/oauth2/Approval"
    headers = {"Content-Type": "application/json"}
    body = {"grant_type": "client_credentials", "appkey": app_key, "secretkey": secret_key}
    res = requests.post(url, headers=headers, data=json.dumps(body))
    res.raise_for_status()
    approval_key = res.json()["approval_key"]
    return approval_key

# 글로벌 변수 (웹소켓 연결 전 approval key 저장)
_connect_key = None

# --- 메시지 빌드 ---
def _build_message(app_key: str, tr_id: str, added_data: str, tr_type: str = '1') -> str:
    message = {
        "header": {
            "approval_key": app_key,
            "custtype": "P",
            "tr_type": tr_type,
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": tr_id,
                "tr_key": added_data
            }
        }
    }
    return json.dumps(message)

# --- 구독/해제 함수 ---
def subscribe(ws, sub_type: str, app_key: str, sub_data: str):
    msg = _build_message(app_key, sub_type, sub_data)
    ws.send(msg, websocket.ABNF.OPCODE_TEXT)
    time.sleep(0.1)

def unsubscribe(ws, sub_type: str, app_key: str, sub_data: str):
    msg = _build_message(app_key, sub_type, sub_data, tr_type='2')
    ws.send(msg, websocket.ABNF.OPCODE_TEXT)
    time.sleep(0.1)

# --- 데이터 파싱 함수 ---
def _dparse(data: str) -> dict:
    try:
        parts = data.split("|")
        tr_id = parts[1]
        return {"tr_id": tr_id, "raw_data": parts[3]}
    except Exception as e:
        logger.error("파싱 오류: %s", e)
        return {}

# --- WebSocket 이벤트 핸들러 (콜백 함수들) ---
def on_message(ws, data):
    logger.info("수신 메세지: %s", data)
    parsed = _dparse(data)
    ws.last_message = parsed  # 마지막 메시지를 저장

def on_error(ws, error):
    logger.error("웹소켓 오류: %s", error)

def on_close(ws, status_code, close_msg):
    logger.info("웹소켓 종료: %s, %s", status_code, close_msg)

def on_open(ws):
    logger.info("웹소켓 연결 성공")
    # 기본적으로 구독할 종목을 지정 (필요에 따라 파라미터로 받을 수 있음)
    stocks = ['009540', '012630']  # 예시 종목
    for scode in stocks:
        subscribe(ws, KIS_WSReq.BID_ASK, _connect_key, scode)
        subscribe(ws, KIS_WSReq.CONTRACT, _connect_key, scode)
    # 계좌체결발생통보 구독 (HTS ID는 환경변수나 인자로 받을 수 있음)
    subscribe(ws, KIS_WSReq.NOTICE, _connect_key, settings.KIS_HTS_ID)

# 국내주식체결처리 출력 포멧
def stockspurchase(data_cnt, data):
    print("============================================")
    menulist = "유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|시간구분코드|임의종료구분코드|정적VI발동기준가"
    menustr = menulist.split('|')
    pValue = data.split('^')
    i = 0
    for cnt in range(data_cnt):  # 넘겨받은 체결데이터 개수만큼 print 한다
        print("### [%d / %d]" % (cnt + 1, data_cnt))
        for menu in menustr:
            # print("%-13s[%s]" % (menu, pValue[i]))
            i += 1
        print("종목코드", pValue[0])
        print("주식체결시간:", pValue[1])
        print("주식현재가:", pValue[2])
        print("전일대비부호:", pValue[3])
        print("전일대비:", pValue[4])
        print("전일대비율:", pValue[5])

async def connect(app_key: str, secret_key: str, 
                        stockcode: str = None, htsid: str = None, 
                        custtype: str = None):
    global _connect_key
    print("connect")
    try:
        _connect_key = get_approval(app_key, secret_key)
        logger.info("approval_key 발급 성공: %s", _connect_key)
    except Exception as e:
        return {"error": f"approval_key 발급 실패: {e}"}
    
    url = settings.KIS_WS_BASE_URL

    try:
        async with websockets.connect(url, ping_interval=None) as websocket:
            
            code_list = [['1','H0STCNT0','005930'],['1','H0STCNT0','066570'],['1','H0STCNT0','000660']]
            senddata_list = []
            for i, j, k in code_list:
                temp = '{"header":{"approval_key": "%s","custtype":"P","tr_type":"%s","content-type":"utf-8"},"body":{"input":{"tr_id":"%s","tr_key":"%s"}}}'%(_connect_key,i,j,k)
                senddata_list.append(temp)

            # print('Input Command is :', senddata)

            # await websocket.send(senddata)
            for senddata in senddata_list:
                await websocket.send(senddata)
            
            await asyncio.sleep(0.5)

            # 데이터가 오길 기다린다.
            while True:
                data = await websocket.recv()
                await asyncio.sleep(0.5)
                print("Recev Command is :", data)
                
                if data[0] == '0' or data[0] == '1':  # 실시간 데이터일 경우
                    trid = jsonObject["header"]["tr_id"]

                    if data[0] == '0':
                        recvstr = data.split('|')  # 수신데이터가 실데이터 이전은 '|'로 나뉘어져있어 split 해야 함
                        trid0 = recvstr[1]
                        print("#### 주식체결 ####")
                        data_cnt = int(recvstr[2])  # 체결데이터 개수
                        stockspurchase(data_cnt, recvstr[3])
                        await asyncio.sleep(0.5)

                    elif data[0] == '1':
                        recvstr = data.split('|')  # 수신데이터가 실데이터 이전은 '|'로 나뉘어져있어 split
                        trid0 = recvstr[1]

                    # clearConsole()
                    # break;
                else:
                    jsonObject = json.loads(data)
                    trid = jsonObject["header"]["tr_id"]

                    if trid != "PINGPONG":
                        rt_cd = jsonObject["body"]["rt_cd"]
                        if rt_cd == '1':  # 에러일 경우
                            print("### ERROR RETURN CODE [ %s ][ %s ] MSG [ %s ]" % (jsonObject["header"]["tr_key"], rt_cd, jsonObject["body"]["msg1"]))
                            #break
                        elif rt_cd == '0':  # 정상일 경우
                            print("### RETURN CODE [ %s ][ %s ] MSG [ %s ]" % (jsonObject["header"]["tr_key"], rt_cd, jsonObject["body"]["msg1"]))
                            # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                            if trid == "H0STCNI0" or trid == "H0STCNI9":
                                aes_key = jsonObject["body"]["output"]["key"]
                                aes_iv = jsonObject["body"]["output"]["iv"]
                                print("### TRID [%s] KEY[%s] IV[%s]" % (trid, aes_key, aes_iv))

                    elif trid == "PINGPONG":
                        print("### RECV [PINGPONG] [%s]" % (data))
                        await websocket.pong(data)
                        print("### SEND [PINGPONG] [%s]" % (data))

    except Exception as e:
        print('Exception Raised!')
        print(e)
        print('Connect Again!')
        time.sleep(0.1)

        # 웹소켓 다시 시작
        await connect()     