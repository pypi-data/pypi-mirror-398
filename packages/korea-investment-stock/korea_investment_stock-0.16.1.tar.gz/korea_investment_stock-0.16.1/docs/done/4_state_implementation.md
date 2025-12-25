# 종목별 투자자매매동향(일별) API 구현 가이드

## 1. 핵심 구현 사항

### 1.1 메서드 추가 위치

`korea_investment_stock/korea_investment_stock.py`의 `KoreaInvestment` 클래스에 메서드 추가

### 1.2 구현 코드

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

## 2. CachedKoreaInvestment 래퍼 추가

`korea_investment_stock/cache/cached_korea_investment.py`에 래퍼 메서드 추가

```python
def fetch_investor_trading_by_stock_daily(
    self,
    symbol: str,
    date: str,
    market_code: str = "J"
) -> dict:
    """투자자 매매동향 조회 (캐시 적용)"""
    cache_key = f"investor_trading:{symbol}:{date}:{market_code}"

    # 과거 데이터는 더 긴 TTL 적용 (1시간)
    today = datetime.now().strftime("%Y%m%d")
    ttl = 3600 if date < today else self._price_ttl

    return self._get_or_fetch(
        cache_key,
        lambda: self._broker.fetch_investor_trading_by_stock_daily(symbol, date, market_code),
        ttl
    )
```

---

## 3. RateLimitedKoreaInvestment 래퍼 추가

`korea_investment_stock/rate_limit/rate_limited_korea_investment.py`에 래퍼 메서드 추가

```python
def fetch_investor_trading_by_stock_daily(
    self,
    symbol: str,
    date: str,
    market_code: str = "J"
) -> dict:
    """투자자 매매동향 조회 (Rate Limit 적용)"""
    self._rate_limiter.wait()
    return self._broker.fetch_investor_trading_by_stock_daily(symbol, date, market_code)
```

---

## 4. 단위 테스트

`korea_investment_stock/tests/test_korea_investment_stock.py`에 테스트 추가

```python
class TestFetchInvestorTradingByStockDaily:
    """fetch_investor_trading_by_stock_daily 단위 테스트"""

    def test_success_response(self, mock_broker):
        """성공 응답 테스트"""
        mock_response = {
            'rt_cd': '0',
            'msg_cd': 'MCA00000',
            'msg1': '정상처리되었습니다',
            'output1': {
                'stck_prpr': '70000',
                'prdy_vrss': '1000',
                'prdy_ctrt': '1.45',
                'acml_vol': '10000000'
            },
            'output2': [
                {
                    'stck_bsop_date': '20251212',
                    'frgn_ntby_qty': '100000',
                    'orgn_ntby_qty': '-50000',
                    'prsn_ntby_qty': '-50000'
                }
            ]
        }
        with patch.object(mock_broker, '_request_with_token_refresh', return_value=mock_response):
            result = mock_broker.fetch_investor_trading_by_stock_daily("005930", "20251212")
            assert result['rt_cd'] == '0'
            assert 'output2' in result
            assert len(result['output2']) > 0

    def test_market_code_options(self, mock_broker):
        """시장 코드 옵션 테스트 (J, NX, UN)"""
        for market_code in ["J", "NX", "UN"]:
            with patch.object(mock_broker, '_request_with_token_refresh') as mock_request:
                mock_request.return_value = {'rt_cd': '0'}
                mock_broker.fetch_investor_trading_by_stock_daily("005930", "20251212", market_code)

                # params 검증
                call_args = mock_request.call_args
                params = call_args[0][3]  # 4번째 인자가 params
                assert params["FID_COND_MRKT_DIV_CODE"] == market_code
```

---

## 5. 통합 테스트 (신규 파일)

`korea_investment_stock/tests/test_integration_investor.py`

```python
import pytest
from datetime import datetime, timedelta
from korea_investment_stock import KoreaInvestment


@pytest.mark.integration
class TestInvestorTradingIntegration:
    """투자자 매매동향 API 통합 테스트"""

    @pytest.fixture
    def broker(self):
        """실제 API 자격 증명으로 broker 생성"""
        return KoreaInvestment()

    def test_samsung_investor_trading(self, broker):
        """삼성전자 투자자 매매동향 조회"""
        # 어제 날짜 (당일은 장 종료 후에만 조회 가능)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        result = broker.fetch_investor_trading_by_stock_daily("005930", yesterday)

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output1' in result
        assert 'output2' in result

    def test_different_market_codes(self, broker):
        """다양한 시장 코드 테스트"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        # KRX (기본)
        result = broker.fetch_investor_trading_by_stock_daily("005930", yesterday, "J")
        assert result['rt_cd'] == '0'
```

---

## 6. 문서 업데이트

### 6.1 CLAUDE.md 업데이트

API 메서드 목록에 추가:
```markdown
- `fetch_investor_trading_by_stock_daily(symbol, date, market_code)` - 종목별 투자자매매동향(일별)
```

### 6.2 CHANGELOG.md 업데이트

```markdown
## [Unreleased]

### Added
- `fetch_investor_trading_by_stock_daily()`: 종목별 투자자매매동향(일별) 조회 API 추가
  - 외국인/기관/개인 순매수 수량 및 금액 조회
  - HTS [0416] 종목별 일별동향과 동일 기능
  - 캐시 및 Rate Limit 래퍼 지원
```
