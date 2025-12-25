# 국내주식 장운영정보 (KRX)

> API 경로: `/tryitout/H0STMKO0`

---

# WEBSOCKET국내주식 장운영정보 (KRX) [실시간-049]

**국내주식 장운영정보 (KRX) [실시간-049] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0STMKO0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0STMKO0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    국내주식 장운영정보 연결 시, 연결종목의 VI 발동 시와 VI 해제 시에 데이터 수신됩니다. 
    
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
tr_id | 거래ID | String | Y | 7 | H0STMKO0  
tr_key | 종목코드 | String | Y | 6 | 종목코드  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권단축종목코드 | Object | Y | 9 | '각 항목사이에는 구분자로 ^ 사용,  
모든 데이터타입은 String으로 변환되어 push 처리됨'  
TRHT_YN | 거래정지여부 | String | Y | 1 |   
TR_SUSP_REAS_CNTT | 거래정지사유내용 | String | Y | 100 |   
MKOP_CLS_CODE | 장운영구분코드 | String | Y | 3 | 110 장전 동시호가 개시   
112 장개시   
121 장후 동시호가 개시   
129 장마감   
130 장개시전시간외개시   
139 장개시전시간외종료   
140 시간외 종가 매매 개시   
146 장종료후시간외 체결지시   
149 시간외 종가 매매 종료   
150 시간외 단일가 매매 개시   
156 시간외단일가 체결지시   
159 시간외 단일가 매매 종료   
164 시장임시정지   
174 서킷브레이크 발동   
175 서킷브레이크 해제   
182 서킷브레이크 장중동시마감   
184 서킷브레이크 개시   
185 서킷브레이크 해제   
387 사이드카 매도발동   
388 사이드카 매도발동해제   
397 사이드카 매수발동   
398 사이드카 매수발동해제   
??? 단일가개시   
??? 서킷브레이크 단일가접수   
F01 장개시 10초전   
F06 장개시 1분전   
F07 장개시 5분전   
F08 장개시 10분전   
F09 장개시 3분전   
F11 장마감 10초전   
F16 장마감 1분전   
F17 장마감 5분전   
F18 장마감 3분전   
P01 장개시 10초전   
P06 장개시 1분전   
P07 장개시 5분전   
P08 장개시 10분전   
P09 장개시 30분전   
P11 장마감 10초전   
P16 장마감 1분전   
P17 장마감 5분전   
P18 장마감 3분전  
ANTC_MKOP_CLS_CODE | 예상장운영구분코드 | String | Y | 3 | 112 장전예상종료   
121 장후예상시작  
129 장후예상종료  
311 장전예상시작  
MRKT_TRTM_CLS_CODE | 임의연장구분코드 | String | Y | 1 |  1 시초동시 임의종료 지정  
2 시초동시 임의종료 해제   
3 마감동시 임의종료 지정   
4 마감동시 임의종료 해제   
5 시간외단일가임의종료 지정   
6 시간외단일가임의종료 해제  
DIVI_APP_CLS_CODE | 동시호가배분처리구분코드 | String | Y | 2 | divi_app_cls_code[0] 1: 배분개시 2: 배분해제  
divi_app_cls_code[1] 1: 매수상한 2: 매수하한 3: 매도상한 4: 매도하한  
ISCD_STAT_CLS_CODE | 종목상태구분코드 | String | Y | 2 | 51 관리종목 지정 종목  
52 시장경고 구분이 '투자위험'인 종목  
53 시장경고 구분이 '투자경고'인 종목  
54 시장경고 구분이 '투자주의'인 종목  
55 당사 신용가능 종목  
57 당사 증거금률이 100인 종목  
58 거래정지 지정된 종목   
59 단기과열종목으로 지정되거나 지정 연장된 종목  
00 그 외 종목  
VI_CLS_CODE | VI적용구분코드 | String | Y | 1 | Y VI적용된 종목  
N VI적용되지 않은 종목  
OVTM_VI_CLS_CODE | 시간외단일가VI적용구분코드 | String | Y | 1 | Y 시간외단일가VI 적용된 종목  
N 시간외단일가VI 적용되지 않은 종목  
EXCH_CLS_CODE | 거래소구분코드 | String | Y | 1 |   
  
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
        TRHT_YN: str    #거래정지여부
        TR_SUSP_REAS_CNTT: str    #거래정지사유내용
        MKOP_CLS_CODE: str    #장운영구분코드
        ANTC_MKOP_CLS_CODE: str    #예상장운영구분코드
        MRKT_TRTM_CLS_CODE: str    #임의연장구분코드
        DIVI_APP_CLS_CODE: str    #동시호가배분처리구분코드
        ISCD_STAT_CLS_CODE: str    #종목상태구분코드
        VI_CLS_CODE: str    #VI적용구분코드
        OVTM_VI_CLS_CODE: str    #시간외단일가VI적용구분코드
        EXCH_CLS_CODE: str    #거래소구분코드
    
    @dataclass
    class ResponseBodyMKSC_SHRN_ISCD:
    
    

복사하기