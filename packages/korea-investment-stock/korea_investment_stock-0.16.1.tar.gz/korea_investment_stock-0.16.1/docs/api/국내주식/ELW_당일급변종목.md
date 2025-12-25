# ELW 당일급변종목

> API 경로: `/uapi/elw/v1/ranking/quick-change`

---

# RESTELW 당일급변종목[국내주식-171]

**ELW 당일급변종목[국내주식-171] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | GET | URL | /uapi/elw/v1/ranking/quick-change  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | 모의투자 미지원  
실전 TR ID  | FHPEW02870000 | 모의 TR ID | 모의투자 미지원  
Format |  | Content-Type |   
  
## 개요
    
    
    ELW 당일급변종목 API입니다. 
    한국투자 HTS(eFriend Plus) > [0287] ELW 당일급변종목 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

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
tr_id | 거래ID | String | Y | 13 | FHPEW02870000  
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
FID_COND_SCR_DIV_CODE | 조건화면분류코드 | String | Y | 5 | Unique key(20287)  
FID_UNAS_INPUT_ISCD | 기초자산입력종목코드 | String | Y | 12 | '000000(전체), 2001(코스피200)  
, 3003(코스닥150), 005930(삼성전자) '  
FID_INPUT_ISCD | 발행사 | String | Y | 12 | '00000(전체), 00003(한국투자증권)  
, 00017(KB증권), 00005(미래에셋주식회사)'  
FID_MRKT_CLS_CODE | 시장구분코드 | String | Y | 2 | Unique key(A)  
FID_INPUT_PRICE_1 | 가격(이상) | String | Y | 12 |   
FID_INPUT_PRICE_2 | 가격(이하) | String | Y | 12 |   
FID_INPUT_VOL_1 | 거래량(이상) | String | Y | 18 |   
FID_INPUT_VOL_2 | 거래량(이하) | String | Y | 18 |   
FID_HOUR_CLS_CODE | 시간구분코드 | String | Y | 5 | 1(분), 2(일)  
FID_INPUT_HOUR_1 | 입력 일 또는 분 | String | Y | 10 |   
FID_INPUT_HOUR_2 | 기준시간(분 선택 시) | String | Y | 10 |   
FID_RANK_SORT_CLS_CODE | 순위정렬구분코드 | String | Y | 2 | '1(가격급등), 2(가격급락), 3(거래량급증)  
, 4(매수잔량급증), 5(매도잔량급증)'  
FID_BLNG_CLS_CODE | 결재방법 | String | Y | 2 | 0(전체), 1(일반), 2(조기종료)  
  
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
elw_shrn_iscd  | ELW단축종목코드 | String | Y | 9 |   
elw_kor_isnm  | ELW한글종목명 | String | Y | 40 |   
elw_prpr  | ELW현재가 | String | Y | 10 |   
prdy_vrss_sign  | 전일대비부호 | String | Y | 1 |   
prdy_vrss  | 전일대비 | String | Y | 10 |   
prdy_ctrt  | 전일대비율 | String | Y | 82 |   
askp  | 매도호가 | String | Y | 10 |   
bidp  | 매수호가 | String | Y | 10 |   
total_askp_rsqn  | 총매도호가잔량 | String | Y | 12 |   
total_bidp_rsqn  | 총매수호가잔량 | String | Y | 12 |   
acml_vol  | 누적거래량 | String | Y | 18 |   
stnd_val  | 기준값 | String | Y | 10 |   
stnd_val_vrss  | 기준값대비 | String | Y | 11 |   
stnd_val_ctrt  | 기준값대비율 | String | Y | 162 |   
  
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
        FID_MRKT_CLS_CODE: str    #시장구분코드
        FID_INPUT_PRICE_1: str    #가격(이상)
        FID_INPUT_PRICE_2: str    #가격(이하)
        FID_INPUT_VOL_1: str    #거래량(이상)
        FID_INPUT_VOL_2: str    #거래량(이하)
        FID_HOUR_CLS_CODE: str    #시간구분코드
        FID_INPUT_HOUR_1: str    #입력 일 또는 분
        FID_INPUT_HOUR_2: str    #기준시간(분 선택 시)
        FID_RANK_SORT_CLS_CODE: str    #순위정렬구분코드
        FID_BLNG_CLS_CODE: str    #결재방법
    
    

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
        elw_shrn_iscd: str    #ELW단축종목코드
        elw_kor_isnm: str    #ELW한글종목명
        elw_prpr: str    #ELW현재가
        prdy_vrss_sign: str    #전일대비부호
        prdy_vrss: str    #전일대비
        prdy_ctrt: str    #전일대비율
        askp: str    #매도호가
        bidp: str    #매수호가
        total_askp_rsqn: str    #총매도호가잔량
        total_bidp_rsqn: str    #총매수호가잔량
        acml_vol: str    #누적거래량
        stnd_val: str    #기준값
        stnd_val_vrss: str    #기준값대비
        stnd_val_ctrt: str    #기준값대비율
    
    

복사하기