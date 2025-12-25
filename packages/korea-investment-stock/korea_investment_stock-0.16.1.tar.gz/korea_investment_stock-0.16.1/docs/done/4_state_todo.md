# 종목별 투자자매매동향(일별) API 구현 TODO

## 1단계: 핵심 API 구현

- [x] `korea_investment_stock/korea_investment_stock.py`에 `fetch_investor_trading_by_stock_daily` 메서드 추가
  - [x] docstring 작성 (Args, Returns, Example 포함)
  - [x] `_request_with_token_refresh` 메서드 사용
  - [x] TR ID: `FHPTJ04160001` 설정
  - [x] Query Parameters 설정 (FID_COND_MRKT_DIV_CODE, FID_INPUT_ISCD, FID_INPUT_DATE_1, FID_ORG_ADJ_PRC, FID_ETC_CLS_CODE)

## 2단계: 래퍼 클래스 추가

- [x] `korea_investment_stock/cache/cached_korea_investment.py`
  - [x] `fetch_investor_trading_by_stock_daily` 래퍼 메서드 추가
  - [x] 과거 날짜 데이터: 1시간 TTL
  - [x] 당일 데이터: `_price_ttl` 사용
- [x] `korea_investment_stock/rate_limit/rate_limited_korea_investment.py`
  - [x] `fetch_investor_trading_by_stock_daily` 래퍼 메서드 추가

## 3단계: 단위 테스트

- [x] `korea_investment_stock/tests/test_investor_trading.py`에 테스트 추가
  - [x] `TestFetchInvestorTradingByStockDaily` 클래스 생성
  - [x] `test_success_response`: 성공 응답 테스트
  - [x] `test_market_code_options`: 시장 코드 옵션 테스트 (J, NX, UN)
  - [x] `test_request_params`: 요청 파라미터 검증

## 4단계: 통합 테스트

- [x] `korea_investment_stock/tests/test_integration_investor.py` 신규 생성
  - [x] `TestInvestorTradingIntegration` 클래스 생성
  - [x] `@pytest.mark.integration` 마커 적용
  - [x] `test_samsung_investor_trading`: 삼성전자 투자자 매매동향 조회
  - [x] `test_different_market_codes`: 다양한 시장 코드 테스트

## 5단계: 문서 업데이트

- [x] `CLAUDE.md` 업데이트
  - [x] API 메서드 목록에 `fetch_investor_trading_by_stock_daily` 추가
- [x] `CHANGELOG.md` 업데이트
  - [x] `[Unreleased]` 섹션에 신규 기능 추가 기록

## 6단계: 테스트 실행 및 검증

- [x] 단위 테스트 실행: `pytest korea_investment_stock/tests/test_investor_trading.py -v`
- [ ] 통합 테스트 실행: `pytest korea_investment_stock/tests/test_integration_investor.py -v` (API 자격 증명 필요)
- [x] 전체 테스트 실행: `pytest -m "not integration"` (223 passed, 4 skipped)
