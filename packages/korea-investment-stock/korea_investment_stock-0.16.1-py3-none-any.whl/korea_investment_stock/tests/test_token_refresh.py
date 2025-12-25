"""토큰 자동 재발급 테스트"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class MockResponse:
    """Mock HTTP 응답 객체"""

    def __init__(self, json_data):
        self._json = json_data

    def json(self):
        return self._json


class TestTokenExpiredDetection:
    """토큰 만료 응답 감지 테스트"""

    def _create_broker_mock(self):
        """테스트용 KoreaInvestment 인스턴스 생성"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            return broker

    def test_detects_expired_token(self):
        """토큰 만료 메시지 감지"""
        broker = self._create_broker_mock()

        expired_resp = {"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}
        assert broker._is_token_expired_response(expired_resp) is True

    def test_detects_expired_token_with_period(self):
        """토큰 만료 메시지 감지 (마침표 포함)"""
        broker = self._create_broker_mock()

        expired_resp = {"rt_cd": "1", "msg1": "기간이 만료된 token 입니다."}
        assert broker._is_token_expired_response(expired_resp) is True

    def test_detects_expired_token_variation(self):
        """다양한 토큰 만료 메시지 감지"""
        broker = self._create_broker_mock()

        # 다양한 만료 메시지 패턴
        variations = [
            {"rt_cd": "1", "msg1": "token이 만료되었습니다"},
            {"rt_cd": "1", "msg1": "Token 만료"},
            {"rt_cd": "1", "msg1": "만료된 TOKEN입니다"},
        ]
        for resp in variations:
            assert broker._is_token_expired_response(resp) is True, f"Failed for: {resp['msg1']}"

    def test_ignores_other_errors(self):
        """다른 에러는 토큰 만료로 감지하지 않음"""
        broker = self._create_broker_mock()

        other_error = {"rt_cd": "1", "msg1": "잘못된 종목코드입니다"}
        assert broker._is_token_expired_response(other_error) is False

    def test_ignores_expiry_without_token(self):
        """token 없이 만료만 있는 경우는 무시"""
        broker = self._create_broker_mock()

        # "만료"는 있지만 "token"이 없는 경우
        no_token = {"rt_cd": "1", "msg1": "세션이 만료되었습니다"}
        assert broker._is_token_expired_response(no_token) is False

    def test_success_response_not_expired(self):
        """성공 응답은 만료로 감지하지 않음"""
        broker = self._create_broker_mock()

        success_resp = {"rt_cd": "0", "output": {}}
        assert broker._is_token_expired_response(success_resp) is False

    def test_missing_msg1_field(self):
        """msg1 필드가 없는 경우"""
        broker = self._create_broker_mock()

        no_msg = {"rt_cd": "1"}
        assert broker._is_token_expired_response(no_msg) is False


class TestAutoTokenRefresh:
    """자동 토큰 재발급 테스트"""

    def _create_broker_mock(self):
        """테스트용 KoreaInvestment 인스턴스 생성"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker.access_token = "Bearer old_token"
            broker._token_manager = Mock()
            return broker

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_refreshes_token_on_expiry(self, mock_get):
        """토큰 만료 시 재발급 후 재시도"""
        broker = self._create_broker_mock()

        # 첫 번째: 만료 응답, 두 번째: 성공 응답
        mock_get.side_effect = [
            MockResponse({"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}),
            MockResponse({"rt_cd": "0", "output": {"stck_prpr": "70000"}})
        ]

        # issue_access_token(force=True) 동작 설정
        def refresh_token(force=False):
            if force:
                broker.access_token = "Bearer new_token"

        broker.issue_access_token = Mock(side_effect=refresh_token)

        headers = {"authorization": broker.access_token}
        result = broker._request_with_token_refresh("GET", "http://test", headers, {})

        # 토큰 재발급 호출 확인
        broker.issue_access_token.assert_called_once_with(force=True)
        # 최종 결과 확인
        assert result["rt_cd"] == "0"
        assert result["output"]["stck_prpr"] == "70000"

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_no_infinite_retry(self, mock_get):
        """재시도 횟수 제한 (무한 루프 방지)"""
        broker = self._create_broker_mock()

        # 계속 만료 응답
        mock_get.return_value = MockResponse(
            {"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}
        )

        broker.issue_access_token = Mock()

        headers = {"authorization": broker.access_token}
        result = broker._request_with_token_refresh(
            "GET", "http://test", headers, {}, max_retries=1
        )

        # 재발급은 1회만
        assert broker.issue_access_token.call_count == 1
        # 결과는 여전히 만료 응답
        assert result["rt_cd"] == "1"

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_header_updated_after_refresh(self, mock_get):
        """헤더의 authorization 갱신 확인"""
        broker = self._create_broker_mock()

        # 첫 번째: 만료 응답, 두 번째: 성공 응답
        mock_get.side_effect = [
            MockResponse({"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}),
            MockResponse({"rt_cd": "0", "output": {}})
        ]

        def refresh_token(force=False):
            if force:
                broker.access_token = "Bearer new_token"

        broker.issue_access_token = Mock(side_effect=refresh_token)

        headers = {"authorization": "Bearer old_token"}
        broker._request_with_token_refresh("GET", "http://test", headers, {})

        # 두 번째 호출 시 헤더가 갱신되었는지 확인
        second_call_headers = mock_get.call_args_list[1][1]["headers"]
        assert second_call_headers["authorization"] == "Bearer new_token"

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_success_response_no_retry(self, mock_get):
        """성공 응답 시 재시도 없음"""
        broker = self._create_broker_mock()

        mock_get.return_value = MockResponse(
            {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        )

        broker.issue_access_token = Mock()

        headers = {"authorization": broker.access_token}
        result = broker._request_with_token_refresh("GET", "http://test", headers, {})

        # 재발급 호출 없음
        broker.issue_access_token.assert_not_called()
        # 성공 응답 반환
        assert result["rt_cd"] == "0"

    @patch('korea_investment_stock.korea_investment_stock.requests.post')
    def test_post_request_with_token_refresh(self, mock_post):
        """POST 요청에서도 토큰 재발급 동작"""
        broker = self._create_broker_mock()

        # 첫 번째: 만료 응답, 두 번째: 성공 응답
        mock_post.side_effect = [
            MockResponse({"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}),
            MockResponse({"rt_cd": "0", "output": {}})
        ]

        def refresh_token(force=False):
            if force:
                broker.access_token = "Bearer new_token"

        broker.issue_access_token = Mock(side_effect=refresh_token)

        headers = {"authorization": broker.access_token}
        result = broker._request_with_token_refresh(
            "POST", "http://test", headers, {"data": "value"}
        )

        # 토큰 재발급 호출 확인
        broker.issue_access_token.assert_called_once_with(force=True)
        assert result["rt_cd"] == "0"

    @patch('korea_investment_stock.korea_investment_stock.requests.get')
    def test_max_retries_zero(self, mock_get):
        """max_retries=0이면 재시도 없음"""
        broker = self._create_broker_mock()

        mock_get.return_value = MockResponse(
            {"rt_cd": "1", "msg1": "기간이 만료된 token 입니다"}
        )

        broker.issue_access_token = Mock()

        headers = {"authorization": broker.access_token}
        result = broker._request_with_token_refresh(
            "GET", "http://test", headers, {}, max_retries=0
        )

        # 재발급 호출 없음
        broker.issue_access_token.assert_not_called()
        # 만료 응답 그대로 반환
        assert result["rt_cd"] == "1"


class TestIssueAccessTokenForce:
    """issue_access_token force 옵션 테스트"""

    def test_issue_access_token_force_true(self):
        """force=True면 강제 재발급"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker._token_manager = Mock()
            broker._token_manager.access_token = "Bearer new_token"
            broker._token_manager._issue_token = Mock()
            broker.access_token = "Bearer old_token"

            broker.issue_access_token(force=True)

            # _issue_token 직접 호출
            broker._token_manager._issue_token.assert_called_once()
            # 새 토큰으로 갱신
            assert broker.access_token == "Bearer new_token"

    def test_issue_access_token_force_false(self):
        """force=False면 기존 동작 (get_valid_token)"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker._token_manager = Mock()
            broker._token_manager.get_valid_token = Mock(return_value="Bearer valid_token")
            broker.access_token = "Bearer old_token"

            broker.issue_access_token(force=False)

            # get_valid_token 호출
            broker._token_manager.get_valid_token.assert_called_once()
            assert broker.access_token == "Bearer valid_token"

    def test_issue_access_token_default_no_force(self):
        """기본 동작은 force=False"""
        from korea_investment_stock import KoreaInvestment

        with patch.object(KoreaInvestment, '__init__', lambda x: None):
            broker = KoreaInvestment.__new__(KoreaInvestment)
            broker._token_manager = Mock()
            broker._token_manager.get_valid_token = Mock(return_value="Bearer valid_token")
            broker.access_token = "Bearer old_token"

            broker.issue_access_token()  # force 인자 없음

            # get_valid_token 호출 (force=False 동작)
            broker._token_manager.get_valid_token.assert_called_once()
