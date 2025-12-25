# IPO 모듈 리팩토링 구현 가이드

## 1. 개요

`korea_investment_stock.py`의 `fetch_ipo_schedule()` 메서드를 `ipo/` 폴더로 분리하여 모듈화한다.

**접근 방식**: 단순 함수 추출 + 위임 패턴

---

## 2. 파일 구조

### 변경 전
```
ipo/
├── __init__.py           # 헬퍼 함수 export
└── ipo_helpers.py        # 유틸리티 함수 7개
```

### 변경 후
```
ipo/
├── __init__.py           # 전체 export (수정)
├── ipo_helpers.py        # 유틸리티 함수 (기존 유지)
└── ipo_api.py            # API 호출 함수 (신규)
```

---

## 3. 구현 상세

### 3.1 신규 파일: `ipo/ipo_api.py`

```python
"""
IPO API 모듈

공모주 청약 일정 조회 API를 제공합니다.
"""
import logging
from datetime import datetime, timedelta

import requests

from .ipo_helpers import validate_date_format, validate_date_range

logger = logging.getLogger(__name__)


def fetch_ipo_schedule(
    base_url: str,
    access_token: str,
    api_key: str,
    api_secret: str,
    from_date: str = None,
    to_date: str = None,
    symbol: str = ""
) -> dict:
    """공모주 청약 일정 조회

    Args:
        base_url: API base URL
        access_token: Bearer 토큰
        api_key: API key
        api_secret: API secret
        from_date: 조회 시작일 (YYYYMMDD, 기본값: 오늘)
        to_date: 조회 종료일 (YYYYMMDD, 기본값: 30일 후)
        symbol: 종목코드 (선택, 공백시 전체 조회)

    Returns:
        dict: 공모주 청약 일정 정보

    Raises:
        ValueError: 날짜 형식 오류시
    """
    # 날짜 기본값 설정
    if not from_date:
        from_date = datetime.now().strftime("%Y%m%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")

    # 날짜 유효성 검증
    if not validate_date_format(from_date) or not validate_date_format(to_date):
        raise ValueError("날짜 형식은 YYYYMMDD 이어야 합니다.")

    if not validate_date_range(from_date, to_date):
        raise ValueError("시작일은 종료일보다 이전이어야 합니다.")

    path = "uapi/domestic-stock/v1/ksdinfo/pub-offer"
    url = f"{base_url}/{path}"
    headers = {
        "content-type": "application/json",
        "authorization": access_token,
        "appKey": api_key,
        "appSecret": api_secret,
        "tr_id": "HHKDB669108C0",
        "custtype": "P"
    }

    params = {
        "SHT_CD": symbol,
        "CTS": "",
        "F_DT": from_date,
        "T_DT": to_date
    }

    resp = requests.get(url, headers=headers, params=params)
    resp_json = resp.json()

    if resp_json.get('rt_cd') != '0':
        logger.error(f"공모주 조회 실패: {resp_json.get('msg1', 'Unknown error')}")

    return resp_json
```

### 3.2 수정 파일: `ipo/__init__.py`

```python
"""
IPO 모듈

공모주 관련 API 및 유틸리티 함수를 제공합니다.
"""
from .ipo_helpers import (
    validate_date_format,
    validate_date_range,
    parse_ipo_date_range,
    format_ipo_date,
    calculate_ipo_d_day,
    get_ipo_status,
    format_number,
)
from .ipo_api import fetch_ipo_schedule

__all__ = [
    # API
    "fetch_ipo_schedule",
    # Helpers
    "validate_date_format",
    "validate_date_range",
    "parse_ipo_date_range",
    "format_ipo_date",
    "calculate_ipo_d_day",
    "get_ipo_status",
    "format_number",
]
```

### 3.3 수정 파일: `korea_investment_stock.py`

**Import 변경** (26-34줄):
```python
# 변경 전
from .ipo import (
    validate_date_format,
    validate_date_range,
    parse_ipo_date_range,
    format_ipo_date,
    calculate_ipo_d_day,
    get_ipo_status,
    format_number,
)

# 변경 후
from .ipo import fetch_ipo_schedule as _fetch_ipo_schedule
```

**메서드 변경** (752-848줄 → 약 15줄):
```python
def fetch_ipo_schedule(
    self,
    from_date: str = None,
    to_date: str = None,
    symbol: str = ""
) -> dict:
    """공모주 청약 일정 조회

    예탁원정보(공모주청약일정) API를 통해 공모주 정보를 조회합니다.

    Args:
        from_date: 조회 시작일 (YYYYMMDD, 기본값: 오늘)
        to_date: 조회 종료일 (YYYYMMDD, 기본값: 30일 후)
        symbol: 종목코드 (선택, 공백시 전체 조회)

    Returns:
        dict: 공모주 청약 일정 정보
    """
    return _fetch_ipo_schedule(
        self.base_url,
        self.access_token,
        self.api_key,
        self.api_secret,
        from_date,
        to_date,
        symbol
    )
```

---

## 4. 영향받는 파일

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `ipo/ipo_api.py` | 신규 | API 호출 로직 (~80줄) |
| `ipo/__init__.py` | 수정 | fetch_ipo_schedule export 추가 |
| `korea_investment_stock.py` | 수정 | import 변경 + 위임 호출 (~79줄 삭제) |

**변경 불필요**:
- `cache/cached_korea_investment.py` - broker 위임 유지
- `korea_investment_stock/__init__.py` - IPO 헬퍼 export 유지

---

## 5. 테스트

```bash
# 단위 테스트
pytest -m "not integration"

# IPO 통합 테스트 (API 자격 증명 필요)
pytest korea_investment_stock/tests/test_ipo_integration.py -v
```
