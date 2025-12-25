"""
설정 해결 로직

5단계 우선순위로 설정을 해결합니다.
"""
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config


class ConfigResolver:
    """5단계 우선순위 설정 해결

    우선순위:
        1. 생성자 파라미터 (최고 우선순위)
        2. config 객체
        3. config_file 파라미터
        4. 환경 변수
        5. 기본 config 파일 (~/.config/kis/config.yaml)
    """

    # 기본 설정 파일 경로 (우선순위 순)
    DEFAULT_CONFIG_PATHS = [
        "~/.config/kis/config.yaml",
        "~/.config/kis/config.yml",
    ]

    def resolve(
        self,
        api_key: str | None,
        api_secret: str | None,
        acc_no: str | None,
        config: "Config | None",
        config_file: "str | Path | None",
    ) -> dict:
        """5단계 우선순위로 설정을 해결

        Args:
            api_key: 생성자에서 전달된 API key
            api_secret: 생성자에서 전달된 API secret
            acc_no: 생성자에서 전달된 계좌번호
            config: Config 객체
            config_file: 설정 파일 경로

        Returns:
            dict: 해결된 설정 값들
                - api_key: API key
                - api_secret: API secret
                - acc_no: 계좌번호
                - token_storage_type: 토큰 저장소 타입
                - redis_url: Redis URL
                - redis_password: Redis 비밀번호
                - token_file: 토큰 파일 경로
        """
        # 결과 딕셔너리 초기화 (None으로)
        result = {
            "api_key": None,
            "api_secret": None,
            "acc_no": None,
            "token_storage_type": None,
            "redis_url": None,
            "redis_password": None,
            "token_file": None,
        }

        # 5단계: 기본 config 파일에서 로드 (가장 낮은 우선순위)
        default_config = self._load_default_config_file()
        if default_config:
            self._merge_config(result, default_config)

        # 4단계: 환경 변수
        env_config = self._load_from_env()
        self._merge_config(result, env_config)

        # 3단계: config_file 파라미터
        if config_file:
            file_config = self._load_config_file(config_file)
            if file_config:
                self._merge_config(result, file_config)

        # 2단계: config 객체
        if config:
            config_dict = {
                "api_key": config.api_key,
                "api_secret": config.api_secret,
                "acc_no": config.acc_no,
                "token_storage_type": config.token_storage_type,
                "redis_url": config.redis_url,
                "redis_password": config.redis_password,
                "token_file": str(config.token_file) if config.token_file else None,
            }
            self._merge_config(result, config_dict)

        # 1단계: 생성자 파라미터 (최고 우선순위)
        constructor_params = {
            "api_key": api_key,
            "api_secret": api_secret,
            "acc_no": acc_no,
        }
        self._merge_config(result, constructor_params)

        return result

    def _merge_config(self, target: dict, source: dict) -> None:
        """source의 non-None 값으로 target을 업데이트

        Args:
            target: 업데이트할 대상 딕셔너리
            source: 소스 딕셔너리
        """
        for key, value in source.items():
            if value is not None and key in target:
                target[key] = value

    def _load_default_config_file(self) -> dict | None:
        """기본 경로에서 config 파일 로드 시도

        DEFAULT_CONFIG_PATHS에 정의된 경로들을 순서대로 확인하여
        첫 번째 존재하는 파일을 로드합니다.

        Returns:
            dict | None: 로드된 설정 또는 None (파일 없음)
        """
        for path in self.DEFAULT_CONFIG_PATHS:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return self._load_config_file(expanded_path)
        return None

    def _load_config_file(self, path: "str | Path") -> dict | None:
        """설정 파일 로드 (YAML 형식 지원)

        Args:
            path: 설정 파일 경로

        Returns:
            dict | None: 로드된 설정 또는 None (실패 시)
        """
        try:
            import yaml
        except ImportError:
            # pyyaml이 설치되지 않은 경우
            return None

        path = Path(path).expanduser()
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            # YAML 키를 내부 키로 매핑
            return {
                "api_key": data.get("api_key"),
                "api_secret": data.get("api_secret"),
                "acc_no": data.get("acc_no"),
                "token_storage_type": data.get("token_storage_type"),
                "redis_url": data.get("redis_url"),
                "redis_password": data.get("redis_password"),
                "token_file": data.get("token_file"),
            }
        except Exception:
            return None

    def _load_from_env(self) -> dict:
        """환경 변수에서 설정 로드

        Returns:
            dict: 환경 변수에서 로드된 설정
        """
        return {
            "api_key": os.getenv("KOREA_INVESTMENT_API_KEY"),
            "api_secret": os.getenv("KOREA_INVESTMENT_API_SECRET"),
            "acc_no": os.getenv("KOREA_INVESTMENT_ACCOUNT_NO"),
            "token_storage_type": os.getenv("KOREA_INVESTMENT_TOKEN_STORAGE"),
            "redis_url": os.getenv("KOREA_INVESTMENT_REDIS_URL"),
            "redis_password": os.getenv("KOREA_INVESTMENT_REDIS_PASSWORD"),
            "token_file": os.getenv("KOREA_INVESTMENT_TOKEN_FILE"),
        }
