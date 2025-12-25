# korea_investment_stock/tests/test_redis_integration.py
"""
Redis 통합 테스트 (testcontainers 사용)

실제 Redis Docker 컨테이너를 사용하여 테스트합니다.
Docker가 설치되어 있어야 합니다.

실행 방법:
    pytest -m integration korea_investment_stock/tests/test_redis_integration.py
"""
import pytest
import time
import threading
from datetime import datetime, timedelta

from korea_investment_stock.token import RedisTokenStorage


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
    def storage(self, redis_url, redis_client):
        """실제 Redis를 사용하는 RedisTokenStorage (각 테스트 전 FLUSHDB됨)"""
        # redis_client fixture가 먼저 FLUSHDB를 실행하므로 격리됨
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
        expiry_time = datetime.now() + timedelta(seconds=2)
        token_data = {
            'access_token': 'Bearer short_lived_token',
            'access_token_token_expired': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(expiry_time.timestamp()),
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
