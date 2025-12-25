"""
토큰 저장소 단위 테스트

FileTokenStorage, RedisTokenStorage의 기능을 테스트합니다.
fakeredis를 사용하여 Redis 테스트를 수행합니다 (Docker 불필요).
"""

import pytest
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from .storage import (
    FileTokenStorage,
    RedisTokenStorage,
)


# ============================================================
# Test Helpers
# ============================================================

def create_token_data(api_key="test_key", api_secret="test_secret", days_until_expiry=1):
    """테스트용 토큰 데이터 생성

    Args:
        api_key: API Key
        api_secret: API Secret
        days_until_expiry: 만료까지 남은 일수

    Returns:
        Dict[str, Any]: 토큰 데이터
    """
    expiry_time = datetime.now() + timedelta(days=days_until_expiry)
    return {
        'access_token': 'Bearer test_token_12345',
        'access_token_token_expired': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': int(expiry_time.timestamp()),
        'api_key': api_key,
        'api_secret': api_secret
    }


# ============================================================
# Global Fixtures (shared across test classes)
# ============================================================

@pytest.fixture
def temp_token_file():
    """임시 토큰 파일 경로 생성 (전역 fixture)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "token.key"


@pytest.fixture
def fake_redis():
    """In-memory Redis 인스턴스 (fakeredis) (전역 fixture)"""
    try:
        import fakeredis
    except ImportError:
        pytest.skip("fakeredis가 설치되지 않았습니다")

    return fakeredis.FakeStrictRedis(decode_responses=True)


# ============================================================
# FileTokenStorage Tests
# ============================================================

class TestFileTokenStorage:
    """FileTokenStorage 클래스 테스트"""

    @pytest.fixture
    def file_storage(self, temp_token_file):
        """FileTokenStorage 인스턴스 생성"""
        return FileTokenStorage(file_path=temp_token_file)

    def test_save_and_load(self, file_storage):
        """토큰 저장 및 로드 테스트"""
        token_data = create_token_data()

        # 저장
        assert file_storage.save_token(token_data) is True

        # 로드
        loaded = file_storage.load_token('test_key', 'test_secret')
        assert loaded is not None
        assert loaded['access_token'] == 'Bearer test_token_12345'
        assert loaded['api_key'] == 'test_key'

    def test_check_token_valid(self, file_storage):
        """토큰 유효성 확인 테스트"""
        token_data = create_token_data()

        # 토큰이 없을 때
        assert file_storage.check_token_valid('test_key', 'test_secret') is False

        # 토큰 저장 후
        file_storage.save_token(token_data)
        assert file_storage.check_token_valid('test_key', 'test_secret') is True

    def test_expired_token(self, file_storage):
        """만료된 토큰 확인 테스트"""
        # 이미 만료된 토큰 (과거 시간)
        token_data = create_token_data(days_until_expiry=-1)
        file_storage.save_token(token_data)

        assert file_storage.check_token_valid('test_key', 'test_secret') is False
        assert file_storage.load_token('test_key', 'test_secret') is None

    def test_wrong_credentials(self, file_storage):
        """잘못된 인증 정보로 접근 시 테스트"""
        token_data = create_token_data(api_key='key1', api_secret='secret1')
        file_storage.save_token(token_data)

        # 잘못된 API Key
        assert file_storage.check_token_valid('wrong_key', 'secret1') is False

        # 잘못된 API Secret
        assert file_storage.check_token_valid('key1', 'wrong_secret') is False

    def test_delete_token(self, file_storage):
        """토큰 삭제 테스트"""
        token_data = create_token_data()
        file_storage.save_token(token_data)

        # 삭제 전 확인
        assert file_storage.check_token_valid('test_key', 'test_secret') is True

        # 삭제
        assert file_storage.delete_token('test_key', 'test_secret') is True

        # 삭제 후 확인
        assert file_storage.check_token_valid('test_key', 'test_secret') is False

    def test_directory_auto_creation(self, temp_token_file):
        """디렉토리 자동 생성 테스트"""
        # 깊은 경로 생성
        deep_path = temp_token_file.parent / "sub1" / "sub2" / "token.key"
        storage = FileTokenStorage(file_path=deep_path)

        token_data = create_token_data()
        assert storage.save_token(token_data) is True
        assert deep_path.exists()


# ============================================================
# RedisTokenStorage Tests (with fakeredis)
# ============================================================

class TestRedisTokenStorage:
    """RedisTokenStorage 클래스 테스트 (fakeredis 사용)"""

    @pytest.fixture
    def redis_storage(self, fake_redis, monkeypatch):
        """fakeredis를 사용하는 RedisTokenStorage"""
        def mock_from_url(*args, **kwargs):
            return fake_redis

        # redis.from_url을 mock으로 대체
        monkeypatch.setattr('redis.from_url', mock_from_url)

        return RedisTokenStorage("redis://localhost:6379/0")

    def test_save_and_load(self, redis_storage):
        """Redis 토큰 저장 및 로드 테스트"""
        token_data = create_token_data()

        # 저장
        assert redis_storage.save_token(token_data) is True

        # 로드
        loaded = redis_storage.load_token('test_key', 'test_secret')
        assert loaded is not None
        assert loaded['access_token'] == 'Bearer test_token_12345'
        assert loaded['timestamp'] == token_data['timestamp']

    def test_redis_with_password(self, fake_redis, monkeypatch):
        """Redis 비밀번호 인증 테스트"""
        # URL 변환이 올바르게 되었는지 확인하기 위한 변수
        captured_url = []

        def mock_from_url(url, *args, **kwargs):
            # 전달된 URL을 캡처
            captured_url.append(url)
            return fake_redis

        monkeypatch.setattr('redis.from_url', mock_from_url)

        storage = RedisTokenStorage(
            redis_url="redis://localhost:6379/0",
            password="mypassword"
        )
        assert storage is not None

        # 캡처된 URL에 비밀번호가 포함되어 있는지 확인
        assert len(captured_url) == 1
        assert ':mypassword@' in captured_url[0]

    def test_ttl_auto_expire(self, redis_storage, fake_redis):
        """TTL 자동 만료 테스트"""
        token_data = create_token_data(days_until_expiry=0)  # 1일
        # 10초 후 만료되도록 설정
        token_data['timestamp'] = int((datetime.now() + timedelta(seconds=10)).timestamp())

        redis_storage.save_token(token_data)

        # TTL 확인
        redis_key = redis_storage._get_redis_key('test_key')
        ttl = fake_redis.ttl(redis_key)
        assert 5 < ttl <= 10  # TTL이 설정되어 있음

    def test_check_token_valid(self, redis_storage):
        """Redis 토큰 유효성 확인 테스트"""
        token_data = create_token_data()

        # 토큰이 없을 때
        assert redis_storage.check_token_valid('test_key', 'test_secret') is False

        # 토큰 저장 후
        redis_storage.save_token(token_data)
        assert redis_storage.check_token_valid('test_key', 'test_secret') is True

    def test_expired_token(self, redis_storage):
        """Redis 만료된 토큰 테스트"""
        token_data = create_token_data(days_until_expiry=-1)
        redis_storage.save_token(token_data)

        assert redis_storage.check_token_valid('test_key', 'test_secret') is False
        assert redis_storage.load_token('test_key', 'test_secret') is None

    def test_wrong_credentials(self, redis_storage):
        """잘못된 인증 정보로 접근 시 테스트"""
        token_data = create_token_data(api_key='key1', api_secret='secret1')
        redis_storage.save_token(token_data)

        # 잘못된 API Secret
        assert redis_storage.check_token_valid('key1', 'wrong_secret') is False

    def test_delete_token(self, redis_storage):
        """Redis 토큰 삭제 테스트"""
        token_data = create_token_data()
        redis_storage.save_token(token_data)

        # 삭제 전 확인
        assert redis_storage.check_token_valid('test_key', 'test_secret') is True

        # 삭제
        assert redis_storage.delete_token('test_key', 'test_secret') is True

        # 삭제 후 확인
        assert redis_storage.check_token_valid('test_key', 'test_secret') is False

    def test_concurrent_access(self, redis_storage):
        """동시 접근 테스트 (멀티 스레드)"""
        token_data = create_token_data()
        results = []

        def save_and_load():
            redis_storage.save_token(token_data)
            loaded = redis_storage.load_token('test_key', 'test_secret')
            results.append(loaded is not None)

        # 10개 스레드 동시 실행
        threads = [threading.Thread(target=save_and_load) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 모든 스레드가 성공적으로 실행되었는지 확인
        assert all(results)
        assert len(results) == 10

    def test_redis_key_generation(self, redis_storage):
        """Redis 키 생성 로직 테스트"""
        key1 = redis_storage._get_redis_key('test_key_1')
        key2 = redis_storage._get_redis_key('test_key_2')
        key3 = redis_storage._get_redis_key('test_key_1')  # 동일한 키

        # 다른 API Key는 다른 Redis 키 생성
        assert key1 != key2

        # 같은 API Key는 같은 Redis 키 생성
        assert key1 == key3

        # 키 프리픽스 확인
        assert key1.startswith('korea_investment:token:')


# ============================================================
# Integration Tests
# ============================================================

class TestTokenStorageIntegration:
    """토큰 저장소 통합 테스트"""

    def test_file_to_redis_migration(self, temp_token_file, fake_redis, monkeypatch):
        """File 저장소에서 Redis 저장소로 마이그레이션 시나리오"""
        # 1. File 저장소에 토큰 저장
        file_storage = FileTokenStorage(file_path=temp_token_file)
        token_data = create_token_data()
        file_storage.save_token(token_data)

        # 2. Redis 저장소로 전환
        def mock_from_url(*args, **kwargs):
            return fake_redis

        monkeypatch.setattr('redis.from_url', mock_from_url)
        redis_storage = RedisTokenStorage("redis://localhost:6379/0")

        # 3. File에서 로드하여 Redis에 저장
        file_token = file_storage.load_token('test_key', 'test_secret')
        assert file_token is not None

        redis_storage.save_token(file_token)

        # 4. Redis에서 로드 확인
        redis_token = redis_storage.load_token('test_key', 'test_secret')
        assert redis_token is not None
        assert redis_token['access_token'] == file_token['access_token']

    def test_custom_key_prefix(self, fake_redis, monkeypatch):
        """커스텀 Redis 키 프리픽스 테스트"""
        def mock_from_url(*args, **kwargs):
            return fake_redis

        monkeypatch.setattr('redis.from_url', mock_from_url)

        storage = RedisTokenStorage(
            redis_url="redis://localhost:6379/0",
            key_prefix="custom:prefix"
        )

        token_data = create_token_data()
        storage.save_token(token_data)

        redis_key = storage._get_redis_key('test_key')
        assert redis_key.startswith('custom:prefix:')


# ============================================================
# Error Handling Tests
# ============================================================

class TestErrorHandling:
    """에러 처리 테스트"""

    def test_file_storage_permission_error(self, monkeypatch):
        """파일 권한 오류 처리 테스트"""
        storage = FileTokenStorage(file_path=Path("/root/no_permission/token.key"))
        token_data = create_token_data()

        # 권한이 없는 경로에 저장 시도
        result = storage.save_token(token_data)
        # 에러가 발생해도 False 반환 (예외 발생 안 함)
        assert result is False

    def test_redis_import_error(self):
        """Redis 패키지 미설치 시 에러 테스트"""
        with patch.dict('sys.modules', {'redis': None}):
            with pytest.raises(ImportError, match="redis 패키지가 필요합니다"):
                RedisTokenStorage()

    @pytest.mark.skip(reason="Test not needed - optional dependency")
    def test_redis_connection_error(self, monkeypatch):
        """Redis 연결 실패 시 에러 테스트"""
        def mock_from_url(*args, **kwargs):
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Connection refused")
            return mock_client

        monkeypatch.setattr('redis.from_url', mock_from_url)

        with pytest.raises(ConnectionError, match="Redis 서버 연결 실패"):
            RedisTokenStorage("redis://invalid:6379/0")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
