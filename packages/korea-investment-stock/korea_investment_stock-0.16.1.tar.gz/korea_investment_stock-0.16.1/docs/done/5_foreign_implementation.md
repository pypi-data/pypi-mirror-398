# 해외 주식 마스터 파일 다운로드 구현 가이드

## 구현 개요

국내 `fetch_kospi_symbols()`, `fetch_kosdaq_symbols()` 패턴을 따라 해외 11개 거래소 종목 코드 다운로드 기능 구현.

---

## 1. 파서 모듈 구현

### 파일 위치

`korea_investment_stock/parsers/overseas_master_parser.py`

### 핵심 구현

```python
"""해외 주식 마스터 파일 파서"""
import pandas as pd

# 지원 시장 코드
OVERSEAS_MARKETS = {
    "nas": "나스닥",
    "nys": "뉴욕",
    "ams": "아멕스",
    "shs": "상해",
    "shi": "상해지수",
    "szs": "심천",
    "szi": "심천지수",
    "tse": "도쿄",
    "hks": "홍콩",
    "hnx": "하노이",
    "hsx": "호치민",
}

# 컬럼명 정의 (24개)
OVERSEAS_COLUMNS = [
    "국가코드", "거래소ID", "거래소코드", "거래소명",
    "심볼", "실시간심볼", "한글명", "영문명",
    "보안유형", "통화", "소수점", "상장주수",
    "매수호가수량", "매도호가수량", "시장개장시간", "시장폐장시간",
    "업종코드", "업종대", "업종중", "업종소",
    "지수구성여부", "거래정지", "틱사이즈유형", "ETP구분코드",
]


def parse_overseas_stock_master(base_dir: str, market_code: str) -> pd.DataFrame:
    """해외 주식 마스터 파일 파싱

    Args:
        base_dir: 마스터 파일이 있는 디렉토리
        market_code: 시장 코드 (nas, nys, ams, ...)

    Returns:
        pd.DataFrame: 종목 정보
    """
    file_path = f"{base_dir}/{market_code}mst.cod"

    df = pd.read_table(
        file_path,
        sep="\t",
        encoding="cp949",
        header=None,
        names=OVERSEAS_COLUMNS,
        dtype=str,  # 모든 컬럼을 문자열로 읽기
    )

    return df
```

### `__init__.py` 업데이트

```python
# korea_investment_stock/parsers/__init__.py
from .master_parser import parse_kospi_master, parse_kosdaq_master
from .overseas_master_parser import parse_overseas_stock_master, OVERSEAS_MARKETS

__all__ = [
    "parse_kospi_master",
    "parse_kosdaq_master",
    "parse_overseas_stock_master",
    "OVERSEAS_MARKETS",
]
```

---

## 2. KoreaInvestment 클래스 메서드 추가

### 파일 위치

`korea_investment_stock/korea_investment_stock.py`

### 핵심 구현

```python
from .parsers import parse_overseas_stock_master, OVERSEAS_MARKETS


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

    Raises:
        ValueError: 잘못된 시장 코드
    """
    if market not in OVERSEAS_MARKETS:
        valid_markets = ", ".join(OVERSEAS_MARKETS.keys())
        raise ValueError(f"잘못된 시장 코드: {market}. 지원 코드: {valid_markets}")

    base_dir = os.getcwd()
    file_name = f"{market}mst.cod.zip"
    url = f"https://new.real.download.dws.co.kr/common/master/{file_name}"

    self.download_master_file(base_dir, file_name, url, ttl_hours, force_download)
    df = parse_overseas_stock_master(base_dir, market)
    return df


# TODO: 전체 해외 시장 다운로드 기능 사용하기 시작하면 아래 편의 메서드들은 삭제 검토
#       fetch_overseas_symbols(market)만으로 충분하며, 11개 시장 중 미국 3개만
#       편의 메서드를 제공하는 것은 불균형할 수 있음

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

## 3. 단위 테스트

### 파일 위치

`korea_investment_stock/parsers/test_overseas_master_parser.py`

### 핵심 테스트

```python
import pytest
from unittest.mock import patch, mock_open
import pandas as pd
from .overseas_master_parser import (
    parse_overseas_stock_master,
    OVERSEAS_MARKETS,
    OVERSEAS_COLUMNS,
)


class TestOverseasMasterParser:
    """해외 마스터 파일 파서 테스트"""

    def test_overseas_markets_contains_all_markets(self):
        """11개 시장 코드 확인"""
        expected = {"nas", "nys", "ams", "shs", "shi", "szs", "szi", "tse", "hks", "hnx", "hsx"}
        assert set(OVERSEAS_MARKETS.keys()) == expected

    def test_overseas_columns_count(self):
        """24개 컬럼 확인"""
        assert len(OVERSEAS_COLUMNS) == 24

    @patch("pandas.read_table")
    def test_parse_overseas_stock_master(self, mock_read_table):
        """파서 함수 호출 테스트"""
        mock_df = pd.DataFrame({"심볼": ["AAPL", "MSFT"]})
        mock_read_table.return_value = mock_df

        result = parse_overseas_stock_master("/tmp", "nas")

        mock_read_table.assert_called_once()
        assert len(result) == 2


class TestFetchOverseasSymbols:
    """fetch_overseas_symbols 메서드 테스트"""

    def test_invalid_market_code_raises_error(self, broker):
        """잘못된 시장 코드 에러"""
        with pytest.raises(ValueError, match="잘못된 시장 코드"):
            broker.fetch_overseas_symbols("invalid")
```

---

## 4. 통합 테스트

### 파일 위치

`korea_investment_stock/tests/test_overseas_symbols_integration.py`

### 핵심 테스트

```python
import pytest
import pandas as pd


@pytest.mark.integration
class TestOverseasSymbolsIntegration:
    """해외 종목 다운로드 통합 테스트 (실제 다운로드)"""

    def test_fetch_nasdaq_symbols(self, broker):
        """나스닥 종목 다운로드"""
        df = broker.fetch_nasdaq_symbols()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "심볼" in df.columns
        assert "한글명" in df.columns

    def test_fetch_nyse_symbols(self, broker):
        """뉴욕 종목 다운로드"""
        df = broker.fetch_nyse_symbols()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_fetch_overseas_symbols_with_cache(self, broker, tmp_path, monkeypatch):
        """캐시 동작 테스트"""
        monkeypatch.chdir(tmp_path)

        # 첫 번째 호출 - 다운로드
        df1 = broker.fetch_overseas_symbols("nas")

        # 두 번째 호출 - 캐시 사용
        df2 = broker.fetch_overseas_symbols("nas")

        assert len(df1) == len(df2)
```

---

## 5. __init__.py Export 추가

### 파일 위치

`korea_investment_stock/__init__.py`

### 추가 내용

```python
from .parsers import OVERSEAS_MARKETS

__all__ = [
    # ... 기존 export
    "OVERSEAS_MARKETS",
]
```

---

## 파일 구조

```
korea_investment_stock/
├── __init__.py                              # OVERSEAS_MARKETS export 추가
├── korea_investment_stock.py                # 메서드 4개 추가
├── parsers/
│   ├── __init__.py                          # export 추가
│   ├── master_parser.py                     # 기존 (변경 없음)
│   ├── overseas_master_parser.py            # 신규
│   └── test_overseas_master_parser.py       # 신규
└── tests/
    └── test_overseas_symbols_integration.py # 신규
```

---

## 주요 변경 파일

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `parsers/overseas_master_parser.py` | 신규 | 해외 마스터 파서 |
| `parsers/__init__.py` | 수정 | export 추가 |
| `korea_investment_stock.py` | 수정 | 메서드 4개 추가 |
| `__init__.py` | 수정 | OVERSEAS_MARKETS export |
| `parsers/test_overseas_master_parser.py` | 신규 | 단위 테스트 |
| `tests/test_overseas_symbols_integration.py` | 신규 | 통합 테스트 |
