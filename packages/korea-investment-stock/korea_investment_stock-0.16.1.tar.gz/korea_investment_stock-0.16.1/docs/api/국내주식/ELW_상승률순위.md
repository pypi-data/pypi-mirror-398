# ELW 상승률순위

> API 경로: `/uapi/elw/v1/ranking/updown-rate`

---

# RESTELW 상승률순위[국내주식-167]

**ELW 상승률순위[국내주식-167] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/elw/v1/ranking/updown-rate  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | FHPEW02770000 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ELW 상승률순위 API입니다. 
    한국투자 HTS(eFriend Plus) > [0277] ELW 상승률순위 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

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
tr_id | 거래ID | String | Y | 13 | FHPEW02770000  
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
FID_COND_MRKT_DIV_CODE | 사용자권한정보 | String | Y | 2 | 시장구분코드 (W)  
FID_COND_SCR_DIV_CODE | 거래소코드 | String | Y | 5 | Unique key(20277)  
FID_UNAS_INPUT_ISCD | 상승율/하락율 구분 | String | Y | 12 | '000000(전체), 2001(코스피200)  
, 3003(코스닥150), 005930(삼성전자) '  
FID_INPUT_ISCD | N일자값 | String | Y | 12 | '00000(전체), 00003(한국투자증권)  
, 00017(KB증권), 00005(미래에셋주식회사)'  
FID_INPUT_RMNN_DYNU_1 | 거래량조건 | String | Y | 5 | '0(전체), 1(1개월이하), 2(1개월~2개월),   
3(2개월~3개월), 4(3개월~6개월),  
5(6개월~9개월),6(9개월~12개월), 7(12개월이상)'  
FID_DIV_CLS_CODE | NEXT KEY BUFF | String | Y | 2 | 0(전체), 1(콜), 2(풋)  
FID_INPUT_PRICE_1 | 사용자권한정보 | String | Y | 12 |   
FID_INPUT_PRICE_2 | 거래소코드 | String | Y | 12 |   
FID_INPUT_VOL_1 | 상승율/하락율 구분 | String | Y | 18 |   
FID_INPUT_VOL_2 | N일자값 | String | Y | 18 |   
FID_INPUT_DATE_1 | 거래량조건 | String | Y | 10 |   
FID_RANK_SORT_CLS_CODE | NEXT KEY BUFF | String | Y | 2 | '0(상승율), 1(하락율), 2(시가대비상승율)  
, 3(시가대비하락율), 4(변동율)'  
FID_BLNG_CLS_CODE | 사용자권한정보 | String | Y | 2 | 0(전체)  
FID_INPUT_DATE_2 | 거래소코드 | String | Y | 10 |   
  
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
hts_kor_isnm  | HTS한글종목명 | String | Y | 40 |   
elw_shrn_iscd  | ELW단축종목코드 | String | Y | 9 |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
prdy_vrss  | 전일대비 | String | Y | 10 |   
prdy_vrss_sign  | 전일대비부호 | String | Y | 1 |   
prdy_ctrt  | 전일대비율 | String | Y | 82 |   
acml_vol  | 누적거래량 | String | Y | 18 |   
stck_sdpr  | 주식기준가 | String | Y | 10 |   
sdpr_vrss_prpr_sign  | 기준가대비현재가부호 | String | Y | 1 |   
sdpr_vrss_prpr  | 기준가대비현재가 | String | Y | 10 |   
sdpr_vrss_prpr_rate  | 기준가대비현재가비율 | String | Y | 84 |   
stck_oprc  | 주식시가2 | String | Y | 10 |   
oprc_vrss_prpr_sign  | 시가2대비현재가부호 | String | Y | 1 |   
oprc_vrss_prpr  | 시가2대비현재가 | String | Y | 10 |   
oprc_vrss_prpr_rate  | 시가2대비현재가비율 | String | Y | 84 |   
stck_hgpr  | 주식최고가 | String | Y | 10 |   
stck_lwpr  | 주식최저가 | String | Y | 10 |   
prd_rsfl_sign  | 기간등락부호 | String | Y | 1 |   
prd_rsfl  | 기간등락 | String | Y | 10 |   
prd_rsfl_rate  | 기간등락비율 | String | Y | 84 |   
stck_cnvr_rate  | 주식전환비율 | String | Y | 136 |   
hts_rmnn_dynu  | HTS잔존일수 | String | Y | 5 |   
acpr  | 행사가 | String | Y | 112 |   
unas_isnm  | 기초자산명 | String | Y | 40 |   
unas_shrn_iscd  | 기초자산코드 | String | Y | 12 |   
lp_hldn_rate  | LP보유비율 | String | Y | 84 |   
prit  | 패리티 | String | Y | 112 |   
prls_qryr_stpr_prc  | 손익분기주가가격 | String | Y | 112 |   
delta_val  | 델타값 | String | Y | 114 |   
theta  | 세타 | String | Y | 84 |   
prls_qryr_rate  | 손익분기비율 | String | Y | 84 |   
stck_lstn_date  | 주식상장일자 | String | Y | 8 |   
stck_last_tr_date  | 주식최종거래일자 | String | Y | 8 |   
hts_ints_vltl  | HTS내재변동성 | String | Y | 114 |   
lvrg_val  | 레버리지값 | String | Y | 114 |   
  
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
        FID_COND_MRKT_DIV_CODE: str    #사용자권한정보
        FID_COND_SCR_DIV_CODE: str    #거래소코드
        FID_UNAS_INPUT_ISCD: str    #상승율/하락율 구분
        FID_INPUT_ISCD: str    #N일자값
        FID_INPUT_RMNN_DYNU_1: str    #거래량조건
        FID_DIV_CLS_CODE: str    #NEXT KEY BUFF
        FID_INPUT_PRICE_1: str    #사용자권한정보
        FID_INPUT_PRICE_2: str    #거래소코드
        FID_INPUT_VOL_1: str    #상승율/하락율 구분
        FID_INPUT_VOL_2: str    #N일자값
        FID_INPUT_DATE_1: str    #거래량조건
        FID_RANK_SORT_CLS_CODE: str    #NEXT KEY BUFF
        FID_BLNG_CLS_CODE: str    #사용자권한정보
        FID_INPUT_DATE_2: str    #거래소코드
    
    

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
        hts_kor_isnm: str    #HTS한글종목명
        elw_shrn_iscd: str    #ELW단축종목코드
        elw_prpr: str    #ELW현재가
        prdy_vrss: str    #전일대비
        prdy_vrss_sign: str    #전일대비부호
        prdy_ctrt: str    #전일대비율
        acml_vol: str    #누적거래량
        stck_sdpr: str    #주식기준가
        sdpr_vrss_prpr_sign: str    #기준가대비현재가부호
        sdpr_vrss_prpr: str    #기준가대비현재가
        sdpr_vrss_prpr_rate: str    #기준가대비현재가비율
        stck_oprc: str    #주식시가2
        oprc_vrss_prpr_sign: str    #시가2대비현재가부호
        oprc_vrss_prpr: str    #시가2대비현재가
        oprc_vrss_prpr_rate: str    #시가2대비현재가비율
        stck_hgpr: str    #주식최고가
        stck_lwpr: str    #주식최저가
        prd_rsfl_sign: str    #기간등락부호
        prd_rsfl: str    #기간등락
        prd_rsfl_rate: str    #기간등락비율
        stck_cnvr_rate: str    #주식전환비율
        hts_rmnn_dynu: str    #HTS잔존일수
        acpr: str    #행사가
        unas_isnm: str    #기초자산명
        unas_shrn_iscd: str    #기초자산코드
        lp_hldn_rate: str    #LP보유비율
        prit: str    #패리티
        prls_qryr_stpr_prc: str    #손익분기주가가격
        delta_val: str    #델타값
        theta: str    #세타
        prls_qryr_rate: str    #손익분기비율
        stck_lstn_date: str    #주식상장일자
        stck_last_tr_date: str    #주식최종거래일자
        hts_ints_vltl: str    #HTS내재변동성
        lvrg_val: str    #레버리지값
    
    

복사하기