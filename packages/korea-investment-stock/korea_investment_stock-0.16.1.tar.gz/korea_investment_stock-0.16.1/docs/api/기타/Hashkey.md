# Hashkey

> API 경로: `/uapi/hashkey`

---

# RESTHashkey

**Hashkey 정보** **Method, URL, 실전 Domain, 모의 Domain, Format, Content-Type** Method | POST | URL | /uapi/hashkey  
---|---|---|---  
실전 Domain  | https://openapi.koreainvestment.com:9443 | 모의 Domain | https://openapivts.koreainvestment.com:29443  
실전 TR ID  |  | 모의 TR ID |   
Format | JSON | Content-Type | application/json  
  
## 개요
    
    
    해쉬키(Hashkey)는 보안을 위한 요소로 사용자가 보낸 요청 값을 중간에 탈취하여 변조하지 못하도록 하는데 사용됩니다.
    해쉬키를 사용하면 POST로 보내는 요청(주로 주문/정정/취소 API 해당)의 body 값을 사전에 암호화시킬 수 있습니다.
    해쉬키는 비필수값으로 사용하지 않아도 POST API 호출은 가능합니다.

## 요청

### Header

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
content-type | 컨텐츠타입 | String | N | 40 | application/json; charset=utf-8  
appkey | 앱키 | String | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.)  
appsecret | 앱시크릿키 | String | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.)  
  
### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
JsonBody | 요청값 | Object | Y | - | POST로 보낼 body값  
  
ex)  
datas = {  
"CANO": '00000000',  
"ACNT_PRDT_CD": "01",  
"OVRS_EXCG_CD": "SHAA"  
}  
  
## 응답

### Header

### Body

**주식주문(현금[V1_국내주식-001]) 정보** **Element, 한글명, Type, Rquired, Length, Description** Element | 한글명 | Type | Required | Length | Description  
---|---|---|---|---|---  
JsonBody | 요청값 | Object | Y | - | 요청한 JsonBody  
HASH | 해쉬키 | String | Y | 256 | [POST API 대상] Client가 요청하는 Request Body를 hashkey api로 생성한 Hash값  
* API문서 > hashkey 참조  
  
## 예시

### Request

  * Data Class (Python)

### Data Class (Python)
    
    
    from dataclasses import dataclass
    
    @dataclass
    class RequestHeader:
        content-type: Optional[str] = None    #컨텐츠타입
        appkey: str    #앱키
        appsecret: str    #앱시크릿키
    
    @dataclass
    class RequestBody:
        JsonBody: RequestBodyJsonBody    #요청값
    
    @dataclass
    class RequestBodyJsonBody:
    
    

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
        JsonBody: ResponseBodyJsonBody    #요청값
        HASH: str    #해쉬키
    
    @dataclass
    class ResponseBodyJsonBody:
    
    

복사하기