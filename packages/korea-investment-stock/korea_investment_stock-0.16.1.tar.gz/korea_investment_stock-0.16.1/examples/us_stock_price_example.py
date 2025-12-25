#!/usr/bin/env python3
"""
미국 주식 현재가 조회 예제
TODO-33 Phase 3.2

이 예제는 한국투자증권 OpenAPI를 사용하여 미국 주식 정보를 조회하는 방법을 보여줍니다.
주의: 미국 주식은 모의투자를 지원하지 않습니다. 실전 계정이 필요합니다.
"""
import os
import sys

# 출력 버퍼링 비활성화
os.environ['PYTHONUNBUFFERED'] = '1'

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from korea_investment_stock import KoreaInvestment


def example_basic_us_stock():
    """기본 미국 주식 조회 예제"""
    print("=" * 60)
    print("1. 기본 미국 주식 조회")
    print("=" * 60)
    sys.stdout.flush()
    
    # API 인증 정보 (환경 변수 또는 직접 입력)
    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')
    
    if not all([api_key, api_secret, acc_no]):
        print("❌ API 인증 정보가 없습니다. 환경 변수를 확인하세요.")
        print(f"  KOREA_INVESTMENT_API_KEY: {'설정됨' if api_key else '없음'}")
        print(f"  KOREA_INVESTMENT_API_SECRET: {'설정됨' if api_secret else '없음'}")
        print(f"  KOREA_INVESTMENT_ACCOUNT_NO: {'설정됨' if acc_no else '없음'}")
        print("\n환경 변수 설정 방법:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='12345678-01'")
        sys.stdout.flush()
        sys.exit(1)
    
    print("✅ API 인증 정보 확인 완료")
    sys.stdout.flush()
    
    # KoreaInvestment 객체 생성
    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        print("📡 AAPL 주식 정보 조회 중...")
        sys.stdout.flush()

        # 단일 미국 주식 조회
        result = broker.fetch_price("AAPL", "US")

        if result['rt_cd'] == '0':
            output = result['output']
            print(f"\n📈 AAPL (애플) 현재가 정보:")
            print(f"  현재가: ${output['last']}")
            print(f"  시가: ${output['open']}")
            print(f"  고가: ${output['high']}")
            print(f"  저가: ${output['low']}")
            print(f"  거래량: {int(output['tvol']):,}")
            print(f"  전일대비: {output['t_xdif']} ({output['t_xrat']}%)")
            print(f"  시가총액: ${float(output['tomv']):,.0f}")
            print(f"  상장주수: {int(output['shar']):,}")
            sys.stdout.flush()
        else:
            print(f"❌ 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
            sys.stdout.flush()


def example_multiple_us_stocks():
    """여러 미국 주식 동시 조회"""
    print("\n" + "=" * 60)
    print("2. 여러 미국 주식 동시 조회")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("❌ API 인증 정보가 없습니다. 환경 변수를 확인하세요.")
        print(f"  KOREA_INVESTMENT_API_KEY: {'설정됨' if api_key else '없음'}")
        print(f"  KOREA_INVESTMENT_API_SECRET: {'설정됨' if api_secret else '없음'}")
        print(f"  KOREA_INVESTMENT_ACCOUNT_NO: {'설정됨' if acc_no else '없음'}")
        print("\n환경 변수 설정 방법:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='12345678-01'")
        sys.exit(1)

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 여러 미국 주식 리스트
        us_stocks = [
            ("AAPL", "US"),    # 애플
            ("MSFT", "US"),    # 마이크로소프트
            ("GOOGL", "US"),   # 구글
            ("AMZN", "US"),    # 아마존
            ("TSLA", "US"),    # 테슬라
            ("NVDA", "US"),    # 엔비디아
        ]

        # 순차 조회
        results = []
        for symbol, market in us_stocks:
            result = broker.fetch_price(symbol, market)
            results.append(result)

        print("\n📊 미국 주요 기술주 현재가:")
        print("-" * 50)

        for (symbol, _), result in zip(us_stocks, results):
            if result['rt_cd'] == '0':
                output = result['output']
                print(f"\n{symbol}:")
                print(f"  현재가: ${output['last']}")
                print(f"  전일대비: {output['t_xdif']} ({output['t_xrat']}%)")
                print(f"  PER: {output['perx']}")
                print(f"  PBR: {output['pbrx']}")
            else:
                print(f"\n{symbol}: ❌ 조회 실패")


def example_mixed_kr_us_stocks():
    """국내/미국 주식 혼합 조회"""
    print("\n" + "=" * 60)
    print("3. 국내/미국 주식 혼합 조회")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("❌ API 인증 정보가 없습니다. 환경 변수를 확인하세요.")
        print(f"  KOREA_INVESTMENT_API_KEY: {'설정됨' if api_key else '없음'}")
        print(f"  KOREA_INVESTMENT_API_SECRET: {'설정됨' if api_secret else '없음'}")
        print(f"  KOREA_INVESTMENT_ACCOUNT_NO: {'설정됨' if acc_no else '없음'}")
        print("\n환경 변수 설정 방법:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='12345678-01'")
        sys.exit(1)

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 국내/미국 혼합 포트폴리오
        mixed_portfolio = [
            ("005930", "KR"),  # 삼성전자
            ("AAPL", "US"),    # 애플
            ("035720", "KR"),  # 카카오
            ("MSFT", "US"),    # 마이크로소프트
            ("000660", "KR"),  # SK하이닉스
            ("NVDA", "US"),    # 엔비디아
        ]

        # 순차 조회
        results = []
        for symbol, market in mixed_portfolio:
            result = broker.fetch_price(symbol, market)
            results.append(result)

        print("\n📈 글로벌 포트폴리오 현재가:")
        print("-" * 60)

        for (symbol, market), result in zip(mixed_portfolio, results):
            if result['rt_cd'] == '0':
                if market == "KR":
                    # 국내 주식
                    output = result.get('output', result.get('output1', {}))
                    price = output.get('stck_prpr', 'N/A')
                    change = output.get('prdy_vrss', 'N/A')
                    rate = output.get('prdy_ctrt', 'N/A')
                    # 가격을 int로 변환하여 포맷팅
                    if price != 'N/A':
                        print(f"{symbol} (KR): ₩{int(price):,} ({change}, {rate}%)")
                    else:
                        print(f"{symbol} (KR): 가격 정보 없음")
                else:
                    # 미국 주식
                    output = result['output']
                    price = output.get('last', 'N/A')
                    change = output.get('t_xdif', 'N/A')
                    rate = output.get('t_xrat', 'N/A')
                    print(f"{symbol} (US): ${price} ({change}, {rate}%)")
            else:
                print(f"{symbol} ({market}): ❌ 조회 실패")


def example_us_stock_details():
    """미국 주식 상세 정보 조회"""
    print("\n" + "=" * 60)
    print("4. 미국 주식 상세 재무 정보")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("❌ API 인증 정보가 없습니다. 환경 변수를 확인하세요.")
        print(f"  KOREA_INVESTMENT_API_KEY: {'설정됨' if api_key else '없음'}")
        print(f"  KOREA_INVESTMENT_API_SECRET: {'설정됨' if api_secret else '없음'}")
        print(f"  KOREA_INVESTMENT_ACCOUNT_NO: {'설정됨' if acc_no else '없음'}")
        print("\n환경 변수 설정 방법:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='12345678-01'")
        sys.exit(1)

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 애플 상세 정보
        result = broker.fetch_price("AAPL", "US")

        if result['rt_cd'] == '0':
            output = result['output']
            
            print(f"\n📊 AAPL 상세 재무 정보:")
            print("-" * 40)
            print(f"현재가: ${output['last']}")
            print(f"시가총액 (API): ${float(output.get('tomv', 0)):,.0f}")
            # 시가총액 계산 방식 (상장주수 × 현재가)
            market_cap_calculated = float(output.get('shar', 0)) * float(output['last'])
            print(f"시가총액 (계산): ${market_cap_calculated:,.0f}")
            print(f"상장주수: {int(output.get('shar', 0)):,}")
            print(f"52주 최고: ${output['h52p']} ({output['h52d']})")
            print(f"52주 최저: ${output['l52p']} ({output['l52d']})")
            print(f"\n재무 지표:")
            print(f"  PER: {output['perx']}")
            print(f"  PBR: {output['pbrx']}")
            print(f"  EPS: ${output['epsx']}")
            print(f"  BPS: ${output['bpsx']}")
            print(f"\n거래 정보:")
            print(f"  거래량: {int(output['tvol']):,}")
            print(f"  전일 거래량: {int(output['pvol']):,}")
            print(f"  매매단위: {output['vnit']}")
            print(f"  호가단위: ${output['e_hogau']}")
            print(f"  섹터: {output.get('e_icod', 'N/A')}")
        else:
            print(f"❌ 조회 실패: {result.get('msg1', '알 수 없는 오류')}")


def example_error_handling():
    """에러 처리 예제"""
    print("\n" + "=" * 60)
    print("5. 에러 처리 예제")
    print("=" * 60)

    api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
    api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
    acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

    if not all([api_key, api_secret, acc_no]):
        print("❌ API 인증 정보가 없습니다. 환경 변수를 확인하세요.")
        print(f"  KOREA_INVESTMENT_API_KEY: {'설정됨' if api_key else '없음'}")
        print(f"  KOREA_INVESTMENT_API_SECRET: {'설정됨' if api_secret else '없음'}")
        print(f"  KOREA_INVESTMENT_ACCOUNT_NO: {'설정됨' if acc_no else '없음'}")
        print("\n환경 변수 설정 방법:")
        print("  export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("  export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO='12345678-01'")
        sys.exit(1)

    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        # 잘못된 심볼들
        test_symbols = [
            ("INVALID", "US"),     # 존재하지 않는 심볼
            ("AAPL", "WRONG"),     # 잘못된 market
            ("BRK.A", "US"),       # 특수 문자 포함
        ]
        
        for symbol, market in test_symbols:
            try:
                print(f"\n테스트: {symbol} ({market})")
                result = broker.fetch_price(symbol, market)

                if result and result['rt_cd'] == '0':
                    print(f"✅ 성공: ${result['output']['last']}")
                else:
                    error_msg = result.get('msg1', '알 수 없는 오류') if result else "No result"
                    print(f"❌ API 오류: {error_msg}")
                    
            except ValueError as e:
                print(f"❌ ValueError: {e}")
            except Exception as e:
                print(f"❌ 예외 발생: {type(e).__name__}: {e}")


def main():
    """메인 함수"""
    print("🚀 한국투자증권 OpenAPI - 미국 주식 조회 예제")
    print("=" * 60)
    print("주의: 미국 주식은 모의투자를 지원하지 않습니다.")
    print("실전 계정이 필요합니다.")
    print("=" * 60)
    
    try:
        # 1. 기본 미국 주식 조회
        example_basic_us_stock()
        
        # 2. 여러 미국 주식 동시 조회
        example_multiple_us_stocks()
        
        # 3. 국내/미국 혼합 조회
        example_mixed_kr_us_stocks()
        
        # 4. 미국 주식 상세 정보
        example_us_stock_details()
        
        # 5. 에러 처리
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 모든 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 