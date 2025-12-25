# 국내ETF NAV추이

> API 경로: `/tryitout/H0STNAV0`

---

# WEBSOCKET국내ETF NAV추이 [실시간-051]

**국내ETF NAV추이 [실시간-051] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0STNAV0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0STNAV0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    [참고자료]
    실시간시세(웹소켓) 파이썬 샘플코드는 한국투자증권 Github 참고 부탁드립니다.
    https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/ws_domestic_overseas_all.py
    
    실시간시세(웹소켓) API 사용방법에 대한 자세한 설명은 한국투자증권 Wikidocs 참고 부탁드립니다.
    https://wikidocs.net/book/7847 (국내주식 업데이트 완료, 추후 해외주식·국내선물옵션 업데이트 예정)
    
    종목코드 마스터파일 파이썬 정제코드는 한국투자증권 Github 참고 부탁드립니다.
    https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info

## 요청

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
approval_key | 웹소켓 접속키 | String | Y | 36 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키  
custtype | 고객 타입 | String | Y | 1 | B : 법인 / P : 개인  
tr_type | 등록/해제 | String | Y | 1 | 1: 등록, 2:해제  
content-type | 컨텐츠타입  | String | Y | 20 | utf-8  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
tr_id | 거래ID | String | Y | 2 | H0STNAV0  
tr_key | 구분값 | String | Y | 12 | 종목코드 (ex. 005930 삼성전자)  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권단축종목코드 | String | Y | 9 |   
NAV | NAV | String | Y | 8 |   
NAV_PRDY_VRSS_SIGN | NAV전일대비부호 | String | Y | 1 |   
NAV_PRDY_VRSS | NAV전일대비 | String | Y | 8 |   
NAV_PRDY_CTRT | NAV전일대비율 | String | Y | 8 |   
OPRC_NAV | NAV시가 | String | Y | 8 |   
HPRC_NAV | NAV고가 | String | Y | 8 |   
LPRC_NAV | NAV저가 | String | Y | 8 |   
  
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
        NAV: str    #NAV
        NAV_PRDY_VRSS_SIGN: str    #NAV전일대비부호
        NAV_PRDY_VRSS: str    #NAV전일대비
        NAV_PRDY_CTRT: str    #NAV전일대비율
        OPRC_NAV: str    #NAV시가
        HPRC_NAV: str    #NAV고가
        LPRC_NAV: str    #NAV저가
    
    

복사하기