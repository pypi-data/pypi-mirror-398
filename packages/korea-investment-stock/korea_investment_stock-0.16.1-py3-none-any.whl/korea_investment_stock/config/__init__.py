"""Config 모듈

설정 관리를 위한 Config 클래스를 제공합니다.

사용 예시:
    # 환경 변수에서 로드
    from korea_investment_stock.config import Config
    config = Config.from_env()

    # YAML 파일에서 로드
    config = Config.from_yaml("~/.config/kis/config.yaml")

    # 직접 생성
    config = Config(
        api_key="your-api-key",
        api_secret="your-api-secret",
        acc_no="12345678-01"
    )
"""

from .config import Config

__all__ = ["Config"]
