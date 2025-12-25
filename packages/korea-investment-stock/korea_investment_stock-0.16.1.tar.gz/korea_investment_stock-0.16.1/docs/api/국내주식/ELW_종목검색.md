# ELW 종목검색

> API 경로: `/uapi/elw/v1/quotations/cond-search`

---

# RESTELW 종목검색 [국내주식-166]

**ELW 종목검색 [국내주식-166] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/elw/v1/quotations/cond-search  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | FHKEW15100000 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ELW 종목검색 API입니다.
    한국투자 HTS(eFriend Plus) > [0291] ELW 종목검색 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    한 번의 호출에 최대 100건까지 확인 가능합니다.

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
tr_id | 거래ID | String | Y | 13 | FHKEW15100000  
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
FID_COND_MRKT_DIV_CODE | 조건시장분류코드 | String | Y | 2 | ELW(W)  
FID_COND_SCR_DIV_CODE | 조건화면분류코드 | String | Y | 5 | 화면번호(11510)  
FID_RANK_SORT_CLS_CODE | 순위정렬구분코드 | String | Y | 2 | '정렬1정렬안함(0)종목코드(1)현재가(2)대비율(3)거래량(4)행사가격(5)  
전환비율(6)상장일(7)만기일(8)잔존일수(9)레버리지(10)'  
FID_INPUT_CNT_1 | 입력수1 | String | Y | 12 | 정렬1기준 - 상위(1)하위(2)  
FID_RANK_SORT_CLS_CODE_2 | 순위정렬구분코드2 | String | Y | 2 | 정렬2  
FID_INPUT_CNT_2 | 입력수2 | String | Y | 12 | 정렬2기준 - 상위(1)하위(2)  
FID_RANK_SORT_CLS_CODE_3 | 순위정렬구분코드3 | String | Y | 2 | 정렬3  
FID_INPUT_CNT_3 | 입력수3 | String | Y | 12 | 정렬3기준 - 상위(1)하위(2)  
FID_TRGT_CLS_CODE | 대상구분코드 | String | Y | 32 | 0:발행회사종목코드,1:기초자산종목코드,2:FID시장구분코드,3:FID입력날짜1(상장일),  
4:FID입력날짜2(만기일),5:LP회원사종목코드,6:행사가기초자산비교>=(1) <=(2),   
7:잔존일 이상 이하, 8:현재가, 9:전일대비율, 10:거래량, 11:최종거래일, 12:레버리지  
FID_INPUT_ISCD | 입력종목코드 | String | Y | 12 | 발행사종목코드전체(00000)  
FID_UNAS_INPUT_ISCD | 기초자산입력종목코드 | String | Y | 12 |   
FID_MRKT_CLS_CODE | 시장구분코드 | String | Y | 2 | 권리유형전체(A)콜(CO)풋(PO)  
FID_INPUT_DATE_1 | 입력날짜1 | String | Y | 10 | 상장일전체(0)금일(1)7일이하(2)8~30일(3)31~90일(4)  
FID_INPUT_DATE_2 | 입력날짜2 | String | Y | 10 | 만기일전체(0)1개월(1)1~2(2)2~3(3)3~6(4)6~9(5)9~12(6)12이상(7)  
FID_INPUT_ISCD_2 | 입력종목코드2 | String | Y | 8 |   
FID_ETC_CLS_CODE | 기타구분코드 | String | Y | 2 | 행사가전체(0)>=(1)  
FID_INPUT_RMNN_DYNU_1 | 입력잔존일수1 | String | Y | 5 | 잔존일이상  
FID_INPUT_RMNN_DYNU_2 | 입력잔존일수2 | String | Y | 5 | 잔존일이하  
FID_PRPR_CNT1 | 현재가수1 | String | Y | 11 | 현재가이상  
FID_PRPR_CNT2 | 현재가수2 | String | Y | 11 | 현재가이하  
FID_RSFL_RATE1 | 등락비율1 | String | Y | 132 | 전일대비율이상  
FID_RSFL_RATE2 | 등락비율2 | String | Y | 132 | 전일대비율이하  
FID_VOL1 | 거래량1 | String | Y | 18 | 거래량이상  
FID_VOL2 | 거래량2 | String | Y | 18 | 거래량이하  
FID_APLY_RANG_PRC_1 | 적용범위가격1 | String | Y | 18 | 최종거래일from  
FID_APLY_RANG_PRC_2 | 적용범위가격2 | String | Y | 18 | 최종거래일to  
FID_LVRG_VAL1 | 레버리지값1 | String | Y | 114 |   
FID_LVRG_VAL2 | 레버리지값2 | String | Y | 114 |   
FID_VOL3 | 거래량3 | String | Y | 18 | LP종료일from  
FID_VOL4 | 거래량4 | String | Y | 18 | LP종료일to  
FID_INTS_VLTL1 | 내재변동성1 | String | Y | 114 | 내재변동성이상  
FID_INTS_VLTL2 | 내재변동성2 | String | Y | 114 | 내재변동성이하  
FID_PRMM_VAL1 | 프리미엄값1 | String | Y | 132 | 프리미엄이상  
FID_PRMM_VAL2 | 프리미엄값2 | String | Y | 132 | 프리미엄이하  
FID_GEAR1 | 기어링1 | String | Y | 84 | 기어링이상  
FID_GEAR2 | 기어링2 | String | Y | 84 | 기어링이하  
FID_PRLS_QRYR_RATE1 | 손익분기비율1 | String | Y | 132 | 손익분기이상  
FID_PRLS_QRYR_RATE2 | 손익분기비율2 | String | Y | 132 | 손익분기이하  
FID_DELTA1 | 델타1 | String | Y | 84 | 델타이상  
FID_DELTA2 | 델타2 | String | Y | 84 | 델타이하  
FID_ACPR1 | 행사가1 | String | Y | 133 |   
FID_ACPR2 | 행사가2 | String | Y | 133 |   
FID_STCK_CNVR_RATE1 | 주식전환비율1 | String | Y | 94 | 전환비율이상  
FID_STCK_CNVR_RATE2 | 주식전환비율2 | String | Y | 94 | 전환비율이하  
FID_DIV_CLS_CODE | 분류구분코드 | String | Y | 2 | 0:전체,1:일반,2:조기종료  
FID_PRIT1 | 패리티1 | String | Y | 112 | 패리티이상  
FID_PRIT2 | 패리티2 | String | Y | 112 | 패리티이하  
FID_CFP1 | 자본지지점1 | String | Y | 112 | 배리어이상  
FID_CFP2 | 자본지지점2 | String | Y | 112 | 배리어이하  
FID_INPUT_NMIX_PRICE_1 | 지수가격1 | String | Y | 112 | LP보유비율이상  
FID_INPUT_NMIX_PRICE_2 | 지수가격2 | String | Y | 112 | LP보유비율이하  
FID_EGEA_VAL1 | E기어링값1 | String | Y | 132 | 접근도이상  
FID_EGEA_VAL2 | E기어링값2 | String | Y | 132 | 접근도이하  
FID_INPUT_DVDN_ERT | 배당수익율 | String | Y | 112 | 손익분기점이상  
FID_INPUT_HIST_VLTL | 역사적변동성 | String | Y | 112 | 손익분기점이하  
FID_THETA1 | 세타1 | String | Y | 84 | MONEYNESS이상  
FID_THETA2 | 세타2 | String | Y | 84 | MONEYNESS이하  
  
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
output1 | 응답상세 | Object Array | Y |  | array  
bond_shrn_iscd  | 채권단축종목코드 | String | Y | 9 |   
hts_kor_isnm  | HTS한글종목명 | String | Y | 40 |   
rght_type_name  | 권리유형명 | String | Y | 40 |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
prdy_vrss  | 전일대비 | String | Y | 10 |   
prdy_vrss_sign  | 전일대비부호 | String | Y | 1 |   
prdy_ctrt  | 전일대비율 | String | Y | 82 |   
acml_vol  | 누적거래량 | String | Y | 18 |   
acpr  | 행사가 | String | Y | 112 |   
stck_cnvr_rate  | 주식전환비율 | String | Y | 136 |   
stck_lstn_date  | 주식상장일자 | String | Y | 8 |   
stck_last_tr_date  | 주식최종거래일자 | String | Y | 8 |   
hts_rmnn_dynu  | HTS잔존일수 | String | Y | 5 |   
unas_isnm  | 기초자산종목명 | String | Y | 40 |   
unas_prpr  | 기초자산현재가 | String | Y | 112 |   
unas_prdy_vrss  | 기초자산전일대비 | String | Y | 112 |   
unas_prdy_vrss_sign  | 기초자산전일대비부호 | String | Y | 1 |   
unas_prdy_ctrt  | 기초자산전일대비율 | String | Y | 82 |   
unas_acml_vol  | 기초자산누적거래량 | String | Y | 18 |   
moneyness  | MONEYNESS | String | Y | 132 |   
atm_cls_name  | ATM구분명 | String | Y | 10 |   
prit  | 패리티 | String | Y | 112 |   
delta_val  | 델타값 | String | Y | 114 |   
hts_ints_vltl  | HTS내재변동성 | String | Y | 114 |   
tmvl_val  | 시간가치값 | String | Y | 132 |   
gear  | 기어링 | String | Y | 84 |   
lvrg_val  | 레버리지값 | String | Y | 114 |   
prls_qryr_rate  | 손익분기비율 | String | Y | 84 |   
cfp  | 자본지지점 | String | Y | 112 |   
lstn_stcn  | 상장주수 | String | Y | 18 |   
pblc_co_name  | 발행회사명 | String | Y | 40 |   
lp_mbcr_name  | LP회원사명 | String | Y | 50 |   
lp_hldn_rate  | LP보유비율 | String | Y | 84 |   
elw_rght_form  | ELW권리형태 | String | Y | 20 |   
elw_ko_barrier  | 조기종료발생기준가격 | String | Y | 112 |   
apprch_rate  | 접근도 | String | Y | 112 |   
unas_shrn_iscd  | 기초자산단축종목코드 | String | Y | 9 |   
mtrt_date  | 만기일자 | String | Y | 8 |   
prmm_val  | 프리미엄값 | String | Y | 114 |   
stck_lp_fin_date  | 주식LP종료일자 | String | Y | 8 |   
tick_conv_prc  | 틱환산가 | String | Y | 11 |   
prls_qryr_stpr_prc  | 손익분기주가가격 | String | Y | 112 |   
lp_hvol  | LP보유량 | String | Y | 18 |   
  
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
        FID_RANK_SORT_CLS_CODE: str    #순위정렬구분코드
        FID_INPUT_CNT_1: str    #입력수1
        FID_RANK_SORT_CLS_CODE_2: str    #순위정렬구분코드2
        FID_INPUT_CNT_2: str    #입력수2
        FID_RANK_SORT_CLS_CODE_3: str    #순위정렬구분코드3
        FID_INPUT_CNT_3: str    #입력수3
        FID_TRGT_CLS_CODE: str    #대상구분코드
        FID_INPUT_ISCD: str    #입력종목코드
        FID_UNAS_INPUT_ISCD: str    #기초자산입력종목코드
        FID_MRKT_CLS_CODE: str    #시장구분코드
        FID_INPUT_DATE_1: str    #입력날짜1
        FID_INPUT_DATE_2: str    #입력날짜2
        FID_INPUT_ISCD_2: str    #입력종목코드2
        FID_ETC_CLS_CODE: str    #기타구분코드
        FID_INPUT_RMNN_DYNU_1: str    #입력잔존일수1
        FID_INPUT_RMNN_DYNU_2: str    #입력잔존일수2
        FID_PRPR_CNT1: str    #현재가수1
        FID_PRPR_CNT2: str    #현재가수2
        FID_RSFL_RATE1: str    #등락비율1
        FID_RSFL_RATE2: str    #등락비율2
        FID_VOL1: str    #거래량1
        FID_VOL2: str    #거래량2
        FID_APLY_RANG_PRC_1: str    #적용범위가격1
        FID_APLY_RANG_PRC_2: str    #적용범위가격2
        FID_LVRG_VAL1: str    #레버리지값1
        FID_LVRG_VAL2: str    #레버리지값2
        FID_VOL3: str    #거래량3
        FID_VOL4: str    #거래량4
        FID_INTS_VLTL1: str    #내재변동성1
        FID_INTS_VLTL2: str    #내재변동성2
        FID_PRMM_VAL1: str    #프리미엄값1
        FID_PRMM_VAL2: str    #프리미엄값2
        FID_GEAR1: str    #기어링1
        FID_GEAR2: str    #기어링2
        FID_PRLS_QRYR_RATE1: str    #손익분기비율1
        FID_PRLS_QRYR_RATE2: str    #손익분기비율2
        FID_DELTA1: str    #델타1
        FID_DELTA2: str    #델타2
        FID_ACPR1: str    #행사가1
        FID_ACPR2: str    #행사가2
        FID_STCK_CNVR_RATE1: str    #주식전환비율1
        FID_STCK_CNVR_RATE2: str    #주식전환비율2
        FID_DIV_CLS_CODE: str    #분류구분코드
        FID_PRIT1: str    #패리티1
        FID_PRIT2: str    #패리티2
        FID_CFP1: str    #자본지지점1
        FID_CFP2: str    #자본지지점2
        FID_INPUT_NMIX_PRICE_1: str    #지수가격1
        FID_INPUT_NMIX_PRICE_2: str    #지수가격2
        FID_EGEA_VAL1: str    #E기어링값1
        FID_EGEA_VAL2: str    #E기어링값2
        FID_INPUT_DVDN_ERT: str    #배당수익율
        FID_INPUT_HIST_VLTL: str    #역사적변동성
        FID_THETA1: str    #세타1
        FID_THETA2: str    #세타2
    
    

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
        output1: List[ResponseBodyoutput1] = field(default_factory=list)    #응답상세
    
    @dataclass
    class ResponseBodyoutput1:
        bond_shrn_iscd: str    #채권단축종목코드
        hts_kor_isnm: str    #HTS한글종목명
        rght_type_name: str    #권리유형명
        elw_prpr: str    #ELW현재가
        prdy_vrss: str    #전일대비
        prdy_vrss_sign: str    #전일대비부호
        prdy_ctrt: str    #전일대비율
        acml_vol: str    #누적거래량
        acpr: str    #행사가
        stck_cnvr_rate: str    #주식전환비율
        stck_lstn_date: str    #주식상장일자
        stck_last_tr_date: str    #주식최종거래일자
        hts_rmnn_dynu: str    #HTS잔존일수
        unas_isnm: str    #기초자산종목명
        unas_prpr: str    #기초자산현재가
        unas_prdy_vrss: str    #기초자산전일대비
        unas_prdy_vrss_sign: str    #기초자산전일대비부호
        unas_prdy_ctrt: str    #기초자산전일대비율
        unas_acml_vol: str    #기초자산누적거래량
        moneyness: str    #MONEYNESS
        atm_cls_name: str    #ATM구분명
        prit: str    #패리티
        delta_val: str    #델타값
        hts_ints_vltl: str    #HTS내재변동성
        tmvl_val: str    #시간가치값
        gear: str    #기어링
        lvrg_val: str    #레버리지값
        prls_qryr_rate: str    #손익분기비율
        cfp: str    #자본지지점
        lstn_stcn: str    #상장주수
        pblc_co_name: str    #발행회사명
        lp_mbcr_name: str    #LP회원사명
        lp_hldn_rate: str    #LP보유비율
        elw_rght_form: str    #ELW권리형태
        elw_ko_barrier: str    #조기종료발생기준가격
        apprch_rate: str    #접근도
        unas_shrn_iscd: str    #기초자산단축종목코드
        mtrt_date: str    #만기일자
        prmm_val: str    #프리미엄값
        stck_lp_fin_date: str    #주식LP종료일자
        tick_conv_prc: str    #틱환산가
        prls_qryr_stpr_prc: str    #손익분기주가가격
        lp_hvol: str    #LP보유량
    
    

복사하기