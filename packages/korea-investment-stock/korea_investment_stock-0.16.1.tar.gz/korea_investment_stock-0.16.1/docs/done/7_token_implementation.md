# Token 관리 리팩토링 구현 가이드

## 개요

`KoreaInvestment` 클래스의 Token 관련 코드를 별도 모듈로 분리하여 SRP 원칙을 준수하고 유지보수성을 개선합니다.

---

## 1. 폴더 구조 변경

### 1.1 폴더/파일 리네이밍

```bash
# 폴더명 변경
mv korea_investment_stock/token_storage korea_investment_stock/token

# 파일명 변경
mv korea_investment_stock/token/token_storage.py korea_investment_stock/token/storage.py
mv korea_investment_stock/token/test_token_storage.py korea_investment_stock/token/test_storage.py
```

### 1.2 Import 경로 업데이트

**변경 전:**
```python
from .token_storage import TokenStorage, FileTokenStorage, RedisTokenStorage
```

**변경 후:**
```python
from .token import TokenStorage, FileTokenStorage, RedisTokenStorage
```

---

## 2. TokenManager 클래스 구현

### 2.1 파일 위치
`korea_investment_stock/token/manager.py`

### 2.2 핵심 구현

```python
"""토큰 관리자 모듈

OAuth 토큰 발급, 검증, 갱신을 담당합니다.
"""

import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

from .storage import TokenStorage

logger = logging.getLogger(__name__)


class TokenManager:
    """OAuth 토큰 관리자"""

    OAUTH_PATH = "oauth2/tokenP"
    HASHKEY_PATH = "uapi/hashkey"

    def __init__(
        self,
        storage: TokenStorage,
        base_url: str,
        api_key: str,
        api_secret: str
    ):
        self.storage = storage
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self._access_token: Optional[str] = None

    @property
    def access_token(self) -> Optional[str]:
        """현재 액세스 토큰 (Bearer 포함)"""
        return self._access_token

    def get_valid_token(self) -> str:
        """유효한 토큰 반환 (필요시 발급/갱신)"""
        if self.is_token_valid():
            if self._access_token is None:
                self._load_token()
            return self._access_token

        self._issue_token()
        return self._access_token

    def is_token_valid(self) -> bool:
        """저장된 토큰의 유효성 확인"""
        return self.storage.check_token_valid(self.api_key, self.api_secret)

    def _load_token(self) -> None:
        """저장소에서 토큰 로드"""
        token_data = self.storage.load_token(self.api_key, self.api_secret)
        if token_data:
            self._access_token = f'Bearer {token_data["access_token"]}'
            logger.debug("토큰 로드 완료")

    def _issue_token(self) -> None:
        """OAuth 토큰 발급"""
        url = f"{self.base_url}/{self.OAUTH_PATH}"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.api_secret
        }

        logger.debug(f"토큰 발급 요청: {url}")
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        resp_data = resp.json()

        self._access_token = f'Bearer {resp_data["access_token"]}'
        token_data = self._parse_token_response(resp_data)
        self.storage.save_token(token_data)
        logger.info("새 토큰 발급 완료")

    def _parse_token_response(self, resp_data: Dict[str, Any]) -> Dict[str, Any]:
        """토큰 응답 파싱"""
        timezone = ZoneInfo('Asia/Seoul')
        dt = datetime.strptime(
            resp_data['access_token_token_expired'],
            '%Y-%m-%d %H:%M:%S'
        ).replace(tzinfo=timezone)

        return {
            **resp_data,
            'timestamp': int(dt.timestamp()),
            'api_key': self.api_key,
            'api_secret': self.api_secret
        }

    def issue_hashkey(self, data: dict) -> str:
        """해쉬키 발급"""
        import json

        url = f"{self.base_url}/{self.HASHKEY_PATH}"
        headers = {
            "content-type": "application/json",
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "User-Agent": "Mozilla/5.0"
        }

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp.raise_for_status()
        return resp.json()["HASH"]

    def invalidate(self) -> bool:
        """저장된 토큰 무효화"""
        self._access_token = None
        return self.storage.delete_token(self.api_key, self.api_secret)
```

---

## 3. TokenStorageFactory 구현

### 3.1 파일 위치
`korea_investment_stock/token/factory.py`

### 3.2 핵심 구현

```python
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
    """
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
```

---

## 4. KoreaInvestment 클래스 수정

### 4.1 Import 변경

```python
from .token import TokenManager, create_token_storage
```

### 4.2 __init__ 수정

```python
def __init__(
    self,
    api_key: str | None = None,
    api_secret: str | None = None,
    acc_no: str | None = None,
    config: "Config | None" = None,
    config_file: "str | Path | None" = None,
    token_storage: Optional[TokenStorage] = None
):
    # ... 기존 설정 해결 로직 ...

    # 토큰 저장소 생성
    storage = token_storage or create_token_storage(self._resolved_config)

    # TokenManager 초기화
    self._token_manager = TokenManager(
        storage=storage,
        base_url=self.base_url,
        api_key=self.api_key,
        api_secret=self.api_secret
    )

    # 토큰 확보
    self.access_token = self._token_manager.get_valid_token()
```

### 4.3 위임 메서드

```python
def issue_access_token(self):
    """OAuth인증/접근토큰발급 (TokenManager로 위임)"""
    self.access_token = self._token_manager.get_valid_token()

def check_access_token(self) -> bool:
    """토큰 유효성 확인"""
    return self._token_manager.is_token_valid()

def load_access_token(self):
    """토큰 로드"""
    self.access_token = self._token_manager.get_valid_token()

def issue_hashkey(self, data: dict) -> str:
    """해쉬키 발급"""
    return self._token_manager.issue_hashkey(data)
```

### 4.4 삭제 대상

- `_create_token_storage()` 메서드 전체 삭제
- `issue_access_token()` 내부 로직 (위임으로 대체)

---

## 5. __init__.py 업데이트

### 5.1 token/__init__.py

```python
"""Token Module

토큰 발급, 관리, 저장을 담당하는 모듈입니다.
"""

from .storage import TokenStorage, FileTokenStorage, RedisTokenStorage
from .manager import TokenManager
from .factory import create_token_storage

__all__ = [
    # 저장소
    'TokenStorage',
    'FileTokenStorage',
    'RedisTokenStorage',
    # 관리자
    'TokenManager',
    # 팩토리
    'create_token_storage',
]
```

---

## 6. 테스트 구현

### 6.1 TokenManager 테스트 (`token/test_manager.py`)

```python
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

    def test_get_valid_token_when_valid(self, token_manager, mock_storage):
        """유효한 토큰이 있으면 로드"""
        mock_storage.check_token_valid.return_value = True
        mock_storage.load_token.return_value = {
            "access_token": "existing-token"
        }

        token = token_manager.get_valid_token()

        assert token == "Bearer existing-token"
        mock_storage.check_token_valid.assert_called_once()

    @patch('requests.post')
    def test_get_valid_token_when_invalid(self, mock_post, token_manager, mock_storage):
        """토큰 만료시 새로 발급"""
        mock_storage.check_token_valid.return_value = False
        mock_post.return_value.json.return_value = {
            "access_token": "new-token",
            "access_token_token_expired": "2025-12-31 23:59:59"
        }
        mock_post.return_value.raise_for_status = Mock()

        token = token_manager.get_valid_token()

        assert token == "Bearer new-token"
        mock_storage.save_token.assert_called_once()

    def test_is_token_valid(self, token_manager, mock_storage):
        """토큰 유효성 확인"""
        mock_storage.check_token_valid.return_value = True

        result = token_manager.is_token_valid()

        assert result is True
        mock_storage.check_token_valid.assert_called_with(
            "test-key", "test-secret"
        )

    def test_invalidate(self, token_manager, mock_storage):
        """토큰 무효화"""
        token_manager._access_token = "Bearer some-token"
        mock_storage.delete_token.return_value = True

        result = token_manager.invalidate()

        assert result is True
        assert token_manager._access_token is None
```

### 6.2 Factory 테스트 (`token/test_factory.py`)

```python
"""create_token_storage 팩토리 테스트"""

import pytest
import os
from unittest.mock import patch

from .factory import create_token_storage
from .storage import FileTokenStorage, RedisTokenStorage


class TestCreateTokenStorage:
    """create_token_storage 테스트"""

    def test_default_file_storage(self):
        """기본값은 FileTokenStorage"""
        storage = create_token_storage()
        assert isinstance(storage, FileTokenStorage)

    def test_config_file_storage(self):
        """config로 file 저장소 생성"""
        config = {"token_storage_type": "file"}
        storage = create_token_storage(config)
        assert isinstance(storage, FileTokenStorage)

    def test_config_redis_storage(self):
        """config로 redis 저장소 생성"""
        config = {
            "token_storage_type": "redis",
            "redis_url": "redis://localhost:6379/0"
        }
        storage = create_token_storage(config)
        assert isinstance(storage, RedisTokenStorage)

    def test_invalid_storage_type(self):
        """지원하지 않는 저장소 타입"""
        config = {"token_storage_type": "mongodb"}
        with pytest.raises(ValueError, match="지원하지 않는 저장소 타입"):
            create_token_storage(config)

    @patch.dict(os.environ, {"KOREA_INVESTMENT_TOKEN_STORAGE_TYPE": "file"})
    def test_env_var_storage_type(self):
        """환경변수에서 저장소 타입 읽기"""
        storage = create_token_storage()
        assert isinstance(storage, FileTokenStorage)
```

---

## 7. 검증 체크리스트

```bash
# 1. 기존 테스트
pytest korea_investment_stock/tests/test_korea_investment_stock.py -v

# 2. 토큰 모듈 테스트
pytest korea_investment_stock/token/ -v

# 3. 통합 테스트 (API 자격 증명 필요)
pytest korea_investment_stock/tests/test_integration_us_stocks.py -v

# 4. import 테스트
python -c "from korea_investment_stock import KoreaInvestment"
python -c "from korea_investment_stock.token import TokenManager"

# 5. 예제 실행
python examples/basic_example.py
```

---

## 8. 하위 호환성

**Breaking Change 없음** - 기존 API 시그니처 유지:

```python
# 기존 코드 (변경 없이 동작)
broker = KoreaInvestment(api_key, api_secret, acc_no)
broker.issue_access_token()
broker.check_access_token()
broker.issue_hashkey(data)
```

---

**문서 버전**: 1.0
**작성일**: 2025-12-06
