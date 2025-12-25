# Master 파일 캐싱 기능 PRD

> **종목 코드 Master 파일**의 불필요한 재다운로드를 방지하는 캐싱 기능 PRD

## Quick Start

```python
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)

# 기존 방식 (매번 다운로드)
df = broker.fetch_kospi_symbols()  # 항상 새로 다운로드

# 개선 후 (캐시 사용)
df = broker.fetch_kospi_symbols()  # 캐시에 있으면 다운로드 스킵 (1주일 유효)
df = broker.fetch_kospi_symbols(force_download=True)  # 강제 다운로드
```

**효과**:
- 불필요한 네트워크 요청 제거
- 실행 시간 단축 (캐시 히트 시 ~0.1초 vs 다운로드 ~2-5초)
- 한국투자증권 서버 부하 감소

## 목차

1. [문제 정의](#1-문제-정의)
2. [솔루션 요구사항](#2-솔루션-요구사항)
3. [현재 코드 분석](#3-현재-코드-분석)
4. [설계 옵션](#4-설계-옵션)
5. [기술 아키텍처](#5-기술-아키텍처)
6. [사용 예제](#6-사용-예제)
7. [마이그레이션 가이드](#7-마이그레이션-가이드)
8. [위험 및 완화 방안](#8-위험-및-완화-방안)
9. [성공 지표](#9-성공-지표)

> **구현 상세**: `3_master_implementation.md` 참조
> **체크리스트**: `3_master_todo.md` 참조

---

## 1. 문제 정의

### 현재 문제점

`fetch_kospi_symbols()` 및 `fetch_kosdaq_symbols()` 메서드가 호출될 때마다 **매번 ZIP 파일을 다운로드**합니다. 이로 인해:

1. **불필요한 네트워크 요청**: Master 파일은 하루에 한 번 업데이트되므로 같은 날 여러 번 다운로드할 필요 없음
2. **실행 시간 증가**: 다운로드 시간 (~2-5초)이 매번 소요
3. **서버 부하**: 한국투자증권 서버에 불필요한 요청 발생
4. **파일 관리 문제**: 현재 디렉토리(`os.getcwd()`)에 파일 생성으로 디렉토리 오염

### 영향받는 메서드

| 메서드 | 파일명 | 설명 |
|--------|--------|------|
| `fetch_kospi_symbols()` | `kospi_code.mst.zip` | KOSPI 종목 코드 |
| `fetch_kosdaq_symbols()` | `kosdaq_code.mst.zip` | KOSDAQ 종목 코드 |
| `fetch_symbols()` | 위 두 파일 모두 | KR 시장 전체 종목 |

### 사용자 요구사항

> "fetch_symbols() 할때마다 매번 다운로드 하는 대신 zip 파일이 이미 존재를 하면 다시 다운로드하지 않도록 변경을 하고 싶다."

## 2. 솔루션 요구사항

### 2.1 핵심 요구사항

#### 기능적 요구사항

1. **파일 존재 확인**: ZIP 파일이 이미 존재하면 다운로드 스킵
2. **TTL 기반 갱신**: 파일이 일정 시간(기본 1주일) 이상 오래된 경우 재다운로드
3. **강제 다운로드 옵션**: `force_download=True` 파라미터로 강제 갱신 가능
4. **현재 디렉토리 사용**: 기존과 동일하게 `os.getcwd()` 사용 (호환성 유지)
5. **캐시 히트 로깅**: ZIP 파일이 존재하여 스킵할 때 로그 출력 (디버깅용)
6. **하위 호환성**: 기존 API 시그니처 변경 없음

#### 비기능적 요구사항

1. **철학 준수**: 단순하고, 투명하며, 유연함
2. **의존성 없음**: 외부 라이브러리 사용하지 않음
3. **스레드 안전**: 멀티스레드 환경에서도 안전하게 동작
4. **플랫폼 호환**: Windows, macOS, Linux 지원

### 2.2 성공 기준

✅ **주요 성공 지표**:
- 같은 날 두 번째 호출부터 다운로드 스킵
- 캐시 히트 시 실행 시간 90% 이상 단축
- 기존 테스트 모두 통과

## 3. 현재 코드 분석

### 3.1 `download_master_file()` 메서드 (라인 748-770)

```python
def download_master_file(self, base_dir: str, file_name: str, url: str):
    """download master file"""
    os.chdir(base_dir)

    # delete legacy master file (문제: 항상 삭제!)
    if os.path.exists(file_name):
        os.remove(file_name)

    # download master file (문제: 항상 다운로드!)
    resp = requests.get(url)
    with open(file_name, "wb") as f:
        f.write(resp.content)

    # unzip
    kospi_zip = zipfile.ZipFile(file_name)
    kospi_zip.extractall()
    kospi_zip.close()
```

**문제점**:
1. 라인 759-760: 파일이 존재하면 **무조건 삭제**
2. 라인 763-765: **항상 새로 다운로드**
3. `os.chdir()` 사용으로 작업 디렉토리 변경 (사이드 이펙트)
4. ZIP 파일 열고 닫기에 `with` 문 미사용

### 3.2 문제 요약

| 문제 | 현재 동작 | 개선 방향 |
|------|----------|----------|
| ZIP 파일 존재 시 | 삭제 후 재다운로드 | 존재하면 스킵 (TTL 체크) |
| 캐시 위치 | `os.getcwd()` | `os.getcwd()` (동일) |
| 파일 유효기간 | 없음 | 1주일 TTL |
| 강제 갱신 | 불가능 | `force_download` 파라미터 |
| 작업 디렉토리 변경 | `os.chdir()` 사용 | `os.chdir()` 제거 |

## 4. 설계 옵션

### 옵션 A: 기존 메서드 수정 ✅ 선택됨

기존 `download_master_file()` 메서드를 수정하여 캐싱 로직 추가.

**장점**:
- ✅ 기존 구조 유지
- ✅ 최소한의 코드 변경
- ✅ 하위 호환성 100%
- ✅ 래퍼 클래스 불필요 (단순함)

**단점**:
- 없음 (기존 파라미터 유지)

**결정**: **선택됨** - 프로젝트 철학(단순, 투명, 유연)에 가장 부합

### 옵션 B: 별도 캐시 관리 클래스 ❌ 기각

새로운 `MasterFileCache` 클래스 생성.

**단점**:
- ❌ 추가 클래스로 복잡도 증가
- ❌ 철학("단순함") 위반

### 옵션 C: 래퍼 클래스 패턴 ❌ 기각

`CachedKoreaInvestment`처럼 별도 래퍼 생성.

**단점**:
- ❌ 단순 캐싱에 과도한 구조
- ❌ 사용자가 별도로 래퍼 적용해야 함

## 5. 기술 아키텍처

### 5.1 캐시 파일 구조

현재 디렉토리(`os.getcwd()`)에 파일 저장 (기존과 동일):

```
{current_working_directory}/
├── kospi_code.mst.zip       # KOSPI master ZIP (캐시)
├── kospi_code.mst           # 압축 해제된 파일
├── kosdaq_code.mst.zip      # KOSDAQ master ZIP (캐시)
└── kosdaq_code.mst          # 압축 해제된 파일
```

### 5.2 캐싱 알고리즘

```
다운로드 필요 여부 판단:
1. force=True → 다운로드
2. 파일 없음 → 다운로드
3. TTL 초과 (1주일) → 다운로드
4. 그 외 → 캐시 사용
```

### 5.3 API 변경 사항

| 메서드 | 새 파라미터 | 기본값 |
|--------|------------|--------|
| `fetch_kospi_symbols()` | `ttl_hours`, `force_download` | 168, False |
| `fetch_kosdaq_symbols()` | `ttl_hours`, `force_download` | 168, False |
| `download_master_file()` | `ttl_hours`, `force_download` | 168, False |

### 5.4 로그 출력

```
# 다운로드 시
INFO - 다운로드 중: {url} -> {zip_path}

# 캐시 사용 시
INFO - 캐시 사용: {zip_path} (age: {age}h, ttl: {ttl}h)
```

## 6. 사용 예제

### 6.1 기본 사용법 (변경 없음)

```python
from korea_investment_stock import KoreaInvestment

broker = KoreaInvestment(api_key, api_secret, acc_no)

# 기존 코드 그대로 동작 (캐싱 자동 적용, 1주일 유효)
df = broker.fetch_kospi_symbols()
```

### 6.2 캐시 TTL 조정

```python
# 1일마다 갱신 (매일 최신 데이터 필요 시)
df = broker.fetch_kospi_symbols(ttl_hours=24)

# 1시간마다 갱신 (테스트/개발 시)
df = broker.fetch_kosdaq_symbols(ttl_hours=1)
```

### 6.3 강제 다운로드

```python
# 캐시 무시하고 항상 새로 다운로드
df = broker.fetch_kospi_symbols(force_download=True)
```

### 6.4 캐시 로그 확인 (디버깅)

```python
import logging

# 로깅 활성화 (캐시 히트/다운로드 로그 확인)
logging.basicConfig(level=logging.INFO)

broker = KoreaInvestment(api_key, api_secret, acc_no)

# 첫 번째 호출 - 다운로드
df = broker.fetch_kospi_symbols()
# 로그: INFO - 다운로드 중: https://...kospi_code.mst.zip -> /path/kospi_code.mst.zip

# 두 번째 호출 - 캐시 사용
df = broker.fetch_kospi_symbols()
# 로그: INFO - 캐시 사용: /path/kospi_code.mst.zip (age: 0.5h, ttl: 168h)
```

## 7. 마이그레이션 가이드

### 7.1 하위 호환성

**중단 변경 없음**: 기존 코드는 변경 없이 계속 작동합니다.

```python
# 기존 코드 (여전히 작동함)
df = broker.fetch_kospi_symbols()

# 새 기능 (선택적 사용)
df = broker.fetch_kospi_symbols(ttl_hours=12, force_download=True)
```

### 7.2 동작 변경 사항

| 항목 | 기존 동작 | 새 동작 |
|------|----------|---------|
| 파일 저장 위치 | `os.getcwd()` | `os.getcwd()` (동일) |
| 호출 시마다 | 항상 다운로드 | 캐시 확인 후 필요시만 다운로드 |
| 파일 삭제 | ZIP 파일 삭제 | ZIP 파일 유지 (캐시, 1주일) |
| TTL | 없음 | 1주일 (168시간) |

## 8. 위험 및 완화 방안

### 위험 1: 현재 디렉토리 쓰기 권한

**위험**: 현재 디렉토리에 쓰기 권한이 없을 수 있음
**완화**: 기존과 동일한 동작이므로 사용자가 이미 인지하고 있음
**조치**: 예외 발생 시 명확한 에러 메시지

### 위험 2: 파일 손상

**위험**: 다운로드 중 중단으로 파일 손상
**완화**: 다운로드 완료 후 압축 해제
**조치**: 손상된 파일 감지 시 `force_download=True`로 재다운로드

### 위험 3: 멀티프로세스 경합

**위험**: 여러 프로세스가 동시에 같은 파일 다운로드
**완화**: 기존과 동일한 동작
**조치**: 초기 버전에서는 경합 허용 (드문 케이스)

## 9. 성공 지표

### 완료 기준

#### 필수 (P0)
- [ ] 캐시 히트 시 다운로드 스킵 (1주일 이내)
- [ ] TTL 만료 시 재다운로드 (1주일 초과)
- [ ] `force_download=True` 동작
- [ ] 기존 테스트 모두 통과
- [ ] `os.chdir()` 제거

#### 권장 (P1)
- [ ] 단위 테스트 작성
- [ ] CLAUDE.md 문서화
- [ ] 로깅 추가 (캐시 히트/다운로드 로그)

#### 추가 (P2)
- [ ] 통합 테스트

---

**문서 버전**: 1.1
**마지막 업데이트**: 2025-12-04
**상태**: 분석 완료, 구현 준비
