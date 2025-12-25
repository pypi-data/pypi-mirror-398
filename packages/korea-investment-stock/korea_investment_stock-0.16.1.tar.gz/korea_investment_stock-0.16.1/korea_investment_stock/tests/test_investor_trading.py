"""종목별 투자자매매동향(일별) 단위 테스트"""
import pytest
from unittest.mock import Mock, patch


class MockResponse:
    """Mock HTTP 응답 객체"""

    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json


class TestFetchInvestorTradingByStockDaily:
    """fetch_investor_trading_by_stock_daily 단위 테스트"""

    def _create_broker_mock(self):
        """테스트용 KoreaInvestment 인스턴스 생성"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker.base_url = "https://openapi.koreainvestment.com:9443"
            broker.access_token = "Bearer test_token"
            broker.api_key = "test_api_key"
            broker.api_secret = "test_api_secret"
            broker._token_manager = Mock()
            return broker

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_success_response(self, mock_get):
        """성공 응답 테스트"""
        broker = self._create_broker_mock()

        mock_response = {
            'rt_cd': '0',
            'msg_cd': 'MCA00000',
            'msg1': '정상처리되었습니다',
            'output1': {
                'stck_prpr': '70000',
                'prdy_vrss': '1000',
                'prdy_ctrt': '1.45',
                'acml_vol': '10000000'
            },
            'output2': [
                {
                    'stck_bsop_date': '20251212',
                    'frgn_ntby_qty': '100000',
                    'orgn_ntby_qty': '-50000',
                    'prsn_ntby_qty': '-50000',
                    'frgn_ntby_tr_pbmn': '7000',
                    'orgn_ntby_tr_pbmn': '-3500',
                    'prsn_ntby_tr_pbmn': '-3500'
                }
            ]
        }
        mock_get.return_value = MockResponse(mock_response)

        result = broker.fetch_investor_trading_by_stock_daily("005930", "20251212")

        assert result['rt_cd'] == '0'
        assert 'output1' in result
        assert 'output2' in result
        assert len(result['output2']) > 0
        assert result['output2'][0]['frgn_ntby_qty'] == '100000'

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_request_url_and_headers(self, mock_get):
        """요청 URL 및 헤더 검증"""
        broker = self._create_broker_mock()

        mock_get.return_value = MockResponse({'rt_cd': '0'})

        broker.fetch_investor_trading_by_stock_daily("005930", "20251212")

        call_args = mock_get.call_args
        url = call_args[0][0]
        headers = call_args[1]['headers']

        # URL 검증
        assert "investor-trade-by-stock-daily" in url

        # 헤더 검증
        assert headers['tr_id'] == 'FHPTJ04160001'
        assert headers['appKey'] == 'test_api_key'
        assert headers['appSecret'] == 'test_api_secret'
        assert headers['authorization'] == 'Bearer test_token'

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_request_params_default_market_code(self, mock_get):
        """기본 시장 코드(J) 파라미터 검증"""
        broker = self._create_broker_mock()

        mock_get.return_value = MockResponse({'rt_cd': '0'})

        broker.fetch_investor_trading_by_stock_daily("005930", "20251212")

        call_args = mock_get.call_args
        params = call_args[1]['params']

        assert params['FID_COND_MRKT_DIV_CODE'] == 'J'
        assert params['FID_INPUT_ISCD'] == '005930'
        assert params['FID_INPUT_DATE_1'] == '20251212'
        assert params['FID_ORG_ADJ_PRC'] == ''
        assert params['FID_ETC_CLS_CODE'] == ''

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_market_code_options(self, mock_get):
        """시장 코드 옵션 테스트 (J, NX, UN)"""
        broker = self._create_broker_mock()

        mock_get.return_value = MockResponse({'rt_cd': '0'})

        for market_code in ["J", "NX", "UN"]:
            broker.fetch_investor_trading_by_stock_daily("005930", "20251212", market_code)

            call_args = mock_get.call_args
            params = call_args[1]['params']

            assert params['FID_COND_MRKT_DIV_CODE'] == market_code

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_error_response(self, mock_get):
        """에러 응답 테스트"""
        broker = self._create_broker_mock()

        mock_response = {
            'rt_cd': '1',
            'msg_cd': 'MCA01000',
            'msg1': '잘못된 종목코드입니다'
        }
        mock_get.return_value = MockResponse(mock_response)

        result = broker.fetch_investor_trading_by_stock_daily("INVALID", "20251212")

        assert result['rt_cd'] == '1'

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_token_refresh_on_expiry(self, mock_get):
        """토큰 만료 시 자동 재발급 테스트"""
        broker = self._create_broker_mock()

        # 첫 번째: 만료 응답, 두 번째: 성공 응답
        mock_get.side_effect = [
            MockResponse({"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}),
            MockResponse({"rt_cd": "0", "output1": {}, "output2": []})
        ]

        def refresh_token(force=False):
            if force:
                broker.access_token = "Bearer new_token"

        broker.issue_access_token = Mock(side_effect=refresh_token)

        result = broker.fetch_investor_trading_by_stock_daily("005930", "20251212")

        # 토큰 재발급 호출 확인
        broker.issue_access_token.assert_called_once_with(force=True)
        # 최종 결과 확인
        assert result["rt_cd"] == "0"


class TestCachedInvestorTrading:
    """CachedKoreaInvestment의 투자자 매매동향 캐싱 테스트"""

    def test_cache_hit(self):
        """캐시 히트 테스트"""
        from korea_investment_stock import KoreaInvestment
        from korea_investment_stock.cache import CachedKoreaInvestment

        # Mock broker
        mock_broker = Mock(spec=KoreaInvestment)
        mock_broker.fetch_investor_trading_by_stock_daily.return_value = {
            'rt_cd': '0',
            'output2': [{'frgn_ntby_qty': '100000'}]
        }

        cached = CachedKoreaInvestment(mock_broker, enable_cache=True)

        # 첫 번째 호출 - 캐시 미스
        result1 = cached.fetch_investor_trading_by_stock_daily("005930", "20251210")
        assert result1['rt_cd'] == '0'

        # 두 번째 호출 - 캐시 히트 (broker 호출 안됨)
        result2 = cached.fetch_investor_trading_by_stock_daily("005930", "20251210")
        assert result2['rt_cd'] == '0'

        # broker는 한 번만 호출됨
        assert mock_broker.fetch_investor_trading_by_stock_daily.call_count == 1

    def test_cache_disabled(self):
        """캐시 비활성화 테스트"""
        from korea_investment_stock import KoreaInvestment
        from korea_investment_stock.cache import CachedKoreaInvestment

        mock_broker = Mock(spec=KoreaInvestment)
        mock_broker.fetch_investor_trading_by_stock_daily.return_value = {
            'rt_cd': '0',
            'output2': []
        }

        cached = CachedKoreaInvestment(mock_broker, enable_cache=False)

        # 두 번 호출
        cached.fetch_investor_trading_by_stock_daily("005930", "20251210")
        cached.fetch_investor_trading_by_stock_daily("005930", "20251210")

        # broker가 두 번 호출됨
        assert mock_broker.fetch_investor_trading_by_stock_daily.call_count == 2


class TestRateLimitedInvestorTrading:
    """RateLimitedKoreaInvestment의 투자자 매매동향 테스트"""

    def test_rate_limit_applied(self):
        """속도 제한 적용 테스트"""
        from korea_investment_stock import KoreaInvestment
        from korea_investment_stock.rate_limit import RateLimitedKoreaInvestment

        mock_broker = Mock(spec=KoreaInvestment)
        mock_broker.fetch_investor_trading_by_stock_daily.return_value = {
            'rt_cd': '0',
            'output2': []
        }

        rate_limited = RateLimitedKoreaInvestment(mock_broker, calls_per_second=10)

        result = rate_limited.fetch_investor_trading_by_stock_daily("005930", "20251210")

        assert result['rt_cd'] == '0'
        mock_broker.fetch_investor_trading_by_stock_daily.assert_called_once_with(
            "005930", "20251210", "J"
        )

    def test_rate_limit_stats(self):
        """속도 제한 통계 테스트"""
        from korea_investment_stock import KoreaInvestment
        from korea_investment_stock.rate_limit import RateLimitedKoreaInvestment

        mock_broker = Mock(spec=KoreaInvestment)
        mock_broker.fetch_investor_trading_by_stock_daily.return_value = {
            'rt_cd': '0',
            'output2': []
        }

        rate_limited = RateLimitedKoreaInvestment(mock_broker, calls_per_second=15)

        # 몇 번 호출
        rate_limited.fetch_investor_trading_by_stock_daily("005930", "20251210")
        rate_limited.fetch_investor_trading_by_stock_daily("005930", "20251211")

        stats = rate_limited.get_rate_limit_stats()

        assert stats['total_calls'] >= 2
        assert stats['calls_per_second'] == 15.0
