# 국내주식 실시간프로그램매매 (KRX)

> API 경로: `/tryitout/H0STPGM0`

---

# WEBSOCKET국내주식 실시간프로그램매매 (KRX) [실시간-048]

**국내주식 실시간프로그램매매 (KRX) [실시간-048] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0STPGM0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0STPGM0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
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
tr_type | 등록/해제 | String | Y | 1 | "1: 등록, 2:해제"  
content-type | 컨텐츠타입 | String | Y | 20 | utf-8  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
tr_id | 거래ID | String | Y | 7 | H0STPGM0  
tr_key | 종목코드 | String | Y | 6 | 종목코드  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권단축종목코드 | Object | Y | 9 | '각 항목사이에는 구분자로 ^ 사용,  
모든 데이터타입은 String으로 변환되어 push 처리됨'  
STCK_CNTG_HOUR | 주식체결시간 | String | Y | 6 |   
SELN_CNQN | 매도체결량 | String | Y | 1 |   
SELN_TR_PBMN | 매도거래대금 | String | Y | 1 |   
SHNU_CNQN | 매수2체결량 | String | Y | 1 |   
SHNU_TR_PBMN | 매수2거래대금 | String | Y | 1 |   
NTBY_CNQN | 순매수체결량 | String | Y | 1 |   
NTBY_TR_PBMN | 순매수거래대금 | String | Y | 1 |   
SELN_RSQN | 매도호가잔량 | String | Y | 1 |   
SHNU_RSQN | 매수호가잔량 | String | Y | 1 |   
WHOL_NTBY_QTY | 전체순매수호가잔량 | String | Y | 1 |   
  
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
        tr_key: str    #종목코드
    
    

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
        MKSC_SHRN_ISCD: ResponseBodyMKSC_SHRN_ISCD    #유가증권단축종목코드
        STCK_CNTG_HOUR: str    #주식체결시간
        SELN_CNQN: str    #매도체결량
        SELN_TR_PBMN: str    #매도거래대금
        SHNU_CNQN: str    #매수2체결량
        SHNU_TR_PBMN: str    #매수2거래대금
        NTBY_CNQN: str    #순매수체결량
        NTBY_TR_PBMN: str    #순매수거래대금
        SELN_RSQN: str    #매도호가잔량
        SHNU_RSQN: str    #매수호가잔량
        WHOL_NTBY_QTY: str    #전체순매수호가잔량
    
    @dataclass
    class ResponseBodyMKSC_SHRN_ISCD:
    
    

복사하기