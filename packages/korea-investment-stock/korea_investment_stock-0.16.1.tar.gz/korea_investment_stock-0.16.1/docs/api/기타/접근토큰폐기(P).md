# 접근토큰폐기(P)

> API 경로: `/oauth2/revokeP`

---

# REST접근토큰폐기(P)[인증-002]

**접근토큰폐기(P)[인증-002] 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /oauth2/revokeP  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | https://openapivts.koreainvestment.com:29443  
실전 TR ID  |  | 모의 TR ID |   
Format | JSON | Content-Type | application/json; charset=UTF-8  
  
## 개요
    
    
     부여받은 접큰토큰을 더 이상 활용하지 않을 때 사용합니다.

## 요청

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
appkey | 고객 앱Key | String | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.)  
appsecret | 고객 앱Secret | String | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.)  
token | 접근토큰 | String | Y | 286 | OAuth 토큰이 필요한 API 경우 발급한 Access token  
일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  
법인(Access token 유효기간 3개월, Refresh token 유효기간 1년, OAuth 2.0의 Authorization Code Grant 절차를 준용)  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
code | 응답코드 | String | N | 8 | HTTP 응답코드  
message | 응답메세지 | String | N | 450 | 응답메세지  
  
## 예시

### Request

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    
    @dataclass
    class RequestHeader:
    
    @dataclass
    class RequestBody:
        appkey: str    #고객 앱Key
        appsecret: str    #고객 앱Secret
        token: str    #접근토큰
    
    

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
        code: Optional[str] = None    #응답코드
        message: Optional[str] = None    #응답메세지
    
    

복사하기