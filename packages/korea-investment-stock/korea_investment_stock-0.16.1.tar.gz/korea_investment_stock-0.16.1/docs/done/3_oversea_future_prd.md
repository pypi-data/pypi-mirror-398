# 해외선물 API 구현 PRD

## 1. 개요

### 1.1 목표
한국투자증권 OpenAPI의 **해외선물옵션** API를 `korea-investment-stock` 라이브러리에 구현하여, 미국 선물(나스닥, S&P500, 원유, 금 등) 시세 조회 및 거래 기능을 제공한다.

### 1.2 배경
- 현재 라이브러리: 국내 주식, 해외 주식(미국/홍콩/일본 등) 지원
- **해외선물**: 미지원 상태
- 사용자 요청: 미국 선물(CME, NYMEX 등) 시세 조회 필요

### 1.3 참고 자료
- **API 문서 위치**: `docs/api/해외선물옵션/` (35개 API 문서)
- **한국투자증권 공식 문서**: https://apiportal.koreainvestment.com
- **종목 마스터 파일**: https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/overseas_future_code.py

---

## 2. 지원 거래소 및 상품

### 2.1 거래소

> **⚠️ 중요: 해외선물 시세는 대부분 유료입니다.**
>
> CME, SGX 거래소 API 시세는 **유료 시세**로 HTS/MTS에서 유료 가입이 필요합니다.
> 유료 가입하지 않은 경우 API 호출 시 `"CME SUB거래소 신청 계좌가 아닙니다."` 오류가 발생합니다.

| 거래소 | 코드 | 주요 상품 | 시세 |
|--------|------|----------|------|
| CME (시카고상업거래소) | CME | E-mini S&P500, E-mini 나스닥, 유로FX | **유료** |
| NYMEX (뉴욕상업거래소) | NYM | WTI 원유, 천연가스 | **유료** |
| COMEX | CMX | 금, 은, 구리 | **유료** |
| CBOT (시카고상품거래소) | CBT | 옥수수, 대두, 소맥 | **유료** |
| SGX (싱가포르거래소) | SGX | 니케이225, MSCI 대만 | **유료** |
| EUREX | EUX | 유로스톡스50, DAX | 유료 |
| ICE | ICE | 브렌트유, 코코아 | 유료 |

### 2.2 인기 상품 (우선 구현 대상)

아래 인기 상품들을 우선적으로 지원합니다:

| 우선순위 | 상품 | 종목코드 예시 | 거래소 | 설명 |
|----------|------|--------------|--------|------|
| 1 | **금 선물** | GCG25 | COMEX | 금 선물 (2025년 2월물) |
| 2 | **WTI 원유** | CLG25 | NYMEX | WTI 원유선물 |
| 3 | **천연가스** | NGG25 | NYMEX | 천연가스 선물 |
| 4 | **E-mini S&P500** | ESH25 | CME | S&P500 미니선물 (2025년 3월물) |
| 5 | **E-mini 나스닥** | NQH25 | CME | 나스닥100 미니선물 |
| 6 | 유로/달러 | 6EH25 | CME | 유로 FX 선물 |
| 7 | 미국채 30년 | ZBH25 | CBOT | 미국 국채 선물 |

### 2.3 종목코드 규칙

```
[상품코드 2자리][월물코드 1자리][연도 2자리]

예: ESH25
- ES: E-mini S&P500
- H: 3월물 (F=1월, G=2월, H=3월, J=4월, K=5월, M=6월, N=7월, Q=8월, U=9월, V=10월, X=11월, Z=12월)
- 25: 2025년
```

---

## 3. API 구현 범위

### 3.1 Phase 1: 시세 조회 (MVP)

| API | TR ID | 설명 | 우선순위 |
|-----|-------|------|----------|
| 해외선물종목현재가 | `HHDFC55010000` | 현재가, 고/저/시가, 거래량 | **P0** |
| 해외선물_호가 | `HHDFC86000000` | 매수/매도 호가 | P1 |
| 해외선물_상품기본정보 | `HHDFC55200000` | 증거금, 틱사이즈, 만기일 | P1 |
| 해외선물종목상세 | - | 종목 상세 정보 | P1 |

### 3.2 Phase 2: 차트/추이 데이터

| API | 설명 | 우선순위 |
|-----|------|----------|
| 해외선물_분봉조회 | 분봉 차트 데이터 | P2 |
| 해외선물_체결추이(틱) | 틱 단위 체결 | P2 |
| 해외선물_체결추이(일간) | 일별 시세 | P2 |
| 해외선물_미결제추이 | 미결제약정 추이 | P3 |

### 3.3 Phase 3: 주문/계좌 (선택적)

| API | 설명 | 우선순위 |
|-----|------|----------|
| 해외선물옵션_주문 | 선물 주문 | P3 |
| 해외선물옵션_정정취소주문 | 주문 정정/취소 | P3 |
| 해외선물옵션_주문가능조회 | 주문 가능 수량 | P3 |
| 해외선물옵션_미결제내역조회 | 잔고 조회 | P3 |
| 해외선물옵션_예수금현황 | 예수금 조회 | P3 |

### 3.4 Phase 4: 실시간 (WebSocket)

| API | 설명 | 우선순위 |
|-----|------|----------|
| 해외선물옵션_실시간체결가 | 실시간 체결 | P4 |
| 해외선물옵션_실시간호가 | 실시간 호가 | P4 |

> **Note**: WebSocket 실시간 API는 별도 모듈로 분리 고려

---

## 4. API 설계

### 4.1 시세 조회 메서드

```python
def fetch_overseas_future_price(
    self,
    symbol: str
) -> Dict[str, Any]:
    """해외선물 현재가 조회

    Args:
        symbol: 종목코드 (예: "ESH25", "GCG25")

    Returns:
        API 응답 딕셔너리

    Example:
        >>> result = broker.fetch_overseas_future_price("ESH25")
        >>> if result['rt_cd'] == '0':
        ...     print(f"현재가: {result['output1']['last_price']}")
    """
```

### 4.2 호가 조회 메서드

```python
def fetch_overseas_future_orderbook(
    self,
    symbol: str
) -> Dict[str, Any]:
    """해외선물 호가 조회

    Args:
        symbol: 종목코드

    Returns:
        호가 정보 (매수/매도 호가, 수량)
    """
```

### 4.3 상품 기본정보 조회

```python
def fetch_overseas_future_info(
    self,
    symbols: List[str]
) -> Dict[str, Any]:
    """해외선물 상품 기본정보 조회 (최대 32개)

    Args:
        symbols: 종목코드 리스트

    Returns:
        거래소, 증거금, 틱사이즈, 만기일 등
    """
```

### 4.4 분봉 조회

```python
def fetch_overseas_future_minute_chart(
    self,
    symbol: str,
    period: str = "1"  # 1, 3, 5, 10, 15, 30, 60분
) -> Dict[str, Any]:
    """해외선물 분봉 조회

    Args:
        symbol: 종목코드
        period: 분봉 주기

    Returns:
        분봉 데이터
    """
```

---

## 5. 구현 상세

### 5.1 API 엔드포인트

```python
# 해외선물 Base URL
BASE_URL = "https://openapi.koreainvestment.com:9443"

# 시세 조회
FUTURE_PRICE_URL = "/uapi/overseas-futureoption/v1/quotations/inquire-price"
FUTURE_ORDERBOOK_URL = "/uapi/overseas-futureoption/v1/quotations/inquire-asking-price"
FUTURE_INFO_URL = "/uapi/overseas-futureoption/v1/quotations/search-contract-detail"
```

### 5.2 TR ID 매핑

```python
TR_IDS = {
    "overseas_future_price": "HHDFC55010000",
    "overseas_future_orderbook": "HHDFC86000000",
    "overseas_future_info": "HHDFC55200000",
    # ... 추가
}
```

### 5.3 소수점 처리 (중요)

해외선물 시세는 **계산 소수점** 값을 적용해야 정확한 가격을 얻을 수 있음:

```python
# ffcode.mst 파일의 sCalcDesz(계산 소수점) 값 참고
# 품목코드 6A 계산소수점 -4 → 시세 6882.5 → 0.68825
# 품목코드 GC 계산소수점 -1 → 시세 19225 → 1922.5

def convert_price(raw_price: str, calc_decimal: int) -> float:
    """시세 소수점 변환"""
    return float(raw_price) * (10 ** calc_decimal)
```

### 5.4 종목 마스터 파일

해외선물 종목코드 조회를 위해 마스터 파일 다운로드 필요:

```python
def fetch_overseas_future_symbols(
    self,
    ttl_hours: int = 24,
    force_download: bool = False
) -> pd.DataFrame:
    """해외선물 종목 마스터 파일 다운로드

    Returns:
        종목코드, 상품명, 거래소, 소수점 등 정보
    """
```

- **파일명**: `ffcode.mst`
- **다운로드**: 포럼 > FAQ > 종목정보 다운로드(해외) > 해외지수선물

---

## 6. 제약사항 및 주의사항

### 6.1 유료 시세 (가장 중요)

> **⚠️ 중요**: 해외선물 API 시세는 **유료**입니다. 유료 가입 없이는 API 호출이 불가능합니다.

#### 유료 시세 미가입 시 오류 메시지

```json
{
    "rt_cd": "1",
    "msg_cd": "EGW00550",
    "msg1": "CME SUB거래소 신청 계좌가 아닙니다."
}
```

#### 유료 시세 가입 방법

1. **한국투자증권 HTS (eFriend Plus)** 또는 **MTS** 접속
2. **해외선물옵션 > 유료시세 신청** 메뉴
3. 원하는 거래소 선택 (CME, SGX 등)
4. **월 이용료** 결제 (거래소별 상이)
5. **익일부터** API 시세 조회 가능

#### 거래소별 유료 시세

| 거래소 | 포함 상품 | 비고 |
|--------|----------|------|
| CME | E-mini S&P500, E-mini 나스닥, 유로FX | CME 그룹 통합 |
| NYMEX | WTI 원유, 천연가스 | CME 그룹 |
| COMEX | 금, 은, 구리 | CME 그룹 |
| CBOT | 옥수수, 대두, 미국채 | CME 그룹 |
| SGX | 니케이225, MSCI 대만 | 별도 가입 |

> **참고**: 포럼 > FAQ > 해외선물옵션 API 유료시세 신청방법

### 6.2 모의투자 미지원

- 대부분의 해외선물 API는 **모의투자 미지원**
- 실전 계좌에서만 테스트 가능

### 6.3 거래 시간

- CME: 한국시간 07:00 ~ 익일 06:00 (서머타임 적용)
- 장 운영시간 API (`해외선물옵션_장운영시간`) 활용 권장

### 6.4 토큰

- 기존 토큰 재사용 (별도 토큰 불필요)
- `custtype`: B(법인) / P(개인)

---

## 7. 파일 구조

### 7.1 신규 파일

```
korea_investment_stock/
├── overseas_future/                      # 신규 모듈
│   ├── __init__.py
│   ├── overseas_future_api.py           # API 호출 함수
│   ├── overseas_future_parser.py        # 마스터 파일 파서
│   └── constants.py                     # TR ID, 거래소 코드 상수
│
├── tests/
│   ├── test_overseas_future.py          # 단위 테스트
│   └── test_overseas_future_integration.py  # 통합 테스트
│
└── examples/
    └── overseas_future_example.py       # 사용 예제
```

### 7.2 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `korea_investment_stock.py` | 해외선물 메서드 추가 또는 위임 |
| `__init__.py` | overseas_future 모듈 export |
| `CLAUDE.md` | 해외선물 API 문서 추가 |
| `CHANGELOG.md` | 버전 업데이트 |

---

## 8. 테스트 계획

### 8.1 단위 테스트

```bash
# 마스터 파일 파서 테스트
pytest korea_investment_stock/tests/test_overseas_future.py -v
```

### 8.2 통합 테스트 (API 키 필요)

```bash
# 실제 API 호출 테스트 (유료 시세 가입 필요)
pytest korea_investment_stock/tests/test_overseas_future_integration.py -v
```

### 8.3 테스트 케이스

| 테스트 | 설명 |
|--------|------|
| `test_fetch_future_price_success` | 정상 시세 조회 |
| `test_fetch_future_price_invalid_symbol` | 잘못된 종목코드 |
| `test_fetch_future_orderbook` | 호가 조회 |
| `test_price_decimal_conversion` | 소수점 변환 |
| `test_master_file_download` | 마스터 파일 다운로드 |

---

## 9. 사용 예시

### 9.1 기본 시세 조회

```python
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)

# E-mini S&P500 선물 현재가
result = broker.fetch_overseas_future_price("ESH25")

if result['rt_cd'] == '0':
    output = result['output1']
    print(f"현재가: {output['last_price']}")
    print(f"전일대비: {output['prev_diff_price']} ({output['prev_diff_rate']}%)")
    print(f"거래량: {output['vol']}")
```

### 9.2 호가 조회

```python
# 금 선물 호가
result = broker.fetch_overseas_future_orderbook("GCG25")

if result['rt_cd'] == '0':
    for quote in result['output2']:
        print(f"매수: {quote['bid_price']} x {quote['bid_qntt']}")
        print(f"매도: {quote['ask_price']} x {quote['ask_qntt']}")
```

### 9.3 상품 정보 조회

```python
# 여러 상품 기본 정보
result = broker.fetch_overseas_future_info(["ESH25", "NQH25", "GCG25"])

if result['rt_cd'] == '0':
    for info in result['output2']:
        print(f"{info['exch_cd']}: 증거금 {info['trst_mgn']}, 만기 {info['expr_date']}")
```

---

## 10. 구현 체크리스트

### Phase 1: MVP (시세 조회)

- [ ] `overseas_future/` 모듈 생성
- [ ] `fetch_overseas_future_price()` 구현
- [ ] `fetch_overseas_future_orderbook()` 구현
- [ ] `fetch_overseas_future_info()` 구현
- [ ] 소수점 변환 유틸리티 구현
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성 (유료 시세 계정 필요)

### Phase 2: 차트 데이터

- [ ] `fetch_overseas_future_minute_chart()` 구현
- [ ] `fetch_overseas_future_daily_chart()` 구현
- [ ] 테스트 추가

### Phase 3: 마스터 파일

- [ ] `fetch_overseas_future_symbols()` 구현
- [ ] ffcode.mst 파서 구현
- [ ] 캐싱 로직 적용

### Phase 4: 문서화

- [ ] `examples/overseas_future_example.py` 작성
- [ ] CLAUDE.md 업데이트
- [ ] CHANGELOG.md 업데이트
- [ ] README 업데이트 (선택)

---

## 11. 위험 요소 및 대응

| 위험 | 영향 | 대응 |
|------|------|------|
| 유료 시세 미가입 | 테스트 불가 | 문서화 우선, 유료 가입 후 테스트 |
| 모의투자 미지원 | 실계좌 필요 | 소액 테스트 또는 조회만 테스트 |
| 소수점 처리 오류 | 가격 표시 오류 | 마스터 파일 기반 변환 로직 필수 |
| 장 운영시간 외 조회 | 빈 데이터 | 에러 처리 및 안내 메시지 |

---

## 12. 일정 (예상)

| Phase | 작업 내용 |
|-------|----------|
| Phase 1 | MVP 시세 조회 API 구현 |
| Phase 2 | 차트/추이 데이터 API |
| Phase 3 | 마스터 파일 다운로드 |
| Phase 4 | 문서화 및 예제 |

---

## 13. 관련 문서

- `docs/api/해외선물옵션/` - 한국투자 API 문서 (35개)
- `docs/start/3_oversea_future_implementation.md` - 구현 상세 (예정)
- `docs/start/3_oversea_future_todo.md` - 구현 체크리스트 (예정)

---

## 14. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2025-12-17 | 초안 작성 |
| 1.1 | 2025-12-21 | 유료 시세 제약사항 상세화, 인기 상품 우선순위 정리 (금, WTI, 천연가스, ES, NQ) |
