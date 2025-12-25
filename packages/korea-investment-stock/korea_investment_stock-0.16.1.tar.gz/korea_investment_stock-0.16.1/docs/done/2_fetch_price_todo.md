# fetch_domestic_price 병합 TODO

## Phase 1: 핵심 메서드 수정

- [x] `korea_investment_stock/korea_investment_stock.py` 수정
  - [x] `fetch_domestic_price` 시그니처 변경: `(symbol, symbol_type="Stock")`
  - [x] `TR_ID_MAP` 딕셔너리 추가
  - [x] `FID_COND_MRKT_DIV_CODE_STOCK["KRX"]` 상수 사용
  - [x] import 문 추가: `from .constants import FID_COND_MRKT_DIV_CODE_STOCK`
  - [x] `fetch_price` 메서드 호출 수정: `fetch_domestic_price(symbol, symbol_type)`
  - [x] `fetch_etf_domestic_price` 메서드 삭제

## Phase 2: 래퍼 클래스 수정

- [x] `korea_investment_stock/cache/cached_korea_investment.py` 수정
  - [x] `fetch_domestic_price` 시그니처 변경
  - [x] `fetch_etf_domestic_price` 메서드 삭제

- [x] `korea_investment_stock/rate_limit/rate_limited_korea_investment.py` 수정
  - [x] `fetch_domestic_price` 시그니처 변경
  - [x] `fetch_etf_domestic_price` 메서드 삭제

## Phase 3: 테스트

- [x] 핵심 단위 테스트 통과 (25 passed)
- [ ] 통합 테스트: 삼성전자(005930) 조회 확인 (API 자격증명 필요)
- [ ] 통합 테스트: KODEX 200 ETF(069500) 조회 확인 (API 자격증명 필요)

## Phase 4: 문서 정리

- [ ] CHANGELOG.md 업데이트 (Breaking Changes 명시)
- [ ] CLAUDE.md API 문서 업데이트
- [ ] PRD 파일 docs/done 폴더로 이동
