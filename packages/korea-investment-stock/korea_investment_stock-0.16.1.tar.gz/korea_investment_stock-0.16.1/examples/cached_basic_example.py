"""
캐싱 기능 기본 사용 예제

메모리 기반 캐싱을 통해 불필요한 API 호출을 줄이고 응답 속도를 개선합니다.
"""

import os
import time
from korea_investment_stock import KoreaInvestment, CachedKoreaInvestment


def example_basic_usage():
    """기본 사용법"""
    print("=" * 60)
    print("1. 기본 사용법")
    print("=" * 60)

    # 환경 변수에서 API 정보 로드
    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("⚠️  환경 변수가 설정되지 않았습니다.")
        print("다음 환경 변수를 설정해주세요:")
        print("  - KOREA_INVESTMENT_API_KEY")
        print("  - KOREA_INVESTMENT_API_SECRET")
        print("  - KOREA_INVESTMENT_ACCOUNT_NO")
        return

    # 기본 broker 생성
    broker = KoreaInvestment(api_key, api_secret, acc_no)

    # 캐싱 래퍼 적용
    cached_broker = CachedKoreaInvestment(broker)

    # 가격 조회 (첫 호출 - 캐시 미스)
    print("\n첫 번째 조회 (API 호출):")
    start = time.time()
    result = cached_broker.fetch_price("005930", "KR")
    elapsed1 = time.time() - start
    print(f"  - 삼성전자 현재가: {result['output']['stck_prpr']}원")
    print(f"  - 소요 시간: {elapsed1*1000:.2f}ms")

    # 동일 종목 재조회 (캐시 히트)
    print("\n두 번째 조회 (캐시 사용):")
    start = time.time()
    result = cached_broker.fetch_price("005930", "KR")
    elapsed2 = time.time() - start
    print(f"  - 삼성전자 현재가: {result['output']['stck_prpr']}원")
    print(f"  - 소요 시간: {elapsed2*1000:.2f}ms")
    print(f"  - 속도 개선: {(1 - elapsed2/elapsed1)*100:.1f}%")

    # 캐시 통계
    stats = cached_broker.get_cache_stats()
    print(f"\n캐시 통계:")
    print(f"  - 캐시 크기: {stats['cache_size']}")
    print(f"  - 히트: {stats['hits']}")
    print(f"  - 미스: {stats['misses']}")
    print(f"  - 히트율: {stats['hit_rate']}")


def example_custom_ttl():
    """TTL 커스터마이징 예제"""
    print("\n" + "=" * 60)
    print("2. TTL 커스터마이징")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        return

    broker = KoreaInvestment(api_key, api_secret, acc_no)

    # 실시간 트레이딩용: 짧은 TTL
    print("\n실시간 트레이딩용 설정 (price_ttl=1초):")
    cached_broker = CachedKoreaInvestment(
        broker,
        price_ttl=1,        # 1초
        stock_info_ttl=60   # 1분
    )

    stats = cached_broker.get_cache_stats()
    print(f"  - 가격 TTL: {stats['ttl_config']['price']}초")
    print(f"  - 종목정보 TTL: {stats['ttl_config']['stock_info']}초")

    # 백테스팅/분석용: 긴 TTL
    print("\n백테스팅/분석용 설정 (price_ttl=60초):")
    cached_broker2 = CachedKoreaInvestment(
        broker,
        price_ttl=60,       # 1분
        stock_info_ttl=3600 # 1시간
    )

    stats2 = cached_broker2.get_cache_stats()
    print(f"  - 가격 TTL: {stats2['ttl_config']['price']}초")
    print(f"  - 종목정보 TTL: {stats2['ttl_config']['stock_info']}초")


def example_context_manager():
    """컨텍스트 매니저 예제"""
    print("\n" + "=" * 60)
    print("3. 컨텍스트 매니저 사용")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        return

    broker = KoreaInvestment(api_key, api_secret, acc_no)

    # with 블록으로 자동 정리
    print("\nwith 블록 사용 (자동 캐시 정리):")
    with CachedKoreaInvestment(broker) as cached_broker:
        symbols = ["005930", "000660", "035720"]
        for symbol in symbols:
            result = cached_broker.fetch_price(symbol, "KR")
            print(f"  - {symbol}: {result['output']['stck_prpr']}원")

        stats = cached_broker.get_cache_stats()
        print(f"\n  캐시 크기: {stats['cache_size']}")
    # with 블록 종료 시 캐시 자동 정리됨
    print("  ✅ with 블록 종료 → 캐시 자동 정리 완료")


def example_cache_control():
    """캐시 제어 예제"""
    print("\n" + "=" * 60)
    print("4. 캐시 제어")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        return

    broker = KoreaInvestment(api_key, api_secret, acc_no)
    cached_broker = CachedKoreaInvestment(broker, price_ttl=60)

    # 가격 조회
    print("\n여러 종목 조회:")
    symbols = ["005930", "000660", "035720"]
    for symbol in symbols:
        result = cached_broker.fetch_price(symbol, "KR")
        print(f"  - {symbol}: {result['output']['stck_prpr']}원")

    stats = cached_broker.get_cache_stats()
    print(f"\n조회 후 캐시 통계:")
    print(f"  - 캐시 크기: {stats['cache_size']}")
    print(f"  - 히트: {stats['hits']}")
    print(f"  - 미스: {stats['misses']}")

    # 캐시 무효화 (예: 장 시작/마감 시)
    print("\n캐시 무효화 (장 마감 시):")
    cached_broker.invalidate_cache()

    stats_after = cached_broker.get_cache_stats()
    print(f"  - 무효화 후 캐시 크기: {stats_after['cache_size']}")
    print(f"  - 제거된 항목: {stats_after['evictions']}")


def example_performance_comparison():
    """성능 비교 예제"""
    print("\n" + "=" * 60)
    print("5. 성능 비교 (캐싱 전후)")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        return

    broker = KoreaInvestment(api_key, api_secret, acc_no)
    cached_broker = CachedKoreaInvestment(broker, price_ttl=10)

    symbols = ["005930", "000660", "035720", "051910", "068270"]
    iterations = 3

    print(f"\n{len(symbols)}개 종목을 {iterations}회 반복 조회:")

    # 캐싱 없이 조회
    print("\n[캐싱 없음]")
    start = time.time()
    for _ in range(iterations):
        for symbol in symbols:
            broker.fetch_price(symbol, "KR")
    elapsed_no_cache = time.time() - start
    total_calls_no_cache = len(symbols) * iterations
    print(f"  - 총 API 호출: {total_calls_no_cache}회")
    print(f"  - 총 소요 시간: {elapsed_no_cache:.2f}초")
    print(f"  - 평균 응답 시간: {elapsed_no_cache/total_calls_no_cache*1000:.0f}ms")

    # 캐싱 사용
    print("\n[캐싱 사용]")
    start = time.time()
    for _ in range(iterations):
        for symbol in symbols:
            cached_broker.fetch_price(symbol, "KR")
    elapsed_with_cache = time.time() - start

    stats = cached_broker.get_cache_stats()
    print(f"  - 캐시 히트: {stats['hits']}회")
    print(f"  - 캐시 미스: {stats['misses']}회")
    print(f"  - 실제 API 호출: {stats['misses']}회")
    print(f"  - 총 소요 시간: {elapsed_with_cache:.2f}초")

    # 성능 개선
    print("\n[성능 개선]")
    api_reduction = (1 - stats['misses'] / total_calls_no_cache) * 100
    time_reduction = (1 - elapsed_with_cache / elapsed_no_cache) * 100
    print(f"  - API 호출 감소: {api_reduction:.1f}%")
    print(f"  - 응답 시간 개선: {time_reduction:.1f}%")


def main():
    """메인 함수"""
    print("\n🚀 캐싱 기능 기본 사용 예제\n")

    # 1. 기본 사용법
    example_basic_usage()

    # 2. TTL 커스터마이징
    example_custom_ttl()

    # 3. 컨텍스트 매니저
    example_context_manager()

    # 4. 캐시 제어
    example_cache_control()

    # 5. 성능 비교
    example_performance_comparison()

    print("\n" + "=" * 60)
    print("✅ 모든 예제 실행 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
