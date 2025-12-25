# KRX야간옵션 실시간체결가

> API 경로: `/tryitout/H0EUCNT0`

---

# WEBSOCKETKRX야간옵션 실시간체결가 [실시간-032]

**KRX야간옵션 실시간체결가 [실시간-032] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /tryitout/H0EUCNT0  
---|---|---|---  
실전 Domain  | ws://ops.koreainvestment.com:21000 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | H0EUCNT0 | 모의 TR ID | 모의투자 미지원  
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
tr_id | 거래ID | String | Y | 2 | H0EUCNT0  
tr_key | 구분값 | String | Y | 12 | 야간옵션 종목코드  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
OPTN_SHRN_ISCD | 옵션단축종목코드 | String | Y | 9 |   
BSOP_HOUR | 영업시간 | String | Y | 6 |   
OPTN_PRPR | 옵션현재가 | String | Y | 1 |   
PRDY_VRSS_SIGN | 전일대비부호 | String | Y | 1 |   
OPTN_PRDY_VRSS | 옵션전일대비 | String | Y | 1 |   
PRDY_CTRT | 전일대비율 | String | Y | 1 |   
OPTN_OPRC | 옵션시가2 | String | Y | 1 |   
OPTN_HGPR | 옵션최고가 | String | Y | 1 |   
OPTN_LWPR | 옵션최저가 | String | Y | 1 |   
LAST_CNQN | 최종거래량 | String | Y | 1 |   
ACML_VOL | 누적거래량 | String | Y | 1 |   
ACML_TR_PBMN | 누적거래대금 | String | Y | 1 |   
HTS_THPR | HTS이론가 | String | Y | 1 |   
HTS_OTST_STPL_QTY | HTS미결제약정수량 | String | Y | 1 |   
OTST_STPL_QTY_ICDC | 미결제약정수량증감 | String | Y | 1 |   
OPRC_HOUR | 시가시간 | String | Y | 6 |   
OPRC_VRSS_PRPR_SIGN | 시가2대비현재가부호 | String | Y | 1 |   
OPRC_VRSS_NMIX_PRPR | 시가대비지수현재가 | String | Y | 1 |   
HGPR_HOUR | 최고가시간 | String | Y | 6 |   
HGPR_VRSS_PRPR_SIGN | 최고가대비현재가부호 | String | Y | 1 |   
HGPR_VRSS_NMIX_PRPR | 최고가대비지수현재가 | String | Y | 1 |   
LWPR_HOUR | 최저가시간 | String | Y | 6 |   
LWPR_VRSS_PRPR_SIGN | 최저가대비현재가부호 | String | Y | 1 |   
LWPR_VRSS_NMIX_PRPR | 최저가대비지수현재가 | String | Y | 1 |   
SHNU_RATE | 매수2비율 | String | Y | 1 |   
PRMM_VAL | 프리미엄값 | String | Y | 1 |   
INVL_VAL | 내재가치값 | String | Y | 1 |   
TMVL_VAL | 시간가치값 | String | Y | 1 |   
DELTA | 델타 | String | Y | 1 |   
GAMA | 감마 | String | Y | 1 |   
VEGA | 베가 | String | Y | 1 |   
THETA | 세타 | String | Y | 1 |   
RHO | 로우 | String | Y | 1 |   
HTS_INTS_VLTL | HTS내재변동성 | String | Y | 1 |   
ESDG | 괴리도 | String | Y | 1 |   
OTST_STPL_RGBF_QTY_ICDC | 미결제약정직전수량증감 | String | Y | 1 |   
THPR_BASIS | 이론베이시스 | String | Y | 1 |   
UNAS_HIST_VLTL | 역사적변동성 | String | Y | 1 |   
CTTR | 체결강도 | String | Y | 1 |   
DPRT | 괴리율 | String | Y | 1 |   
MRKT_BASIS | 시장베이시스 | String | Y | 1 |   
OPTN_ASKP1 | 옵션매도호가1 | String | Y | 1 |   
OPTN_BIDP1 | 옵션매수호가1 | String | Y | 1 |   
ASKP_RSQN1 | 매도호가잔량1 | String | Y | 1 |   
BIDP_RSQN1 | 매수호가잔량1 | String | Y | 1 |   
SELN_CNTG_CSNU | 매도체결건수 | String | Y | 1 |   
SHNU_CNTG_CSNU | 매수체결건수 | String | Y | 1 |   
NTBY_CNTG_CSNU | 순매수체결건수 | String | Y | 1 |   
SELN_CNTG_SMTN | 총매도수량 | String | Y | 1 |   
SHNU_CNTG_SMTN | 총매수수량 | String | Y | 1 |   
TOTAL_ASKP_RSQN | 총매도호가잔량 | String | Y | 1 |   
TOTAL_BIDP_RSQN | 총매수호가잔량 | String | Y | 1 |   
PRDY_VOL_VRSS_ACML_VOL_RATE | 전일거래량대비등락율 | String | Y | 1 |   
DYNM_MXPR | 실시간상한가 | String | Y | 8 |   
DYNM_PRC_LIMT_YN | 실시간가격제한구분 | String | Y | 1 |   
DYNM_LLAM | 실시간하한가 | String | Y | 8 |   
  
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
        OPTN_PRPR: str    #옵션현재가
        PRDY_VRSS_SIGN: str    #전일대비부호
        OPTN_PRDY_VRSS: str    #옵션전일대비
        PRDY_CTRT: str    #전일대비율
        OPTN_OPRC: str    #옵션시가2
        OPTN_HGPR: str    #옵션최고가
        OPTN_LWPR: str    #옵션최저가
        LAST_CNQN: str    #최종거래량
        ACML_VOL: str    #누적거래량
        ACML_TR_PBMN: str    #누적거래대금
        HTS_THPR: str    #HTS이론가
        HTS_OTST_STPL_QTY: str    #HTS미결제약정수량
        OTST_STPL_QTY_ICDC: str    #미결제약정수량증감
        OPRC_HOUR: str    #시가시간
        OPRC_VRSS_PRPR_SIGN: str    #시가2대비현재가부호
        OPRC_VRSS_NMIX_PRPR: str    #시가대비지수현재가
        HGPR_HOUR: str    #최고가시간
        HGPR_VRSS_PRPR_SIGN: str    #최고가대비현재가부호
        HGPR_VRSS_NMIX_PRPR: str    #최고가대비지수현재가
        LWPR_HOUR: str    #최저가시간
        LWPR_VRSS_PRPR_SIGN: str    #최저가대비현재가부호
        LWPR_VRSS_NMIX_PRPR: str    #최저가대비지수현재가
        SHNU_RATE: str    #매수2비율
        PRMM_VAL: str    #프리미엄값
        INVL_VAL: str    #내재가치값
        TMVL_VAL: str    #시간가치값
        DELTA: str    #델타
        GAMA: str    #감마
        VEGA: str    #베가
        THETA: str    #세타
        RHO: str    #로우
        HTS_INTS_VLTL: str    #HTS내재변동성
        ESDG: str    #괴리도
        OTST_STPL_RGBF_QTY_ICDC: str    #미결제약정직전수량증감
        THPR_BASIS: str    #이론베이시스
        UNAS_HIST_VLTL: str    #역사적변동성
        CTTR: str    #체결강도
        DPRT: str    #괴리율
        MRKT_BASIS: str    #시장베이시스
        OPTN_ASKP1: str    #옵션매도호가1
        OPTN_BIDP1: str    #옵션매수호가1
        ASKP_RSQN1: str    #매도호가잔량1
        BIDP_RSQN1: str    #매수호가잔량1
        SELN_CNTG_CSNU: str    #매도체결건수
        SHNU_CNTG_CSNU: str    #매수체결건수
        NTBY_CNTG_CSNU: str    #순매수체결건수
        SELN_CNTG_SMTN: str    #총매도수량
        SHNU_CNTG_SMTN: str    #총매수수량
        TOTAL_ASKP_RSQN: str    #총매도호가잔량
        TOTAL_BIDP_RSQN: str    #총매수호가잔량
        PRDY_VOL_VRSS_ACML_VOL_RATE: str    #전일거래량대비등락율
        DYNM_MXPR: str    #실시간상한가
        DYNM_PRC_LIMT_YN: str    #실시간가격제한구분
        DYNM_LLAM: str    #실시간하한가
    
    

복사하기