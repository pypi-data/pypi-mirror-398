# 종목별 투자자매매동향(일별) API 추가 PRD

## 1. 개요

### 1.1 목표

특정 종목에 대해 날짜별 외국인/기관/개인의 매수/매도 현황을 조회하는 API를 추가합니다.

### 1.2 배경

- 투자자들이 특정 종목의 수급 동향을 파악하는 데 필수적인 정보
- 외국인/기관의 순매수/순매도 추이 분석에 활용
- 한국투자증권 HTS [0416] 종목별 일별동향 화면과 동일한 기능

---

## 2. API 문서 정보

**문서 위치**: [docs/api/국내주식/종목별_투자자매매동향(일별).md](../api/국내주식/종목별_투자자매매동향(일별).md)

### 2.1 API 기본 정보

| 항목 | 값 |
|------|-----|
| API 경로 | `/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily` |
| Method | GET |
| 실전 TR ID | `FHPTJ04160001` |
| 모의 TR ID | 모의투자 미지원 |
| HTS 화면 | [0416] 종목별 일별동향 |

### 2.2 Query Parameters

| Parameter | 한글명 | Required | 설명 |
|-----------|--------|----------|------|
| FID_COND_MRKT_DIV_CODE | 시장 분류 코드 | Y | J: KRX, NX: NXT, UN: 통합 |
| FID_INPUT_ISCD | 종목코드 | Y | 종목번호 6자리 (예: 005930) |
| FID_INPUT_DATE_1 | 조회 날짜 | Y | YYYYMMDD 형식 (예: 20251213) |
| FID_ORG_ADJ_PRC | 수정주가 원주가 | Y | 공란 입력 |
| FID_ETC_CLS_CODE | 기타 구분 코드 | Y | 공란 입력 |

### 2.3 주요 응답 필드

#### output1 (종목 현재 정보)

| 필드명 | 한글명 | 설명 |
|--------|--------|------|
| stck_prpr | 주식 현재가 | |
| prdy_vrss | 전일 대비 | |
| prdy_ctrt | 전일 대비율 | % |
| acml_vol | 누적 거래량 | |

#### output2 (일별 투자자 매매동향) - Array

**순매수 수량:**

| 필드명 | 한글명 | 단위 |
|--------|--------|------|
| frgn_ntby_qty | 외국인 순매수 수량 | 주 |
| orgn_ntby_qty | 기관계 순매수 수량 | 주 |
| prsn_ntby_qty | 개인 순매수 수량 | 주 |

**매수 거래량:**

| 필드명 | 한글명 | 단위 |
|--------|--------|------|
| frgn_shnu_vol | 외국인 매수 거래량 | 주 |
| orgn_shnu_vol | 기관계 매수 거래량 | 주 |
| prsn_shnu_vol | 개인 매수 거래량 | 주 |

**매도 거래량:**

| 필드명 | 한글명 | 단위 |
|--------|--------|------|
| frgn_seln_vol | 외국인 매도 거래량 | 주 |
| orgn_seln_vol | 기관계 매도 거래량 | 주 |
| prsn_seln_vol | 개인 매도 거래량 | 주 |

**기관 세부 분류:**

| 필드명 | 한글명 |
|--------|--------|
| scrt_ntby_qty | 증권 순매수 수량 |
| ivtr_ntby_qty | 투자신탁 순매수 수량 |
| pe_fund_ntby_vol | 사모펀드 순매수 거래량 |
| bank_ntby_qty | 은행 순매수 수량 |
| insu_ntby_qty | 보험 순매수 수량 |
| mrbn_ntby_qty | 종금 순매수 수량 |
| fund_ntby_qty | 기금 순매수 수량 |

**금액 정보 (단위: 백만원):**

| 필드명 | 한글명 |
|--------|--------|
| frgn_ntby_tr_pbmn | 외국인 순매수 거래 대금 |
| orgn_ntby_tr_pbmn | 기관계 순매수 거래 대금 |
| prsn_ntby_tr_pbmn | 개인 순매수 거래 대금 |

---

## 3. 구현 계획

### 3.1 메서드 시그니처

```python
def fetch_investor_trading_by_stock_daily(
    self,
    symbol: str,
    date: str,
    market_code: str = "J"
) -> dict:
    """종목별 투자자매매동향(일별) 조회 [v1_국내주식]

    특정 종목의 날짜별 외국인/기관/개인 매수매도 현황을 조회합니다.
    한국투자 HTS [0416] 종목별 일별동향 화면과 동일한 기능입니다.

    ※ 단위: 금액(백만원), 수량(주)
    ※ 당일 데이터는 장 종료 후 정상 조회 가능

    API 정보:
        - 경로: /uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily
        - Method: GET
        - 실전 TR ID: FHPTJ04160001
        - 모의투자: 미지원

    Args:
        symbol (str): 종목코드 6자리 (예: "005930")
        date (str): 조회 날짜 YYYYMMDD 형식 (예: "20251213")
        market_code (str): 시장 분류 코드 (기본값: "J")
            - "J": KRX (기본값)
            - "NX": NXT
            - "UN": 통합

    Returns:
        dict: API 응답 딕셔너리
            - rt_cd: 성공 실패 여부 ("0": 성공)
            - msg_cd: 응답코드
            - msg1: 응답메시지
            - output1: 종목 현재가 정보
            - output2: 일별 투자자 매매동향 리스트

    Example:
        >>> # 삼성전자 2025년 12월 13일 투자자 매매동향
        >>> result = broker.fetch_investor_trading_by_stock_daily("005930", "20251213")
        >>> if result['rt_cd'] == '0':
        ...     for day in result['output2']:
        ...         print(f"날짜: {day['stck_bsop_date']}")
        ...         print(f"외국인 순매수: {day['frgn_ntby_qty']}주")
        ...         print(f"기관 순매수: {day['orgn_ntby_qty']}주")
        ...         print(f"개인 순매수: {day['prsn_ntby_qty']}주")
    """
```

### 3.2 구현 패턴

기존 `fetch_stock_info`, `fetch_domestic_price` 메서드와 동일한 패턴 사용:

```python
def fetch_investor_trading_by_stock_daily(
    self,
    symbol: str,
    date: str,
    market_code: str = "J"
) -> dict:
    path = "uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily"
    url = f"{self.base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "FHPTJ04160001"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": market_code,
        "FID_INPUT_ISCD": symbol,
        "FID_INPUT_DATE_1": date,
        "FID_ORG_ADJ_PRC": "",
        "FID_ETC_CLS_CODE": ""
    }
    return self._request_with_token_refresh("GET", url, headers, params)
```

---

## 4. 수정 대상 파일

### 4.1 필수 수정

| 파일 | 변경 내용 |
|------|----------|
| `korea_investment_stock/korea_investment_stock.py` | `fetch_investor_trading_by_stock_daily` 메서드 추가 |
| `korea_investment_stock/cache/cached_korea_investment.py` | 래퍼 메서드 추가 (캐시 지원) |
| `korea_investment_stock/rate_limit/rate_limited_korea_investment.py` | 래퍼 메서드 추가 |

### 4.2 테스트 파일

| 파일 | 변경 내용 |
|------|----------|
| `korea_investment_stock/tests/test_korea_investment_stock.py` | 단위 테스트 추가 |
| `korea_investment_stock/tests/test_integration_investor.py` | 통합 테스트 (신규) |

### 4.3 문서 업데이트

| 파일 | 변경 내용 |
|------|----------|
| `CLAUDE.md` | API 메서드 목록에 추가 |
| `CHANGELOG.md` | 신규 기능 추가 기록 |
| `korea_investment_stock/__init__.py` | export 확인 (필요시) |

---

## 5. 캐시 전략

### 5.1 TTL 권장값

| 데이터 유형 | TTL | 이유 |
|------------|-----|------|
| 당일 데이터 | 캐시 미적용 또는 5초 | 장중 실시간 변동 |
| 과거 날짜 데이터 | 1시간 (3600초) | 확정된 데이터로 변동 없음 |

### 5.2 CachedKoreaInvestment 구현

```python
def fetch_investor_trading_by_stock_daily(
    self,
    symbol: str,
    date: str,
    market_code: str = "J"
) -> dict:
    """투자자 매매동향 조회 (캐시 적용)"""
    cache_key = f"investor_trading:{symbol}:{date}:{market_code}"

    # 과거 데이터는 더 긴 TTL 적용
    today = datetime.now().strftime("%Y%m%d")
    ttl = self._investor_ttl if date < today else self._price_ttl

    return self._get_or_fetch(
        cache_key,
        lambda: self._broker.fetch_investor_trading_by_stock_daily(symbol, date, market_code),
        ttl
    )
```

---

## 6. 테스트 계획

### 6.1 단위 테스트

```python
class TestFetchInvestorTradingByStockDaily:
    """fetch_investor_trading_by_stock_daily 단위 테스트"""

    def test_success_response(self, mock_broker):
        """성공 응답 테스트"""
        pass

    def test_invalid_symbol(self, mock_broker):
        """잘못된 종목코드 테스트"""
        pass

    def test_invalid_date_format(self, mock_broker):
        """잘못된 날짜 형식 테스트"""
        pass

    def test_market_code_options(self, mock_broker):
        """시장 코드 옵션 테스트 (J, NX, UN)"""
        pass
```

### 6.2 통합 테스트 (API 자격 증명 필요)

```bash
# 통합 테스트 실행
pytest korea_investment_stock/tests/test_integration_investor.py -v
```

```python
@pytest.mark.integration
class TestInvestorTradingIntegration:
    """투자자 매매동향 API 통합 테스트"""

    def test_samsung_investor_trading(self, broker):
        """삼성전자 투자자 매매동향 조회"""
        result = broker.fetch_investor_trading_by_stock_daily(
            "005930",
            (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        )
        assert result['rt_cd'] == '0'
        assert 'output2' in result
```

---

## 7. 사용 예시

### 7.1 기본 사용

```python
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment()

# 삼성전자 어제 투자자 매매동향
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

result = broker.fetch_investor_trading_by_stock_daily("005930", yesterday)

if result['rt_cd'] == '0':
    for day in result['output2']:
        print(f"날짜: {day['stck_bsop_date']}")
        print(f"외국인 순매수: {day['frgn_ntby_qty']}주 ({day['frgn_ntby_tr_pbmn']}백만원)")
        print(f"기관 순매수: {day['orgn_ntby_qty']}주 ({day['orgn_ntby_tr_pbmn']}백만원)")
        print(f"개인 순매수: {day['prsn_ntby_qty']}주")
```

### 7.2 캐시 및 Rate Limit 적용

```python
from korea_investment_stock import (
    KoreaInvestment,
    CachedKoreaInvestment,
    RateLimitedKoreaInvestment
)

broker = KoreaInvestment()
cached = CachedKoreaInvestment(broker, investor_ttl=3600)  # 1시간 캐시
safe_broker = RateLimitedKoreaInvestment(cached, calls_per_second=15)

# 여러 종목 조회도 안전하게
symbols = ["005930", "000660", "035420"]
for symbol in symbols:
    result = safe_broker.fetch_investor_trading_by_stock_daily(symbol, yesterday)
    # 처리...
```

---

## 8. Breaking Changes

**없음** - 신규 API 추가이므로 기존 코드에 영향 없음

---

## 9. 참고 자료

- [종목별 투자자매매동향(일별) API 문서](../api/국내주식/종목별_투자자매매동향(일별).md)
- [주식현재가 투자자 API 문서](../api/국내주식/주식현재가_투자자.md) - 유사 API 참고
- [기존 fetch_stock_info 구현](../../korea_investment_stock/korea_investment_stock.py) - 구현 패턴 참고
