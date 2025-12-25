# 환경 변수 설정 방식 개선 TODO

## Phase 1: 환경변수 자동 감지 (v0.9.0)

- [x] `KoreaInvestment.__init__()` 파라미터 기본값을 `None`으로 변경
- [x] 환경 변수 자동 감지 로직 추가 (`api_key or os.getenv(...)`)
- [x] 필수값 누락 시 명확한 에러 메시지 출력
- [x] 단위 테스트 작성
  - [x] 환경 변수만으로 초기화 테스트
  - [x] 생성자 파라미터 우선순위 테스트
  - [x] 혼합 사용 테스트 (일부 파라미터 + 환경변수)
- [x] 기존 테스트 통과 확인
- [x] README 업데이트

---

## Phase 2: Config 클래스 추가 (v1.0.0)

- [x] `pyyaml>=6.0` 의존성 추가 (`pyproject.toml`)
- [x] `korea_investment_stock/config.py` 파일 생성
  - [x] `Config` dataclass 정의
  - [x] `from_env()` 메서드 구현
  - [x] `from_yaml()` 메서드 구현
  - [x] `to_dict()`, `to_yaml()` 메서드 구현
- [x] `__init__.py`에서 `Config` 클래스 export
- [x] 단위 테스트 작성
  - [x] YAML 파일 로딩 테스트
  - [x] 환경 변수 로딩 테스트
  - [x] 잘못된 파일 형식 에러 처리 테스트
- [x] 사용 예제 추가 (`examples/config_example.py`)

---

## Phase 3: Hybrid 통합 (v1.1.0)

- [x] `KoreaInvestment.__init__()` 에 `config`, `config_file` 파라미터 추가
- [x] `_resolve_config()` 메서드 구현 (우선순위 로직)
- [x] `_load_config_file()` 메서드 구현 (확장자별 로더 선택)
- [x] `DEFAULT_CONFIG_PATHS` 상수 정의
- [x] 단위 테스트 작성
  - [x] 5단계 우선순위 테스트
  - [x] 기본 경로 자동 탐색 테스트
  - [x] config 객체 주입 테스트
- [x] 통합 테스트 작성
- [x] CLAUDE.md 업데이트
- [x] CHANGELOG.md 업데이트
