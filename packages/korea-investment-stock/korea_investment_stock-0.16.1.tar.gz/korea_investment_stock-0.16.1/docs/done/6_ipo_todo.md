# IPO 모듈 리팩토링 TODO

## Phase 1: 코드 이동

- [x] `ipo/ipo_api.py` 파일 생성
  - [x] import 문 작성 (logging, datetime, requests)
  - [x] `fetch_ipo_schedule()` 함수 구현
  - [x] docstring 작성

- [x] `ipo/__init__.py` 업데이트
  - [x] `from .ipo_api import fetch_ipo_schedule` 추가
  - [x] `__all__`에 `fetch_ipo_schedule` 추가

- [x] `korea_investment_stock.py` 수정
  - [x] import 변경: `from .ipo import fetch_ipo_schedule as _fetch_ipo_schedule`
  - [x] 기존 `fetch_ipo_schedule` 메서드 삭제 (752-848줄)
  - [x] 새 `fetch_ipo_schedule` 위임 메서드 작성

## Phase 2: 테스트

- [x] 단위 테스트 통과 확인
  ```bash
  pytest -m "not integration"
  ```

- [ ] IPO 통합 테스트 통과 확인 (선택)
  ```bash
  pytest korea_investment_stock/tests/test_ipo_integration.py -v
  ```

## Phase 3: 정리

- [ ] CLAUDE.md 문서 업데이트 (필요시)
- [x] docs/start/6_ipo_prd.md → docs/done/ 이동
