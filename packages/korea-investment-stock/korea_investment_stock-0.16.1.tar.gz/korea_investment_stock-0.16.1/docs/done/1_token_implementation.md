# 토큰 자동 재발급 구현 가이드

## 개요

API 호출 중 토큰 만료 응답 감지 시 자동으로 토큰을 재발급하고 요청을 재시도하는 기능 구현.

## 구현 파일

| 파일 | 변경 내용 |
|------|-----------|
| `korea_investment_stock/korea_investment_stock.py` | 헬퍼 메서드 추가, API 메서드 수정 |
| `korea_investment_stock/ipo.py` | `fetch_ipo_schedule` 수정 |
| `korea_investment_stock/tests/test_token_refresh.py` | 테스트 파일 신규 생성 |

## 핵심 구현

### 1. 토큰 만료 응답 감지 메서드

**파일:** `korea_investment_stock.py`

```python
def _is_token_expired_response(self, resp_json: dict) -> bool:
    """API 응답에서 토큰 만료 여부 확인

    Note:
        공식 API 문서에는 토큰 만료 에러 메시지가 명시되어 있지 않음.
        실제 운영 환경에서 관측된 메시지: "기간이 만료된 token 입니다."
        (stock-data-batch 프로젝트 로그 참조)

    Args:
        resp_json: API 응답 JSON

    Returns:
        bool: 토큰 만료 에러이면 True
    """
    if resp_json.get('rt_cd') != '0':
        msg = resp_json.get('msg1', '')
        return '기간이 만료된 token' in msg
    return False
```

### 2. 토큰 재발급 요청 래퍼

**파일:** `korea_investment_stock.py`

```python
def _request_with_token_refresh(
    self,
    method: str,
    url: str,
    headers: dict,
    params: dict = None,
    max_retries: int = 1
) -> dict:
    """토큰 만료 시 자동 재발급 후 재시도하는 요청 래퍼

    Args:
        method: HTTP 메서드 ("GET" 또는 "POST")
        url: API URL
        headers: 요청 헤더 (authorization 포함)
        params: 쿼리 파라미터 또는 POST 바디
        max_retries: 토큰 재발급 후 재시도 횟수 (기본 1회)

    Returns:
        dict: API 응답 JSON
    """
    for attempt in range(max_retries + 1):
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params)
        else:
            resp = requests.post(url, headers=headers, json=params)

        resp_json = resp.json()

        # 토큰 만료 에러 감지 및 재발급
        if self._is_token_expired_response(resp_json) and attempt < max_retries:
            logger.info("토큰 만료 감지, 재발급 시도...")
            self.issue_access_token()
            headers["authorization"] = self.access_token
            continue

        return resp_json

    return resp_json
```

### 3. API 메서드 수정

#### fetch_domestic_price

**Before:**
```python
def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> dict:
    # ... headers, params 설정 ...
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()
```

**After:**
```python
def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> dict:
    # ... headers, params 설정 ...
    return self._request_with_token_refresh("GET", url, headers, params)
```

#### fetch_price_detail_oversea

**주의:** 이 메서드는 여러 거래소를 순회하므로 내부 루프에서 처리 필요.

```python
def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> dict:
    # ... 기존 로직 ...
    for exchange_code in exchange_codes:
        params = {"AUTH": "", "EXCD": exchange_code, "SYMB": symbol}

        # 변경: requests.get 대신 래퍼 사용
        resp_json = self._request_with_token_refresh("GET", url, headers, params)

        if resp_json['rt_cd'] != API_RETURN_CODE["SUCCESS"] or resp_json['output']['rsym'] == '':
            continue
        return resp_json
    # ...
```

#### fetch_stock_info / fetch_search_stock_info

동일한 패턴으로 수정:

```python
def fetch_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
    # ... 기존 로직 ...
    for prdt_type_cd in PRDT_TYPE_CD_BY_COUNTRY[country_code]:
        try:
            params = {"PDNO": symbol, "PRDT_TYPE_CD": prdt_type_cd}

            # 변경: requests.get 대신 래퍼 사용
            resp_json = self._request_with_token_refresh("GET", url, headers, params)

            if resp_json['rt_cd'] == API_RETURN_CODE['NO_DATA']:
                continue
            return resp_json
        except Exception as e:
            # ... 기존 에러 처리 ...
```

### 4. IPO 모듈 수정

**파일:** `korea_investment_stock/ipo.py`

IPO 모듈은 별도 함수이므로 KoreaInvestment 클래스의 메서드를 사용하도록 리팩토링하거나, 토큰 재발급 로직을 인자로 전달.

**방안 A: 콜백 함수 전달**

```python
def fetch_ipo_schedule(
    base_url: str,
    access_token: str,
    api_key: str,
    api_secret: str,
    from_date: str = None,
    to_date: str = None,
    symbol: str = "",
    token_refresh_callback: callable = None  # 추가
) -> dict:
    # ... 기존 로직 ...
    resp = requests.get(url, headers=headers, params=params)
    resp_json = resp.json()

    # 토큰 만료 시 콜백 호출
    if token_refresh_callback and _is_token_expired(resp_json):
        new_token = token_refresh_callback()
        headers["authorization"] = new_token
        resp = requests.get(url, headers=headers, params=params)
        resp_json = resp.json()

    return resp_json
```

**방안 B: KoreaInvestment.fetch_ipo_schedule에서 처리** (권장)

```python
# korea_investment_stock.py
def fetch_ipo_schedule(self, from_date=None, to_date=None, symbol="") -> dict:
    # 직접 _request_with_token_refresh 사용
    url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/ipo-schedule"
    headers = {
        "authorization": self.access_token,
        "appKey": self.api_key,
        "appSecret": self.api_secret,
        "tr_id": "CTCA0022R"
    }
    params = {"SYMB": symbol, ...}

    return self._request_with_token_refresh("GET", url, headers, params)
```

## 테스트 구현

**파일:** `korea_investment_stock/tests/test_token_refresh.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class MockResponse:
    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json


class TestTokenExpiredDetection:
    """토큰 만료 응답 감지 테스트"""

    def test_detects_expired_token(self):
        """토큰 만료 메시지 감지"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)

            expired_resp = {"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}
            assert broker._is_token_expired_response(expired_resp) is True

    def test_ignores_other_errors(self):
        """다른 에러는 토큰 만료로 감지하지 않음"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)

            other_error = {"rt_cd": "1", "msg1": "잘못된 종목코드입니다"}
            assert broker._is_token_expired_response(other_error) is False

    def test_success_response_not_expired(self):
        """성공 응답은 만료로 감지하지 않음"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)

            success_resp = {"rt_cd": "0", "output": {}}
            assert broker._is_token_expired_response(success_resp) is False


class TestAutoTokenRefresh:
    """자동 토큰 재발급 테스트"""

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_refreshes_token_on_expiry(self, mock_get):
        """토큰 만료 시 재발급 후 재시도"""
        from korea_investment_stock import KoreaInvestment

        # 첫 번째: 만료 응답, 두 번째: 성공 응답
        mock_get.side_effect = [
            MockResponse({"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}),
            MockResponse({"rt_cd": "0", "output": {"stck_prpr": "70000"}})
        ]

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker.access_token = "Bearer old_token"
            broker.issue_access_token = Mock()
            broker.issue_access_token.side_effect = lambda: setattr(broker, 'access_token', 'Bearer new_token')

            headers = {"authorization": broker.access_token}
            result = broker._request_with_token_refresh("GET", "http://test", headers, {})

            # 토큰 재발급 호출 확인
            broker.issue_access_token.assert_called_once()
            # 최종 결과 확인
            assert result["rt_cd"] == "0"
            assert result["output"]["stck_prpr"] == "70000"

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_no_infinite_retry(self, mock_get):
        """재시도 횟수 제한 (무한 루프 방지)"""
        from korea_investment_stock import KoreaInvestment

        # 계속 만료 응답
        mock_get.return_value = MockResponse({"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"})

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker.access_token = "Bearer token"
            broker.issue_access_token = Mock()

            headers = {"authorization": broker.access_token}
            result = broker._request_with_token_refresh("GET", "http://test", headers, {}, max_retries=1)

            # 재발급은 1회만
            assert broker.issue_access_token.call_count == 1
            # 결과는 여전히 만료 응답
            assert result["rt_cd"] == "1"
```

## 로깅

토큰 재발급 이벤트는 `INFO` 레벨로 로깅:

```python
logger.info("토큰 만료 감지, 재발급 시도...")
```

사용자가 확인하려면:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 하위 호환성

- 기존 API 시그니처 변경 없음
- 성공 시 동일한 응답 반환
- 실패 시 동일한 에러 응답 반환 (재시도 실패 시)
- 사용자 코드 수정 불필요
