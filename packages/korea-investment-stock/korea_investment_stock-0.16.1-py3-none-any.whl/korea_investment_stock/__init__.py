'''
한국투자증권 OpenAPI Python Wrapper

Simple, transparent, and flexible Python wrapper for Korea Investment Securities OpenAPI.
'''

# 메인 클래스
from .korea_investment_stock import KoreaInvestment

# 상수 정의 (API 파라미터명 사용)
from .constants import (
    # 국가 코드
    COUNTRY_CODE,
    # 조건 시장 분류 코드 (FID_COND_MRKT_DIV_CODE)
    FID_COND_MRKT_DIV_CODE_STOCK,
    FID_COND_MRKT_DIV_CODE_BOND,
    FID_COND_MRKT_DIV_CODE_FUTURES,
    FID_COND_MRKT_DIV_CODE_OVERSEAS,
    # 거래소 코드
    EXCG_ID_DVSN_CD,    # 국내 주문용
    EXCD,               # 해외 시세 조회용
    EXCD_BY_COUNTRY,    # 해외 시세 조회용 (국가별 매핑)
    OVRS_EXCG_CD,       # 해외 주문/잔고용
    # 상품유형 코드
    PRDT_TYPE_CD,
    PRDT_TYPE_CD_BY_COUNTRY,  # 국가별 상품유형코드 매핑
    # 시장별 투자자동향 코드
    MARKET_INVESTOR_TREND_CODE,  # 시장 코드 (KSP, KSQ, ETF 등)
    SECTOR_CODE,                  # 업종 코드 (0001, 1001, T000 등)
    # 기타
    API_RETURN_CODE,
)

# 설정 관리
from .config import Config
from .config_resolver import ConfigResolver

# 캐시 기능 (서브패키지)
from .cache import CacheManager, CacheEntry, CachedKoreaInvestment

# 토큰 관리 (서브패키지)
from .token import TokenStorage, FileTokenStorage, RedisTokenStorage, TokenManager, create_token_storage

# Rate Limiting (서브패키지)
from .rate_limit import RateLimiter, RateLimitedKoreaInvestment

# 파서 (서브패키지)
from .parsers import (
    parse_kospi_master,
    parse_kosdaq_master,
    parse_overseas_stock_master,
    OVERSEAS_MARKETS,
    OVERSEAS_COLUMNS,
)

# IPO 헬퍼 (서브패키지)
from .ipo import (
    validate_date_format,
    validate_date_range,
    parse_ipo_date_range,
    format_ipo_date,
    calculate_ipo_d_day,
    get_ipo_status,
    format_number,
)

# Git tag에서 버전 자동 추출 (setuptools-scm)
try:
    from importlib.metadata import version
    __version__ = version("korea-investment-stock")
except Exception:
    # Fallback for development without git tags
    __version__ = "0.0.0.dev0"

__all__ = [
    # 메인 API
    "KoreaInvestment",

    # 상수 정의 - 국가 코드
    "COUNTRY_CODE",
    # 상수 정의 - 시장 분류 코드 (FID_COND_MRKT_DIV_CODE)
    "FID_COND_MRKT_DIV_CODE_STOCK",
    "FID_COND_MRKT_DIV_CODE_BOND",
    "FID_COND_MRKT_DIV_CODE_FUTURES",
    "FID_COND_MRKT_DIV_CODE_OVERSEAS",
    # 상수 정의 - 거래소 코드
    "EXCG_ID_DVSN_CD",
    "EXCD",
    "EXCD_BY_COUNTRY",
    "OVRS_EXCG_CD",
    # 상수 정의 - 상품유형 코드
    "PRDT_TYPE_CD",
    "PRDT_TYPE_CD_BY_COUNTRY",
    # 상수 정의 - 시장별 투자자동향 코드
    "MARKET_INVESTOR_TREND_CODE",
    "SECTOR_CODE",
    # 상수 정의 - 기타
    "API_RETURN_CODE",

    # 설정 관리
    "Config",
    "ConfigResolver",

    # 캐시 기능
    "CacheManager",
    "CacheEntry",
    "CachedKoreaInvestment",

    # 토큰 관리
    "TokenStorage",
    "FileTokenStorage",
    "RedisTokenStorage",
    "TokenManager",
    "create_token_storage",

    # Rate Limiting
    "RateLimiter",
    "RateLimitedKoreaInvestment",

    # 파서
    "parse_kospi_master",
    "parse_kosdaq_master",
    "parse_overseas_stock_master",
    "OVERSEAS_MARKETS",
    "OVERSEAS_COLUMNS",

    # IPO 헬퍼
    "validate_date_format",
    "validate_date_range",
    "parse_ipo_date_range",
    "format_ipo_date",
    "calculate_ipo_d_day",
    "get_ipo_status",
    "format_number",
]
