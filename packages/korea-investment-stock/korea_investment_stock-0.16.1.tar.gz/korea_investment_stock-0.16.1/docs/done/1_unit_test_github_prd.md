# PRD: GitHub Actions for Unit Test Automation

## 1. 개요

### 목적
PR 생성 및 업데이트 시 자동으로 unit test를 실행하여 코드 품질을 보장하고, 버그를 조기에 발견합니다.

### 범위
- **포함**: Unit test 자동화 (API 호출이 필요하지 않은 테스트)
- **제외**: Integration test (API credential 필요)

## 2. 현재 상황 분석

### 2.1 테스트 파일 구조
```
korea_investment_stock/
├── test_korea_investment_stock.py          # Integration tests (API 필요)
├── test_integration_us_stocks.py           # Integration tests (API 필요)
├── cache/
│   ├── test_cache_manager.py               # Unit tests (API 불필요) ✅
│   └── test_cached_integration.py          # Integration tests (API 필요)
└── token_storage/
    └── test_token_storage.py               # Unit tests (일부 Redis 필요)
```

### 2.2 테스트 분류

**Unit Tests (GitHub Actions에서 실행 가능):**
- `cache/test_cache_manager.py` - 순수 메모리 캐시 테스트
- `token_storage/test_token_storage.py` - FileTokenStorage 테스트 (fakeredis 사용)

**Integration Tests (GitHub Actions 제외):**
- `test_korea_investment_stock.py` - API credential 필요
- `test_integration_us_stocks.py` - API credential 필요
- `cache/test_cached_integration.py` - API credential 필요

### 2.3 현재 의존성 (pyproject.toml)
```toml
[project.optional-dependencies]
redis = ["redis>=4.5.0"]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "fakeredis>=2.10.0",
]
```

## 3. 요구사항

### 3.1 기능 요구사항

#### FR-1: PR 트리거
- **조건**: Pull Request 생성 또는 업데이트 시 자동 실행
- **대상 브랜치**: `main`, `master`
- **이벤트**: `pull_request` (opened, synchronize, reopened)

#### FR-2: Unit Test 실행
- **실행 대상**: API credential이 필요하지 않은 테스트만
- **테스트 명령어**:
  ```bash
  pytest korea_investment_stock/cache/test_cache_manager.py -v
  pytest korea_investment_stock/token_storage/test_token_storage.py -v -k "not redis_storage"
  ```
- **실패 조건**: 테스트 실패 시 PR merge 차단

#### FR-3: 다중 Python 버전 지원
- **Python 버전**: 3.11, 3.12
- **이유**: pyproject.toml에 `requires-python = ">=3.11"` 명시됨
- **전략**: Matrix strategy로 병렬 실행

#### FR-4: 의존성 캐싱
- **대상**: pip 패키지
- **목적**: 빌드 시간 단축 (30초 → 5초)
- **캐시 키**: Python 버전 + `pyproject.toml` 해시

### 3.2 비기능 요구사항

#### NFR-1: 빠른 피드백
- **목표**: 테스트 완료 시간 < 3분
- **방법**:
  - 의존성 캐싱
  - Unit test만 실행 (Integration test 제외)
  - 병렬 실행 (Python 3.11, 3.12)

#### NFR-2: 명확한 실패 메시지
- **요구사항**: 테스트 실패 시 구체적인 오류 위치 표시
- **방법**: `pytest -v` (verbose mode)

#### NFR-3: 보안
- **원칙**: API credential을 GitHub Actions에 저장하지 않음
- **이유**: Unit test는 API 호출이 필요 없으므로 credential 불필요

## 4. 기술 설계

### 4.1 Workflow 파일 구조

**파일 위치**: `.github/workflows/unit-tests.yml`

**기본 구조**:
```yaml
name: Unit Tests

on:
  pull_request:
    branches: [main, master]
    types: [opened, synchronize, reopened]

jobs:
  unit-tests:
    name: Unit Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          pytest korea_investment_stock/cache/test_cache_manager.py -v
          pytest korea_investment_stock/token_storage/test_token_storage.py -v -k "not redis_storage"
```

### 4.2 테스트 선택 전략

**포함되는 테스트**:
1. `cache/test_cache_manager.py` - 전체
   - 이유: 순수 메모리 캐시, 외부 의존성 없음

2. `token_storage/test_token_storage.py` - FileTokenStorage만
   - 명령어: `pytest -k "not redis_storage"`
   - 이유: fakeredis 사용, Redis 서비스 불필요

**제외되는 테스트**:
1. `test_korea_investment_stock.py` - API credential 필요
2. `test_integration_us_stocks.py` - API credential 필요
3. `cache/test_cached_integration.py` - API credential 필요

### 4.3 의존성 설치

**설치 방법**:
```bash
pip install -e ".[dev]"
```

**포함되는 패키지**:
- `requests`, `pandas` (core dependencies)
- `pytest>=7.0.0`, `pytest-mock>=3.10.0` (dev dependencies)
- `fakeredis>=2.10.0` (dev dependencies)

**Redis 의존성**:
- `redis` 패키지는 설치하지 않음 (`[redis]` optional dependency)
- `fakeredis`만 사용하여 Redis 테스트 진행

## 5. 구현 계획

### 5.1 작업 단계

#### Step 1: Workflow 파일 생성
- **파일**: `.github/workflows/unit-tests.yml`
- **내용**: 기본 pytest 실행 workflow
- **검증**: PR 생성하여 workflow 실행 확인

#### Step 2: 테스트 선택 검증
- **확인 사항**:
  1. `cache/test_cache_manager.py` 전체 실행 확인
  2. `token_storage/test_token_storage.py`에서 Redis 테스트 제외 확인
- **로컬 테스트**:
  ```bash
  pytest korea_investment_stock/cache/test_cache_manager.py -v
  pytest korea_investment_stock/token_storage/test_token_storage.py -v -k "not redis_storage"
  ```

#### Step 3: Matrix Strategy 추가
- **Python 버전**: 3.11, 3.12
- **병렬 실행**: 2개의 job이 동시에 실행됨

#### Step 4: 캐싱 최적화
- **캐시 설정**: `actions/setup-python`의 `cache: 'pip'`
- **효과 측정**: 초기 실행 vs 캐시 적중 시 실행 시간 비교

### 5.2 테스트 시나리오

#### 시나리오 1: 정상 케이스
1. PR 생성
2. Workflow 자동 실행
3. 모든 unit test 통과
4. PR merge 가능 상태

#### 시나리오 2: 테스트 실패
1. PR 생성 (버그 포함)
2. Workflow 실행
3. 테스트 실패
4. PR merge 차단
5. 개발자가 수정 후 push
6. Workflow 재실행

#### 시나리오 3: Python 버전별 차이
1. PR 생성
2. Python 3.11에서 통과, 3.12에서 실패
3. Matrix strategy로 두 버전 모두 테스트
4. 버전 호환성 문제 조기 발견

## 6. 성공 지표

### 6.1 정량적 지표
- **실행 시간**: < 3분 (목표)
- **캐시 적중률**: > 80%
- **테스트 커버리지**: Unit test 100% 자동 실행

### 6.2 정성적 지표
- PR에서 테스트 결과를 명확히 확인 가능
- 테스트 실패 시 구체적인 오류 메시지 제공
- 개발자 경험 향상 (빠른 피드백)

## 7. 위험 요소 및 대응

### 7.1 위험: Integration Test 오실행
- **설명**: API credential 필요한 테스트가 실행되어 실패
- **영향**: PR 차단, 개발자 혼란
- **대응**:
  - 테스트 파일명 규칙 명확화 (`test_integration_*.py`)
  - Workflow에서 명시적으로 unit test만 실행
  - 로컬에서 사전 검증

### 7.2 위험: Python 버전 호환성
- **설명**: 3.11에서 동작하지만 3.12에서 실패
- **영향**: 특정 Python 버전 사용자 문제 발생
- **대응**:
  - Matrix strategy로 두 버전 모두 테스트
  - 버전별 차이 조기 발견

### 7.3 위험: 의존성 설치 실패
- **설명**: `pip install -e ".[dev]"` 실패
- **영향**: Workflow 전체 실패
- **대응**:
  - 캐싱으로 재시도 시 빠른 복구
  - pip 업그레이드 선행 (`python -m pip install --upgrade pip`)

## 8. 향후 확장 계획

### 8.1 Coverage 리포트 추가
```yaml
- name: Run tests with coverage
  run: |
    pip install pytest-cov
    pytest --cov=korea_investment_stock --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

### 8.2 Integration Test Workflow (별도)
- **조건**: Manual trigger (`workflow_dispatch`)
- **Secrets**: API credentials를 GitHub Secrets에 저장
- **용도**: Release 전 full integration test

### 8.3 Pre-commit Hook 연동
```yaml
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## 9. 참고 자료

### 9.1 기존 Workflow
- `.github/workflows/label-merge-conflict.yml` - 구조 참고

### 9.2 유사 프로젝트
- pandas, requests 등 유명 Python 라이브러리의 CI/CD 설정

### 9.3 공식 문서
- [GitHub Actions - Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [pytest 공식 문서](https://docs.pytest.org/)

## 10. 결론

이 PRD는 korea-investment-stock 프로젝트에 PR 자동화 unit test를 도입하기 위한 계획을 정의합니다.

**핵심 원칙**:
1. **빠른 피드백**: < 3분 실행 시간
2. **안전한 실행**: API credential 불필요한 unit test만
3. **명확한 결과**: 실패 시 구체적인 오류 메시지
4. **확장 가능**: 향후 coverage, integration test 추가 가능

**다음 단계**:
1. `.github/workflows/unit-tests.yml` 파일 작성
2. 로컬에서 테스트 명령어 검증
3. PR 생성하여 실제 동작 확인
