# fetch_stock_info, fetch_search_stock_info 개선 작업 체크리스트

## 1단계: constants.py 수정

- [x] `OVRS_EXCG_CD` 키 변경
  - [x] `"NASDAQ"` → `"NASD"`
  - [x] `"HONGKONG"` → `"SEHK"`
  - [x] `"TOKYO"` → `"TKSE"`
  - [x] `"SHANGHAI"` → `"SHAA"`
  - [x] `"SHENZHEN"` → `"SZAA"`
  - [x] `"HANOI"` → `"HASE"`
  - [x] `"HOCHIMINH"` → `"VNSE"`

- [x] `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY` 변경
  - [x] 변수명 변경
  - [x] `PRDT_TYPE_CD` 상수 참조 사용
  - [x] 거래소 코드 키 제거 (NASDAQ, NYSE, AMEX, TYO, HKEX, HNX, HSX, SSE, SZSE)
  - [x] 국가 코드만 유지 (KR, KRX, US, JP, HK, CN, VN)

## 2단계: korea_investment_stock.py 메서드 수정

- [x] import 문 변경
  - [x] `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY`

- [x] `fetch_stock_info` 메서드 수정
  - [x] 인자 `market` → `country_code` 변경
  - [x] 반환 타입 힌트 `-> dict` 추가
  - [x] docstring 추가 (API 정보, Query Parameters, Args, Returns, Raises, Example)
  - [x] 내부 변수명 `market_code` → `prdt_type_cd` 변경
  - [x] `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY` 변경

- [x] `fetch_search_stock_info` 메서드 수정
  - [x] 인자 `market` → `country_code` 변경
  - [x] 반환 타입 힌트 `-> dict` 추가
  - [x] docstring 확장 (API 정보, Query Parameters, Args, Returns, Raises, Example)
  - [x] 에러 메시지 업데이트 (`market` → `country_code`)
  - [x] 내부 변수명 `market_` → `prdt_type_cd` 변경
  - [x] `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY` 변경

## 3단계: 래퍼 클래스 수정

- [x] `cached_korea_investment.py` 수정
  - [x] `fetch_stock_info` 인자 변경 (`market` → `country_code`)
  - [x] `fetch_search_stock_info` 인자 변경 (`market` → `country_code`)

- [x] `rate_limited_korea_investment.py` 수정
  - [x] `fetch_stock_info` 인자 변경 (`market` → `country_code`)
  - [x] `fetch_search_stock_info` 인자 변경 (`market` → `country_code`)
  - [x] docstring 업데이트

## 4단계: 테스트 작성/수정

- [x] 단위 테스트 확인
  - [x] 기존 테스트가 위치 인자 사용으로 호환성 유지
  - [x] 단위 테스트 82개 통과 확인

- [x] __init__.py 수정
  - [x] `MARKET_TYPE_MAP` → `PRDT_TYPE_CD_BY_COUNTRY` export 변경

## 5단계: 문서 업데이트

- [x] CLAUDE.md 업데이트
  - [x] 메서드 시그니처 변경 반영

- [x] CHANGELOG.md 업데이트
  - [x] Breaking Changes 섹션 추가
  - [x] Changed 섹션에 변경 내용 기록

## 6단계: 최종 검증

- [x] 단위 테스트 실행 및 통과
  - [x] `pytest korea_investment_stock/rate_limit/test_rate_limiter.py korea_investment_stock/cache/test_cache_manager.py korea_investment_stock/config/ -v`

## 완료 후

- [ ] 요구사항 문서 → done 폴더로 이동
  - [ ] `6_stock_prd.md` → `docs/done/`
  - [ ] `6_stock_implementation.md` → `docs/done/`
  - [ ] `6_stock_todo.md` → 삭제 또는 `docs/done/`
