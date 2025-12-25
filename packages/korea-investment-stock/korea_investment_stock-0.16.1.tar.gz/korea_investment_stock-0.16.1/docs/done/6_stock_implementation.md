# fetch_stock_info, fetch_search_stock_info 개선 구현 가이드

## 1. constants.py 수정

### 1.1 OVRS_EXCG_CD 키 변경

**파일**: `korea_investment_stock/constants.py:103`

```python
# 변경 전
OVRS_EXCG_CD = {
    # 미국
    "NASDAQ": "NASD",
    "NYSE": "NYSE",
    "AMEX": "AMEX",
    # 아시아
    "HONGKONG": "SEHK",
    "TOKYO": "TKSE",
    "SHANGHAI": "SHAA",
    "SHENZHEN": "SZAA",
    "HANOI": "HASE",
    "HOCHIMINH": "VNSE",
}

# 변경 후
OVRS_EXCG_CD = {
    # 미국
    "NASD": "NASD",   # 나스닥
    "NYSE": "NYSE",   # 뉴욕
    "AMEX": "AMEX",   # 아멕스
    # 아시아
    "SEHK": "SEHK",   # 홍콩
    "TKSE": "TKSE",   # 도쿄
    "SHAA": "SHAA",   # 상하이
    "SZAA": "SZAA",   # 심천
    "HASE": "HASE",   # 하노이
    "VNSE": "VNSE",   # 호치민
}
```

### 1.2 MARKET_TYPE_MAP → PRDT_TYPE_CD_BY_COUNTRY

**파일**: `korea_investment_stock/constants.py:148`

```python
# 변경 전
MARKET_TYPE_MAP = {
    "KR": ["300"],
    "KRX": ["300"],
    "NASDAQ": ["512"],
    "NYSE": ["513"],
    "AMEX": ["529"],
    "US": ["512", "513", "529"],
    "TYO": ["515"],
    "JP": ["515"],
    "HKEX": ["501"],
    "HK": ["501", "543", "558"],
    "HNX": ["507"],
    "HSX": ["508"],
    "VN": ["507", "508"],
    "SSE": ["551"],
    "SZSE": ["552"],
    "CN": ["551", "552"]
}

# 변경 후
PRDT_TYPE_CD_BY_COUNTRY = {
    "KR": [PRDT_TYPE_CD["KR_STOCK"]],
    "KRX": [PRDT_TYPE_CD["KR_STOCK"]],
    "US": [PRDT_TYPE_CD["US_NASDAQ"], PRDT_TYPE_CD["US_NYSE"], PRDT_TYPE_CD["US_AMEX"]],
    "JP": [PRDT_TYPE_CD["JP"]],
    "HK": [PRDT_TYPE_CD["HK"], PRDT_TYPE_CD["HK_CNY"], PRDT_TYPE_CD["HK_USD"]],
    "CN": [PRDT_TYPE_CD["CN_SHANGHAI"], PRDT_TYPE_CD["CN_SHENZHEN"]],
    "VN": [PRDT_TYPE_CD["VN_HANOI"], PRDT_TYPE_CD["VN_HOCHIMINH"]],
}
```

## 2. korea_investment_stock.py 수정

### 2.1 import 변경

```python
# 변경 전
from korea_investment_stock.constants import MARKET_TYPE_MAP

# 변경 후
from korea_investment_stock.constants import PRDT_TYPE_CD_BY_COUNTRY
```

### 2.2 fetch_stock_info 메서드 변경

**파일**: `korea_investment_stock/korea_investment_stock.py:593`

```python
def fetch_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
    """상품기본조회 [v1_국내주식-029]

    국내/해외 주식의 기본 상품 정보를 조회합니다.
    국가 코드에 따라 해당 국가의 상품유형코드를 자동으로 탐색합니다.

    API 정보:
        - 경로: /uapi/domestic-stock/v1/quotations/search-info
        - Method: GET
        - 실전 TR ID: CTPF1604R
        - 모의투자: 미지원

    Query Parameters:
        PDNO (str): 상품번호
            - Required: Yes
            - Length: 12
            - 예) 000660 (하이닉스), AAPL (애플)

        PRDT_TYPE_CD (str): 상품유형코드
            - Required: Yes
            - Length: 3
            - 국내: 300 (주식), 301 (선물옵션), 302 (채권)
            - 미국: 512 (나스닥), 513 (뉴욕), 529 (아멕스)
            - 일본: 515
            - 홍콩: 501, 543 (CNY), 558 (USD)
            - 베트남: 507 (하노이), 508 (호치민)
            - 중국: 551 (상해A), 552 (심천A)

    Args:
        symbol (str): 종목 코드 (예: 005930, AAPL)
        country_code (str): 국가 코드 (기본값: "KR")
            - KR/KRX: 한국
            - US: 미국 (NASDAQ, NYSE, AMEX)
            - JP: 일본
            - HK: 홍콩
            - CN: 중국 (상해, 심천)
            - VN: 베트남 (하노이, 호치민)

    Returns:
        dict: API 응답 딕셔너리
            - rt_cd: 성공 실패 여부 ("0": 성공)
            - msg_cd: 응답코드
            - msg1: 응답메시지
            - output: 상품기본정보

    Raises:
        KeyError: 지원하지 않는 country_code인 경우

    Example:
        >>> broker.fetch_stock_info("005930", "KR")  # 삼성전자
        >>> broker.fetch_stock_info("AAPL", "US")    # 애플
    """
    path = "uapi/domestic-stock/v1/quotations/search-info"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "CTPF1604R"
    }

    for prdt_type_cd in PRDT_TYPE_CD_BY_COUNTRY[country_code]:
        try:
            params = {
                "PDNO": symbol,
                "PRDT_TYPE_CD": prdt_type_cd
            }
            resp = requests.get(url, headers=headers, params=params)
            resp_json = resp.json()

            if resp_json['rt_cd'] == API_RETURN_CODE['NO_DATA']:
                continue
            return resp_json

        except Exception as e:
            logger.debug(f"fetch_stock_info 에러: {e}")
            if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:
                continue
            raise e
```

### 2.3 fetch_search_stock_info 메서드 변경

**파일**: `korea_investment_stock/korea_investment_stock.py:623`

```python
def fetch_search_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
    """주식기본조회 [v1_국내주식-067]

    국내주식 종목의 상세 정보를 조회합니다.
    상장주수, 자본금, 액면가, 시장구분, 업종분류 등 상세 정보를 제공합니다.

    ⚠️ 주의: 이 API는 **국내주식만 지원**합니다.
    해외주식 정보는 fetch_stock_info() 또는 fetch_price_detail_oversea()를 사용하세요.

    API 정보:
        - 경로: /uapi/domestic-stock/v1/quotations/search-stock-info
        - Method: GET
        - 실전 TR ID: CTPF1002R
        - 모의투자: 미지원

    Query Parameters:
        PRDT_TYPE_CD (str): 상품유형코드
            - Required: Yes
            - Length: 3
            - 300: 주식, ETF, ETN, ELW
            - 301: 선물옵션
            - 302: 채권
            - 306: ELS

        PDNO (str): 상품번호
            - Required: Yes
            - Length: 12
            - 종목번호 6자리 (예: 005930)
            - ETN의 경우 Q로 시작 (예: Q500001)

    Args:
        symbol (str): 종목 코드 (예: 005930, 000660)
        country_code (str): 국가 코드 (기본값: "KR")
            - KR/KRX만 지원
            - 그 외 값은 ValueError 발생

    Returns:
        dict: API 응답 딕셔너리

    Raises:
        ValueError: country_code가 "KR" 또는 "KRX"가 아닌 경우

    Example:
        >>> broker.fetch_search_stock_info("005930")        # 삼성전자
        >>> broker.fetch_search_stock_info("005930", "KR")  # 동일
    """
    path = "uapi/domestic-stock/v1/quotations/search-stock-info"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "CTPF1002R"
    }

    if country_code != "KR" and country_code != "KRX":
        raise ValueError("country_code must be either 'KR' or 'KRX'.")

    for prdt_type_cd in PRDT_TYPE_CD_BY_COUNTRY[country_code]:
        try:
            params = {
                "PDNO": symbol,
                "PRDT_TYPE_CD": prdt_type_cd
            }
            resp = requests.get(url, headers=headers, params=params)
            resp_json = resp.json()

            if resp_json['rt_cd'] == API_RETURN_CODE['NO_DATA']:
                continue
            return resp_json

        except Exception as e:
            logger.debug(f"fetch_search_stock_info 에러: {e}")
            if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:
                continue
            raise e
```

## 3. 래퍼 클래스 수정

### 3.1 cached_korea_investment.py

**파일**: `korea_investment_stock/cache/cached_korea_investment.py:106`

```python
def fetch_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
    """상품 정보 조회 (캐싱 지원)"""
    if not self.enable_cache:
        return self.broker.fetch_stock_info(symbol, country_code)

    cache_key = self._make_cache_key("fetch_stock_info", symbol, country_code)
    cached = self._cache_manager.get(cache_key)
    if cached is not None:
        return cached

    result = self.broker.fetch_stock_info(symbol, country_code)
    self._cache_manager.set(cache_key, result, ttl=self._stock_info_ttl)
    return result

def fetch_search_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
    """주식 기본 정보 조회 (캐싱 지원)"""
    if not self.enable_cache:
        return self.broker.fetch_search_stock_info(symbol, country_code)

    cache_key = self._make_cache_key("fetch_search_stock_info", symbol, country_code)
    cached = self._cache_manager.get(cache_key)
    if cached is not None:
        return cached

    result = self.broker.fetch_search_stock_info(symbol, country_code)
    self._cache_manager.set(cache_key, result, ttl=self._stock_info_ttl)
    return result
```

### 3.2 rate_limited_korea_investment.py

**파일**: `korea_investment_stock/rate_limit/rate_limited_korea_investment.py:86`

```python
def fetch_stock_info(self, symbol: str, country_code: str = "KR") -> Dict[str, Any]:
    """
    속도 제한이 적용된 종목 정보 조회

    Args:
        symbol: 종목 코드
        country_code: 국가 코드 (기본값: "KR")

    Returns:
        API 응답 딕셔너리
    """
    self._rate_limiter.wait()
    return self._broker.fetch_stock_info(symbol, country_code)

def fetch_search_stock_info(self, symbol: str, country_code: str = "KR") -> Dict[str, Any]:
    """
    속도 제한이 적용된 주식 기본 정보 조회

    Args:
        symbol: 종목 코드
        country_code: 국가 코드 (기본값: "KR")

    Returns:
        API 응답 딕셔너리
    """
    self._rate_limiter.wait()
    return self._broker.fetch_search_stock_info(symbol, country_code)
```

## 4. 테스트 코드 수정

### 4.1 단위 테스트

**파일**: `korea_investment_stock/tests/test_korea_investment_stock.py`

```python
def test_fetch_stock_info_kr():
    """국내 주식 정보 조회 테스트"""
    with KoreaInvestment() as broker:
        result = broker.fetch_stock_info("005930", country_code="KR")
        assert result['rt_cd'] == '0'
        assert 'output' in result

def test_fetch_stock_info_us():
    """미국 주식 정보 조회 테스트"""
    with KoreaInvestment() as broker:
        result = broker.fetch_stock_info("AAPL", country_code="US")
        assert result['rt_cd'] == '0'

def test_fetch_search_stock_info():
    """주식 기본 정보 조회 테스트"""
    with KoreaInvestment() as broker:
        result = broker.fetch_search_stock_info("005930")
        assert result['rt_cd'] == '0'

def test_fetch_search_stock_info_invalid_country():
    """해외 주식 시도 시 ValueError 테스트"""
    with KoreaInvestment() as broker:
        with pytest.raises(ValueError):
            broker.fetch_search_stock_info("AAPL", country_code="US")
```

## 5. 문서 업데이트

### 5.1 CLAUDE.md 변경 사항

메서드 시그니처 섹션 업데이트:

```markdown
- `fetch_stock_info(symbol, country_code)` - Stock information
- `fetch_search_stock_info(symbol, country_code)` - Stock search (국내주식만)
```

### 5.2 CHANGELOG.md 추가 항목

```markdown
## [Unreleased]

### Changed
- `fetch_stock_info`: 인자 `market` → `country_code`로 변경
- `fetch_search_stock_info`: 인자 `market` → `country_code`로 변경
- `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY`로 이름 변경
- `OVRS_EXCG_CD`: 키 형태 변경 (NASD:NASD 패턴)

### Breaking Changes
- `fetch_stock_info(symbol, market="KR")` → `fetch_stock_info(symbol, country_code="KR")`
- `fetch_search_stock_info(symbol, market="KR")` → `fetch_search_stock_info(symbol, country_code="KR")`
```
