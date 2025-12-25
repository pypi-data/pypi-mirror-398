# 국내주식 실시간프로그램매매 (NXT)

> API 경로: `/tryitout/H0NXPGM0`

---

# WEBSOCKET국내주식 실시간프로그램매매 (NXT)

**국내주식 실시간프로그램매매 (NXT) 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0NXPGM0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0NXPGM0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요

## 요청

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
approval_key | 웹소켓 접속키 | String | N | 286 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키  
custtype | 고객타입 | String | N | 1 | 'B : 법인  
P : 개인'  
tr_type | 거래타입 | String | N | 1 | '1 : 등록  
2 : 해제'  
content-type | 컨텐츠타입 | String | N | 1 | ' utf-8'  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
tr_id | 거래ID | String | Y | 2 | H0NXPGM0 : 실시간 주식프로그램매매 (NXT)  
tr_key | 구분값 | String | Y | 12 | 종목코드 (ex 005930 삼성전자)  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권 단축 종목코드 | String | Y | 9 |   
STCK_CNTG_HOUR | 주식 체결 시간 | String | Y | 6 |   
SELN_CNQN | 매도 체결량 | String | Y | 8 |   
SELN_TR_PBMN | 매도 거래 대금 | String | Y | 8 |   
SHNU_CNQN | 매수2 체결량 | String | Y | 8 |   
SHNU_TR_PBMN | 매수2 거래 대금 | String | Y | 8 |   
NTBY_CNQN | 순매수 체결량 | String | Y | 8 |   
NTBY_TR_PBMN | 순매수 거래 대금 | String | Y | 8 |   
SELN_RSQN | 매도호가잔량 | String | Y | 8 |   
SHNU_RSQN | 매수호가잔량 | String | Y | 8 |   
WHOL_NTBY_QTY | 전체순매수호가잔량 | String | Y | 8 |   
  
## 예시

### Request

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    
    @dataclass
    class RequestHeader:
        approval_key: Optional[str] = None    #웹소켓 접속키
        custtype: Optional[str] = None    #고객타입
        tr_type: Optional[str] = None    #거래타입
        content-type: Optional[str] = None    #컨텐츠타입
    
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
        MKSC_SHRN_ISCD: str    #유가증권 단축 종목코드
        STCK_CNTG_HOUR: str    #주식 체결 시간
        SELN_CNQN: str    #매도 체결량
        SELN_TR_PBMN: str    #매도 거래 대금
        SHNU_CNQN: str    #매수2 체결량
        SHNU_TR_PBMN: str    #매수2 거래 대금
        NTBY_CNQN: str    #순매수 체결량
        NTBY_TR_PBMN: str    #순매수 거래 대금
        SELN_RSQN: str    #매도호가잔량
        SHNU_RSQN: str    #매수호가잔량
        WHOL_NTBY_QTY: str    #전체순매수호가잔량
    
    

복사하기