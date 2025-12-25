# Master 파일 캐싱 구현 가이드

> PRD: `3_master_prd.md` 기반 구현 문서

## 1. 개요

### 목표
`fetch_kospi_symbols()`, `fetch_kosdaq_symbols()` 메서드에서 ZIP 파일이 이미 존재하면 다운로드를 스킵하는 캐싱 기능 구현

### 설계 결정
- **옵션 A 선택**: 기존 메서드 수정 (래퍼 클래스 없음)
- **TTL**: 1주일 (168시간)
- **캐시 위치**: 현재 디렉토리 (`os.getcwd()`)

## 2. 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `korea_investment_stock/korea_investment_stock.py` | 핵심 캐싱 로직 |
| `korea_investment_stock/tests/test_master_cache.py` | 단위 테스트 (신규) |
| `CLAUDE.md` | 문서화 |

## 3. 구현 상세

### 3.1 클래스 상수 추가

```python
class KoreaInvestment:
    # 기본 캐시 TTL (시간) - 1주일
    DEFAULT_MASTER_TTL_HOURS = 168
```

**위치**: 클래스 정의 시작 부분 (라인 166 근처)

### 3.2 `_should_download()` 메서드 추가

```python
def _should_download(
    self,
    file_path: Path,
    ttl_hours: int,
    force: bool
) -> bool:
    """다운로드 필요 여부 판단

    Args:
        file_path: ZIP 파일 경로
        ttl_hours: 캐시 유효 시간
        force: 강제 다운로드 여부

    Returns:
        bool: True=다운로드 필요, False=캐시 사용
    """
    if force:
        return True

    if not file_path.exists():
        return True

    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    age = datetime.now() - mtime

    if age.total_seconds() > ttl_hours * 3600:
        logger.debug(f"캐시 만료: {file_path} (age={age})")
        return True

    return False
```

**위치**: `download_master_file()` 메서드 앞

### 3.3 `download_master_file()` 메서드 수정

**기존 코드** (라인 748-770):
```python
def download_master_file(self, base_dir: str, file_name: str, url: str):
    os.chdir(base_dir)
    if os.path.exists(file_name):
        os.remove(file_name)
    resp = requests.get(url)
    with open(file_name, "wb") as f:
        f.write(resp.content)
    kospi_zip = zipfile.ZipFile(file_name)
    kospi_zip.extractall()
    kospi_zip.close()
```

**수정 코드**:
```python
def download_master_file(
    self,
    base_dir: str,
    file_name: str,
    url: str,
    ttl_hours: int = 168,
    force_download: bool = False
) -> bool:
    """master 파일 다운로드 (캐싱 지원)

    Args:
        base_dir: 저장 디렉토리
        file_name: 파일명 (예: "kospi_code.mst.zip")
        url: 다운로드 URL
        ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
        force_download: 강제 다운로드 여부

    Returns:
        bool: True=다운로드됨, False=캐시 사용
    """
    zip_path = Path(base_dir) / file_name

    # 다운로드 필요 여부 확인
    if not self._should_download(zip_path, ttl_hours, force_download):
        mtime = datetime.fromtimestamp(zip_path.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        logger.info(f"캐시 사용: {zip_path} (age: {age_hours:.1f}h, ttl: {ttl_hours}h)")
        return False

    # 다운로드
    logger.info(f"다운로드 중: {url} -> {zip_path}")
    resp = requests.get(url)
    resp.raise_for_status()

    with open(zip_path, "wb") as f:
        f.write(resp.content)

    # 압축 해제
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(base_dir)

    return True
```

**핵심 변경 사항**:
1. `ttl_hours`, `force_download` 파라미터 추가
2. `os.chdir()` 제거 - 절대 경로 사용
3. 파일 존재 시 삭제 로직 제거 → TTL 체크로 변경
4. `with` 문으로 ZipFile 처리
5. 캐시 히트 시 로그 출력

### 3.4 `fetch_kospi_symbols()` 메서드 수정

**기존 코드** (라인 686-714):
```python
def fetch_kospi_symbols(self):
    base_dir = os.getcwd()
    file_name = "kospi_code.mst.zip"
    url = "https://new.real.download.dws.co.kr/common/master/" + file_name
    self.download_master_file(base_dir, file_name, url)
    df = self.parse_kospi_master(base_dir)
    return df
```

**수정 코드**:
```python
def fetch_kospi_symbols(
    self,
    ttl_hours: int = 168,
    force_download: bool = False
) -> pd.DataFrame:
    """코스피 종목 코드

    Args:
        ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
        force_download: 강제 다운로드 여부

    Returns:
        DataFrame: 코스피 종목 정보
    """
    base_dir = os.getcwd()
    file_name = "kospi_code.mst.zip"
    url = "https://new.real.download.dws.co.kr/common/master/" + file_name

    self.download_master_file(base_dir, file_name, url, ttl_hours, force_download)
    df = self.parse_kospi_master(base_dir)
    return df
```

### 3.5 `fetch_kosdaq_symbols()` 메서드 수정

동일한 패턴으로 수정:

```python
def fetch_kosdaq_symbols(
    self,
    ttl_hours: int = 168,
    force_download: bool = False
) -> pd.DataFrame:
    """코스닥 종목 코드

    Args:
        ttl_hours: 캐시 유효 시간 (기본 1주일 = 168시간)
        force_download: 강제 다운로드 여부

    Returns:
        DataFrame: 코스닥 종목 정보
    """
    base_dir = os.getcwd()
    file_name = "kosdaq_code.mst.zip"
    url = "https://new.real.download.dws.co.kr/common/master/" + file_name

    self.download_master_file(base_dir, file_name, url, ttl_hours, force_download)
    df = self.parse_kosdaq_master(base_dir)
    return df
```

## 4. 테스트 구현

### 4.1 단위 테스트 파일 생성

**파일**: `korea_investment_stock/tests/test_master_cache.py`

```python
"""Master 파일 캐싱 테스트"""
import os
import time
from pathlib import Path

import pytest


class TestShouldDownload:
    """_should_download() 메서드 테스트"""

    def test_file_not_exists(self, broker, tmp_path):
        """파일 없을 때 다운로드 필요"""
        file_path = tmp_path / "nonexistent.zip"
        assert broker._should_download(file_path, 168, False) is True

    def test_file_fresh(self, broker, tmp_path):
        """파일이 신선할 때 다운로드 불필요"""
        file_path = tmp_path / "fresh.zip"
        file_path.touch()
        assert broker._should_download(file_path, 168, False) is False

    def test_file_stale(self, broker, tmp_path):
        """파일이 오래됐을 때 다운로드 필요 (1주일 초과)"""
        file_path = tmp_path / "stale.zip"
        file_path.touch()
        old_time = time.time() - (169 * 3600)  # 1주일 + 1시간
        os.utime(file_path, (old_time, old_time))
        assert broker._should_download(file_path, 168, False) is True

    def test_force_download(self, broker, tmp_path):
        """강제 다운로드 시 항상 True"""
        file_path = tmp_path / "forced.zip"
        file_path.touch()
        assert broker._should_download(file_path, 168, True) is True

    def test_custom_ttl(self, broker, tmp_path):
        """커스텀 TTL 테스트"""
        file_path = tmp_path / "custom.zip"
        file_path.touch()
        old_time = time.time() - (2 * 3600)  # 2시간 전
        os.utime(file_path, (old_time, old_time))

        # 1시간 TTL → 다운로드 필요
        assert broker._should_download(file_path, 1, False) is True
        # 24시간 TTL → 캐시 사용
        assert broker._should_download(file_path, 24, False) is False
```

### 4.2 conftest.py에 fixture 추가 (필요 시)

```python
@pytest.fixture
def broker():
    """테스트용 broker fixture"""
    # Mock 또는 실제 broker 인스턴스
    return KoreaInvestment(api_key, api_secret, acc_no)
```

## 5. CLAUDE.md 문서화

### 추가할 섹션

```markdown
## Master 파일 캐싱

**NEW**: `fetch_kospi_symbols()`, `fetch_kosdaq_symbols()` 메서드에 캐싱 기능 추가.

### 기본 동작

```python
# 기존 코드 그대로 동작 (캐싱 자동 적용, 1주일 유효)
df = broker.fetch_kospi_symbols()
```

### TTL 조정

```python
# 1일마다 갱신
df = broker.fetch_kospi_symbols(ttl_hours=24)
```

### 강제 다운로드

```python
# 캐시 무시
df = broker.fetch_kospi_symbols(force_download=True)
```

### 캐시 로그 확인

```python
import logging
logging.basicConfig(level=logging.INFO)

df = broker.fetch_kospi_symbols()
# 로그: INFO - 캐시 사용: /path/kospi_code.mst.zip (age: 0.5h, ttl: 168h)
```
```

## 6. 검증 방법

### 수동 테스트

```python
import time
import os
import logging

logging.basicConfig(level=logging.INFO)

broker = KoreaInvestment(api_key, api_secret, acc_no)

# 캐시 삭제
for f in ["kospi_code.mst.zip", "kospi_code.mst"]:
    if os.path.exists(f):
        os.remove(f)

# 1. 첫 호출 - 다운로드
start = time.time()
df1 = broker.fetch_kospi_symbols()
print(f"첫 호출: {time.time() - start:.2f}초")

# 2. 두 번째 호출 - 캐시
start = time.time()
df2 = broker.fetch_kospi_symbols()
print(f"두번째 호출: {time.time() - start:.2f}초")

# 3. 강제 다운로드
start = time.time()
df3 = broker.fetch_kospi_symbols(force_download=True)
print(f"강제 다운로드: {time.time() - start:.2f}초")
```

### 예상 출력

```
INFO - 다운로드 중: https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip -> /path/kospi_code.mst.zip
첫 호출: 2.50초
INFO - 캐시 사용: /path/kospi_code.mst.zip (age: 0.0h, ttl: 168h)
두번째 호출: 0.10초
INFO - 다운로드 중: https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip -> /path/kospi_code.mst.zip
강제 다운로드: 2.30초
```
