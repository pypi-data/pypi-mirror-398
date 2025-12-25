"""
해외 마스터 파일 파서 단위 테스트
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd

from .overseas_master_parser import (
    parse_overseas_stock_master,
    OVERSEAS_MARKETS,
    OVERSEAS_COLUMNS,
)


class TestOverseasMasterConstants:
    """상수 테스트"""

    def test_overseas_markets_contains_all_markets(self):
        """11개 시장 코드 확인"""
        expected = {
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
        assert set(OVERSEAS_MARKETS.keys()) == expected

    def test_overseas_markets_count(self):
        """시장 수 확인"""
        assert len(OVERSEAS_MARKETS) == 11

    def test_overseas_columns_count(self):
        """24개 컬럼 확인"""
        assert len(OVERSEAS_COLUMNS) == 24

    def test_overseas_columns_essential_fields(self):
        """필수 컬럼 존재 확인"""
        essential = ["심볼", "한글명", "영문명", "통화", "거래소코드"]
        for col in essential:
            assert col in OVERSEAS_COLUMNS

    def test_us_markets_exist(self):
        """미국 시장 코드 확인"""
        assert "nas" in OVERSEAS_MARKETS
        assert "nys" in OVERSEAS_MARKETS
        assert "ams" in OVERSEAS_MARKETS

    def test_asia_markets_exist(self):
        """아시아 시장 코드 확인"""
        assert "tse" in OVERSEAS_MARKETS
        assert "hks" in OVERSEAS_MARKETS
        assert "hnx" in OVERSEAS_MARKETS
        assert "hsx" in OVERSEAS_MARKETS


class TestParseOverseasStockMaster:
    """파서 함수 테스트"""

    @patch("pandas.read_table")
    @patch("pathlib.Path.iterdir")
    def test_parse_overseas_stock_master_calls_read_table(
        self, mock_iterdir, mock_read_table
    ):
        """pd.read_table 호출 확인"""
        # Mock file path found via iterdir
        mock_file = MagicMock(spec=Path)
        mock_file.name = "nasmst.cod"
        mock_iterdir.return_value = [mock_file]

        mock_df = pd.DataFrame(
            {"심볼": ["AAPL", "MSFT"], "한글명": ["애플", "마이크로소프트"]}
        )
        mock_read_table.return_value = mock_df

        result = parse_overseas_stock_master("/tmp", "nas")

        mock_read_table.assert_called_once()
        assert len(result) == 2

    @patch("pandas.read_table")
    @patch("pathlib.Path.iterdir")
    def test_parse_overseas_stock_master_correct_file_path(
        self, mock_iterdir, mock_read_table
    ):
        """올바른 파일 경로 생성 확인"""
        # Mock file path found via iterdir
        mock_file = MagicMock(spec=Path)
        mock_file.name = "hksmst.cod"
        mock_iterdir.return_value = [mock_file]

        mock_df = pd.DataFrame()
        mock_read_table.return_value = mock_df

        parse_overseas_stock_master("/data", "hks")

        call_args = mock_read_table.call_args
        # 파일 경로는 iterdir에서 찾은 mock_file이 전달됨
        assert call_args[0][0] == mock_file

    @patch("pandas.read_table")
    @patch("pathlib.Path.iterdir")
    def test_parse_overseas_stock_master_correct_encoding(
        self, mock_iterdir, mock_read_table
    ):
        """CP949 인코딩 사용 확인"""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "nasmst.cod"
        mock_iterdir.return_value = [mock_file]

        mock_df = pd.DataFrame()
        mock_read_table.return_value = mock_df

        parse_overseas_stock_master("/tmp", "nas")

        call_args = mock_read_table.call_args
        assert call_args[1]["encoding"] == "cp949"

    @patch("pandas.read_table")
    @patch("pathlib.Path.iterdir")
    def test_parse_overseas_stock_master_tab_separator(
        self, mock_iterdir, mock_read_table
    ):
        """탭 구분자 사용 확인"""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "nasmst.cod"
        mock_iterdir.return_value = [mock_file]

        mock_df = pd.DataFrame()
        mock_read_table.return_value = mock_df

        parse_overseas_stock_master("/tmp", "nas")

        call_args = mock_read_table.call_args
        assert call_args[1]["sep"] == "\t"

    @patch("pandas.read_table")
    @patch("pathlib.Path.iterdir")
    def test_parse_overseas_stock_master_string_dtype(
        self, mock_iterdir, mock_read_table
    ):
        """문자열 타입 지정 확인"""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "nasmst.cod"
        mock_iterdir.return_value = [mock_file]

        mock_df = pd.DataFrame()
        mock_read_table.return_value = mock_df

        parse_overseas_stock_master("/tmp", "nas")

        call_args = mock_read_table.call_args
        assert call_args[1]["dtype"] == str
