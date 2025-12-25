# fetch_price_detail_oversea 리팩토링 TODO

## 1단계: constants.py 수정

- [x] EXCD 상수 키 변경 (`"NYSE"` → `"NYS"`, `"NASDAQ"` → `"NAS"` 등)
- [x] EXCD_BY_COUNTRY 상수 추가
- [x] __init__.py에 EXCD_BY_COUNTRY export 추가

## 2단계: korea_investment_stock.py 수정

- [x] EXCD_BY_COUNTRY import 추가
- [x] fetch_price_detail_oversea 인자명 변경 (`market` → `country_code`)
- [x] 기본값 변경 (`"KR"` → `"US"`)
- [x] KR/KRX 체크 로직 제거
- [x] EXCD_BY_COUNTRY를 활용한 거래소 순회 로직 적용
- [x] ValueError 메시지 한글화
- [x] docstring 업데이트 (Query Parameters, Returns, Raises 포함)
- [x] return type hint 추가 (`-> dict`)

## 3단계: Wrapper 클래스 수정

- [x] cached_korea_investment.py: `market` → `country_code` 변경
- [x] cached_korea_investment.py: 기본값 `"US"` 적용
- [x] rate_limited_korea_investment.py: `market` → `country_code` 변경
- [x] rate_limited_korea_investment.py: 기본값 `"US"` 적용

## 4단계: 테스트 수정

- [x] 기존 테스트에서 `market` → `country_code` 변경
- [x] 에러 메시지 변경 반영 (한글화)
- [x] `fetch_price_detail_oversea("AAPL")` 기본값 테스트 추가
- [x] `fetch_price_detail_oversea("AAPL", country_code="US")` 테스트
- [x] 홍콩 주식 테스트 (`country_code="HK"`)
- [x] 일본 주식 테스트 (`country_code="JP"`)
- [x] 중국 주식 테스트 (`country_code="CN"`)
- [x] 베트남 주식 테스트 (`country_code="VN"`)
- [x] 지원하지 않는 country_code에 대한 ValueError 테스트
- [x] CachedKoreaInvestment 래퍼 테스트
- [x] RateLimitedKoreaInvestment 래퍼 테스트

## 5단계: 문서 업데이트

- [x] CLAUDE.md 메서드 시그니처 업데이트 (`market` → `country_code`)
- [x] CHANGELOG.md에 Breaking Changes 추가
- [x] examples/ 예제 코드 확인 (수정 불필요 - fetch_price 사용)

## 6단계: 검증

- [x] `pytest` 전체 테스트 통과 확인
- [x] 기존 테스트 통과 확인
- [x] 신규 테스트 통과 확인
