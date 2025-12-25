# 환경 변수 설정 방식 구현 가이드

## 목표

Type C Hybrid 패턴 구현: `생성자 파라미터 > 환경 변수 > Config 파일`

## Phase 1: 환경변수 자동 감지 (v0.9.0)

### 변경 파일
- `korea_investment_stock/korea_investment_stock.py`

### 구현 코드

```python
class KoreaInvestment:
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        acc_no: str | None = None,
        token_storage: TokenStorage | None = None
    ):
        # 우선순위: 생성자 파라미터 > 환경 변수
        self.api_key = api_key or os.getenv("KOREA_INVESTMENT_API_KEY")
        self.api_secret = api_secret or os.getenv("KOREA_INVESTMENT_API_SECRET")
        self.acc_no = acc_no or os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

        if not all([self.api_key, self.api_secret, self.acc_no]):
            raise ValueError(
                "API credentials required. "
                "Pass as parameters or set KOREA_INVESTMENT_* environment variables."
            )
```

---

## Phase 2: Config 클래스 추가 (v1.0.0)

### 새 파일 생성
- `korea_investment_stock/config.py`

### 의존성 추가

```toml
# pyproject.toml
[project]
dependencies = [
    "requests",
    "pandas",
    "pyyaml>=6.0",
]
```

### Config 클래스

```python
# korea_investment_stock/config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

@dataclass
class Config:
    api_key: str
    api_secret: str
    acc_no: str
    token_storage_type: str = "file"
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    token_file: Optional[Path] = None

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            api_key=os.environ["KOREA_INVESTMENT_API_KEY"],
            api_secret=os.environ["KOREA_INVESTMENT_API_SECRET"],
            acc_no=os.environ["KOREA_INVESTMENT_ACCOUNT_NO"],
            token_storage_type=os.getenv("KOREA_INVESTMENT_TOKEN_STORAGE", "file"),
            redis_url=os.getenv("KOREA_INVESTMENT_REDIS_URL", "redis://localhost:6379/0"),
            redis_password=os.getenv("KOREA_INVESTMENT_REDIS_PASSWORD"),
            token_file=Path(os.getenv("KOREA_INVESTMENT_TOKEN_FILE", "~/.cache/kis/token.key")).expanduser(),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        import yaml
        path = Path(path).expanduser()
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

### Config 파일 형식

```yaml
# ~/.config/kis/config.yaml
api_key: your-api-key
api_secret: your-api-secret
acc_no: "12345678-01"
token_storage_type: file
token_file: ~/.cache/kis/token.key
```

---

## Phase 3: Hybrid 통합 (v1.1.0)

### 변경 파일
- `korea_investment_stock/korea_investment_stock.py`

### 핵심 구현

```python
class KoreaInvestment:
    DEFAULT_CONFIG_PATHS = [
        "~/.config/kis/config.yaml",
        "~/.config/kis/config.yml",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        acc_no: str | None = None,
        config: Config | None = None,
        config_file: str | Path | None = None,
        token_storage: TokenStorage | None = None
    ):
        """
        설정 우선순위:
        1. 생성자 파라미터
        2. config 객체
        3. config_file 파라미터
        4. 환경 변수
        5. 기본 config 파일 (~/.config/kis/config.yaml)
        """
        resolved_config = self._resolve_config(
            api_key, api_secret, acc_no, config, config_file
        )
        self.api_key = resolved_config.api_key
        self.api_secret = resolved_config.api_secret
        self.acc_no = resolved_config.acc_no
```

---

## 테스트 전략

### 단위 테스트

```python
# tests/test_config.py
def test_config_from_env(monkeypatch):
    monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "test-key")
    monkeypatch.setenv("KOREA_INVESTMENT_API_SECRET", "test-secret")
    monkeypatch.setenv("KOREA_INVESTMENT_ACCOUNT_NO", "12345678-01")

    config = Config.from_env()
    assert config.api_key == "test-key"

def test_config_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
api_key: yaml-key
api_secret: yaml-secret
acc_no: "12345678-01"
""")
    config = Config.from_yaml(config_file)
    assert config.api_key == "yaml-key"

def test_priority_constructor_over_env(monkeypatch):
    monkeypatch.setenv("KOREA_INVESTMENT_API_KEY", "env-key")
    broker = KoreaInvestment(api_key="constructor-key", ...)
    assert broker.api_key == "constructor-key"
```

---

## 하위 호환성

- 기존 코드 100% 호환
- 새 기능은 opt-in 방식
- 기존 생성자 호출 방식 유지
