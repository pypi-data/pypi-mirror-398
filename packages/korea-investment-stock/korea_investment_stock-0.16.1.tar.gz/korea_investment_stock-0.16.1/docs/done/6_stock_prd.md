# fetch_stock_info, fetch_search_stock_info 개선 PRD

## 1. 개요

### 1.1 목적

`fetch_stock_info`와 `fetch_search_stock_info` 메서드의 인자명을 `market`에서 `country_code`로 변경하고, API 문서 기반의 상세 docstring을 추가합니다.

### 1.2 배경

- `fetch_price_detail_oversea` 메서드는 이미 `country_code` 인자를 사용하도록 리팩토링 완료 ([4_fetch_implementation.md](../done/4_fetch_implementation.md) 참조)
- 일관성을 위해 `fetch_stock_info`, `fetch_search_stock_info`도 동일한 패턴으로 변경 필요
- constants.py에 정의된 상수를 활용하여 코드 품질 향상

## 2. 현재 상태 분석

### 2.1 fetch_stock_info (상품기본조회)

**파일**: [korea_investment_stock.py:593](../../korea_investment_stock/korea_investment_stock.py#L593)

```python
def fetch_stock_info(self, symbol: str, market: str = "KR"):
    path = "uapi/domestic-stock/v1/quotations/search-info"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "CTPF1604R"
    }

    for market_code in MARKET_TYPE_MAP[market]:
        try:
            params = {
                "PDNO": symbol,
                "PRDT_TYPE_CD": market_code
            }
            # ...
```

**문제점**:
- docstring 없음
- 인자명 `market`이 `country_code`와 일관성 없음
- API 문서 정보(TR ID, 파라미터 설명 등) 미포함

### 2.2 fetch_search_stock_info (주식기본조회)

**파일**: [korea_investment_stock.py:623](../../korea_investment_stock/korea_investment_stock.py#L623)

```python
def fetch_search_stock_info(self, symbol: str, market: str = "KR"):
    """
    국내 주식만 제공하는 API이다
    """
    path = "uapi/domestic-stock/v1/quotations/search-stock-info"
    # ...
    headers = {
        # ...
        "tr_id": "CTPF1002R"
    }

    if market != "KR" and market != "KRX":
        raise ValueError("Market must be either 'KR' or 'KRX'.")
    # ...
```

**문제점**:
- 최소한의 docstring만 존재
- 인자명 `market`이 `country_code`와 일관성 없음
- API 문서 정보 미포함

## 3. API 문서 정보

### 3.1 상품기본조회 (fetch_stock_info)

**문서 위치**: [docs/api/국내주식/상품기본조회.md](../api/국내주식/상품기본조회.md)

| 항목 | 값 |
|------|-----|
| API 경로 | `/uapi/domestic-stock/v1/quotations/search-info` |
| Method | GET |
| 실전 TR ID | CTPF1604R |
| 모의 TR ID | 모의투자 미지원 |

**Query Parameters**:

| Parameter | 한글명 | Required | 설명 |
|-----------|--------|----------|------|
| PDNO | 상품번호 | Y | 종목코드 (예: 000660, AAPL) |
| PRDT_TYPE_CD | 상품유형코드 | Y | 아래 참조 |

**PRDT_TYPE_CD 값**:

| 코드 | 설명 | 상수명 (constants.py) |
|------|------|----------------------|
| 300 | 국내 주식 | `PRDT_TYPE_CD["KR_STOCK"]` |
| 301 | 선물옵션 | `PRDT_TYPE_CD["KR_FUTURES"]` |
| 302 | 채권 | `PRDT_TYPE_CD["KR_BOND"]` |
| 512 | 미국 나스닥 | `PRDT_TYPE_CD["US_NASDAQ"]` |
| 513 | 미국 뉴욕 | `PRDT_TYPE_CD["US_NYSE"]` |
| 529 | 미국 아멕스 | `PRDT_TYPE_CD["US_AMEX"]` |
| 515 | 일본 | `PRDT_TYPE_CD["JP"]` |
| 501 | 홍콩 | `PRDT_TYPE_CD["HK"]` |
| 543 | 홍콩CNY | `PRDT_TYPE_CD["HK_CNY"]` |
| 558 | 홍콩USD | `PRDT_TYPE_CD["HK_USD"]` |
| 507 | 베트남 하노이 | `PRDT_TYPE_CD["VN_HANOI"]` |
| 508 | 베트남 호치민 | `PRDT_TYPE_CD["VN_HOCHIMINH"]` |
| 551 | 중국 상해A | `PRDT_TYPE_CD["CN_SHANGHAI"]` |
| 552 | 중국 심천A | `PRDT_TYPE_CD["CN_SHENZHEN"]` |

**주요 응답 필드** (output):
- `pdno`: 상품번호
- `prdt_type_cd`: 상품유형코드
- `prdt_name`: 상품명
- `prdt_eng_name`: 상품영문명
- `std_pdno`: 표준상품번호 (ISIN)
- `prdt_clsf_name`: 상품분류명
- `sale_strt_dt`: 판매시작일자
- `sale_end_dt`: 판매종료일자

### 3.2 주식기본조회 (fetch_search_stock_info)

**문서 위치**: [docs/api/국내주식/주식기본조회.md](../api/국내주식/주식기본조회.md)

| 항목 | 값 |
|------|-----|
| API 경로 | `/uapi/domestic-stock/v1/quotations/search-stock-info` |
| Method | GET |
| 실전 TR ID | CTPF1002R |
| 모의 TR ID | 모의투자 미지원 |

**Query Parameters**:

| Parameter | 한글명 | Required | 설명 |
|-----------|--------|----------|------|
| PRDT_TYPE_CD | 상품유형코드 | Y | 300 (주식/ETF/ETN/ELW), 301 (선물옵션), 302 (채권), 306 (ELS) |
| PDNO | 상품번호 | Y | 종목번호 (6자리), ETN은 Q로 시작 |

**⚠️ 중요**: 이 API는 **국내주식만 지원**합니다.

**주요 응답 필드** (output):
- `pdno`: 상품번호
- `prdt_type_cd`: 상품유형코드
- `mket_id_cd`: 시장ID코드 (STK=유가증권, KSQ=코스닥, KNX=코넥스)
- `scty_grp_id_cd`: 증권그룹ID코드 (ST=주권, EF=ETF, EN=ETN, EW=ELW)
- `excg_dvsn_cd`: 거래소구분코드
- `lstg_stqt`: 상장주수
- `cpta`: 자본금
- `papr`: 액면가
- `kospi200_item_yn`: 코스피200종목여부
- `prdt_name`: 상품명
- `prdt_eng_name`: 상품영문명
- `std_pdno`: 표준상품번호 (ISIN)
- `tr_stop_yn`: 거래정지여부
- `admn_item_yn`: 관리종목여부

### 3.3 해외주식 상품기본정보 (참고)

**문서 위치**: [docs/api/해외주식/해외주식_상품기본정보.md](../api/해외주식/해외주식_상품기본정보.md)

| 항목 | 값 |
|------|-----|
| API 경로 | `/uapi/overseas-price/v1/quotations/search-info` |
| Method | GET |
| 실전 TR ID | CTPF1702R |
| 모의 TR ID | 모의투자 미지원 |

**참고**: 상품기본조회(CTPF1604R)로 해외주식도 조회 가능하지만, 더 상세한 해외주식 정보가 필요한 경우 별도 API(CTPF1702R) 사용 가능

## 4. 변경 요약

### 4.1 메서드 시그니처 변경

| 메서드 | 변경 전 | 변경 후 |
|--------|---------|---------|
| `fetch_stock_info` | `(symbol, market="KR")` | `(symbol, country_code="KR") -> dict` |
| `fetch_search_stock_info` | `(symbol, market="KR")` | `(symbol, country_code="KR") -> dict` |

### 4.2 주요 변경 내용

- 인자명: `market` → `country_code`
- 반환 타입 힌트 추가: `-> dict`
- API 문서 기반 상세 docstring 추가
- 내부 상수 참조 변경: `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY`

상세 구현 내용은 [6_stock_implementation.md](./6_stock_implementation.md) 참조

## 5. 수정 대상 파일

### 5.1 필수 수정

| 파일 | 변경 내용 |
|------|----------|
| [constants.py:103](../../korea_investment_stock/constants.py#L103) | `OVRS_EXCG_CD` 키 변경 (NASD:NASD 형태) |
| [constants.py:148](../../korea_investment_stock/constants.py#L148) | `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY` 개선 |
| [korea_investment_stock.py:593](../../korea_investment_stock/korea_investment_stock.py#L593) | `fetch_stock_info` 메서드 시그니처 및 docstring 변경 |
| [korea_investment_stock.py:623](../../korea_investment_stock/korea_investment_stock.py#L623) | `fetch_search_stock_info` 메서드 시그니처 및 docstring 변경 |
| [cached_korea_investment.py:106](../../korea_investment_stock/cache/cached_korea_investment.py#L106) | `fetch_stock_info` 래퍼 메서드 시그니처 변경 |
| [cached_korea_investment.py:124](../../korea_investment_stock/cache/cached_korea_investment.py#L124) | `fetch_search_stock_info` 래퍼 메서드 시그니처 변경 |
| [rate_limited_korea_investment.py:86](../../korea_investment_stock/rate_limit/rate_limited_korea_investment.py#L86) | `fetch_stock_info` 래퍼 메서드 시그니처 변경 |
| [rate_limited_korea_investment.py:100](../../korea_investment_stock/rate_limit/rate_limited_korea_investment.py#L100) | `fetch_search_stock_info` 래퍼 메서드 시그니처 변경 |

### 5.2 문서 업데이트

| 파일 | 변경 내용 |
|------|----------|
| [CLAUDE.md](../../CLAUDE.md) | 메서드 시그니처 업데이트 |
| [CHANGELOG.md](../../CHANGELOG.md) | Breaking Changes 추가 |

## 6. constants.py 개선

### 6.1 OVRS_EXCG_CD 키 변경

`EXCD` 패턴과 일관성을 위해 키를 API 파라미터 값으로 변경:
- `"NASDAQ"` → `"NASD"`
- `"HONGKONG"` → `"SEHK"` 등

### 6.2 MARKET_TYPE_MAP → PRDT_TYPE_CD_BY_COUNTRY

| 개선 항목 | 변경 내용 |
|-----------|----------|
| 변수명 | `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY` |
| 값 형태 | 하드코딩 문자열 → `PRDT_TYPE_CD` 상수 참조 |
| 키 정리 | 거래소 코드 키 제거, 국가 코드만 유지 |

상세 구현은 [6_stock_implementation.md](./6_stock_implementation.md) 섹션 1 참조

## 7. Breaking Changes

### 7.1 API 호출 방식 변경

```python
# 변경 전
broker.fetch_stock_info("005930", market="KR")
broker.fetch_search_stock_info("005930", market="KR")

# 변경 후
broker.fetch_stock_info("005930", country_code="KR")
broker.fetch_search_stock_info("005930", country_code="KR")

# 기본값 사용 (호환성 유지)
broker.fetch_stock_info("005930")           # OK (기본값 "KR")
broker.fetch_search_stock_info("005930")    # OK (기본값 "KR")
```

### 7.2 위치 인자 사용 시 호환성

```python
# 위치 인자로 사용 시 - 동작은 동일
broker.fetch_stock_info("005930", "KR")           # OK
broker.fetch_search_stock_info("005930", "KR")    # OK
```

### 7.3 키워드 인자 사용 시 - Breaking Change

```python
# 키워드 인자 사용 시 - 변경 필요
broker.fetch_stock_info("005930", market="KR")    # ❌ TypeError
broker.fetch_stock_info("005930", country_code="KR")  # ✅
```

## 8. 테스트 및 작업 체크리스트

테스트 계획 및 작업 체크리스트는 [6_stock_todo.md](./6_stock_todo.md) 참조

## 9. 참고 자료

- [4_fetch_implementation.md](../done/4_fetch_implementation.md) - fetch_price_detail_oversea 리팩토링 가이드
- [상품기본조회 API 문서](../api/국내주식/상품기본조회.md)
- [주식기본조회 API 문서](../api/국내주식/주식기본조회.md)
- [해외주식 상품기본정보 API 문서](../api/해외주식/해외주식_상품기본정보.md)
