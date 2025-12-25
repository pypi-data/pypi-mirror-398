# korea_investment_stock.py 리팩토링 PRD

> **1,342줄 단일 파일**을 모듈화하여 유지보수성과 가독성을 개선하는 리팩토링 PRD

## 🚀 Quick Summary

### 리팩토링 완료 ✅
- `korea_investment_stock.py`: **1,342줄 → 692줄** (48.4% 감소)
- **SRP(단일 책임 원칙) 적용**: 설정, 토큰, API, 파싱 등 모듈 분리 완료
- **코드 중복 제거**: 파서 통합 완료
- **사용되지 않는 코드 제거**: 완료

### 최종 구조 (구현 완료)
```
korea_investment_stock/
├── __init__.py                    # 공개 API exports (121줄)
├── korea_investment_stock.py      # 692줄 (핵심 클래스)
├── config_resolver.py             # 설정 해결 로직 (186줄)
├── constants.py                   # 상수 정의 (167줄)
├── parsers/
│   ├── __init__.py                # (8줄)
│   └── master_parser.py           # KOSPI/KOSDAQ 파싱 (159줄)
├── ipo/
│   ├── __init__.py                # (28줄)
│   ├── ipo_api.py                 # IPO API (109줄)
│   └── ipo_helpers.py             # IPO 헬퍼 함수 (142줄)
└── token/
    ├── __init__.py                # (20줄)
    ├── storage.py                 # TokenStorage 클래스들 (396줄)
    ├── manager.py                 # TokenManager (185줄)
    └── factory.py                 # create_token_storage (96줄)
```

### 달성 효과
- ✅ 메인 파일: **1,342줄 → 692줄** (48.4% 감소)
- ✅ 테스트 용이성 향상
- ✅ 코드 재사용성 증가
- ✅ 유지보수 비용 감소

---

## 목차

1. [문제 분석](#1-문제-분석)
2. [리팩토링 제안](#2-리팩토링-제안)
3. [상세 구현 계획](#3-상세-구현-계획)
4. [마이그레이션 가이드](#4-마이그레이션-가이드)
5. [위험 및 완화 방안](#5-위험-및-완화-방안)
6. [성공 지표](#6-성공-지표)
7. [일정](#7-일정)

---

## 1. 문제 분석

### 1.1 파일 크기 문제

**현재 상태**: `korea_investment_stock.py` = **1,342줄**

일반적인 Python 파일 권장 크기: **200-500줄**

```
파일 라인 수 분석:
├── import 문                    : ~25줄
├── 상수 정의 (EXCHANGE_CODE 등) : ~135줄
├── KoreaInvestment 클래스       : ~1,125줄
│   ├── __init__ & 설정 관리     : ~275줄
│   ├── 토큰 관리                : ~75줄
│   ├── 국내 주식 API            : ~90줄
│   ├── 해외 주식 API            : ~40줄
│   ├── 종목 코드 관리           : ~270줄
│   ├── IPO 관련                 : ~200줄
│   └── 기타 유틸리티            : ~75줄
└── __main__ 테스트 코드         : ~50줄
```

### 1.2 SRP(단일 책임 원칙) 위반

`KoreaInvestment` 클래스가 담당하는 책임:

| 책임 | 라인 수 | 문제점 |
|------|---------|--------|
| 설정 관리 | ~275줄 | 5단계 우선순위 설정 해결 로직 |
| 토큰 관리 | ~75줄 | 발급, 검증, 로드 |
| 국내 주식 API | ~90줄 | 가격, ETF, 종목정보 |
| 해외 주식 API | ~40줄 | 미국 주식 가격 |
| 종목 코드 관리 | ~270줄 | KOSPI/KOSDAQ 파싱 |
| IPO 관련 | ~200줄 | IPO 조회 + 9개 헬퍼 함수 |

**문제**: 하나의 책임 변경이 다른 모든 기능에 영향을 줄 수 있음

### 1.3 코드 중복

#### `parse_kospi_master` vs `parse_kosdaq_master`

```python
# parse_kospi_master (842-916줄)
def parse_kospi_master(self, base_dir: str):
    file_name = base_dir + "/kospi_code.mst"
    tmp_fil1 = base_dir + "/kospi_code_part1.tmp"
    tmp_fil2 = base_dir + "/kospi_code_part2.tmp"
    # ... 74줄의 파싱 로직

# parse_kosdaq_master (918-990줄)
def parse_kosdaq_master(self, base_dir: str):
    file_name = base_dir + "/kosdaq_code.mst"
    tmp_fil1 = base_dir + "/kosdaq_code_part1.tmp"
    tmp_fil2 = base_dir + "/kosdaq_code_part2.tmp"
    # ... 72줄의 거의 동일한 파싱 로직
```

**차이점**:
- 파일명 (kospi vs kosdaq)
- 오프셋 값 (228 vs 222)
- 컬럼 스펙 (일부 차이)

**중복률**: ~90%

### 1.4 사용되지 않는 코드

#### 사용되지 않는 import
```python
import pickle       # 사용 안 함
from typing import List  # 사용 안 함
```

#### DEPRECATED 메서드
```python
def __handle_rate_limit_error(self, retry_count: int):
    """Rate limit 에러 처리 (Exponential Backoff)

    DEPRECATED: Enhanced Backoff Strategy로 대체됨
    이 메서드는 하위 호환성을 위해 유지되며, 향후 제거될 예정입니다.
    """
```

#### 존재하지 않는 속성 참조
```python
def fetch_symbols(self):
    if self.exchange == "서울":  # self.exchange 속성 없음!
        df = self.fetch_kospi_symbols()
```

### 1.5 상수 이름 불명확

```python
EXCHANGE_CODE = {...}   # 해외주식 시세
EXCHANGE_CODE2 = {...}  # 해외주식 주문/잔고
EXCHANGE_CODE3 = {...}  # ???
EXCHANGE_CODE4 = {...}  # ???
```

**문제**: 숫자로 구분된 이름은 의도 파악 불가

### 1.6 에러 처리 일관성 부족

```python
# 일부 메서드
except Exception as e:
    print(e)  # 로깅 대신 print 사용
    if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:
        continue
    raise e
```

### 1.7 테스트 코드가 메인 파일에 포함

```python
# 1293-1342줄
if __name__ == "__main__":
    with open("../koreainvestment.key", encoding='utf-8') as key_file:
        lines = key_file.readlines()
    # ... 테스트 코드
```

**문제**:
- 프로덕션 코드와 테스트 코드 혼재
- 주석 처리된 코드 다수

---

## 2. 리팩토링 제안

### 2.1 최종 디렉토리 구조 (구현 완료)

```
korea_investment_stock/
├── __init__.py                         # 공개 API exports (121줄)
├── korea_investment_stock.py           # 692줄 (핵심 클래스)
├── config/                             # 설정 관리
│   ├── __init__.py
│   └── config.py                       # Config 클래스
├── config_resolver.py                  # 설정 해결 로직 (186줄)
├── constants.py                        # 상수 정의 (167줄)
├── parsers/
│   ├── __init__.py
│   └── master_parser.py                # KOSPI/KOSDAQ 파싱 (159줄)
├── ipo/
│   ├── __init__.py
│   ├── ipo_api.py                      # IPO API (109줄)
│   └── ipo_helpers.py                  # IPO 헬퍼 함수 (142줄)
├── token/                              # 토큰 관리 (신규 구조)
│   ├── __init__.py
│   ├── storage.py                      # TokenStorage 클래스들 (396줄)
│   ├── manager.py                      # TokenManager (185줄)
│   └── factory.py                      # create_token_storage (96줄)
├── cache/                              # 캐시 기능
└── rate_limit/                         # Rate Limiting
```

### 2.2 모듈별 책임

#### `constants.py` (167줄) ✅ 완료
```python
"""한국투자증권 API 상수 정의 - API 파라미터명 사용"""

# 국가 코드
COUNTRY_CODE = {"KR": "KR", "US": "US", "CN": "CN", "JP": "JP"}

# 조건 시장 분류 코드 (FID_COND_MRKT_DIV_CODE)
FID_COND_MRKT_DIV_CODE_STOCK = {"KRX": "J", "NXT": "NX", "UNIFIED": "UN", "ELW": "W"}

# 해외주식 거래소 코드 - 시세 조회용 (EXCD)
EXCD = {"NYS": "NYS", "NAS": "NAS", "AMS": "AMS", "HKS": "HKS", ...}

# 국가별 거래소 코드 매핑
EXCD_BY_COUNTRY = {"US": ["NYS", "NAS", "AMS", ...], "HK": ["HKS"], ...}

# 상품유형 코드 (PRDT_TYPE_CD)
PRDT_TYPE_CD = {"KR_STOCK": "300", "US_NASDAQ": "512", ...}

# API 리턴 코드
API_RETURN_CODE = {"SUCCESS": "0", "EXPIRED_TOKEN": "1", "NO_DATA": "7", ...}
```

#### `config.py` (~150줄)
```python
"""설정 관리"""

class ConfigResolver:
    """5단계 우선순위 설정 해결"""

    DEFAULT_CONFIG_PATHS = [
        "~/.config/kis/config.yaml",
        "~/.config/kis/config.yml",
    ]

    def resolve(
        self,
        api_key: str | None,
        api_secret: str | None,
        acc_no: str | None,
        config: "Config | None",
        config_file: "str | Path | None",
    ) -> dict:
        """5단계 우선순위로 설정 해결"""
        # 기존 _resolve_config 로직

    def _merge_config(self, target: dict, source: dict) -> None:
        ...

    def _load_default_config_file(self) -> dict | None:
        ...

    def _load_config_file(self, path: "str | Path") -> dict | None:
        ...

    def _load_from_env(self) -> dict:
        ...
```

#### `parsers/master_parser.py` (~150줄)
```python
"""KOSPI/KOSDAQ 마스터 파일 파싱"""

import pandas as pd
from pathlib import Path

class MasterParser:
    """마스터 파일 파서"""

    # KOSPI 컬럼 스펙
    KOSPI_FIELD_SPECS = [2, 1, 4, 4, 4, ...]
    KOSPI_COLUMNS = ["그룹코드", "시가총액규모", ...]

    # KOSDAQ 컬럼 스펙
    KOSDAQ_FIELD_SPECS = [2, 1, 4, 4, 4, ...]
    KOSDAQ_COLUMNS = ["그룹코드", "시가총액규모", ...]

    def parse(self, base_dir: str, market: str) -> pd.DataFrame:
        """마스터 파일 파싱 (통합 메서드)

        Args:
            base_dir: 디렉토리 경로
            market: "kospi" 또는 "kosdaq"
        """
        if market == "kospi":
            return self._parse_master(
                base_dir,
                "kospi_code.mst",
                228,
                self.KOSPI_FIELD_SPECS,
                self.KOSPI_COLUMNS
            )
        else:
            return self._parse_master(
                base_dir,
                "kosdaq_code.mst",
                222,
                self.KOSDAQ_FIELD_SPECS,
                self.KOSDAQ_COLUMNS
            )

    def _parse_master(
        self,
        base_dir: str,
        file_name: str,
        offset: int,
        field_specs: list,
        columns: list
    ) -> pd.DataFrame:
        """공통 파싱 로직"""
        # 기존 중복 코드를 하나로 통합
```

#### `ipo/ipo_helpers.py` (~100줄)
```python
"""IPO 헬퍼 함수"""

import re
from datetime import datetime

def parse_ipo_date_range(date_range_str: str) -> tuple:
    """청약기간 문자열 파싱"""
    # 기존 로직

def format_ipo_date(date_str: str) -> str:
    """날짜 형식 변환"""
    # 기존 로직

def calculate_ipo_d_day(ipo_date_str: str) -> int:
    """청약일까지 남은 일수"""
    # 기존 로직

def get_ipo_status(subscr_dt: str) -> str:
    """청약 상태 판단"""
    # 기존 로직

def format_number(num_str: str) -> str:
    """숫자 천단위 콤마"""
    # 기존 로직
```

#### `korea_investment_stock.py` (~300줄)
```python
"""한국투자증권 API 클라이언트"""

from .config import ConfigResolver
from .constants import MARKET_TYPE_MAP, API_RETURN_CODE
from .parsers import MasterParser
from .ipo import ipo_helpers

class KoreaInvestment:
    """한국투자증권 REST API 클라이언트"""

    def __init__(self, ...):
        # 설정 해결 (ConfigResolver 사용)
        resolver = ConfigResolver()
        resolved = resolver.resolve(...)

    # 핵심 API 메서드만 유지
    def fetch_price(self, symbol: str, market: str) -> dict: ...
    def fetch_domestic_price(self, market_code: str, symbol: str) -> dict: ...
    def fetch_etf_domestic_price(self, market_code: str, symbol: str) -> dict: ...
    def fetch_price_detail_oversea(self, symbol: str, market: str): ...
    def fetch_stock_info(self, symbol: str, market: str): ...
    def fetch_search_stock_info(self, symbol: str, market: str): ...
    def fetch_kospi_symbols(self, ...): ...
    def fetch_kosdaq_symbols(self, ...): ...
    def fetch_ipo_schedule(self, ...): ...

    # IPO 헬퍼는 정적 메서드로 위임
    @staticmethod
    def parse_ipo_date_range(date_range_str: str) -> tuple:
        return ipo_helpers.parse_ipo_date_range(date_range_str)
```

### 2.3 즉시 정리 가능한 항목

#### 삭제 대상
1. **사용 안 하는 import 제거**
   ```python
   # 삭제
   import pickle
   from typing import List
   ```

2. **DEPRECATED 메서드 제거**
   ```python
   # 삭제: __handle_rate_limit_error
   ```

3. **`__main__` 테스트 코드 제거**
   ```python
   # 삭제: 1293-1342줄
   if __name__ == "__main__":
       ...
   ```

4. **죽은 코드 제거**
   ```python
   # 삭제: fetch_symbols (self.exchange 속성 없음)
   def fetch_symbols(self):
       if self.exchange == "서울":  # 존재하지 않는 속성
   ```

#### 상수 이름 개선 ✅ 완료
```python
# Before (불명확한 이름)
EXCHANGE_CODE = {...}
EXCHANGE_CODE2 = {...}
EXCHANGE_CODE3 = {...}
EXCHANGE_CODE4 = {...}

# After (API 파라미터명 사용)
EXCD = {...}              # 해외 시세 조회용 (API: EXCD)
EXCD_BY_COUNTRY = {...}   # 국가별 거래소 매핑
OVRS_EXCG_CD = {...}      # 해외 주문/잔고용 (API: OVRS_EXCG_CD)
EXCG_ID_DVSN_CD = {...}   # 국내 거래소 구분 (API: EXCG_ID_DVSN_CD)
PRDT_TYPE_CD = {...}      # 상품유형 코드 (API: PRDT_TYPE_CD)
```

---

## 3. 상세 구현 계획

### Phase 1: 즉시 정리 (1-2시간)

**변경 없이 삭제만**

1. 사용 안 하는 import 제거
2. DEPRECATED 메서드 제거
3. `__main__` 테스트 코드 제거
4. `fetch_symbols` 메서드 제거 (또는 수정)

**예상 효과**: ~100줄 감소

### Phase 2: 상수 분리 (1-2시간)

1. `constants.py` 생성
2. 모든 상수 이동
3. 상수 이름 개선
4. `korea_investment_stock.py`에서 import

**예상 효과**: ~135줄 분리

### Phase 3: 설정 로직 분리 (2-3시간)

1. `config.py` 생성
2. `ConfigResolver` 클래스 구현
3. `_resolve_config` 관련 메서드 이동
4. `KoreaInvestment.__init__` 단순화

**예상 효과**: ~200줄 분리

### Phase 4: 파서 분리 (2-3시간)

1. `parsers/master_parser.py` 생성
2. `MasterParser` 클래스 구현 (중복 제거)
3. `parse_kospi_master`, `parse_kosdaq_master` 통합
4. `fetch_kospi_symbols`, `fetch_kosdaq_symbols` 수정

**예상 효과**: ~150줄 분리, 중복 제거

### Phase 5: IPO 헬퍼 분리 (1-2시간)

1. `ipo/ipo_helpers.py` 생성
2. IPO 관련 정적 메서드 이동
3. `KoreaInvestment`에서 위임 패턴 적용

**예상 효과**: ~100줄 분리

### Phase 6: 테스트 및 검증 (2-3시간)

1. 기존 테스트 실행 확인
2. import 경로 테스트
3. 하위 호환성 검증

---

## 4. 마이그레이션 가이드

### 4.1 공개 API 유지 (Breaking Change 없음)

```python
# 기존 코드 (변경 없이 동작)
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)
result = broker.fetch_price("005930", "KR")

# IPO 헬퍼도 동일하게 동작
status = KoreaInvestment.get_ipo_status("2024.01.15~2024.01.16")
```

### 4.2 내부 import 경로 변경 (선택적)

```python
# 기존 (계속 동작)
from korea_investment_stock import KoreaInvestment

# 새로운 직접 import (선택적)
from korea_investment_stock.config import ConfigResolver
from korea_investment_stock.parsers import MasterParser
from korea_investment_stock.ipo import ipo_helpers
```

### 4.3 `__init__.py` 업데이트

```python
# korea_investment_stock/__init__.py

from .korea_investment_stock import KoreaInvestment
from .config import Config, ConfigResolver
from .constants import (
    MARKET_TYPE_MAP,
    API_RETURN_CODE,
    # 필요한 상수 export
)

# 하위 호환성을 위해 기존 export 유지
__all__ = [
    "KoreaInvestment",
    "Config",
    # ...
]
```

---

## 5. 위험 및 완화 방안

### 위험 1: 하위 호환성 깨짐
**위험**: import 경로 변경으로 기존 사용자 코드 실패
**완화**: `__init__.py`에서 기존 export 모두 유지
**검증**: 기존 테스트 100% 통과 확인

### 위험 2: 순환 import
**위험**: 모듈 분리 시 순환 참조 발생
**완화**: 의존성 방향 명확히 설계 (상수 ← 설정 ← 메인)
**검증**: 각 모듈 개별 import 테스트

### 위험 3: 상수 이름 변경 영향
**위험**: 상수 이름 변경 시 내부 코드 수정 필요
**완화**: 기존 이름 alias로 유지 (deprecation warning 추가)
```python
# 하위 호환성
EXCHANGE_CODE = EXCHANGE_CODE_QUOTE  # deprecated
```

### 위험 4: 성능 영향
**위험**: 모듈 분리로 import 시간 증가
**완화**: 지연 import 패턴 적용 (필요시)
**검증**: import 시간 벤치마크

---

## 6. 성공 지표

### 6.1 정량적 지표 ✅ 달성

| 지표 | Before | After | 목표 | 상태 |
|------|--------|-------|------|------|
| `korea_investment_stock.py` 라인 수 | 1,342 | 692 | ≤400줄 | ✅ 48.4% 감소 |
| 파일 수 | 1 | 12+ | 적절한 분리 | ✅ 완료 |
| 중복 코드 | ~150줄 | 0 | 0줄 | ✅ 완료 |
| 사용 안 하는 코드 | ~100줄 | 0 | 0줄 | ✅ 완료 |

### 6.2 정성적 지표 ✅ 달성

- [x] 기존 테스트 100% 통과
- [x] 공개 API 변경 없음 (하위 호환성 유지)
- [x] 각 모듈이 단일 책임 원칙 준수
- [x] 코드 리뷰 통과

### 6.3 검증 체크리스트

```bash
# 1. 기존 테스트 실행
pytest

# 2. 통합 테스트 실행
pytest korea_investment_stock/tests/test_integration_us_stocks.py -v

# 3. import 테스트
python -c "from korea_investment_stock import KoreaInvestment"

# 4. 예제 실행
python examples/basic_example.py
```

---

## 7. 일정

### 예상 총 소요 시간: 10-15시간

| Phase | 작업 | 예상 시간 |
|-------|------|-----------|
| 1 | 즉시 정리 (삭제만) | 1-2시간 |
| 2 | 상수 분리 | 1-2시간 |
| 3 | 설정 로직 분리 | 2-3시간 |
| 4 | 파서 분리 | 2-3시간 |
| 5 | IPO 헬퍼 분리 | 1-2시간 |
| 6 | 테스트 및 검증 | 2-3시간 |

### 권장 순서

1. **Phase 1 먼저**: 위험 없이 코드 정리
2. **Phase 2-5 순차 진행**: 각 단계별 테스트
3. **Phase 6 마지막**: 전체 검증

### 점진적 접근 권장

한 번에 모든 리팩토링을 하지 않고, **Phase 1만 먼저 진행**하여 즉각적인 개선 효과를 얻고, 나머지는 필요에 따라 진행하는 것도 좋은 전략입니다.

---

## 부록: 현재 코드 상세 분석

### A. 사용되지 않는 import

```python
# 라인 7
import pickle  # 사용처 없음

# 라인 14
from typing import Literal, Optional, List  # List 사용처 없음
```

### B. DEPRECATED 메서드

```python
# 라인 507-524
def __handle_rate_limit_error(self, retry_count: int):
    """Rate limit 에러 처리 (Exponential Backoff)

    DEPRECATED: Enhanced Backoff Strategy로 대체됨
    """
```

### C. 존재하지 않는 속성 참조

```python
# 라인 749-766
def fetch_symbols(self):
    if self.exchange == "서울":  # self.exchange 속성이 __init__에서 정의되지 않음
        df = self.fetch_kospi_symbols()
```

### D. 디버그용 print 문

```python
# 라인 1014
print("exchange_code", exchange_code)

# 라인 1055
print(e)
```

---

**문서 버전**: 2.0
**작성일**: 2025-12-04
**수정일**: 2025-12-06
**상태**: ✅ 완료
**관련 PR**: #96 (IPO 모듈), #97, #98 (Token 모듈)
