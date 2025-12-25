#!/usr/bin/env python3
"""
해외 주식 종목 코드 다운로드 예제

이 예제는 해외 거래소(나스닥, 뉴욕, 홍콩 등) 종목 코드를 다운로드하는 방법을 보여줍니다.
API 자격 증명이 필요하지만, 마스터 파일 다운로드는 공개 데이터입니다.
"""
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from korea_investment_stock import KoreaInvestment, OVERSEAS_MARKETS


def load_credentials():
    """환경 변수에서 API 자격 증명 로드"""
    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("API 자격 증명이 설정되지 않았습니다.")
        print("\n환경 변수를 설정하세요:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='your-account-no'")
        sys.exit(1)

    return api_key, api_secret, acc_no


def example_nasdaq_symbols():
    """나스닥 종목 코드 다운로드 예제"""
    print("\n" + "="*60)
    print("1. 나스닥(NASDAQ) 종목 코드 다운로드")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 나스닥 종목 다운로드 (첫 호출 시 다운로드, 이후 캐시 사용)
        df = broker.fetch_nasdaq_symbols()

        print(f"\n나스닥 종목 수: {len(df):,}개")
        print(f"컬럼: {list(df.columns)[:5]}...")

        # 샘플 데이터 출력
        print("\n[샘플 데이터 (상위 5개)]")
        print(df[['심볼', '한글명', '영문명', '통화']].head())


def example_us_all_symbols():
    """미국 전체 종목 (나스닥 + 뉴욕 + 아멕스) 통합 조회"""
    print("\n" + "="*60)
    print("2. 미국 전체 종목 통합 조회")
    print("="*60)

    import pandas as pd

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 3개 거래소 다운로드
        nasdaq = broker.fetch_nasdaq_symbols()
        nyse = broker.fetch_nyse_symbols()
        amex = broker.fetch_amex_symbols()

        # 통합
        us_stocks = pd.concat([nasdaq, nyse, amex], ignore_index=True)

        print(f"\n나스닥: {len(nasdaq):,}개")
        print(f"뉴욕증권거래소: {len(nyse):,}개")
        print(f"아멕스: {len(amex):,}개")
        print(f"미국 전체: {len(us_stocks):,}개")


def example_overseas_symbols():
    """다양한 해외 거래소 종목 조회"""
    print("\n" + "="*60)
    print("3. 다양한 해외 거래소 종목 조회")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 홍콩 종목
        hk_df = broker.fetch_overseas_symbols("hks")
        print(f"\n홍콩 종목 수: {len(hk_df):,}개")

        # 도쿄 종목
        tse_df = broker.fetch_overseas_symbols("tse")
        print(f"도쿄 종목 수: {len(tse_df):,}개")

        # 상해 종목
        shs_df = broker.fetch_overseas_symbols("shs")
        print(f"상해 종목 수: {len(shs_df):,}개")


def example_search_symbol():
    """특정 종목 검색"""
    print("\n" + "="*60)
    print("4. 특정 종목 검색")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 나스닥 종목 다운로드
        nasdaq = broker.fetch_nasdaq_symbols()

        # AAPL 검색
        aapl = nasdaq[nasdaq['심볼'] == 'AAPL']
        if len(aapl) > 0:
            print("\n[AAPL 정보]")
            print(aapl[['심볼', '한글명', '영문명', '통화', '거래소코드']].to_string(index=False))

        # 한글명에 '애플' 포함 검색
        apple_stocks = nasdaq[nasdaq['한글명'].str.contains('애플', na=False)]
        if len(apple_stocks) > 0:
            print(f"\n[한글명에 '애플' 포함 종목: {len(apple_stocks)}개]")
            print(apple_stocks[['심볼', '한글명', '영문명']].head(10).to_string(index=False))


def example_cache_usage():
    """캐시 사용 예제"""
    print("\n" + "="*60)
    print("5. 캐시 사용 예제")
    print("="*60)

    import time

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 첫 번째 호출 - 다운로드
        print("\n[첫 번째 호출 - 다운로드]")
        start = time.time()
        df1 = broker.fetch_nasdaq_symbols()
        elapsed1 = time.time() - start
        print(f"소요 시간: {elapsed1:.2f}초, 종목 수: {len(df1):,}개")

        # 두 번째 호출 - 캐시 사용
        print("\n[두 번째 호출 - 캐시 사용]")
        start = time.time()
        df2 = broker.fetch_nasdaq_symbols()
        elapsed2 = time.time() - start
        print(f"소요 시간: {elapsed2:.2f}초, 종목 수: {len(df2):,}개")

        if elapsed2 < elapsed1:
            print(f"\n캐시로 {elapsed1 - elapsed2:.2f}초 단축!")

        # 강제 다운로드
        print("\n[강제 다운로드]")
        start = time.time()
        df3 = broker.fetch_nasdaq_symbols(force_download=True)
        elapsed3 = time.time() - start
        print(f"소요 시간: {elapsed3:.2f}초, 종목 수: {len(df3):,}개")


def example_list_markets():
    """지원하는 해외 시장 목록"""
    print("\n" + "="*60)
    print("6. 지원하는 해외 시장 목록")
    print("="*60)

    print("\n지원 거래소 (11개):")
    for code, name in OVERSEAS_MARKETS.items():
        print(f"  {code}: {name}")


def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("해외 주식 종목 코드 다운로드 예제")
    print("="*60)

    try:
        # 지원 시장 목록 확인
        example_list_markets()

        # 나스닥 종목 다운로드
        example_nasdaq_symbols()

        # 미국 전체 종목
        # example_us_all_symbols()

        # 다양한 해외 거래소
        # example_overseas_symbols()

        # 특정 종목 검색
        # example_search_symbol()

        # 캐시 사용
        # example_cache_usage()

        print("\n" + "="*60)
        print("모든 예제 실행 완료!")
        print("="*60)

    except Exception as e:
        print(f"\n예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
