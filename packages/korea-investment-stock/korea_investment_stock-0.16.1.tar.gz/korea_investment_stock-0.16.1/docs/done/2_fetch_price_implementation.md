# fetch_domestic_price와 fetch_etf_domestic_price 병합 구현

## 변경 범위

| 파일 | 변경 내용 |
|------|----------|
| `korea_investment_stock/korea_investment_stock.py` | 메서드 병합, `fetch_etf_domestic_price` 삭제 |
| `korea_investment_stock/cache/cached_korea_investment.py` | 래퍼 메서드 시그니처 변경 |
| `korea_investment_stock/rate_limit/rate_limited_korea_investment.py` | 래퍼 메서드 시그니처 변경 |

---

## 1. KoreaInvestment 클래스 수정

### 1.1 fetch_domestic_price 변경

**현재 코드** (lines 348-371):
```python
def fetch_domestic_price(self, market_code: str, symbol: str) -> dict:
```

**변경 후**:
```python
def fetch_domestic_price(
    self,
    symbol: str,
    symbol_type: str = "Stock"
) -> dict:
    """국내 주식/ETF 현재가시세

    Args:
        symbol: 종목코드 (ex: 005930)
        symbol_type: 상품 타입 ("Stock" 또는 "ETF")

    Returns:
        dict: API 응답 데이터
    """
    TR_ID_MAP = {
        "Stock": "FHKST01010100",
        "ETF": "FHPST02400000"
    }

    path = "uapi/domestic-stock/v1/quotations/inquire-price"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": TR_ID_MAP.get(symbol_type, "FHKST01010100")
    }
    params = {
        "fid_cond_mrkt_div_code": FID_COND_MRKT_DIV_CODE_STOCK["UNIFIED"],
        "fid_input_iscd": symbol
    }
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()
```

### 1.2 fetch_price 호출 변경

**현재 코드** (lines 296-299):
```python
if symbol_type == "ETF":
    resp_json = self.fetch_etf_domestic_price("J", symbol)
else:
    resp_json = self.fetch_domestic_price("J", symbol)
```

**변경 후**:
```python
resp_json = self.fetch_domestic_price(symbol, symbol_type)
```

### 1.3 fetch_etf_domestic_price 삭제

lines 323-346 전체 삭제

---

## 2. CachedKoreaInvestment 래퍼 수정

**현재 코드** (lines 70-104):
- `fetch_domestic_price(market_code, symbol)`
- `fetch_etf_domestic_price(market_code, symbol)`

**변경 후**:
```python
def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> dict:
    """국내 주식/ETF 가격 조회 (캐싱 지원)"""
    if not self.enable_cache:
        return self.broker.fetch_domestic_price(symbol, symbol_type)

    cache_key = self._make_cache_key("fetch_domestic_price", symbol, symbol_type)
    cached_data = self.cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    result = self.broker.fetch_domestic_price(symbol, symbol_type)

    if result.get('rt_cd') == '0':
        self.cache.set(cache_key, result, self.ttl['price'])

    return result
```

`fetch_etf_domestic_price` 메서드 삭제

---

## 3. RateLimitedKoreaInvestment 래퍼 수정

**현재 코드** (lines 58-84):
- `fetch_domestic_price(market_code, symbol)`
- `fetch_etf_domestic_price(market_code, symbol)`

**변경 후**:
```python
def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> Dict[str, Any]:
    """속도 제한이 적용된 국내 주식/ETF 가격 조회"""
    self._rate_limiter.wait()
    return self._broker.fetch_domestic_price(symbol, symbol_type)
```

`fetch_etf_domestic_price` 메서드 삭제

---

## 4. 상수 사용

`FID_COND_MRKT_DIV_CODE_STOCK["UNIFIED"]` 사용:
- 기존: `"J"` (하드코딩)
- 변경: `FID_COND_MRKT_DIV_CODE_STOCK["UNIFIED"]` → `"UN"` (통합)

import 추가:
```python
from .constants import FID_COND_MRKT_DIV_CODE_STOCK
```

---

## Breaking Changes

| 기존 호출 | 신규 호출 |
|----------|----------|
| `fetch_domestic_price("J", "005930")` | `fetch_domestic_price("005930")` |
| `fetch_etf_domestic_price("J", "069500")` | `fetch_domestic_price("069500", "ETF")` |

**삭제되는 메서드**: `fetch_etf_domestic_price`

---

## 코드 감소 효과

- 중복 코드: **48줄 → 24줄** (50% 감소)
- 삭제 메서드: 1개 (`fetch_etf_domestic_price`)
- 유지보수: 하나의 메서드만 관리
