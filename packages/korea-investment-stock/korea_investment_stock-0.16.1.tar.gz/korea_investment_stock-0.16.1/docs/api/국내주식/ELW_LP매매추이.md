# ELW LP매매추이

> API 경로: `/uapi/elw/v1/quotations/lp-trade-trend`

---

# RESTELW LP매매추이 [국내주식-182]

**ELW LP매매추이 [국내주식-182] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/elw/v1/quotations/lp-trade-trend  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 미지원  
실전 TR ID  | FHPEW03760000 | 모의 TR ID |   
Format |  | Content-Type |   
  
## 개요
    
    
    ELW LP매매추이 API입니다.
    한국투자 HTS(eFriend Plus) > [0376] ELW LP매매추이 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

## 요청

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
content-type | 컨텐츠타입 | String | Y | 40 | application/json; charset=utf-8  
authorization | 접근토큰 | String | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token   
일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)   
법인(Access token 유효기간 3개월, Refresh token 유효기간 1년, OAuth 2.0의 Authorization Code Grant 절차를 준용)  
appkey | 앱키 | String | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.)  
appsecret | 앱시크릿키 | String | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.)  
personalseckey | 고객식별키 | String | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키  
tr_id | 거래ID | String | Y | 13 | FHPEW03760000  
tr_cont | 연속 거래 여부 | String | N | 1 | tr_cont를 이용한 다음조회 불가 API  
custtype | 고객 타입 | String | Y | 1 | B : 법인   
P : 개인  
seq_no | 일련번호 | String | N | 2 | [법인 필수] 001  
mac_address | 맥주소 | String | N | 12 | 법인고객 혹은 개인고객의 Mac address 값  
phone_number | 핸드폰번호 | String | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호   
ex) 01011112222 (하이픈 등 구분값 제거)  
ip_addr | 접속 단말 공인 IP | String | N | 12 | [법인 필수] 사용자(회원)의 IP Address  
gt_uid | Global UID | String | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함  
  
### Query Parameter

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
FID_COND_MRKT_DIV_CODE | 조건시장분류코드 | String | Y | 2 | 시장구분(W)  
FID_INPUT_ISCD | 입력종목코드 | String | Y | 12 | 입력종목코드(ex 52K577(미래 K577KOSDAQ150콜)  
  
## 응답

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
content-type | 컨텐츠타입 | String | Y | 40 | application/json; charset=utf-8  
tr_id | 거래ID | String | Y | 13 | 요청한 tr_id  
tr_cont | 연속 거래 여부 | String | N | 1 | tr_cont를 이용한 다음조회 불가 API  
gt_uid | Global UID | String | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
rt_cd | 성공 실패 여부 | String | Y | 1 |   
msg_cd | 응답코드 | String | Y | 8 |   
msg1 | 응답메세지 | String | Y | 80 |   
output1 | 응답상세 | Object | Y |  |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
prdy_vrss_sign  | 전일대비부호 | String | Y | 1 |   
prdy_vrss  | 전일대비 | String | Y | 10 |   
prdy_ctrt  | 전일대비율 | String | Y | 82 |   
acml_vol  | 누적거래량 | String | Y | 18 |   
prdy_vol  | 전일거래량 | String | Y | 18 |   
stck_cnvr_rate  | 주식전환비율 | String | Y | 136 |   
prit  | 패리티 | String | Y | 112 |   
lvrg_val  | 레버리지값 | String | Y | 114 |   
gear  | 기어링 | String | Y | 84 |   
prls_qryr_rate  | 손익분기비율 | String | Y | 84 |   
cfp  | 자본지지점 | String | Y | 112 |   
invl_val  | 내재가치값 | String | Y | 132 |   
tmvl_val  | 시간가치값 | String | Y | 132 |   
acpr  | 행사가 | String | Y | 112 |   
elw_ko_barrier  | 조기종료발생기준가격 | String | Y | 112 |   
output2 | 응답상세 | Object Array | Y |  | array  
stck_bsop_date  | 주식영업일자 | String | Y | 8 |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
prdy_vrss_sign  | 전일대비부호 | String | Y | 1 |   
prdy_vrss  | 전일대비 | String | Y | 10 |   
prdy_ctrt  | 전일대비율 | String | Y | 82 |   
lp_seln_qty  | LP매도수량 | String | Y | 19 |   
lp_seln_avrg_unpr  | LP매도평균단가 | String | Y | 19 |   
lp_shnu_qty  | LP매수수량 | String | Y | 19 |   
lp_shnu_avrg_unpr  | LP매수평균단가 | String | Y | 19 |   
lp_hvol  | LP보유량 | String | Y | 18 |   
lp_hldn_rate  | LP보유비율 | String | Y | 84 |   
prsn_deal_qty  | 개인매매수량 | String | Y | 19 |   
apprch_rate  | 접근도 | String | Y | 112 |   
  
## 예시

### Request

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    
    @dataclass
    class RequestHeader:
        content-type: str    #컨텐츠타입
        authorization: str    #접근토큰
        appkey: str    #앱키
        appsecret: str    #앱시크릿키
        personalseckey: Optional[str] = None    #고객식별키
        tr_id: str    #거래ID
        tr_cont: Optional[str] = None    #연속 거래 여부
        custtype: str    #고객 타입
        seq_no: Optional[str] = None    #일련번호
        mac_address: Optional[str] = None    #맥주소
        phone_number: Optional[str] = None    #핸드폰번호
        ip_addr: Optional[str] = None    #접속 단말 공인 IP
        gt_uid: Optional[str] = None    #Global UID
    
    @dataclass
    class RequestQueryParam:
        FID_COND_MRKT_DIV_CODE: str    #조건시장분류코드
        FID_INPUT_ISCD: str    #입력종목코드
    
    

복사하기

### Response

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class ResponseHeader:
        content-type: str    #컨텐츠타입
        tr_id: str    #거래ID
        tr_cont: Optional[str] = None    #연속 거래 여부
        gt_uid: Optional[str] = None    #Global UID
    
    @dataclass
    class ResponseBody:
        rt_cd: str    #성공 실패 여부
        msg_cd: str    #응답코드
        msg1: str    #응답메세지
        output1: ResponseBodyoutput1    #응답상세
        output2: List[ResponseBodyoutput2] = field(default_factory=list)    #응답상세
    
    @dataclass
    class ResponseBodyoutput1:
        elw_prpr: str    #ELW현재가
        prdy_vrss_sign: str    #전일대비부호
        prdy_vrss: str    #전일대비
        prdy_ctrt: str    #전일대비율
        acml_vol: str    #누적거래량
        prdy_vol: str    #전일거래량
        stck_cnvr_rate: str    #주식전환비율
        prit: str    #패리티
        lvrg_val: str    #레버리지값
        gear: str    #기어링
        prls_qryr_rate: str    #손익분기비율
        cfp: str    #자본지지점
        invl_val: str    #내재가치값
        tmvl_val: str    #시간가치값
        acpr: str    #행사가
        elw_ko_barrier: str    #조기종료발생기준가격
    
    @dataclass
    class ResponseBodyoutput2:
        stck_bsop_date: str    #주식영업일자
        elw_prpr: str    #ELW현재가
        prdy_vrss_sign: str    #전일대비부호
        prdy_vrss: str    #전일대비
        prdy_ctrt: str    #전일대비율
        lp_seln_qty: str    #LP매도수량
        lp_seln_avrg_unpr: str    #LP매도평균단가
        lp_shnu_qty: str    #LP매수수량
        lp_shnu_avrg_unpr: str    #LP매수평균단가
        lp_hvol: str    #LP보유량
        lp_hldn_rate: str    #LP보유비율
        prsn_deal_qty: str    #개인매매수량
        apprch_rate: str    #접근도
    
    

복사하기