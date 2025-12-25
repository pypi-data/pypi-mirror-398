# fetch_price_detail_oversea 메서드 리팩토링 PRD

## 1. 개요

### 1.1 목적
`fetch_price_detail_oversea()` 메서드의 인자명 변경(`market` → `country_code`) 및 상수 정의 개선을 통해 API 사용성과 코드 일관성을 향상시킵니다.

### 1.2 현재 문제점

#### 문제 1: EXCD 상수 키 불일치
```python
# 현재 (constants.py)
EXCD = {
    "NYSE": "NYS",
    "NASDAQ": "NAS",
    "AMEX": "AMS",
    ...
}
```
- 키(NYSE)와 값(NYS)이 다름
- 실제 API에서 사용하는 값은 `NYS`, `NAS` 등
- 불필요한 매핑 레이어 존재

#### 문제 2: 거래소 코드 하드코딩
```python
# 현재 (korea_investment_stock.py:490)
def fetch_price_detail_oversea(self, symbol: str, market: str = "KR"):
```
- 거래소 코드가 메서드 내부에 하드코딩됨
- 국가별 거래소 매핑이 상수로 정의되어 있지 않음
  ```python
  for exchange_code in ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]:
  ```

#### 문제 3: 인자명 불일치
- `market` 인자명이 다른 메서드(`fetch_price`)의 `country_code`와 불일치
- API 일관성 저해

## 2. 요구사항

### 2.1 constants.py 수정

#### 변경 전
```python
EXCD = {
    # 미국 (정규장)
    "NYSE": "NYS",
    "NASDAQ": "NAS",
    "AMEX": "AMS",
    # 미국 (주간거래)
    "NYSE_DAY": "BAY",
    "NASDAQ_DAY": "BAQ",
    "AMEX_DAY": "BAA",
    # 아시아
    "HONGKONG": "HKS",
    "TOKYO": "TSE",
    "SHANGHAI": "SHS",
    "SHENZHEN": "SZS",
    "SHANGHAI_INDEX": "SHI",
    "SHENZHEN_INDEX": "SZI",
    "HOCHIMINH": "HSX",
    "HANOI": "HNX",
}
```

#### 변경 후
```python
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

# 국가별 거래소 코드 매핑 (신규 추가)
EXCD_BY_COUNTRY = {
    "US": ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"],  # 미국 (정규장 + 주간거래)
    "HK": ["HKS"],                                      # 홍콩
    "JP": ["TSE"],                                      # 일본
    "CN": ["SHS", "SZS"],                               # 중국 (상하이, 심천)
    "VN": ["HSX", "HNX"],                               # 베트남 (호치민, 하노이)
}
```

**이유:**
- API 파라미터에서 사용하는 실제 코드값을 키로 사용
- 불필요한 매핑 제거
- 코드 직관성 향상
- `EXCD_BY_COUNTRY`: 국가별 거래소 순회를 위한 상수 추가

### 2.2 fetch_price_detail_oversea 수정

#### 변경 전
```python
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
```

#### 변경 후
```python
def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> dict:
    """해외주식 현재가상세

    해외주식 종목의 현재가, PER, PBR, EPS, BPS 등 상세 정보를 조회합니다.
    국가 코드에 따라 해당 국가의 거래소를 자동으로 탐색합니다.

    API 정보:
        - 경로: /uapi/overseas-price/v1/quotations/price-detail
        - TR ID: HHDFS76200200
        - 모의투자: 미지원

    Query Parameters:
        - AUTH (str): 사용자권한정보 (빈 문자열)
        - EXCD (str): 거래소코드
            - NYS: 뉴욕 (NYSE)
            - NAS: 나스닥 (NASDAQ)
            - AMS: 아멕스 (AMEX)
            - BAY: 뉴욕 주간거래
            - BAQ: 나스닥 주간거래
            - BAA: 아멕스 주간거래
            - HKS: 홍콩
            - TSE: 도쿄
            - SHS: 상하이
            - SZS: 심천
            - HSX: 호치민
            - HNX: 하노이
        - SYMB (str): 종목코드

    Args:
        symbol (str): 종목 코드 (예: AAPL, MSFT, TSLA)
        country_code (str): 국가 코드 (기본값: "US")
            - "US": 미국 (NYS → NAS → AMS → BAY → BAQ → BAA)
            - "HK": 홍콩 (HKS)
            - "JP": 일본 (TSE)
            - "CN": 중국 (SHS → SZS)
            - "VN": 베트남 (HSX → HNX)

    Returns:
        dict: API 응답. 주요 필드:
            - rt_cd (str): 성공/실패 ("0"=성공)
            - msg1 (str): 응답 메시지
            - output (dict): 응답 상세
                - rsym (str): 실시간조회종목코드
                - last (str): 현재가
                - open (str): 시가
                - high (str): 고가
                - low (str): 저가
                - base (str): 전일종가
                - tvol (str): 거래량
                - tamt (str): 거래대금
                - tomv (str): 시가총액
                - shar (str): 상장주수
                - perx (str): PER
                - pbrx (str): PBR
                - epsx (str): EPS
                - bpsx (str): BPS
                - h52p (str): 52주최고가
                - l52p (str): 52주최저가
                - vnit (str): 매매단위
                - e_hogau (str): 호가단위
                - e_icod (str): 업종(섹터)
                - curr (str): 통화

    Raises:
        ValueError: 지원하지 않는 country_code인 경우

    Note:
        - 지연시세: 미국 실시간무료(0분), 홍콩/베트남/중국/일본 15분 지연
        - 미국 주간거래 시간에도 동일한 API로 조회 가능
    """
    exchange_codes = EXCD_BY_COUNTRY.get(country_code)
    if not exchange_codes:
        raise ValueError(f"지원하지 않는 country_code: {country_code}")

    for exchange_code in exchange_codes:
        # ...
```

**이유:**
- `market` → `country_code`로 인자명 변경 (다른 메서드와 일관성)
- 기본값을 `"US"`로 변경 (해외주식 메서드이므로 합리적)
- `EXCD_BY_COUNTRY` 상수를 활용하여 국가별 거래소 순회
- API 문서 참고하여 docstring에 Query Parameters 및 응답 필드 상세 추가

## 3. 영향 범위

### 3.1 수정 대상 파일

| 파일 | 수정 내용 |
|------|----------|
| `korea_investment_stock/constants.py` | EXCD 키 변경, EXCD_BY_COUNTRY 추가 |
| `korea_investment_stock/korea_investment_stock.py` | `market` → `country_code` 변경, EXCD_BY_COUNTRY 활용 |
| `korea_investment_stock/cache/cached_korea_investment.py` | `market` → `country_code` 변경 |
| `korea_investment_stock/rate_limit/rate_limited_korea_investment.py` | `market` → `country_code` 변경 |

### 3.2 Breaking Changes

#### API 변경
```python
# 변경 전
result = broker.fetch_price_detail_oversea("AAPL", "US")
result = broker.fetch_price_detail_oversea("AAPL", market="US")

# 변경 후
result = broker.fetch_price_detail_oversea("AAPL")  # 기본값 "US"
result = broker.fetch_price_detail_oversea("AAPL", country_code="US")
result = broker.fetch_price_detail_oversea("9988", country_code="HK")  # 홍콩 알리바바
result = broker.fetch_price_detail_oversea("7203", country_code="JP")  # 일본 토요타
```

#### 상수 사용 변경
```python
# 변경 전
exchange = EXCD["NYSE"]  # "NYS"

# 변경 후
exchange = EXCD["NYS"]   # "NYS"

# 신규: 국가별 거래소 리스트
from korea_investment_stock.constants import EXCD_BY_COUNTRY
us_exchanges = EXCD_BY_COUNTRY["US"]  # ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]
```

### 3.3 하위 호환성

- **fetch_price_detail_oversea**: Breaking Change
  - 인자명 `market` → `country_code` 변경
  - 기존 `market="US"` 형태 사용 시 TypeError 발생
  - 위치 인자로 사용한 경우는 정상 동작 (단, 기본값이 "US"로 변경됨)
  - CHANGELOG에 마이그레이션 가이드 추가 필요

- **EXCD 상수**: Breaking Change
  - 기존 `EXCD["NYSE"]` 형태 사용 시 KeyError 발생
  - 그러나 현재 코드베이스에서 EXCD 상수를 직접 참조하는 곳 없음

## 4. 구현 계획

### 4.1 작업 순서

1. **constants.py 수정**
   - EXCD 딕셔너리 키 변경 (`"NYSE"` → `"NYS"`)
   - `EXCD_BY_COUNTRY` 상수 추가

2. **korea_investment_stock.py 수정**
   - `fetch_price_detail_oversea` 메서드 인자명 변경 (`market` → `country_code`)
   - 기본값 변경 (`"KR"` → `"US"`)
   - `EXCD_BY_COUNTRY` 상수 활용
   - docstring 업데이트

3. **Wrapper 클래스 수정**
   - `cached_korea_investment.py`: `market` → `country_code` 변경
   - `rate_limited_korea_investment.py`: `market` → `country_code` 변경

4. **테스트 수정**
   - 관련 테스트 케이스 업데이트

5. **문서 업데이트**
   - CLAUDE.md 업데이트
   - CHANGELOG.md 업데이트

### 4.2 테스트 체크리스트

- [ ] `fetch_price_detail_oversea("AAPL")` 정상 동작 (기본값 US)
- [ ] `fetch_price_detail_oversea("AAPL", country_code="US")` 정상 동작
- [ ] `fetch_price_detail_oversea("9988", country_code="HK")` 정상 동작 (홍콩)
- [ ] `fetch_price_detail_oversea("7203", country_code="JP")` 정상 동작 (일본)
- [ ] 지원하지 않는 country_code에 대해 ValueError 발생
- [ ] CachedKoreaInvestment 래퍼 정상 동작
- [ ] RateLimitedKoreaInvestment 래퍼 정상 동작
- [ ] 기존 테스트 통과

## 5. 마이그레이션 가이드

### 5.1 코드 변경 예시

```python
# Before (v1.x)
broker.fetch_price_detail_oversea("AAPL", "US")
broker.fetch_price_detail_oversea("AAPL", market="US")
broker.fetch_price_detail_oversea(symbol="AAPL", market="US")

# After (v2.x)
broker.fetch_price_detail_oversea("AAPL")  # 기본값 US
broker.fetch_price_detail_oversea("AAPL", country_code="US")
broker.fetch_price_detail_oversea(symbol="AAPL", country_code="US")

# 신규: 다른 국가 주식 조회
broker.fetch_price_detail_oversea("9988", country_code="HK")   # 홍콩 알리바바
broker.fetch_price_detail_oversea("7203", country_code="JP")   # 일본 토요타
broker.fetch_price_detail_oversea("600519", country_code="CN") # 중국 마오타이
broker.fetch_price_detail_oversea("VNM", country_code="VN")    # 베트남
```

### 5.2 상수 사용 변경

```python
# Before
from korea_investment_stock.constants import EXCD
exchange = EXCD["NYSE"]  # KeyError in v2.x

# After
from korea_investment_stock.constants import EXCD, EXCD_BY_COUNTRY
exchange = EXCD["NYS"]   # "NYS"

# 신규: 국가별 거래소 리스트 활용
us_exchanges = EXCD_BY_COUNTRY["US"]  # ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]
hk_exchanges = EXCD_BY_COUNTRY["HK"]  # ["HKS"]
```
