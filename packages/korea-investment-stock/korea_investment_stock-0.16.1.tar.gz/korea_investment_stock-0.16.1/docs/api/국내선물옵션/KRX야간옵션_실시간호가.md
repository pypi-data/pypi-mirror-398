# KRX야간옵션 실시간호가

> API 경로: `/tryitout/H0EUASP0`

---

# WEBSOCKETKRX야간옵션 실시간호가 [실시간-033]

**KRX야간옵션 실시간호가 [실시간-033] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0EUASP0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0EUASP0 | 모의 TR ID | 모의투자 미지원  
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
content-type | 컨텐츠타입 | String | Y | 20 | utf-8  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
tr_id | 거래ID | String | Y | 2 | H0EUASP0  
tr_key | 구분값 | String | Y | 12 | 야간옵션 종목코드  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
OPTN_SHRN_ISCD | 옵션단축종목코드 | String | Y | 9 |   
BSOP_HOUR | 영업시간 | String | Y | 6 |   
OPTN_ASKP1 | 옵션매도호가1 | String | Y | 1 |   
OPTN_ASKP2 | 옵션매도호가2 | String | Y | 1 |   
OPTN_ASKP3 | 옵션매도호가3 | String | Y | 1 |   
OPTN_ASKP4 | 옵션매도호가4 | String | Y | 1 |   
OPTN_ASKP5 | 옵션매도호가5 | String | Y | 1 |   
OPTN_BIDP1 | 옵션매수호가1 | String | Y | 1 |   
OPTN_BIDP2 | 옵션매수호가2 | String | Y | 1 |   
OPTN_BIDP3 | 옵션매수호가3 | String | Y | 1 |   
OPTN_BIDP4 | 옵션매수호가4 | String | Y | 1 |   
OPTN_BIDP5 | 옵션매수호가5 | String | Y | 1 |   
ASKP_CSNU1 | 매도호가건수1 | String | Y | 1 |   
ASKP_CSNU2 | 매도호가건수2 | String | Y | 1 |   
ASKP_CSNU3 | 매도호가건수3 | String | Y | 1 |   
ASKP_CSNU4 | 매도호가건수4 | String | Y | 1 |   
ASKP_CSNU5 | 매도호가건수5 | String | Y | 1 |   
BIDP_CSNU1 | 매수호가건수1 | String | Y | 1 |   
BIDP_CSNU2 | 매수호가건수2 | String | Y | 1 |   
BIDP_CSNU3 | 매수호가건수3 | String | Y | 1 |   
BIDP_CSNU4 | 매수호가건수4 | String | Y | 1 |   
BIDP_CSNU5 | 매수호가건수5 | String | Y | 1 |   
ASKP_RSQN1 | 매도호가잔량1 | String | Y | 1 |   
ASKP_RSQN2 | 매도호가잔량2 | String | Y | 1 |   
ASKP_RSQN3 | 매도호가잔량3 | String | Y | 1 |   
ASKP_RSQN4 | 매도호가잔량4 | String | Y | 1 |   
ASKP_RSQN5 | 매도호가잔량5 | String | Y | 1 |   
BIDP_RSQN1 | 매수호가잔량1 | String | Y | 1 |   
BIDP_RSQN2 | 매수호가잔량2 | String | Y | 1 |   
BIDP_RSQN3 | 매수호가잔량3 | String | Y | 1 |   
BIDP_RSQN4 | 매수호가잔량4 | String | Y | 1 |   
BIDP_RSQN5 | 매수호가잔량5 | String | Y | 1 |   
TOTAL_ASKP_CSNU | 총매도호가건수 | String | Y | 1 |   
TOTAL_BIDP_CSNU | 총매수호가건수 | String | Y | 1 |   
TOTAL_ASKP_RSQN | 총매도호가잔량 | String | Y | 1 |   
TOTAL_BIDP_RSQN | 총매수호가잔량 | String | Y | 1 |   
TOTAL_ASKP_RSQN_ICDC | 총매도호가잔량증감 | String | Y | 1 |   
TOTAL_BIDP_RSQN_ICDC | 총매수호가잔량증감 | String | Y | 1 |   
  
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
        OPTN_SHRN_ISCD: str    #옵션단축종목코드
        BSOP_HOUR: str    #영업시간
        OPTN_ASKP1: str    #옵션매도호가1
        OPTN_ASKP2: str    #옵션매도호가2
        OPTN_ASKP3: str    #옵션매도호가3
        OPTN_ASKP4: str    #옵션매도호가4
        OPTN_ASKP5: str    #옵션매도호가5
        OPTN_BIDP1: str    #옵션매수호가1
        OPTN_BIDP2: str    #옵션매수호가2
        OPTN_BIDP3: str    #옵션매수호가3
        OPTN_BIDP4: str    #옵션매수호가4
        OPTN_BIDP5: str    #옵션매수호가5
        ASKP_CSNU1: str    #매도호가건수1
        ASKP_CSNU2: str    #매도호가건수2
        ASKP_CSNU3: str    #매도호가건수3
        ASKP_CSNU4: str    #매도호가건수4
        ASKP_CSNU5: str    #매도호가건수5
        BIDP_CSNU1: str    #매수호가건수1
        BIDP_CSNU2: str    #매수호가건수2
        BIDP_CSNU3: str    #매수호가건수3
        BIDP_CSNU4: str    #매수호가건수4
        BIDP_CSNU5: str    #매수호가건수5
        ASKP_RSQN1: str    #매도호가잔량1
        ASKP_RSQN2: str    #매도호가잔량2
        ASKP_RSQN3: str    #매도호가잔량3
        ASKP_RSQN4: str    #매도호가잔량4
        ASKP_RSQN5: str    #매도호가잔량5
        BIDP_RSQN1: str    #매수호가잔량1
        BIDP_RSQN2: str    #매수호가잔량2
        BIDP_RSQN3: str    #매수호가잔량3
        BIDP_RSQN4: str    #매수호가잔량4
        BIDP_RSQN5: str    #매수호가잔량5
        TOTAL_ASKP_CSNU: str    #총매도호가건수
        TOTAL_BIDP_CSNU: str    #총매수호가건수
        TOTAL_ASKP_RSQN: str    #총매도호가잔량
        TOTAL_BIDP_RSQN: str    #총매수호가잔량
        TOTAL_ASKP_RSQN_ICDC: str    #총매도호가잔량증감
        TOTAL_BIDP_RSQN_ICDC: str    #총매수호가잔량증감
    
    

복사하기