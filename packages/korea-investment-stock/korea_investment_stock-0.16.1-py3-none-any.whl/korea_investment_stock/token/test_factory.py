"""create_token_storage 팩토리 테스트"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from .factory import create_token_storage, _get_config_value
from .storage import FileTokenStorage, RedisTokenStorage


class TestCreateTokenStorage:
    """create_token_storage 팩토리 테스트"""

    def test_default_file_storage(self):
        """기본값은 FileTokenStorage"""
        storage = create_token_storage()
        assert isinstance(storage, FileTokenStorage)

    def test_config_file_storage(self):
        """config로 file 저장소 생성"""
        config = {"token_storage_type": "file"}
        storage = create_token_storage(config)
        assert isinstance(storage, FileTokenStorage)

    def test_config_file_storage_uppercase(self):
        """대문자 타입도 처리"""
        config = {"token_storage_type": "FILE"}
        storage = create_token_storage(config)
        assert isinstance(storage, FileTokenStorage)

    def test_config_file_storage_with_path(self):
        """파일 경로 지정"""
        config = {
            "token_storage_type": "file",
            "token_file": "/tmp/test_token.key"
        }
        storage = create_token_storage(config)
        assert isinstance(storage, FileTokenStorage)
        assert storage.token_file == Path("/tmp/test_token.key")

    def test_config_file_storage_with_expanduser(self):
        """~/ 경로 확장"""
        config = {
            "token_storage_type": "file",
            "token_file": "~/.cache/test_token.key"
        }
        storage = create_token_storage(config)
        assert isinstance(storage, FileTokenStorage)
        assert str(storage.token_file).startswith(str(Path.home()))

    @patch.dict(os.environ, {}, clear=False)
    @patch('korea_investment_stock.token.factory.RedisTokenStorage')
    def test_config_redis_storage(self, mock_redis_cls):
        """config로 redis 저장소 생성"""
        # 환경변수에서 redis_password 제거
        os.environ.pop("KOREA_INVESTMENT_REDIS_PASSWORD", None)

        mock_redis_cls.return_value = MagicMock(spec=RedisTokenStorage)

        config = {
            "token_storage_type": "redis",
            "redis_url": "redis://localhost:6379/0"
        }
        storage = create_token_storage(config)

        mock_redis_cls.assert_called_once_with(
            "redis://localhost:6379/0",
            password=None
        )

    @patch('korea_investment_stock.token.factory.RedisTokenStorage')
    def test_config_redis_storage_with_password(self, mock_redis_cls):
        """Redis 비밀번호 지정"""
        mock_redis_cls.return_value = MagicMock(spec=RedisTokenStorage)

        config = {
            "token_storage_type": "redis",
            "redis_url": "redis://localhost:6379/0",
            "redis_password": "secret123"
        }
        storage = create_token_storage(config)

        mock_redis_cls.assert_called_once_with(
            "redis://localhost:6379/0",
            password="secret123"
        )

    def test_invalid_storage_type(self):
        """지원하지 않는 저장소 타입"""
        config = {"token_storage_type": "mongodb"}
        with pytest.raises(ValueError, match="지원하지 않는 저장소 타입"):
            create_token_storage(config)

    def test_invalid_storage_type_error_message(self):
        """에러 메시지에 올바른 타입 안내 포함"""
        config = {"token_storage_type": "mysql"}
        with pytest.raises(ValueError) as exc_info:
            create_token_storage(config)
        assert "mysql" in str(exc_info.value)
        assert "file" in str(exc_info.value)
        assert "redis" in str(exc_info.value)

    @patch.dict(os.environ, {"KOREA_INVESTMENT_TOKEN_STORAGE_TYPE": "file"})
    def test_env_var_storage_type(self):
        """환경변수에서 저장소 타입 읽기"""
        storage = create_token_storage()
        assert isinstance(storage, FileTokenStorage)

    @patch.dict(os.environ, {"KOREA_INVESTMENT_TOKEN_FILE": "/tmp/env_token.key"})
    def test_env_var_token_file(self):
        """환경변수에서 토큰 파일 경로 읽기"""
        storage = create_token_storage()
        assert isinstance(storage, FileTokenStorage)
        assert storage.token_file == Path("/tmp/env_token.key")

    def test_config_overrides_env_var(self):
        """config가 환경변수보다 우선"""
        with patch.dict(os.environ, {"KOREA_INVESTMENT_TOKEN_FILE": "/tmp/env.key"}):
            config = {"token_file": "/tmp/config.key"}
            storage = create_token_storage(config)
            assert storage.token_file == Path("/tmp/config.key")

    def test_none_config(self):
        """config가 None일 때 기본값 사용"""
        storage = create_token_storage(None)
        assert isinstance(storage, FileTokenStorage)

    def test_empty_config(self):
        """빈 config일 때 기본값 사용"""
        storage = create_token_storage({})
        assert isinstance(storage, FileTokenStorage)


class TestGetConfigValue:
    """_get_config_value 헬퍼 테스트"""

    def test_config_value(self):
        """config에서 값 읽기"""
        config = {"my_key": "my_value"}
        result = _get_config_value(config, "my_key")
        assert result == "my_value"

    def test_env_var_value(self):
        """환경변수에서 값 읽기"""
        with patch.dict(os.environ, {"KOREA_INVESTMENT_MY_KEY": "env_value"}):
            result = _get_config_value(None, "my_key")
            assert result == "env_value"

    def test_default_value(self):
        """기본값 반환"""
        result = _get_config_value(None, "nonexistent_key", "default")
        assert result == "default"

    def test_config_priority_over_env(self):
        """config가 환경변수보다 우선"""
        with patch.dict(os.environ, {"KOREA_INVESTMENT_MY_KEY": "env_value"}):
            config = {"my_key": "config_value"}
            result = _get_config_value(config, "my_key")
            assert result == "config_value"

    def test_empty_string_in_config(self):
        """빈 문자열은 환경변수로 폴백"""
        with patch.dict(os.environ, {"KOREA_INVESTMENT_MY_KEY": "env_value"}):
            config = {"my_key": ""}
            result = _get_config_value(config, "my_key")
            assert result == "env_value"

    def test_none_in_config(self):
        """None은 환경변수로 폴백"""
        with patch.dict(os.environ, {"KOREA_INVESTMENT_MY_KEY": "env_value"}):
            config = {"my_key": None}
            result = _get_config_value(config, "my_key")
            assert result == "env_value"
