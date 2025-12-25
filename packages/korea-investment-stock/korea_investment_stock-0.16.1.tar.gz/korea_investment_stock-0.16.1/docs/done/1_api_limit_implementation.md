# API 호출 속도 제한 구현 가이드

> 한국투자증권 OpenAPI 초당 20회 제한 문제 해결을 위한 Rate Limiting 구현

## 아키텍처

```
KoreaInvestment (변경 없음)
    ↓
RateLimitedKoreaInvestment (래퍼)
    ↓
RateLimiter (스레드 안전 속도 제어기)
```

## 구현할 컴포넌트

### 1. RateLimiter 클래스

**파일**: `korea_investment_stock/rate_limit/rate_limiter.py`

**책임**:
- API 호출 타임스탬프 추적
- 다음 허용 호출까지 대기 시간 계산
- 스레드 안전 동작 보장

**구현**:

```python
import time
import threading
from typing import Dict, Any


class RateLimiter:
    """
    API 호출 속도 제한을 위한 스레드 안전 Rate Limiter

    토큰 버킷 알고리즘 기반 단순 구현
    """

    def __init__(self, calls_per_second: float = 15.0):
        """
        Args:
            calls_per_second: 초당 최대 API 호출 수 (기본값: 15)
        """
        if calls_per_second <= 0:
            raise ValueError("calls_per_second must be positive")

        self._calls_per_second = calls_per_second
        self._min_interval = 1.0 / calls_per_second
        self._last_call = 0.0
        self._total_calls = 0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """
        다음 API 호출이 허용될 때까지 대기

        속도 제한을 초과하면 자동으로 sleep
        """
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self._last_call

            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                time.sleep(sleep_time)
                current_time = time.time()

            self._last_call = current_time
            self._total_calls += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        속도 제한 통계 반환

        Returns:
            {
                'calls_per_second': float,
                'min_interval': float,
                'last_call': float,
                'total_calls': int
            }
        """
        with self._lock:
            return {
                'calls_per_second': self._calls_per_second,
                'min_interval': self._min_interval,
                'last_call': self._last_call,
                'total_calls': self._total_calls
            }

    def adjust_rate_limit(self, calls_per_second: float) -> None:
        """
        런타임 중 속도 제한 동적 조정

        Args:
            calls_per_second: 새로운 초당 호출 수
        """
        if calls_per_second <= 0:
            raise ValueError("calls_per_second must be positive")

        with self._lock:
            self._calls_per_second = calls_per_second
            self._min_interval = 1.0 / calls_per_second
```

**핵심 알고리즘**:
```python
# 토큰 버킷 알고리즘 (단순화)
min_interval = 1.0 / calls_per_second  # 15회/초일 때 0.0667초
elapsed = time.time() - last_call

if elapsed < min_interval:
    time.sleep(min_interval - elapsed)

last_call = time.time()
```

### 2. RateLimitedKoreaInvestment 래퍼

**파일**: `korea_investment_stock/rate_limit/rate_limited_korea_investment.py`

**책임**:
- `KoreaInvestment` 인스턴스 래핑
- API 메서드 호출 가로채기
- 각 API 호출 전 속도 제한 적용

**구현**:

```python
from typing import Dict, Any, Optional
from korea_investment_stock import KoreaInvestment
from .rate_limiter import RateLimiter


class RateLimitedKoreaInvestment:
    """
    속도 제한이 적용된 KoreaInvestment 래퍼

    기존 KoreaInvestment 객체를 래핑하여 모든 API 호출에
    자동으로 속도 제한을 적용합니다.
    """

    def __init__(
        self,
        broker: KoreaInvestment,
        calls_per_second: float = 15.0
    ):
        """
        Args:
            broker: 기존 KoreaInvestment 인스턴스
            calls_per_second: 속도 제한 (기본값: 15회/초)
        """
        self._broker = broker
        self._rate_limiter = RateLimiter(calls_per_second)

    # === Context Manager 지원 ===
    def __enter__(self):
        self._broker.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._broker.__exit__(exc_type, exc_val, exc_tb)

    # === 래핑된 API 메서드 (속도 제한 적용) ===

    def fetch_price(self, symbol: str, market: str) -> Dict[str, Any]:
        """속도 제한이 적용된 가격 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_price(symbol, market)

    def fetch_domestic_price(self, market_code: str, symbol: str) -> Dict[str, Any]:
        """속도 제한이 적용된 국내 주식 가격 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_domestic_price(market_code, symbol)

    def fetch_etf_domestic_price(self, market_code: str, symbol: str) -> Dict[str, Any]:
        """속도 제한이 적용된 ETF 가격 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_etf_domestic_price(market_code, symbol)

    def fetch_price_detail_oversea(self, symbol: str, market: str) -> Dict[str, Any]:
        """속도 제한이 적용된 해외 주식 가격 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_price_detail_oversea(symbol, market)

    def fetch_stock_info(self, symbol: str, market: str) -> Dict[str, Any]:
        """속도 제한이 적용된 종목 정보 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_stock_info(symbol, market)

    def fetch_search_stock_info(self, symbol: str, market: str) -> Dict[str, Any]:
        """속도 제한이 적용된 종목 검색"""
        self._rate_limiter.wait()
        return self._broker.fetch_search_stock_info(symbol, market)

    def fetch_kospi_symbols(self) -> Dict[str, Any]:
        """속도 제한이 적용된 KOSPI 종목 리스트 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_kospi_symbols()

    def fetch_kosdaq_symbols(self) -> Dict[str, Any]:
        """속도 제한이 적용된 KOSDAQ 종목 리스트 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_kosdaq_symbols()

    def fetch_ipo_schedule(self) -> Dict[str, Any]:
        """속도 제한이 적용된 IPO 일정 조회"""
        self._rate_limiter.wait()
        return self._broker.fetch_ipo_schedule()

    # IPO 헬퍼 메서드들 (9개)
    def get_ipo_schedule_details(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_ipo_schedule_details(*args, **kwargs)

    def get_upcoming_ipos(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_upcoming_ipos(*args, **kwargs)

    def get_recent_ipos(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_recent_ipos(*args, **kwargs)

    def get_ipo_by_company(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_ipo_by_company(*args, **kwargs)

    def get_ipo_by_date_range(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_ipo_by_date_range(*args, **kwargs)

    def get_ipo_statistics(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_ipo_statistics(*args, **kwargs)

    def filter_ipos_by_market(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.filter_ipos_by_market(*args, **kwargs)

    def get_ipo_calendar(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.get_ipo_calendar(*args, **kwargs)

    def format_ipo_schedule(self, *args, **kwargs):
        self._rate_limiter.wait()
        return self._broker.format_ipo_schedule(*args, **kwargs)

    # === 유틸리티 메서드 ===

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """속도 제한 통계 조회"""
        return self._rate_limiter.get_stats()

    def adjust_rate_limit(self, calls_per_second: float) -> None:
        """런타임 중 속도 제한 동적 조정"""
        self._rate_limiter.adjust_rate_limit(calls_per_second)
```

### 3. 패키지 초기화 파일

**파일**: `korea_investment_stock/rate_limit/__init__.py`

```python
"""
Rate Limiting 모듈

한국투자증권 OpenAPI의 초당 20회 호출 제한을 관리하기 위한
속도 제한 기능을 제공합니다.
"""

from .rate_limiter import RateLimiter
from .rate_limited_korea_investment import RateLimitedKoreaInvestment

__all__ = [
    'RateLimiter',
    'RateLimitedKoreaInvestment',
]
```

### 4. 메인 패키지 업데이트

**파일**: `korea_investment_stock/__init__.py`

기존 내용에 추가:

```python
# Rate Limiting (v0.8.0)
from .rate_limit import RateLimiter, RateLimitedKoreaInvestment

__all__ = [
    # ... 기존 exports
    'RateLimiter',
    'RateLimitedKoreaInvestment',
]
```

## 테스트 구현

### 1. RateLimiter 단위 테스트

**파일**: `korea_investment_stock/rate_limit/test_rate_limiter.py`

```python
import time
import threading
import pytest
from .rate_limiter import RateLimiter


def test_rate_limiter_basic():
    """기본 속도 제한 테스트"""
    limiter = RateLimiter(calls_per_second=10)

    start = time.time()
    for _ in range(20):
        limiter.wait()
    elapsed = time.time() - start

    # 10회/초로 20번 호출하면 약 2초 소요
    assert 1.8 <= elapsed <= 2.2


def test_rate_limiter_thread_safe():
    """멀티스레드 안전성 테스트"""
    limiter = RateLimiter(calls_per_second=10)
    results = []

    def worker():
        for _ in range(10):
            limiter.wait()
            results.append(time.time())

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 호출이 적절히 간격이 있는지 검증
    assert len(results) == 30

    # 시간순 정렬 후 간격 확인
    results.sort()
    intervals = [results[i+1] - results[i] for i in range(len(results)-1)]
    # 0.1초 간격 (허용 오차 10%)
    assert all(interval >= 0.09 for interval in intervals)


def test_rate_limiter_stats():
    """통계 정보 테스트"""
    limiter = RateLimiter(calls_per_second=15)

    for _ in range(5):
        limiter.wait()

    stats = limiter.get_stats()
    assert stats['calls_per_second'] == 15
    assert stats['total_calls'] == 5
    assert stats['min_interval'] == pytest.approx(1.0 / 15)


def test_rate_limiter_adjust():
    """동적 속도 조정 테스트"""
    limiter = RateLimiter(calls_per_second=10)

    # 초기 설정 확인
    stats = limiter.get_stats()
    assert stats['calls_per_second'] == 10

    # 속도 조정
    limiter.adjust_rate_limit(calls_per_second=20)

    # 변경 확인
    stats = limiter.get_stats()
    assert stats['calls_per_second'] == 20
    assert stats['min_interval'] == pytest.approx(1.0 / 20)


def test_rate_limiter_invalid_input():
    """잘못된 입력 테스트"""
    with pytest.raises(ValueError):
        RateLimiter(calls_per_second=0)

    with pytest.raises(ValueError):
        RateLimiter(calls_per_second=-1)
```

### 2. RateLimitedKoreaInvestment 통합 테스트

**파일**: `korea_investment_stock/rate_limit/test_rate_limited_integration.py`

```python
import os
import time
import pytest
from korea_investment_stock import KoreaInvestment
from .rate_limited_korea_investment import RateLimitedKoreaInvestment


@pytest.fixture
def credentials():
    """환경 변수에서 API 인증 정보 로드"""
    api_key = os.environ.get('KOREA_INVESTMENT_API_KEY')
    api_secret = os.environ.get('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.environ.get('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        pytest.skip("API credentials not found in environment variables")

    return api_key, api_secret, acc_no


def test_rate_limited_basic(credentials):
    """기본 속도 제한 통합 테스트"""
    api_key, api_secret, acc_no = credentials

    broker = KoreaInvestment(api_key, api_secret, acc_no)
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # 30번 API 호출 (약 2초 소요 예상)
    start = time.time()
    test_stocks = [
        ("005930", "KR"),  # 삼성전자
        ("035720", "KR"),  # 카카오
        ("AAPL", "US"),    # Apple
    ]

    for _ in range(10):
        for symbol, market in test_stocks:
            result = rate_limited.fetch_price(symbol, market)
            assert result['rt_cd'] == '0', f"API 호출 실패: {result.get('msg1', 'Unknown error')}"

    elapsed = time.time() - start

    # 30회 호출, 15회/초 = 2초 (허용 오차 포함)
    assert 1.8 <= elapsed <= 2.5


def test_rate_limited_context_manager(credentials):
    """컨텍스트 매니저 테스트"""
    api_key, api_secret, acc_no = credentials

    broker = KoreaInvestment(api_key, api_secret, acc_no)
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    with rate_limited:
        result = rate_limited.fetch_price("005930", "KR")
        assert result['rt_cd'] == '0'


def test_rate_limited_preserves_functionality(credentials):
    """래퍼가 모든 API 기능을 보존하는지 테스트"""
    api_key, api_secret, acc_no = credentials

    broker = KoreaInvestment(api_key, api_secret, acc_no)
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # 다양한 API 메서드 테스트
    result = rate_limited.fetch_price("005930", "KR")
    assert result['rt_cd'] == '0'

    result = rate_limited.fetch_stock_info("AAPL", "US")
    assert result['rt_cd'] == '0'

    result = rate_limited.fetch_kospi_symbols()
    assert result['rt_cd'] == '0'


def test_rate_limited_stats(credentials):
    """통계 조회 테스트"""
    api_key, api_secret, acc_no = credentials

    broker = KoreaInvestment(api_key, api_secret, acc_no)
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # 몇 번 호출
    for _ in range(3):
        rate_limited.fetch_price("005930", "KR")

    # 통계 확인
    stats = rate_limited.get_rate_limit_stats()
    assert stats['calls_per_second'] == 15
    assert stats['total_calls'] == 3
```

### 3. Stress Test 업데이트

**파일**: `examples/stress_test.py` (수정)

기존 코드에서 다음과 같이 변경:

```python
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# ... (기존 코드)

def run_stress_test():
    # ... (환경 변수 로드)

    # 기존: with KoreaInvestment(...) as broker:
    # 변경:
    broker = KoreaInvestment(api_key, api_secret, acc_no)
    rate_limited_broker = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    with rate_limited_broker:
        for i, (symbol, market) in enumerate(stock_list, 1):
            # ... (기존 로직, rate_limited_broker 사용)
```

## 파일 구조

```
korea_investment_stock/
├── __init__.py                          # RateLimitedKoreaInvestment export 추가
├── korea_investment_stock.py
│
└── rate_limit/                          # 새로 생성
    ├── __init__.py                      # 모듈 exports
    ├── rate_limiter.py                  # RateLimiter 클래스
    ├── rate_limited_korea_investment.py # RateLimitedKoreaInvestment 래퍼
    ├── test_rate_limiter.py             # 단위 테스트
    └── test_rate_limited_integration.py # 통합 테스트

examples/
└── stress_test.py                       # 업데이트 필요
```

## 성공 기준

1. **단위 테스트 통과**
   - `test_rate_limiter.py` 모든 테스트 통과
   - 스레드 안전성 검증

2. **통합 테스트 통과**
   - `test_rate_limited_integration.py` 모든 테스트 통과
   - 실제 API 호출 정상 동작

3. **Stress Test 통과**
   - `examples/stress_test.py` 500회 호출 100% 성공
   - API 속도 제한 에러 0건
   - 실행 시간: 33-40초

## 구현 시 주의사항

1. **스레드 안전성**
   - `threading.Lock` 사용
   - 임계 구역 최소화

2. **성능**
   - 호출당 오버헤드 5ms 미만 유지
   - Lock 경합 최소화

3. **호환성**
   - 기존 `KoreaInvestment` 클래스 변경 없음
   - 선택적 적용 (opt-in)
   - 모든 API 메서드 래핑

4. **에러 처리**
   - 잘못된 `calls_per_second` 입력 검증
   - API 에러는 그대로 전달 (래핑만 담당)
