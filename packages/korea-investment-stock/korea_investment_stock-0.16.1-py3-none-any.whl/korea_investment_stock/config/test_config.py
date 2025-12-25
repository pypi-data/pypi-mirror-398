"""Config 클래스 단위 테스트

Phase 2 (v1.0.0): Config 클래스 기능 검증
- 환경 변수 로딩
- YAML 파일 로딩
- 유효성 검증
- 직렬화/역직렬화
"""

import os
import pytest
from pathlib import Path

from korea_investment_stock import Config


class TestConfigBasic:
    """Config 기본 기능 테스트"""

    def test_config_creation(self):
        """기본 Config 생성 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01"
        )

        assert config.api_key == "test-api-key"
        assert config.api_secret == "test-api-secret"
        assert config.acc_no == "12345678-01"
        assert config.token_storage_type == "file"  # 기본값
        assert config.redis_url == "redis://localhost:6379/0"  # 기본값

    def test_config_with_all_options(self):
        """모든 옵션으로 Config 생성 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01",
            token_storage_type="redis",
            redis_url="redis://custom:6380/1",
            redis_password="secret",
            token_file="/custom/path/token.key"
        )

        assert config.token_storage_type == "redis"
        assert config.redis_url == "redis://custom:6380/1"
        assert config.redis_password == "secret"
        assert config.token_file == Path("/custom/path/token.key")

    def test_token_file_path_expansion(self):
        """토큰 파일 경로 확장 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01",
            token_file="~/custom/token.key"
        )

        # ~ 확장됨
        assert str(config.token_file).startswith("/")
        assert "~" not in str(config.token_file)

    def test_default_token_file(self):
        """기본 토큰 파일 경로 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01"
        )

        assert config.token_file is not None
        assert "token.key" in str(config.token_file)


class TestConfigValidation:
    """Config 유효성 검증 테스트"""

    def test_invalid_acc_no_no_dash(self):
        """계좌번호 형식 오류 (대시 없음)"""
        with pytest.raises(ValueError) as exc_info:
            Config(
                api_key="test-api-key",
                api_secret="test-api-secret",
                acc_no="1234567801"
            )

        assert "계좌번호 형식" in str(exc_info.value)

    def test_invalid_acc_no_wrong_format(self):
        """계좌번호 형식 오류 (잘못된 자릿수)"""
        with pytest.raises(ValueError) as exc_info:
            Config(
                api_key="test-api-key",
                api_secret="test-api-secret",
                acc_no="1234-5678"
            )

        assert "앞 8자리-뒤 2자리" in str(exc_info.value)

    def test_invalid_token_storage_type(self):
        """지원하지 않는 토큰 저장소 타입"""
        with pytest.raises(ValueError) as exc_info:
            Config(
                api_key="test-api-key",
                api_secret="test-api-secret",
                acc_no="12345678-01",
                token_storage_type="mysql"
            )

        assert "지원하지 않는 저장소 타입" in str(exc_info.value)


class TestConfigFromEnv:
    """환경 변수 로딩 테스트"""

    def test_from_env_success(self, monkeypatch):
        """환경 변수에서 성공적으로 로드"""
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-api-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-api-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")

        config = Config.from_env()

        assert config.api_key == "env-api-key"
        assert config.api_secret == "env-api-secret"
        assert config.acc_no == "12345678-01"

    def test_from_env_with_optional(self, monkeypatch):
        """환경 변수에서 선택 옵션 포함 로드"""
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-api-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-api-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")
        monkeypatch.setenv("KOREA_INVESTMENT_TOKEN_STORAGE", "redis")
        monkeypatch.setenv("KOREA_INVESTMENT_REDIS_URL", "redis://custom:6380/1")

        config = Config.from_env()

        assert config.token_storage_type == "redis"
        assert config.redis_url == "redis://custom:6380/1"

    def test_from_env_missing_required(self, monkeypatch):
        """필수 환경 변수 누락"""
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        with pytest.raises(KeyError) as exc_info:
            Config.from_env()

        assert "KOREA_INVESTMENT_API_KEY" in str(exc_info.value)

    def test_from_env_partial_missing(self, monkeypatch):
        """일부 환경 변수 누락"""
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-api-key")
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        with pytest.raises(KeyError) as exc_info:
            Config.from_env()

        error_msg = str(exc_info.value)
        assert "KOREA_INVESTMENT_API_SECRET" in error_msg
        assert "KOREA_INVESTMENT_ACCOUNT_NO" in error_msg


class TestConfigFromYaml:
    """YAML 파일 로딩 테스트"""

    def test_from_yaml_success(self, tmp_path):
        """YAML 파일에서 성공적으로 로드"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: yaml-api-key
api_secret: yaml-api-secret
acc_no: "12345678-01"
""")

        config = Config.from_yaml(config_file)

        assert config.api_key == "yaml-api-key"
        assert config.api_secret == "yaml-api-secret"
        assert config.acc_no == "12345678-01"

    def test_from_yaml_with_all_options(self, tmp_path):
        """모든 옵션이 포함된 YAML 파일 로드"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: yaml-api-key
api_secret: yaml-api-secret
acc_no: "12345678-01"
token_storage_type: redis
redis_url: redis://custom:6380/1
redis_password: secret
token_file: ~/.cache/custom/token.key
""")

        config = Config.from_yaml(config_file)

        assert config.token_storage_type == "redis"
        assert config.redis_url == "redis://custom:6380/1"
        assert config.redis_password == "secret"

    def test_from_yaml_file_not_found(self):
        """존재하지 않는 파일"""
        with pytest.raises(FileNotFoundError) as exc_info:
            Config.from_yaml("/non/existent/config.yaml")

        assert "설정 파일을 찾을 수 없습니다" in str(exc_info.value)

    def test_from_yaml_empty_file(self, tmp_path):
        """빈 YAML 파일"""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        with pytest.raises(ValueError) as exc_info:
            Config.from_yaml(config_file)

        assert "빈 설정 파일" in str(exc_info.value)

    def test_from_yaml_missing_required(self, tmp_path):
        """필수 필드 누락"""
        config_file = tmp_path / "incomplete.yaml"
        config_file.write_text("""
api_key: yaml-api-key
""")

        with pytest.raises(ValueError) as exc_info:
            Config.from_yaml(config_file)

        assert "필수 필드가 누락" in str(exc_info.value)

    def test_from_yaml_path_expansion(self, tmp_path):
        """~ 경로 확장 테스트"""
        # 실제 홈 디렉터리에 테스트 파일 생성 대신 tmp_path 사용
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: yaml-api-key
api_secret: yaml-api-secret
acc_no: "12345678-01"
""")

        # 상대 경로로 테스트
        config = Config.from_yaml(str(config_file))
        assert config.api_key == "yaml-api-key"


class TestConfigSerialization:
    """직렬화/역직렬화 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01",
            token_storage_type="file"
        )

        result = config.to_dict()

        assert result['api_key'] == "test-api-key"
        assert result['api_secret'] == "test-api-secret"
        assert result['acc_no'] == "12345678-01"
        assert result['token_storage_type'] == "file"
        assert isinstance(result['token_file'], str)  # Path -> str 변환됨

    def test_to_yaml_string(self):
        """YAML 문자열 변환 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01"
        )

        yaml_str = config.to_yaml()

        assert "api_key: test-api-key" in yaml_str
        assert "api_secret: test-api-secret" in yaml_str
        assert "acc_no: '12345678-01'" in yaml_str or "acc_no: 12345678-01" in yaml_str

    def test_to_yaml_file(self, tmp_path):
        """YAML 파일 저장 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01"
        )

        output_file = tmp_path / "output.yaml"
        config.to_yaml(output_file)

        assert output_file.exists()

        # 저장된 파일 다시 로드
        loaded_config = Config.from_yaml(output_file)
        assert loaded_config.api_key == config.api_key
        assert loaded_config.acc_no == config.acc_no

    def test_to_yaml_creates_parent_dirs(self, tmp_path):
        """부모 디렉터리 자동 생성 테스트"""
        config = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01"
        )

        output_file = tmp_path / "nested" / "dir" / "config.yaml"
        config.to_yaml(output_file)

        assert output_file.exists()


class TestConfigRepr:
    """문자열 표현 테스트"""

    def test_repr_masks_sensitive_data(self):
        """민감한 정보 마스킹"""
        config = Config(
            api_key="my-secret-api-key",
            api_secret="my-secret-api-secret",
            acc_no="12345678-01"
        )

        repr_str = repr(config)

        # API key/secret의 마지막 4자리만 표시
        assert "my-secret-api-key" not in repr_str
        assert "my-secret-api-secret" not in repr_str
        assert "***" in repr_str
        # 계좌번호는 표시
        assert "12345678-01" in repr_str


class TestConfigRoundTrip:
    """왕복 변환 테스트"""

    def test_yaml_roundtrip(self, tmp_path):
        """YAML 저장 → 로드 왕복 테스트"""
        original = Config(
            api_key="test-api-key",
            api_secret="test-api-secret",
            acc_no="12345678-01",
            token_storage_type="redis",
            redis_url="redis://custom:6380/1"
        )

        # 저장
        config_file = tmp_path / "roundtrip.yaml"
        original.to_yaml(config_file)

        # 로드
        loaded = Config.from_yaml(config_file)

        # 비교
        assert loaded.api_key == original.api_key
        assert loaded.api_secret == original.api_secret
        assert loaded.acc_no == original.acc_no
        assert loaded.token_storage_type == original.token_storage_type
        assert loaded.redis_url == original.redis_url
