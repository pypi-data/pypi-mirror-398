"""Config 클래스 - 설정 관리

Korea Investment Stock 라이브러리의 설정을 관리하는 클래스입니다.
환경 변수, YAML 파일 등 다양한 소스에서 설정을 로드할 수 있습니다.

Examples:
    # 환경 변수에서 로드
    >>> config = Config.from_env()

    # YAML 파일에서 로드
    >>> config = Config.from_yaml("~/.config/kis/config.yaml")

    # 직접 생성
    >>> config = Config(
    ...     api_key="your-api-key",
    ...     api_secret="your-api-secret",
    ...     acc_no="12345678-01"
    ... )
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import os


@dataclass
class Config:
    """Korea Investment Stock 설정 클래스

    Attributes:
        api_key: 발급받은 API key
        api_secret: 발급받은 API secret
        acc_no: 계좌번호 (12345678-01 형식)
        token_storage_type: 토큰 저장 방식 ("file" 또는 "redis")
        redis_url: Redis 연결 URL
        redis_password: Redis 비밀번호 (선택)
        token_file: 토큰 파일 경로 (file 방식일 때)
    """

    api_key: str
    api_secret: str
    acc_no: str
    token_storage_type: str = "file"
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    token_file: Optional[Path] = field(default=None)

    def __post_init__(self):
        """초기화 후 유효성 검증"""
        # token_file이 문자열이면 Path로 변환
        if isinstance(self.token_file, str):
            self.token_file = Path(self.token_file).expanduser()
        elif self.token_file is None:
            self.token_file = Path("~/.cache/kis/token.key").expanduser()

        # 계좌번호 형식 검증
        if '-' not in self.acc_no:
            raise ValueError(
                f"계좌번호 형식이 올바르지 않습니다. '12345678-01' 형식이어야 합니다. "
                f"입력값: {self.acc_no}"
            )

        parts = self.acc_no.split('-')
        if len(parts) != 2 or len(parts[0]) != 8 or len(parts[1]) != 2:
            raise ValueError(
                f"계좌번호 형식이 올바르지 않습니다. 앞 8자리-뒤 2자리여야 합니다. "
                f"입력값: {self.acc_no}"
            )

        # token_storage_type 검증
        valid_types = ("file", "redis")
        if self.token_storage_type.lower() not in valid_types:
            raise ValueError(
                f"지원하지 않는 저장소 타입: {self.token_storage_type}. "
                f"'file' 또는 'redis'만 지원됩니다."
            )

    @classmethod
    def from_env(cls) -> "Config":
        """환경 변수에서 설정 로드

        환경 변수:
            KOREA_INVESTMENT_API_KEY: API key (필수)
            KOREA_INVESTMENT_API_SECRET: API secret (필수)
            KOREA_INVESTMENT_ACCOUNT_NO: 계좌번호 (필수)
            KOREA_INVESTMENT_TOKEN_STORAGE: 토큰 저장 방식 (기본: file)
            KOREA_INVESTMENT_REDIS_URL: Redis URL (기본: redis://localhost:6379/0)
            KOREA_INVESTMENT_REDIS_PASSWORD: Redis 비밀번호 (선택)
            KOREA_INVESTMENT_TOKEN_FILE: 토큰 파일 경로 (기본: ~/.cache/kis/token.key)

        Returns:
            Config: 설정 객체

        Raises:
            KeyError: 필수 환경 변수가 설정되지 않은 경우
        """
        # 필수 환경 변수 확인
        missing = []
        if not os.getenv("KOREA_INVESTMENT_API_KEY"):
            missing.append("KOREA_INVESTMENT_API_KEY")
        if not os.getenv("KOREA_INVESTMENT_API_SECRET"):
            missing.append("KOREA_INVESTMENT_API_SECRET")
        if not os.getenv("KOREA_INVESTMENT_ACCOUNT_NO"):
            missing.append("KOREA_INVESTMENT_ACCOUNT_NO")

        if missing:
            raise KeyError(
                f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}"
            )

        token_file_str = os.getenv("KOREA_INVESTMENT_TOKEN_FILE")
        token_file = Path(token_file_str).expanduser() if token_file_str else None

        return cls(
            api_key=os.environ["KOREA_INVESTMENT_API_KEY"],
            api_secret=os.environ["KOREA_INVESTMENT_API_SECRET"],
            acc_no=os.environ["KOREA_INVESTMENT_ACCOUNT_NO"],
            token_storage_type=os.getenv("KOREA_INVESTMENT_TOKEN_STORAGE", "file"),
            redis_url=os.getenv("KOREA_INVESTMENT_REDIS_URL", "redis://localhost:6379/0"),
            redis_password=os.getenv("KOREA_INVESTMENT_REDIS_PASSWORD"),
            token_file=token_file,
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """YAML 파일에서 설정 로드

        Args:
            path: YAML 설정 파일 경로 (~/ 확장 지원)

        Returns:
            Config: 설정 객체

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            yaml.YAMLError: YAML 파싱 오류

        YAML 파일 형식:
            ```yaml
            api_key: your-api-key
            api_secret: your-api-secret
            acc_no: "12345678-01"
            token_storage_type: file  # 선택
            token_file: ~/.cache/kis/token.key  # 선택
            ```
        """
        import yaml

        path = Path(path).expanduser()

        if not path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")

        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ValueError(f"빈 설정 파일입니다: {path}")

        # 필수 필드 확인
        required_fields = ['api_key', 'api_secret', 'acc_no']
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(
                f"필수 필드가 누락되었습니다: {', '.join(missing)}"
            )

        return cls(**data)

    def to_dict(self) -> dict:
        """설정을 딕셔너리로 변환

        Returns:
            dict: 설정 딕셔너리

        Note:
            token_file은 문자열로 변환됩니다.
        """
        result = asdict(self)
        # Path를 문자열로 변환
        if result['token_file']:
            result['token_file'] = str(result['token_file'])
        return result

    def to_yaml(self, path: str | Path | None = None) -> str:
        """설정을 YAML 형식으로 변환

        Args:
            path: 저장할 파일 경로 (None이면 문자열만 반환)

        Returns:
            str: YAML 형식 문자열
        """
        import yaml

        data = self.to_dict()

        # 민감한 정보는 마스킹 옵션 제공 가능 (향후 확장)
        yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)

        if path:
            path = Path(path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(yaml_str)

        return yaml_str

    def __repr__(self) -> str:
        """문자열 표현 (민감 정보 마스킹)"""
        return (
            f"Config("
            f"api_key='***{self.api_key[-4:] if len(self.api_key) > 4 else '****'}', "
            f"api_secret='***{self.api_secret[-4:] if len(self.api_secret) > 4 else '****'}', "
            f"acc_no='{self.acc_no}', "
            f"token_storage_type='{self.token_storage_type}')"
        )
