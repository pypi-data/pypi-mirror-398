# Master 파일 캐싱 구현 TODO

> PRD: `3_master_prd.md` | 구현 가이드: `3_master_implementation.md`

## Phase 1: 핵심 캐싱 로직

- [x] 클래스 상수 추가
  - [x] `DEFAULT_MASTER_TTL_HOURS = 168` 추가
  - [x] 위치: `KoreaInvestment` 클래스 정의 시작 부분

- [x] `_should_download()` 메서드 추가
  - [x] 파라미터: `file_path`, `ttl_hours`, `force`
  - [x] 강제 다운로드 체크
  - [x] 파일 존재 여부 체크
  - [x] TTL 만료 체크 (mtime 기반)
  - [x] 반환: `bool`

- [x] `download_master_file()` 메서드 수정
  - [x] `ttl_hours` 파라미터 추가 (기본값: 168)
  - [x] `force_download` 파라미터 추가 (기본값: False)
  - [x] `os.chdir()` 제거 → 절대 경로 사용
  - [x] 파일 존재 시 삭제 로직 제거
  - [x] `_should_download()` 호출로 대체
  - [x] 캐시 히트 시 로그 출력 (`logger.info`)
  - [x] `with` 문으로 ZipFile 처리
  - [x] 반환 타입 `bool` 추가

## Phase 2: 공개 메서드 수정

- [x] `fetch_kospi_symbols()` 수정
  - [x] `ttl_hours` 파라미터 추가 (기본값: 168)
  - [x] `force_download` 파라미터 추가 (기본값: False)
  - [x] `download_master_file()` 호출 시 파라미터 전달
  - [x] 반환 타입 힌트 추가: `-> pd.DataFrame`
  - [x] docstring 업데이트

- [x] `fetch_kosdaq_symbols()` 수정
  - [x] `ttl_hours` 파라미터 추가 (기본값: 168)
  - [x] `force_download` 파라미터 추가 (기본값: False)
  - [x] `download_master_file()` 호출 시 파라미터 전달
  - [x] 반환 타입 힌트 추가: `-> pd.DataFrame`
  - [x] docstring 업데이트

- [x] `fetch_symbols()` 확인 (필요 시 수정) - 수정 불필요 (내부적으로 fetch_kospi/kosdaq 호출)

## Phase 3: 테스트

- [x] 테스트 파일 생성: `korea_investment_stock/test_master_cache.py`
  - [x] `test_should_download_file_not_exists` - 파일 없을 때
  - [x] `test_should_download_file_fresh` - 파일이 신선할 때
  - [x] `test_should_download_file_stale` - 파일이 오래됐을 때 (1주일 초과)
  - [x] `test_should_download_force` - 강제 다운로드
  - [x] `test_should_download_custom_ttl` - 커스텀 TTL

- [x] 기존 테스트 실행 확인
  - [x] `pytest korea_investment_stock/test_master_cache.py` 통과 (9/9 passed)

## Phase 4: 문서화 및 정리

- [x] CLAUDE.md 업데이트
  - [x] "Master 파일 캐싱" 섹션 추가
  - [x] 기본 사용법
  - [x] TTL 조정 예제
  - [x] 강제 다운로드 예제
  - [x] 로그 확인 방법

- [x] 코드 정리
  - [x] import 정리 (Path, datetime 이미 존재 확인)
  - [x] 타입 힌트 확인
  - [x] 불필요한 코드 제거

- [x] 커밋 완료
  - [x] 커밋 메시지: `[feat] Add master file caching for fetch_*_symbols()`

## 검증 체크리스트

- [x] 첫 번째 호출 시 다운로드됨 (로그 확인) - 테스트 통과
- [x] 두 번째 호출 시 캐시 사용 (로그 확인) - 테스트 통과
- [x] `force_download=True` 시 재다운로드됨 - 테스트 통과
- [x] 1주일 이후 자동 재다운로드됨 (mtime 조작으로 테스트) - 테스트 통과
- [x] 기존 기능 정상 동작 (종목 목록 반환) - API 시그니처 검증 완료
