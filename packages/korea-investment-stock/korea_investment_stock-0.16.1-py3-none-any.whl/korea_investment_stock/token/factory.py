"""토큰 저장소 팩토리

설정에 따라 적절한 TokenStorage 인스턴스를 생성합니다.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .storage import TokenStorage, FileTokenStorage, RedisTokenStorage

logger = logging.getLogger(__name__)


def create_token_storage(
    config: Optional[Dict[str, Any]] = None
) -> TokenStorage:
    """설정 기반 토큰 저장소 생성

    우선순위:
    1. config 딕셔너리
    2. 환경 변수 (KOREA_INVESTMENT_*)

    Args:
        config: 설정 딕셔너리 (선택)
            - token_storage_type: "file" 또는 "redis"
            - token_file: 파일 경로 (file 타입)
            - redis_url: Redis URL (redis 타입)
            - redis_password: Redis 비밀번호 (선택)

    Returns:
        TokenStorage: 생성된 저장소 인스턴스

    Raises:
        ValueError: 지원하지 않는 저장소 타입

    Example:
        >>> # 환경 변수 사용
        >>> storage = create_token_storage()

        >>> # 설정 딕셔너리 사용
        >>> storage = create_token_storage({
        ...     "token_storage_type": "redis",
        ...     "redis_url": "redis://localhost:6379/0"
        ... })
    """
    # 설정 로드
    storage_type = _get_config_value(config, "token_storage_type", "file")
    storage_type = storage_type.lower()

    if storage_type == "file":
        return _create_file_storage(config)
    elif storage_type == "redis":
        return _create_redis_storage(config)
    else:
        raise ValueError(
            f"지원하지 않는 저장소 타입: {storage_type}\n"
            f"'file' 또는 'redis'만 지원됩니다."
        )


def _get_config_value(
    config: Optional[Dict[str, Any]],
    key: str,
    default: Optional[str] = None
) -> Optional[str]:
    """설정값 조회 (config -> 환경변수 -> 기본값)"""
    if config and config.get(key):
        return config[key]

    env_key = f"KOREA_INVESTMENT_{key.upper()}"
    return os.getenv(env_key, default)


def _create_file_storage(config: Optional[Dict[str, Any]]) -> FileTokenStorage:
    """파일 기반 저장소 생성"""
    token_file = _get_config_value(config, "token_file")

    file_path = None
    if token_file:
        file_path = Path(token_file).expanduser()

    logger.debug(f"FileTokenStorage 생성: {file_path or '기본 경로'}")
    return FileTokenStorage(file_path)


def _create_redis_storage(config: Optional[Dict[str, Any]]) -> RedisTokenStorage:
    """Redis 기반 저장소 생성"""
    redis_url = _get_config_value(
        config, "redis_url", "redis://localhost:6379/0"
    )
    redis_password = _get_config_value(config, "redis_password")

    logger.debug(f"RedisTokenStorage 생성: {redis_url}")
    return RedisTokenStorage(redis_url, password=redis_password)
