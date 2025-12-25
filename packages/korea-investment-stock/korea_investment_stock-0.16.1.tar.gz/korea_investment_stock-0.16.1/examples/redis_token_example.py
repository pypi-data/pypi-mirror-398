"""
Redis Token Storage 예제

이 예제는 Korea Investment Stock 라이브러리에서
Redis 기반 토큰 저장소를 사용하는 방법을 보여줍니다.

사전 요구사항:
    pip install korea-investment-stock[redis]
"""

import os
from korea_investment_stock import (
    KoreaInvestment,
    FileTokenStorage,
    RedisTokenStorage
)


def example_1_default_file_storage():
    """예제 1: 기본 파일 저장소 사용 (변경 없음)"""
    print("=" * 60)
    print("예제 1: 기본 파일 저장소 (FileTokenStorage)")
    print("=" * 60)

    api_key = os.getenv("KOREA_INVESTMENT_API_KEY")
    api_secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
    acc_no = os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

    # 환경 변수 설정 없이 사용 시 자동으로 파일 저장소 사용
    # 토큰 위치: ~/.cache/kis/token.key
    with KoreaInvestment(api_key, api_secret, acc_no) as broker:
        print(f"✅ 연결 성공: {broker.access_token[:50]}...")
        print(f"📁 토큰 저장소 타입: {type(broker.token_storage).__name__}")
    print()


def example_2_redis_via_env():
    """예제 2: 환경 변수로 Redis 저장소 사용"""
    print("=" * 60)
    print("예제 2: 환경 변수로 Redis 저장소 설정")
    print("=" * 60)

    # 환경 변수 설정
    os.environ["KOREA_INVESTMENT_TOKEN_STORAGE"] = "redis"
    os.environ["KOREA_INVESTMENT_REDIS_URL"] = "redis://localhost:6379/0"

    api_key = os.getenv("KOREA_INVESTMENT_API_KEY")
    api_secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
    acc_no = os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

    try:
        with KoreaInvestment(api_key, api_secret, acc_no) as broker:
            print(f"✅ 연결 성공: {broker.access_token[:50]}...")
            print(f"📦 토큰 저장소 타입: {type(broker.token_storage).__name__}")

            # Redis 키 확인
            if hasattr(broker.token_storage, '_get_redis_key'):
                redis_key = broker.token_storage._get_redis_key(api_key)
                print(f"🔑 Redis 키: {redis_key}")
    except ConnectionError as e:
        print(f"❌ Redis 연결 실패: {e}")
        print("   Redis 서버가 실행 중인지 확인하세요:")
        print("   docker run -d -p 6379:6379 redis:7-alpine")

    # 환경 변수 정리
    os.environ.pop("KOREA_INVESTMENT_TOKEN_STORAGE", None)
    os.environ.pop("KOREA_INVESTMENT_REDIS_URL", None)
    print()


def example_3_redis_with_password():
    """예제 3: Redis 비밀번호 인증 사용"""
    print("=" * 60)
    print("예제 3: Redis 비밀번호 인증")
    print("=" * 60)

    os.environ["KOREA_INVESTMENT_TOKEN_STORAGE"] = "redis"
    os.environ["KOREA_INVESTMENT_REDIS_URL"] = "redis://redis-server:6379/1"
    os.environ["KOREA_INVESTMENT_REDIS_PASSWORD"] = "your-secure-password"

    api_key = os.getenv("KOREA_INVESTMENT_API_KEY")
    api_secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
    acc_no = os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

    try:
        with KoreaInvestment(api_key, api_secret, acc_no) as broker:
            print(f"✅ 인증된 Redis 연결 성공")
            print(f"📦 토큰 저장소 타입: {type(broker.token_storage).__name__}")
    except ConnectionError as e:
        print(f"❌ Redis 연결 실패: {e}")

    # 환경 변수 정리
    os.environ.pop("KOREA_INVESTMENT_TOKEN_STORAGE", None)
    os.environ.pop("KOREA_INVESTMENT_REDIS_URL", None)
    os.environ.pop("KOREA_INVESTMENT_REDIS_PASSWORD", None)
    print()


def example_4_custom_storage():
    """예제 4: 커스텀 저장소 직접 주입"""
    print("=" * 60)
    print("예제 4: 커스텀 저장소 직접 주입")
    print("=" * 60)

    api_key = os.getenv("KOREA_INVESTMENT_API_KEY")
    api_secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
    acc_no = os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

    # 방법 1: File 저장소를 특정 경로에 생성
    from pathlib import Path
    custom_file_storage = FileTokenStorage(
        file_path=Path("/tmp/my_custom_token.key")
    )

    with KoreaInvestment(api_key, api_secret, acc_no, token_storage=custom_file_storage) as broker:
        print(f"✅ 커스텀 파일 저장소 사용: /tmp/my_custom_token.key")
        print(f"📁 토큰 저장소 타입: {type(broker.token_storage).__name__}")
    print()

    # 방법 2: Redis 저장소를 커스텀 설정으로 생성
    try:
        custom_redis_storage = RedisTokenStorage(
            redis_url="redis://localhost:6379/2",  # DB 2 사용
            key_prefix="my_app:token"  # 커스텀 키 프리픽스
        )

        with KoreaInvestment(api_key, api_secret, acc_no, token_storage=custom_redis_storage) as broker:
            print(f"✅ 커스텀 Redis 저장소 사용 (DB 2)")
            print(f"📦 토큰 저장소 타입: {type(broker.token_storage).__name__}")

            if hasattr(broker.token_storage, '_get_redis_key'):
                redis_key = broker.token_storage._get_redis_key(api_key)
                print(f"🔑 커스텀 Redis 키: {redis_key}")
    except Exception as e:
        print(f"❌ 커스텀 Redis 연결 실패: {e}")
    print()


def example_5_distributed_environment():
    """예제 5: 분산 환경에서 토큰 공유"""
    print("=" * 60)
    print("예제 5: 분산 환경에서 토큰 공유")
    print("=" * 60)

    os.environ["KOREA_INVESTMENT_TOKEN_STORAGE"] = "redis"
    os.environ["KOREA_INVESTMENT_REDIS_URL"] = "redis://localhost:6379/0"

    api_key = os.getenv("KOREA_INVESTMENT_API_KEY")
    api_secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
    acc_no = os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

    try:
        # 서버 1: 토큰 발급 및 저장
        print("🖥️  서버 1: 토큰 발급")
        with KoreaInvestment(api_key, api_secret, acc_no) as broker1:
            token1 = broker1.access_token
            print(f"   토큰 생성: {token1[:50]}...")

        # 서버 2: Redis에서 토큰 로드 (새로 발급하지 않음)
        print("🖥️  서버 2: Redis에서 토큰 로드")
        with KoreaInvestment(api_key, api_secret, acc_no) as broker2:
            token2 = broker2.access_token
            print(f"   토큰 로드: {token2[:50]}...")

        # 같은 토큰 확인
        if token1 == token2:
            print("✅ 성공: 두 서버가 동일한 토큰을 공유합니다!")
        else:
            print("❌ 실패: 토큰이 다릅니다")

    except ConnectionError as e:
        print(f"❌ Redis 연결 실패: {e}")

    # 환경 변수 정리
    os.environ.pop("KOREA_INVESTMENT_TOKEN_STORAGE", None)
    os.environ.pop("KOREA_INVESTMENT_REDIS_URL", None)
    print()


def example_6_migration_from_file_to_redis():
    """예제 6: File 저장소에서 Redis 저장소로 마이그레이션"""
    print("=" * 60)
    print("예제 6: File → Redis 마이그레이션")
    print("=" * 60)

    from pathlib import Path

    api_key = os.getenv("KOREA_INVESTMENT_API_KEY")
    api_secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
    acc_no = os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")

    # 1. 기존 파일 저장소 사용
    file_storage = FileTokenStorage(file_path=Path("/tmp/migration_token.key"))
    print("📁 단계 1: File 저장소에 토큰 저장")
    with KoreaInvestment(api_key, api_secret, acc_no, token_storage=file_storage) as broker:
        print(f"   저장 완료: {broker.access_token[:50]}...")

    try:
        # 2. Redis 저장소로 전환
        redis_storage = RedisTokenStorage("redis://localhost:6379/0")
        print("📦 단계 2: Redis 저장소로 전환")

        # 3. File에서 토큰 로드
        token_data = file_storage.load_token(api_key, api_secret)
        if token_data:
            # 4. Redis에 저장
            redis_storage.save_token(token_data)
            print("   ✅ 마이그레이션 완료!")

            # 5. Redis에서 로드 확인
            loaded_data = redis_storage.load_token(api_key, api_secret)
            if loaded_data:
                print(f"   검증 완료: {loaded_data['access_token'][:50]}...")
        else:
            print("   ❌ File 저장소에서 토큰을 로드할 수 없습니다")

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Korea Investment Stock - Redis Token Storage 예제")
    print("=" * 60 + "\n")

    # 환경 변수 확인
    if not all([
        os.getenv("KOREA_INVESTMENT_API_KEY"),
        os.getenv("KOREA_INVESTMENT_API_SECRET"),
        os.getenv("KOREA_INVESTMENT_ACCOUNT_NO")
    ]):
        print("❌ 오류: 환경 변수를 설정해주세요:")
        print("   export KOREA_INVESTMENT_API_KEY='your-api-key'")
        print("   export KOREA_INVESTMENT_API_SECRET='your-api-secret'")
        print("   export KOREA_INVESTMENT_ACCOUNT_NO='12345678-01'")
        exit(1)

    # 예제 실행
    example_1_default_file_storage()
    example_2_redis_via_env()
    example_3_redis_with_password()
    example_4_custom_storage()
    example_5_distributed_environment()
    example_6_migration_from_file_to_redis()

    print("=" * 60)
    print("모든 예제 완료!")
    print("=" * 60)
