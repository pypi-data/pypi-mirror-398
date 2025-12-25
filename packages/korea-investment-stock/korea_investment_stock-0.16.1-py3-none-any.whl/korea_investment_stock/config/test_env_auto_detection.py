"""환경 변수 자동 감지 테스트

Phase 1 (v0.9.0): 환경 변수 자동 감지 기능 검증
- 환경 변수만으로 초기화
- 생성자 파라미터 우선순위
- 혼합 사용 (일부 파라미터 + 환경변수)
- 필수값 누락 시 에러 메시지
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from korea_investment_stock import KoreaInvestment


class TestEnvAutoDetection:
    """환경 변수 자동 감지 테스트"""

    @pytest.fixture
    def mock_token_storage(self):
        """토큰 저장소 mock"""
        mock_storage = MagicMock()
        mock_storage.check_token_valid.return_value = True
        mock_storage.load_token.return_value = {
            "access_token": "test_token_12345"
        }
        return mock_storage

    def test_init_with_env_vars_only(self, mock_token_storage, monkeypatch):
        """환경 변수만으로 초기화 테스트"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-api-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-api-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")

        # 파라미터 없이 초기화
        broker = KoreaInvestment(token_storage=mock_token_storage)

        # 검증
        assert broker.api_key == "env-api-key"
        assert broker.api_secret == "env-api-secret"
        assert broker.acc_no == "12345678-01"

    def test_init_with_constructor_params(self, mock_token_storage, monkeypatch):
        """생성자 파라미터로 초기화 테스트"""
        # 환경 변수 설정 (사용되지 않아야 함)
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-api-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-api-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "99999999-99")

        # 생성자 파라미터로 초기화
        broker = KoreaInvestment(
            api_key="param-api-key",
            api_secret="param-api-secret",
            acc_no="12345678-01",
            token_storage=mock_token_storage
        )

        # 생성자 파라미터가 우선
        assert broker.api_key == "param-api-key"
        assert broker.api_secret == "param-api-secret"
        assert broker.acc_no == "12345678-01"

    def test_priority_constructor_over_env(self, mock_token_storage, monkeypatch):
        """생성자 파라미터가 환경 변수보다 우선순위 테스트"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "99999999-99")

        # 생성자 파라미터로 override
        broker = KoreaInvestment(
            api_key="constructor-key",
            api_secret="constructor-secret",
            acc_no="12345678-01",
            token_storage=mock_token_storage
        )

        # 생성자 파라미터가 우선
        assert broker.api_key == "constructor-key"
        assert broker.api_secret == "constructor-secret"
        assert broker.acc_no == "12345678-01"

    def test_mixed_usage_partial_override(self, mock_token_storage, monkeypatch):
        """혼합 사용 테스트 - 일부만 override"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")

        # api_key만 override
        broker = KoreaInvestment(
            api_key="override-key",
            token_storage=mock_token_storage
        )

        # override된 것만 변경
        assert broker.api_key == "override-key"
        assert broker.api_secret == "env-secret"
        assert broker.acc_no == "12345678-01"

    def test_missing_all_credentials_error(self, monkeypatch):
        """모든 필수값 누락 시 에러 테스트"""
        # 환경 변수 제거
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        # 에러 발생 확인
        with pytest.raises(ValueError) as exc_info:
            KoreaInvestment()

        error_msg = str(exc_info.value)
        assert "API credentials required" in error_msg
        assert "api_key (KOREA_INVESTMENT_API_KEY)" in error_msg
        assert "api_secret (KOREA_INVESTMENT_API_SECRET)" in error_msg
        assert "acc_no (KOREA_INVESTMENT_ACCOUNT_NO)" in error_msg

    def test_missing_partial_credentials_error(self, monkeypatch):
        """일부 필수값 누락 시 에러 테스트"""
        # api_key만 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        # 에러 발생 확인
        with pytest.raises(ValueError) as exc_info:
            KoreaInvestment()

        error_msg = str(exc_info.value)
        assert "api_key (KOREA_INVESTMENT_API_KEY)" not in error_msg  # 설정됨
        assert "api_secret (KOREA_INVESTMENT_API_SECRET)" in error_msg  # 누락
        assert "acc_no (KOREA_INVESTMENT_ACCOUNT_NO)" in error_msg  # 누락

    def test_invalid_acc_no_format(self, mock_token_storage, monkeypatch):
        """잘못된 계좌번호 형식 테스트"""
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678")  # - 없음

        with pytest.raises(ValueError) as exc_info:
            KoreaInvestment(token_storage=mock_token_storage)

        assert "계좌번호 형식이 올바르지 않습니다" in str(exc_info.value)

    def test_invalid_acc_no_parts(self, mock_token_storage, monkeypatch):
        """잘못된 계좌번호 부분 형식 테스트"""
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "1234-567")  # 앞 4자리, 뒤 3자리

        with pytest.raises(ValueError) as exc_info:
            KoreaInvestment(token_storage=mock_token_storage)

        assert "앞 8자리-뒤 2자리" in str(exc_info.value)

    def test_empty_string_treated_as_none(self, monkeypatch):
        """빈 문자열은 None처럼 처리되는지 테스트"""
        # 빈 문자열 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "")

        # 에러 발생 확인 (빈 문자열도 누락으로 처리)
        with pytest.raises(ValueError) as exc_info:
            KoreaInvestment()

        error_msg = str(exc_info.value)
        assert "API credentials required" in error_msg


class TestBackwardCompatibility:
    """하위 호환성 테스트"""

    @pytest.fixture
    def mock_token_storage(self):
        """토큰 저장소 mock"""
        mock_storage = MagicMock()
        mock_storage.check_token_valid.return_value = True
        mock_storage.load_token.return_value = {
            "access_token": "test_token_12345"
        }
        return mock_storage

    def test_existing_usage_still_works(self, mock_token_storage, monkeypatch):
        """기존 사용 방식이 여전히 동작하는지 테스트

        기존 코드:
            api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
            api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
            acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')
            broker = KoreaInvestment(api_key, api_secret, acc_no)
        """
        # 환경 변수에서 직접 읽어서 전달 (기존 방식)
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "existing-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "existing-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")

        api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
        api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
        acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

        broker = KoreaInvestment(
            api_key=api_key,
            api_secret=api_secret,
            acc_no=acc_no,
            token_storage=mock_token_storage
        )

        assert broker.api_key == "existing-key"
        assert broker.api_secret == "existing-secret"
        assert broker.acc_no == "12345678-01"

    def test_positional_args_still_work(self, mock_token_storage):
        """위치 인자가 여전히 동작하는지 테스트

        기존 코드:
            broker = KoreaInvestment(key, secret, acc_no)

        Note: Phase 3에서 config, config_file 파라미터가 추가되어
              token_storage는 키워드 인자로 전달해야 합니다.
        """
        broker = KoreaInvestment(
            "positional-key",
            "positional-secret",
            "12345678-01",
            token_storage=mock_token_storage
        )

        assert broker.api_key == "positional-key"
        assert broker.api_secret == "positional-secret"
        assert broker.acc_no == "12345678-01"
