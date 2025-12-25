# fetch_domestic_price와 fetch_etf_domestic_price 병합 PRD

> **중복 코드 제거**: `tr_id` 헤더 값 하나만 다른 두 메서드를 하나로 통합

## Quick Summary

### 현재 문제
- `fetch_domestic_price`와 `fetch_etf_domestic_price`: **95% 동일한 코드**
- 차이점: `tr_id` 헤더 값 하나 (`FHKST01010100` vs `FHPST02400000`)
- 코드 중복: **~48줄** (24줄 × 2)

### 제안
```python
# Before: 2개 메서드 (48줄)
def fetch_domestic_price(self, market_code, symbol): ...   # tr_id: FHKST01010100
def fetch_etf_domestic_price(self, market_code, symbol): ... # tr_id: FHPST02400000

# After: 1개 메서드 (24줄) - market_code 인자 제거
def fetch_domestic_price(self, symbol, symbol_type="Stock"): ...
```

### 예상 효과
- ✅ 코드 중복 제거: **48줄 → 24줄** (50% 감소)
- ✅ 유지보수성 향상: 하나의 메서드만 관리
- ✅ API 단순화: `fetch_etf_domestic_price` 메서드 삭제

---

## 목차

1. [문제 분석](#1-문제-분석)
2. [리팩토링 제안](#2-리팩토링-제안)
3. [Breaking Changes](#3-breaking-changes)
4. [구현 계획](#4-구현-계획)
5. [테스트 전략](#5-테스트-전략)

---

## 1. 문제 분석

### 1.1 현재 코드 비교

#### `fetch_domestic_price` (lines 348-371)

```python
def fetch_domestic_price(self, market_code: str, symbol: str) -> dict:
    """국내 주식현재가시세"""
    path = "uapi/domestic-stock/v1/quotations/inquire-price"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "FHKST01010100"  # 일반 주식
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": market_code,
        "FID_INPUT_ISCD": symbol
    }
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()
```

#### `fetch_etf_domestic_price` (lines 323-346)

```python
def fetch_etf_domestic_price(self, market_code: str, symbol: str) -> dict:
    """ETF 주식현재가시세"""
    path = "uapi/domestic-stock/v1/quotations/inquire-price"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "FHPST02400000"  # ETF
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": market_code,
        "FID_INPUT_ISCD": symbol
    }
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()
```

### 1.2 차이점 분석

| 항목 | `fetch_domestic_price` | `fetch_etf_domestic_price` |
|------|------------------------|---------------------------|
| API 엔드포인트 | `uapi/domestic-stock/v1/quotations/inquire-price` | **동일** |
| 파라미터 | `FID_COND_MRKT_DIV_CODE`, `FID_INPUT_ISCD` | **동일** |
| 헤더 구조 | 동일 | **동일** |
| **tr_id** | `FHKST01010100` | `FHPST02400000` |

**결론**: `tr_id` 값 하나만 다르고 나머지 100% 동일

### 1.3 호출 흐름

```
fetch_price(symbol, country_code)
    │
    ├─ country_code == "KR" or "KRX"
    │   └─ fetch_stock_info() → get_symbol_type()
    │       ├─ ETF → fetch_domestic_price(symbol, "ETF")
    │       └─ Stock → fetch_domestic_price(symbol, "Stock")
    │
    └─ country_code == "US"
        └─ fetch_price_detail_oversea(symbol, country_code)
```

### 1.4 중복 코드 통계

- 중복 라인 수: **~20줄** (95% 동일)
- 유일한 차이: 1줄 (`tr_id` 값)
- DRY 원칙 위반

---

## 2. 리팩토링 제안

### 2.1 통합 메서드 설계

```python
from .constants import FID_COND_MRKT_DIV_CODE_STOCK

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
        "FID_COND_MRKT_DIV_CODE": FID_COND_MRKT_DIV_CODE_STOCK.UNIFIED,
        "FID_INPUT_ISCD": symbol
    }
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()
```

### 2.2 fetch_price 호출 변경

```python
# Before
if symbol_type == "ETF":
    resp_json = self.fetch_etf_domestic_price("J", symbol)
else:
    resp_json = self.fetch_domestic_price("J", symbol)

# After
resp_json = self.fetch_domestic_price(symbol, symbol_type)
```

---

## 3. Breaking Changes

### 3.1 변경 사항

| 기존 호출 | 리팩토링 후 |
|----------|------------|
| `fetch_domestic_price("J", "005930")` | `fetch_domestic_price("005930")` |
| `fetch_etf_domestic_price("J", "069500")` | `fetch_domestic_price("069500", "ETF")` |

### 3.2 삭제되는 메서드

- `fetch_etf_domestic_price` → **삭제**
- `fetch_domestic_price`의 `market_code` 파라미터 → **삭제**

---

## 4. 구현 계획

### 4.1 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| [korea_investment_stock.py](../../korea_investment_stock/korea_investment_stock.py) | 메서드 병합 |

### 4.2 단계별 작업

#### Step 1: fetch_domestic_price 수정 (5분)
- `market_code` 파라미터 제거
- `symbol_type` 파라미터 추가
- `TR_ID_MAP` 딕셔너리 추가
- `FID_COND_MRKT_DIV_CODE_STOCK.UNIFIED` 상수 사용

#### Step 2: fetch_price 수정 (2분)
- `fetch_etf_domestic_price` → `fetch_domestic_price(..., "ETF")` 변경

#### Step 3: fetch_etf_domestic_price 삭제 (2분)
- 메서드 삭제

#### Step 4: 테스트 (5분)
- 기존 테스트 실행
- 수동 검증

---

## 5. 테스트 전략

### 5.1 단위 테스트

```python
def test_fetch_domestic_price_stock():
    """일반 주식 시세 조회"""
    result = broker.fetch_domestic_price("005930")
    assert result['rt_cd'] == '0'

def test_fetch_domestic_price_etf():
    """ETF 시세 조회"""
    result = broker.fetch_domestic_price("069500", symbol_type="ETF")
    assert result['rt_cd'] == '0'

def test_fetch_domestic_price_default_symbol_type():
    """기본값 symbol_type="Stock" 테스트"""
    result = broker.fetch_domestic_price("005930")
    # Stock tr_id가 사용되었는지 확인
```

### 5.2 통합 테스트

```bash
# 기존 테스트 실행
pytest korea_investment_stock/tests/ -v

# 통합 테스트
pytest korea_investment_stock/tests/test_integration_us_stocks.py -v
```

### 5.3 수동 검증

```python
# 삼성전자 (주식)
result = broker.fetch_price("005930", country_code="KR")
print(result['output']['stck_prpr'])

# KODEX 200 (ETF)
result = broker.fetch_price("069500", country_code="KR")
print(result['output']['stck_prpr'])
```

---

## 부록: Transaction ID 참조

| tr_id | 용도 | API 문서 |
|-------|------|----------|
| `FHKST01010100` | 국내 주식 현재가 시세 | [주식현재가 시세](https://apiportal.koreainvestment.com) |
| `FHPST02400000` | 국내 ETF 현재가 시세 | [ETF현재가 시세](https://apiportal.koreainvestment.com) |

---

**문서 버전**: 1.0
**작성일**: 2025-12-06
**상태**: 분석 완료
**다음 단계**: 리팩토링 구현 결정
