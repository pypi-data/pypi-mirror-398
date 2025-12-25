# 구현 문서: 주식 필드 추가 (거래량, 시가총액)

## 구현 범위

### 1. 테스트 Mock 데이터 수정

**파일**: `korea_investment_stock/test_integration_us_stocks.py`

#### 국내 주식 Mock 데이터
추가할 필드:
- `acml_vol`: 거래량
- `hts_avls`: 시가총액 (억원)

#### 해외 주식 Mock 데이터
추가할 필드:
- `tomv`: 시가총액
- `shar`: 상장주수

### 2. README.md 수정

**위치**: Response Format 섹션

#### Korean Stock (KR) 응답 예시
추가할 필드:
- `'acml_vol': '15234567'` - Volume (거래량)
- `'hts_avls': '3735468'` - Market cap (시가총액, 억원)

#### US Stock (US) 응답 예시
추가할 필드:
- `'tomv': '3250000000000'` - Market cap (시가총액)
- `'shar': '15384171000'` - Shares outstanding (상장주수)

### 3. CLAUDE.md 수정

**위치**: Error Handling Pattern 섹션 아래 또는 API Response Format 관련 섹션

추가할 내용:
- 국내/해외 주식 응답 필드 목록에 거래량, 시가총액 필드 추가

### 4. 예제 코드 수정

#### `examples/basic_example.py`
**위치**: `example_domestic_stock_price()` 함수

추가할 출력:
```python
print(f"  시가총액: {int(output['hts_avls']):,}억원")
```

#### `examples/us_stock_price_example.py`
**위치**: `example_basic_us_stock()`, `example_us_stock_details()` 함수

추가할 출력:
```python
print(f"  시가총액: ${float(output['tomv']):,.0f}")
print(f"  상장주수: {int(output['shar']):,}")
```

## 수정 파일 목록

| 순서 | 파일 | 수정 유형 |
|------|------|----------|
| 1 | `korea_investment_stock/test_integration_us_stocks.py` | Mock 데이터 필드 추가 |
| 2 | `README.md` | 문서 업데이트 |
| 3 | `CLAUDE.md` | 문서 업데이트 |
| 4 | `examples/basic_example.py` | 코드 수정 |
| 5 | `examples/us_stock_price_example.py` | 코드 수정 |

## 주의사항

- 기존 코드 구조 유지
- 새 필드는 기존 필드 뒤에 추가
- 한글 인코딩 UTF-8 확인
- 예제 실행 시 실제 API 호출하므로 필드 존재 여부는 API 응답에 의존
