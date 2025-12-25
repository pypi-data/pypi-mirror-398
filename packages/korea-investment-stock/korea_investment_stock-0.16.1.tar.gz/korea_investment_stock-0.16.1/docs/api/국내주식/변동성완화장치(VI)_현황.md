# 변동성완화장치(VI) 현황

> API 경로: `/uapi/domestic-stock/v1/quotations/inquire-vi-status`

---

# REST변동성완화장치(VI) 현황 [v1_국내주식-055]

**변동성완화장치(VI) 현황 [v1_국내주식-055] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/domestic-stock/v1/quotations/inquire-vi-status  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | FHPST01390000 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    HTS(eFriend Plus) [0139] 변동성 완화장치(VI) 현황 데이터를 확인할 수 있는 API입니다.
    
    최근 30건까지 확인 가능합니다.

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
tr_id | 거래ID | String | Y | 13 | FHPST01390000  
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
FID_DIV_CLS_CODE | FID 분류 구분 코드 | String | Y | 2 | 0:전체 1:상승 2:하락  
FID_COND_SCR_DIV_CODE | FID 조건 화면 분류 코드 | String | Y | 5 | 20139  
FID_MRKT_CLS_CODE | FID 시장 구분 코드 | String | Y | 2 | 0:전체 K:거래소 Q:코스닥  
FID_INPUT_ISCD | FID 입력 종목코드 | String | Y | 12 |   
FID_RANK_SORT_CLS_CODE | FID 순위 정렬 구분 코드 | String | Y | 2 | 0:전체1:정적2:동적3:정적&동적  
FID_INPUT_DATE_1 | FID 입력 날짜1 | String | Y | 10 | 영업일  
FID_TRGT_CLS_CODE | FID 대상 구분 코드 | String | Y | 32 |   
FID_TRGT_EXLS_CLS_CODE | FID 대상 제외 구분 코드 | String | Y | 32 |   
  
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
output | 응답상세 | Object | Y |  |   
hts_kor_isnm  | HTS 한글 종목명 | String | Y | 40 |   
mksc_shrn_iscd  | 유가증권 단축 종목코드 | String | Y | 9 |   
vi_cls_code  | VI발동상태 | String | Y | 1 | Y: 발동 / N: 해제  
bsop_date  | 영업 일자 | String | Y | 8 |   
cntg_vi_hour  | VI발동시간 | String | Y | 6 | VI발동시간  
vi_cncl_hour  | VI해제시간 | String | Y | 6 | VI해제시간  
vi_kind_code  | VI종류코드 | String | Y | 1 | 1:정적 2:동적 3:정적&동적  
vi_prc  | VI발동가격 | String | Y | 10 |   
vi_stnd_prc  | 정적VI발동기준가격 | String | Y | 10 |   
vi_dprt  | 정적VI발동괴리율 | String | Y | 82 | %  
vi_dmc_stnd_prc  | 동적VI발동기준가격 | String | Y | 10 |   
vi_dmc_dprt  | 동적VI발동괴리율 | String | Y | 82 | %  
vi_count  | VI발동횟수 | String | Y | 7 |   
  
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
        FID_DIV_CLS_CODE: str    #FID 분류 구분 코드
        FID_COND_SCR_DIV_CODE: str    #FID 조건 화면 분류 코드
        FID_MRKT_CLS_CODE: str    #FID 시장 구분 코드
        FID_INPUT_ISCD: str    #FID 입력 종목코드
        FID_RANK_SORT_CLS_CODE: str    #FID 순위 정렬 구분 코드
        FID_INPUT_DATE_1: str    #FID 입력 날짜1
        FID_TRGT_CLS_CODE: str    #FID 대상 구분 코드
        FID_TRGT_EXLS_CLS_CODE: str    #FID 대상 제외 구분 코드
    
    

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
        output: ResponseBodyoutput    #응답상세
    
    @dataclass
    class ResponseBodyoutput:
        hts_kor_isnm: str    #HTS 한글 종목명
        mksc_shrn_iscd: str    #유가증권 단축 종목코드
        vi_cls_code: str    #VI발동상태
        bsop_date: str    #영업 일자
        cntg_vi_hour: str    #VI발동시간
        vi_cncl_hour: str    #VI해제시간
        vi_kind_code: str    #VI종류코드
        vi_prc: str    #VI발동가격
        vi_stnd_prc: str    #정적VI발동기준가격
        vi_dprt: str    #정적VI발동괴리율
        vi_dmc_stnd_prc: str    #동적VI발동기준가격
        vi_dmc_dprt: str    #동적VI발동괴리율
        vi_count: str    #VI발동횟수
    
    

복사하기