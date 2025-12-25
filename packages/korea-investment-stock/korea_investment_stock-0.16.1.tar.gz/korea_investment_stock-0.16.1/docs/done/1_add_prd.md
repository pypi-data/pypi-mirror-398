# PRD: 주식 필드 추가 (거래량, 시가총액)

## 개요

현재 `korea_investment_stock` 라이브러리의 테스트 및 예제 코드에서 일부 주요 필드가 누락되어 있음. API는 해당 필드를 반환하지만, 테스트 mock 데이터와 문서에서 활용되지 않고 있어 사용자가 해당 필드의 존재를 인지하기 어려움.

## 현황 분석

### 국내 주식 (KR) - `fetch_domestic_price()` / `fetch_price(symbol, "KR")`

| 필드 | API 키 | 설명 | 현재 상태 |
|------|--------|------|-----------|
| 현재가 | `stck_prpr` | 주식 현재가 | ✅ 테스트/예제에서 사용 |
| 등락률 | `prdy_ctrt` | 전일 대비율 (%) | ✅ 테스트/예제에서 사용 |
| 거래량 | `acml_vol` | 누적 거래량 | ⚠️ examples만 사용, 테스트 미포함 |
| 시가총액 | `hts_avls` | HTS 시가총액 | ❌ 미사용 |

### 해외 주식 (US) - `fetch_price_detail_oversea()` / `fetch_price(symbol, "US")`

| 필드 | API 키 | 설명 | 현재 상태 |
|------|--------|------|-----------|
| 현재가 | `last` | 현재가 | ✅ 테스트/예제에서 사용 |
| 등락률 | `t_xrat` | 원환산 당일등락 (%) | ✅ 테스트/예제에서 사용 |
| 거래량 | `tvol` | 거래량 | ✅ 테스트에서 사용 |
| 시가총액 | `tomv` | 시가총액 | ❌ 미사용 |
| 상장주수 | `shar` | 상장주수 | ❌ 미사용 (시가총액 계산용) |

## 요구사항

### 1. 테스트 Mock 데이터 보강

**파일**: `korea_investment_stock/test_integration_us_stocks.py`

#### 1.1 국내 주식 Mock 데이터에 필드 추가

```python
kr_response = {
    'rt_cd': '0',
    'msg1': '정상처리 되었습니다.',
    'output1': {
        'stck_shrn_iscd': '005930',
        'stck_prpr': '62600',      # 현재가
        'prdy_vrss': '1600',       # 전일대비
        'prdy_ctrt': '2.62',       # 등락률
        'acml_vol': '15234567',    # 거래량 (추가)
        'hts_avls': '3735468',     # 시가총액 (추가, 단위: 억원)
    }
}
```

#### 1.2 해외 주식 Mock 데이터에 필드 추가

```python
us_response = {
    'rt_cd': '0',
    'msg1': '정상처리 되었습니다.',
    'output': {
        'rsym': 'DNASAAPL',
        'last': '211.1600',        # 현재가
        't_xdif': '1720',          # 전일대비
        't_xrat': '-0.59',         # 등락률
        'tvol': '39765812',        # 거래량
        'tomv': '3250000000000',   # 시가총액 (추가)
        'shar': '15384171000',     # 상장주수 (추가)
        'perx': '32.95',
        'pbrx': '47.23',
    }
}
```

### 2. README 문서 업데이트

**파일**: `README.md`

#### 2.1 국내 주식 응답 예시 보강

```python
'output1': {
    'stck_prpr': '62600',      # Current price (현재가)
    'prdy_vrss': '1600',       # Change from previous day (전일대비)
    'prdy_ctrt': '2.62',       # Change rate (%) (등락률)
    'stck_oprc': '61000',      # Opening price (시가)
    'stck_hgpr': '63000',      # High price (고가)
    'stck_lwpr': '60500',      # Low price (저가)
    'acml_vol': '15234567',    # Volume (거래량)
    'hts_avls': '3735468',     # Market cap (시가총액, 억원)
    # ... more fields
}
```

#### 2.2 해외 주식 응답 예시 보강

```python
'output': {
    'rsym': 'DNASAAPL',        # Exchange + Symbol
    'last': '211.16',          # Current price (현재가)
    'open': '210.56',          # Opening price (시가)
    'high': '212.13',          # High price (고가)
    'low': '209.86',           # Low price (저가)
    'tvol': '39765812',        # Volume (거래량)
    't_xdif': '1.72',          # Change (전일대비)
    't_xrat': '-0.59',         # Change rate (%) (등락률)
    'tomv': '3250000000000',   # Market cap (시가총액)
    'shar': '15384171000',     # Shares outstanding (상장주수)
    'perx': '32.95',           # PER
    'pbrx': '47.23',           # PBR
    # ... more fields
}
```

### 3. CLAUDE.md 업데이트

**파일**: `CLAUDE.md`

API Response Format 섹션에 거래량/시가총액 필드 문서화 추가.

### 4. 예제 코드 업데이트

#### 4.1 국내 주식 예제

**파일**: `examples/basic_example.py`

시가총액 출력 추가:

```python
# example_domestic_stock_price() 함수 내
if result['rt_cd'] == '0':
    output = result.get('output', {})
    print(f"\n✅ 삼성전자 (005930) 현재가:")
    print(f"  현재가: {int(output['stck_prpr']):,}원")
    print(f"  전일대비: {output['prdy_vrss']} ({output['prdy_ctrt']}%)")
    print(f"  시가: {int(output['stck_oprc']):,}원")
    print(f"  고가: {int(output['stck_hgpr']):,}원")
    print(f"  저가: {int(output['stck_lwpr']):,}원")
    print(f"  거래량: {int(output['acml_vol']):,}주")
    print(f"  시가총액: {int(output['hts_avls']):,}억원")  # 추가
```

#### 4.2 해외 주식 예제

**파일**: `examples/us_stock_price_example.py`

시가총액 출력 추가:

```python
# example_basic_us_stock() 함수 내
if result['rt_cd'] == '0':
    output = result['output']
    print(f"\n📈 AAPL (애플) 현재가 정보:")
    print(f"  현재가: ${output['last']}")
    print(f"  시가: ${output['open']}")
    print(f"  고가: ${output['high']}")
    print(f"  저가: ${output['low']}")
    print(f"  거래량: {int(output['tvol']):,}")
    print(f"  전일대비: {output['t_xdif']} ({output['t_xrat']}%)")
    print(f"  시가총액: ${float(output['tomv']):,.0f}")  # 추가
    print(f"  상장주수: {int(output['shar']):,}")        # 추가

# example_us_stock_details() 함수 내 - 시가총액 계산 방식도 추가
market_cap_calculated = float(output['shar']) * float(output['last'])
print(f"  시가총액 (API): ${float(output['tomv']):,.0f}")
print(f"  시가총액 (계산): ${market_cap_calculated:,.0f}")
```

## 수정 대상 파일

| 파일 | 수정 내용 | 우선순위 |
|------|----------|----------|
| `korea_investment_stock/test_integration_us_stocks.py` | Mock 데이터에 필드 추가 | P1 |
| `README.md` | 응답 예시에 필드 추가 | P1 |
| `CLAUDE.md` | API 응답 형식 문서화 | P1 |
| `examples/basic_example.py` | 시가총액 출력 추가 | P1 |
| `examples/us_stock_price_example.py` | 시가총액/상장주수 출력 추가 | P1 |

## 참고: API 문서

- **국내 주식**: `FHKST01010100` (주식현재가시세)
- **해외 주식**: `HHDFS76200200` (해외주식 현재가상세)
  - API 문서: `docs/api/해외주식 현재가상세_v1_해외주식-029.md`

## 비고

- 라이브러리는 raw API 응답을 그대로 반환하므로, 코드 변경 없이 해당 필드 접근 가능
- 이 작업은 **문서화 및 테스트 보강** 목적
- 실제 API 응답값은 한국투자증권 서버에서 결정됨
