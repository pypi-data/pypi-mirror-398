# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Korea Investment Stock is a **pure Python wrapper** for the Korea Investment Securities OpenAPI. This library focuses on providing direct, transparent access to the API without abstraction layers.

**Philosophy**: Simple, transparent, and flexible - let users implement features their way.

**Key Capabilities:**
- Domestic (KR) and US stock price/info queries
- Stock information and search
- IPO schedule lookup
- Unified interface for mixed KR/US stock queries via `fetch_price(symbol, market)`
- Context manager support for resource cleanup

## Development Commands

### Environment Setup

```bash
# Create and activate virtual environment (.venv is required)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install package in editable mode (uses pyproject.toml, NOT requirements.txt)
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run unit tests only (no Docker required)
pytest -m "not integration"

# Run integration tests only (Docker required)
pytest -m integration

# Run specific test file
pytest korea_investment_stock/tests/test_korea_investment_stock.py

# Run with verbose output
pytest -v

# Run API integration tests (requires API credentials)
pytest korea_investment_stock/tests/test_integration_us_stocks.py -v
pytest korea_investment_stock/tests/test_ipo_integration.py -v

# Run Redis integration tests (requires Docker)
pytest korea_investment_stock/tests/test_redis_integration.py -v
```

### Running Examples

```bash
# Always activate virtual environment first
source .venv/bin/activate

# Run examples
python examples/basic_example.py
python examples/ipo_schedule_example.py
python examples/us_stock_price_example.py
```

### Package Management

```bash
# Build distribution packages
python -m build

# Upload to PyPI (maintainers only)
./upload.sh
```

## Configuration

**NEW in v1.1.0**: Multiple configuration methods with 5-level priority.

### Configuration Priority (Highest to Lowest)

1. **Constructor parameters** - Direct values in code
2. **Config object** - `Config` instance passed to constructor
3. **config_file parameter** - Path to YAML file
4. **Environment variables** - `KOREA_INVESTMENT_*` env vars
5. **Default config file** - `~/.config/kis/config.yaml`

### Method 1: Constructor Parameters (Existing)

```python
broker = KoreaInvestment(
    api_key="your-api-key",
    api_secret="your-api-secret",
    acc_no="12345678-01"
)
```

### Method 2: Environment Variables Only

Set in shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export KOREA_INVESTMENT_API_KEY="your-api-key"
export KOREA_INVESTMENT_API_SECRET="your-api-secret"
export KOREA_INVESTMENT_ACCOUNT_NO="12345678-01"
```

Then initialize without parameters:

```python
broker = KoreaInvestment()  # Auto-detects from env vars
```

### Method 3: Config Object (NEW v1.0.0)

```python
from korea_investment_stock import Config, KoreaInvestment

# Create config from env vars
config = Config.from_env()

# Or from YAML file
config = Config.from_yaml("~/.config/kis/config.yaml")

# Use config object
broker = KoreaInvestment(config=config)
```

### Method 4: config_file Parameter (NEW v1.1.0)

```python
broker = KoreaInvestment(config_file="./my_config.yaml")
```

### Method 5: Default Config File (NEW v1.1.0)

Place config at `~/.config/kis/config.yaml`:

```yaml
api_key: your-api-key
api_secret: your-api-secret
acc_no: "12345678-01"
token_storage_type: file
token_file: ~/.cache/kis/token.key
```

Then initialize without any parameters:

```python
broker = KoreaInvestment()  # Auto-loads from default path
```

### Mixed Usage (Partial Override)

```python
# Config object + constructor override
config = Config.from_yaml("~/.config/kis/config.yaml")
broker = KoreaInvestment(
    config=config,
    api_key="override-key"  # This overrides config's api_key
)
```

### Environment Variable Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `KOREA_INVESTMENT_API_KEY` | API Key | Yes |
| `KOREA_INVESTMENT_API_SECRET` | API Secret | Yes |
| `KOREA_INVESTMENT_ACCOUNT_NO` | Account (8-2 format) | Yes |
| `KOREA_INVESTMENT_TOKEN_STORAGE` | "file" or "redis" | No |
| `KOREA_INVESTMENT_TOKEN_FILE` | Token file path | No |
| `KOREA_INVESTMENT_REDIS_URL` | Redis URL | No |
| `KOREA_INVESTMENT_REDIS_PASSWORD` | Redis password | No |

**Naming Convention:**
- Always use `KOREA_INVESTMENT_` prefix
- Account number is `ACCOUNT_NO` (not `ACC_NO`)
- All uppercase with underscore separators

## Architecture Overview

### Simplified Component Flow

```
User API Call
  ↓
KoreaInvestment.fetch_price(symbol, market)
  ↓
HTTP Request to Korea Investment API
  ↓
Return raw API response
```

**That's it.** No decorators, no caching, no rate limiting, no magic.

### Core Module

**`korea_investment_stock/korea_investment_stock.py`** - Main class (1,011 lines)
- `KoreaInvestment`: Primary API interface
- Context manager pattern (`__enter__`, `__exit__`)
- Token management (`issue_access_token()`)
- Public API methods (18 total):
  - `fetch_price(symbol, market)` - Unified KR/US price query
  - `fetch_domestic_price(market_code, symbol)` - KR stocks
  - `fetch_etf_domestic_price(market_code, symbol)` - KR ETFs
  - `fetch_price_detail_oversea(symbol, country_code)` - Overseas stocks (US/HK/JP/CN/VN)
  - `fetch_stock_info(symbol, country_code)` - Stock information
  - `fetch_search_stock_info(symbol, country_code)` - Stock search (국내주식 전용, KR만 지원)
  - `fetch_kospi_symbols()` - KOSPI symbol list
  - `fetch_kosdaq_symbols()` - KOSDAQ symbol list
  - `fetch_ipo_schedule()` - IPO schedule
  - `fetch_investor_trading_by_stock_daily(symbol, date, market_code)` - 종목별 투자자매매동향(일별)
  - IPO helper methods (9 total)

### Package Structure

```
korea_investment_stock/
├── __init__.py                          # Module exports
├── korea_investment_stock.py            # Main KoreaInvestment class
├── test_korea_investment_stock.py       # Main class tests
├── test_integration_us_stocks.py        # Integration tests
│
├── cache/                               # Cache module
│   ├── __init__.py                      # Cache exports
│   ├── cache_manager.py                 # CacheManager, CacheEntry
│   ├── cached_korea_investment.py       # CachedKoreaInvestment wrapper
│   ├── test_cache_manager.py            # Cache unit tests
│   └── test_cached_integration.py       # Cache integration tests
│
└── token_storage/                       # Token storage module
    ├── __init__.py                      # Token storage exports
    ├── token_storage.py                 # FileTokenStorage, RedisTokenStorage
    └── test_token_storage.py            # Token storage tests
```

**Dependencies:** `requests`, `pandas` (minimal)

**Note:** Tests are co-located with implementation files for better maintainability.

## Code Style & Conventions

**From `.cursorrules`:**

1. **Python Version**: 3.11+ (uses `zoneinfo`, modern type hints)
2. **Type Hints**: Required for all public methods
3. **Comments**: Prefer Korean for domain-specific comments
4. **Error Messages**: Korean for user-facing messages
5. **Dependency Management**: Use `pyproject.toml` only (no `requirements.txt`)

## Common Development Patterns

### Adding a New API Method

1. Define method in `KoreaInvestment` class
2. **No decorators** - just pure API calls
3. Add tests in `korea_investment_stock/tests/test_korea_investment_stock.py`

```python
def fetch_new_data(self, symbol: str) -> Dict[str, Any]:
    """
    새로운 데이터 조회

    Args:
        symbol: 종목 코드

    Returns:
        API 응답 딕셔너리
    """
    url = f"{self.base_url}/endpoint"
    headers = {
        "authorization": self.access_token,
        "appkey": self.api_key,
        "appsecret": self.api_secret,
        "tr_id": "TRANSACTION_ID"
    }
    params = {"symbol": symbol}

    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

### Error Handling Pattern

API returns error codes in response:
```python
result = broker.fetch_price("005930", "KR")

if result['rt_cd'] == '0':
    # Success
    price = result['output1']['stck_prpr']
else:
    # Error
    print(f"Error: {result['msg1']}")
```

Users should implement their own retry logic:
```python
import time

def fetch_with_retry(broker, symbol, market, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = broker.fetch_price(symbol, market)
            if result['rt_cd'] == '0':
                return result
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

### Working with US Stocks

US stock query features:
- Exchange auto-detection: NASDAQ → NYSE → AMEX
- Symbol format: Plain ticker (e.g., "AAPL", not "AAPL.US")
- Additional fields: PER, PBR, EPS, BPS included in response

Example:
```python
with KoreaInvestment(api_key, api_secret, acc_no) as broker:
    result = broker.fetch_price("AAPL", "US")

    if result['rt_cd'] == '0':
        output = result['output']
        print(f"Price: ${output['last']}")
        print(f"PER: {output['perx']}")
```

### API Response Fields Reference

**국내 주식 (KR)** - `fetch_price(symbol, "KR")` 주요 필드:
| 필드 | API 키 | 설명 |
|------|--------|------|
| 현재가 | `stck_prpr` | 주식 현재가 |
| 전일대비 | `prdy_vrss` | 전일 대비 가격 변동 |
| 등락률 | `prdy_ctrt` | 전일 대비율 (%) |
| 시가 | `stck_oprc` | 시가 |
| 고가 | `stck_hgpr` | 고가 |
| 저가 | `stck_lwpr` | 저가 |
| 거래량 | `acml_vol` | 누적 거래량 |
| 시가총액 | `hts_avls` | HTS 시가총액 (억원) |

**해외 주식 (US)** - `fetch_price(symbol, "US")` 주요 필드:
| 필드 | API 키 | 설명 |
|------|--------|------|
| 현재가 | `last` | 현재가 |
| 시가 | `open` | 시가 |
| 고가 | `high` | 고가 |
| 저가 | `low` | 저가 |
| 거래량 | `tvol` | 거래량 |
| 시가총액 | `tomv` | 시가총액 |
| 상장주수 | `shar` | 상장주수 |
| 전일대비 | `t_xdif` | 전일 대비 |
| 등락률 | `t_xrat` | 등락률 (%) |
| PER | `perx` | 주가수익비율 |
| PBR | `pbrx` | 주가순자산비율 |
| EPS | `epsx` | 주당순이익 |
| BPS | `bpsx` | 주당순자산 |

## Testing Strategy

### Test Markers

pytest markers로 테스트 유형 구분:

```bash
# 단위 테스트만 (Docker 불필요)
pytest -m "not integration"

# 통합 테스트만 (Docker 필요)
pytest -m integration

# 전체 테스트
pytest
```

### Test Organization

- **Unit tests**: `test_korea_investment_stock.py` - 기본 API 테스트
- **API Integration tests** (API 자격 증명 필요):
  - `test_integration_us_stocks.py` - US stock queries
  - `test_ipo_integration.py` - IPO schedule
- **Redis Integration tests** (Docker 필요):
  - `tests/test_redis_integration.py` - Redis testcontainers 테스트
- **Feature tests**: `test_ipo_schedule.py` - IPO helpers

### Running API Integration Tests

API 통합 테스트는 유효한 API 자격 증명이 필요합니다:

```bash
# Set credentials in environment
export KOREA_INVESTMENT_API_KEY="..."
export KOREA_INVESTMENT_API_SECRET="..."
export KOREA_INVESTMENT_ACCOUNT_NO="..."

# Run API integration tests
pytest korea_investment_stock/tests/test_integration_us_stocks.py -v
pytest korea_investment_stock/tests/test_ipo_integration.py -v
```

### Running Redis Integration Tests (Testcontainers)

Redis 통합 테스트는 Docker가 필요합니다:

```bash
# Docker 실행 상태 확인 후 테스트 실행
pytest -m integration -v

# 결과 예시:
# test_redis_integration.py::TestRedisTokenStorageIntegration::test_save_and_load PASSED
# test_redis_integration.py::TestRedisTokenStorageIntegration::test_connection_pool PASSED
# test_redis_integration.py::TestRedisTokenStorageIntegration::test_ttl_actual_expiry PASSED
# ...
```

**Testcontainers 특징**:
- 실제 Redis Docker 컨테이너 사용
- 세션 단위 컨테이너 재사용 (성능 최적화)
- Docker 미설치 시 자동 스킵
- 테스트 격리 (각 테스트 전 FLUSHDB)

## Important Files

- **`pyproject.toml`**: Package metadata, dependencies, build config
- **`.cursorrules`**: Development conventions (env vars, virtual env, naming)
- **`CHANGELOG.md`**: Version history and release notes (v0.6.0 = breaking changes)
- **`examples/`**: Usage examples:
  - `basic_example.py` - Getting started
  - `ipo_schedule_example.py` - IPO queries
  - `us_stock_price_example.py` - US stock queries

## API Rate Limiting

**User Responsibility**: You must implement your own rate limiting.

Korea Investment Securities API limits:
- **Official**: 20 requests/second
- **Recommended**: 15 requests/second (conservative)

Simple rate limiting example:
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

# Usage
limiter = RateLimiter(calls_per_second=15)

for symbol, market in stocks:
    limiter.wait()
    result = broker.fetch_price(symbol, market)
```

## Known Limitations

1. **IPO data**: Reference only (from 예탁원)
2. **Order functionality**: Not yet implemented (planned)
3. **WebSocket**: Not included in this library
4. **No built-in rate limiting**: Users must implement
5. **No built-in caching**: Users must implement
6. **No automatic retry**: Users must implement

## Git Commit Message Guidelines

Follow conventional commit format:
- `[feat]`: New feature
- `[fix]`: Bug fix
- `[chore]`: Maintenance (docs, CI, etc.)
- `[refactor]`: Code restructuring
- `[test]`: Test additions/changes

Example: `[feat] Add US stock PER/PBR data to fetch_price`

## GitHub Actions Workflows

- **`label-merge-conflict.yml`**: Auto-labels PRs with merge conflicts
- Additional workflows may be present for CI/CD

## Context Manager Pattern

Always use context manager for proper resource cleanup:

```python
# ✅ Good: Automatic cleanup
with KoreaInvestment(api_key, api_secret, acc_no) as broker:
    result = broker.fetch_price("005930", "KR")

# ❌ Bad: Manual cleanup required
broker = KoreaInvestment(api_key, api_secret, acc_no)
result = broker.fetch_price("005930", "KR")
broker.shutdown()  # Must call manually
```

## Master File Caching

**NEW**: `fetch_kospi_symbols()` and `fetch_kosdaq_symbols()` methods now include file-based caching to prevent unnecessary re-downloads of master ZIP files.

### How It Works

Master files (종목 코드 리스트) are cached locally and reused if:
- File exists in current directory
- File age is within TTL (default: 1 week = 168 hours)
- `force_download=False` (default)

### Basic Usage (Automatic Caching)

```python
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)

# First call - downloads ZIP file (~2-5 seconds)
df = broker.fetch_kospi_symbols()

# Second call - uses cached file (~0.1 seconds)
df = broker.fetch_kospi_symbols()
```

### Custom TTL

```python
# Cache for 1 day (24 hours)
df = broker.fetch_kospi_symbols(ttl_hours=24)

# Cache for 1 hour (for testing/development)
df = broker.fetch_kosdaq_symbols(ttl_hours=1)
```

### Force Download

```python
# Ignore cache and always download fresh data
df = broker.fetch_kospi_symbols(force_download=True)
```

### Cache Logging

```python
import logging

# Enable INFO logging to see cache hits/downloads
logging.basicConfig(level=logging.INFO)

broker = KoreaInvestment(api_key, api_secret, acc_no)

# First call
df = broker.fetch_kospi_symbols()
# LOG: INFO - 다운로드 중: https://...kospi_code.mst.zip -> /path/kospi_code.mst.zip

# Second call (within 1 week)
df = broker.fetch_kospi_symbols()
# LOG: INFO - 캐시 사용: /path/kospi_code.mst.zip (age: 0.5h, ttl: 168h)
```

### Performance Benefits

| Scenario | Without Cache | With Cache | Improvement |
|----------|--------------|------------|-------------|
| First call | ~2-5 seconds | ~2-5 seconds | - |
| Second call (same day) | ~2-5 seconds | ~0.1 seconds | 95%+ faster |
| Multiple calls | N × 2-5 sec | 2-5 + (N-1) × 0.1 sec | ~95% faster |

### Cache Location

Files are stored in the current working directory (`os.getcwd()`):
```
{current_working_directory}/
├── kospi_code.mst.zip       # KOSPI master ZIP (cached)
├── kospi_code.mst           # Extracted file
├── kosdaq_code.mst.zip      # KOSDAQ master ZIP (cached)
└── kosdaq_code.mst          # Extracted file
```

### Migration Notes

**No breaking changes**: Existing code continues to work without modification. Caching is applied automatically with sensible defaults.

```python
# Existing code (v0.x) - still works, now with caching
df = broker.fetch_kospi_symbols()

# New features (optional)
df = broker.fetch_kospi_symbols(ttl_hours=24, force_download=True)
```

## Built-in Memory Caching

**NEW in v0.7.0**: Optional memory-based caching to reduce API calls and improve response times.

### Basic Usage

```python
from korea_investment_stock import KoreaInvestment, CachedKoreaInvestment

# Create base broker
broker = KoreaInvestment(api_key, api_secret, acc_no)

# Wrap with caching (opt-in)
cached_broker = CachedKoreaInvestment(broker, price_ttl=5)

# Use as normal - caching happens automatically
result = cached_broker.fetch_price("005930", "KR")

# Cache statistics
stats = cached_broker.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}")
```

### Architecture

**Option B: Wrapper Class Pattern** (implemented)
- Existing `KoreaInvestment` class remains unchanged
- `CachedKoreaInvestment` wraps the broker
- Opt-in: Users choose to enable caching
- Philosophy compliant: Simple, transparent, flexible

```
KoreaInvestment (unchanged)
    ↓
CachedKoreaInvestment (wrapper)
    ↓
CacheManager (thread-safe memory cache)
```

### TTL Configuration

Default TTL values (in seconds):
- **Price data**: 5 seconds (real-time)
- **Stock info**: 300 seconds (5 minutes)
- **Symbol lists**: 3600 seconds (1 hour)
- **IPO schedule**: 1800 seconds (30 minutes)

Custom TTL:
```python
cached_broker = CachedKoreaInvestment(
    broker,
    price_ttl=1,        # Real-time trading: 1 second
    stock_info_ttl=60,  # Stock info: 1 minute
    symbols_ttl=3600,   # Symbols: 1 hour
    ipo_ttl=1800        # IPO: 30 minutes
)
```

### Cache Features

- **Thread-safe**: Uses threading.Lock for concurrent access
- **Auto-expiration**: TTL-based cache invalidation
- **Statistics**: Hit rate, miss rate, cache size tracking
- **Manual control**: `invalidate_cache()` for forced refresh
- **Context manager**: Automatic cache cleanup
- **No external deps**: Pure Python (datetime, threading)

### Performance Benefits

| Scenario | Without Cache | With Cache | Improvement |
|----------|--------------|------------|-------------|
| Repeated queries (1min) | 60 API calls | 12 calls | 80% reduction |
| Response time | 100-300ms | <1ms | 99% faster |
| Symbol lists (daily) | 10 calls | 1 call | 90% reduction |

### When to Use Caching

**✅ Good use cases:**
- Backtesting and analysis (longer TTL acceptable)
- Dashboard updates (repeated queries to same symbols)
- Symbol list queries (rarely change)
- IPO schedule monitoring

**❌ Not recommended for:**
- High-frequency trading (TTL too long for real-time)
- Single query per symbol (no benefit)
- Different symbols each time (cache never hits)

### See Also

- **Implementation guide**: `docs/start/2_cache_implementation.md`
- **PRD**: `docs/start/2_cache_prd.md`
- **Usage examples**: `examples/cached_basic_example.py`

## Automatic Token Refresh

**NEW**: API 호출 중 토큰 만료 시 자동 재발급 기능.

### Problem

장시간 실행되는 배치 작업에서 토큰이 만료되면 모든 API 호출이 실패합니다:

```
[US 11780/11780] ✗ ZVOL (API): API Error (info): 기간이 만료된 token 입니다
```

### Solution

라이브러리가 자동으로 토큰 만료를 감지하고 재발급합니다:

1. API 응답에서 토큰 만료 에러 감지 (`"기간이 만료된 token 입니다"`)
2. 자동으로 `issue_access_token(force=True)` 호출
3. 동일 요청 재시도

**사용자 코드 수정 불필요** - 투명하게 처리됩니다.

### Applied Methods

다음 API 메서드에 자동 토큰 재발급이 적용됩니다:

- `fetch_domestic_price()`
- `fetch_price_detail_oversea()`
- `fetch_stock_info()`
- `fetch_search_stock_info()`
- `fetch_ipo_schedule()`

### Force Token Refresh

수동으로 토큰을 강제 재발급할 수 있습니다:

```python
# 기존 동작: 저장소 토큰이 유효하면 재사용
broker.issue_access_token()

# 강제 재발급: 저장소 상태와 무관하게 새 토큰 발급
broker.issue_access_token(force=True)
```

### Logging

토큰 재발급 이벤트는 INFO 레벨로 로깅됩니다:

```python
import logging
logging.basicConfig(level=logging.INFO)

# API 호출 시 토큰 만료되면:
# INFO - 토큰 만료 감지, 재발급 시도...
```

### See Also

- **Implementation guide**: `docs/start/1_token_implementation.md`
- **PRD**: `docs/start/1_token_prd.md`
- **Tests**: `korea_investment_stock/tests/test_token_refresh.py`

## API Rate Limiting

**NEW in v0.8.0**: Automatic rate limiting to manage Korea Investment API's 20 calls/second limit.

### Problem

Korea Investment Securities OpenAPI has a **20 calls/second limit**. Exceeding this causes API errors:
- `examples/stress_test.py` with 500 API calls fails without rate limiting
- Batch processing of stocks triggers rate limit errors
- API returns error codes when limit exceeded

### Solution

**RateLimitedKoreaInvestment** wrapper automatically throttles API calls to stay within limits:

```python
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# Create base broker
broker = KoreaInvestment(api_key, api_secret, acc_no)

# Wrap with rate limiting (15 calls/second - conservative)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# Use as normal - rate limiting applied automatically
result = rate_limited.fetch_price("005930", "KR")

# Batch processing is now safe!
for symbol, market in stock_list:
    result = rate_limited.fetch_price(symbol, market)  # Auto-throttled
```

### Architecture

**Wrapper Pattern** (same as Cache):
```
KoreaInvestment (unchanged)
    ↓
RateLimitedKoreaInvestment (wrapper)
    ↓
RateLimiter (thread-safe rate control)
```

- Existing `KoreaInvestment` class unchanged
- Opt-in: Users choose to enable rate limiting
- Thread-safe: Uses `threading.Lock`
- Philosophy compliant: Simple, transparent, flexible

### Configuration

Default: **15 calls/second** (conservative margin below 20/sec limit)

Custom rates:
```python
# Production - ultra safe
conservative = RateLimitedKoreaInvestment(broker, calls_per_second=12)

# Testing - closer to limit
aggressive = RateLimitedKoreaInvestment(broker, calls_per_second=18)

# Maximum safety
ultra_safe = RateLimitedKoreaInvestment(broker, calls_per_second=10)
```

### Dynamic Adjustment

```python
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# Adjust at runtime
rate_limited.adjust_rate_limit(calls_per_second=10)

# Check statistics
stats = rate_limited.get_rate_limit_stats()
print(f"Current rate: {stats['calls_per_second']}/sec")
print(f"Total calls: {stats['total_calls']}")
```

### Combined with Cache (Recommended!)

**Best practice**: Use both Cache and Rate Limiting together for optimal performance and safety:

```python
from korea_investment_stock import (
    KoreaInvestment,
    CachedKoreaInvestment,
    RateLimitedKoreaInvestment
)

# Stack both wrappers
broker = KoreaInvestment(api_key, api_secret, acc_no)
cached = CachedKoreaInvestment(broker, price_ttl=5)
safe_broker = RateLimitedKoreaInvestment(cached, calls_per_second=15)

# Benefits:
# ✅ Cache reduces API calls (performance)
# ✅ Rate limit protects cache misses (safety)
# ✅ No API errors, maximum efficiency
```

**How it works together:**
1. **Rate Limit**: wait() check (throttle)
2. **Cache**: Check cache (hit = instant return, miss = continue)
3. **API**: Real API call (only if cache miss)

### Performance Impact

| Scenario | Without Rate Limit | With Rate Limit (15/sec) |
|----------|-------------------|-------------------------|
| 10 API calls | ~1-3 sec | ~0.67 sec |
| 100 API calls | ~10-30 sec | ~6.7 sec |
| 500 API calls | **FAILS** (rate limit errors) | ~33 sec (100% success) |

### When to Use

**✅ Use rate limiting for:**
- Batch processing (>20 stocks)
- Continuous queries (production apps)
- Stress tests
- Any scenario where rate limit errors occur

**❌ Not needed for:**
- Single or rare queries
- Already have custom rate limiting
- Interactive development/manual testing

### Context Manager Support

```python
broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

with rate_limited:
    for symbol, market in stocks:
        result = rate_limited.fetch_price(symbol, market)
```

### Stress Test Example

See `examples/stress_test.py` for complete example with 250 stocks (500 API calls):

```bash
# Run stress test with rate limiting
python examples/stress_test.py

# Expected results:
# - 500 API calls complete
# - 100% success rate
# - ~33 seconds execution time
# - 0 rate limit errors
```

### See Also

- **Implementation guide**: `docs/start/1_api_limit_implementation.md`
- **PRD**: `docs/start/1_api_limit_prd.md`
- **TODO checklist**: `docs/start/1_api_limit_todo.md`

## Rate Limit Logging and Monitoring

**NEW**: Built-in logging and extended statistics for production monitoring.

### Logging

Rate limiter uses Python's standard `logging` module for throttle event logging:

```python
import logging
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# Enable DEBUG logging to see throttle events
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# Each throttle event will be logged:
# "Rate limit: waiting 0.067s (call #2)"
result = rate_limited.fetch_price("005930", "KR")
```

**Log Levels:**
- `DEBUG`: Every throttle event with wait time
- `INFO`: Application-level messages (default in examples)
- User can configure logging as needed

### Extended Statistics

The `get_rate_limit_stats()` method now returns comprehensive metrics:

```python
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# Make some API calls
for symbol, market in stock_list:
    rate_limited.fetch_price(symbol, market)

# Get detailed statistics
stats = rate_limited.get_rate_limit_stats()
```

**Statistics Fields:**

```python
{
    # Basic Configuration
    'calls_per_second': 15.0,       # Configured rate limit
    'min_interval': 0.0667,         # Minimum interval between calls (seconds)
    'last_call': 1699999999.123,    # Timestamp of last call

    # Call Counts
    'total_calls': 500,              # Total API calls made
    'throttled_calls': 450,          # Calls that were throttled

    # Throttle Metrics (NEW)
    'throttle_rate': 0.90,           # Percentage of calls throttled (0.0 - 1.0)
    'total_wait_time': 28.5,         # Total time spent waiting (seconds)
    'avg_wait_time': 0.0633          # Average wait per throttled call (seconds)
}
```

### Production Monitoring Example

```python
import logging
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

broker = KoreaInvestment(api_key, api_secret, acc_no)
rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

# Run batch processing
with rate_limited:
    for symbol, market in stock_list:
        result = rate_limited.fetch_price(symbol, market)
        # Process result...

# Get performance metrics
stats = rate_limited.get_rate_limit_stats()

print(f"Performance Metrics:")
print(f"  Total calls: {stats['total_calls']}")
print(f"  Throttled: {stats['throttled_calls']} ({stats['throttle_rate']*100:.1f}%)")
print(f"  Total wait time: {stats['total_wait_time']:.2f}s")
print(f"  Avg wait time: {stats['avg_wait_time']:.3f}s")

# Example output:
# Performance Metrics:
#   Total calls: 500
#   Throttled: 450 (90.0%)
#   Total wait time: 28.5s
#   Avg wait time: 0.063s
```

### Interpreting Statistics

**Throttle Rate:**
- **0-20%**: Low throttling, rate limit is generous
- **20-80%**: Moderate throttling, balanced configuration
- **80-100%**: High throttling, may want to reduce `calls_per_second`

**Total Wait Time:**
- Shows overhead from rate limiting
- Compare with total execution time to assess impact
- Example: 28.5s wait / 33s total = 86% of time spent waiting

**Average Wait Time:**
- Should be close to `min_interval` (1/calls_per_second)
- Example: 15 calls/sec → 0.067s interval
- Higher values may indicate timing issues

### See Also

- **Example**: `examples/stress_test.py` demonstrates logging and statistics
- **Tests**: `korea_investment_stock/rate_limit/test_rate_limiter.py`

## User Implementation Examples

### Batch Processing Example

```python
def fetch_multiple_stocks(broker, stock_list, rate_limit=15):
    """Fetch multiple stocks with rate limiting"""
    import time

    min_interval = 1.0 / rate_limit
    last_call = 0
    results = []

    for symbol, market in stock_list:
        # Rate limiting
        elapsed = time.time() - last_call
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        last_call = time.time()

        # API call
        result = broker.fetch_price(symbol, market)
        results.append(result)

    return results
```

## Migration from v0.5.0

**Breaking Changes in v0.6.0:**

1. **Removed Methods:**
   - `fetch_price_list()` → Use loop with `fetch_price()`
   - `fetch_stock_info_list()` → Use loop with `fetch_stock_info()`
   - All batch processing methods
   - All caching methods
   - All monitoring methods

2. **Removed Features:**
   - Rate limiting system
   - TTL caching
   - Statistics collection
   - Visualization tools
   - Automatic retry decorators

3. **Migration Example:**
```python
# v0.5.0 (Old)
results = broker.fetch_price_list([("005930", "KR"), ("AAPL", "US")])

# v0.6.0 (New)
results = []
for symbol, market in [("005930", "KR"), ("AAPL", "US")]:
    result = broker.fetch_price(symbol, market)
    results.append(result)
    # Add your own rate limiting here if needed
```

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## Additional Resources

- **Official API Docs**: https://wikidocs.net/book/7845
- **GitHub Issues**: https://github.com/kenshin579/korea-investment-stock/issues
- **PyPI**: https://pypi.org/project/korea-investment-stock/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md) - v0.6.0 breaking changes

---

**Remember**: This is a pure wrapper. You control rate limiting, caching, error handling, and monitoring according to your needs.
