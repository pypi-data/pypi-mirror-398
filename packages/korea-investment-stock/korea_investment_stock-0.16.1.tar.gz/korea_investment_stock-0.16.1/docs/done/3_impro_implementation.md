# korea_investment_stock.py 리팩토링 구현 가이드

> PRD: `3_impro_prd.md` 기반 구현 상세
>
> **상태**: ✅ 모든 Phase 완료 (2025-12-06)

## 1. Phase 1: 즉시 정리 (삭제만)

### 1.1 사용 안 하는 import 제거

**파일**: `korea_investment_stock/korea_investment_stock.py`

```python
# 삭제할 import (라인 7)
import pickle  # 삭제

# 수정할 import (라인 14)
# Before
from typing import Literal, Optional, List

# After
from typing import Literal, Optional
```

### 1.2 DEPRECATED 메서드 제거

**삭제**: `__handle_rate_limit_error` 메서드 (라인 507-524)

```python
# 삭제할 코드
def __handle_rate_limit_error(self, retry_count: int):
    """Rate limit 에러 처리 (Exponential Backoff)

    DEPRECATED: Enhanced Backoff Strategy로 대체됨
    """
    # ... 전체 삭제
```

### 1.3 `__main__` 테스트 코드 제거

**삭제**: 라인 1293-1342 전체

```python
# 삭제할 코드
if __name__ == "__main__":
    with open("../koreainvestment.key", encoding='utf-8') as key_file:
        # ... 전체 삭제
```

### 1.4 죽은 코드 제거

**삭제**: `fetch_symbols` 메서드 (라인 749-766)

```python
# 삭제할 코드 - self.exchange 속성이 존재하지 않음
def fetch_symbols(self):
    if self.exchange == "서울":  # 존재하지 않는 속성
        # ... 전체 삭제
```

### 1.5 디버그 print 문을 logger.debug로 변경

**수정 1**: `fetch_price_detail_oversea` (라인 1014)

```python
# Before
for exchange_code in ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]:
    print("exchange_code", exchange_code)
    params = {...}

# After
for exchange_code in ["NYS", "NAS", "AMS", "BAY", "BAQ", "BAA"]:
    logger.debug(f"exchange_code: {exchange_code}")
    params = {...}
```

**수정 2**: `fetch_stock_info` (라인 1055)

```python
# Before
except Exception as e:
    print(e)
    if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:

# After
except Exception as e:
    logger.debug(f"fetch_stock_info 에러: {e}")
    if resp_json['rt_cd'] != API_RETURN_CODE['SUCCESS']:
```

---

## 2. Phase 2: 상수 분리

### 2.1 constants.py 생성

**파일**: `korea_investment_stock/constants.py`

```python
"""
한국투자증권 API 상수 정의

거래소 코드, 시장 타입, API 리턴 코드 등을 정의합니다.
"""
from typing import Literal

# 해외주식 시세 조회용
EXCHANGE_CODE_QUOTE = {
    "홍콩": "HKS",
    "뉴욕": "NYS",
    "나스닥": "NAS",
    "아멕스": "AMS",
    "도쿄": "TSE",
    "상해": "SHS",
    "심천": "SZS",
    "상해지수": "SHI",
    "심천지수": "SZI",
    "호치민": "HSX",
    "하노이": "HNX"
}

# 해외주식 주문/잔고용
EXCHANGE_CODE_ORDER = {
    "미국전체": "NASD",
    "나스닥": "NAS",
    "뉴욕": "NYSE",
    "아멕스": "AMEX",
    "홍콩": "SEHK",
    "상해": "SHAA",
    "심천": "SZAA",
    "도쿄": "TKSE",
    "하노이": "HASE",
    "호치민": "VNSE"
}

# 잔고 조회용
EXCHANGE_CODE_BALANCE = {
    "나스닥": "NASD",
    "뉴욕": "NYSE",
    "아멕스": "AMEX",
    "홍콩": "SEHK",
    "상해": "SHAA",
    "심천": "SZAA",
    "도쿄": "TKSE",
    "하노이": "HASE",
    "호치민": "VNSE"
}

# 상세 조회용
EXCHANGE_CODE_DETAIL = {
    "나스닥": "NAS",
    "뉴욕": "NYS",
    "아멕스": "AMS",
    "홍콩": "HKS",
    "상해": "SHS",
    "심천": "SZS",
    "도쿄": "TSE",
    "하노이": "HNX",
    "호치민": "HSX",
    "상해지수": "SHI",
    "심천지수": "SZI"
}

# 통화 코드
CURRENCY_CODE = {
    "나스닥": "USD",
    "뉴욕": "USD",
    "아멕스": "USD",
    "홍콩": "HKD",
    "상해": "CNY",
    "심천": "CNY",
    "도쿄": "JPY",
    "하노이": "VND",
    "호치민": "VND"
}

# 시장 타입 매핑
MARKET_TYPE_MAP = {
    "KR": ["300"],
    "KRX": ["300"],
    "NASDAQ": ["512"],
    "NYSE": ["513"],
    "AMEX": ["529"],
    "US": ["512", "513", "529"],
    "TYO": ["515"],
    "JP": ["515"],
    "HKEX": ["501"],
    "HK": ["501", "543", "558"],
    "HNX": ["507"],
    "HSX": ["508"],
    "VN": ["507", "508"],
    "SSE": ["551"],
    "SZSE": ["552"],
    "CN": ["551", "552"]
}

# 타입 정의
MARKET_TYPE = Literal[
    "KRX", "NASDAQ", "NYSE", "AMEX",
    "TYO", "HKEX", "HNX", "HSX", "SSE", "SZSE",
]

EXCHANGE_TYPE = Literal["NAS", "NYS", "AMS"]

# 시장 코드 → 시장 타입 매핑
MARKET_CODE_MAP: dict[str, MARKET_TYPE] = {
    "300": "KRX", "301": "KRX", "302": "KRX",
    "512": "NASDAQ", "513": "NYSE", "529": "AMEX",
    "515": "TYO",
    "501": "HKEX", "543": "HKEX", "558": "HKEX",
    "507": "HNX", "508": "HSX",
    "551": "SSE", "552": "SZSE",
}

# 거래소 코드 매핑
EXCHANGE_CODE_MAP: dict[str, EXCHANGE_TYPE] = {
    "NASDAQ": "NAS",
    "NYSE": "NYS",
    "AMEX": "AMS"
}

# API 리턴 코드
API_RETURN_CODE = {
    "SUCCESS": "0",
    "EXPIRED_TOKEN": "1",
    "NO_DATA": "7",
    "RATE_LIMIT_EXCEEDED": "EGW00201",
}

# 하위 호환성을 위한 alias (deprecated)
EXCHANGE_CODE = EXCHANGE_CODE_QUOTE
EXCHANGE_CODE2 = EXCHANGE_CODE_ORDER
EXCHANGE_CODE3 = EXCHANGE_CODE_BALANCE
EXCHANGE_CODE4 = EXCHANGE_CODE_DETAIL
```

### 2.2 메인 파일 수정

**파일**: `korea_investment_stock/korea_investment_stock.py`

```python
# Before (라인 27-160)
EXCHANGE_CODE = {...}
EXCHANGE_CODE2 = {...}
# ... 모든 상수 정의

# After
from .constants import (
    EXCHANGE_CODE_QUOTE,
    EXCHANGE_CODE_ORDER,
    MARKET_TYPE_MAP,
    MARKET_CODE_MAP,
    EXCHANGE_CODE_MAP,
    API_RETURN_CODE,
    MARKET_TYPE,
    EXCHANGE_TYPE,
    # 하위 호환성
    EXCHANGE_CODE,
    EXCHANGE_CODE2,
    EXCHANGE_CODE3,
    EXCHANGE_CODE4,
    CURRENCY_CODE,
)
```

---

## 3. Phase 3: 설정 로직 분리

### 3.1 ConfigResolver 클래스 생성

**파일**: `korea_investment_stock/config_resolver.py`

```python
"""설정 해결 로직"""
import os
from pathlib import Path
from typing import Optional


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
        result = {
            "api_key": None,
            "api_secret": None,
            "acc_no": None,
            "token_storage_type": None,
            "redis_url": None,
            "redis_password": None,
            "token_file": None,
        }

        # 5단계: 기본 config 파일
        default_config = self._load_default_config_file()
        if default_config:
            self._merge_config(result, default_config)

        # 4단계: 환경 변수
        env_config = self._load_from_env()
        self._merge_config(result, env_config)

        # 3단계: config_file 파라미터
        if config_file:
            file_config = self._load_config_file(config_file)
            if file_config:
                self._merge_config(result, file_config)

        # 2단계: config 객체
        if config:
            config_dict = {
                "api_key": config.api_key,
                "api_secret": config.api_secret,
                "acc_no": config.acc_no,
                "token_storage_type": config.token_storage_type,
                "redis_url": config.redis_url,
                "redis_password": config.redis_password,
                "token_file": str(config.token_file) if config.token_file else None,
            }
            self._merge_config(result, config_dict)

        # 1단계: 생성자 파라미터
        constructor_params = {
            "api_key": api_key,
            "api_secret": api_secret,
            "acc_no": acc_no,
        }
        self._merge_config(result, constructor_params)

        return result

    def _merge_config(self, target: dict, source: dict) -> None:
        """source의 non-None 값으로 target 업데이트"""
        for key, value in source.items():
            if value is not None and key in target:
                target[key] = value

    def _load_default_config_file(self) -> dict | None:
        """기본 경로에서 config 파일 로드"""
        for path in self.DEFAULT_CONFIG_PATHS:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return self._load_config_file(expanded_path)
        return None

    def _load_config_file(self, path: "str | Path") -> dict | None:
        """YAML 설정 파일 로드"""
        try:
            import yaml
        except ImportError:
            return None

        path = Path(path).expanduser()
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            return {
                "api_key": data.get("api_key"),
                "api_secret": data.get("api_secret"),
                "acc_no": data.get("acc_no"),
                "token_storage_type": data.get("token_storage_type"),
                "redis_url": data.get("redis_url"),
                "redis_password": data.get("redis_password"),
                "token_file": data.get("token_file"),
            }
        except Exception:
            return None

    def _load_from_env(self) -> dict:
        """환경 변수에서 설정 로드"""
        return {
            "api_key": os.getenv("KOREA_INVESTMENT_API_KEY"),
            "api_secret": os.getenv("KOREA_INVESTMENT_API_SECRET"),
            "acc_no": os.getenv("KOREA_INVESTMENT_ACCOUNT_NO"),
            "token_storage_type": os.getenv("KOREA_INVESTMENT_TOKEN_STORAGE"),
            "redis_url": os.getenv("KOREA_INVESTMENT_REDIS_URL"),
            "redis_password": os.getenv("KOREA_INVESTMENT_REDIS_PASSWORD"),
            "token_file": os.getenv("KOREA_INVESTMENT_TOKEN_FILE"),
        }
```

### 3.2 메인 파일에서 ConfigResolver 사용

```python
# korea_investment_stock.py

from .config_resolver import ConfigResolver

class KoreaInvestment:
    def __init__(self, ...):
        # 설정 해결
        resolver = ConfigResolver()
        resolved = resolver.resolve(
            api_key=api_key,
            api_secret=api_secret,
            acc_no=acc_no,
            config=config,
            config_file=config_file,
        )
        # ... 나머지 로직
```

---

## 4. Phase 4: 파서 분리

### 4.1 MasterParser 클래스 생성

**파일**: `korea_investment_stock/parsers/__init__.py`

```python
from .master_parser import MasterParser

__all__ = ["MasterParser"]
```

**파일**: `korea_investment_stock/parsers/master_parser.py`

```python
"""KOSPI/KOSDAQ 마스터 파일 파싱"""
import os
import pandas as pd
from pathlib import Path


class MasterParser:
    """마스터 파일 파서 (중복 제거된 통합 구현)"""

    # KOSPI 설정
    KOSPI_OFFSET = 228
    KOSPI_FIELD_SPECS = [
        2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 9, 5, 5, 1, 1, 1, 2, 1, 1,
        1, 2, 2, 2, 3, 1, 3, 12, 12, 8,
        15, 21, 2, 7, 1, 1, 1, 1, 1, 9,
        9, 9, 5, 9, 8, 9, 3, 1, 1, 1
    ]
    KOSPI_COLUMNS = [
        '그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류',
        '제조업', '저유동성', '지배구조지수종목', 'KOSPI200섹터업종', 'KOSPI100',
        'KOSPI50', 'KRX', 'ETP', 'ELW발행', 'KRX100',
        'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC',
        'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설',
        'Non1', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송',
        'SRI', '기준가', '매매수량단위', '시간외수량단위', '거래정지',
        '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',
        '우회상장', '락구분', '액면변경', '증자구분', '증거금비율',
        '신용가능', '신용기간', '전일거래량', '액면가', '상장일자',
        '상장주수', '자본금', '결산월', '공모가', '우선주',
        '공매도과열', '이상급등', 'KRX300', 'KOSPI', '매출액',
        '영업이익', '경상이익', '당기순이익', 'ROE', '기준년월',
        '시가총액', '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능'
    ]

    # KOSDAQ 설정
    KOSDAQ_OFFSET = 222
    KOSDAQ_FIELD_SPECS = [
        2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 9, 5, 5, 1,
        1, 1, 2, 1, 1, 1, 2, 2, 2, 3,
        1, 3, 12, 12, 8, 15, 21, 2, 7, 1,
        1, 1, 1, 9, 9, 9, 5, 9, 8, 9,
        3, 1, 1, 1
    ]
    KOSDAQ_COLUMNS = [
        '그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류',
        '벤처기업', '저유동성', 'KRX', 'ETP', 'KRX100',
        'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC',
        'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설',
        '투자주의', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송',
        'KOSDAQ150', '기준가', '매매수량단위', '시간외수량단위', '거래정지',
        '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',
        '우회상장', '락구분', '액면변경', '증자구분', '증거금비율',
        '신용가능', '신용기간', '전일거래량', '액면가', '상장일자',
        '상장주수', '자본금', '결산월', '공모가', '우선주',
        '공매도과열', '이상급등', 'KRX300', '매출액', '영업이익',
        '경상이익', '당기순이익', 'ROE', '기준년월', '시가총액',
        '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능'
    ]

    def parse_kospi(self, base_dir: str) -> pd.DataFrame:
        """KOSPI 마스터 파일 파싱"""
        return self._parse_master(
            base_dir=base_dir,
            prefix="kospi",
            offset=self.KOSPI_OFFSET,
            field_specs=self.KOSPI_FIELD_SPECS,
            columns=self.KOSPI_COLUMNS
        )

    def parse_kosdaq(self, base_dir: str) -> pd.DataFrame:
        """KOSDAQ 마스터 파일 파싱"""
        return self._parse_master(
            base_dir=base_dir,
            prefix="kosdaq",
            offset=self.KOSDAQ_OFFSET,
            field_specs=self.KOSDAQ_FIELD_SPECS,
            columns=self.KOSDAQ_COLUMNS
        )

    def _parse_master(
        self,
        base_dir: str,
        prefix: str,
        offset: int,
        field_specs: list,
        columns: list
    ) -> pd.DataFrame:
        """공통 마스터 파일 파싱 로직"""
        file_name = f"{base_dir}/{prefix}_code.mst"
        tmp_fil1 = f"{base_dir}/{prefix}_code_part1.tmp"
        tmp_fil2 = f"{base_dir}/{prefix}_code_part2.tmp"

        wf1 = open(tmp_fil1, mode="w", encoding="cp949")
        wf2 = open(tmp_fil2, mode="w")

        with open(file_name, mode="r", encoding="cp949") as f:
            for row in f:
                rf1 = row[0:len(row) - offset]
                rf1_1 = rf1[0:9].rstrip()
                rf1_2 = rf1[9:21].rstrip()
                rf1_3 = rf1[21:].strip()
                wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')
                rf2 = row[-offset:]
                wf2.write(rf2)

        wf1.close()
        wf2.close()

        part1_columns = ['단축코드', '표준코드', '한글명']
        df1 = pd.read_csv(tmp_fil1, header=None, encoding='cp949', names=part1_columns)
        df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=columns)
        df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)

        # 임시 파일 정리
        del df1
        del df2
        os.remove(tmp_fil1)
        os.remove(tmp_fil2)

        return df
```

### 4.2 메인 파일에서 MasterParser 사용

```python
# korea_investment_stock.py

from .parsers import MasterParser

class KoreaInvestment:
    def __init__(self, ...):
        self._master_parser = MasterParser()
        # ...

    def fetch_kospi_symbols(self, ttl_hours=168, force_download=False):
        base_dir = os.getcwd()
        # ... 다운로드 로직 ...
        return self._master_parser.parse_kospi(base_dir)

    def fetch_kosdaq_symbols(self, ttl_hours=168, force_download=False):
        base_dir = os.getcwd()
        # ... 다운로드 로직 ...
        return self._master_parser.parse_kosdaq(base_dir)
```

---

## 5. Phase 5: IPO 헬퍼 분리

### 5.1 ipo_helpers 모듈 생성

**파일**: `korea_investment_stock/ipo/__init__.py`

```python
from .ipo_helpers import (
    parse_ipo_date_range,
    format_ipo_date,
    calculate_ipo_d_day,
    get_ipo_status,
    format_number,
)

__all__ = [
    "parse_ipo_date_range",
    "format_ipo_date",
    "calculate_ipo_d_day",
    "get_ipo_status",
    "format_number",
]
```

**파일**: `korea_investment_stock/ipo/ipo_helpers.py`

```python
"""IPO 관련 헬퍼 함수"""
import re
from datetime import datetime


def parse_ipo_date_range(date_range_str: str) -> tuple:
    """청약기간 문자열 파싱

    Args:
        date_range_str: "2024.01.15~2024.01.16" 형식

    Returns:
        tuple: (시작일 datetime, 종료일 datetime) 또는 (None, None)
    """
    if not date_range_str:
        return (None, None)

    pattern = r'(\d{4}\.\d{2}\.\d{2})~(\d{4}\.\d{2}\.\d{2})'
    match = re.match(pattern, date_range_str)

    if match:
        try:
            start_str = match.group(1).replace('.', '')
            end_str = match.group(2).replace('.', '')
            start_date = datetime.strptime(start_str, "%Y%m%d")
            end_date = datetime.strptime(end_str, "%Y%m%d")
            return (start_date, end_date)
        except ValueError:
            pass

    return (None, None)


def format_ipo_date(date_str: str) -> str:
    """날짜 형식 변환 (YYYYMMDD -> YYYY-MM-DD)"""
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    elif '.' in date_str:
        return date_str.replace('.', '-')
    return date_str


def calculate_ipo_d_day(ipo_date_str: str) -> int:
    """청약일까지 남은 일수 계산"""
    if '~' in ipo_date_str:
        start_date, _ = parse_ipo_date_range(ipo_date_str)
        if start_date:
            today = datetime.now()
            return (start_date - today).days
    return -999


def get_ipo_status(subscr_dt: str) -> str:
    """청약 상태 판단

    Returns:
        str: "예정", "진행중", "마감", "알수없음"
    """
    start_date, end_date = parse_ipo_date_range(subscr_dt)
    if not start_date or not end_date:
        return "알수없음"

    today = datetime.now()
    if today < start_date:
        return "예정"
    elif start_date <= today <= end_date:
        return "진행중"
    else:
        return "마감"


def format_number(num_str: str) -> str:
    """숫자 문자열에 천단위 콤마 추가"""
    try:
        return f"{int(num_str):,}"
    except (ValueError, TypeError):
        return num_str
```

### 5.2 메인 파일에서 IPO 헬퍼 위임

```python
# korea_investment_stock.py

from .ipo import ipo_helpers

class KoreaInvestment:
    # 하위 호환성을 위해 정적 메서드로 위임
    @staticmethod
    def parse_ipo_date_range(date_range_str: str) -> tuple:
        return ipo_helpers.parse_ipo_date_range(date_range_str)

    @staticmethod
    def format_ipo_date(date_str: str) -> str:
        return ipo_helpers.format_ipo_date(date_str)

    @staticmethod
    def calculate_ipo_d_day(ipo_date_str: str) -> int:
        return ipo_helpers.calculate_ipo_d_day(ipo_date_str)

    @staticmethod
    def get_ipo_status(subscr_dt: str) -> str:
        return ipo_helpers.get_ipo_status(subscr_dt)

    @staticmethod
    def format_number(num_str: str) -> str:
        return ipo_helpers.format_number(num_str)
```

---

## 6. __init__.py 업데이트 ✅ 완료

**파일**: `korea_investment_stock/__init__.py` (121줄)

```python
"""한국투자증권 OpenAPI Python Wrapper"""

# 메인 클래스
from .korea_investment_stock import KoreaInvestment

# 상수 정의 (API 파라미터명 사용)
from .constants import (
    COUNTRY_CODE,
    FID_COND_MRKT_DIV_CODE_STOCK,
    EXCG_ID_DVSN_CD,
    EXCD,
    EXCD_BY_COUNTRY,
    OVRS_EXCG_CD,
    PRDT_TYPE_CD,
    PRDT_TYPE_CD_BY_COUNTRY,
    API_RETURN_CODE,
)

# 설정 관리
from .config import Config
from .config_resolver import ConfigResolver

# 캐시 기능
from .cache import CacheManager, CacheEntry, CachedKoreaInvestment

# 토큰 관리
from .token import TokenStorage, FileTokenStorage, RedisTokenStorage, TokenManager, create_token_storage

# Rate Limiting
from .rate_limit import RateLimiter, RateLimitedKoreaInvestment

# 파서
from .parsers import parse_kospi_master, parse_kosdaq_master

# IPO 헬퍼
from .ipo import (
    validate_date_format,
    validate_date_range,
    parse_ipo_date_range,
    format_ipo_date,
    calculate_ipo_d_day,
    get_ipo_status,
    format_number,
)
```

---

## 7. 검증 명령어

```bash
# 1. 기존 테스트 실행
pytest

# 2. 통합 테스트
pytest korea_investment_stock/tests/test_integration_us_stocks.py -v

# 3. import 테스트
python -c "from korea_investment_stock import KoreaInvestment; print('OK')"

# 4. 상수 import 테스트
python -c "from korea_investment_stock.constants import MARKET_TYPE_MAP; print('OK')"

# 5. 예제 실행
python examples/basic_example.py
```

---

## 8. 추가 리팩토링: Token 모듈 (Phase 7) ✅ 완료

PR #98에서 token 모듈 구조가 추가로 개선되었습니다.

### 8.1 token_storage/ → token/ 폴더 변경

```
# Before
token_storage/
├── __init__.py
└── token_storage.py       # 모든 기능이 한 파일에

# After
token/
├── __init__.py            # exports (20줄)
├── storage.py             # TokenStorage 클래스들 (396줄)
├── manager.py             # TokenManager (185줄)
└── factory.py             # create_token_storage (96줄)
```

### 8.2 TokenManager 클래스 분리

```python
# token/manager.py
class TokenManager:
    """토큰 발급, 검증, 갱신을 담당"""

    def __init__(self, storage, base_url, api_key, api_secret):
        self.storage = storage
        # ...

    def get_valid_token(self) -> str:
        """유효한 토큰 반환 (만료 시 자동 갱신)"""

    def is_token_valid(self) -> bool:
        """토큰 유효성 확인"""

    def issue_hashkey(self, data: dict) -> str:
        """해쉬키 발급"""
```

### 8.3 TokenStorage Factory 분리

```python
# token/factory.py
def create_token_storage(config: dict) -> TokenStorage:
    """설정에 따라 적절한 TokenStorage 생성"""
    storage_type = config.get("token_storage_type", "file")

    if storage_type == "redis":
        return RedisTokenStorage(...)
    else:
        return FileTokenStorage(...)
```

---

## 9. 추가 리팩토링: IPO 모듈 (Phase 8) ✅ 완료

PR #96에서 IPO API가 분리되었습니다.

### 9.1 ipo_api.py 추가

```python
# ipo/ipo_api.py (109줄)
def fetch_ipo_schedule(
    base_url: str,
    access_token: str,
    api_key: str,
    api_secret: str,
    from_date: str = None,
    to_date: str = None,
    symbol: str = ""
) -> dict:
    """공모주 청약 일정 조회 API"""
    # API 호출 로직
```

### 9.2 KoreaInvestment에서 위임

```python
# korea_investment_stock.py
from .ipo import fetch_ipo_schedule as _fetch_ipo_schedule

class KoreaInvestment:
    def fetch_ipo_schedule(self, from_date=None, to_date=None, symbol=""):
        return _fetch_ipo_schedule(
            self.base_url, self.access_token,
            self.api_key, self.api_secret,
            from_date, to_date, symbol
        )
```

---

**문서 버전**: 2.0
**작성일**: 2025-12-04
**수정일**: 2025-12-06
