# Token 관리 리팩토링 PRD

> **KoreaInvestment 클래스의 Token 관련 코드**를 별도 모듈로 분리하여 책임 분리 및 유지보수성 개선

## Quick Summary

### 현재 문제
- `KoreaInvestment` 클래스에 **토큰 발급/관리 로직이 혼재** (~118줄)
- `token_storage/` 모듈은 분리되어 있으나, **토큰 발급 로직은 메인 클래스에 있음**
- **SRP(단일 책임 원칙) 위반**: API 호출과 토큰 관리가 한 클래스에
- **팩토리 로직 분산**: `_create_token_storage()`가 메인 클래스에 있음

### 제안 구조
```
korea_investment_stock/
├── token/                       # 🔄 token_storage → token 으로 변경
│   ├── __init__.py              # 기존 유지 + TokenManager export 추가
│   ├── storage.py               # 🔄 token_storage.py → storage.py
│   ├── manager.py               # ✨ NEW: 토큰 발급/관리 담당
│   ├── factory.py               # ✨ NEW: 저장소 생성 팩토리
│   └── test_*.py                # 기존 + 신규 테스트
└── korea_investment_stock.py    # TokenManager만 사용
```

### 예상 효과
- ✅ 메인 클래스에서 **~100줄 감소**
- ✅ 토큰 관련 로직 **단일 모듈로 통합**
- ✅ **테스트 용이성 향상** (TokenManager 단위 테스트 가능)
- ✅ **의존성 역전**: KoreaInvestment → TokenManager → TokenStorage

---

## 목차

1. [현재 상태 분석](#1-현재-상태-분석)
2. [리팩토링 제안](#2-리팩토링-제안)
3. [상세 구현 계획](#3-상세-구현-계획)
4. [마이그레이션 가이드](#4-마이그레이션-가이드)
5. [위험 및 완화 방안](#5-위험-및-완화-방안)
6. [성공 지표](#6-성공-지표)

---

## 1. 현재 상태 분석

### 1.1 Token 관련 코드 분포

#### token_storage/ 모듈 (이미 분리됨, ~400줄) → token/ 으로 변경 예정

```
token_storage/  →  token/
├── __init__.py                  # 12줄
├── token_storage.py → storage.py    # 397줄
│   ├── TokenStorage (ABC)       # 추상 클래스
│   ├── FileTokenStorage         # 파일 기반 저장
│   └── RedisTokenStorage        # Redis 기반 저장
└── test_token_storage.py → test_storage.py  # 테스트
```

**✅ 잘 분리된 부분**: 토큰 저장/로드/삭제/검증 로직

#### KoreaInvestment 클래스 내 Token 코드 (분리 대상, ~118줄)

| 메서드 | 라인 | 역할 | 문제점 |
|--------|------|------|--------|
| `__init__` (일부) | 143-159 | 토큰 초기화 | API 클라이언트 책임 아님 |
| `_create_token_storage()` | 161-201 | 저장소 팩토리 | 팩토리 로직이 메인 클래스에 |
| `issue_access_token()` | 219-247 | OAuth 토큰 발급 | **핵심 문제**: API 호출과 혼재 |
| `check_access_token()` | 249-255 | 토큰 유효성 확인 | 단순 위임, 분리 가능 |
| `load_access_token()` | 257-262 | 토큰 로드 | 단순 위임, 분리 가능 |
| `issue_hashkey()` | 264-281 | 해쉬키 발급 | 토큰과 별개지만 인증 관련 |

### 1.2 현재 의존성 구조

```
KoreaInvestment
    ├── TokenStorage (직접 의존)
    ├── 토큰 발급 로직 (내장)
    ├── 저장소 팩토리 로직 (내장)
    └── API 호출 로직
```

**문제점**:
1. `KoreaInvestment`가 토큰 발급 HTTP 요청까지 직접 수행
2. 설정 기반 저장소 생성 로직이 메인 클래스에 있음
3. 토큰 관리 테스트를 위해 전체 클래스 인스턴스 필요

### 1.3 issue_access_token() 상세 분석

```python
def issue_access_token(self):
    """OAuth인증/접근토큰발급"""
    path = "oauth2/tokenP"
    url = f"{self.base_url}/{path}"
    headers = {"content-type": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "appkey": self.api_key,
        "appsecret": self.api_secret
    }

    resp = requests.post(url, headers=headers, json=data)
    resp_data = resp.json()
    self.access_token = f'Bearer {resp_data["access_token"]}'

    # 만료 시간 파싱 (서울 시간대)
    timezone = ZoneInfo('Asia/Seoul')
    dt = datetime.strptime(
        resp_data['access_token_token_expired'],
        '%Y-%m-%d %H:%M:%S'
    ).replace(tzinfo=timezone)
    resp_data['timestamp'] = int(dt.timestamp())
    resp_data['api_key'] = self.api_key
    resp_data['api_secret'] = self.api_secret

    # 토큰 저장
    self.token_storage.save_token(resp_data)
```

**이 메서드의 책임**:
1. OAuth 엔드포인트 URL 구성
2. HTTP POST 요청 수행
3. 만료 시간 파싱 (시간대 처리)
4. 토큰 데이터 저장

→ **모두 TokenManager의 책임으로 이동 가능**

### 1.4 _create_token_storage() 분석

```python
def _create_token_storage(self) -> TokenStorage:
    """설정 기반 토큰 저장소 생성"""
    # _resolved_config에서 설정 읽기
    if hasattr(self, "_resolved_config") and self._resolved_config:
        storage_type = self._resolved_config.get("token_storage_type") or "file"
        redis_url = self._resolved_config.get("redis_url") or "redis://localhost:6379/0"
        redis_password = self._resolved_config.get("redis_password")
        token_file = self._resolved_config.get("token_file")
    else:
        # 환경 변수에서 읽기
        storage_type = os.getenv("KOREA_INVESTMENT_TOKEN_STORAGE", "file")
        redis_url = os.getenv("KOREA_INVESTMENT_REDIS_URL", "redis://localhost:6379/0")
        redis_password = os.getenv("KOREA_INVESTMENT_REDIS_PASSWORD")
        token_file = os.getenv("KOREA_INVESTMENT_TOKEN_FILE")

    storage_type = storage_type.lower()

    if storage_type == "file":
        return FileTokenStorage(file_path)
    elif storage_type == "redis":
        return RedisTokenStorage(redis_url, password=redis_password)
    else:
        raise ValueError(f"지원하지 않는 저장소 타입: {storage_type}")
```

**문제점**:
- 팩토리 패턴이지만 메인 클래스에 있음
- 환경 변수 읽기 로직 중복 (ConfigResolver와 유사)
- 저장소 타입 확장 시 메인 클래스 수정 필요

---

## 2. 리팩토링 제안

### 2.1 제안 디렉토리 구조

```
korea_investment_stock/
├── token/                       # 🔄 token_storage → token
│   ├── __init__.py              # Export 업데이트
│   ├── storage.py               # 🔄 TokenStorage, FileTokenStorage, RedisTokenStorage
│   ├── manager.py               # ✨ NEW: TokenManager 클래스
│   ├── factory.py               # ✨ NEW: create_token_storage()
│   ├── test_storage.py          # 저장소 테스트
│   └── test_manager.py          # ✨ NEW: TokenManager 테스트
└── korea_investment_stock.py    # ~100줄 감소
```

### 2.2 새로운 의존성 구조

```
KoreaInvestment
    └── TokenManager (의존)
            ├── TokenStorage (의존)
            └── 토큰 발급 로직
```

**개선점**:
1. `KoreaInvestment`는 `TokenManager`만 알면 됨
2. 토큰 관련 변경이 `TokenManager`에 캡슐화
3. 단위 테스트 용이

### 2.3 TokenManager 클래스 설계

```python
# token/manager.py

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
    """OAuth 토큰 관리자

    토큰 발급, 유효성 검증, 자동 갱신을 담당합니다.
    TokenStorage를 통해 토큰을 영구 저장합니다.

    Attributes:
        storage: 토큰 저장소 인스턴스
        access_token: 현재 액세스 토큰 (Bearer 포함)

    Example:
        >>> storage = FileTokenStorage()
        >>> manager = TokenManager(
        ...     storage=storage,
        ...     base_url="https://openapi.koreainvestment.com:9443",
        ...     api_key="your-key",
        ...     api_secret="your-secret"
        ... )
        >>> token = manager.get_valid_token()
    """

    OAUTH_PATH = "oauth2/tokenP"
    HASHKEY_PATH = "uapi/hashkey"

    def __init__(
        self,
        storage: TokenStorage,
        base_url: str,
        api_key: str,
        api_secret: str
    ):
        """TokenManager 초기화

        Args:
            storage: 토큰 저장소
            base_url: API 기본 URL
            api_key: API Key
            api_secret: API Secret
        """
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
        """유효한 토큰 반환 (필요시 발급/갱신)

        1. 저장된 토큰이 유효하면 반환
        2. 유효하지 않으면 새로 발급

        Returns:
            str: Bearer 토큰 문자열

        Raises:
            requests.RequestException: 토큰 발급 실패시
        """
        if self.is_token_valid():
            if self._access_token is None:
                self._load_token()
            return self._access_token

        # 토큰 발급
        self._issue_token()
        return self._access_token

    def is_token_valid(self) -> bool:
        """저장된 토큰의 유효성 확인

        Returns:
            bool: 토큰이 존재하고 만료되지 않았으면 True
        """
        return self.storage.check_token_valid(self.api_key, self.api_secret)

    def _load_token(self) -> None:
        """저장소에서 토큰 로드"""
        token_data = self.storage.load_token(self.api_key, self.api_secret)
        if token_data:
            self._access_token = f'Bearer {token_data["access_token"]}'
            logger.debug("토큰 로드 완료")

    def _issue_token(self) -> None:
        """OAuth 토큰 발급

        Korea Investment API의 OAuth 엔드포인트를 호출하여
        새 토큰을 발급받고 저장합니다.
        """
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

        # Bearer 토큰 설정
        self._access_token = f'Bearer {resp_data["access_token"]}'

        # 만료 시간 파싱 (서울 시간대)
        token_data = self._parse_token_response(resp_data)

        # 저장
        self.storage.save_token(token_data)
        logger.info("새 토큰 발급 완료")

    def _parse_token_response(self, resp_data: Dict[str, Any]) -> Dict[str, Any]:
        """토큰 응답 파싱

        Args:
            resp_data: API 응답 데이터

        Returns:
            저장용 토큰 데이터 (timestamp 포함)
        """
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
        """해쉬키 발급

        POST 요청 데이터에 대한 해쉬키를 발급합니다.

        Args:
            data: POST 요청 데이터

        Returns:
            str: 해쉬키 문자열
        """
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
        """저장된 토큰 무효화

        Returns:
            bool: 삭제 성공 여부
        """
        self._access_token = None
        return self.storage.delete_token(self.api_key, self.api_secret)
```

### 2.4 TokenStorageFactory 설계

```python
# token/factory.py

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
    """설정값 조회 (config → 환경변수 → 기본값)"""
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

### 2.5 KoreaInvestment 수정 후 모습

```python
# korea_investment_stock.py (수정 후)

from .token import TokenManager, create_token_storage

class KoreaInvestment:

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        acc_no: str | None = None,
        config: "Config | None" = None,
        config_file: "str | Path | None" = None,
        token_storage: Optional[TokenStorage] = None
    ):
        # ... 설정 해결 로직 (기존 유지) ...

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

    # 기존 메서드는 TokenManager로 위임
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

    # _create_token_storage() 메서드 삭제됨
    # ...
```

### 2.6 __init__.py 업데이트

```python
# token/__init__.py

"""
Token Module

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

## 3. 상세 구현 계획

### Phase 1: 폴더 구조 변경 (1시간)

1. `token_storage/` → `token/` 폴더명 변경
2. `token_storage.py` → `storage.py` 파일명 변경
3. import 경로 업데이트
4. 기존 테스트 통과 확인

**예상 결과**: 폴더/파일 구조 정리

### Phase 2: TokenManager 클래스 생성 (2-3시간)

1. `token/manager.py` 생성
2. `issue_access_token()` 로직 이동
3. `_parse_token_response()` 추출
4. `issue_hashkey()` 이동
5. 단위 테스트 작성

**예상 결과**: ~150줄 신규 파일

### Phase 3: TokenStorageFactory 분리 (1-2시간)

1. `token/factory.py` 생성
2. `_create_token_storage()` 로직 이동
3. `_get_config_value()` 헬퍼 추가
4. 테스트 작성

**예상 결과**: ~80줄 신규 파일

### Phase 4: KoreaInvestment 수정 (1-2시간)

1. `TokenManager` import
2. `__init__`에서 `TokenManager` 사용
3. 기존 메서드를 위임 패턴으로 변경
4. `_create_token_storage()` 삭제

**예상 결과**: ~100줄 감소

### Phase 5: 테스트 및 검증 (2-3시간)

1. 기존 테스트 실행
2. 통합 테스트 확인
3. 예제 코드 실행
4. 하위 호환성 검증

---

## 4. 마이그레이션 가이드

### 4.1 하위 호환성 유지 (Breaking Change 없음)

```python
# 기존 코드 (변경 없이 동작)
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)
broker.issue_access_token()  # 내부적으로 TokenManager 사용
broker.check_access_token()
broker.issue_hashkey(data)
```

### 4.2 새로운 직접 사용 (선택적)

```python
# TokenManager 직접 사용 가능
from korea_investment_stock.token import (
    TokenManager,
    create_token_storage
)

storage = create_token_storage()
manager = TokenManager(
    storage=storage,
    base_url="https://openapi.koreainvestment.com:9443",
    api_key=api_key,
    api_secret=api_secret
)

token = manager.get_valid_token()
```

### 4.3 커스텀 저장소 주입

```python
# 커스텀 TokenStorage 구현 주입
class MyCustomStorage(TokenStorage):
    # ... 구현 ...

broker = KoreaInvestment(
    api_key=api_key,
    api_secret=api_secret,
    acc_no=acc_no,
    token_storage=MyCustomStorage()  # 커스텀 저장소
)
```

---

## 5. 위험 및 완화 방안

### 위험 1: 하위 호환성

| 위험 | 기존 코드가 `issue_access_token()` 직접 호출 |
|------|---------------------------------------------|
| 영향 | 중간 (일부 사용자) |
| 완화 | 기존 메서드 시그니처 유지, 내부만 위임 |
| 검증 | 기존 테스트 100% 통과 확인 |

### 위험 2: 순환 import

| 위험 | `manager.py`가 다른 모듈 참조 시 순환 발생 가능 |
|------|-----------------------------------------------------|
| 영향 | 낮음 |
| 완화 | TokenManager는 TokenStorage만 의존 |
| 검증 | 각 모듈 개별 import 테스트 |

### 위험 3: 토큰 발급 실패

| 위험 | 리팩토링 중 토큰 발급 로직 오류 |
|------|--------------------------------|
| 영향 | 높음 (API 사용 불가) |
| 완화 | 통합 테스트로 실제 API 호출 검증 |
| 검증 | `test_integration_us_stocks.py` 통과 |

---

## 6. 성공 지표

### 6.1 정량적 지표

| 지표 | Before | After | 목표 |
|------|--------|-------|------|
| `korea_investment_stock.py` 토큰 관련 코드 | ~118줄 | ~20줄 | ≤30줄 |
| `token/` 파일 수 | 3개 | 5개 | 적절한 분리 |
| TokenManager 테스트 커버리지 | 0% | 80%+ | ≥80% |

### 6.2 정성적 지표

- [ ] 기존 테스트 100% 통과
- [ ] 공개 API 변경 없음
- [ ] TokenManager 단위 테스트 가능
- [ ] 토큰 관련 로직이 한 곳에 집중

### 6.3 검증 체크리스트

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

## 부록: 파일별 변경 요약

### 폴더/파일 리네이밍

| Before | After |
|--------|-------|
| `token_storage/` | `token/` |
| `token_storage/token_storage.py` | `token/storage.py` |
| `token_storage/test_token_storage.py` | `token/test_storage.py` |

### 신규 파일

| 파일 | 라인 수 | 역할 |
|------|---------|------|
| `token/manager.py` | ~150줄 | 토큰 발급/관리 |
| `token/factory.py` | ~80줄 | 저장소 팩토리 |
| `token/test_manager.py` | ~100줄 | TokenManager 테스트 |

### 수정 파일

| 파일 | 변경 사항 |
|------|-----------|
| `token/__init__.py` | TokenManager, create_token_storage export 추가 |
| `korea_investment_stock.py` | TokenManager 사용, ~100줄 감소 |

### 삭제 코드

| 위치 | 내용 |
|------|------|
| `KoreaInvestment._create_token_storage()` | factory.py로 이동 |
| `KoreaInvestment.issue_access_token()` 로직 | TokenManager로 이동 (메서드는 위임으로 유지) |

---

**문서 버전**: 1.0
**작성일**: 2025-12-06
**상태**: 검토 대기
**다음 단계**: Phase 1 구현 시작
