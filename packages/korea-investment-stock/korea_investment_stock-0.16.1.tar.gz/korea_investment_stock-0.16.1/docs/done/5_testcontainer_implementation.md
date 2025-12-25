# Testcontainers 구현 가이드

## 1. 개요

`testcontainers-python`을 도입하여 실제 Redis Docker 컨테이너 기반 통합 테스트 환경을 구축한다.

**핵심 원칙:**
- 기존 `fakeredis` 단위 테스트 유지 (빠른 테스트용)
- `testcontainers` 통합 테스트 추가 (실제 환경 검증용)
- pytest marker로 테스트 유형 구분

## 2. 파일 구조

```
korea_investment_stock/
├── tests/                              # (신규) 통합 테스트 디렉토리
│   ├── __init__.py
│   ├── conftest.py                     # 공통 fixture 정의
│   └── test_redis_integration.py       # Redis 통합 테스트
│
├── token_storage/
│   └── test_token_storage.py           # 기존 유지 (fakeredis)
│
└── pyproject.toml                      # 의존성 추가
```

## 3. 의존성 변경

### pyproject.toml

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "fakeredis>=2.10.0",
    "testcontainers>=4.0.0",  # 추가
]

[tool.pytest.ini_options]
markers = [
    "unit: 단위 테스트 (fakeredis, Docker 불필요)",
    "integration: 통합 테스트 (Docker 필요)",
]
```

## 4. 핵심 구현

### 4.1 conftest.py

```python
# korea_investment_stock/tests/conftest.py
"""통합 테스트용 공통 fixture"""
import pytest


def pytest_configure(config):
    """pytest marker 등록"""
    config.addinivalue_line("markers", "unit: 단위 테스트")
    config.addinivalue_line("markers", "integration: 통합 테스트 (Docker 필요)")


@pytest.fixture(scope="session")
def redis_container():
    """실제 Redis Docker 컨테이너 (세션 단위 재사용)"""
    try:
        from testcontainers.redis import RedisContainer
    except ImportError:
        pytest.skip("testcontainers가 설치되지 않았습니다")

    try:
        container = RedisContainer("redis:7-alpine")
        container.start()
        yield container
        container.stop()
    except Exception as e:
        pytest.skip(f"Docker를 사용할 수 없습니다: {e}")


@pytest.fixture
def redis_url(redis_container):
    """Redis 컨테이너의 연결 URL"""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"


@pytest.fixture
def redis_client(redis_container, redis_url):
    """Redis 클라이언트 인스턴스 (각 테스트 전 FLUSHDB)"""
    import redis

    client = redis.from_url(redis_url)
    client.flushdb()  # 테스트 격리
    yield client
    client.close()
```

### 4.2 test_redis_integration.py

```python
# korea_investment_stock/tests/test_redis_integration.py
"""
Redis 통합 테스트 (testcontainers 사용)

실행: pytest -m integration
"""
import pytest
import time
import threading
from datetime import datetime, timedelta

from korea_investment_stock.token_storage import RedisTokenStorage


def create_token_data(api_key="test_key", api_secret="test_secret", days=1):
    """테스트용 토큰 데이터 생성"""
    expiry_time = datetime.now() + timedelta(days=days)
    return {
        'access_token': 'Bearer test_token_12345',
        'access_token_token_expired': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': int(expiry_time.timestamp()),
        'api_key': api_key,
        'api_secret': api_secret
    }


@pytest.mark.integration
class TestRedisTokenStorageIntegration:
    """RedisTokenStorage 실제 Redis 통합 테스트"""

    @pytest.fixture
    def storage(self, redis_url):
        """실제 Redis를 사용하는 RedisTokenStorage"""
        return RedisTokenStorage(redis_url=redis_url)

    def test_save_and_load(self, storage):
        """토큰 저장 및 로드"""
        token_data = create_token_data()
        assert storage.save_token(token_data) is True

        loaded = storage.load_token('test_key', 'test_secret')
        assert loaded is not None
        assert loaded['access_token'] == token_data['access_token']

    def test_check_token_valid(self, storage):
        """토큰 유효성 확인"""
        assert storage.check_token_valid('test_key', 'test_secret') is False

        token_data = create_token_data()
        storage.save_token(token_data)
        assert storage.check_token_valid('test_key', 'test_secret') is True

    def test_delete_token(self, storage):
        """토큰 삭제"""
        token_data = create_token_data()
        storage.save_token(token_data)

        assert storage.delete_token('test_key', 'test_secret') is True
        assert storage.check_token_valid('test_key', 'test_secret') is False

    def test_connection_pool(self, redis_url):
        """다중 스레드 연결 풀 동작 확인"""
        storage = RedisTokenStorage(redis_url=redis_url)
        results = []

        def save_token(idx):
            token_data = create_token_data(api_key=f'key_{idx}', api_secret=f'secret_{idx}')
            result = storage.save_token(token_data)
            results.append((idx, result))

        threads = [threading.Thread(target=save_token, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        assert all(r[1] for r in results)

    def test_ttl_actual_expiry(self, storage, redis_client):
        """실제 TTL 만료 확인 (fakeredis로 불가능)"""
        # 2초 후 만료되는 토큰
        token_data = {
            'access_token': 'Bearer short_lived_token',
            'timestamp': int((datetime.now() + timedelta(seconds=2)).timestamp()),
            'api_key': 'ttl_key',
            'api_secret': 'ttl_secret'
        }
        storage.save_token(token_data)

        # 즉시 확인 - 존재해야 함
        assert storage.check_token_valid('ttl_key', 'ttl_secret') is True

        # 3초 대기 후 - 만료되어야 함
        time.sleep(3)
        assert storage.check_token_valid('ttl_key', 'ttl_secret') is False


@pytest.mark.integration
class TestRedisConnectionHandling:
    """Redis 연결 관련 통합 테스트"""

    def test_reconnection_after_flushdb(self, redis_url, redis_client):
        """FLUSHDB 후 재연결 동작 확인"""
        storage = RedisTokenStorage(redis_url=redis_url)
        token_data = create_token_data()

        storage.save_token(token_data)
        assert storage.check_token_valid('test_key', 'test_secret') is True

        redis_client.flushdb()
        assert storage.check_token_valid('test_key', 'test_secret') is False

    def test_multiple_databases(self, redis_container):
        """다중 Redis 데이터베이스 격리 확인"""
        host = redis_container.get_container_host_ip()
        port = redis_container.get_exposed_port(6379)

        storage_db0 = RedisTokenStorage(redis_url=f"redis://{host}:{port}/0")
        storage_db1 = RedisTokenStorage(redis_url=f"redis://{host}:{port}/1")

        token_data = create_token_data()
        storage_db0.save_token(token_data)

        # DB0에만 저장됨
        assert storage_db0.check_token_valid('test_key', 'test_secret') is True
        assert storage_db1.check_token_valid('test_key', 'test_secret') is False
```

## 5. 테스트 실행

```bash
# 단위 테스트만 (Docker 불필요, 빠름)
pytest -m "not integration"

# 통합 테스트만 (Docker 필요)
pytest -m integration

# 전체 테스트
pytest

# 통합 테스트 상세 출력
pytest -m integration -v
```

## 6. CI/CD 설정

### GitHub Actions workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run unit tests
        run: pytest -m "not integration" -v

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev,redis]"
      - name: Run integration tests
        run: pytest -m integration -v
```

## 7. 주의사항

### Docker 미설치 환경
- `redis_container` fixture에서 자동 skip 처리
- 단위 테스트는 정상 실행됨

### 테스트 격리
- `redis_client` fixture에서 `FLUSHDB` 실행
- 각 테스트는 독립적인 상태에서 시작

### 성능 최적화
- `scope="session"`으로 컨테이너 1회만 시작
- 컨테이너 시작 시간: ~2-3초
