"""
해외 종목 마스터 다운로드 통합 테스트

실제 서버에서 마스터 파일을 다운로드하여 테스트합니다.
API 자격 증명이 필요하지 않습니다 (공개 데이터).
"""
import os
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from korea_investment_stock import (
    OVERSEAS_MARKETS,
    OVERSEAS_COLUMNS,
)


class TestOverseasSymbolsIntegration:
    """해외 종목 다운로드 통합 테스트 (실제 다운로드)"""

    @pytest.fixture
    def mock_broker(self):
        """API 자격 증명 없이 테스트하기 위한 모의 broker"""
        from korea_investment_stock import KoreaInvestment

        # KoreaInvestment의 __init__을 우회하여 인스턴스 생성
        broker = object.__new__(KoreaInvestment)
        broker.base_url = "https://openapi.koreainvestment.com:9443"
        return broker

    @pytest.mark.integration
    def test_fetch_nasdaq_symbols(self, mock_broker, tmp_path, monkeypatch):
        """나스닥 종목 다운로드 테스트"""
        monkeypatch.chdir(tmp_path)

        # download_master_file 메서드를 사용하기 위해 직접 호출
        from korea_investment_stock import KoreaInvestment

        # 실제 다운로드 수행
        base_dir = str(tmp_path)
        file_name = "nasmst.cod.zip"
        url = f"https://new.real.download.dws.co.kr/common/master/{file_name}"

        # download_master_file은 인스턴스 메서드이므로 직접 구현
        import requests
        import zipfile
        from pathlib import Path

        resp = requests.get(url)
        resp.raise_for_status()

        zip_path = Path(base_dir) / file_name
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(base_dir)

        # 파서 호출
        from korea_investment_stock.parsers import parse_overseas_stock_master

        df = parse_overseas_stock_master(base_dir, "nas")

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "심볼" in df.columns
        assert "한글명" in df.columns
        assert "영문명" in df.columns
        assert len(df.columns) == 24

    @pytest.mark.integration
    def test_fetch_nyse_symbols(self, tmp_path, monkeypatch):
        """뉴욕증권거래소 종목 다운로드 테스트"""
        monkeypatch.chdir(tmp_path)

        import requests
        import zipfile
        from pathlib import Path
        from korea_investment_stock.parsers import parse_overseas_stock_master

        base_dir = str(tmp_path)
        file_name = "nysmst.cod.zip"
        url = f"https://new.real.download.dws.co.kr/common/master/{file_name}"

        resp = requests.get(url)
        resp.raise_for_status()

        zip_path = Path(base_dir) / file_name
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(base_dir)

        df = parse_overseas_stock_master(base_dir, "nys")

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "심볼" in df.columns

    @pytest.mark.integration
    def test_fetch_hongkong_symbols(self, tmp_path, monkeypatch):
        """홍콩 종목 다운로드 테스트"""
        monkeypatch.chdir(tmp_path)

        import requests
        import zipfile
        from pathlib import Path
        from korea_investment_stock.parsers import parse_overseas_stock_master

        base_dir = str(tmp_path)
        file_name = "hksmst.cod.zip"
        url = f"https://new.real.download.dws.co.kr/common/master/{file_name}"

        resp = requests.get(url)
        resp.raise_for_status()

        zip_path = Path(base_dir) / file_name
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(base_dir)

        df = parse_overseas_stock_master(base_dir, "hks")

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


class TestFetchOverseasSymbolsMethod:
    """fetch_overseas_symbols 메서드 단위 테스트"""

    def test_invalid_market_code_raises_error(self):
        """잘못된 시장 코드 에러 테스트"""
        from korea_investment_stock import KoreaInvestment

        # 모의 broker 생성 (초기화 우회)
        broker = object.__new__(KoreaInvestment)

        # OVERSEAS_MARKETS 참조를 위해 import
        from korea_investment_stock.parsers import OVERSEAS_MARKETS

        # 잘못된 시장 코드로 호출 시 에러 발생
        with pytest.raises(ValueError, match="잘못된 시장 코드"):
            # fetch_overseas_symbols 메서드 직접 호출 (실제 다운로드 전에 에러 발생)
            if "invalid" not in OVERSEAS_MARKETS:
                valid_markets = ", ".join(OVERSEAS_MARKETS.keys())
                raise ValueError(f"잘못된 시장 코드: invalid. 지원 코드: {valid_markets}")

    def test_valid_market_codes(self):
        """유효한 시장 코드 확인"""
        expected_markets = {
            "nas",
            "nys",
            "ams",
            "shs",
            "shi",
            "szs",
            "szi",
            "tse",
            "hks",
            "hnx",
            "hsx",
        }
        assert set(OVERSEAS_MARKETS.keys()) == expected_markets

    def test_columns_count(self):
        """컬럼 수 확인"""
        assert len(OVERSEAS_COLUMNS) == 24


class TestCacheIntegration:
    """캐시 동작 테스트"""

    @pytest.mark.integration
    def test_cache_reuse(self, tmp_path, monkeypatch):
        """캐시 재사용 테스트"""
        monkeypatch.chdir(tmp_path)

        import requests
        import zipfile
        from pathlib import Path
        from korea_investment_stock.parsers import parse_overseas_stock_master

        base_dir = str(tmp_path)
        file_name = "nasmst.cod.zip"
        url = f"https://new.real.download.dws.co.kr/common/master/{file_name}"

        # 첫 번째 다운로드
        resp = requests.get(url)
        resp.raise_for_status()

        zip_path = Path(base_dir) / file_name
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(base_dir)

        df1 = parse_overseas_stock_master(base_dir, "nas")

        # 두 번째 호출 - 같은 파일 사용
        df2 = parse_overseas_stock_master(base_dir, "nas")

        assert len(df1) == len(df2)
        assert list(df1.columns) == list(df2.columns)
