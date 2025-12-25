# ELW 실시간체결가

> API 경로: `/tryitout/H0EWCNT0`

---

# WEBSOCKETELW 실시간체결가 [실시간-061]

**ELW 실시간체결가 [실시간-061] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0EWCNT0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0EWCNT0 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ELW 실시간체결가 API입니다.
    
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
tr_id | 거래ID | String | Y | 2 | H0EWCNT0  
tr_key | 구분값 | String | Y | 12 | ELW 종목코드(ex. 57LA24)  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
MKSC_SHRN_ISCD | 유가증권단축종목코드 | String | Y | 9 |   
STCK_CNTG_HOUR | 주식체결시간 | String | Y | 6 |   
STCK_PRPR | 주식현재가 | String | Y | 4 |   
PRDY_VRSS_SIGN | 전일대비부호 | String | Y | 1 |   
PRDY_VRSS | 전일대비 | String | Y | 4 |   
PRDY_CTRT | 전일대비율 | String | Y | 8 |   
WGHN_AVRG_STCK_PRC | 가중평균주식가격 | String | Y | 8 |   
STCK_OPRC | 주식시가2 | String | Y | 4 |   
STCK_HGPR | 주식최고가 | String | Y | 4 |   
STCK_LWPR | 주식최저가 | String | Y | 4 |   
ASKP1 | 매도호가1 | String | Y | 4 |   
BIDP1 | 매수호가1 | String | Y | 4 |   
CNTG_VOL | 체결거래량 | String | Y | 8 |   
ACML_VOL | 누적거래량 | String | Y | 8 |   
ACML_TR_PBMN | 누적거래대금 | String | Y | 8 |   
SELN_CNTG_CSNU | 매도체결건수 | String | Y | 4 |   
SHNU_CNTG_CSNU | 매수체결건수 | String | Y | 4 |   
NTBY_CNTG_CSNU | 순매수체결건수 | String | Y | 4 |   
CTTR | 체결강도 | String | Y | 8 |   
SELN_CNTG_SMTN | 총매도수량 | String | Y | 8 |   
SHNU_CNTG_SMTN | 총매수수량 | String | Y | 8 |   
CNTG_CLS_CODE | 체결구분코드 | String | Y | 1 |   
SHNU_RATE | 매수2비율 | String | Y | 8 |   
PRDY_VOL_VRSS_ACML_VOL_RATE | 전일거래량대비등락율 | String | Y | 8 |   
OPRC_HOUR | 시가시간 | String | Y | 6 |   
OPRC_VRSS_PRPR_SIGN | 시가2대비현재가부호 | String | Y | 1 |   
OPRC_VRSS_PRPR | 시가2대비현재가 | String | Y | 4 |   
HGPR_HOUR | 최고가시간 | String | Y | 6 |   
HGPR_VRSS_PRPR_SIGN | 최고가대비현재가부호 | String | Y | 1 |   
HGPR_VRSS_PRPR | 최고가대비현재가 | String | Y | 4 |   
LWPR_HOUR | 최저가시간 | String | Y | 6 |   
LWPR_VRSS_PRPR_SIGN | 최저가대비현재가부호 | String | Y | 1 |   
LWPR_VRSS_PRPR | 최저가대비현재가 | String | Y | 4 |   
BSOP_DATE | 영업일자 | String | Y | 8 |   
NEW_MKOP_CLS_CODE | 신장운영구분코드 | String | Y | 2 |   
TRHT_YN | 거래정지여부 | String | Y | 1 |   
ASKP_RSQN1 | 매도호가잔량1 | String | Y | 8 |   
BIDP_RSQN1 | 매수호가잔량1 | String | Y | 8 |   
TOTAL_ASKP_RSQN | 총매도호가잔량 | String | Y | 8 |   
TOTAL_BIDP_RSQN | 총매수호가잔량 | String | Y | 8 |   
TMVL_VAL | 시간가치값 | String | Y | 8 |   
PRIT | 패리티 | String | Y | 8 |   
PRMM_VAL | 프리미엄값 | String | Y | 8 |   
GEAR | 기어링 | String | Y | 8 |   
PRLS_QRYR_RATE | 손익분기비율 | String | Y | 8 |   
INVL_VAL | 내재가치값 | String | Y | 8 |   
PRMM_RATE | 프리미엄비율 | String | Y | 8 |   
CFP | 자본지지점 | String | Y | 8 |   
LVRG_VAL | 레버리지값 | String | Y | 8 |   
DELTA | 델타 | String | Y | 8 |   
GAMA | 감마 | String | Y | 8 |   
VEGA | 베가 | String | Y | 8 |   
THETA | 세타 | String | Y | 8 |   
RHO | 로우 | String | Y | 8 |   
HTS_INTS_VLTL | HTS내재변동성 | String | Y | 8 |   
HTS_THPR | HTS이론가 | String | Y | 8 |   
VOL_TNRT | 거래량회전율 | String | Y | 8 |   
PRDY_SMNS_HOUR_ACML_VOL | 전일동시간누적거래량 | String | Y | 8 |   
PRDY_SMNS_HOUR_ACML_VOL_RATE | 전일동시간누적거래량비율 | String | Y | 8 |   
APPRCH_RATE | 접근도 | String | Y | 8 |   
LP_HVOL | LP보유량 | String | Y | 8 |   
LP_HLDN_RATE | LP보유비율 | String | Y | 8 |   
LP_NTBY_QTY | LP순매도량 | String | Y | 8 |   
  
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
        STCK_CNTG_HOUR: str    #주식체결시간
        STCK_PRPR: str    #주식현재가
        PRDY_VRSS_SIGN: str    #전일대비부호
        PRDY_VRSS: str    #전일대비
        PRDY_CTRT: str    #전일대비율
        WGHN_AVRG_STCK_PRC: str    #가중평균주식가격
        STCK_OPRC: str    #주식시가2
        STCK_HGPR: str    #주식최고가
        STCK_LWPR: str    #주식최저가
        ASKP1: str    #매도호가1
        BIDP1: str    #매수호가1
        CNTG_VOL: str    #체결거래량
        ACML_VOL: str    #누적거래량
        ACML_TR_PBMN: str    #누적거래대금
        SELN_CNTG_CSNU: str    #매도체결건수
        SHNU_CNTG_CSNU: str    #매수체결건수
        NTBY_CNTG_CSNU: str    #순매수체결건수
        CTTR: str    #체결강도
        SELN_CNTG_SMTN: str    #총매도수량
        SHNU_CNTG_SMTN: str    #총매수수량
        CNTG_CLS_CODE: str    #체결구분코드
        SHNU_RATE: str    #매수2비율
        PRDY_VOL_VRSS_ACML_VOL_RATE: str    #전일거래량대비등락율
        OPRC_HOUR: str    #시가시간
        OPRC_VRSS_PRPR_SIGN: str    #시가2대비현재가부호
        OPRC_VRSS_PRPR: str    #시가2대비현재가
        HGPR_HOUR: str    #최고가시간
        HGPR_VRSS_PRPR_SIGN: str    #최고가대비현재가부호
        HGPR_VRSS_PRPR: str    #최고가대비현재가
        LWPR_HOUR: str    #최저가시간
        LWPR_VRSS_PRPR_SIGN: str    #최저가대비현재가부호
        LWPR_VRSS_PRPR: str    #최저가대비현재가
        BSOP_DATE: str    #영업일자
        NEW_MKOP_CLS_CODE: str    #신장운영구분코드
        TRHT_YN: str    #거래정지여부
        ASKP_RSQN1: str    #매도호가잔량1
        BIDP_RSQN1: str    #매수호가잔량1
        TOTAL_ASKP_RSQN: str    #총매도호가잔량
        TOTAL_BIDP_RSQN: str    #총매수호가잔량
        TMVL_VAL: str    #시간가치값
        PRIT: str    #패리티
        PRMM_VAL: str    #프리미엄값
        GEAR: str    #기어링
        PRLS_QRYR_RATE: str    #손익분기비율
        INVL_VAL: str    #내재가치값
        PRMM_RATE: str    #프리미엄비율
        CFP: str    #자본지지점
        LVRG_VAL: str    #레버리지값
        DELTA: str    #델타
        GAMA: str    #감마
        VEGA: str    #베가
        THETA: str    #세타
        RHO: str    #로우
        HTS_INTS_VLTL: str    #HTS내재변동성
        HTS_THPR: str    #HTS이론가
        VOL_TNRT: str    #거래량회전율
        PRDY_SMNS_HOUR_ACML_VOL: str    #전일동시간누적거래량
        PRDY_SMNS_HOUR_ACML_VOL_RATE: str    #전일동시간누적거래량비율
        APPRCH_RATE: str    #접근도
        LP_HVOL: str    #LP보유량
        LP_HLDN_RATE: str    #LP보유비율
        LP_NTBY_QTY: str    #LP순매도량
    
    

복사하기