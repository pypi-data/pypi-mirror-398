"""
토큰 저장소 추상화 모듈

이 모듈은 Korea Investment API 토큰을 저장하고 관리하기 위한
추상화 계층을 제공합니다.

지원하는 저장소:
- FileTokenStorage: 파일 기반 저장 (기본값)
- RedisTokenStorage: Redis 기반 저장 (분산 환경 지원)
"""

import hashlib
import logging
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TokenStorage(ABC):
    """토큰 저장소 추상 클래스

    모든 토큰 저장소는 이 인터페이스를 구현해야 합니다.
    """

    @abstractmethod
    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """토큰 데이터를 저장합니다.

        Args:
            token_data: 토큰 정보를 담은 딕셔너리
                - access_token: JWT 토큰
                - access_token_token_expired: 만료 시각 (문자열)
                - timestamp: 만료 시각 (Unix epoch)
                - api_key: API Key
                - api_secret: API Secret

        Returns:
            bool: 저장 성공 여부
        """
        pass

    @abstractmethod
    def load_token(self, api_key: str, api_secret: str) -> Optional[Dict[str, Any]]:
        """저장된 토큰을 로드합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            Optional[Dict[str, Any]]: 토큰 데이터 (없거나 만료된 경우 None)
        """
        pass

    @abstractmethod
    def check_token_valid(self, api_key: str, api_secret: str) -> bool:
        """토큰의 유효성을 확인합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            bool: 토큰이 존재하고 유효한 경우 True
        """
        pass

    @abstractmethod
    def delete_token(self, api_key: str, api_secret: str) -> bool:
        """토큰을 삭제합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            bool: 삭제 성공 여부
        """
        pass


class FileTokenStorage(TokenStorage):
    """파일 기반 토큰 저장소

    토큰을 로컬 파일 시스템에 Pickle 형식으로 저장합니다.
    기존 구현과의 하위 호환성을 제공합니다.
    """

    def __init__(self, file_path: Optional[Path] = None):
        """FileTokenStorage 초기화

        Args:
            file_path: 토큰 파일 경로 (기본값: ~/.cache/kis/token.key)
        """
        self.token_file = file_path or Path("~/.cache/kis/token.key").expanduser()

    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """토큰을 Pickle 파일로 저장합니다.

        Args:
            token_data: 토큰 정보

        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 디렉토리가 없으면 생성
            self.token_file.parent.mkdir(parents=True, exist_ok=True)

            with self.token_file.open("wb") as f:
                pickle.dump(token_data, f)

            logger.debug(f"토큰이 파일에 저장되었습니다: {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"토큰 파일 저장 실패: {e}")
            return False

    def load_token(self, api_key: str, api_secret: str) -> Optional[Dict[str, Any]]:
        """파일에서 토큰을 로드하고 검증합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            Optional[Dict[str, Any]]: 유효한 토큰 데이터 또는 None
        """
        if not self.check_token_valid(api_key, api_secret):
            return None

        try:
            with self.token_file.open("rb") as f:
                data = pickle.load(f)

            logger.debug(f"토큰이 파일에서 로드되었습니다: {self.token_file}")
            return data
        except Exception as e:
            logger.error(f"토큰 파일 로드 실패: {e}")
            return None

    def check_token_valid(self, api_key: str, api_secret: str) -> bool:
        """파일 기반 토큰의 유효성을 확인합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            bool: 토큰이 존재하고 유효한 경우 True
        """
        # 파일 존재 여부 확인
        if not self.token_file.exists():
            logger.debug(f"토큰 파일이 존재하지 않습니다: {self.token_file}")
            return False

        try:
            with self.token_file.open("rb") as f:
                data = pickle.load(f)
        except Exception as e:
            logger.error(f"토큰 파일 읽기 실패: {e}")
            return False

        # API Key/Secret 확인
        if (data.get('api_key') != api_key) or (data.get('api_secret') != api_secret):
            logger.debug("API Key 또는 Secret이 일치하지 않습니다")
            return False

        # 만료 시각 확인
        ts_now = int(datetime.now().timestamp())
        timestamp = data.get('timestamp', 0)

        if ts_now >= timestamp:
            logger.debug("토큰이 만료되었습니다")
            return False

        return True

    def delete_token(self, api_key: str, api_secret: str) -> bool:
        """토큰 파일을 삭제합니다.

        Args:
            api_key: API Key (사용되지 않음, 인터페이스 일관성 유지)
            api_secret: API Secret (사용되지 않음, 인터페이스 일관성 유지)

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                logger.debug(f"토큰 파일이 삭제되었습니다: {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"토큰 파일 삭제 실패: {e}")
            return False


class RedisTokenStorage(TokenStorage):
    """Redis 기반 토큰 저장소

    토큰을 Redis에 저장하여 분산 환경과 멀티 프로세스 환경을 지원합니다.
    Redis TTL 기능을 사용하여 만료된 토큰을 자동으로 삭제합니다.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        password: Optional[str] = None,
        key_prefix: str = "korea_investment:token"
    ):
        """RedisTokenStorage 초기화

        Args:
            redis_url: Redis 연결 URL (예: redis://localhost:6379/0)
            password: Redis 인증 비밀번호 (선택 사항)
            key_prefix: Redis 키 프리픽스

        Raises:
            ImportError: redis 패키지가 설치되지 않은 경우
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis 저장소를 사용하려면 redis 패키지가 필요합니다.\n"
                "설치: pip install korea-investment-stock[redis]"
            )

        # Redis URL에 비밀번호가 없고 password 파라미터가 제공된 경우
        if password and '@' not in redis_url:
            # redis://host:port/db → redis://:password@host:port/db
            parts = redis_url.split('//')
            protocol = parts[0]
            rest = parts[1]
            redis_url = f"{protocol}//:{password}@{rest}"

        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # 연결 테스트
            self.redis_client.ping()
            logger.debug(f"Redis 연결 성공: {redis_url}")
        except Exception as e:
            raise ConnectionError(f"Redis 서버 연결 실패: {e}")

        self.key_prefix = key_prefix

    def _get_redis_key(self, api_key: str) -> str:
        """API Key로부터 Redis 키를 생성합니다.

        Args:
            api_key: API Key

        Returns:
            str: Redis 키 (예: korea_investment:token:abc123def456)
        """
        # API Key의 SHA-256 해시 생성 (앞 12자리만 사용)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:12]
        return f"{self.key_prefix}:{key_hash}"

    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """토큰을 Redis Hash로 저장하고 TTL을 설정합니다.

        Args:
            token_data: 토큰 정보

        Returns:
            bool: 저장 성공 여부
        """
        try:
            redis_key = self._get_redis_key(token_data['api_key'])

            # Hash 저장
            self.redis_client.hset(
                redis_key,
                mapping={
                    'access_token': token_data['access_token'],
                    'access_token_token_expired': token_data['access_token_token_expired'],
                    'timestamp': str(token_data['timestamp']),
                    'api_key': token_data['api_key'],
                    'api_secret': token_data['api_secret']
                }
            )

            # TTL 설정 (만료 시각까지 남은 시간)
            ts_now = int(datetime.now().timestamp())
            ttl = token_data['timestamp'] - ts_now
            if ttl > 0:
                self.redis_client.expire(redis_key, ttl)
                logger.debug(f"토큰이 Redis에 저장되었습니다 (TTL: {ttl}초): {redis_key}")
            else:
                logger.warning(f"토큰이 이미 만료되었습니다 (TTL: {ttl}초)")

            return True
        except Exception as e:
            logger.error(f"Redis 토큰 저장 실패: {e}")
            return False

    def load_token(self, api_key: str, api_secret: str) -> Optional[Dict[str, Any]]:
        """Redis에서 토큰을 로드합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            Optional[Dict[str, Any]]: 유효한 토큰 데이터 또는 None
        """
        if not self.check_token_valid(api_key, api_secret):
            return None

        try:
            redis_key = self._get_redis_key(api_key)
            data = self.redis_client.hgetall(redis_key)

            if not data:
                logger.debug(f"Redis에 토큰이 존재하지 않습니다: {redis_key}")
                return None

            # 타입 변환 (Redis는 모든 값을 문자열로 저장)
            result = {
                'access_token': data['access_token'],
                'access_token_token_expired': data['access_token_token_expired'],
                'timestamp': int(data['timestamp']),
                'api_key': data['api_key'],
                'api_secret': data['api_secret']
            }

            logger.debug(f"토큰이 Redis에서 로드되었습니다: {redis_key}")
            return result
        except Exception as e:
            logger.error(f"Redis 토큰 로드 실패: {e}")
            return None

    def check_token_valid(self, api_key: str, api_secret: str) -> bool:
        """Redis 토큰의 유효성을 확인합니다.

        Args:
            api_key: API Key
            api_secret: API Secret

        Returns:
            bool: 토큰이 존재하고 유효한 경우 True
        """
        try:
            redis_key = self._get_redis_key(api_key)

            # 키 존재 확인
            if not self.redis_client.exists(redis_key):
                logger.debug(f"Redis에 토큰이 존재하지 않습니다: {redis_key}")
                return False

            # 데이터 로드
            data = self.redis_client.hgetall(redis_key)

            # API Secret 확인
            if data.get('api_secret') != api_secret:
                logger.debug("API Secret이 일치하지 않습니다")
                return False

            # 만료 시각 확인 (이중 체크: TTL과 timestamp)
            ts_now = int(datetime.now().timestamp())
            timestamp = int(data.get('timestamp', 0))

            if ts_now >= timestamp:
                logger.debug("토큰이 만료되었습니다")
                return False

            return True

        except Exception as e:
            logger.error(f"Redis 토큰 확인 실패: {e}")
            return False

    def delete_token(self, api_key: str, api_secret: str) -> bool:
        """Redis에서 토큰을 삭제합니다.

        Args:
            api_key: API Key
            api_secret: API Secret (사용되지 않음, 인터페이스 일관성 유지)

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            redis_key = self._get_redis_key(api_key)
            self.redis_client.delete(redis_key)
            logger.debug(f"토큰이 Redis에서 삭제되었습니다: {redis_key}")
            return True
        except Exception as e:
            logger.error(f"Redis 토큰 삭제 실패: {e}")
            return False
