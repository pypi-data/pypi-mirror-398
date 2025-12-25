#!/usr/bin/env python3
"""
한국투자증권 OpenAPI 기본 사용 예제

이 예제는 korea-investment-stock 라이브러리의 기본 사용법을 보여줍니다.
간단한 주식 조회 및 정보 확인 방법을 다룹니다.
"""
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from korea_investment_stock import KoreaInvestment


def load_credentials():
    """환경 변수에서 API 자격 증명 로드"""
    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("❌ API 자격 증명이 설정되지 않았습니다.")
        print("\n환경 변수를 설정하세요:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='your-account-no'")
        sys.exit(1)

    return api_key, api_secret, acc_no


def example_domestic_stock_price():
    """국내 주식 현재가 조회 예제"""
    print("\n" + "="*60)
    print("📌 1. 국내 주식 현재가 조회")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    # KoreaInvestment 인스턴스 생성
    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 삼성전자 현재가 조회
        result = broker.fetch_price("005930", "KR")

        if result['rt_cd'] == '0':
            output = result.get('output', {})
            print(f"\n✅ 삼성전자 (005930) 현재가:")
            print(f"  현재가: {int(output['stck_prpr']):,}원")
            print(f"  전일대비: {output['prdy_vrss']} ({output['prdy_ctrt']}%)")
            print(f"  시가: {int(output['stck_oprc']):,}원")
            print(f"  고가: {int(output['stck_hgpr']):,}원")
            print(f"  저가: {int(output['stck_lwpr']):,}원")
            print(f"  거래량: {int(output['acml_vol']):,}주")
            print(f"  시가총액: {int(output['hts_avls']):,}억원")
        else:
            print(f"❌ 조회 실패: {result.get('msg1', '알 수 없는 오류')}")


def example_us_stock_price():
    """미국 주식 현재가 조회 예제"""
    print("\n" + "="*60)
    print("📌 2. 미국 주식 현재가 조회")
    print("="*60)
    print("⚠️  주의: 미국 주식은 실전계좌만 지원됩니다.")

    api_key, api_secret, acc_no = load_credentials()

    # 실전계좌 사용
    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 애플 현재가 조회
        result = broker.fetch_price("AAPL", "US")

        if result['rt_cd'] == '0':
            output = result['output']
            print(f"\n✅ Apple (AAPL) 현재가:")
            print(f"  현재가: ${output['last']}")
            print(f"  전일대비: {output['t_xdif']} ({output['t_xrat']}%)")
            print(f"  시가: ${output['open']}")
            print(f"  고가: ${output['high']}")
            print(f"  저가: ${output['low']}")
            print(f"  거래량: {int(output['tvol']):,}")
            print(f"  PER: {output['perx']}")
            print(f"  PBR: {output['pbrx']}")
        else:
            print(f"❌ 조회 실패: {result.get('msg1', '알 수 없는 오류')}")


def example_stock_info():
    """종목 정보 조회 예제"""
    print("\n" + "="*60)
    print("📌 3. 종목 정보 조회")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 카카오 종목 정보 조회
        result = broker.fetch_stock_info("035720", "KR")

        if result['rt_cd'] == '0':
            output = result['output']
            print(f"\n✅ 카카오 (035720) 종목 정보:")
            print(f"  종목명: {output.get('prdt_name', 'N/A')}")
            print(f"  시장구분: {output.get('prdt_clsf_name', 'N/A')}")
            print(f"  표준산업분류: {output.get('std_idst_clsf_name', 'N/A')}")
        else:
            print(f"❌ 조회 실패: {result.get('msg1', '알 수 없는 오류')}")


def example_multiple_stocks():
    """여러 종목 순차 조회 예제"""
    print("\n" + "="*60)
    print("📌 4. 여러 종목 순차 조회")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    # 조회할 종목 리스트
    stocks = [
        ("005930", "KR"),  # 삼성전자
        ("000660", "KR"),  # SK하이닉스
        ("035720", "KR"),  # 카카오
    ]

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        print("\n📊 국내 주요 종목 현재가:")
        print("-" * 50)

        for symbol, market in stocks:
            result = broker.fetch_price(symbol, market)

            if result['rt_cd'] == '0':
                output = result.get('output', {})
                stock_name = {
                    "005930": "삼성전자",
                    "000660": "SK하이닉스",
                    "035720": "카카오"
                }.get(symbol, symbol)

                print(f"\n{stock_name} ({symbol}):")
                print(f"  현재가: {int(output['stck_prpr']):,}원")
                print(f"  전일대비: {output['prdy_vrss']} ({output['prdy_ctrt']}%)")
            else:
                print(f"\n{symbol}: ❌ 조회 실패")


def example_error_handling():
    """에러 처리 예제"""
    print("\n" + "="*60)
    print("📌 5. 에러 처리 예제")
    print("="*60)

    api_key, api_secret, acc_no = load_credentials()

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 잘못된 시장 코드
        try:
            print("\n테스트 1: 잘못된 시장 코드")
            result = broker.fetch_price("005930", "INVALID")
            print(f"결과: {result}")
        except ValueError as e:
            print(f"✅ ValueError 발생 (예상됨): {e}")

        # 존재하지 않는 종목
        print("\n테스트 2: 존재하지 않는 종목")
        result = broker.fetch_price("999999", "KR")
        if result['rt_cd'] != '0':
            print(f"✅ API 오류 응답 (예상됨): {result.get('msg1', 'N/A')}")


def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("🚀 한국투자증권 OpenAPI 기본 사용 예제")
    print("="*60)

    try:
        # 1. 국내 주식 현재가 조회
        example_domestic_stock_price()

        # 2. 미국 주식 현재가 조회 (실전계좌만 가능)
        print("\n미국 주식 조회 예제는 실전계좌가 필요하여 생략합니다.")
        print("실행하려면 example_us_stock_price() 주석을 해제하세요.")
        # example_us_stock_price()

        # 3. 종목 정보 조회
        # example_stock_info()

        # 4. 여러 종목 순차 조회
        # example_multiple_stocks()

        # 5. 에러 처리
        # example_error_handling()

        print("\n" + "="*60)
        print("✅ 모든 예제 실행 완료!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
