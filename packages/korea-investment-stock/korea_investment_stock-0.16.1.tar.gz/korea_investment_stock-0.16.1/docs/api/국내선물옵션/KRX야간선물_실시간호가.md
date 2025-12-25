# KRX야간선물 실시간호가

> API 경로: `/tryitout/H0MFASP0`

---

# WEBSOCKETKRX야간선물 실시간호가 [실시간-065]

**KRX야간선물 실시간호가 [실시간-065] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0MFASP0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0MFASP0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ※ 선물옵션 호가 데이터는 0.2초 필터링 옵션이 있습니다.
      필터링 사유는 순간적으로 데이터가 폭증할 경우 서버 뿐만아니라 클라이언트 환경에도 부하를 줄 수 있어 적용된 사항인 점 양해 부탁드립니다.
    
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
tr_id | 거래ID | String | Y | 2 | H0MFASP0  
tr_key | 구분값 | String | Y | 12 | 야간선물 종목코드  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
FUTS_SHRN_ISCD | 선물 단축 종목코드 | String | Y | 9 |   
BSOP_HOUR | 영업 시간 | String | Y | 6 |   
FUTS_ASKP1 | 선물 매도호가1 | String | Y | 8 |   
FUTS_ASKP2 | 선물 매도호가2 | String | Y | 8 |   
FUTS_ASKP3 | 선물 매도호가3 | String | Y | 8 |   
FUTS_ASKP4 | 선물 매도호가4 | String | Y | 8 |   
FUTS_ASKP5 | 선물 매도호가5 | String | Y | 8 |   
FUTS_BIDP1 | 선물 매수호가1 | String | Y | 8 |   
FUTS_BIDP2 | 선물 매수호가2 | String | Y | 8 |   
FUTS_BIDP3 | 선물 매수호가3 | String | Y | 8 |   
FUTS_BIDP4 | 선물 매수호가4 | String | Y | 8 |   
FUTS_BIDP5 | 선물 매수호가5 | String | Y | 8 |   
ASKP_CSNU1 | 매도호가 건수1 | String | Y | 4 |   
ASKP_CSNU2 | 매도호가 건수2 | String | Y | 4 |   
ASKP_CSNU3 | 매도호가 건수3 | String | Y | 4 |   
ASKP_CSNU4 | 매도호가 건수4 | String | Y | 4 |   
ASKP_CSNU5 | 매도호가 건수5 | String | Y | 4 |   
BIDP_CSNU1 | 매수호가 건수1 | String | Y | 4 |   
BIDP_CSNU2 | 매수호가 건수2 | String | Y | 4 |   
BIDP_CSNU3 | 매수호가 건수3 | String | Y | 4 |   
BIDP_CSNU4 | 매수호가 건수4 | String | Y | 4 |   
BIDP_CSNU5 | 매수호가 건수5 | String | Y | 4 |   
ASKP_RSQN1 | 매도호가 잔량1 | String | Y | 8 |   
ASKP_RSQN2 | 매도호가 잔량2 | String | Y | 8 |   
ASKP_RSQN3 | 매도호가 잔량3 | String | Y | 8 |   
ASKP_RSQN4 | 매도호가 잔량4 | String | Y | 8 |   
ASKP_RSQN5 | 매도호가 잔량5 | String | Y | 8 |   
BIDP_RSQN1 | 매수호가 잔량1 | String | Y | 8 |   
BIDP_RSQN2 | 매수호가 잔량2 | String | Y | 8 |   
BIDP_RSQN3 | 매수호가 잔량3 | String | Y | 8 |   
BIDP_RSQN4 | 매수호가 잔량4 | String | Y | 8 |   
BIDP_RSQN5 | 매수호가 잔량5 | String | Y | 8 |   
TOTAL_ASKP_CSNU | 총 매도호가 건수 | String | Y | 4 |   
TOTAL_BIDP_CSNU | 총 매수호가 건수 | String | Y | 4 |   
TOTAL_ASKP_RSQN | 총 매도호가 잔량 | String | Y | 8 |   
TOTAL_BIDP_RSQN | 총 매수호가 잔량 | String | Y | 8 |   
TOTAL_ASKP_RSQN_ICDC | 총 매도호가 잔량 증감 | String | Y | 4 |   
TOTAL_BIDP_RSQN_ICDC | 총 매수호가 잔량 증감 | String | Y | 4 |   
  
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
        FUTS_SHRN_ISCD: str    #선물 단축 종목코드
        BSOP_HOUR: str    #영업 시간
        FUTS_ASKP1: str    #선물 매도호가1
        FUTS_ASKP2: str    #선물 매도호가2
        FUTS_ASKP3: str    #선물 매도호가3
        FUTS_ASKP4: str    #선물 매도호가4
        FUTS_ASKP5: str    #선물 매도호가5
        FUTS_BIDP1: str    #선물 매수호가1
        FUTS_BIDP2: str    #선물 매수호가2
        FUTS_BIDP3: str    #선물 매수호가3
        FUTS_BIDP4: str    #선물 매수호가4
        FUTS_BIDP5: str    #선물 매수호가5
        ASKP_CSNU1: str    #매도호가 건수1
        ASKP_CSNU2: str    #매도호가 건수2
        ASKP_CSNU3: str    #매도호가 건수3
        ASKP_CSNU4: str    #매도호가 건수4
        ASKP_CSNU5: str    #매도호가 건수5
        BIDP_CSNU1: str    #매수호가 건수1
        BIDP_CSNU2: str    #매수호가 건수2
        BIDP_CSNU3: str    #매수호가 건수3
        BIDP_CSNU4: str    #매수호가 건수4
        BIDP_CSNU5: str    #매수호가 건수5
        ASKP_RSQN1: str    #매도호가 잔량1
        ASKP_RSQN2: str    #매도호가 잔량2
        ASKP_RSQN3: str    #매도호가 잔량3
        ASKP_RSQN4: str    #매도호가 잔량4
        ASKP_RSQN5: str    #매도호가 잔량5
        BIDP_RSQN1: str    #매수호가 잔량1
        BIDP_RSQN2: str    #매수호가 잔량2
        BIDP_RSQN3: str    #매수호가 잔량3
        BIDP_RSQN4: str    #매수호가 잔량4
        BIDP_RSQN5: str    #매수호가 잔량5
        TOTAL_ASKP_CSNU: str    #총 매도호가 건수
        TOTAL_BIDP_CSNU: str    #총 매수호가 건수
        TOTAL_ASKP_RSQN: str    #총 매도호가 잔량
        TOTAL_BIDP_RSQN: str    #총 매수호가 잔량
        TOTAL_ASKP_RSQN_ICDC: str    #총 매도호가 잔량 증감
        TOTAL_BIDP_RSQN_ICDC: str    #총 매수호가 잔량 증감
    
    

복사하기