# NAV 비교추이(일)

> API 경로: `/uapi/etfetn/v1/quotations/nav-comparison-daily-trend`

---

# RESTNAV 비교추이(일)[v1_국내주식-071]

**NAV 비교추이(일)[v1_국내주식-071] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/etfetn/v1/quotations/nav-comparison-daily-trend  
---|---|---|---  
실전 Domain  |  | 모의 Domain |   
실전 TR ID  | FHPST02440200 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    NAV 비교추이(일) API입니다.
    한국투자 HTS(eFriend Plus) > [0244] ETF/ETN 비교추이(NAV/IIV) 좌측 화면 "일별" 비교추이 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    실전계좌의 경우, 한 번의 호출에 최대 100건까지 확인 가능합니다.

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
tr_id | 거래ID | String | Y | 13 | FHPST02440200  
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
fid_cond_mrkt_div_code | FID 조건 시장 분류 코드 | String | Y | 2 | J 입력  
fid_input_iscd | FID 입력 종목코드 | String | Y | 12 | 종목코드 (6자리)  
fid_input_date_1 | FID 입력 날짜1 | String | Y | 10 | 조회 시작일자 (ex. 20240101)  
fid_input_date_2 | FID 입력 날짜2 | String | Y | 10 | 조회 종료일자 (ex. 20240220)  
  
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
stck_bsop_date  | 주식 영업 일자 | String | Y | 8 |   
stck_clpr  | 주식 종가 | String | Y | 10 |   
prdy_vrss  | 전일 대비 | String | Y | 10 |   
prdy_vrss_sign  | 전일 대비 부호 | String | Y | 1 |   
prdy_ctrt  | 전일 대비율 | String | Y | 82 |   
acml_vol  | 누적 거래량 | String | Y | 18 |   
cntg_vol  | 체결 거래량 | String | Y | 18 |   
dprt  | 괴리율 | String | Y | 82 |   
nav_vrss_prpr  | NAV 대비 현재가 | String | Y | 112 |   
nav  | NAV | String | Y | 112 |   
nav_prdy_vrss_sign  | NAV 전일 대비 부호 | String | Y | 1 |   
nav_prdy_vrss  | NAV 전일 대비 | String | Y | 112 |   
nav_prdy_ctrt  | NAV 전일 대비율 | String | Y | 84 |   
  
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
        fid_cond_mrkt_div_code: str    #FID 조건 시장 분류 코드
        fid_input_iscd: str    #FID 입력 종목코드
        fid_input_date_1: str    #FID 입력 날짜1
        fid_input_date_2: str    #FID 입력 날짜2
    
    

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
        stck_bsop_date: str    #주식 영업 일자
        stck_clpr: str    #주식 종가
        prdy_vrss: str    #전일 대비
        prdy_vrss_sign: str    #전일 대비 부호
        prdy_ctrt: str    #전일 대비율
        acml_vol: str    #누적 거래량
        cntg_vol: str    #체결 거래량
        dprt: str    #괴리율
        nav_vrss_prpr: str    #NAV 대비 현재가
        nav: str    #NAV
        nav_prdy_vrss_sign: str    #NAV 전일 대비 부호
        nav_prdy_vrss: str    #NAV 전일 대비
        nav_prdy_ctrt: str    #NAV 전일 대비율
    
    

복사하기