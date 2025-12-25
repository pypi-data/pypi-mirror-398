# 토큰 자동 재발급 구현 체크리스트

## Phase 1: 핵심 메서드 구현

- [x] `_is_token_expired_response()` 헬퍼 메서드 추가
  - 파일: `korea_investment_stock/korea_investment_stock.py`
  - `rt_cd != '0'` 이고 `msg1`에 "기간이 만료된 token" 포함 시 True 반환

- [x] `_request_with_token_refresh()` 래퍼 메서드 추가
  - 파일: `korea_investment_stock/korea_investment_stock.py`
  - GET/POST 메서드 지원
  - 토큰 만료 시 `issue_access_token(force=True)` 호출 후 재시도
  - `max_retries` 파라미터로 재시도 횟수 제한 (기본 1회)

## Phase 2: API 메서드 적용

- [x] `fetch_domestic_price()` 수정
  - `requests.get()` → `_request_with_token_refresh("GET", ...)` 변경

- [x] `fetch_price_detail_oversea()` 수정
  - 거래소 순회 루프 내에서 래퍼 사용
  - `requests.get()` → `_request_with_token_refresh("GET", ...)` 변경

- [x] `fetch_stock_info()` 수정
  - 상품유형코드 순회 루프 내에서 래퍼 사용
  - `requests.get()` → `_request_with_token_refresh("GET", ...)` 변경

- [x] `fetch_search_stock_info()` 수정
  - `requests.get()` → `_request_with_token_refresh("GET", ...)` 변경

- [x] `fetch_ipo_schedule()` 수정
  - 메인 클래스에서 직접 처리 (ipo 모듈 위임 대신)
  - 토큰 재발급 로직 적용

## Phase 3: 테스트 작성

- [x] 테스트 파일 생성: `korea_investment_stock/tests/test_token_refresh.py`

- [x] 토큰 만료 응답 감지 테스트
  - `test_detects_expired_token`: 만료 메시지 감지
  - `test_detects_expired_token_with_period`: 마침표 포함 메시지 감지
  - `test_ignores_other_errors`: 다른 에러는 무시
  - `test_success_response_not_expired`: 성공 응답은 만료 아님
  - `test_missing_msg1_field`: msg1 필드 없는 경우

- [x] 자동 재발급 테스트
  - `test_refreshes_token_on_expiry`: 만료 시 재발급 후 재시도
  - `test_no_infinite_retry`: 재시도 횟수 제한 확인
  - `test_header_updated_after_refresh`: 헤더의 authorization 갱신 확인
  - `test_success_response_no_retry`: 성공 응답 시 재시도 없음
  - `test_post_request_with_token_refresh`: POST 요청 지원
  - `test_max_retries_zero`: max_retries=0 동작 확인

- [x] issue_access_token force 옵션 테스트
  - `test_issue_access_token_force_true`: 강제 재발급
  - `test_issue_access_token_force_false`: 기존 동작
  - `test_issue_access_token_default_no_force`: 기본값 확인

- [x] 테스트 실행 및 통과 확인 (14 passed)
  ```bash
  pytest korea_investment_stock/tests/test_token_refresh.py -v
  ```

## Phase 4: 문서화

- [x] CHANGELOG.md 업데이트
  - API 호출 중 토큰 만료 시 자동 재발급 기능 추가
  - 적용된 API 메서드 목록
  - 로깅 방법

- [x] CLAUDE.md 업데이트
  - "Automatic Token Refresh" 섹션 추가
  - Problem/Solution 설명
  - Applied Methods 목록
  - Force Token Refresh 사용법
  - 로깅 활성화 방법

## 검증

- [x] 기존 테스트 통과 확인 (211 passed, 4 skipped)
  ```bash
  pytest -m "not integration"
  ```

- [ ] 수동 검증 (선택)
  - 토큰 파일의 timestamp를 과거로 수정
  - API 호출 시 자동 재발급 확인
  - 로그에서 "토큰 만료 감지, 재발급 시도..." 메시지 확인
