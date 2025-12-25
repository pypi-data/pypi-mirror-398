# ELW 투자지표추이(분별)

> API 경로: `/uapi/elw/v1/quotations/indicator-trend-minute`

---

# RESTELW 투자지표추이(분별) [국내주식-174]

**ELW 투자지표추이(분별) [국내주식-174] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/elw/v1/quotations/indicator-trend-minute  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 미지원  
실전 TR ID  | FHPEW02740300 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ELW 투자지표추이(분별) API입니다.
    한국투자 HTS(eFriend Plus) > [0274] ELW 투자지표추이 화면 데이터의 "분별 비교추이" 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다. 

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
tr_id | 거래ID | String | Y | 13 | FHPEW02740300  
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
FID_COND_MRKT_DIV_CODE | 조건시장분류코드 | String | Y | 2 | 시장구분코드 (W)  
FID_INPUT_ISCD | 입력종목코드 | String | Y | 12 | ex) 58J297(KBJ297삼성전자콜)  
FID_HOUR_CLS_CODE | 시간구분코드 | String | Y | 5 | '60(1분), 180(3분), 300(5분), 600(10분), 1800(30분), 3600(60분), 7200(60분)  
'  
FID_PW_DATA_INCU_YN | 과거데이터 포함 여부 | String | Y | 2 | N(과거데이터포함X),Y(과거데이터포함O)  
  
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
output | 응답상세 | Object Array | Y |  | array  
stck_bsop_date  | 주식영업일자 | String | Y | 8 |   
stck_cntg_hour  | 주식체결시간 | String | Y | 6 |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
elw_oprc  | ELW시가2 | String | Y | 10 |   
elw_hgpr  | ELW최고가 | String | Y | 10 |   
elw_lwpr  | ELW최저가 | String | Y | 10 |   
lvrg_val  | 레버리지값 | String | Y | 114 |   
gear  | 기어링 | String | Y | 84 |   
prmm_val  | 프리미엄값 | String | Y | 114 |   
invl_val  | 내재가치값 | String | Y | 132 |   
prit  | 패리티 | String | Y | 112 |   
acml_vol  | 누적거래량 | String | Y | 18 |   
cntg_vol  | 체결거래량 | String | Y | 18 |   
  
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
        FID_HOUR_CLS_CODE: str    #시간구분코드
        FID_PW_DATA_INCU_YN: str    #과거데이터 포함 여부
    
    

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
        output: List[ResponseBodyoutput] = field(default_factory=list)    #응답상세
    
    @dataclass
    class ResponseBodyoutput:
        stck_bsop_date: str    #주식영업일자
        stck_cntg_hour: str    #주식체결시간
        elw_prpr: str    #ELW현재가
        elw_oprc: str    #ELW시가2
        elw_hgpr: str    #ELW최고가
        elw_lwpr: str    #ELW최저가
        lvrg_val: str    #레버리지값
        gear: str    #기어링
        prmm_val: str    #프리미엄값
        invl_val: str    #내재가치값
        prit: str    #패리티
        acml_vol: str    #누적거래량
        cntg_vol: str    #체결거래량
    
    

복사하기