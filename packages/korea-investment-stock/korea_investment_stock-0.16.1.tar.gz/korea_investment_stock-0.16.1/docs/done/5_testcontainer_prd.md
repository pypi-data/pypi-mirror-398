# Testcontainers 도입 PRD

## 1. 개요

### 1.1 현재 상태

현재 `korea-investment-stock` 프로젝트의 테스트 구조:

| 파일 | 외부 의존성 | 현재 방식 | 문제점 |
|------|------------|----------|--------|
| `test_token_storage.py` | Redis | `fakeredis` (in-memory mock) | 실제 Redis와 동작 차이 가능 |
| `test_cached_integration.py` | Korea Investment API | 실제 API 호출 | API 자격 증명 필요 |
| `test_rate_limited_integration.py` | Korea Investment API | 실제 API 호출 | API 자격 증명 필요 |
| `redis_token_example.py` | Redis | 실제 Redis 필요 | 수동 Docker 실행 필요 |

### 1.2 문제점

1. **fakeredis의 한계**
   - 일부 Redis 명령어 미지원 (예: `CLIENT`, `CLUSTER`, `DEBUG`)
   - 실제 네트워크 통신 테스트 불가
   - 연결 풀링, 타임아웃 등 실제 환경 동작 검증 불가
   - Redis 버전별 동작 차이 테스트 불가

2. **CI/CD 환경의 일관성 부족**
   - 개발자 로컬 환경마다 Redis 설치 여부 다름
   - GitHub Actions에서 별도 Redis 서비스 설정 필요
   - 테스트 격리가 완벽하지 않음 (포트 충돌 가능)

3. **확장성 문제**
   - 향후 다른 외부 서비스 (PostgreSQL, Kafka 등) 추가 시 동일 문제 반복

### 1.3 목표

- `testcontainers-python`을 도입하여 실제 Docker 컨테이너 기반 테스트 환경 구축
- 기존 `fakeredis` 테스트와 `testcontainers` 테스트 공존 (선택 가능)
- CI/CD 파이프라인에서 자동화된 컨테이너 테스트 지원

## 2. 영향받는 파일

### 2.1 수정 대상

```
korea_investment_stock/
├── token_storage/
│   └── test_token_storage.py          # Redis testcontainer 추가
│
└── tests/                              # (신규) 통합 테스트 디렉토리
    ├── conftest.py                     # 공통 fixture 정의
    └── test_redis_integration.py       # 실제 Redis 통합 테스트
```

### 2.2 현재 test_token_storage.py 분석

**fakeredis 사용 부분** (수정 대상):

```python
# 현재 코드 (lines 57-65)
@pytest.fixture
def fake_redis():
    """In-memory Redis 인스턴스 (fakeredis) (전역 fixture)"""
    try:
        import fakeredis
    except ImportError:
        pytest.skip("fakeredis가 설치되지 않았습니다")
    return fakeredis.FakeStrictRedis(decode_responses=True)
```

**영향받는 테스트 클래스:**
- `TestRedisTokenStorage` (10개 테스트 메서드)
- `TestTokenStorageIntegration` (2개 테스트 메서드)

## 3. 요구사항

### 3.1 기능 요구사항

#### FR-1: Testcontainers 의존성 추가
- `testcontainers[redis]>=4.0.0` 패키지를 `pyproject.toml`의 `dev` 의존성에 추가
- Docker가 설치되어 있지 않은 환경에서는 테스트 자동 스킵

#### FR-2: Redis 컨테이너 fixture 구현
- pytest fixture로 Redis 컨테이너 생명주기 관리
- 테스트 세션 또는 모듈 단위로 컨테이너 재사용 (성능 최적화)
- 컨테이너 시작 실패 시 graceful skip

```python
# 예상 구현
@pytest.fixture(scope="module")
def redis_container():
    """실제 Redis Docker 컨테이너"""
    try:
        from testcontainers.redis import RedisContainer
    except ImportError:
        pytest.skip("testcontainers가 설치되지 않았습니다")

    with RedisContainer("redis:7-alpine") as redis:
        yield redis
```

#### FR-3: 기존 fakeredis 테스트 유지
- 기존 `fakeredis` 기반 테스트는 그대로 유지 (빠른 단위 테스트용)
- pytest marker로 테스트 유형 구분:
  - `@pytest.mark.unit`: fakeredis 사용 (기본)
  - `@pytest.mark.integration`: testcontainers 사용

#### FR-4: 테스트 실행 옵션
```bash
# 단위 테스트만 실행 (fakeredis, Docker 불필요)
pytest -m "not integration"

# 통합 테스트만 실행 (Docker 필요)
pytest -m integration

# 전체 테스트 실행
pytest
```

### 3.2 비기능 요구사항

#### NFR-1: 성능
- 컨테이너 시작 시간: < 5초
- 테스트 세션 당 컨테이너 1회만 시작 (scope="session" 사용)

#### NFR-2: 격리
- 각 테스트 간 데이터 격리 (테스트 전 `FLUSHDB` 실행)
- 랜덤 포트 사용으로 포트 충돌 방지

#### NFR-3: CI/CD 호환성
- GitHub Actions에서 Docker-in-Docker 지원
- Docker 미설치 환경에서 graceful skip

## 4. 구현 계획

### 4.1 Phase 1: 기본 인프라 구축

**작업 내용:**
1. `pyproject.toml`에 `testcontainers` 의존성 추가
2. `conftest.py`에 공통 fixture 정의
3. pytest marker 설정 (`pytest.ini` 또는 `pyproject.toml`)

**예상 변경:**

```toml
# pyproject.toml
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

### 4.2 Phase 2: Redis 통합 테스트 구현

**작업 내용:**
1. `test_redis_integration.py` 파일 생성
2. 기존 `TestRedisTokenStorage` 테스트를 testcontainers 버전으로 복제
3. 실제 Redis 특화 테스트 추가 (연결 풀링, 타임아웃 등)

**추가할 테스트 케이스:**

| 테스트명 | 설명 | fakeredis로 불가능한 이유 |
|---------|------|-------------------------|
| `test_connection_pool` | Redis 연결 풀 동작 확인 | 네트워크 연결 필요 |
| `test_connection_timeout` | 연결 타임아웃 처리 | 실제 네트워크 지연 필요 |
| `test_redis_persistence` | 데이터 영속성 확인 | 실제 Redis 프로세스 필요 |
| `test_concurrent_clients` | 다중 클라이언트 동시 접속 | 실제 TCP 연결 필요 |

### 4.3 Phase 3: CI/CD 통합

**작업 내용:**
1. GitHub Actions workflow 수정
2. Docker 서비스 설정 추가
3. 테스트 실행 순서 최적화

**예상 workflow:**

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: pytest -m "not integration"

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest -m integration
```

## 5. 상세 구현 가이드

### 5.1 conftest.py 구현

```python
# korea_investment_stock/tests/conftest.py
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

### 5.2 test_redis_integration.py 구현

```python
# korea_investment_stock/tests/test_redis_integration.py
"""
Redis 통합 테스트 (testcontainers 사용)

실제 Redis Docker 컨테이너를 사용하여 테스트합니다.
Docker가 설치되어 있어야 합니다.

실행 방법:
    pytest -m integration korea_investment_stock/tests/test_redis_integration.py
"""
import pytest
from datetime import datetime, timedelta

from korea_investment_stock.token_storage import RedisTokenStorage


@pytest.mark.integration
class TestRedisTokenStorageIntegration:
    """RedisTokenStorage 실제 Redis 통합 테스트"""

    @pytest.fixture
    def storage(self, redis_url):
        """실제 Redis를 사용하는 RedisTokenStorage"""
        return RedisTokenStorage(redis_url=redis_url)

    @pytest.fixture
    def token_data(self):
        """테스트용 토큰 데이터"""
        expiry_time = datetime.now() + timedelta(days=1)
        return {
            'access_token': 'Bearer test_token_12345',
            'access_token_token_expired': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(expiry_time.timestamp()),
            'api_key': 'test_key',
            'api_secret': 'test_secret'
        }

    def test_save_and_load(self, storage, token_data):
        """토큰 저장 및 로드 테스트"""
        assert storage.save_token(token_data) is True
        loaded = storage.load_token('test_key', 'test_secret')
        assert loaded is not None
        assert loaded['access_token'] == token_data['access_token']

    def test_connection_pool(self, redis_url):
        """연결 풀 동작 확인"""
        import threading

        storage = RedisTokenStorage(redis_url=redis_url)
        results = []

        def save_token(idx):
            token_data = {
                'access_token': f'Bearer token_{idx}',
                'timestamp': int((datetime.now() + timedelta(days=1)).timestamp()),
                'api_key': f'key_{idx}',
                'api_secret': f'secret_{idx}'
            }
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
        import time

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
```

## 6. 마이그레이션 가이드

### 6.1 기존 테스트와의 호환성

기존 `fakeredis` 테스트는 변경 없이 유지됩니다:

```bash
# 기존 방식 (여전히 동작)
pytest korea_investment_stock/token_storage/test_token_storage.py

# Docker 없이 빠른 테스트
pytest -m "not integration"
```

### 6.2 새로운 통합 테스트 실행

```bash
# Docker 필요
pytest -m integration

# 전체 테스트 (단위 + 통합)
pytest
```

## 7. 의존성

### 7.1 필수 의존성

| 패키지 | 버전 | 용도 |
|--------|------|-----|
| `testcontainers` | >=4.0.0 | Docker 컨테이너 관리 |
| `docker` | >=6.0.0 | Docker API 클라이언트 (testcontainers 의존성) |

### 7.2 시스템 요구사항

| 요구사항 | 설명 |
|---------|------|
| Docker | Docker Desktop 또는 Docker Engine 설치 필요 |
| Docker Compose | 선택사항 (복잡한 테스트 환경 구성 시) |

## 8. 위험 및 제약사항

### 8.1 위험 요소

| 위험 | 영향 | 완화 방안 |
|-----|-----|----------|
| Docker 미설치 환경 | 테스트 실패 | graceful skip 구현 |
| 컨테이너 시작 지연 | 테스트 시간 증가 | 세션 스코프 fixture 사용 |
| CI/CD 환경 차이 | 예상치 못한 실패 | Docker-in-Docker 설정 문서화 |

### 8.2 제약사항

- Windows 환경에서 Docker Desktop 필요 (WSL2 권장)
- Apple Silicon Mac에서 ARM 이미지 사용 (redis:7-alpine 지원)
- GitHub Actions free tier에서 Docker 서비스 실행 시간 제한

## 9. 참고 자료

- [Testcontainers Python Documentation](https://testcontainers-python.readthedocs.io/)
- [pytest markers](https://docs.pytest.org/en/stable/example/markers.html)
- [GitHub Actions - Docker services](https://docs.github.com/en/actions/using-containerized-services)
