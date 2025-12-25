# IPO 모듈 리팩토링 PRD

## 1. 개요

### 1.1 목표
`korea_investment_stock.py`에 있는 IPO 관련 코드를 `ipo/` 폴더로 분리하여 모듈화한다.

### 1.2 배경
현재 IPO 관련 코드가 두 곳에 분산되어 있음:
- **korea_investment_stock.py**: `fetch_ipo_schedule()` 메서드 (API 호출 로직)
- **ipo/ipo_helpers.py**: 유틸리티 함수들 (날짜 검증, 파싱 등)

기존 패키지 구조(cache, token_storage, rate_limit)와 일관성을 위해 IPO 관련 코드를 `ipo/` 폴더에 통합한다.

---

## 2. 현재 코드 분석

### 2.1 korea_investment_stock.py 내 IPO 코드

**위치**: 752-848줄

- 날짜 기본값 설정 (오늘 ~ 30일 후)
- 날짜 유효성 검증 (validate_date_format, validate_date_range 호출)
- API 호출: `/uapi/domestic-stock/v1/ksdinfo/pub-offer`
- TR ID: `HHKDB669108C0`

### 2.2 ipo/ 폴더 현재 구조

```
ipo/
├── __init__.py           # 헬퍼 함수 export
└── ipo_helpers.py        # 유틸리티 함수 7개
```

**ipo_helpers.py 함수 목록**:
| 함수 | 설명 |
|------|------|
| `validate_date_format()` | YYYYMMDD 형식 검증 |
| `validate_date_range()` | 시작일 <= 종료일 검증 |
| `parse_ipo_date_range()` | "2024.01.15~2024.01.16" 파싱 |
| `format_ipo_date()` | YYYYMMDD → YYYY-MM-DD 변환 |
| `calculate_ipo_d_day()` | 청약일까지 남은 일수 계산 |
| `get_ipo_status()` | "예정"/"진행중"/"마감" 상태 판단 |
| `format_number()` | 천단위 콤마 추가 |

### 2.3 IPO 관련 외부 참조

- **패키지 __init__.py**: IPO 헬퍼 함수 export
- **cache/cached_korea_investment.py**: `fetch_ipo_schedule()` 캐싱 지원 (broker 위임)

---

## 3. 리팩토링 방안

### 3.1 Option A: 단순 이동 (권장)

`fetch_ipo_schedule` 로직을 별도 모듈로 분리하되, `KoreaInvestment` 클래스에서 위임 호출.

**새 구조**:
```
ipo/
├── __init__.py           # 전체 export
├── ipo_helpers.py        # 유틸리티 함수 (기존 유지)
└── ipo_api.py            # IPO API 호출 함수 (신규)
```

**장점**:
- 기존 API 호환성 유지 (`broker.fetch_ipo_schedule()` 그대로 사용)
- IPO 로직 응집도 향상
- 단위 테스트 용이

### 3.2 Option B: Wrapper 패턴 (Cache/RateLimit 스타일)

`IpoKoreaInvestment` 래퍼 클래스 생성.

**평가**: Not Recommended (오버엔지니어링 - IPO 기능 하나를 위해 과도함)

---

## 4. 영향도 분석

### 4.1 Breaking Changes
**없음** - 기존 API 완전 호환
- `broker.fetch_ipo_schedule()` 그대로 사용 가능
- 헬퍼 함수 import 경로 동일

### 4.2 영향받는 파일

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| korea_investment_stock.py | 수정 | import 변경, 메서드 간소화 |
| ipo/__init__.py | 수정 | fetch_ipo_schedule export 추가 |
| ipo/ipo_api.py | 신규 | API 호출 로직 |
| cache/cached_korea_investment.py | 없음 | 변경 불필요 (broker 위임 유지) |

### 4.3 코드 라인 수 변화

| 파일 | 현재 | 변경 후 | 차이 |
|------|------|---------|------|
| korea_investment_stock.py | 849줄 | ~770줄 | -79줄 |
| ipo/ipo_api.py | 0줄 | ~80줄 | +80줄 |

---

## 5. 테스트 계획

```bash
# 단위 테스트
pytest -m "not integration"

# IPO 통합 테스트 (API 자격 증명 필요)
pytest korea_investment_stock/tests/test_ipo_integration.py -v
```

---

## 6. 마이그레이션 가이드

**사용자 영향**: 없음

```python
# 기존 코드 그대로 동작
broker = KoreaInvestment(...)
ipos = broker.fetch_ipo_schedule()

# 헬퍼 함수도 그대로 동작
from korea_investment_stock import get_ipo_status, format_ipo_date
```

---

## 7. 관련 문서

- [6_ipo_implementation.md](6_ipo_implementation.md) - 구현 상세
- [6_ipo_todo.md](6_ipo_todo.md) - 구현 체크리스트
