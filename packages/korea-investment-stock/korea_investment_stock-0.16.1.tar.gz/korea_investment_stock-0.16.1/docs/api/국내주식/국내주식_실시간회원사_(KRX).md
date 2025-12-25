# 국내주식 실시간회원사 (KRX)

> API 경로: `/tryitout/H0STMBC0`

---

# WEBSOCKET국내주식 실시간회원사 (KRX) [실시간-047]

**국내주식 실시간회원사 (KRX) [실시간-047] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0STMBC0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0STMBC0 | 모의 TR ID | 모의투자 미지원  
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
tr_id | 거래ID | String | Y | 7 | H0STMBC0  
tr_key | 종목코드 | String | Y | 6 | 종목코드  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권단축종목코드 | Object | Y | 9 | '각 항목사이에는 구분자로 ^ 사용,  
모든 데이터타입은 String으로 변환되어 push 처리됨'  
SELN2_MBCR_NAME1 | 매도2회원사명1 | String | Y | 16 |   
SELN2_MBCR_NAME2 | 매도2회원사명2 | String | Y | 16 |   
SELN2_MBCR_NAME3 | 매도2회원사명3 | String | Y | 16 |   
SELN2_MBCR_NAME4 | 매도2회원사명4 | String | Y | 16 |   
SELN2_MBCR_NAME5 | 매도2회원사명5 | String | Y | 16 |   
BYOV_MBCR_NAME1 | 매수회원사명1 | String | Y | 16 |   
BYOV_MBCR_NAME2 | 매수회원사명2 | String | Y | 16 |   
BYOV_MBCR_NAME3 | 매수회원사명3 | String | Y | 16 |   
BYOV_MBCR_NAME4 | 매수회원사명4 | String | Y | 16 |   
BYOV_MBCR_NAME5 | 매수회원사명5 | String | Y | 16 |   
TOTAL_SELN_QTY1 | 총매도수량1 | String | Y | 8 |   
TOTAL_SELN_QTY2 | 총매도수량2 | String | Y | 8 |   
TOTAL_SELN_QTY3 | 총매도수량3 | String | Y | 8 |   
TOTAL_SELN_QTY4 | 총매도수량4 | String | Y | 8 |   
TOTAL_SELN_QTY5 | 총매도수량5 | String | Y | 8 |   
TOTAL_SHNU_QTY1 | 총매수2수량1 | String | Y | 8 |   
TOTAL_SHNU_QTY2 | 총매수2수량2 | String | Y | 8 |   
TOTAL_SHNU_QTY3 | 총매수2수량3 | String | Y | 8 |   
TOTAL_SHNU_QTY4 | 총매수2수량4 | String | Y | 8 |   
TOTAL_SHNU_QTY5 | 총매수2수량5 | String | Y | 8 |   
SELN_MBCR_GLOB_YN_1 | 매도거래원구분1 | String | Y | 1 |   
SELN_MBCR_GLOB_YN_2 | 매도거래원구분2 | String | Y | 1 |   
SELN_MBCR_GLOB_YN_3 | 매도거래원구분3 | String | Y | 1 |   
SELN_MBCR_GLOB_YN_4 | 매도거래원구분4 | String | Y | 1 |   
SELN_MBCR_GLOB_YN_5 | 매도거래원구분5 | String | Y | 1 |   
SHNU_MBCR_GLOB_YN_1 | 매수거래원구분1 | String | Y | 1 |   
SHNU_MBCR_GLOB_YN_2 | 매수거래원구분2 | String | Y | 1 |   
SHNU_MBCR_GLOB_YN_3 | 매수거래원구분3 | String | Y | 1 |   
SHNU_MBCR_GLOB_YN_4 | 매수거래원구분4 | String | Y | 1 |   
SHNU_MBCR_GLOB_YN_5 | 매수거래원구분5 | String | Y | 1 |   
SELN_MBCR_NO1 | 매도거래원코드1 | String | Y | 5 |   
SELN_MBCR_NO2 | 매도거래원코드2 | String | Y | 5 |   
SELN_MBCR_NO3 | 매도거래원코드3 | String | Y | 5 |   
SELN_MBCR_NO4 | 매도거래원코드4 | String | Y | 5 |   
SELN_MBCR_NO5 | 매도거래원코드5 | String | Y | 5 |   
SHNU_MBCR_NO1 | 매수거래원코드1 | String | Y | 5 |   
SHNU_MBCR_NO2 | 매수거래원코드2 | String | Y | 5 |   
SHNU_MBCR_NO3 | 매수거래원코드3 | String | Y | 5 |   
SHNU_MBCR_NO4 | 매수거래원코드4 | String | Y | 5 |   
SHNU_MBCR_NO5 | 매수거래원코드5 | String | Y | 5 |   
SELN_MBCR_RLIM1 | 매도회원사비중1 | String | Y | 8 |   
SELN_MBCR_RLIM2 | 매도회원사비중2 | String | Y | 8 |   
SELN_MBCR_RLIM3 | 매도회원사비중3 | String | Y | 8 |   
SELN_MBCR_RLIM4 | 매도회원사비중4 | String | Y | 8 |   
SELN_MBCR_RLIM5 | 매도회원사비중5 | String | Y | 8 |   
SHNU_MBCR_RLIM1 | 매수2회원사비중1 | String | Y | 8 |   
SHNU_MBCR_RLIM2 | 매수2회원사비중2 | String | Y | 8 |   
SHNU_MBCR_RLIM3 | 매수2회원사비중3 | String | Y | 8 |   
SHNU_MBCR_RLIM4 | 매수2회원사비중4 | String | Y | 8 |   
SHNU_MBCR_RLIM5 | 매수2회원사비중5 | String | Y | 8 |   
SELN_QTY_ICDC1 | 매도수량증감1 | String | Y | 4 |   
SELN_QTY_ICDC2 | 매도수량증감2 | String | Y | 4 |   
SELN_QTY_ICDC3 | 매도수량증감3 | String | Y | 4 |   
SELN_QTY_ICDC4 | 매도수량증감4 | String | Y | 4 |   
SELN_QTY_ICDC5 | 매도수량증감5 | String | Y | 4 |   
SHNU_QTY_ICDC1 | 매수2수량증감1 | String | Y | 4 |   
SHNU_QTY_ICDC2 | 매수2수량증감2 | String | Y | 4 |   
SHNU_QTY_ICDC3 | 매수2수량증감3 | String | Y | 4 |   
SHNU_QTY_ICDC4 | 매수2수량증감4 | String | Y | 4 |   
SHNU_QTY_ICDC5 | 매수2수량증감5 | String | Y | 4 |   
GLOB_TOTAL_SELN_QTY | 외국계총매도수량 | String | Y | 8 |   
GLOB_TOTAL_SHNU_QTY | 외국계총매수2수량 | String | Y | 8 |   
GLOB_TOTAL_SELN_QTY_ICDC | 외국계총매도수량증감 | String | Y | 4 |   
GLOB_TOTAL_SHNU_QTY_ICDC | 외국계총매수2수량증감 | String | Y | 4 |   
GLOB_NTBY_QTY | 외국계순매수수량 | String | Y | 8 |   
GLOB_SELN_RLIM | 외국계매도비중 | String | Y | 8 |   
GLOB_SHNU_RLIM | 외국계매수2비중 | String | Y | 8 |   
SELN2_MBCR_ENG_NAME1 | 매도2영문회원사명1 | String | Y | 20 |   
SELN2_MBCR_ENG_NAME2 | 매도2영문회원사명2 | String | Y | 20 |   
SELN2_MBCR_ENG_NAME3 | 매도2영문회원사명3 | String | Y | 20 |   
SELN2_MBCR_ENG_NAME4 | 매도2영문회원사명4 | String | Y | 20 |   
SELN2_MBCR_ENG_NAME5 | 매도2영문회원사명5 | String | Y | 20 |   
BYOV_MBCR_ENG_NAME1 | 매수영문회원사명1 | String | Y | 20 |   
BYOV_MBCR_ENG_NAME2 | 매수영문회원사명2 | String | Y | 20 |   
BYOV_MBCR_ENG_NAME3 | 매수영문회원사명3 | String | Y | 20 |   
BYOV_MBCR_ENG_NAME4 | 매수영문회원사명4 | String | Y | 20 |   
BYOV_MBCR_ENG_NAME5 | 매수영문회원사명5 | String | Y | 20 |   
  
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
        SELN2_MBCR_NAME1: str    #매도2회원사명1
        SELN2_MBCR_NAME2: str    #매도2회원사명2
        SELN2_MBCR_NAME3: str    #매도2회원사명3
        SELN2_MBCR_NAME4: str    #매도2회원사명4
        SELN2_MBCR_NAME5: str    #매도2회원사명5
        BYOV_MBCR_NAME1: str    #매수회원사명1
        BYOV_MBCR_NAME2: str    #매수회원사명2
        BYOV_MBCR_NAME3: str    #매수회원사명3
        BYOV_MBCR_NAME4: str    #매수회원사명4
        BYOV_MBCR_NAME5: str    #매수회원사명5
        TOTAL_SELN_QTY1: str    #총매도수량1
        TOTAL_SELN_QTY2: str    #총매도수량2
        TOTAL_SELN_QTY3: str    #총매도수량3
        TOTAL_SELN_QTY4: str    #총매도수량4
        TOTAL_SELN_QTY5: str    #총매도수량5
        TOTAL_SHNU_QTY1: str    #총매수2수량1
        TOTAL_SHNU_QTY2: str    #총매수2수량2
        TOTAL_SHNU_QTY3: str    #총매수2수량3
        TOTAL_SHNU_QTY4: str    #총매수2수량4
        TOTAL_SHNU_QTY5: str    #총매수2수량5
        SELN_MBCR_GLOB_YN_1: str    #매도거래원구분1
        SELN_MBCR_GLOB_YN_2: str    #매도거래원구분2
        SELN_MBCR_GLOB_YN_3: str    #매도거래원구분3
        SELN_MBCR_GLOB_YN_4: str    #매도거래원구분4
        SELN_MBCR_GLOB_YN_5: str    #매도거래원구분5
        SHNU_MBCR_GLOB_YN_1: str    #매수거래원구분1
        SHNU_MBCR_GLOB_YN_2: str    #매수거래원구분2
        SHNU_MBCR_GLOB_YN_3: str    #매수거래원구분3
        SHNU_MBCR_GLOB_YN_4: str    #매수거래원구분4
        SHNU_MBCR_GLOB_YN_5: str    #매수거래원구분5
        SELN_MBCR_NO1: str    #매도거래원코드1
        SELN_MBCR_NO2: str    #매도거래원코드2
        SELN_MBCR_NO3: str    #매도거래원코드3
        SELN_MBCR_NO4: str    #매도거래원코드4
        SELN_MBCR_NO5: str    #매도거래원코드5
        SHNU_MBCR_NO1: str    #매수거래원코드1
        SHNU_MBCR_NO2: str    #매수거래원코드2
        SHNU_MBCR_NO3: str    #매수거래원코드3
        SHNU_MBCR_NO4: str    #매수거래원코드4
        SHNU_MBCR_NO5: str    #매수거래원코드5
        SELN_MBCR_RLIM1: str    #매도회원사비중1
        SELN_MBCR_RLIM2: str    #매도회원사비중2
        SELN_MBCR_RLIM3: str    #매도회원사비중3
        SELN_MBCR_RLIM4: str    #매도회원사비중4
        SELN_MBCR_RLIM5: str    #매도회원사비중5
        SHNU_MBCR_RLIM1: str    #매수2회원사비중1
        SHNU_MBCR_RLIM2: str    #매수2회원사비중2
        SHNU_MBCR_RLIM3: str    #매수2회원사비중3
        SHNU_MBCR_RLIM4: str    #매수2회원사비중4
        SHNU_MBCR_RLIM5: str    #매수2회원사비중5
        SELN_QTY_ICDC1: str    #매도수량증감1
        SELN_QTY_ICDC2: str    #매도수량증감2
        SELN_QTY_ICDC3: str    #매도수량증감3
        SELN_QTY_ICDC4: str    #매도수량증감4
        SELN_QTY_ICDC5: str    #매도수량증감5
        SHNU_QTY_ICDC1: str    #매수2수량증감1
        SHNU_QTY_ICDC2: str    #매수2수량증감2
        SHNU_QTY_ICDC3: str    #매수2수량증감3
        SHNU_QTY_ICDC4: str    #매수2수량증감4
        SHNU_QTY_ICDC5: str    #매수2수량증감5
        GLOB_TOTAL_SELN_QTY: str    #외국계총매도수량
        GLOB_TOTAL_SHNU_QTY: str    #외국계총매수2수량
        GLOB_TOTAL_SELN_QTY_ICDC: str    #외국계총매도수량증감
        GLOB_TOTAL_SHNU_QTY_ICDC: str    #외국계총매수2수량증감
        GLOB_NTBY_QTY: str    #외국계순매수수량
        GLOB_SELN_RLIM: str    #외국계매도비중
        GLOB_SHNU_RLIM: str    #외국계매수2비중
        SELN2_MBCR_ENG_NAME1: str    #매도2영문회원사명1
        SELN2_MBCR_ENG_NAME2: str    #매도2영문회원사명2
        SELN2_MBCR_ENG_NAME3: str    #매도2영문회원사명3
        SELN2_MBCR_ENG_NAME4: str    #매도2영문회원사명4
        SELN2_MBCR_ENG_NAME5: str    #매도2영문회원사명5
        BYOV_MBCR_ENG_NAME1: str    #매수영문회원사명1
        BYOV_MBCR_ENG_NAME2: str    #매수영문회원사명2
        BYOV_MBCR_ENG_NAME3: str    #매수영문회원사명3
        BYOV_MBCR_ENG_NAME4: str    #매수영문회원사명4
        BYOV_MBCR_ENG_NAME5: str    #매수영문회원사명5
    
    @dataclass
    class ResponseBodyMKSC_SHRN_ISCD:
    
    

복사하기