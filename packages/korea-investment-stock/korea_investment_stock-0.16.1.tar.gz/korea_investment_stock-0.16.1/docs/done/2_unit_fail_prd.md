# PRD: Unit Test 실패 수정

> **프로젝트**: Korea Investment Stock - Unit Test Failures Fix
> **작성일**: 2025-11-07
> **버전**: 1.0
> **관련 브랜치**: feature/remove-mock-mode

---

## 📋 Executive Summary

### 문제 개요
v0.8.0 mock 모드 제거 후 unit test 실행 결과 58개 중 42개 통과, 4개 실패, 2개 에러, 10개 스킵 발생. 실패한 테스트는 모두 기존 코드의 버그로, mock 제거와는 무관함.

### 핵심 이슈
1. **DataFrame 비교 문제**: pandas DataFrame 직접 비교 시 오류
2. **잘못된 테스트 데이터**: 한국 종목을 US 마켓으로 조회
3. **에러 핸들링 누락**: None 반환 시 TypeError 발생
4. **Redis 의존성 누락**: fakeredis 미설치로 테스트 실패

### 수정 범위
- 캐시 통합 테스트 3개 수정
- Redis 관련 테스트 3개 스킵 처리 (옵셔널 의존성)

---

## 🔍 Current State Analysis

### 테스트 실행 결과 (2025-11-07)

```bash
pytest korea_investment_stock -v --tb=short

======================== test session starts =========================
collected 58 items

✅ PASSED: 42/58 (72%)
❌ FAILED: 4/58 (7%)
⚠️ ERROR: 2/58 (3%)
⏭️ SKIPPED: 10/58 (17%)
```

### 1. 실패 테스트 상세 분석

#### ❌ FAILED #1: test_fetch_kospi_symbols_cached

**위치**: `korea_investment_stock/cache/test_cached_integration.py:177`

**오류 내용**:
```python
def test_fetch_kospi_symbols_cached(self):
    result1 = cached_broker.fetch_kospi_symbols()
    result2 = cached_broker.fetch_kospi_symbols()  # Should hit cache
    assert result2 == result1  # ❌ DataFrame comparison error

# ValueError: The truth value of a DataFrame is ambiguous.
# Use a.empty, a.bool(), a.item(), a.any() or a.all().
```

**원인 분석**:
- `fetch_kospi_symbols()` 메서드가 pandas DataFrame 반환
- DataFrame 직접 비교 시 `==` 연산자는 element-wise 비교 반환
- `assert` 문에서 boolean으로 변환 시 ambiguous 오류 발생

**영향도**: 🟡 중간 (캐시 기능은 정상, 테스트 코드만 수정 필요)

**해결 방법**:
```python
# 수정 전
assert result2 == result1

# 수정 후
import pandas as pd
pd.testing.assert_frame_equal(result2, result1)
```

---

#### ❌ FAILED #2: test_different_markets_separate_cache

**위치**: `korea_investment_stock/cache/test_cached_integration.py:189`

**오류 내용**:
```python
def test_different_markets_separate_cache(self):
    result_kr = cached_broker.fetch_price("005930", "KR")  # ✅ 삼성전자
    result_us = cached_broker.fetch_price("005930", "US")  # ❌ 005930은 한국 종목!

# ValueError: Unable to fetch price for symbol '005930' in any US exchange
# market_code 512 (NASDAQ)
# market_code 513 (NYSE)
# market_code 529 (AMEX)
```

**원인 분석**:
- 테스트 데이터 오류: "005930"은 삼성전자 한국 종목 코드
- US 마켓에서 한국 종목 코드를 조회하려 시도
- 당연히 NASDAQ, NYSE, AMEX 어디서도 찾을 수 없음

**영향도**: 🟢 낮음 (테스트 데이터만 수정)

**해결 방법**:
```python
# 수정 전
result_kr = cached_broker.fetch_price("005930", "KR")
result_us = cached_broker.fetch_price("005930", "US")  # ❌ 잘못된 데이터

# 수정 후
result_kr = cached_broker.fetch_price("005930", "KR")  # 삼성전자
result_us = cached_broker.fetch_price("AAPL", "US")    # 애플
```

---

#### ❌ FAILED #3: test_error_response_not_cached

**위치**: `korea_investment_stock/cache/test_cached_integration.py:201`

**오류 내용**:
```python
def test_error_response_not_cached(self):
    result1 = cached_broker.fetch_price("INVALID", "KR")
    # ❌ TypeError: 'NoneType' object is not subscriptable

# 호출 스택:
# cached_korea_investment.py:63  -> result = self.broker.fetch_price(symbol, market)
# korea_investment_stock.py:372  -> symbol_type = self.get_symbol_type(stock_info)
# korea_investment_stock.py:388  -> symbol_type = symbol_info['output']['prdt_clsf_name']
```

**원인 분석**:
1. `fetch_stock_info("INVALID", "KR")` 호출 시 None 반환 (유효하지 않은 종목)
2. `get_symbol_type()` 메서드에서 None 체크 없이 `symbol_info['output']` 접근
3. TypeError 발생으로 테스트 중단

**코드 분석**:
```python
# korea_investment_stock.py:388 (현재 코드)
def get_symbol_type(self, symbol_info):
    symbol_type = symbol_info['output']['prdt_clsf_name']  # ❌ None 체크 없음
    # ...
```

**영향도**: 🔴 높음 (실제 사용자 코드에서도 예외 발생 가능)

**해결 방법**:
```python
# Option 1: get_symbol_type 메서드에 None 체크 추가
def get_symbol_type(self, symbol_info):
    if symbol_info is None:
        return None  # or raise ValueError("Invalid symbol")

    symbol_type = symbol_info['output']['prdt_clsf_name']
    # ...

# Option 2: fetch_price 메서드에서 먼저 체크
def fetch_price(self, symbol, market):
    stock_info = self.fetch_stock_info(symbol, market)
    if stock_info is None:
        return {"rt_cd": "1", "msg1": "Invalid symbol"}

    symbol_type = self.get_symbol_type(stock_info)
    # ...
```

---

#### ❌ FAILED #4: test_redis_connection_error

**위치**: `korea_investment_stock/token_storage/test_token_storage.py:365`

**오류 내용**:
```python
def test_redis_connection_error(self, monkeypatch):
    monkeypatch.setattr('redis.from_url', mock_from_url)
    # ❌ ModuleNotFoundError: No module named 'redis'
```

**원인 분석**:
- `redis`는 옵셔널 의존성 (pyproject.toml의 `[project.optional-dependencies]`)
- 개발 환경에 설치되지 않음
- 테스트가 redis 모듈이 설치되어 있다고 가정

**영향도**: 🟢 낮음 (옵셔널 기능)

**해결 방법**:
```python
# pytest.importorskip 사용
import pytest

@pytest.mark.skipif(not pytest.importorskip("redis"),
                    reason="redis not installed")
def test_redis_connection_error(self, monkeypatch):
    # ...

# 또는 fixture 레벨에서 처리
@pytest.fixture
def redis_client():
    pytest.importorskip("redis")
    # ...
```

---

### 2. 에러 테스트 상세 분석

#### ⚠️ ERROR #1: test_file_to_redis_migration

**위치**: `korea_investment_stock/token_storage/test_token_storage.py:291`

**오류 내용**:
```python
def test_file_to_redis_migration(self, fake_redis, monkeypatch):
    # ❌ fixture 'fake_redis' not found
```

**원인**: fakeredis fixture가 정의되지 않음

**해결 방법**:
```python
# conftest.py에 fixture 추가 또는 테스트 스킵
@pytest.fixture
def fake_redis():
    pytest.importorskip("fakeredis")
    import fakeredis
    return fakeredis.FakeStrictRedis()
```

---

#### ⚠️ ERROR #2: test_custom_key_prefix

**위치**: `korea_investment_stock/token_storage/test_token_storage.py:316`

**오류 내용**:
```python
def test_custom_key_prefix(self, fake_redis, monkeypatch):
    # ❌ fixture 'fake_redis' not found
```

**원인**: 동일 - fakeredis fixture 누락

---

### 3. 스킵된 테스트 (10개)

```
test_fetch_kospi_symbols: @skip("Skipping test_fetch_kospi_symbols")
test_redis_token_storage_*: 7개 (fakeredis 미설치)
test_redis_storage_*: 2개 (fakeredis 미설치)
```

**현황**: 의도적 스킵 또는 옵셔널 의존성으로 정상

---

## 🎯 Proposed Solution

### 1. 수정 우선순위

#### 🔴 Priority 1: 프로덕션 영향 (즉시 수정)
- **test_error_response_not_cached**: None 체크 로직 추가
  - 파일: `korea_investment_stock/korea_investment_stock.py`
  - 영향: 실제 사용자 코드에서도 예외 발생 가능

#### 🟡 Priority 2: 테스트 안정성 (높은 우선순위)
- **test_fetch_kospi_symbols_cached**: DataFrame 비교 수정
  - 파일: `korea_investment_stock/cache/test_cached_integration.py:177`
- **test_different_markets_separate_cache**: 테스트 데이터 수정
  - 파일: `korea_investment_stock/cache/test_cached_integration.py:189`

#### 🟢 Priority 3: 옵셔널 기능 (낮은 우선순위)
- **Redis 관련 테스트 3개**: fakeredis fixture 추가 또는 스킵 처리
  - 파일: `korea_investment_stock/token_storage/test_token_storage.py`

---

### 2. 상세 수정 계획

#### Phase 1: 프로덕션 코드 수정

**파일**: `korea_investment_stock/korea_investment_stock.py`

```python
# Line 388 수정 전
def get_symbol_type(self, symbol_info):
    symbol_type = symbol_info['output']['prdt_clsf_name']

# Line 388 수정 후
def get_symbol_type(self, symbol_info):
    if symbol_info is None:
        raise ValueError("Invalid symbol information")

    if 'output' not in symbol_info or 'prdt_clsf_name' not in symbol_info['output']:
        raise ValueError("Invalid symbol information format")

    symbol_type = symbol_info['output']['prdt_clsf_name']
```

**또는 더 나은 방법** (fetch_price에서 먼저 체크):

```python
# Line 372 수정
def fetch_price(self, symbol: str, market: str) -> Dict[str, Any]:
    stock_info = self.fetch_stock_info(symbol, market)

    # 🆕 None 체크 추가
    if stock_info is None:
        return {
            "rt_cd": "1",
            "msg1": f"Invalid symbol: {symbol}",
            "output": None
        }

    symbol_type = self.get_symbol_type(stock_info)
    # ...
```

---

#### Phase 2: 캐시 통합 테스트 수정

**파일**: `korea_investment_stock/cache/test_cached_integration.py`

**수정 1**: Line 177 (DataFrame 비교)
```python
# 수정 전
def test_fetch_kospi_symbols_cached(self):
    result1 = cached_broker.fetch_kospi_symbols()
    result2 = cached_broker.fetch_kospi_symbols()
    assert result2 == result1  # ❌

# 수정 후
import pandas as pd

def test_fetch_kospi_symbols_cached(self):
    result1 = cached_broker.fetch_kospi_symbols()
    result2 = cached_broker.fetch_kospi_symbols()

    # DataFrame 비교는 pandas.testing 사용
    pd.testing.assert_frame_equal(result2, result1)

    # 캐시 히트 확인
    stats = cached_broker.get_cache_stats()
    assert stats['hits'] == 1
```

**수정 2**: Line 189 (테스트 데이터)
```python
# 수정 전
def test_different_markets_separate_cache(self):
    result_kr = cached_broker.fetch_price("005930", "KR")
    result_us = cached_broker.fetch_price("005930", "US")  # ❌ 잘못된 데이터

# 수정 후
def test_different_markets_separate_cache(self):
    # 각 마켓에 유효한 종목 사용
    result_kr = cached_broker.fetch_price("005930", "KR")  # 삼성전자 (한국)
    result_us = cached_broker.fetch_price("AAPL", "US")    # 애플 (미국)

    # 캐시 키가 다르므로 각각 캐시됨
    stats = cached_broker.get_cache_stats()
    assert stats['total_keys'] == 2
```

**수정 3**: Line 201 (에러 핸들링 테스트)
```python
# 수정 전
def test_error_response_not_cached(self):
    result1 = cached_broker.fetch_price("INVALID", "KR")  # ❌ TypeError

# 수정 후
def test_error_response_not_cached(self):
    # 유효하지 않은 종목 조회 시 에러 응답 반환
    result1 = cached_broker.fetch_price("INVALID", "KR")

    # 에러 응답 확인
    assert result1['rt_cd'] != '0'  # 성공 코드가 아님

    # 에러 응답은 캐시되지 않음
    result2 = cached_broker.fetch_price("INVALID", "KR")
    stats = cached_broker.get_cache_stats()
    assert stats['hits'] == 0  # 캐시 히트 없음
```

---

#### Phase 3: Redis 테스트 스킵 처리

**파일**: `korea_investment_stock/token_storage/test_token_storage.py`

**Option A: conftest.py에 fixture 추가**
```python
# conftest.py (새로 생성)
import pytest

@pytest.fixture
def fake_redis():
    """fakeredis fixture - redis가 설치되지 않으면 테스트 스킵"""
    pytest.importorskip("fakeredis")
    import fakeredis
    return fakeredis.FakeStrictRedis()
```

**Option B: 테스트에 skipif 추가**
```python
import pytest

# Line 291, 316, 365 수정
@pytest.mark.skipif(
    not pytest.importorskip("fakeredis", minversion=None),
    reason="fakeredis not installed"
)
def test_file_to_redis_migration(self, monkeypatch):
    # ...

@pytest.mark.skipif(
    not pytest.importorskip("redis", minversion=None),
    reason="redis not installed"
)
def test_redis_connection_error(self, monkeypatch):
    # ...
```

**권장**: Option A (fixture 사용) - 더 깔끔하고 재사용 가능

---

## ✅ Success Criteria

### 1. 테스트 통과율
- **Before**: 42/58 통과 (72%)
- **Target**: 45/58 통과 (78%) - Priority 1~2 수정 후
- **Ideal**: 55/58 통과 (95%) - 모든 수정 완료 후 (3개 의도적 스킵 제외)

### 2. 기능별 검증
- [x] 캐시 통합 테스트: 12/12 통과
- [x] 에러 핸들링: TypeError 없이 정상 처리
- [x] Redis 테스트: 적절히 스킵 또는 통과

### 3. 프로덕션 안정성
- [x] Invalid symbol 조회 시 예외 발생하지 않음
- [x] None 반환 케이스 모두 처리됨
- [x] 사용자 코드에 영향 없음

---

## ⚠️ Risks & Mitigation

### Risk 1: fetch_price 반환 형식 변경
**위험도**: 🟡 중간
**내용**: None 체크 추가로 반환 형식이 달라질 수 있음

**완화 전략**:
- 에러 케이스도 기존 API 응답 형식 유지 (`{"rt_cd": "1", "msg1": "..."}`)
- 기존 사용자 코드와 호환성 보장
- 단위 테스트로 검증

### Risk 2: pandas.testing import 추가
**위험도**: 🟢 낮음
**내용**: 테스트 코드에 새로운 import 추가

**완화 전략**:
- pandas는 이미 core 의존성
- pandas.testing은 표준 테스트 방법
- 영향 없음

### Risk 3: Redis 테스트 스킵 증가
**위험도**: 🟢 낮음
**내용**: fakeredis 미설치 시 10개 테스트 스킵

**완화 전략**:
- Redis는 옵셔널 기능
- CI/CD에서 fakeredis 설치하여 전체 테스트
- 로컬에서는 스킵 허용

---

## 📊 Testing Strategy

### 1. 수정 전 검증
```bash
# 현재 상태 저장
pytest korea_investment_stock -v --tb=short > test_results_before.txt 2>&1

# 실패 테스트 확인
pytest korea_investment_stock --lf -v
```

### 2. 수정 후 검증
```bash
# Phase 1 후: 프로덕션 코드 수정 검증
pytest korea_investment_stock/test_korea_investment_stock.py -v
pytest korea_investment_stock/cache/test_cached_integration.py::TestCachedKoreaInvestment::test_error_response_not_cached -v

# Phase 2 후: 캐시 테스트 검증
pytest korea_investment_stock/cache/test_cached_integration.py -v

# Phase 3 후: 전체 테스트
pytest korea_investment_stock -v --tb=short > test_results_after.txt 2>&1

# 결과 비교
diff test_results_before.txt test_results_after.txt
```

### 3. 회귀 테스트
```bash
# 전체 테스트 스위트 실행
pytest korea_investment_stock -v

# 캐시 기능 검증
pytest korea_investment_stock/cache/ -v

# 통합 테스트 검증
pytest korea_investment_stock/test_integration_us_stocks.py -v
```

---

## 📚 References

### Python Testing Best Practices
- **pytest documentation**: https://docs.pytest.org/
- **pandas.testing**: https://pandas.pydata.org/docs/reference/api/pandas.testing.assert_frame_equal.html
- **pytest.importorskip**: https://docs.pytest.org/en/stable/how-to/skipping.html

### 관련 이슈
- Issue #55: [v0.8.0] Mock 모드 완전 제거
- PR #56: [v0.8.0] Remove mock mode completely

### 프로젝트 컨텍스트
- Mock 제거 작업은 완료됨
- 이 실패들은 기존 코드의 버그
- Mock 제거와 무관한 독립적 수정

---

## 📂 관련 문서

- **[구현 가이드](2_unit_fail_implementation.md)** - 상세 구현 절차 (작성 예정)
- **[TODO 체크리스트](2_unit_fail_todo.md)** - 단계별 작업 목록 (작성 예정)

---

**작성일**: 2025-11-07
**버전**: 1.0
**상태**: Ready for Implementation
