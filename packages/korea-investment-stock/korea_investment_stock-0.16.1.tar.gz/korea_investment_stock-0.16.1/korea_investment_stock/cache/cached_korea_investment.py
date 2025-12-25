from typing import Optional, Dict, Any
from ..korea_investment_stock import KoreaInvestment
from .cache_manager import CacheManager


class CachedKoreaInvestment:
    """캐싱 기능이 추가된 KoreaInvestment 래퍼"""

    DEFAULT_TTL = {
        'price': 5,           # 실시간 가격: 5초
        'stock_info': 300,    # 종목 정보: 5분
        'symbols': 3600,      # 종목 리스트: 1시간
        'ipo': 1800           # IPO 일정: 30분
    }

    def __init__(
        self,
        broker: KoreaInvestment,
        enable_cache: bool = True,
        price_ttl: Optional[int] = None,
        stock_info_ttl: Optional[int] = None,
        symbols_ttl: Optional[int] = None,
        ipo_ttl: Optional[int] = None
    ):
        """
        Args:
            broker: KoreaInvestment 인스턴스
            enable_cache: 캐싱 활성화 여부
            price_ttl: 실시간 가격 TTL (초)
            stock_info_ttl: 종목정보 TTL (초)
            symbols_ttl: 종목리스트 TTL (초)
            ipo_ttl: IPO 일정 TTL (초)
        """
        self.broker = broker
        self.enable_cache = enable_cache
        self.cache = CacheManager() if enable_cache else None

        # TTL 설정
        self.ttl = {
            'price': price_ttl or self.DEFAULT_TTL['price'],
            'stock_info': stock_info_ttl or self.DEFAULT_TTL['stock_info'],
            'symbols': symbols_ttl or self.DEFAULT_TTL['symbols'],
            'ipo': ipo_ttl or self.DEFAULT_TTL['ipo']
        }

    def _make_cache_key(self, method: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        args_str = "_".join(str(arg) for arg in args)
        kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{method}:{args_str}:{kwargs_str}"

    def fetch_price(self, symbol: str, country_code: str = "KR") -> dict:
        """가격 조회 (캐싱 지원)"""
        if not self.enable_cache:
            return self.broker.fetch_price(symbol, country_code)

        cache_key = self._make_cache_key("fetch_price", symbol, country_code)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_price(symbol, country_code)

        if result.get('rt_cd') == '0':
            self.cache.set(cache_key, result, self.ttl['price'])

        return result

    def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> dict:
        """국내 주식/ETF 가격 조회 (캐싱 지원)"""
        if not self.enable_cache:
            return self.broker.fetch_domestic_price(symbol, symbol_type)

        cache_key = self._make_cache_key("fetch_domestic_price", symbol, symbol_type)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_domestic_price(symbol, symbol_type)

        if result.get('rt_cd') == '0':
            self.cache.set(cache_key, result, self.ttl['price'])

        return result

    def fetch_price_detail_oversea(self, symbol: str, country_code: str = "US") -> dict:
        """해외 주식 가격 조회 (캐싱 지원)"""
        if not self.enable_cache:
            return self.broker.fetch_price_detail_oversea(symbol, country_code)

        cache_key = self._make_cache_key("fetch_price_detail_oversea", symbol, country_code)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_price_detail_oversea(symbol, country_code)

        if result.get('rt_cd') == '0':
            self.cache.set(cache_key, result, self.ttl['price'])

        return result

    def fetch_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
        """종목 정보 조회 (캐싱 지원)"""
        if not self.enable_cache:
            return self.broker.fetch_stock_info(symbol, country_code)

        cache_key = self._make_cache_key("fetch_stock_info", symbol, country_code)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_stock_info(symbol, country_code)

        if result.get('rt_cd') == '0':
            self.cache.set(cache_key, result, self.ttl['stock_info'])

        return result

    def fetch_search_stock_info(self, symbol: str, country_code: str = "KR") -> dict:
        """종목 검색 (캐싱 지원) - 국내주식 전용 (KR만 지원)"""
        if not self.enable_cache:
            return self.broker.fetch_search_stock_info(symbol, country_code)

        cache_key = self._make_cache_key("fetch_search_stock_info", symbol, country_code)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_search_stock_info(symbol, country_code)

        if result.get('rt_cd') == '0':
            self.cache.set(cache_key, result, self.ttl['stock_info'])

        return result

    def fetch_ipo_schedule(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        symbol: str = ""
    ) -> dict:
        """IPO 일정 조회 (캐싱 지원)"""
        if not self.enable_cache:
            return self.broker.fetch_ipo_schedule(from_date, to_date, symbol)

        cache_key = self._make_cache_key("fetch_ipo_schedule", from_date, to_date, symbol)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_ipo_schedule(from_date, to_date, symbol)

        if result.get('rt_cd') == '0':
            self.cache.set(cache_key, result, self.ttl['ipo'])

        return result

    def fetch_investor_trading_by_stock_daily(
        self,
        symbol: str,
        date: str,
        market_code: str = "J"
    ) -> dict:
        """투자자 매매동향 조회 (캐싱 지원)

        과거 날짜 데이터는 1시간 캐시, 당일 데이터는 가격 TTL 적용
        """
        if not self.enable_cache:
            return self.broker.fetch_investor_trading_by_stock_daily(symbol, date, market_code)

        cache_key = self._make_cache_key("fetch_investor_trading_by_stock_daily", symbol, date, market_code)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        result = self.broker.fetch_investor_trading_by_stock_daily(symbol, date, market_code)

        if result.get('rt_cd') == '0':
            # 과거 데이터는 더 긴 TTL 적용 (1시간)
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            ttl = 3600 if date < today else self.ttl['price']
            self.cache.set(cache_key, result, ttl)

        return result

    def invalidate_cache(self, method: Optional[str] = None):
        """캐시 무효화"""
        if not self.enable_cache:
            return

        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        if not self.enable_cache:
            return {'cache_enabled': False}

        stats = self.cache.get_stats()
        stats['cache_enabled'] = True
        stats['ttl_config'] = self.ttl
        return stats

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        if self.enable_cache:
            self.cache.clear()
        return False
