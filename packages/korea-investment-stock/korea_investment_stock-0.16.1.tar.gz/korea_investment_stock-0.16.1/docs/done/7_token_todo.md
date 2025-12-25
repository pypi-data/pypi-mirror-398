# Token 관리 리팩토링 TODO

## Phase 1: 폴더 구조 변경

- [x] `token_storage/` 폴더를 `token/`으로 리네이밍
- [x] `token_storage.py`를 `storage.py`로 리네이밍
- [x] `test_token_storage.py`를 `test_storage.py`로 리네이밍
- [x] `token/__init__.py` import 경로 업데이트
- [x] `korea_investment_stock.py` import 경로 업데이트
- [x] 기존 테스트 실행하여 리네이밍 확인
  ```bash
  pytest korea_investment_stock/token/test_storage.py -v
  ```

## Phase 2: TokenManager 클래스 생성

- [x] `token/manager.py` 파일 생성
- [x] `TokenManager` 클래스 구현
  - [x] `__init__` 메서드 (storage, base_url, api_key, api_secret)
  - [x] `access_token` 프로퍼티
  - [x] `get_valid_token()` 메서드
  - [x] `is_token_valid()` 메서드
  - [x] `_load_token()` 메서드
  - [x] `_issue_token()` 메서드
  - [x] `_parse_token_response()` 메서드
  - [x] `issue_hashkey()` 메서드
  - [x] `invalidate()` 메서드
- [x] `token/test_manager.py` 테스트 파일 생성
  - [x] `test_get_valid_token_when_valid` 테스트
  - [x] `test_get_valid_token_when_invalid` 테스트
  - [x] `test_is_token_valid` 테스트
  - [x] `test_invalidate` 테스트
- [x] TokenManager 단위 테스트 통과 확인 (16 passed)
  ```bash
  pytest korea_investment_stock/token/test_manager.py -v
  ```

## Phase 3: TokenStorageFactory 분리

- [x] `token/factory.py` 파일 생성
- [x] `create_token_storage()` 함수 구현
- [x] `_get_config_value()` 헬퍼 함수 구현
- [x] `_create_file_storage()` 함수 구현
- [x] `_create_redis_storage()` 함수 구현
- [x] `token/test_factory.py` 테스트 파일 생성
  - [x] `test_default_file_storage` 테스트
  - [x] `test_config_file_storage` 테스트
  - [x] `test_config_redis_storage` 테스트
  - [x] `test_invalid_storage_type` 테스트
  - [x] `test_env_var_storage_type` 테스트
- [x] Factory 테스트 통과 확인 (20 passed)
  ```bash
  pytest korea_investment_stock/token/test_factory.py -v
  ```

## Phase 4: KoreaInvestment 수정

- [x] `token` 모듈 import 추가
  ```python
  from .token import TokenStorage, TokenManager, create_token_storage
  ```
- [x] `__init__`에서 `TokenManager` 초기화
- [x] `issue_access_token()` 위임 패턴으로 변경
- [x] `check_access_token()` 위임 패턴으로 변경
- [x] `load_access_token()` 위임 패턴으로 변경
- [x] `issue_hashkey()` 위임 패턴으로 변경
- [x] `_create_token_storage()` 메서드 삭제
- [x] 불필요한 import 정리 (json, ZoneInfo 제거)
- [x] 토큰 모듈 테스트 통과 확인 (55 passed)
  ```bash
  pytest korea_investment_stock/token/ -v
  ```

## Phase 5: __init__.py 업데이트

- [x] `token/__init__.py`에 TokenManager export 추가
- [x] `token/__init__.py`에 create_token_storage export 추가
- [x] `__all__` 리스트 업데이트
- [x] 패키지 `__init__.py`에 TokenManager, create_token_storage 추가
- [x] import 테스트 통과
  ```bash
  python -c "from korea_investment_stock import KoreaInvestment"
  python -c "from korea_investment_stock.token import TokenManager"
  python -c "from korea_investment_stock.token import create_token_storage"
  ```

## Phase 6: 최종 검증

- [x] 토큰 모듈 단위 테스트 통과 확인 (80 passed)
  ```bash
  pytest korea_investment_stock/token/ -v
  ```
- [x] import 테스트 통과
  ```bash
  python -c "from korea_investment_stock import KoreaInvestment, TokenManager, create_token_storage"
  ```
- [x] 하위 호환성 검증
  - token_storage 속성 유지
  - issue_access_token(), check_access_token(), load_access_token(), issue_hashkey() 메서드 유지

---

## 완료 기준

- [x] `korea_investment_stock.py` 토큰 관련 코드 ~70줄 감소 (760줄 → 692줄)
- [x] `token/` 폴더에 7개 파일 (storage.py, manager.py, factory.py, __init__.py, 테스트 파일 3개)
- [x] 기존 API 시그니처 변경 없음 (Breaking Change 없음)
- [x] TokenManager 테스트 커버리지 충족 (56개 테스트)

---

**작성일**: 2025-12-06
