# API 호출 중 토큰 만료 시 자동 재발급 기능 PRD

## 문제 상황

### 현상
장시간 실행되는 배치 작업 중 토큰이 만료되면, 이후 모든 API 호출이 실패합니다.

```
2025-12-11 13:15:11 - stock-data-batch - ERROR -
[US 11780/11780] ✗ ZVOL (API): API Error (info): 기간이 만료된 token 입니다
```

### 영향
- 배치 작업 중단 (16,000+ 종목 중 일부만 처리)
- 연속 5회 동일 에러 발생 시 ConsecutiveFailureTracker에 의해 배치 강제 종료
- 수동 재실행 필요

## 근본 원인 분석

### 1. 현재 토큰 관리 구조

```
KoreaInvestment 클라이언트 초기화
    ↓
TokenManager.get_valid_token()
    ↓
is_token_valid() → 저장소의 만료시간(timestamp) 체크
    ↓
유효하면 저장된 토큰 반환 / 만료면 새로 발급
```

**토큰 유효성 검사 시점:**
- `KoreaInvestment.__init__()` - 클라이언트 초기화 시 **1회만** 검사

### 2. 문제의 코드 흐름

**TokenManager.get_valid_token()** (`token/manager.py:68-87`):
```python
def get_valid_token(self) -> str:
    if self.is_token_valid():           # 저장소 timestamp만 체크
        if self._access_token is None:
            self._load_token()
        return self._access_token

    # 토큰 발급
    self._issue_token()
    return self._access_token
```

**API 호출 메서드** (`korea_investment_stock.py:260-273`):
```python
def fetch_domestic_price(self, symbol: str, ...):
    headers = {
        "authorization": self.access_token,  # 초기화 시 발급된 토큰 그대로 사용
        ...
    }
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()  # ❌ 토큰 만료 에러 체크 없음
```

### 3. 핵심 문제점

| 현재 동작 | 문제점 |
|-----------|--------|
| 초기화 시점에만 토큰 유효성 검사 | 24시간+ 실행되는 배치에서 중간 만료 감지 불가 |
| API 응답에서 만료 에러 무시 | `"기간이 만료된 token 입니다"` 메시지 처리 없음 |
| `issue_access_token()` 메서드는 존재 | 외부에서 수동으로 호출해야 함 |

### 4. 실제 발생 시나리오

```
┌──────────────────────────────────────────────────────────────────┐
│ 배치 시작 (AM 9:00)                                              │
├──────────────────────────────────────────────────────────────────┤
│ 토큰 발급: access_token (만료: AM 9:00 + 24시간)                 │
│ KR 종목 처리: 5,000개 성공 ✓                                     │
│ US 종목 처리: 11,000개 성공 ✓                                    │
└──────────────────────────────────────────────────────────────────┘
          ↓ (토큰 만료 시점 도달 - 예: 다음날 AM 9:00)
┌──────────────────────────────────────────────────────────────────┐
│ US 종목 11,776번째: "기간이 만료된 token 입니다" (1/5)           │
│ US 종목 11,777번째: "기간이 만료된 token 입니다" (2/5)           │
│ US 종목 11,778번째: "기간이 만료된 token 입니다" (3/5)           │
│ US 종목 11,779번째: "기간이 만료된 token 입니다" (4/5)           │
│ US 종목 11,780번째: "기간이 만료된 token 입니다" (5/5)           │
│ [FATAL] 동일 API 오류 5회 연속 발생으로 배치 중단                │
└──────────────────────────────────────────────────────────────────┘
```

## 해결 방안

### 방안 비교

| 방안 | 구현 위치 | 장점 | 단점 |
|------|-----------|------|------|
| **A. 라이브러리 자동 재발급** | korea_investment_stock | 모든 사용자에게 자동 적용 | Breaking change 가능성 |
| **B. Wrapper 클래스 제공** | korea_investment_stock | opt-in, 기존 동작 유지 | 사용자가 명시적 선택 필요 |
| **C. 사용자 직접 구현** | 사용자 프로젝트 | 라이브러리 수정 없음 | 반복 구현 필요 |

### 권장: 방안 A - 라이브러리 자동 재발급 (Transparent Token Refresh)

**핵심 아이디어:**
- API 호출 메서드에서 토큰 만료 응답 감지 시 자동으로 토큰 재발급 후 재시도
- 사용자 코드 수정 불필요 (투명한 처리)
- 기존 API 동작과 호환

## 상세 설계

### 1. 토큰 만료 에러 감지

**API 응답 패턴:**

> **참고**: 공식 API 문서에는 토큰 만료 에러 메시지가 명시되어 있지 않습니다.
> 아래는 실제 운영 환경에서 관측된 응답입니다. (stock-data-batch 프로젝트 로그 참조)

```python
{
    "rt_cd": "1",          # 실패
    "msg_cd": "...",
    "msg1": "기간이 만료된 token 입니다."  # 마침표 포함
}
```

**감지 로직:**
```python
def _is_token_expired_response(self, resp_json: dict) -> bool:
    """API 응답에서 토큰 만료 여부 확인"""
    if resp_json.get('rt_cd') != '0':
        msg = resp_json.get('msg1', '')
        return '기간이 만료된 token' in msg
    return False
```

### 2. 자동 재발급 및 재시도 로직

**구현 위치:** `KoreaInvestment` 클래스

```python
def _request_with_token_refresh(
    self,
    method: str,
    url: str,
    headers: dict,
    params: dict = None,
    max_retries: int = 1
) -> dict:
    """토큰 만료 시 자동 재발급 후 재시도하는 요청 래퍼

    Args:
        method: HTTP 메서드 ("GET" 또는 "POST")
        url: API URL
        headers: 요청 헤더 (authorization 포함)
        params: 쿼리 파라미터
        max_retries: 토큰 재발급 후 재시도 횟수 (기본 1회)

    Returns:
        dict: API 응답 JSON
    """
    for attempt in range(max_retries + 1):
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params)
        else:
            resp = requests.post(url, headers=headers, json=params)

        resp_json = resp.json()

        # 토큰 만료 에러 감지
        if self._is_token_expired_response(resp_json) and attempt < max_retries:
            logger.info("토큰 만료 감지, 재발급 시도...")
            self.issue_access_token()

            # 헤더의 authorization 갱신
            headers["authorization"] = self.access_token
            continue

        return resp_json

    return resp_json
```

### 3. 영향받는 API 메서드

다음 메서드들에 `_request_with_token_refresh` 적용:

| 메서드 | 위치 | 설명 |
|--------|------|------|
| `fetch_domestic_price()` | L240-273 | 국내 주식/ETF 현재가 |
| `fetch_price_detail_oversea()` | L409-509 | 해외 주식 상세 |
| `fetch_stock_info()` | L511-590 | 상품 기본 정보 |
| `fetch_search_stock_info()` | L592-668 | 주식 상세 정보 |
| `fetch_ipo_schedule()` | L671-697 | IPO 일정 |

### 4. 변경 예시

**Before:**
```python
def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> dict:
    # ... headers, params 설정 ...
    resp = requests.get(url, headers=headers, params=params)
    return resp.json()
```

**After:**
```python
def fetch_domestic_price(self, symbol: str, symbol_type: str = "Stock") -> dict:
    # ... headers, params 설정 ...
    return self._request_with_token_refresh("GET", url, headers, params)
```

## 관련 문서

- **구현 가이드**: [1_token_implementation.md](./1_token_implementation.md)
- **체크리스트**: [1_token_todo.md](./1_token_todo.md)

## 리스크 및 고려사항

### 1. 재시도 무한 루프 방지

**문제:** 토큰 재발급 후에도 계속 만료 에러 발생 시

**해결:** `max_retries` 파라미터로 재시도 횟수 제한 (기본 1회)

### 2. API 호출 중복

**문제:** 재시도로 인한 API 호출 2배

**해결:**
- 토큰 만료는 드문 이벤트 (24시간에 1회)
- 사전 TTL 체크로 대부분의 만료 방지 가능

### 3. Thread Safety

**문제:** 멀티스레드 환경에서 동시 토큰 재발급

**해결:**
- TokenManager는 이미 thread-safe 설계
- 여러 스레드가 동시에 재발급해도 최종적으로 유효한 토큰 저장

### 4. 하위 호환성

**영향:**
- 기존 코드 수정 불필요
- API 동작 동일 (성공 시 동일 응답 반환)
- 실패 시에도 동일 에러 메시지 반환 (재시도 실패 시)

## 관련 파일

**라이브러리:**
- `korea_investment_stock/korea_investment_stock.py` - 메인 클라이언트
- `korea_investment_stock/token/manager.py` - 토큰 관리자
- `korea_investment_stock/token/storage.py` - 토큰 저장소
- `korea_investment_stock/ipo.py` - IPO API

**참고 (사용 예시 프로젝트):**
- `/Users/user/PycharmProjects/stock-data-batch/services/stock_collector.py`
- `/Users/user/PycharmProjects/stock-data-batch/docs/start/3_token_prd.md`

## 결론

현재 korea-investment-stock 라이브러리는 **초기화 시점에만** 토큰 유효성을 검사합니다. 장시간 실행되는 배치 작업에서 토큰이 만료되면 모든 API 호출이 실패합니다.

**제안하는 해결책:**
1. API 응답에서 토큰 만료 에러를 감지하는 헬퍼 메서드 추가
2. 토큰 만료 시 자동으로 `issue_access_token()` 호출 후 재시도
3. 기존 API 메서드들에 투명하게 적용

이를 통해 사용자 코드 수정 없이 장시간 배치 작업의 안정성을 확보할 수 있습니다.
