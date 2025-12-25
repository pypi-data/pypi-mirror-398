# fetch_price_detail_oversea 리팩토링 구현 가이드

## 1. constants.py 수정

### 1.1 EXCD 상수 키 변경

**파일**: `korea_investment_stock/constants.py`

```python
# 변경 전
EXCD = {
    "NYSE": "NYS",
    "NASDAQ": "NAS",
    "AMEX": "AMS",
    "NYSE_DAY": "BAY",
    "NASDAQ_DAY": "BAQ",
    "AMEX_DAY": "BAA",
    "HONGKONG": "HKS",
    "TOKYO": "TSE",
    "SHANGHAI": "SHS",
    "SHENZHEN": "SZS",
    "SHANGHAI_INDEX": "SHI",
    "SHENZHEN_INDEX": "SZI",
    "HOCHIMINH": "HSX",
    "HANOI": "HNX",
}

# 변경 후
EXCD = {
    # 미국 (정규장)
    "NYS": "NYS",   # NYSE
    "NAS": "NAS",   # NASDAQ
    "AMS": "AMS",   # AMEX
    # 미국 (주간거래)
    "BAY": "BAY",   # NYSE 주간거래
    "BAQ": "BAQ",   # NASDAQ 주간거래
    "BAA": "BAA",   # AMEX 주간거래
    # 아시아
    "HKS": "HKS",   # 홍콩
    "TSE": "TSE",   # 도쿄
    "SHS": "SHS",   # 상하이
    "SZS": "SZS",   # 심천
    "SHI": "SHI",   # 상하이 지수
    "SZI": "SZI",   # 심천 지수
    "HSX": "HSX",   # 호치민
    "HNX": "HNX",   # 하노이
}
```

### 1.2 EXCD_BY_COUNTRY 상수 추가

```python
# 국가별 거래소 코드 매핑 (신규 추가)
EXCD_BY_COUNTRY = {
    "US": ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"],  # 미국 (정규장 + 주간거래)
    "HK": ["HKS"],                                      # 홍콩
    "JP": ["TSE"],                                      # 일본
    "CN": ["SHS", "SZS"],                               # 중국 (상하이, 심천)
    "VN": ["HSX", "HNX"],                               # 베트남 (호치민, 하노이)
}
```

## 2. korea_investment_stock.py 수정

### 2.1 import 추가

```python
from korea_investment_stock.constants import EXCD_BY_COUNTRY
```

### 2.2 fetch_price_detail_oversea 메서드 변경

**위치**: `korea_investment_stock/korea_investment_stock.py:490`

```python
# 변경 전
def fetch_price_detail_oversea(self, symbol: str, market: str = "KR"):
    """해외주식 현재가상세

    Args:
        symbol (str): symbol
    """
    # ...
    if market == "KR" or market == "KRX":
        raise ValueError("Market cannot be either 'KR' or 'KRX'.")

    for exchange_code in ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]:
        # ...

# 변경 후
def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> dict:
    """해외주식 현재가상세 [v1_해외주식-029]

    해외주식 종목의 현재가, PER, PBR, EPS, BPS 등 상세 정보를 조회합니다.
    국가 코드에 따라 해당 국가의 거래소를 자동으로 탐색합니다.

    API 정보:
        - 경로: /uapi/overseas-price/v1/quotations/price-detail
        - Method: GET
        - 실전 Domain: https://openapi.koreainvestment.com:9443
        - 실전 TR ID: HHDFS76200200
        - 모의투자: 미지원

    Query Parameters:
        AUTH (str): 사용자권한정보
            - Required: Yes
            - Length: 32
            - 빈 문자열로 전송

        EXCD (str): 거래소코드
            - Required: Yes
            - Length: 4
            - 미국:
                - NYS: 뉴욕 (NYSE)
                - NAS: 나스닥 (NASDAQ)
                - AMS: 아멕스 (AMEX)
                - BAY: 뉴욕 (주간거래)
                - BAQ: 나스닥 (주간거래)
                - BAA: 아멕스 (주간거래)
            - 아시아:
                - HKS: 홍콩
                - TSE: 도쿄
                - SHS: 상해
                - SZS: 심천
                - SHI: 상해지수
                - SZI: 심천지수
                - HSX: 호치민
                - HNX: 하노이

        SYMB (str): 종목코드
            - Required: Yes
            - Length: 16

    Args:
        symbol (str): 종목 코드 (예: AAPL, MSFT, TSLA)
        country_code (str): 국가 코드 (기본값: "US")
            - "US": 미국 (NYS → NAS → AMS → BAY → BAQ → BAA)
            - "HK": 홍콩 (HKS)
            - "JP": 일본 (TSE)
            - "CN": 중국 (SHS → SZS)
            - "VN": 베트남 (HSX → HNX)

    Returns:
        dict: API 응답
            rt_cd (str): 성공 실패 여부 ("0"=성공)
            msg_cd (str): 응답코드
            msg1 (str): 응답메세지
            output (dict): 응답상세
                rsym (str): 실시간조회종목코드
                pvol (str): 전일거래량
                open (str): 시가
                high (str): 고가
                low (str): 저가
                last (str): 현재가
                base (str): 전일종가
                tomv (str): 시가총액
                pamt (str): 전일거래대금
                uplp (str): 상한가
                dnlp (str): 하한가
                h52p (str): 52주최고가
                h52d (str): 52주최고일자
                l52p (str): 52주최저가
                l52d (str): 52주최저일자
                perx (str): PER
                pbrx (str): PBR
                epsx (str): EPS
                bpsx (str): BPS
                shar (str): 상장주수
                mcap (str): 자본금
                curr (str): 통화
                zdiv (str): 소수점자리수
                vnit (str): 매매단위
                t_xprc (str): 원환산당일가격
                t_xdif (str): 원환산당일대비
                t_xrat (str): 원환산당일등락
                p_xprc (str): 원환산전일가격
                p_xdif (str): 원환산전일대비
                p_xrat (str): 원환산전일등락
                t_rate (str): 당일환율
                p_rate (str): 전일환율
                t_xsgn (str): 원환산당일기호 (HTS 색상표시용)
                p_xsng (str): 원환산전일기호 (HTS 색상표시용)
                e_ordyn (str): 거래가능여부
                e_hogau (str): 호가단위
                e_icod (str): 업종(섹터)
                e_parp (str): 액면가
                tvol (str): 거래량
                tamt (str): 거래대금
                etyp_nm (str): ETP 분류명

    Raises:
        ValueError: 지원하지 않는 country_code인 경우

    Note:
        - 지연시세: 미국 실시간무료(0분지연), 홍콩/베트남/중국/일본 15분 지연
        - 미국의 경우 0분지연시세로 제공되나, 장중 당일 시가는 상이할 수 있으며,
          익일 정정 표시됩니다.
        - 미국주식 시세의 경우 주간거래시간을 제외한 정규장, 애프터마켓, 프리마켓
          시간대에 동일한 API(TR)로 시세 조회가 됩니다.
    """
    exchange_codes = EXCD_BY_COUNTRY.get(country_code)
    if not exchange_codes:
        raise ValueError(f"지원하지 않는 country_code: {country_code}")

    for exchange_code in exchange_codes:
        # 기존 로직 유지
```

## 3. Wrapper 클래스 수정

### 3.1 cached_korea_investment.py

**파일**: `korea_investment_stock/cache/cached_korea_investment.py:88`

```python
# 변경 전
def fetch_price_detail_oversea(self, symbol: str, market: str = "KR") -> dict:
    """해외 주식 가격 조회 (캐싱 지원)"""
    if not self.enable_cache:
        return self.broker.fetch_price_detail_oversea(symbol, market)

    cache_key = self._make_cache_key("fetch_price_detail_oversea", symbol, market)
    # ...
    result = self.broker.fetch_price_detail_oversea(symbol, market)

# 변경 후
def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> dict:
    """해외 주식 가격 조회 (캐싱 지원)"""
    if not self.enable_cache:
        return self.broker.fetch_price_detail_oversea(symbol, country_code)

    cache_key = self._make_cache_key("fetch_price_detail_oversea", symbol, country_code)
    # ...
    result = self.broker.fetch_price_detail_oversea(symbol, country_code)
```

### 3.2 rate_limited_korea_investment.py

**파일**: `korea_investment_stock/rate_limit/rate_limited_korea_investment.py:72`

```python
# 변경 전
def fetch_price_detail_oversea(self, symbol: str, market: str) -> Dict[str, Any]:
    """
    속도 제한이 적용된 해외 주식 가격 조회

    Args:
        symbol: 종목 코드
        market: 시장 구분
    """
    self._rate_limiter.wait()
    return self._broker.fetch_price_detail_oversea(symbol, market)

# 변경 후
def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> Dict[str, Any]:
    """
    속도 제한이 적용된 해외 주식 가격 조회

    Args:
        symbol: 종목 코드
        country_code: 국가 코드 (기본값: "US")
    """
    self._rate_limiter.wait()
    return self._broker.fetch_price_detail_oversea(symbol, country_code)
```

## 4. Breaking Changes

### API 호출 방식 변경

```python
# 변경 전
broker.fetch_price_detail_oversea("AAPL", market="US")

# 변경 후
broker.fetch_price_detail_oversea("AAPL")  # 기본값 "US"
broker.fetch_price_detail_oversea("AAPL", country_code="US")
broker.fetch_price_detail_oversea("9988", country_code="HK")  # 홍콩 알리바바
broker.fetch_price_detail_oversea("7203", country_code="JP")  # 일본 토요타
```

### 상수 사용 변경

```python
# 변경 전
from korea_investment_stock.constants import EXCD
exchange = EXCD["NYSE"]  # "NYS"

# 변경 후
from korea_investment_stock.constants import EXCD, EXCD_BY_COUNTRY
exchange = EXCD["NYS"]   # "NYS"
us_exchanges = EXCD_BY_COUNTRY["US"]  # ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]
```
