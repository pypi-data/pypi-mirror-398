import os
import pytest
from korea_investment_stock import KoreaInvestment, Config
from .rate_limited_korea_investment import RateLimitedKoreaInvestment


@pytest.fixture
def broker():
    """KoreaInvestment 브로커 픽스처"""
    api_key = os.environ.get('KOREA_INVESTMENT_API_KEY')
    api_secret = os.environ.get('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.environ.get('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        pytest.skip("API credentials not found in environment variables")

    config = Config(
        api_key=api_key,
        api_secret=api_secret,
        acc_no=acc_no,
        token_storage_type="file",
    )
    return KoreaInvestment(config=config)


def test_rate_limited_basic(broker):
    """기본 속도 제한 통합 테스트"""
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # 30번 API 호출
    test_stocks = [
        ("005930", "KR"),  # 삼성전자
        ("035720", "KR"),  # 카카오
        ("AAPL", "US"),    # Apple
    ]

    success_count = 0
    for _ in range(10):
        for symbol, market in test_stocks:
            result = rate_limited.fetch_price(symbol, market)
            if result['rt_cd'] == '0':
                success_count += 1
            else:
                print(f"API 호출 실패: {symbol}/{market} - {result.get('msg1', 'Unknown error')}")

    # 성공률 검증 (최소 90% 이상)
    success_rate = success_count / 30
    assert success_rate >= 0.9, \
        f"Expected success rate >= 90%, got {success_rate*100:.1f}%"


def test_rate_limited_context_manager(broker):
    """컨텍스트 매니저 테스트"""
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    with rate_limited:
        result = rate_limited.fetch_price("005930", "KR")
        assert result['rt_cd'] == '0', \
            f"API call failed: {result.get('msg1', 'Unknown error')}"


def test_rate_limited_preserves_functionality(broker):
    """래퍼가 모든 API 기능을 보존하는지 테스트"""
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # fetch_price 테스트
    result = rate_limited.fetch_price("005930", "KR")
    assert result['rt_cd'] == '0', \
        f"fetch_price failed: {result.get('msg1', 'Unknown error')}"

    # fetch_stock_info 테스트
    result = rate_limited.fetch_stock_info("AAPL", "US")
    assert result['rt_cd'] == '0', \
        f"fetch_stock_info failed: {result.get('msg1', 'Unknown error')}"


def test_rate_limited_stats(broker):
    """통계 조회 테스트"""
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # 3번 호출
    for _ in range(3):
        rate_limited.fetch_price("005930", "KR")

    # 통계 확인
    stats = rate_limited.get_rate_limit_stats()

    assert stats['calls_per_second'] == 15, \
        f"Expected calls_per_second=15, got {stats['calls_per_second']}"
    assert stats['total_calls'] == 3, \
        f"Expected total_calls=3, got {stats['total_calls']}"


def test_rate_limited_adjust_runtime(broker):
    """런타임 속도 조정 테스트"""
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # 초기 설정 확인
    stats = rate_limited.get_rate_limit_stats()
    assert stats['calls_per_second'] == 15

    # 속도 조정
    rate_limited.adjust_rate_limit(calls_per_second=10)

    # 변경 확인
    stats = rate_limited.get_rate_limit_stats()
    assert stats['calls_per_second'] == 10

    # 조정된 속도로 API 호출
    for _ in range(10):
        result = rate_limited.fetch_price("005930", "KR")
        assert result['rt_cd'] == '0'


def test_rate_limited_multiple_markets(broker):
    """다양한 시장(KR/US) 혼합 호출 테스트"""
    rate_limited = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    # KR과 US 종목 혼합
    test_stocks = [
        ("005930", "KR"),  # 삼성전자
        ("AAPL", "US"),    # Apple
        ("035720", "KR"),  # 카카오
        ("MSFT", "US"),    # Microsoft
        ("000660", "KR"),  # SK하이닉스
        ("GOOGL", "US"),   # Google
    ]

    success_count = 0
    for symbol, market in test_stocks:
        result = rate_limited.fetch_price(symbol, market)
        if result['rt_cd'] == '0':
            success_count += 1

    # 성공률 검증 (최소 90% 이상)
    success_rate = success_count / len(test_stocks)
    assert success_rate >= 0.9, \
        f"Expected success rate >= 90%, got {success_rate*100:.1f}%"
