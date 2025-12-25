# 해외 주식 마스터 파일 다운로드 기능 PRD

## 개요

국내 KOSPI/KOSDAQ 종목 코드 다운로드 기능(`fetch_kospi_symbols()`, `fetch_kosdaq_symbols()`)과 동일한 패턴으로 **해외 주식** 종목 코드를 다운로드하는 기능을 추가합니다.

## 배경

### 현재 상태

- 국내: `fetch_kospi_symbols()`, `fetch_kosdaq_symbols()` 메서드로 종목 코드 다운로드 지원
- 해외: **미지원** (해외 주식 가격 조회는 가능하지만, 종목 리스트 조회 불가)

### 필요성

- 해외 주식 종목 리스트 조회 기능 필요
- 전체 해외 종목 배치 처리 시 필수
- 국내와 동일한 사용자 경험 제공

## 목표

1. **해외 주식 마스터**: 11개 거래소 종목 코드 다운로드
2. 기존 국내 마스터 파일과 동일한 캐싱 로직 적용

## 참고 자료

- **공식 샘플 코드 (해외 주식)**: https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/overseas_stock_code.py
- **API 포털**: https://apiportal.koreainvestment.com/apiservice-category

---

## 해외 주식 마스터 파일

### 지원 거래소 (11개 시장)

| 시장 코드 | 거래소명 | 국가 |
|-----------|----------|------|
| `nas` | 나스닥 (NASDAQ) | 미국 |
| `nys` | 뉴욕증권거래소 (NYSE) | 미국 |
| `ams` | 아멕스 (AMEX) | 미국 |
| `shs` | 상해 | 중국 |
| `shi` | 상해지수 | 중국 |
| `szs` | 심천 | 중국 |
| `szi` | 심천지수 | 중국 |
| `tse` | 도쿄 | 일본 |
| `hks` | 홍콩 | 홍콩 |
| `hnx` | 하노이 | 베트남 |
| `hsx` | 호치민 | 베트남 |

### 다운로드 URL 패턴

```
https://new.real.download.dws.co.kr/common/master/{market_code}mst.cod.zip
```

예시:
- 나스닥: `https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip`
- 뉴욕: `https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip`
- 홍콩: `https://new.real.download.dws.co.kr/common/master/hksmst.cod.zip`

### 파일 형식

- **인코딩**: CP949
- **구분자**: 탭 (Tab)
- **파일명**: `{market_code}mst.cod` (압축 해제 후)

### 데이터 필드 (24개 컬럼)

| 컬럼명 | 설명 |
|--------|------|
| 국가코드 | 국가 구분 코드 |
| 거래소ID | 거래소 식별자 |
| 심볼 | 종목 심볼 (티커) |
| 한글명 | 종목 한글명 |
| 영문명 | 종목 영문명 |
| 보안유형 | 보안 유형 코드 |
| 통화 | 거래 통화 |
| 기초가격 | 기초 가격 |
| 매수호가수량 | 매수 호가 수량 |
| 매도호가수량 | 매도 호가 수량 |
| 시장개장시간 | 시장 개장 시간 |
| 시장폐장시간 | 시장 폐장 시간 |
| 업종코드 | 업종 분류 코드 |
| 지수구성여부 | 지수 구성 종목 여부 |
| 틱사이즈유형 | 틱 사이즈 유형 코드 |
| ETP구분코드 | ETF/ETN 등 ETP 구분 |
| ... | (기타 필드) |

---

## API 설계

### 1. 해외 주식 종목 다운로드

```python
def fetch_overseas_symbols(
    self,
    market: str,
    ttl_hours: int = 168,
    force_download: bool = False
) -> pd.DataFrame:
    """해외 주식 종목 코드 조회

    Args:
        market: 시장 코드 (nas, nys, ams, shs, shi, szs, szi, tse, hks, hnx, hsx)
        ttl_hours: 캐시 유효 시간 (기본 1주일)
        force_download: 강제 다운로드 여부

    Returns:
        DataFrame: 해외 종목 정보

    Example:
        >>> df = broker.fetch_overseas_symbols("nas")  # 나스닥
        >>> df = broker.fetch_overseas_symbols("hks")  # 홍콩
    """
```

### 2. 편의 메서드 (미국 주식 전용)

> **TODO**: 전체 해외 시장 다운로드 기능 사용하기 시작하면 아래 편의 메서드들은 삭제 검토.
> `fetch_overseas_symbols(market)`만으로 충분하며, 11개 시장 중 미국 3개만 편의 메서드를 제공하는 것은 불균형할 수 있음.

```python
def fetch_nasdaq_symbols(
    self,
    ttl_hours: int = 168,
    force_download: bool = False
) -> pd.DataFrame:
    """나스닥 종목 코드"""
    return self.fetch_overseas_symbols("nas", ttl_hours, force_download)

def fetch_nyse_symbols(
    self,
    ttl_hours: int = 168,
    force_download: bool = False
) -> pd.DataFrame:
    """뉴욕증권거래소 종목 코드"""
    return self.fetch_overseas_symbols("nys", ttl_hours, force_download)

def fetch_amex_symbols(
    self,
    ttl_hours: int = 168,
    force_download: bool = False
) -> pd.DataFrame:
    """아멕스 종목 코드"""
    return self.fetch_overseas_symbols("ams", ttl_hours, force_download)
```

---

## 구현 계획

### Phase 1: 파서 모듈 추가

- [ ] `parsers/overseas_master_parser.py` 생성
- [ ] `parse_overseas_stock_master()` 함수 구현
- [ ] 단위 테스트 작성

### Phase 2: KoreaInvestment 클래스 메서드 추가

- [ ] `fetch_overseas_symbols()` 메서드 추가
- [ ] `fetch_nasdaq_symbols()` 편의 메서드 추가
- [ ] `fetch_nyse_symbols()` 편의 메서드 추가
- [ ] `fetch_amex_symbols()` 편의 메서드 추가

### Phase 3: 캐싱 및 Wrapper 지원

- [ ] 기존 `download_master_file()` 재활용
- [ ] `CachedKoreaInvestment`, `RateLimitedKoreaInvestment` 호환 확인

### Phase 4: 테스트 및 문서화

- [ ] 통합 테스트 작성
- [ ] 예제 파일 작성 (`examples/overseas_symbols_example.py`)
- [ ] CLAUDE.md 업데이트
- [ ] CHANGELOG.md 업데이트

---

## 기술적 고려사항

### 1. 파일 파싱

국내 마스터 파일과 달리 해외 마스터 파일은:
- **탭 구분자** 사용 → `pd.read_table()` 사용
- **CP949 인코딩** → 동일

### 2. 에러 처리

- 잘못된 시장 코드 입력 시 명확한 에러 메시지
- 네트워크 오류 시 재시도 로직 (사용자 구현 권장)

### 3. 캐싱

기존 `download_master_file()` 메서드 재활용:
- TTL 기반 캐싱 (기본 1주일)
- `force_download` 옵션

### 4. 시장 코드 상수

```python
class OverseasMarket:
    """해외 시장 코드 상수"""
    # 미국
    NASDAQ = "nas"
    NYSE = "nys"
    AMEX = "ams"

    # 중국
    SHANGHAI = "shs"
    SHANGHAI_INDEX = "shi"
    SHENZHEN = "szs"
    SHENZHEN_INDEX = "szi"

    # 기타
    TOKYO = "tse"
    HONGKONG = "hks"
    HANOI = "hnx"
    HOCHIMINH = "hsx"

    ALL = [NASDAQ, NYSE, AMEX, SHANGHAI, SHANGHAI_INDEX,
           SHENZHEN, SHENZHEN_INDEX, TOKYO, HONGKONG, HANOI, HOCHIMINH]
```

---

## 사용 예시

### 기본 사용

```python
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)

# 나스닥 종목 조회
nasdaq_df = broker.fetch_nasdaq_symbols()
print(f"나스닥 종목 수: {len(nasdaq_df)}")

# 홍콩 종목 조회
hk_df = broker.fetch_overseas_symbols("hks")
print(f"홍콩 종목 수: {len(hk_df)}")
```

### 전체 미국 주식 조회

```python
# 미국 3개 거래소 통합 조회
import pandas as pd

nasdaq = broker.fetch_nasdaq_symbols()
nyse = broker.fetch_nyse_symbols()
amex = broker.fetch_amex_symbols()

us_stocks = pd.concat([nasdaq, nyse, amex], ignore_index=True)
print(f"미국 전체 종목 수: {len(us_stocks)}")
```

---

## 비기능적 요구사항

### 성능

- 첫 다운로드: 2-5초 (네트워크 상태에 따라)
- 캐시 사용 시: <0.1초

### 호환성

- Python 3.11+
- pandas 의존성 (기존과 동일)
- 기존 Wrapper 클래스 (`CachedKoreaInvestment`, `RateLimitedKoreaInvestment`) 호환

### 테스트

- 단위 테스트: 파서 함수
- 통합 테스트: 실제 다운로드 (API 키 불필요)

---

## 일정 (예상)

| 단계 | 작업 |
|------|------|
| Phase 1 | 파서 모듈 구현 |
| Phase 2 | KoreaInvestment 메서드 추가 |
| Phase 3 | Wrapper 호환성 확인 |
| Phase 4 | 테스트 및 문서화 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2025-12-06 | 초안 작성 |
| 1.1 | 2025-12-06 | 해외 지수 마스터 제외 (별도 작업으로 분리) |
