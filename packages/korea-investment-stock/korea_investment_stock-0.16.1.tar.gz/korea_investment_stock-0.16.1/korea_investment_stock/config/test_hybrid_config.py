"""Hybrid Config 통합 테스트

Phase 3 (v1.1.0): ConfigResolver 클래스의 5단계 설정 우선순위 검증
- 생성자 파라미터 > config 객체 > config_file > 환경 변수 > 기본 config 파일

테스트 카테고리:
1. 5단계 우선순위 테스트
2. 기본 경로 자동 탐색 테스트
3. config 객체 주입 테스트
4. 혼합 사용 테스트
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from korea_investment_stock import KoreaInvestment, Config, ConfigResolver


class TestConfigPriority:
    """5단계 우선순위 테스트"""

    def test_priority_1_constructor_params_highest(self, monkeypatch):
        """1단계: 생성자 파라미터가 최고 우선순위"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "11111111-01")

        # config 객체 생성
        config = Config(
            api_key="config-key",
            api_secret="config-secret",
            acc_no="22222222-01"
        )

        # ConfigResolver 사용
        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key="constructor-key",
            api_secret="constructor-secret",
            acc_no="33333333-01",
            config=config,
            config_file=None,
        )

        # 생성자 파라미터가 최고 우선순위
        assert result["api_key"] == "constructor-key"
        assert result["api_secret"] == "constructor-secret"
        assert result["acc_no"] == "33333333-01"

    def test_priority_2_config_object_over_env(self, monkeypatch):
        """2단계: config 객체가 환경 변수보다 우선"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "11111111-01")

        # config 객체 생성
        config = Config(
            api_key="config-key",
            api_secret="config-secret",
            acc_no="22222222-01"
        )

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=config,
            config_file=None,
        )

        # config 객체가 환경 변수보다 우선
        assert result["api_key"] == "config-key"
        assert result["api_secret"] == "config-secret"
        assert result["acc_no"] == "22222222-01"

    def test_priority_3_config_file_over_env(self, monkeypatch, tmp_path):
        """3단계: config_file이 환경 변수보다 우선"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "11111111-01")

        # config 파일 생성
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: file-key
api_secret: file-secret
acc_no: "22222222-01"
""")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=config_file,
        )

        # config_file이 환경 변수보다 우선
        assert result["api_key"] == "file-key"
        assert result["api_secret"] == "file-secret"
        assert result["acc_no"] == "22222222-01"

    def test_priority_4_env_over_default_config(self, monkeypatch, tmp_path):
        """4단계: 환경 변수가 기본 config 파일보다 우선"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "11111111-01")

        # 기본 config 파일 생성
        default_config = tmp_path / "default.yaml"
        default_config.write_text("""
api_key: default-key
api_secret: default-secret
acc_no: "22222222-01"
""")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = [str(default_config)]

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=None,
        )

        # 환경 변수가 기본 config 파일보다 우선
        assert result["api_key"] == "env-key"
        assert result["api_secret"] == "env-secret"
        assert result["acc_no"] == "11111111-01"

    def test_priority_5_default_config_file_lowest(self, monkeypatch, tmp_path):
        """5단계: 기본 config 파일이 가장 낮은 우선순위"""
        # 환경 변수 제거
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        # 기본 config 파일 생성
        default_config = tmp_path / "default.yaml"
        default_config.write_text("""
api_key: default-key
api_secret: default-secret
acc_no: "12345678-01"
""")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = [str(default_config)]

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=None,
        )

        # 기본 config 파일에서 로드
        assert result["api_key"] == "default-key"
        assert result["api_secret"] == "default-secret"
        assert result["acc_no"] == "12345678-01"


class TestDefaultConfigPaths:
    """기본 경로 자동 탐색 테스트"""

    def test_default_config_paths_constant(self):
        """DEFAULT_CONFIG_PATHS 상수가 정의되어 있음"""
        assert hasattr(ConfigResolver, 'DEFAULT_CONFIG_PATHS')
        assert isinstance(ConfigResolver.DEFAULT_CONFIG_PATHS, list)
        assert len(ConfigResolver.DEFAULT_CONFIG_PATHS) >= 1
        assert "~/.config/kis/config.yaml" in ConfigResolver.DEFAULT_CONFIG_PATHS

    def test_load_first_existing_default_config(self, monkeypatch, tmp_path):
        """첫 번째 존재하는 기본 config 파일을 로드"""
        # 환경 변수 제거
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        # 두 번째 파일만 존재하도록 설정
        non_existent = tmp_path / "non_existent.yaml"
        existing_config = tmp_path / "existing.yaml"
        existing_config.write_text("""
api_key: existing-key
api_secret: existing-secret
acc_no: "12345678-01"
""")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = [str(non_existent), str(existing_config)]

        result = resolver._load_default_config_file()

        assert result is not None
        assert result["api_key"] == "existing-key"

    def test_no_default_config_found(self, tmp_path):
        """기본 config 파일이 없으면 None 반환"""
        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = [
            str(tmp_path / "non_existent1.yaml"),
            str(tmp_path / "non_existent2.yaml"),
        ]

        result = resolver._load_default_config_file()
        assert result is None


class TestConfigObjectInjection:
    """config 객체 주입 테스트"""

    def test_config_object_provides_all_settings(self, monkeypatch):
        """Config 객체에서 모든 설정을 가져옴"""
        # 환경 변수 제거
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        config = Config(
            api_key="config-api-key",
            api_secret="config-api-secret",
            acc_no="12345678-01",
            token_storage_type="redis",
            redis_url="redis://custom:6380/1",
        )

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=config,
            config_file=None,
        )

        assert result["api_key"] == "config-api-key"
        assert result["api_secret"] == "config-api-secret"
        assert result["acc_no"] == "12345678-01"
        assert result["token_storage_type"] == "redis"
        assert result["redis_url"] == "redis://custom:6380/1"

    def test_config_from_yaml_integration(self, tmp_path, monkeypatch):
        """Config.from_yaml()로 생성한 객체 주입"""
        # 환경 변수 제거
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        # YAML 파일 생성
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
api_key: yaml-config-key
api_secret: yaml-config-secret
acc_no: "12345678-01"
token_storage_type: file
""")

        # Config.from_yaml()로 로드
        config = Config.from_yaml(yaml_file)

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=config,
            config_file=None,
        )

        assert result["api_key"] == "yaml-config-key"
        assert result["api_secret"] == "yaml-config-secret"
        assert result["acc_no"] == "12345678-01"


class TestMixedUsage:
    """혼합 사용 테스트"""

    def test_partial_override_with_constructor(self, monkeypatch):
        """생성자 파라미터로 일부만 override"""
        # 환경 변수 설정
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "11111111-01")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        # api_key만 override
        result = resolver.resolve(
            api_key="override-key",
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=None,
        )

        assert result["api_key"] == "override-key"  # override됨
        assert result["api_secret"] == "env-secret"  # 환경 변수
        assert result["acc_no"] == "11111111-01"  # 환경 변수

    def test_config_with_partial_constructor_override(self, monkeypatch):
        """Config 객체 + 생성자 파라미터 일부 override"""
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        config = Config(
            api_key="config-key",
            api_secret="config-secret",
            acc_no="22222222-01",
        )

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key="override-key",  # 이것만 override
            api_secret=None,
            acc_no=None,
            config=config,
            config_file=None,
        )

        assert result["api_key"] == "override-key"  # 생성자 파라미터
        assert result["api_secret"] == "config-secret"  # config 객체
        assert result["acc_no"] == "22222222-01"  # config 객체

    def test_config_file_with_env_fallback(self, monkeypatch, tmp_path):
        """config_file에 일부만 설정되어 있으면 환경 변수로 fallback"""
        # 환경 변수 설정 (전체)
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "11111111-01")

        # config 파일에는 일부만 설정
        config_file = tmp_path / "partial.yaml"
        config_file.write_text("""
api_key: file-key
""")  # api_secret, acc_no는 없음

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=config_file,
        )

        assert result["api_key"] == "file-key"  # config_file
        assert result["api_secret"] == "env-secret"  # 환경 변수 fallback
        assert result["acc_no"] == "11111111-01"  # 환경 변수 fallback


class TestLoadConfigFile:
    """_load_config_file 메서드 테스트"""

    def test_load_yaml_file(self, tmp_path):
        """YAML 파일 로드"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: test-key
api_secret: test-secret
acc_no: "12345678-01"
token_storage_type: redis
redis_url: redis://localhost:6380/0
""")

        resolver = ConfigResolver()
        result = resolver._load_config_file(config_file)

        assert result["api_key"] == "test-key"
        assert result["api_secret"] == "test-secret"
        assert result["acc_no"] == "12345678-01"
        assert result["token_storage_type"] == "redis"
        assert result["redis_url"] == "redis://localhost:6380/0"

    def test_load_yml_file(self, tmp_path):
        """YML 확장자 파일 로드"""
        config_file = tmp_path / "config.yml"
        config_file.write_text("""
api_key: yml-key
api_secret: yml-secret
acc_no: "12345678-01"
""")

        resolver = ConfigResolver()
        result = resolver._load_config_file(config_file)

        assert result["api_key"] == "yml-key"

    def test_non_existent_file(self, tmp_path):
        """존재하지 않는 파일"""
        resolver = ConfigResolver()
        result = resolver._load_config_file(tmp_path / "non_existent.yaml")

        assert result is None

    def test_empty_file(self, tmp_path):
        """빈 파일"""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        resolver = ConfigResolver()
        result = resolver._load_config_file(config_file)

        assert result is None

    def test_path_expansion(self, tmp_path):
        """경로 확장 (~) 처리"""
        # 실제 ~ 경로 테스트는 복잡하므로 tmp_path로 대체
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: expanded-key
api_secret: expanded-secret
acc_no: "12345678-01"
""")

        resolver = ConfigResolver()
        result = resolver._load_config_file(str(config_file))

        assert result["api_key"] == "expanded-key"


class TestMergeConfig:
    """_merge_config 메서드 테스트"""

    def test_merge_non_none_values(self):
        """None이 아닌 값만 병합"""
        resolver = ConfigResolver()

        target = {"a": None, "b": "original", "c": None}
        source = {"a": "new_a", "b": None, "c": "new_c"}

        resolver._merge_config(target, source)

        assert target["a"] == "new_a"  # source에서 업데이트
        assert target["b"] == "original"  # source가 None이므로 유지
        assert target["c"] == "new_c"  # source에서 업데이트

    def test_ignore_unknown_keys(self):
        """target에 없는 키는 무시"""
        resolver = ConfigResolver()

        target = {"a": None}
        source = {"a": "new", "b": "ignored"}

        resolver._merge_config(target, source)

        assert target["a"] == "new"
        assert "b" not in target


class TestTokenStorageFromConfig:
    """Config에서 토큰 저장소 설정 테스트"""

    def test_token_storage_from_resolved_config(self, monkeypatch, tmp_path):
        """_resolved_config에서 토큰 저장소 설정 사용"""
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_TOKEN_STORAGE", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_TOKEN_FILE", raising=False)

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
api_key: test-key
api_secret: test-secret
acc_no: "12345678-01"
token_storage_type: file
token_file: /custom/path/token.key
""")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        resolved = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=config_file,
        )

        # resolved가 올바르게 설정되었는지 확인
        assert resolved["api_key"] == "test-key"
        assert resolved["token_storage_type"] == "file"
        assert resolved["token_file"] == "/custom/path/token.key"


class TestBackwardCompatibility:
    """하위 호환성 테스트"""

    def test_existing_constructor_usage(self, monkeypatch):
        """기존 생성자 호출 방식 호환"""
        # 환경 변수 제거 (기존 방식 테스트)
        monkeypatch.delenv("KOREA_INVESTMENT_API_KEY", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_API_SECRET", raising=False)
        monkeypatch.delenv("KOREA_INVESTMENT_ACCOUNT_NO", raising=False)

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        # 기존 방식: 모든 파라미터를 생성자에 전달
        result = resolver.resolve(
            api_key="direct-key",
            api_secret="direct-secret",
            acc_no="12345678-01",
            config=None,
            config_file=None,
        )

        assert result["api_key"] == "direct-key"
        assert result["api_secret"] == "direct-secret"
        assert result["acc_no"] == "12345678-01"

    def test_env_only_usage(self, monkeypatch):
        """환경 변수만 사용하는 방식 호환"""
        monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-only-key")
        monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "env-only-secret")
        monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")

        resolver = ConfigResolver()
        resolver.DEFAULT_CONFIG_PATHS = []

        # 환경 변수만 사용
        result = resolver.resolve(
            api_key=None,
            api_secret=None,
            acc_no=None,
            config=None,
            config_file=None,
        )

        assert result["api_key"] == "env-only-key"
        assert result["api_secret"] == "env-only-secret"
        assert result["acc_no"] == "12345678-01"
