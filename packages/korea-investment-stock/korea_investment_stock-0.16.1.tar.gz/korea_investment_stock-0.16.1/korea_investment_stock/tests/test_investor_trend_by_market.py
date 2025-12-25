"""시장별 투자자매매동향(시세) 통합 테스트

이 테스트는 실제 API 자격 증명이 필요합니다.
환경 변수 설정:
    - KOREA_INVESTMENT_API_KEY
    - KOREA_INVESTMENT_API_SECRET
    - KOREA_INVESTMENT_ACCOUNT_NO

실행:
    pytest korea_investment_stock/tests/test_investor_trend_by_market.py -v
"""
import os
import pytest


def _has_api_credentials() -> bool:
    """API 자격 증명이 설정되어 있는지 확인"""
    return all([
        os.environ.get("KOREA_INVESTMENT_API_KEY"),
        os.environ.get("KOREA_INVESTMENT_API_SECRET"),
        os.environ.get("KOREA_INVESTMENT_ACCOUNT_NO"),
    ])


@pytest.mark.integration
@pytest.mark.skipif(
    not _has_api_credentials(),
    reason="API credentials not available (KOREA_INVESTMENT_* env vars required)"
)
class TestInvestorTrendByMarketIntegration:
    """시장별 투자자매매동향(시세) API 통합 테스트"""

    @pytest.fixture
    def broker(self):
        """실제 API 자격 증명으로 broker 생성"""
        from korea_investment_stock import KoreaInvestment
        return KoreaInvestment()

    def test_kospi_investor_trend(self, broker):
        """코스피 종합 투자자 동향 조회"""
        result = broker.fetch_investor_trend_by_market("KSP", "0001")

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output' in result

    def test_kosdaq_investor_trend(self, broker):
        """코스닥 종합 투자자 동향 조회"""
        result = broker.fetch_investor_trend_by_market("KSQ", "1001")

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output' in result

    def test_etf_investor_trend(self, broker):
        """ETF 전체 투자자 동향 조회"""
        result = broker.fetch_investor_trend_by_market("ETF", "T000")

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output' in result

    def test_default_parameters(self, broker):
        """기본 파라미터(코스피 종합) 테스트"""
        result = broker.fetch_investor_trend_by_market()

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output' in result

    def test_investor_trend_response_fields(self, broker):
        """응답 필드 검증"""
        result = broker.fetch_investor_trend_by_market("KSP", "0001")

        if result['rt_cd'] == '0' and result.get('output'):
            item = result['output'][0]

            # 주요 투자자 유형별 순매수 필드 존재 확인
            expected_fields = [
                'frgn_ntby_qty',   # 외국인 순매수 수량
                'prsn_ntby_qty',   # 개인 순매수 수량
                'orgn_ntby_qty',   # 기관 순매수 수량
            ]

            for field in expected_fields:
                assert field in item, f"Missing field: {field}"

    def test_context_manager(self, broker):
        """컨텍스트 매니저 테스트"""
        from korea_investment_stock import KoreaInvestment

        with KoreaInvestment() as ctx_broker:
            result = ctx_broker.fetch_investor_trend_by_market("KSP", "0001")
            assert result['rt_cd'] == '0'
