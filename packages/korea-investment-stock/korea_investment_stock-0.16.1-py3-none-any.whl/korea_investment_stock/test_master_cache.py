"""Master 파일 캐싱 테스트"""
import os
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from korea_investment_stock import KoreaInvestment


class TestShouldDownload:
    """_should_download() 메서드 테스트"""

    @pytest.fixture
    def broker(self):
        """테스트용 broker fixture"""
        # Mock broker without actual API credentials
        broker = Mock(spec=KoreaInvestment)
        broker._should_download = KoreaInvestment._should_download.__get__(broker)
        return broker

    def test_file_not_exists(self, broker, tmp_path):
        """파일 없을 때 다운로드 필요"""
        file_path = tmp_path / "nonexistent.zip"
        assert broker._should_download(file_path, 168, False) is True

    def test_file_fresh(self, broker, tmp_path):
        """파일이 신선할 때 다운로드 불필요"""
        file_path = tmp_path / "fresh.zip"
        file_path.touch()
        assert broker._should_download(file_path, 168, False) is False

    def test_file_stale(self, broker, tmp_path):
        """파일이 오래됐을 때 다운로드 필요 (1주일 초과)"""
        file_path = tmp_path / "stale.zip"
        file_path.touch()
        old_time = time.time() - (169 * 3600)  # 1주일 + 1시간
        os.utime(file_path, (old_time, old_time))
        assert broker._should_download(file_path, 168, False) is True

    def test_force_download(self, broker, tmp_path):
        """강제 다운로드 시 항상 True"""
        file_path = tmp_path / "forced.zip"
        file_path.touch()
        assert broker._should_download(file_path, 168, True) is True

    def test_custom_ttl(self, broker, tmp_path):
        """커스텀 TTL 테스트"""
        file_path = tmp_path / "custom.zip"
        file_path.touch()
        old_time = time.time() - (2 * 3600)  # 2시간 전
        os.utime(file_path, (old_time, old_time))

        # 1시간 TTL → 다운로드 필요
        assert broker._should_download(file_path, 1, False) is True
        # 24시간 TTL → 캐시 사용
        assert broker._should_download(file_path, 24, False) is False


class TestMasterFileCache:
    """Master 파일 캐싱 통합 테스트"""

    def test_default_ttl_constant(self):
        """기본 TTL 상수 확인"""
        assert KoreaInvestment.DEFAULT_MASTER_TTL_HOURS == 168

    def test_fetch_kospi_symbols_signature(self):
        """fetch_kospi_symbols 메서드 시그니처 확인"""
        import inspect
        sig = inspect.signature(KoreaInvestment.fetch_kospi_symbols)
        params = sig.parameters

        # 파라미터 존재 확인
        assert 'ttl_hours' in params
        assert 'force_download' in params

        # 기본값 확인
        assert params['ttl_hours'].default == 168
        assert params['force_download'].default is False

    def test_fetch_kosdaq_symbols_signature(self):
        """fetch_kosdaq_symbols 메서드 시그니처 확인"""
        import inspect
        sig = inspect.signature(KoreaInvestment.fetch_kosdaq_symbols)
        params = sig.parameters

        # 파라미터 존재 확인
        assert 'ttl_hours' in params
        assert 'force_download' in params

        # 기본값 확인
        assert params['ttl_hours'].default == 168
        assert params['force_download'].default is False

    def test_download_master_file_signature(self):
        """download_master_file 메서드 시그니처 확인"""
        import inspect
        sig = inspect.signature(KoreaInvestment.download_master_file)
        params = sig.parameters

        # 파라미터 존재 확인
        assert 'ttl_hours' in params
        assert 'force_download' in params

        # 기본값 확인
        assert params['ttl_hours'].default == 168
        assert params['force_download'].default is False

        # 반환 타입 확인
        assert sig.return_annotation == bool
