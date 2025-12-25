"""
Stress Test Example

종목 리스트를 순회하며 종목 정보와 가격을 조회하는 간단한 stress test
Rate Limiting을 적용하여 API 호출 속도를 자동으로 조절합니다.
"""

import os
import time
import yaml
import logging
from pathlib import Path
from korea_investment_stock import KoreaInvestment, RateLimitedKoreaInvestment

# Logging 설정 (DEBUG 레벨로 설정하면 rate limit 로그 확인 가능)
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_stock_list(yaml_path: str) -> list:
    """
    YAML 파일에서 종목 리스트 로드

    Args:
        yaml_path: YAML 파일 경로

    Returns:
        종목 리스트 [["symbol", "market"], ...]
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['stock_list']


def run_stress_test():
    """
    종목 리스트를 순회하며 API 호출 stress test 실행

    각 종목에 대해:
    1. fetch_stock_info() 호출
    2. fetch_price() 호출

    Rate Limiting (15회/초)이 자동으로 적용되어 API 속도 제한 에러를 방지합니다.
    """
    # Environment variables
    api_key = os.environ.get('KOREA_INVESTMENT_API_KEY')
    api_secret = os.environ.get('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.environ.get('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("❌ Error: 환경변수를 설정해주세요:")
        print("  - KOREA_INVESTMENT_API_KEY")
        print("  - KOREA_INVESTMENT_API_SECRET")
        print("  - KOREA_INVESTMENT_ACCOUNT_NO")
        return

    # Load stock list
    yaml_path = Path(__file__).parent / 'testdata' / 'stock_list.yaml'
    stock_list = load_stock_list(yaml_path)

    print(f"📋 총 {len(stock_list)}개 종목 stress test 시작")
    print("⚡ Rate Limiting: 15 calls/second")
    print("=" * 60)

    success_count = 0
    error_count = 0
    start_time = time.time()

    # Initialize broker with rate limiting
    broker = KoreaInvestment(api_key, api_secret, acc_no)
    rate_limited_broker = RateLimitedKoreaInvestment(broker, calls_per_second=15)

    with rate_limited_broker:
        for i, (symbol, market) in enumerate(stock_list, 1):
            print(f"\n[{i}/{len(stock_list)}] {symbol} ({market})")

            # 1. fetch_stock_info
            try:
                info_result = rate_limited_broker.fetch_stock_info(symbol, market)
                if info_result['rt_cd'] == '0':
                    print(f"  ✅ Stock Info: Success")
                    success_count += 1
                else:
                    print(f"  ⚠️  Stock Info: {info_result['msg1']}")
                    error_count += 1
                    print("\n🚨 실패 감지: Stress test 중단")
                    break
            except Exception as e:
                print(f"  ❌ Stock Info Error: {e}")
                error_count += 1
                print("\n🚨 예외 발생: Stress test 중단")
                break

            # 2. fetch_price
            try:
                price_result = rate_limited_broker.fetch_price(symbol, market)
                if price_result['rt_cd'] == '0':
                    print(f"  ✅ Price: Success")
                    success_count += 1
                else:
                    print(f"  ⚠️  Price: {price_result['msg1']}")
                    error_count += 1
                    print("\n🚨 실패 감지: Stress test 중단")
                    break
            except Exception as e:
                print(f"  ❌ Price Error: {e}")
                error_count += 1
                print("\n🚨 예외 발생: Stress test 중단")
                break

    # Rate limit stats
    stats = rate_limited_broker.get_rate_limit_stats()

    # Summary
    elapsed_time = time.time() - start_time
    total_calls = success_count + error_count
    avg_time = elapsed_time / total_calls if total_calls > 0 else 0

    print("\n" + "=" * 60)
    print("📊 Stress Test 결과")
    print("=" * 60)
    print(f"총 API 호출: {total_calls}회")
    print(f"성공: {success_count}회")
    print(f"실패: {error_count}회")
    print(f"성공률: {success_count / total_calls * 100:.1f}%" if total_calls > 0 else "N/A")
    print(f"실행 시간: {elapsed_time:.2f}초")
    print(f"평균 응답 시간: {avg_time:.3f}초/호출")
    print(f"\n⚡ Rate Limit 통계:")
    print(f"  - 설정: {stats['calls_per_second']}회/초")
    print(f"  - 총 호출: {stats['total_calls']}회")
    print(f"  - Throttle된 호출: {stats['throttled_calls']}회")
    print(f"  - Throttle 비율: {stats['throttle_rate']*100:.1f}%")
    print(f"  - 총 대기 시간: {stats['total_wait_time']:.2f}초")
    print(f"  - 평균 대기 시간: {stats['avg_wait_time']:.3f}초")
    print(f"\n💡 Tip: DEBUG 로그를 보려면 파일 상단의 logging.basicConfig를 DEBUG로 변경하세요")


if __name__ == "__main__":
    run_stress_test()
