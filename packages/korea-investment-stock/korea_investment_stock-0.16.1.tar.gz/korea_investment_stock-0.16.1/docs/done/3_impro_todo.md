# korea_investment_stock.py 리팩토링 TODO

> PRD: `3_impro_prd.md` | 구현 가이드: `3_impro_implementation.md`

---

## Phase 1: 즉시 정리 (삭제만) - 완료

### 1.1 사용 안 하는 import 제거
- [x] `import pickle` 삭제
- [x] `import datetime` 삭제
- [x] `import random` 삭제
- [x] `import time` 삭제
- [x] `from typing import List, Dict, Any` 삭제

### 1.2 DEPRECATED 메서드 제거
- [x] `__handle_rate_limit_error` 메서드 삭제

### 1.3 `__main__` 테스트 코드 제거
- [x] `if __name__ == "__main__":` 블록 전체 삭제

### 1.4 죽은 코드 제거
- [x] `fetch_symbols` 메서드 삭제 (self.exchange 속성이 존재하지 않음)

### 1.5 디버그 print 문을 logger.debug로 변경
- [x] `fetch_price_detail_oversea`의 `print(...)` → `logger.debug(...)` 변경
- [x] `fetch_stock_info`의 `print(e)` → `logger.debug(...)` 변경
- [x] `fetch_search_stock_info`의 `print(e)` → `logger.debug(...)` 변경

### 1.6 Phase 1 검증
- [x] `pytest` 실행 - 모든 테스트 통과
- [x] `python -c "from korea_investment_stock import KoreaInvestment"` 성공

**라인 감소**: 1342줄 → 1244줄 (98줄 감소)

---

## Phase 2: 상수 분리 - 완료

### 2.1 constants.py 생성
- [x] `korea_investment_stock/constants.py` 파일 생성
- [x] `EXCHANGE_CODE` → `EXCHANGE_CODE_QUOTE` 이름 변경 후 이동
- [x] `EXCHANGE_CODE2` → `EXCHANGE_CODE_ORDER` 이름 변경 후 이동
- [x] `EXCHANGE_CODE3` → `EXCHANGE_CODE_BALANCE` 이름 변경 후 이동
- [x] `EXCHANGE_CODE4` → `EXCHANGE_CODE_DETAIL` 이름 변경 후 이동
- [x] `CURRENCY_CODE` 이동
- [x] `MARKET_TYPE_MAP` 이동
- [x] `MARKET_TYPE`, `EXCHANGE_TYPE` 타입 정의 이동
- [x] `MARKET_CODE_MAP`, `EXCHANGE_CODE_MAP` 이동
- [x] `API_RETURN_CODE` 이동
- [x] 하위 호환성 alias 추가 (기존 이름 유지)

### 2.2 메인 파일 수정
- [x] `korea_investment_stock.py`에서 상수 정의 삭제
- [x] `from .constants import ...` 추가

### 2.3 Phase 2 검증
- [x] `pytest` 실행 - 모든 테스트 통과
- [x] `python -c "from korea_investment_stock.constants import MARKET_TYPE_MAP"` 성공

**라인 감소**: 1244줄 → 1110줄 (134줄 감소)

---

## Phase 3: 설정 로직 분리 - 완료

### 3.1 ConfigResolver 클래스 생성
- [x] `korea_investment_stock/config_resolver.py` 파일 생성
- [x] `ConfigResolver` 클래스 구현
- [x] `resolve()` 메서드 구현
- [x] `_merge_config()` 메서드 구현
- [x] `_load_default_config_file()` 메서드 구현
- [x] `_load_config_file()` 메서드 구현
- [x] `_load_from_env()` 메서드 구현

### 3.2 메인 파일 수정
- [x] `KoreaInvestment`에서 `_resolve_config` 관련 메서드 삭제
- [x] `KoreaInvestment`에서 `_merge_config` 삭제
- [x] `KoreaInvestment`에서 `_load_default_config_file` 삭제
- [x] `KoreaInvestment`에서 `_load_config_file` 삭제
- [x] `KoreaInvestment`에서 `_load_from_env` 삭제
- [x] `__init__`에서 `ConfigResolver` 사용하도록 수정

### 3.3 Phase 3 검증
- [x] `pytest` 실행 - 모든 테스트 통과
- [x] Config 관련 테스트 통과 확인

**라인 감소**: 1110줄 → 942줄 (168줄 감소)

---

## Phase 4: 파서 분리 - 완료

### 4.1 parsers 모듈 생성
- [x] `korea_investment_stock/parsers/` 디렉토리 생성
- [x] `korea_investment_stock/parsers/__init__.py` 생성
- [x] `korea_investment_stock/parsers/master_parser.py` 생성

### 4.2 파서 함수 구현
- [x] `parse_kospi_master()` 함수 이동
- [x] `parse_kosdaq_master()` 함수 이동

### 4.3 메인 파일 수정
- [x] `parse_kospi_master` 메서드 삭제
- [x] `parse_kosdaq_master` 메서드 삭제
- [x] parsers 모듈 import 추가
- [x] `fetch_kospi_symbols`에서 `parse_kospi_master` 함수 사용
- [x] `fetch_kosdaq_symbols`에서 `parse_kosdaq_master` 함수 사용

### 4.4 Phase 4 검증
- [x] `pytest` 실행 - 모든 테스트 통과

**라인 감소**: 942줄 → 793줄 (149줄 감소)

---

## Phase 5: IPO 헬퍼 분리 - 완료

### 5.1 ipo 모듈 생성
- [x] `korea_investment_stock/ipo/` 디렉토리 생성
- [x] `korea_investment_stock/ipo/__init__.py` 생성
- [x] `korea_investment_stock/ipo/ipo_helpers.py` 생성

### 5.2 IPO 헬퍼 함수 구현
- [x] `validate_date_format()` 함수 이동
- [x] `validate_date_range()` 함수 이동
- [x] `parse_ipo_date_range()` 함수 이동
- [x] `format_ipo_date()` 함수 이동
- [x] `calculate_ipo_d_day()` 함수 이동
- [x] `get_ipo_status()` 함수 이동
- [x] `format_number()` 함수 이동

### 5.3 메인 파일 수정
- [x] IPO 관련 정적 메서드 삭제
- [x] ipo 모듈 import 추가
- [x] `fetch_ipo_schedule`에서 import된 함수 사용

### 5.4 Phase 5 검증
- [x] `pytest` 실행 - 모든 테스트 통과
- [x] IPO 헬퍼 함수 동작 확인

**라인 감소**: 793줄 → 707줄 (86줄 감소)

---

## Phase 6: 최종 검증 - 완료

### 6.1 __init__.py 업데이트
- [x] 새로운 모듈 export 추가
- [x] 하위 호환성 확인

### 6.2 전체 테스트
- [x] `pytest` 전체 테스트 통과 (110 passed)

### 6.3 Import 테스트
- [x] `from korea_investment_stock import KoreaInvestment` 성공
- [x] `from korea_investment_stock.constants import MARKET_TYPE_MAP` 성공
- [x] `from korea_investment_stock.config_resolver import ConfigResolver` 성공
- [x] `from korea_investment_stock.parsers import parse_kospi_master` 성공
- [x] `from korea_investment_stock.ipo import parse_ipo_date_range` 성공

### 6.4 코드 품질 확인
- [x] `korea_investment_stock.py` 라인 수: 707줄 (목표 400줄보다 높지만 API 메서드가 많음)
- [x] 사용 안 하는 코드 제거 완료

---

## Phase 7: Token 모듈 리팩토링 - 완료

### 7.1 token_storage/ → token/ 폴더 변경
- [x] `token_storage/` → `token/` 이름 변경
- [x] `token_storage.py` → `storage.py` 이름 변경

### 7.2 TokenManager 클래스 분리
- [x] `token/manager.py` 파일 생성
- [x] 토큰 발급, 검증, 갱신 로직 이동
- [x] `KoreaInvestment`에서 `TokenManager` 사용

### 7.3 TokenStorage Factory 분리
- [x] `token/factory.py` 파일 생성
- [x] `create_token_storage()` 함수 구현
- [x] 설정에 따른 TokenStorage 생성 로직

### 7.4 Phase 7 검증
- [x] `pytest` 실행 - 모든 테스트 통과
- [x] Token 관련 테스트 통과 확인

**관련 PR**: #98

---

## Phase 8: IPO API 분리 - 완료

### 8.1 ipo_api.py 생성
- [x] `korea_investment_stock/ipo/ipo_api.py` 파일 생성
- [x] `fetch_ipo_schedule` 함수 분리

### 8.2 KoreaInvestment 수정
- [x] `fetch_ipo_schedule` 메서드에서 `ipo_api.fetch_ipo_schedule` 위임

### 8.3 Phase 8 검증
- [x] `pytest` 실행 - 모든 테스트 통과

**관련 PR**: #96

---

## 완료 체크리스트

- [x] Phase 1 완료 (즉시 정리)
- [x] Phase 2 완료 (상수 분리)
- [x] Phase 3 완료 (설정 로직 분리)
- [x] Phase 4 완료 (파서 분리)
- [x] Phase 5 완료 (IPO 헬퍼 분리)
- [x] Phase 6 완료 (최종 검증)
- [x] Phase 7 완료 (Token 모듈 리팩토링)
- [x] Phase 8 완료 (IPO API 분리)

---

## 리팩토링 결과 요약

| Phase | 작업 내용 | 라인 감소 |
|-------|----------|----------|
| Phase 1 | 즉시 정리 (사용 안 하는 코드 삭제) | 1342 → 1244 (98줄) |
| Phase 2 | 상수 분리 (constants.py) | 1244 → 1110 (134줄) |
| Phase 3 | 설정 로직 분리 (config_resolver.py) | 1110 → 942 (168줄) |
| Phase 4 | 파서 분리 (parsers/master_parser.py) | 942 → 793 (149줄) |
| Phase 5 | IPO 헬퍼 분리 (ipo/ipo_helpers.py) | 793 → 707 (86줄) |
| Phase 6 | 최종 검증 및 __init__.py 업데이트 | 707줄 유지 |
| Phase 7 | Token 모듈 리팩토링 (PR #98) | 707 → 692 (15줄) |
| Phase 8 | IPO API 분리 (PR #96) | ipo_api.py 추가 |
| **총계** | - | **1342 → 692 (650줄 감소, 48.4%)** |

### 최종 모듈 구조

```
korea_investment_stock/
├── __init__.py                    # 공개 API exports (121줄)
├── korea_investment_stock.py      # 692줄 (핵심 클래스)
├── constants.py                   # 상수 정의 (167줄)
├── config_resolver.py             # 설정 해결 로직 (186줄)
├── config/
│   ├── __init__.py
│   └── config.py                  # Config 클래스
├── parsers/
│   ├── __init__.py                # (8줄)
│   └── master_parser.py           # KOSPI/KOSDAQ 파싱 (159줄)
├── ipo/
│   ├── __init__.py                # (28줄)
│   ├── ipo_api.py                 # IPO API (109줄)
│   └── ipo_helpers.py             # IPO 헬퍼 함수 (142줄)
├── token/
│   ├── __init__.py                # (20줄)
│   ├── storage.py                 # TokenStorage 클래스들 (396줄)
│   ├── manager.py                 # TokenManager (185줄)
│   └── factory.py                 # create_token_storage (96줄)
├── cache/                         # 캐시 기능
└── rate_limit/                    # Rate Limiting
```
