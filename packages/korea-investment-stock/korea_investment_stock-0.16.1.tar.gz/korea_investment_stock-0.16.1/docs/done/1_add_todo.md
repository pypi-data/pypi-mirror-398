# TODO: 주식 필드 추가 (거래량, 시가총액)

## 1단계: 테스트 Mock 데이터 수정

- [x] `korea_investment_stock/test_integration_us_stocks.py` 파일 열기
- [x] 국내 주식 Mock 데이터에 필드 추가
  - [x] `'acml_vol': '15234567'` 추가
  - [x] `'hts_avls': '3735468'` 추가
- [x] 해외 주식 Mock 데이터에 필드 추가
  - [x] `'tomv': '3250000000000'` 추가
  - [x] `'shar': '15384171000'` 추가
- [x] 테스트 실행하여 기존 테스트 통과 확인
  ```bash
  pytest korea_investment_stock/test_integration_us_stocks.py -v
  ```

## 2단계: README.md 문서 수정

- [x] `README.md` 파일 열기
- [x] Korean Stock (KR) 응답 예시 섹션 찾기
- [x] 국내 주식 필드 추가
  - [x] `'acml_vol': '15234567'` 추가 (Volume)
  - [x] `'hts_avls': '3735468'` 추가 (Market cap)
- [x] US Stock (US) 응답 예시 섹션 찾기
- [x] 해외 주식 필드 추가
  - [x] `'tomv': '3250000000000'` 추가 (Market cap)
  - [x] `'shar': '15384171000'` 추가 (Shares outstanding)

## 3단계: CLAUDE.md 문서 수정

- [x] `CLAUDE.md` 파일 열기
- [x] API Response Format 관련 섹션 찾기
- [x] 국내 주식 응답 필드에 거래량, 시가총액 추가
- [x] 해외 주식 응답 필드에 시가총액, 상장주수 추가

## 4단계: 예제 코드 수정

### 4.1 국내 주식 예제
- [x] `examples/basic_example.py` 파일 열기
- [x] `example_domestic_stock_price()` 함수 찾기
- [x] 시가총액 출력 라인 추가
  ```python
  print(f"  시가총액: {int(output['hts_avls']):,}억원")
  ```

### 4.2 해외 주식 예제
- [x] `examples/us_stock_price_example.py` 파일 열기
- [x] `example_basic_us_stock()` 함수 찾기
- [x] 시가총액, 상장주수 출력 라인 추가
  ```python
  print(f"  시가총액: ${float(output['tomv']):,.0f}")
  print(f"  상장주수: {int(output['shar']):,}")
  ```
- [x] `example_us_stock_details()` 함수에 시가총액 계산 방식 추가 (선택)

## 5단계: 검증

- [x] 테스트 전체 실행
  ```bash
  pytest korea_investment_stock/ -v
  ```
- [ ] 예제 코드 실행 테스트 (API 키 필요)
  ```bash
  python examples/basic_example.py
  python examples/us_stock_price_example.py
  ```
- [x] 한글 인코딩 확인
  ```bash
  file -I docs/start/1_add_*.md
  ```

## 완료 기준

- [x] 모든 테스트 통과
- [x] 문서에 새 필드 반영됨
- [x] 예제 코드에 시가총액 출력 추가됨
- [x] 한글 인코딩 UTF-8 확인됨
