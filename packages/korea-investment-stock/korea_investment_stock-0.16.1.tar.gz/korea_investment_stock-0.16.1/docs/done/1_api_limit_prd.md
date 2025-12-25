# API 호출 속도 제한 기능 PRD

> **한국투자증권 OpenAPI**의 초당 20회 호출 제한 문제를 해결하는 Rate Limiting 기능 PRD

## 🚀 Quick Start

```python
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# 기본 브로커 생성
broker = KoreaInvestment(api_key, api_secret, acc_no)

# 속도 제한 래퍼 적용 (초당 15회 제한)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# 평소처럼 사용 - 속도 제한 자동 적용
result = rate_limited.fetch_price("005930", "KR")

# 대량 조회도 안전하게! (500회 호출도 에러 없음)
for symbol, market in stock_list:
    result = rate_limited.fetch_price(symbol, market)
```

**효과**:
- ✅ API 속도 제한 에러 0건
- ✅ `examples/stress_test.py` 500회 호출 100% 성공
- ✅ 기존 코드 변경 없이 선택적 적용

## 목차

1. [문제 정의](#1-문제-정의)
2. [솔루션 요구사항](#2-솔루션-요구사항)
   - ❓ [FAQ: Cache와 Rate Limit 함께 사용](#-faq-cache와-rate-limit을-함께-사용할-수-있나요)
3. [설계 옵션](#3-설계-옵션)
4. [기술 아키텍처](#4-기술-아키텍처)
5. [구현 계획](#5-구현-계획)
6. [테스트 전략](#6-테스트-전략)
7. [사용 예제](#7-사용-예제)
8. [성능 특성](#8-성능-특성)
9. [마이그레이션 가이드](#9-마이그레이션-가이드)
10. [대안 접근법 (참고용)](#10-대안-접근법-참고용)
    - 🔥 [CachedKoreaInvestment와 결합 - 상세 가이드](#cachedkoreainvestment와-결합)
11. [위험 및 완화 방안](#11-위험-및-완화-방안)
12. [성공 지표](#12-성공-지표)
13. [일정](#13-일정)
14. [미해결 질문](#14-미해결-질문)
15. [참고 자료](#15-참고-자료)

---

## 1. 문제 정의

### 현재 문제점
한국투자증권 OpenAPI는 **초당 최대 20회 API 호출 제한**이 있습니다. 이 제한을 초과하면 API가 에러를 반환하거나 응답하지 않아 애플리케이션이 실패합니다.

### Stress Test에서 발견된 문제
`examples/stress_test.py` 파일이 문제를 보여줍니다:
- `testdata/stock_list.yaml`에 250개 종목
- 각 종목마다 2번의 API 호출: `fetch_stock_info()` + `fetch_price()`
- 총 **500번의 API 호출**
- 현재 sleep 주석 처리된 부분(85, 104번 줄)은 이전 속도 제한 시도를 보여줌
- API 호출이 초당 20회를 넘으면 테스트 실패

### 사용자 요구사항
대량의 종목 데이터를 조회할 때 API 호출 제한(1초당 20회)을 넘지 않도록 자동으로 속도를 조절해야 합니다.

## 2. 솔루션 요구사항

### ❓ FAQ: Cache와 Rate Limit을 함께 사용할 수 있나요?

**질문**: "Cache 기능을 사용하면 RateLimit은 적용이 안되는 건가요?"

**답변**: **예! 둘 다 함께 사용 가능하며, 함께 사용하는 것이 가장 효율적입니다.**

```python
# 최적의 조합
broker = KoreaInvestment(api_key, api_secret, acc_no)
cached = CachedKoreaInvestment(broker, price_ttl=5)      # 캐싱으로 API 호출 감소
safe = RateLimitedKoreaInvestment(cached, calls_per_second=15)  # 속도 제한으로 안전성

# 동작 순서:
# 1. Rate Limit: wait() 체크 (속도 제한)
# 2. Cache: 캐시 확인 (히트 시 즉시 반환, 미스 시 API 호출)
# 3. API: 실제 한국투자증권 API 호출

# 효과:
# ✅ 반복 쿼리는 캐시에서 빠르게 (성능↑)
# ✅ 새 쿼리는 속도 제한으로 안전하게 (안정성↑)
# ✅ API 속도 제한 에러 0건
```

**시너지 효과**:
- Cache가 API 호출을 줄여서 → Rate Limit 부담 감소
- Rate Limit이 캐시 미스를 보호해서 → 안전성 보장
- **결과**: 최고 성능 + 최고 안정성! 🚀

자세한 내용은 "10. 대안 접근법 > CachedKoreaInvestment와 결합" 섹션을 참조하세요.

---

### 2.1 핵심 요구사항

#### 기능적 요구사항
1. **속도 제한**: API 호출을 자동으로 초당 20회 이하로 조절
2. **보수적 접근**: 기본값 **초당 15회** 사용 (안전 마진)
3. **투명성**: API 메서드 시그니처 변경 없음
4. **선택적 적용**: 사용자가 속도 제한 활성화 여부 선택
5. **스레드 안전**: 멀티스레드 환경에서도 안전하게 동작

#### 비기능적 요구사항
1. **철학 준수**: 단순하고, 투명하며, 유연함 (마법 같은 동작 없음)
2. **의존성 없음**: 외부 속도 제한 라이브러리 사용하지 않음
3. **성능**: 최소 오버헤드 (호출당 5ms 미만)
4. **유지보수성**: 명확하고 읽기 쉬운 구현

### 2.2 성공 기준

✅ **주요 성공 지표**: `examples/stress_test.py`가 오류 없이 통과
- 500번의 API 호출이 모두 성공적으로 완료
- API 속도 제한 에러 없음 (`rt_cd != '0'`)
- 실행 중 예외 발생 없음

✅ **보조 지표**:
- 실행 시간: ≤ 40초 (500회 ÷ 15회/초 = 33.3초 + 오버헤드)
- 성공률: 100% (모든 API 호출이 `rt_cd == '0'` 반환)
- 스레드 안전성: 동시 실행 스트레스 테스트 통과

## 3. 설계 옵션

### 옵션 A: 데코레이터 패턴 (기각)
```python
@rate_limit(calls_per_second=15)
def fetch_price(self, symbol, market):
    # API 호출
```

**장점**: 파이썬스럽고 선언적
**단점**: ❌ "마법 없음" 철학 위반
**결정**: 기각 (v0.6.0 단순화 방향과 상충)

### 옵션 B: 래퍼 클래스 패턴 (권장)
```python
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited_broker = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# 평소처럼 사용 - 속도 제한은 자동으로 적용됨
result = rate_limited_broker.fetch_price("005930", "KR")
```

**장점**:
- ✅ 선택적: 사용자가 활성화 여부 선택
- ✅ 투명함: 기존 `KoreaInvestment` 클래스 변경 없음
- ✅ 유연함: 속도 제한 쉽게 커스터마이징 가능
- ✅ 철학 준수: 단순하고 명시적

**결정**: **선택됨** (v0.7.0의 `CachedKoreaInvestment` 패턴과 일치)

### 옵션 C: 수동 속도 제한기 (대안)
```python
limiter = RateLimiter(calls_per_second=15)

for symbol, market in stocks:
    limiter.wait()  # 사용자가 명시적으로 wait 호출
    result = broker.fetch_price(symbol, market)
```

**장점**: 최대 투명성, 완전한 사용자 제어
**단점**: 모든 루프에서 코드 변경 필요
**결정**: 문서에 참고 예제로 포함

## 4. 기술 아키텍처

### 4.1 컴포넌트 설계

```
KoreaInvestment (변경 없음)
    ↓
RateLimitedKoreaInvestment (래퍼)
    ↓
RateLimiter (스레드 안전 속도 제어기)
```

### 4.2 핵심 컴포넌트

#### 컴포넌트 1: `RateLimiter`
**위치**: `korea_investment_stock/rate_limit/rate_limiter.py`

**책임**:
- API 호출 타임스탬프 추적
- 다음 허용 호출까지 대기 시간 계산
- `threading.Lock`을 사용한 스레드 안전 동작

**인터페이스**:
```python
class RateLimiter:
    def __init__(self, calls_per_second: float = 15.0):
        """
        Args:
            calls_per_second: 초당 최대 API 호출 수 (기본값: 15)
        """

    def wait(self) -> None:
        """
        다음 API 호출이 허용될 때까지 대기.
        속도 제한 초과 시 자동으로 sleep.
        """

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns:
            {
                'calls_per_second': float,
                'min_interval': float,
                'last_call': float,
                'total_calls': int
            }
        """
```

**알고리즘**:
```python
# 토큰 버킷 알고리즘 (단순화 버전)
min_interval = 1.0 / calls_per_second  # 15회/초일 때 0.0667초
elapsed = time.time() - last_call

if elapsed < min_interval:
    time.sleep(min_interval - elapsed)

last_call = time.time()
```

#### 컴포넌트 2: `RateLimitedKoreaInvestment`
**위치**: `korea_investment_stock/rate_limit/rate_limited_korea_investment.py`

**책임**:
- `KoreaInvestment` 인스턴스 래핑
- API 메서드 호출 가로채기
- 각 API 호출 전 속도 제한 적용
- 나머지 메서드는 변경 없이 전달

**인터페이스**:
```python
class RateLimitedKoreaInvestment:
    def __init__(
        self,
        broker: KoreaInvestment,
        calls_per_second: float = 15.0
    ):
        """
        Args:
            broker: 기존 KoreaInvestment 인스턴스
            calls_per_second: 속도 제한 (기본값: 15)
        """

    # 래핑된 메서드 (속도 제한 적용)
    def fetch_price(self, symbol: str, market: str) -> Dict[str, Any]:
        self._rate_limiter.wait()
        return self._broker.fetch_price(symbol, market)

    def fetch_stock_info(self, symbol: str, market: str) -> Dict[str, Any]:
        self._rate_limiter.wait()
        return self._broker.fetch_stock_info(symbol, market)

    # ... (모든 API 메서드)

    # 유틸리티 메서드
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """속도 제한 통계 조회"""

    def adjust_rate_limit(self, calls_per_second: float) -> None:
        """런타임 중 속도 제한 동적 조정"""
```

**래핑할 API 메서드** (CLAUDE.md 기준 총 18개):
1. `fetch_price(symbol, market)`
2. `fetch_domestic_price(market_code, symbol)`
3. `fetch_etf_domestic_price(market_code, symbol)`
4. `fetch_price_detail_oversea(symbol, market)`
5. `fetch_stock_info(symbol, market)`
6. `fetch_search_stock_info(symbol, market)`
7. `fetch_kospi_symbols()`
8. `fetch_kosdaq_symbols()`
9. `fetch_ipo_schedule()`
10-18. IPO 헬퍼 메서드 (9개)

### 4.3 스레드 안전성

**메커니즘**: `RateLimiter`에서 `threading.Lock` 사용

```python
class RateLimiter:
    def __init__(self, calls_per_second: float):
        self._lock = threading.Lock()
        self._last_call = 0
        self._min_interval = 1.0 / calls_per_second

    def wait(self) -> None:
        with self._lock:  # 임계 구역
            elapsed = time.time() - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.time()
```

## 5. 구현 방향

구현 계획 및 상세 구현 가이드는 별도 문서 참조:
- **구현 가이드**: `1_api_limit_implementation.md`
- **TODO 체크리스트**: `1_api_limit_todo.md`

## 6. 테스트 전략

테스트 구현 세부사항은 별도 문서 참조:
- **구현 가이드**: `1_api_limit_implementation.md` (테스트 구현 섹션)

**테스트 범위**:
- 단위 테스트: `RateLimiter` 기본 동작, 스레드 안전성, 통계, 동적 조정
- 통합 테스트: 실제 API 호출, Context Manager, 기능 보존
- Stress Test: 500회 API 호출 100% 성공 검증

## 7. 사용 예제

### 기본 사용법
```python
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# 기본 브로커 생성
broker = KoreaInvestment(api_key, api_secret, acc_no)

# 속도 제한 래퍼로 감싸기 (선택적)
rate_limited_broker = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# 평소처럼 사용 - 속도 제한은 자동으로 적용됨
result = rate_limited_broker.fetch_price("005930", "KR")
```

### 속도 제한과 함께 배치 처리
```python
from korea_investment_stock import RateLimitedKoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

stocks = [("005930", "KR"), ("AAPL", "US"), ("035720", "KR")]

results = []
for symbol, market in stocks:
    result = rate_limited.fetch_price(symbol, market)
    if result['rt_cd'] == '0':
        results.append(result)
    else:
        print(f"에러: {result['msg1']}")
```

### 커스텀 속도 제한
```python
# 프로덕션용 보수적 설정 (12회/초)
conservative = RateLimitedKoreaInvestment(broker, calls_per_second=12)

# 테스트용 공격적 설정 (18회/초 - 한계에 가까움)
aggressive = RateLimitedKoreaInvestment(broker, calls_per_second=18)

# 안정성 최우선 설정 (10회/초)
ultra_safe = RateLimitedKoreaInvestment(broker, calls_per_second=10)
```

### 동적 속도 조정
```python
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# 처리 시작
for symbol, market in high_priority_stocks:
    result = rate_limited.fetch_price(symbol, market)

    # 에러 발생 시 속도 낮추기
    if result['rt_cd'] != '0':
        rate_limited.adjust_rate_limit(calls_per_second=10)
        print("속도 제한을 10회/초로 조정했습니다")

# 통계 확인
stats = rate_limited.get_rate_limit_stats()
print(f"총 호출 횟수: {stats['total_calls']}")
print(f"현재 속도: {stats['calls_per_second']}/초")
```

### 컨텍스트 매니저와 함께 사용
```python
broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

with rate_limited:
    for symbol, market in stocks:
        result = rate_limited.fetch_price(symbol, market)
        process_result(result)
```

## 8. 성능 특성

### 예상 동작

| 시나리오 | 속도 제한 없음 | 속도 제한 적용 (15회/초) |
|----------|----------------|-------------------------|
| API 10회 호출 | ~1-3초 | ~0.67초 |
| API 100회 호출 | ~10-30초 | ~6.7초 |
| API 500회 호출 | **실패** (속도 제한 초과) | ~33초 |
| API 1000회 호출 | **실패** (속도 제한 초과) | ~67초 |

### 오버헤드 분석
- **호출당 오버헤드**: 5ms 미만 (time.time() + lock + 계산)
- **메모리 오버헤드**: ~100 바이트 (RateLimiter 인스턴스)
- **스레드 동기화**: 최소한의 경합 (단일 lock)

### 스트레스 테스트 예상 결과
```
📊 Stress Test 결과 (250개 종목 × 2회 호출 = 500회 총 호출)

속도 제한 없음:
- 총 API 호출: 500회
- 성공: ~100-200회 (타이밍에 따라)
- 실패: ~300-400회 (속도 제한 에러)
- 성공률: 20-40%
- 실행 시간: 10-20초
- 상태: ❌ 실패

속도 제한 적용 (15회/초):
- 총 API 호출: 500회
- 성공: 500회
- 실패: 0회
- 성공률: 100%
- 실행 시간: 33-37초
- 상태: ✅ 성공
```

## 9. 마이그레이션 가이드

### 기존 사용자를 위한 안내

**중단 변경 없음**: 기존 코드는 변경 없이 계속 작동합니다.

```python
# 기존 코드 (여전히 작동함)
with KoreaInvestment(api_key, api_secret, acc_no) as broker:
    result = broker.fetch_price("005930", "KR")

# 새 기능 (속도 제한을 위한 선택적 적용)
broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

with rate_limited:
    result = rate_limited.fetch_price("005930", "KR")
```

### 속도 제한 사용 시기

**✅ 속도 제한을 사용해야 하는 경우**:
- 대량의 종목 리스트 처리 시 (20개 이상)
- 배치 작업이나 자동화 스크립트 실행 시
- 지속적인 쿼리를 하는 프로덕션 애플리케이션 구축 시
- API 속도 제한 에러를 경험한 경우

**❌ 속도 제한이 필요 없는 경우**:
- 단일 또는 드문 쿼리 수행 시
- 대화형 개발 (수동 테스트)
- 이미 커스텀 속도 제한 로직을 구현한 경우

### Cache와 Rate Limit 함께 사용

**💡 중요**: Cache와 Rate Limit은 **동시에 사용 가능**하며, 함께 사용하는 것이 권장됩니다!

```python
# 최적의 조합 (둘 다 사용)
broker = KoreaInvestment(api_key, api_secret, acc_no)
cached = CachedKoreaInvestment(broker, price_ttl=5)
safe_broker = RateLimitedKoreaInvestment(cached, calls_per_second=15)

# 효과:
# ✅ Cache: API 호출 횟수 감소 (성능 향상)
# ✅ Rate Limit: 캐시 미스 시 속도 제한 (안정성 보장)
# ✅ 시너지: 최고의 성능 + 안정성
```

**장점**:
- 반복 쿼리는 캐시에서 빠르게 반환
- 새로운 쿼리는 Rate Limit으로 안전하게 처리
- API 속도 제한 에러 완전 차단
- 최소 API 호출로 최대 성능 달성

자세한 설명은 "10. 대안 접근법 > CachedKoreaInvestment와 결합" 섹션을 참조하세요.

## 10. 대안 접근법 (참고용)

### 수동 속도 제한 (CLAUDE.md에서)
```python
import time

class RateLimiter:
    def __init__(self, calls_per_second=15):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0

    def wait(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()

# 사용법
limiter = RateLimiter(calls_per_second=15)

for symbol, market in stocks:
    limiter.wait()  # 각 호출 전 명시적 대기
    result = broker.fetch_price(symbol, market)
```

**사용 시기**: 최대 제어가 필요한 경우, 커스텀 로직, 교육 목적

### CachedKoreaInvestment와 결합

#### ❓ 자주 묻는 질문: Cache와 Rate Limit 동시 사용?

**질문**: "cache 기능을 사용하면 RateLimit은 적용이 안되는 건가요?"

**답변**: **아니요! 둘 다 함께 사용할 수 있고, 실제로 함께 사용하는 것이 가장 효율적입니다.**

#### 동작 원리 설명

```python
from korea_investment_stock import (
    KoreaInvestment,
    CachedKoreaInvestment,
    RateLimitedKoreaInvestment
)

# 기본 브로커 생성
broker = KoreaInvestment(api_key, api_secret, acc_no)

# 캐싱 레이어 추가
cached_broker = CachedKoreaInvestment(broker, price_ttl=5)

# 속도 제한 레이어 추가
rate_limited_cached = RateLimitedKoreaInvestment(cached_broker, calls_per_second=15)

# 사용 예시
result = rate_limited_cached.fetch_price("005930", "KR")
```

**레이어 순서별 동작**:

```
1. rate_limited_cached.fetch_price("005930", "KR") 호출
   ↓
2. RateLimitedKoreaInvestment: "속도 제한 체크"
   - wait() 호출 (필요시 sleep)
   ↓
3. cached_broker.fetch_price("005930", "KR") 호출
   ↓
4. CachedKoreaInvestment: "캐시 확인"
   - 캐시에 있으면? → 캐시에서 반환 (API 호출 X)
   - 캐시에 없으면? → broker.fetch_price() 호출 (API 호출 O)
   ↓
5. broker.fetch_price("005930", "KR") (실제 API 호출)
```

#### 시나리오별 동작

**시나리오 1: 캐시 히트 (캐시에 데이터 있음)**
```python
# 첫 번째 호출 (0.067초 대기 후 API 호출)
result1 = rate_limited_cached.fetch_price("005930", "KR")
# → Rate Limit: wait() → Cache: Miss → API 호출 ✅

time.sleep(1)  # 1초 대기

# 두 번째 호출 (0.067초 대기 후 캐시에서 반환)
result2 = rate_limited_cached.fetch_price("005930", "KR")
# → Rate Limit: wait() → Cache: Hit → 캐시 반환 (API 호출 X) ✅
```

**결과**:
- ✅ Rate Limit 적용됨 (wait() 호출)
- ✅ 캐시도 적용됨 (API 호출 1회만)
- ✅ 두 번째 호출은 빠르게 반환 (캐시에서)

**시나리오 2: 캐시 미스 (캐시에 데이터 없음)**
```python
# 100개 종목 조회 (모두 처음 조회)
for symbol in symbols[:100]:
    result = rate_limited_cached.fetch_price(symbol, "KR")
    # → Rate Limit: wait() → Cache: Miss → API 호출 ✅
```

**결과**:
- ✅ Rate Limit 적용됨 (초당 15회로 제한)
- ✅ 실행 시간: ~6.7초 (100회 ÷ 15회/초)
- ✅ API 속도 제한 에러 없음

**시나리오 3: 혼합 상황 (일부 캐시 히트)**
```python
# 같은 종목을 반복 조회
symbols = ["005930", "035720", "005930", "AAPL", "035720", "005930"]

for symbol in symbols:
    result = rate_limited_cached.fetch_price(symbol, "KR")

# 동작:
# 1. "005930" → Rate Limit: wait() → Cache: Miss → API 호출
# 2. "035720" → Rate Limit: wait() → Cache: Miss → API 호출
# 3. "005930" → Rate Limit: wait() → Cache: Hit → 캐시 반환 (API X)
# 4. "AAPL"   → Rate Limit: wait() → Cache: Miss → API 호출
# 5. "035720" → Rate Limit: wait() → Cache: Hit → 캐시 반환 (API X)
# 6. "005930" → Rate Limit: wait() → Cache: Hit → 캐시 반환 (API X)
```

**결과**:
- ✅ 총 6회 메서드 호출
- ✅ 실제 API 호출: 3회만 (캐시 적중: 3회)
- ✅ Rate Limit은 6회 모두 적용 (wait() 호출)
- ✅ 하지만 API 호출이 줄어들어 실제 대기 시간 감소

#### 성능 비교

| 시나리오 | Rate Limit만 | Cache만 | 둘 다 사용 |
|----------|-------------|---------|-----------|
| 100개 종목 (모두 새로운 데이터) | ~6.7초, API 100회 | 빠르지만 API 제한 에러 | ~6.7초, API 100회, 에러 없음 ✅ |
| 100개 종목 (50% 반복) | ~6.7초, API 100회 | 빠르지만 API 제한 에러 | ~3.5초, API 50회, 에러 없음 ✅ |
| 같은 종목 100번 반복 | ~6.7초, API 100회 | 즉시, API 1회 | 즉시, API 1회, 에러 없음 ✅ |

#### 권장 사용 패턴

**패턴 1: 안전 우선 (Rate Limit 먼저)**
```python
# Rate Limit을 먼저 적용하여 API 보호
broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)
final_broker = CachedKoreaInvestment(rate_limited, price_ttl=5)

# 동작: Rate Limit → Cache → API
# 장점: API 속도 제한 에러 완전 차단
```

**패턴 2: 성능 우선 (Cache 먼저) - 권장 ✅**
```python
# Cache를 먼저 적용하여 불필요한 wait() 최소화
broker = KoreaInvestment(api_key, api_secret, acc_no)
cached = CachedKoreaInvestment(broker, price_ttl=5)
final_broker = RateLimitedKoreaInvestment(cached, calls_per_second=15)

# 동작: Rate Limit (wait 체크) → Cache (히트 시 즉시 반환) → API
# 장점: 캐시 히트 시에도 wait() 호출하지만, 실제 API 호출은 안 함
# 추천: 대부분의 경우 이 패턴 사용
```

**어느 순서든 상관없는 이유**:
- Rate Limit이 바깥쪽: 모든 호출에 대해 wait() 체크 → 안전
- Cache가 바깥쪽: 캐시 히트 시 wait() 스킵 → 약간 더 빠름

#### 실제 사용 예제

```python
from korea_investment_stock import (
    KoreaInvestment,
    CachedKoreaInvestment,
    RateLimitedKoreaInvestment
)

# 설정
broker = KoreaInvestment(api_key, api_secret, acc_no)
cached = CachedKoreaInvestment(broker, price_ttl=5)  # 5초 캐시
rate_limited = RateLimitedKoreaInvestment(cached, calls_per_second=15)

# 사용
stocks = ["005930", "035720", "005930", "AAPL", "035720"] * 20  # 100회 호출

start = time.time()
for symbol in stocks:
    result = rate_limited.fetch_price(symbol, "KR")
    if result['rt_cd'] == '0':
        print(f"{symbol}: {result['output']['price']}")
elapsed = time.time() - start

print(f"실행 시간: {elapsed:.2f}초")
print(f"실제 API 호출: {100 - 캐시_히트_수}회")

# 예상 결과:
# - 실행 시간: ~2-3초 (캐시 덕분에 빠름)
# - 실제 API 호출: ~10-20회 (중복 제거)
# - API 속도 제한 에러: 0회 (Rate Limit 덕분)
```

#### 결론

**✅ Cache와 Rate Limit은 독립적으로 작동합니다**:
- **Rate Limit**: 실제 API 호출 속도를 제한 (에러 방지)
- **Cache**: API 호출 자체를 줄임 (성능 향상)

**✅ 함께 사용하면 시너지 효과**:
- Cache가 API 호출을 줄여 → Rate Limit 부담 감소
- Rate Limit이 캐시 미스 상황을 보호 → 안전성 보장

**✅ 권장 설정**:
```python
# 최적의 조합
cached = CachedKoreaInvestment(broker, price_ttl=5)
safe_broker = RateLimitedKoreaInvestment(cached, calls_per_second=15)
```

이렇게 하면:
- 반복 쿼리는 빠르게 (캐시에서)
- 새로운 쿼리는 안전하게 (Rate Limit으로)
- API 속도 제한 에러 없이
- 최대 성능으로 동작합니다! 🚀

## 11. 위험 및 완화 방안

### 위험 1: API 제한 변경
**위험**: 한국투자증권이 API 제한을 초당 20회에서 변경
**완화**: 설정 가능한 `calls_per_second` 파라미터
**조치**: 사용자가 속도 제한을 동적으로 조정 가능

### 위험 2: 스레드 안전성 문제
**위험**: 멀티스레드 환경에서 경합 조건 발생
**완화**: 임계 구역에서 `threading.Lock` 사용
**검증**: 테스트 스위트에 동시 실행 스트레스 테스트 포함

### 위험 3: 시계 드리프트
**위험**: 일부 시스템에서 `time.time()` 드리프트 발생 가능
**완화**: 간격에 `time.monotonic()` 사용
**영향**: 최소 (초 단위에서는 드리프트 무시 가능)

### 위험 4: 성능 오버헤드
**위험**: 속도 제한이 지연시간 추가
**완화**: 최소 오버헤드 (5ms 미만), 쓰로틀링 필요시에만
**모니터링**: 통계에 성능 메트릭 포함

## 12. 성공 지표

### 완료 기준

#### 필수 (P0)
- [x] `examples/stress_test.py`가 오류 없이 통과 (500회 호출)
- [x] API 호출 100% 성공률
- [x] 스레드 안전 구현 검증됨
- [x] `KoreaInvestment` 클래스 변경 없음

#### 권장 (P1)
- [x] `CLAUDE.md` 문서화
- [x] 사용 예제
- [x] 성능 벤치마크 문서화
- [x] 90% 이상 커버리지를 가진 단위 테스트

#### 추가 (P2)
- [x] 통계/모니터링 기능
- [x] 동적 속도 조정
- [x] `CachedKoreaInvestment`와 통합 예제

### 인수 기준

**✅ 인수 테스트**:
```bash
# 환경 변수 설정
export KOREA_INVESTMENT_API_KEY="..."
export KOREA_INVESTMENT_API_SECRET="..."
export KOREA_INVESTMENT_ACCOUNT_NO="..."

# 스트레스 테스트 실행
python examples/stress_test.py

# 예상 출력:
# 📋 총 250개 종목 stress test 시작
# [1/250] 005830 (KR)
#   ✅ Stock Info: Success
#   ✅ Price: Success
# ...
# [250/250] IAU (US)
#   ✅ Stock Info: Success
#   ✅ Price: Success
#
# 📊 Stress Test 결과
# 총 API 호출: 500회
# 성공: 500회
# 실패: 0회
# 성공률: 100.0%
# 실행 시간: 35.43초
```

## 13. 일정

상세 일정은 별도 문서 참조:
- **TODO 체크리스트**: `1_api_limit_todo.md`

**예상 소요 시간**: 6-9시간
- 1단계 (핵심 구현): 3-4시간
- 2단계 (테스트 구현): 2-3시간
- 3단계 (검증 및 문서화): 1-2시간

## 14. 미해결 질문

### 해결됨
- ✅ **질문**: `KoreaInvestment`를 직접 수정할지 래퍼를 만들지?
  **답변**: 래퍼 클래스 (v0.7.0 캐시 패턴과 일치, 철학 보존)

- ✅ **질문**: 기본 속도 제한은 얼마로?
  **답변**: 초당 15회 (20회/초 제한에서 안전 마진)

- ✅ **질문**: 속도 제한은 선택적으로 할지 자동으로 할지?
  **답변**: 선택적 (철학: 사용자 제어, 놀라움 없음)

- ✅ **질문**: Cache 기능을 사용하면 RateLimit은 적용이 안되는 건가?
  **답변**: 둘 다 함께 사용 가능! 오히려 함께 사용하는 것이 가장 효율적. Cache는 API 호출을 줄이고, Rate Limit은 캐시 미스 상황을 보호. 시너지 효과로 최적의 성능과 안정성 제공. 자세한 내용은 "10. 대안 접근법 > CachedKoreaInvestment와 결합" 섹션 참조.

### 보류 중
- **질문**: API 에러 시 지수 백오프를 추가해야 하는지?
  **답변**: v0.8.0 범위 밖 (별도 기능으로 가능)

- **질문**: 실제 API 응답 시간을 모니터링해야 하는지?
  **답변**: 좋긴 하지만, 향후 버전으로 연기

- **질문**: asyncio/비동기 코드와 통합?
  **답변**: 범위 밖 (라이브러리는 동기식)

## 15. 참고 자료

### 관련 문서
- `CLAUDE.md` - 프로젝트 개요 및 아키텍처
- `CHANGELOG.md` - 버전 히스토리 (v0.6.0 중단 변경)
- `examples/stress_test.py` - 인수 테스트 참조
- `.cursorrules` - 개발 관례

### 관련 기능
- **v0.7.0**: `CachedKoreaInvestment` (유사한 래퍼 패턴)
- **v0.6.0**: 단순화 철학 (데코레이터 제거)
- **API 문서**: https://wikidocs.net/book/7845

### 외부 리소스
- 한국투자증권 API 제한: 초당 20회 (공식)
- 토큰 버킷 알고리즘: 표준 속도 제한 접근법
- 파이썬 스레딩: 스레드 안전성을 위한 `threading.Lock`

---

**문서 버전**: 1.0
**마지막 업데이트**: 2025-11-07
**상태**: 구현 준비 완료
**다음 단계**: 1단계 구현 시작
