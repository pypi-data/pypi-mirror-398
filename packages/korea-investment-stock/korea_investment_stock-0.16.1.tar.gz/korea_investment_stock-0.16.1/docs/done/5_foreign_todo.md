# 해외 주식 마스터 파일 다운로드 구현 TODO

## Phase 1: 파서 모듈 추가

- [x] `parsers/overseas_master_parser.py` 생성
  - [x] `OVERSEAS_MARKETS` 상수 정의 (11개 시장)
  - [x] `OVERSEAS_COLUMNS` 상수 정의 (24개 컬럼)
  - [x] `parse_overseas_stock_master()` 함수 구현
- [x] `parsers/__init__.py` export 추가
- [x] 단위 테스트 작성 (`parsers/test_overseas_master_parser.py`)
  - [x] 시장 코드 상수 테스트
  - [x] 컬럼 개수 테스트
  - [x] 파서 함수 mock 테스트

## Phase 2: KoreaInvestment 클래스 메서드 추가

- [x] `fetch_overseas_symbols(market, ttl_hours, force_download)` 메서드 추가
  - [x] 시장 코드 유효성 검증
  - [x] URL 생성 및 다운로드
  - [x] 파서 호출 및 DataFrame 반환
- [x] 편의 메서드 추가 (TODO: 전체 해외 시장 다운로드 기능 사용하기 시작하면 삭제 검토)
  - [x] `fetch_nasdaq_symbols()`
  - [x] `fetch_nyse_symbols()`
  - [x] `fetch_amex_symbols()`
- [x] import 문 추가 (`parse_overseas_stock_master`, `OVERSEAS_MARKETS`)

## Phase 3: Wrapper 호환성 확인

- [x] `CachedKoreaInvestment` 동작 확인
- [x] `RateLimitedKoreaInvestment` 동작 확인
- [x] 기존 `download_master_file()` 재활용 확인

## Phase 4: 테스트

- [x] 통합 테스트 작성 (`tests/test_overseas_symbols_integration.py`)
  - [x] 나스닥 다운로드 테스트
  - [x] 뉴욕 다운로드 테스트
  - [x] 캐시 동작 테스트
  - [x] 잘못된 시장 코드 에러 테스트
- [x] 전체 테스트 실행 (`pytest`)
- [x] 통합 테스트 실행 (`pytest -m integration`)

## Phase 5: 문서화

- [x] `__init__.py`에 `OVERSEAS_MARKETS` export 추가
- [x] 예제 파일 작성 (`examples/overseas_symbols_example.py`)
- [ ] CLAUDE.md 업데이트
  - [ ] API 메서드 목록에 추가
  - [ ] 사용 예시 추가
- [x] CHANGELOG.md 업데이트

## Phase 6: 최종 검증

- [x] 린트 검사 통과
- [x] 타입 힌트 확인
- [x] 전체 테스트 통과 확인
- [x] docs/start → docs/done 이동
