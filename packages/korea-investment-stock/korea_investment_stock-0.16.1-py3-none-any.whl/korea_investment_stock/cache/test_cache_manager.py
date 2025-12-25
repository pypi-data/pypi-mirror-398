import pytest
import time
from .cache_manager import CacheManager, CacheEntry


class TestCacheEntry:
    def test_cache_entry_creation(self):
        """캐시 엔트리 생성 테스트"""
        data = {"key": "value"}
        entry = CacheEntry(data, ttl_seconds=5)

        assert entry.data == data
        assert not entry.is_expired()
        assert entry.age_seconds() < 1

    def test_cache_entry_expiration(self):
        """캐시 엔트리 만료 테스트"""
        entry = CacheEntry("test", ttl_seconds=1)
        assert not entry.is_expired()

        time.sleep(1.1)
        assert entry.is_expired()

    def test_cache_entry_age(self):
        """캐시 엔트리 경과 시간 테스트"""
        entry = CacheEntry("test", ttl_seconds=10)
        assert entry.age_seconds() < 0.5

        time.sleep(1)
        age = entry.age_seconds()
        assert 0.9 < age < 1.5


class TestCacheManager:
    def test_cache_set_get(self):
        """캐시 저장 및 조회 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=10)
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """캐시 미스 테스트"""
        cache = CacheManager()
        assert cache.get("nonexistent") is None

    def test_cache_expiration(self):
        """캐시 만료 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=1)
        assert cache.get("key1") == "value1"

        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_invalidation(self):
        """캐시 무효화 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=10)
        cache.set("key2", "value2", ttl_seconds=10)

        cache.invalidate("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_clear(self):
        """전체 캐시 삭제 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=10)
        cache.set("key2", "value2", ttl_seconds=10)
        cache.set("key3", "value3", ttl_seconds=10)

        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

        stats = cache.get_stats()
        assert stats['cache_size'] == 0

    def test_cache_stats(self):
        """캐시 통계 테스트"""
        cache = CacheManager()

        # 첫 번째 miss
        cache.get("key1")

        # 저장
        cache.set("key1", "value1", ttl_seconds=10)

        # 첫 번째 hit
        cache.get("key1")

        # 두 번째 hit
        cache.get("key1")

        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['cache_size'] == 1
        assert "%" in stats['hit_rate']

    def test_cache_info(self):
        """캐시 정보 조회 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=10)

        info = cache.get_cache_info("key1")
        assert info is not None
        assert 'cached_at' in info
        assert 'expires_at' in info
        assert 'age_seconds' in info
        assert 'is_expired' in info
        assert info['is_expired'] is False

    def test_cache_info_nonexistent(self):
        """존재하지 않는 캐시 정보 조회 테스트"""
        cache = CacheManager()
        info = cache.get_cache_info("nonexistent")
        assert info is None

    def test_cache_multiple_keys(self):
        """여러 키 캐시 테스트"""
        cache = CacheManager()
        test_data = {
            "key1": "value1",
            "key2": {"nested": "data"},
            "key3": [1, 2, 3],
            "key4": 123
        }

        for key, value in test_data.items():
            cache.set(key, value, ttl_seconds=10)

        for key, expected_value in test_data.items():
            assert cache.get(key) == expected_value

    def test_cache_stats_hit_rate_calculation(self):
        """히트율 계산 테스트"""
        cache = CacheManager()

        # 5 misses
        for i in range(5):
            cache.get(f"key{i}")

        # 5 sets
        for i in range(5):
            cache.set(f"key{i}", f"value{i}", ttl_seconds=10)

        # 10 hits
        for _ in range(2):
            for i in range(5):
                cache.get(f"key{i}")

        stats = cache.get_stats()
        assert stats['hits'] == 10
        assert stats['misses'] == 5
        # 10 / (10 + 5) = 66.67%
        assert "66.67%" in stats['hit_rate']

    def test_cache_overwrite(self):
        """캐시 덮어쓰기 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=10)
        assert cache.get("key1") == "value1"

        cache.set("key1", "value2", ttl_seconds=10)
        assert cache.get("key1") == "value2"

    def test_cache_expiration_updates_stats(self):
        """만료된 캐시가 통계를 업데이트하는지 테스트"""
        cache = CacheManager()
        cache.set("key1", "value1", ttl_seconds=1)

        time.sleep(1.1)
        result = cache.get("key1")

        assert result is None
        stats = cache.get_stats()
        assert stats['evictions'] == 1
        assert stats['misses'] == 1
