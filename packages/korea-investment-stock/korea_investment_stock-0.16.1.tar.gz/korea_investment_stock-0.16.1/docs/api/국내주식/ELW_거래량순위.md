# ELW 거래량순위

> API 경로: `/uapi/elw/v1/ranking/volume-rank`

---

# RESTELW 거래량순위[국내주식-168]

**ELW 거래량순위[국내주식-168] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/elw/v1/ranking/volume-rank  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | FHPEW02780000 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ELW 거래량순위 API입니다. 
    한국투자 HTS(eFriend Plus) > [0278] ELW 거래량순위 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

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
tr_id | 거래ID | String | Y | 13 | FHPEW02780000  
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
FID_COND_MRKT_DIV_CODE | 조건시장분류코드 | String | Y | 2 | W  
FID_COND_SCR_DIV_CODE | 조건화면분류코드 | String | Y | 5 | 20278  
FID_UNAS_INPUT_ISCD | 기초자산입력종목코드 | String | Y | 12 | 000000  
FID_INPUT_ISCD | 발행사 | String | Y | 12 | 00000(전체), 00003(한국투자증권)  
, 00017(KB증권), 00005(미래에셋주식회사)'  
FID_INPUT_RMNN_DYNU_1 | 입력잔존일수 | String | Y | 5 |   
FID_DIV_CLS_CODE | 콜풋구분코드 | String | Y | 2 | 0(전체), 1(콜), 2(풋)  
FID_INPUT_PRICE_1 | 가격(이상) | String | Y | 12 | 거래가격1(이상)  
FID_INPUT_PRICE_2 | 가격(이하) | String | Y | 12 | 거래가격1(이하)  
FID_INPUT_VOL_1 | 거래량(이상) | String | Y | 18 | 거래량1(이상)  
FID_INPUT_VOL_2 | 거래량(이하) | String | Y | 18 | 거래량1(이하)  
FID_INPUT_DATE_1 | 조회기준일 | String | Y | 10 | 입력날짜(기준가 조회기준)  
FID_RANK_SORT_CLS_CODE | 순위정렬구분코드 | String | Y | 2 | 0: 거래량순 1: 평균거래증가율 2: 평균거래회전율 3:거래금액순 4: 순매수잔량순 5: 순매도잔량순  
FID_BLNG_CLS_CODE | 소속구분코드 | String | Y | 2 | 0: 전체  
FID_INPUT_ISCD_2 | LP발행사 | String | Y | 8 | 0000  
FID_INPUT_DATE_2 | 만기일-최종거래일조회 | String | Y | 10 | 공백  
  
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
elw_kor_isnm  | ELW한글종목명 | String | Y | 40 |   
elw_shrn_iscd  | ELW단축종목코드 | String | Y | 9 |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
prdy_vrss  | 전일대비 | String | Y | 10 |   
prdy_vrss_sign  | 전일대비부호 | String | Y | 1 |   
prdy_ctrt  | 전일대비율 | String | Y | 82 |   
lstn_stcn  | 상장주수 | String | Y | 18 |   
acml_vol  | 누적거래량 | String | Y | 18 |   
n_prdy_vol  | N전일거래량 | String | Y | 18 |   
n_prdy_vol_vrss  | N전일거래량대비 | String | Y | 18 |   
vol_inrt  | 거래량증가율 | String | Y | 84 |   
vol_tnrt  | 거래량회전율 | String | Y | 82 |   
nday_vol_tnrt  | N일거래량회전율 | String | Y | 8 |   
acml_tr_pbmn  | 누적거래대금 | String | Y | 18 |   
n_prdy_tr_pbmn  | N전일거래대금 | String | Y | 18 |   
n_prdy_tr_pbmn_vrss  | N전일거래대금대비 | String | Y | 18 |   
total_askp_rsqn  | 총매도호가잔량 | String | Y | 12 |   
total_bidp_rsqn  | 총매수호가잔량 | String | Y | 12 |   
ntsl_rsqn  | 순매도잔량 | String | Y | 13 |   
ntby_rsqn  | 순매수잔량 | String | Y | 12 |   
seln_rsqn_rate  | 매도잔량비율 | String | Y | 84 |   
shnu_rsqn_rate  | 매수2잔량비율 | String | Y | 84 |   
stck_cnvr_rate  | 주식전환비율 | String | Y | 136 |   
hts_rmnn_dynu  | HTS잔존일수 | String | Y | 5 |   
invl_val  | 내재가치값 | String | Y | 132 |   
tmvl_val  | 시간가치값 | String | Y | 132 |   
acpr  | 행사가 | String | Y | 112 |   
lp_mbcr_name  | LP회원사명 | String | Y | 50 |   
unas_isnm  | 기초자산명 | String | Y | 40 |   
stck_last_tr_date  | 최종거래일 | String | Y | 8 |   
unas_shrn_iscd  | 기초자산코드 | String | Y | 12 |   
prdy_vol  | 전일거래량 | String | Y | 18 |   
lp_hldn_rate  | LP보유비율 | String | Y | 84 |   
prit  | 패리티 | String | Y | 112 |   
prls_qryr_stpr_prc  | 손익분기주가가격 | String | Y | 112 |   
delta_val  | 델타값 | String | Y | 114 |   
theta  | 세타 | String | Y | 84 |   
prls_qryr_rate  | 손익분기비율 | String | Y | 84 |   
stck_lstn_date  | 주식상장일자 | String | Y | 8 |   
hts_ints_vltl  | HTS내재변동성 | String | Y | 114 |   
lvrg_val  | 레버리지값 | String | Y | 114 |   
lp_ntby_qty  | LP순매도량 | String | Y | 18 |   
  
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
        FID_COND_SCR_DIV_CODE: str    #조건화면분류코드
        FID_UNAS_INPUT_ISCD: str    #기초자산입력종목코드
        FID_INPUT_ISCD: str    #발행사
        FID_INPUT_RMNN_DYNU_1: str    #입력잔존일수
        FID_DIV_CLS_CODE: str    #콜풋구분코드
        FID_INPUT_PRICE_1: str    #가격(이상)
        FID_INPUT_PRICE_2: str    #가격(이하)
        FID_INPUT_VOL_1: str    #거래량(이상)
        FID_INPUT_VOL_2: str    #거래량(이하)
        FID_INPUT_DATE_1: str    #조회기준일
        FID_RANK_SORT_CLS_CODE: str    #순위정렬구분코드
        FID_BLNG_CLS_CODE: str    #소속구분코드
        FID_INPUT_ISCD_2: str    #LP발행사
        FID_INPUT_DATE_2: str    #만기일-최종거래일조회
    
    

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
        elw_kor_isnm: str    #ELW한글종목명
        elw_shrn_iscd: str    #ELW단축종목코드
        elw_prpr: str    #ELW현재가
        prdy_vrss: str    #전일대비
        prdy_vrss_sign: str    #전일대비부호
        prdy_ctrt: str    #전일대비율
        lstn_stcn: str    #상장주수
        acml_vol: str    #누적거래량
        n_prdy_vol: str    #N전일거래량
        n_prdy_vol_vrss: str    #N전일거래량대비
        vol_inrt: str    #거래량증가율
        vol_tnrt: str    #거래량회전율
        nday_vol_tnrt: str    #N일거래량회전율
        acml_tr_pbmn: str    #누적거래대금
        n_prdy_tr_pbmn: str    #N전일거래대금
        n_prdy_tr_pbmn_vrss: str    #N전일거래대금대비
        total_askp_rsqn: str    #총매도호가잔량
        total_bidp_rsqn: str    #총매수호가잔량
        ntsl_rsqn: str    #순매도잔량
        ntby_rsqn: str    #순매수잔량
        seln_rsqn_rate: str    #매도잔량비율
        shnu_rsqn_rate: str    #매수2잔량비율
        stck_cnvr_rate: str    #주식전환비율
        hts_rmnn_dynu: str    #HTS잔존일수
        invl_val: str    #내재가치값
        tmvl_val: str    #시간가치값
        acpr: str    #행사가
        lp_mbcr_name: str    #LP회원사명
        unas_isnm: str    #기초자산명
        stck_last_tr_date: str    #최종거래일
        unas_shrn_iscd: str    #기초자산코드
        prdy_vol: str    #전일거래량
        lp_hldn_rate: str    #LP보유비율
        prit: str    #패리티
        prls_qryr_stpr_prc: str    #손익분기주가가격
        delta_val: str    #델타값
        theta: str    #세타
        prls_qryr_rate: str    #손익분기비율
        stck_lstn_date: str    #주식상장일자
        hts_ints_vltl: str    #HTS내재변동성
        lvrg_val: str    #레버리지값
        lp_ntby_qty: str    #LP순매도량
    
    

복사하기