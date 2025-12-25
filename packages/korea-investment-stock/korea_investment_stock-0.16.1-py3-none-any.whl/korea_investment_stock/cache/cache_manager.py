from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading


class CacheEntry:
    """캐시 엔트리"""

    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.cached_at = datetime.now()
        self.expires_at = self.cached_at + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        return datetime.now() > self.expires_at

    def age_seconds(self) -> float:
        """캐시 생성 후 경과 시간 (초)"""
        return (datetime.now() - self.cached_at).total_seconds()


class CacheManager:
    """메모리 기반 캐시 매니저 (Thread-safe)"""

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats['misses'] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats['evictions'] += 1
                self._stats['misses'] += 1
                return None

            self._stats['hits'] += 1
            return entry.data

    def set(self, key: str, data: Any, ttl_seconds: int):
        """캐시에 데이터 저장"""
        with self._lock:
            self._cache[key] = CacheEntry(data, ttl_seconds)

    def invalidate(self, key: str):
        """특정 캐시 무효화"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['evictions'] += 1

    def clear(self):
        """전체 캐시 삭제"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats['evictions'] += count

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100
                       if total_requests > 0 else 0)

            return {
                'cache_size': len(self._cache),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'hit_rate': f"{hit_rate:.2f}%"
            }

    def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """특정 캐시 엔트리 정보 반환"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            return {
                'cached_at': entry.cached_at.isoformat(),
                'expires_at': entry.expires_at.isoformat(),
                'age_seconds': entry.age_seconds(),
                'is_expired': entry.is_expired()
            }
