"""Config 클래스 사용 예제

Phase 2 (v1.0.0): Config 클래스를 사용한 설정 관리 예제

다양한 방법으로 Config를 생성하고 관리하는 방법을 보여줍니다:
1. 환경 변수에서 로드
2. YAML 파일에서 로드
3. 직접 생성
4. YAML 파일로 내보내기

사전 준비:
    # 환경 변수 설정 (방법 1 사용시)
    export KOREA_INVESTMENT_API_KEY="your-api-key"
    export KOREA_INVESTMENT_API_SECRET="your-api-secret"
    export KOREA_INVESTMENT_ACCOUNT_NO="12345678-01"

    # 또는 YAML 파일 생성 (방법 2 사용시)
    # ~/.config/kis/config.yaml

실행:
    python examples/config_example.py
"""

import os
from pathlib import Path

from korea_investment_stock import Config


def example_from_env():
    """환경 변수에서 Config 로드 예제"""
    print("=" * 60)
    print("1. 환경 변수에서 Config 로드")
    print("=" * 60)

    try:
        config = Config.from_env()
        print(f"Config 로드 성공!")
        print(f"  API Key: ***{config.api_key[-4:]}")
        print(f"  계좌번호: {config.acc_no}")
        print(f"  토큰 저장소: {config.token_storage_type}")
        print()
        return config
    except KeyError as e:
        print(f"환경 변수 누락: {e}")
        print("다음 환경 변수를 설정하세요:")
        print("  export KOREA_INVESTMENT_API_KEY=...")
        print("  export KOREA_INVESTMENT_API_SECRET=...")
        print("  export KOREA_INVESTMENT_ACCOUNT_NO=...")
        print()
        return None


def example_from_yaml():
    """YAML 파일에서 Config 로드 예제"""
    print("=" * 60)
    print("2. YAML 파일에서 Config 로드")
    print("=" * 60)

    # 샘플 YAML 경로
    config_paths = [
        Path("~/.config/kis/config.yaml").expanduser(),
        Path("./config.yaml"),
        Path("./examples/testdata/sample_config.yaml"),
    ]

    for path in config_paths:
        if path.exists():
            try:
                config = Config.from_yaml(path)
                print(f"Config 로드 성공: {path}")
                print(f"  API Key: ***{config.api_key[-4:]}")
                print(f"  계좌번호: {config.acc_no}")
                print()
                return config
            except Exception as e:
                print(f"로드 실패 ({path}): {e}")

    print("사용 가능한 config 파일을 찾을 수 없습니다.")
    print("다음 위치에 config.yaml 파일을 생성하세요:")
    print("  ~/.config/kis/config.yaml")
    print()
    print("파일 형식:")
    print("""
api_key: your-api-key
api_secret: your-api-secret
acc_no: "12345678-01"
token_storage_type: file
""")
    print()
    return None


def example_direct_creation():
    """직접 Config 생성 예제"""
    print("=" * 60)
    print("3. 직접 Config 생성")
    print("=" * 60)

    # 테스트용 더미 데이터
    config = Config(
        api_key="demo-api-key-12345",
        api_secret="demo-api-secret-67890",
        acc_no="12345678-01",
        token_storage_type="file",
        redis_url="redis://localhost:6379/0"
    )

    print("Config 생성 완료!")
    print(f"  repr(): {repr(config)}")  # 민감 정보 마스킹
    print()

    # 딕셔너리로 변환
    print("딕셔너리 변환:")
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        # 민감 정보 마스킹
        if key in ('api_key', 'api_secret') and value:
            value = f"***{value[-4:]}"
        print(f"  {key}: {value}")
    print()

    return config


def example_export_yaml(config: Config, output_dir: Path):
    """Config를 YAML로 내보내기 예제"""
    print("=" * 60)
    print("4. Config를 YAML 파일로 내보내기")
    print("=" * 60)

    output_file = output_dir / "exported_config.yaml"

    # YAML 문자열 미리보기
    print("YAML 내용 미리보기:")
    yaml_str = config.to_yaml()
    # 민감 정보 마스킹하여 출력
    for line in yaml_str.split('\n'):
        if 'api_key:' in line or 'api_secret:' in line:
            key = line.split(':')[0]
            print(f"  {key}: ***masked***")
        else:
            print(f"  {line}")
    print()

    # 파일로 저장
    config.to_yaml(output_file)
    print(f"파일로 저장됨: {output_file}")
    print()


def example_config_priority():
    """Config 우선순위 설명"""
    print("=" * 60)
    print("5. 설정 우선순위 (Phase 3 예정)")
    print("=" * 60)
    print("""
향후 v1.1.0에서 Hybrid 통합 시 다음 우선순위가 적용됩니다:

1. 생성자 파라미터 (최고 우선순위)
2. config 객체 주입
3. config_file 파라미터
4. 환경 변수
5. 기본 config 파일 (~/.config/kis/config.yaml)

예시:
    # 환경 변수 자동 감지 (현재 v0.9.0)
    broker = KoreaInvestment()

    # config 객체 사용 (v1.1.0 예정)
    config = Config.from_yaml("~/.config/kis/config.yaml")
    broker = KoreaInvestment(config=config)

    # 일부만 override (v1.1.0 예정)
    broker = KoreaInvestment(
        config=config,
        api_key="override-key"  # config보다 우선
    )
""")


def main():
    """모든 예제 실행"""
    print()
    print("=" * 60)
    print("Korea Investment Stock - Config 클래스 예제")
    print("=" * 60)
    print()

    # 1. 환경 변수에서 로드
    env_config = example_from_env()

    # 2. YAML 파일에서 로드
    yaml_config = example_from_yaml()

    # 3. 직접 생성
    direct_config = example_direct_creation()

    # 4. YAML로 내보내기
    output_dir = Path("./examples/testdata")
    output_dir.mkdir(parents=True, exist_ok=True)
    example_export_yaml(direct_config, output_dir)

    # 5. 우선순위 설명
    example_config_priority()

    print("=" * 60)
    print("예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
