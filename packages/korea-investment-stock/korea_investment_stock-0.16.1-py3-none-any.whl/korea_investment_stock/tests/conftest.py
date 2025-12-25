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
