# 국내주식 실시간호가 (KRX)

> API 경로: `/tryitout/H0STASP0`

---

# WEBSOCKET국내주식 실시간호가 (KRX) [실시간-004]

**국내주식 실시간호가 (KRX) [실시간-004] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0STASP0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain |  ws://ops.koreainvestment.com:31000  
실전 TR ID  | H0STASP0 | 모의 TR ID | H0STASP0  
Format |  | Content-Type | text/plain  
  
## 개요
    
    
    [참고자료]
    실시간시세(웹소켓) 파이썬 샘플코드는 한국투자증권 Github 참고 부탁드립니다.
    https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/ws_domestic_overseas_all.py
    
    실시간시세(웹소켓) API 사용방법에 대한 자세한 설명은 한국투자증권 Wikidocs 참고 부탁드립니다.
    https://wikidocs.net/book/7847 (국내주식 업데이트 완료, 추후 해외주식·국내선물옵션 업데이트 예정)
    
    [호출 데이터]
    헤더와 바디 값을 합쳐 JSON 형태로 전송합니다.
    
    [응답 데이터]
    1. 정상 등록 여부 (JSON)
    - JSON["body"]["msg1"] - 정상 응답 시, SUBSCRIBE SUCCESS
    - JSON["body"]["output"]["iv"] - 실시간 결과 복호화에 필요한 AES256 IV (Initialize Vector)
    - JSON["body"]["output"]["key"] - 실시간 결과 복호화에 필요한 AES256 Key
    
    2. 실시간 결과 응답 ( | 로 구분되는 값)
    - 암호화 유무 : 0 암호화 되지 않은 데이터 / 1 암호화된 데이터
    - TR_ID : 등록한 tr_id
    - 데이터 건수 : (ex. 001 데이터 건수를 참조하여 활용)
    - 응답 데이터 : 아래 response 데이터 참조 ( ^로 구분됨)

## 요청

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
approval_key | 웹소켓 접속키 | String | Y | 286 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키  
custtype | 고객타입 | String | Y | 1 | B : 법인  
P : 개인  
tr_type | 거래타입 | String | Y | 1 | 1 : 등록  
2 : 해제  
content-type | 컨텐츠타입 | String | Y | 1 | utf-8  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
tr_id | 거래ID | String | Y | 1 | [실전/모의투자]  
H0STASP0 : 주식호가  
tr_key | 구분값 | String | Y | 1 | 종목번호 (6자리)  
ETN의 경우, Q로 시작 (EX. Q500001)  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권 단축 종목코드 | String | Y | 9 |   
BSOP_HOUR | 영업 시간 | String | Y | 6 |   
HOUR_CLS_CODE | 시간 구분 코드 | String | Y | 1 | 0 : 장중  
A : 장후예상  
B : 장전예상  
C : 9시이후의 예상가, VI발동  
D : 시간외 단일가 예상  
ASKP1 | 매도호가1 | Number | Y | 4 |   
ASKP2 | 매도호가2 | Number | Y | 4 |   
ASKP3 | 매도호가3 | Number | Y | 4 |   
ASKP4 | 매도호가4 | Number | Y | 4 |   
ASKP5 | 매도호가5 | Number | Y | 4 |   
ASKP6 | 매도호가6 | Number | Y | 4 |   
ASKP7 | 매도호가7 | Number | Y | 4 |   
ASKP8 | 매도호가8 | Number | Y | 4 |   
ASKP9 | 매도호가9 | Number | Y | 4 |   
ASKP10 | 매도호가10 | Number | Y | 4 |   
BIDP1 | 매수호가1 | Number | Y | 4 |   
BIDP2 | 매수호가2 | Number | Y | 4 |   
BIDP3 | 매수호가3 | Number | Y | 4 |   
BIDP4 | 매수호가4 | Number | Y | 4 |   
BIDP5 | 매수호가5 | Number | Y | 4 |   
BIDP6 | 매수호가6 | Number | Y | 4 |   
BIDP7 | 매수호가7 | Number | Y | 4 |   
BIDP8 | 매수호가8 | Number | Y | 4 |   
BIDP9 | 매수호가9 | Number | Y | 4 |   
BIDP10 | 매수호가10 | Number | Y | 4 |   
ASKP_RSQN1 | 매도호가 잔량1 | Number | Y | 8 |   
ASKP_RSQN2 | 매도호가 잔량2 | Number | Y | 8 |   
ASKP_RSQN3 | 매도호가 잔량3 | Number | Y | 8 |   
ASKP_RSQN4 | 매도호가 잔량4 | Number | Y | 8 |   
ASKP_RSQN5 | 매도호가 잔량5 | Number | Y | 8 |   
ASKP_RSQN6 | 매도호가 잔량6 | Number | Y | 8 |   
ASKP_RSQN7 | 매도호가 잔량7 | Number | Y | 8 |   
ASKP_RSQN8 | 매도호가 잔량8 | Number | Y | 8 |   
ASKP_RSQN9 | 매도호가 잔량9 | Number | Y | 8 |   
ASKP_RSQN10 | 매도호가 잔량10 | Number | Y | 8 |   
BIDP_RSQN1 | 매수호가 잔량1 | Number | Y | 8 |   
BIDP_RSQN2 | 매수호가 잔량2 | Number | Y | 8 |   
BIDP_RSQN3 | 매수호가 잔량3 | Number | Y | 8 |   
BIDP_RSQN4 | 매수호가 잔량4 | Number | Y | 8 |   
BIDP_RSQN5 | 매수호가 잔량5 | Number | Y | 8 |   
BIDP_RSQN6 | 매수호가 잔량6 | Number | Y | 8 |   
BIDP_RSQN7 | 매수호가 잔량7 | Number | Y | 8 |   
BIDP_RSQN8 | 매수호가 잔량8 | Number | Y | 8 |   
BIDP_RSQN9 | 매수호가 잔량9 | Number | Y | 8 |   
BIDP_RSQN10 | 매수호가 잔량10 | Number | Y | 8 |   
TOTAL_ASKP_RSQN | 총 매도호가 잔량 | Number | Y | 8 |   
TOTAL_BIDP_RSQN | 총 매수호가 잔량 | Number | Y | 8 |   
OVTM_TOTAL_ASKP_RSQN | 시간외 총 매도호가 잔량 | Number | Y | 8 |   
OVTM_TOTAL_BIDP_RSQN | 시간외 총 매수호가 잔량 | Number | Y | 8 |   
ANTC_CNPR | 예상 체결가 | Number | Y | 4 | 동시호가 등 특정 조건하에서만 발생  
ANTC_CNQN | 예상 체결량 | Number | Y | 8 | 동시호가 등 특정 조건하에서만 발생  
ANTC_VOL | 예상 거래량 | Number | Y | 8 | 동시호가 등 특정 조건하에서만 발생  
ANTC_CNTG_VRSS | 예상 체결 대비 | Number | Y | 4 | 동시호가 등 특정 조건하에서만 발생  
ANTC_CNTG_VRSS_SIGN | 예상 체결 대비 부호 | String | Y | 1 | 동시호가 등 특정 조건하에서만 발생  
  
1 : 상한  
2 : 상승  
3 : 보합  
4 : 하한  
5 : 하락  
ANTC_CNTG_PRDY_CTRT | 예상 체결 전일 대비율 | Number | Y | 8 |   
ACML_VOL | 누적 거래량 | Number | Y | 8 |   
TOTAL_ASKP_RSQN_ICDC | 총 매도호가 잔량 증감 | Number | Y | 4 |   
TOTAL_BIDP_RSQN_ICDC | 총 매수호가 잔량 증감 | Number | Y | 4 |   
OVTM_TOTAL_ASKP_ICDC | 시간외 총 매도호가 증감 | Number | Y | 4 |   
OVTM_TOTAL_BIDP_ICDC | 시간외 총 매수호가 증감 | Number | Y | 4 |   
STCK_DEAL_CLS_CODE | 주식 매매 구분 코드 | String | Y | 2 | 사용 X (삭제된 값)  
  
## 예시

### Request

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    
    @dataclass
    class RequestHeader:
        approval_key: str    #웹소켓 접속키
        custtype: str    #고객타입
        tr_type: str    #거래타입
        content-type: str    #컨텐츠타입
    
    @dataclass
    class RequestBody:
        tr_id: str    #거래ID
        tr_key: str    #구분값
    
    

복사하기

### Response

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    from typing import List, Optional
    from decimal import Decimal
    
    @dataclass
    class ResponseHeader:
    
    @dataclass
    class ResponseBody:
        MKSC_SHRN_ISCD: str    #유가증권 단축 종목코드
        BSOP_HOUR: str    #영업 시간
        HOUR_CLS_CODE: str    #시간 구분 코드
        ASKP1: float    #매도호가1
        ASKP2: float    #매도호가2
        ASKP3: float    #매도호가3
        ASKP4: float    #매도호가4
        ASKP5: float    #매도호가5
        ASKP6: float    #매도호가6
        ASKP7: float    #매도호가7
        ASKP8: float    #매도호가8
        ASKP9: float    #매도호가9
        ASKP10: float    #매도호가10
        BIDP1: float    #매수호가1
        BIDP2: float    #매수호가2
        BIDP3: float    #매수호가3
        BIDP4: float    #매수호가4
        BIDP5: float    #매수호가5
        BIDP6: float    #매수호가6
        BIDP7: float    #매수호가7
        BIDP8: float    #매수호가8
        BIDP9: float    #매수호가9
        BIDP10: float    #매수호가10
        ASKP_RSQN1: float    #매도호가 잔량1
        ASKP_RSQN2: float    #매도호가 잔량2
        ASKP_RSQN3: float    #매도호가 잔량3
        ASKP_RSQN4: float    #매도호가 잔량4
        ASKP_RSQN5: float    #매도호가 잔량5
        ASKP_RSQN6: float    #매도호가 잔량6
        ASKP_RSQN7: float    #매도호가 잔량7
        ASKP_RSQN8: float    #매도호가 잔량8
        ASKP_RSQN9: float    #매도호가 잔량9
        ASKP_RSQN10: float    #매도호가 잔량10
        BIDP_RSQN1: float    #매수호가 잔량1
        BIDP_RSQN2: float    #매수호가 잔량2
        BIDP_RSQN3: float    #매수호가 잔량3
        BIDP_RSQN4: float    #매수호가 잔량4
        BIDP_RSQN5: float    #매수호가 잔량5
        BIDP_RSQN6: float    #매수호가 잔량6
        BIDP_RSQN7: float    #매수호가 잔량7
        BIDP_RSQN8: float    #매수호가 잔량8
        BIDP_RSQN9: float    #매수호가 잔량9
        BIDP_RSQN10: float    #매수호가 잔량10
        TOTAL_ASKP_RSQN: float    #총 매도호가 잔량
        TOTAL_BIDP_RSQN: float    #총 매수호가 잔량
        OVTM_TOTAL_ASKP_RSQN: float    #시간외 총 매도호가 잔량
        OVTM_TOTAL_BIDP_RSQN: float    #시간외 총 매수호가 잔량
        ANTC_CNPR: float    #예상 체결가
        ANTC_CNQN: float    #예상 체결량
        ANTC_VOL: float    #예상 거래량
        ANTC_CNTG_VRSS: float    #예상 체결 대비
        ANTC_CNTG_VRSS_SIGN: str    #예상 체결 대비 부호
        ANTC_CNTG_PRDY_CTRT: float    #예상 체결 전일 대비율
        ACML_VOL: float    #누적 거래량
        TOTAL_ASKP_RSQN_ICDC: float    #총 매도호가 잔량 증감
        TOTAL_BIDP_RSQN_ICDC: float    #총 매수호가 잔량 증감
        OVTM_TOTAL_ASKP_ICDC: float    #시간외 총 매도호가 증감
        OVTM_TOTAL_BIDP_ICDC: float    #시간외 총 매수호가 증감
        STCK_DEAL_CLS_CODE: str    #주식 매매 구분 코드
    
    

복사하기