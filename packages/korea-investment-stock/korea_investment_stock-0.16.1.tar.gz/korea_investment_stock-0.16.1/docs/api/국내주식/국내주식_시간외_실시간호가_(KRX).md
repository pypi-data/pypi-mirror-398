# 국내주식 시간외 실시간호가 (KRX)

> API 경로: `/tryitout/H0STOAA0`

---

# WEBSOCKET국내주식 시간외 실시간호가 (KRX) [실시간-025]

**국내주식 시간외 실시간호가 (KRX) [실시간-025] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0STOAA0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0STOAA0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    국내주식 시간외 실시간호가 API입니다.
    국내주식 시간외 단일가(16:00~18:00) 시간대에 실시간호가 데이터 확인 가능합니다.
    
    [참고자료]
    실시간시세(웹소켓) 파이썬 샘플코드는 한국투자증권 Github 참고 부탁드립니다.
    https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/ws_domestic_overseas_all.py
    
    실시간시세(웹소켓) API 사용방법에 대한 자세한 설명은 한국투자증권 Wikidocs 참고 부탁드립니다.
    https://wikidocs.net/book/7847 (국내주식 업데이트 완료, 추후 해외주식·국내선물옵션 업데이트 예정)
    
    종목코드 마스터파일 파이썬 정제코드는 한국투자증권 Github 참고 부탁드립니다.
    https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info
    
    
    [호출 데이터]
    헤더와 바디 값을 합쳐 JSON 형태로 전송합니다.
    
    [응답 데이터]
    1. 정상 등록 여부 (JSON)
    - JSON["body"]["msg1"] - 정상 응답 시, SUBSCRIBE SUCCESS
    - JSON["body"]["output"]["iv"] - 실시간 결과 복호화에 필요한 AES256 IV (Initialize Vector)
    - JSON["body"]["output"]["key"] - 실시간 결과 복호화에 필요한 AES256 Key
    
    2. 실시간 결과 응답 ( | 로 구분되는 값)
    ex) 0|H0STCNT0|004|005930^123929^73100^5^...
    - 암호화 유무 : 0 암호화 되지 않은 데이터 / 1 암호화된 데이터
    - TR_ID : 등록한 tr_id (ex. H0STCNT0)
    - 데이터 건수 : (ex. 001 인 경우 데이터 건수 1건, 004인 경우 데이터 건수 4건)
    - 응답 데이터 : 아래 response 데이터 참조 ( ^로 구분됨)

## 요청

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
approval_key | 웹소켓 접속키 | String | Y | 36 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키  
custtype | 고객 타입 | String | Y | 1 | B : 법인 / P : 개인  
tr_type | 등록/해제 | String | Y | 1 | 1: 등록, 2:해제  
content-type | 컨텐츠타입 | String | Y | 20 | utf-8  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
tr_id | 거래ID | String | Y | 2 | H0STOAA0  
tr_key | 구분값 | String | Y | 12 | 종목코드 (ex 005930 삼성전자)  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권단축종목코드 | String | Y | 9 |   
BSOP_HOUR | 영업시간 | String | Y | 6 |   
HOUR_CLS_CODE | 시간구분코드 | String | Y | 1 |   
ASKP1 | 매도호가1 | String | Y | 1 |   
ASKP2 | 매도호가2 | String | Y | 1 |   
ASKP3 | 매도호가3 | String | Y | 1 |   
ASKP4 | 매도호가4 | String | Y | 1 |   
ASKP5 | 매도호가5 | String | Y | 1 |   
ASKP6 | 매도호가6 | String | Y | 1 |   
ASKP7 | 매도호가7 | String | Y | 1 |   
ASKP8 | 매도호가8 | String | Y | 1 |   
ASKP9 | 매도호가9 | String | Y | 1 |   
BIDP1 | 매수호가1 | String | Y | 1 |   
BIDP2 | 매수호가2 | String | Y | 1 |   
BIDP3 | 매수호가3 | String | Y | 1 |   
BIDP4 | 매수호가4 | String | Y | 1 |   
BIDP5 | 매수호가5 | String | Y | 1 |   
BIDP6 | 매수호가6 | String | Y | 1 |   
BIDP7 | 매수호가7 | String | Y | 1 |   
BIDP8 | 매수호가8 | String | Y | 1 |   
BIDP9 | 매수호가9 | String | Y | 1 |   
ASKP_RSQN1 | 매도호가잔량1 | String | Y | 1 |   
ASKP_RSQN2 | 매도호가잔량2 | String | Y | 1 |   
ASKP_RSQN3 | 매도호가잔량3 | String | Y | 1 |   
ASKP_RSQN4 | 매도호가잔량4 | String | Y | 1 |   
ASKP_RSQN5 | 매도호가잔량5 | String | Y | 1 |   
ASKP_RSQN6 | 매도호가잔량6 | String | Y | 1 |   
ASKP_RSQN7 | 매도호가잔량7 | String | Y | 1 |   
ASKP_RSQN8 | 매도호가잔량8 | String | Y | 1 |   
ASKP_RSQN9 | 매도호가잔량9 | String | Y | 1 |   
BIDP_RSQN1 | 매수호가잔량1 | String | Y | 1 |   
BIDP_RSQN2 | 매수호가잔량2 | String | Y | 1 |   
BIDP_RSQN3 | 매수호가잔량3 | String | Y | 1 |   
BIDP_RSQN4 | 매수호가잔량4 | String | Y | 1 |   
BIDP_RSQN5 | 매수호가잔량5 | String | Y | 1 |   
BIDP_RSQN6 | 매수호가잔량6 | String | Y | 1 |   
BIDP_RSQN7 | 매수호가잔량7 | String | Y | 1 |   
BIDP_RSQN8 | 매수호가잔량8 | String | Y | 1 |   
BIDP_RSQN9 | 매수호가잔량9 | String | Y | 1 |   
TOTAL_ASKP_RSQN | 총매도호가잔량 | String | Y | 1 |   
TOTAL_BIDP_RSQN | 총매수호가잔량 | String | Y | 1 |   
OVTM_TOTAL_ASKP_RSQN | 시간외총매도호가잔량 | String | Y | 1 |   
OVTM_TOTAL_BIDP_RSQN | 시간외총매수호가잔량 | String | Y | 1 |   
ANTC_CNPR | 예상체결가 | String | Y | 1 |   
ANTC_CNQN | 예상체결량 | String | Y | 1 |   
ANTC_VOL | 예상거래량 | String | Y | 1 |   
ANTC_CNTG_VRSS | 예상체결대비 | String | Y | 1 |   
ANTC_CNTG_VRSS_SIGN | 예상체결대비부호 | String | Y | 1 |   
ANTC_CNTG_PRDY_CTRT | 예상체결전일대비율 | String | Y | 1 |   
ACML_VOL | 누적거래량 | String | Y | 1 |   
TOTAL_ASKP_RSQN_ICDC | 총매도호가잔량증감 | String | Y | 1 |   
TOTAL_BIDP_RSQN_ICDC | 총매수호가잔량증감 | String | Y | 1 |   
OVTM_TOTAL_ASKP_ICDC | 시간외총매도호가증감 | String | Y | 1 |   
OVTM_TOTAL_BIDP_ICDC | 시간외총매수호가증감 | String | Y | 1 |   
  
## 예시

### Request

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    
    @dataclass
    class RequestHeader:
        approval_key: str    #웹소켓 접속키
        custtype: str    #고객 타입
        tr_type: str    #등록/해제
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
    
    @dataclass
    class ResponseHeader:
    
    @dataclass
    class ResponseBody:
        MKSC_SHRN_ISCD: str    #유가증권단축종목코드
        BSOP_HOUR: str    #영업시간
        HOUR_CLS_CODE: str    #시간구분코드
        ASKP1: str    #매도호가1
        ASKP2: str    #매도호가2
        ASKP3: str    #매도호가3
        ASKP4: str    #매도호가4
        ASKP5: str    #매도호가5
        ASKP6: str    #매도호가6
        ASKP7: str    #매도호가7
        ASKP8: str    #매도호가8
        ASKP9: str    #매도호가9
        BIDP1: str    #매수호가1
        BIDP2: str    #매수호가2
        BIDP3: str    #매수호가3
        BIDP4: str    #매수호가4
        BIDP5: str    #매수호가5
        BIDP6: str    #매수호가6
        BIDP7: str    #매수호가7
        BIDP8: str    #매수호가8
        BIDP9: str    #매수호가9
        ASKP_RSQN1: str    #매도호가잔량1
        ASKP_RSQN2: str    #매도호가잔량2
        ASKP_RSQN3: str    #매도호가잔량3
        ASKP_RSQN4: str    #매도호가잔량4
        ASKP_RSQN5: str    #매도호가잔량5
        ASKP_RSQN6: str    #매도호가잔량6
        ASKP_RSQN7: str    #매도호가잔량7
        ASKP_RSQN8: str    #매도호가잔량8
        ASKP_RSQN9: str    #매도호가잔량9
        BIDP_RSQN1: str    #매수호가잔량1
        BIDP_RSQN2: str    #매수호가잔량2
        BIDP_RSQN3: str    #매수호가잔량3
        BIDP_RSQN4: str    #매수호가잔량4
        BIDP_RSQN5: str    #매수호가잔량5
        BIDP_RSQN6: str    #매수호가잔량6
        BIDP_RSQN7: str    #매수호가잔량7
        BIDP_RSQN8: str    #매수호가잔량8
        BIDP_RSQN9: str    #매수호가잔량9
        TOTAL_ASKP_RSQN: str    #총매도호가잔량
        TOTAL_BIDP_RSQN: str    #총매수호가잔량
        OVTM_TOTAL_ASKP_RSQN: str    #시간외총매도호가잔량
        OVTM_TOTAL_BIDP_RSQN: str    #시간외총매수호가잔량
        ANTC_CNPR: str    #예상체결가
        ANTC_CNQN: str    #예상체결량
        ANTC_VOL: str    #예상거래량
        ANTC_CNTG_VRSS: str    #예상체결대비
        ANTC_CNTG_VRSS_SIGN: str    #예상체결대비부호
        ANTC_CNTG_PRDY_CTRT: str    #예상체결전일대비율
        ACML_VOL: str    #누적거래량
        TOTAL_ASKP_RSQN_ICDC: str    #총매도호가잔량증감
        TOTAL_BIDP_RSQN_ICDC: str    #총매수호가잔량증감
        OVTM_TOTAL_ASKP_ICDC: str    #시간외총매도호가증감
        OVTM_TOTAL_BIDP_ICDC: str    #시간외총매수호가증감
    
    

복사하기