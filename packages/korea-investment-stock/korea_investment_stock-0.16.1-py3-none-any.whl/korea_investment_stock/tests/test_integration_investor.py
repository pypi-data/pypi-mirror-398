"""종목별 투자자매매동향(일별) 통합 테스트

이 테스트는 실제 API 자격 증명이 필요합니다.
환경 변수 설정:
    - KOREA_INVESTMENT_API_KEY
    - KOREA_INVESTMENT_API_SECRET
    - KOREA_INVESTMENT_ACCOUNT_NO

실행:
    pytest korea_investment_stock/tests/test_integration_investor.py -v
"""
import pytest
from datetime import datetime, timedelta


@pytest.mark.integration
class TestInvestorTradingIntegration:
    """투자자 매매동향 API 통합 테스트"""

    @pytest.fixture
    def broker(self):
        """실제 API 자격 증명으로 broker 생성"""
        from korea_investment_stock import KoreaInvestment
        return KoreaInvestment()

    def test_samsung_investor_trading(self, broker):
        """삼성전자 투자자 매매동향 조회"""
        # 어제 날짜 (당일은 장 종료 후에만 조회 가능)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        result = broker.fetch_investor_trading_by_stock_daily("005930", yesterday)

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output1' in result
        assert 'output2' in result

    def test_hynix_investor_trading(self, broker):
        """SK하이닉스 투자자 매매동향 조회"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        result = broker.fetch_investor_trading_by_stock_daily("000660", yesterday)

        assert result['rt_cd'] == '0', f"API Error: {result.get('msg1', 'Unknown error')}"
        assert 'output2' in result

    def test_different_market_codes(self, broker):
        """다양한 시장 코드 테스트"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        # KRX (기본)
        result_j = broker.fetch_investor_trading_by_stock_daily("005930", yesterday, "J")
        assert result_j['rt_cd'] == '0', f"API Error (J): {result_j.get('msg1')}"

    def test_investor_trading_response_fields(self, broker):
        """응답 필드 검증"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        result = broker.fetch_investor_trading_by_stock_daily("005930", yesterday)

        if result['rt_cd'] == '0' and result.get('output2'):
            daily_data = result['output2'][0]

            # 주요 필드 존재 확인
            expected_fields = [
                'stck_bsop_date',  # 영업일자
                'frgn_ntby_qty',   # 외국인 순매수 수량
                'orgn_ntby_qty',   # 기관 순매수 수량
                'prsn_ntby_qty',   # 개인 순매수 수량
            ]

            for field in expected_fields:
                assert field in daily_data, f"Missing field: {field}"

    def test_context_manager(self, broker):
        """컨텍스트 매니저 테스트"""
        from korea_investment_stock import KoreaInvestment

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        with KoreaInvestment() as broker:
            result = broker.fetch_investor_trading_by_stock_daily("005930", yesterday)
            assert result['rt_cd'] == '0'
