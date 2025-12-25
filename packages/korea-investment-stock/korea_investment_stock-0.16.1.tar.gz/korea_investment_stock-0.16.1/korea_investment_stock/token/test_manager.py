"""TokenManager 단위 테스트"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from .manager import TokenManager
from .storage import TokenStorage


class TestTokenManager:
    """TokenManager 테스트"""

    @pytest.fixture
    def mock_storage(self):
        """Mock TokenStorage"""
        return Mock(spec=TokenStorage)

    @pytest.fixture
    def token_manager(self, mock_storage):
        """TokenManager 인스턴스"""
        return TokenManager(
            storage=mock_storage,
            base_url="https://openapi.koreainvestment.com:9443",
            api_key="test-key",
            api_secret="test-secret"
        )

    def test_init(self, token_manager, mock_storage):
        """초기화 테스트"""
        assert token_manager.storage == mock_storage
        assert token_manager.base_url == "https://openapi.koreainvestment.com:9443"
        assert token_manager.api_key == "test-key"
        assert token_manager.api_secret == "test-secret"
        assert token_manager._access_token is None

    def test_access_token_property(self, token_manager):
        """access_token 프로퍼티 테스트"""
        assert token_manager.access_token is None
        token_manager._access_token = "Bearer test-token"
        assert token_manager.access_token == "Bearer test-token"

    def test_get_valid_token_when_valid(self, token_manager, mock_storage):
        """유효한 토큰이 있으면 로드"""
        mock_storage.check_token_valid.return_value = True
        mock_storage.load_token.return_value = {
            "access_token": "existing-token"
        }

        token = token_manager.get_valid_token()

        assert token == "Bearer existing-token"
        mock_storage.check_token_valid.assert_called_once_with("test-key", "test-secret")
        mock_storage.load_token.assert_called_once_with("test-key", "test-secret")

    def test_get_valid_token_when_already_loaded(self, token_manager, mock_storage):
        """이미 로드된 토큰이 있으면 재사용"""
        mock_storage.check_token_valid.return_value = True
        token_manager._access_token = "Bearer already-loaded"

        token = token_manager.get_valid_token()

        assert token == "Bearer already-loaded"
        mock_storage.check_token_valid.assert_called_once()
        mock_storage.load_token.assert_not_called()  # 이미 로드됨

    @patch('requests.post')
    def test_get_valid_token_when_invalid(self, mock_post, token_manager, mock_storage):
        """토큰 만료시 새로 발급"""
        mock_storage.check_token_valid.return_value = False
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-token",
            "access_token_token_expired": "2025-12-31 23:59:59"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        token = token_manager.get_valid_token()

        assert token == "Bearer new-token"
        mock_storage.save_token.assert_called_once()
        saved_data = mock_storage.save_token.call_args[0][0]
        assert saved_data["access_token"] == "new-token"
        assert saved_data["api_key"] == "test-key"
        assert saved_data["api_secret"] == "test-secret"
        assert "timestamp" in saved_data

    def test_is_token_valid(self, token_manager, mock_storage):
        """토큰 유효성 확인"""
        mock_storage.check_token_valid.return_value = True

        result = token_manager.is_token_valid()

        assert result is True
        mock_storage.check_token_valid.assert_called_with("test-key", "test-secret")

    def test_is_token_invalid(self, token_manager, mock_storage):
        """토큰 무효 확인"""
        mock_storage.check_token_valid.return_value = False

        result = token_manager.is_token_valid()

        assert result is False

    def test_load_token(self, token_manager, mock_storage):
        """토큰 로드 테스트"""
        mock_storage.load_token.return_value = {
            "access_token": "loaded-token"
        }

        token_manager._load_token()

        assert token_manager._access_token == "Bearer loaded-token"

    def test_load_token_when_none(self, token_manager, mock_storage):
        """토큰이 없을 때 로드 테스트"""
        mock_storage.load_token.return_value = None

        token_manager._load_token()

        assert token_manager._access_token is None

    @patch('requests.post')
    def test_issue_token(self, mock_post, token_manager, mock_storage):
        """토큰 발급 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "issued-token",
            "access_token_token_expired": "2025-12-31 23:59:59"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        token_manager._issue_token()

        assert token_manager._access_token == "Bearer issued-token"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "oauth2/tokenP" in call_args[0][0]
        assert call_args[1]["json"]["appkey"] == "test-key"
        assert call_args[1]["json"]["appsecret"] == "test-secret"

    def test_parse_token_response(self, token_manager):
        """토큰 응답 파싱 테스트"""
        resp_data = {
            "access_token": "test-token",
            "access_token_token_expired": "2025-12-31 23:59:59"
        }

        result = token_manager._parse_token_response(resp_data)

        assert result["access_token"] == "test-token"
        assert result["api_key"] == "test-key"
        assert result["api_secret"] == "test-secret"
        assert "timestamp" in result
        assert isinstance(result["timestamp"], int)

    @patch('requests.post')
    def test_issue_hashkey(self, mock_post, token_manager):
        """해쉬키 발급 테스트"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"HASH": "abc123hash"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        data = {"ORD_QTY": "10", "ORD_UNPR": "50000"}
        result = token_manager.issue_hashkey(data)

        assert result == "abc123hash"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "uapi/hashkey" in call_args[0][0]

    def test_invalidate(self, token_manager, mock_storage):
        """토큰 무효화 테스트"""
        token_manager._access_token = "Bearer some-token"
        mock_storage.delete_token.return_value = True

        result = token_manager.invalidate()

        assert result is True
        assert token_manager._access_token is None
        mock_storage.delete_token.assert_called_once_with("test-key", "test-secret")

    def test_invalidate_when_no_token(self, token_manager, mock_storage):
        """토큰 없을 때 무효화 테스트"""
        mock_storage.delete_token.return_value = False

        result = token_manager.invalidate()

        assert result is False
        assert token_manager._access_token is None


class TestTokenManagerConstants:
    """TokenManager 상수 테스트"""

    def test_oauth_path(self):
        """OAUTH_PATH 상수 테스트"""
        assert TokenManager.OAUTH_PATH == "oauth2/tokenP"

    def test_hashkey_path(self):
        """HASHKEY_PATH 상수 테스트"""
        assert TokenManager.HASHKEY_PATH == "uapi/hashkey"
