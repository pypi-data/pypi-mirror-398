# 환경 변수 설정 방식 분석 PRD

## 1. 개요

### 1.1 목적
`korea_investment_stock` 라이브러리의 환경 변수 설정 방식이 Python 생태계에서 일반적인 패턴인지 분석하고, 개선 가능한 부분을 도출한다.

### 1.2 배경
- 라이브러리가 다른 모듈에서 사용될 때 설정 값(API 키, Redis URL 등)을 어떻게 전달받을지는 사용자 경험과 보안에 중요한 영향을 미침
- 현재 OS 환경 변수만 사용하는 방식이 업계 표준인지 검토 필요

### 1.3 분석 범위
- 현재 구현된 환경 변수 사용 패턴 분석
- 주요 Python SDK/라이브러리 비교 (boto3, OpenAI, Stripe, Twilio, Firebase)
- Best Practice 평가 및 개선 권장사항 도출

---

## 2. 현재 구현 분석

### 2.1 환경 변수 목록

| 환경 변수 | 필수 여부 | 기본값 | 용도 |
|----------|----------|--------|------|
| `KOREA_INVESTMENT_API_KEY` | 필수 | - | API 인증 키 |
| `KOREA_INVESTMENT_API_SECRET` | 필수 | - | API 인증 시크릿 |
| `KOREA_INVESTMENT_ACCOUNT_NO` | 필수 | - | 계좌번호 (12345678-01 형식) |
| `KOREA_INVESTMENT_TOKEN_STORAGE` | 선택 | `"file"` | 토큰 저장 방식 (file/redis) |
| `KOREA_INVESTMENT_REDIS_URL` | 선택 | `redis://localhost:6379/0` | Redis 연결 URL |
| `KOREA_INVESTMENT_REDIS_PASSWORD` | 선택 | - | Redis 비밀번호 |
| `KOREA_INVESTMENT_TOKEN_FILE` | 선택 | `~/.cache/kis/token.key` | 토큰 파일 경로 |

### 2.2 설정 패턴

#### 패턴 A: 필수 설정 (생성자 파라미터)
```python
# 사용자가 환경 변수를 직접 읽어서 전달해야 함
api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

with KoreaInvestment(api_key, api_secret, acc_no) as broker:
    result = broker.fetch_price("005930", "KR")
```

#### 패턴 B: 선택 설정 (환경 변수 + Fallback)
```python
# korea_investment_stock.py:239-250
storage_type = os.getenv("KOREA_INVESTMENT_TOKEN_STORAGE", "file").lower()
redis_url = os.getenv("KOREA_INVESTMENT_REDIS_URL", "redis://localhost:6379/0")
```

#### 패턴 C: 직접 객체 주입
```python
# 환경 변수 우회 가능
custom_storage = FileTokenStorage(file_path=Path("/custom/path/token.key"))
broker = KoreaInvestment(api_key, api_secret, acc_no, token_storage=custom_storage)
```

### 2.3 현재 방식 특징
- `.env` 파일 미지원 (OS 환경 변수만 사용)
- 필수 값은 반드시 생성자 파라미터로 전달
- 선택 값은 환경 변수에서 자동 로드 (fallback 값 존재)
- 테스트 용이성을 위한 직접 주입 지원

---

## 3. Python 라이브러리 비교 분석

### 3.1 비교 대상 라이브러리

#### boto3 (AWS SDK)
```python
# 방법 1: 환경 변수 자동 감지
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY 설정 시
client = boto3.client('s3')  # 자동으로 환경 변수 사용

# 방법 2: 생성자 파라미터 직접 전달
client = boto3.client('s3',
    aws_access_key_id='...',
    aws_secret_access_key='...'
)

# 방법 3: Config 파일 (~/.aws/credentials)
# 자동으로 읽어옴
```

**특징**: 다중 소스 지원, 명확한 우선순위 체계
- 우선순위: 생성자 파라미터 > 환경 변수 > Config 파일 > IAM Role

#### OpenAI SDK
```python
# 방법 1: 환경 변수 자동 감지
# OPENAI_API_KEY 설정 시 자동 사용
client = OpenAI()

# 방법 2: 생성자 파라미터
client = OpenAI(api_key="sk-...")

# 방법 3: set_default 함수
from agents import set_default_openai_key
set_default_openai_key("sk-...")
```

**특징**: 환경 변수 자동 감지 + `set_default_*()` 헬퍼 함수 제공

#### Stripe SDK
```python
# 방법 1: 모듈 레벨 설정 (레거시)
import stripe
stripe.api_key = os.environ.get("STRIPE_API_KEY")

# 방법 2: StripeClient 생성자 (v8+)
client = StripeClient("sk_test_...")
```

**특징**: 환경 변수 자동 감지 미지원, 사용자가 수동으로 설정해야 함

#### Twilio SDK
```python
# 방법 1: 환경 변수 자동 감지
# TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN 설정 시
client = Client()  # 자동으로 환경 변수 사용

# 방법 2: 생성자 파라미터
client = Client(account_sid, auth_token)
```

**특징**: 환경 변수 자동 감지, `.env` 파일 사용 권장

#### Firebase Admin SDK
```python
# 방법 1: 환경 변수 자동 감지
# GOOGLE_APPLICATION_CREDENTIALS (JSON 파일 경로) 설정 시
firebase_admin.initialize_app()

# 방법 2: 명시적 인증 정보 전달
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred)

# 방법 3: 개별 환경 변수로 dict 구성
cred = credentials.Certificate({
    "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
    "private_key": os.environ.get('FIREBASE_PRIVATE_KEY'),
    "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
})
```

**특징**: 다양한 설정 방식 지원, Google 환경에서 자동 감지

### 3.2 비교 표

| 라이브러리 | 환경변수 자동감지 | 생성자 파라미터 | Config 파일 | set_default() | 특징 |
|-----------|:---------------:|:-------------:|:-----------:|:-------------:|------|
| **boto3** | O | O | O | - | 가장 유연, 다중 소스 |
| **OpenAI** | O | O | - | O | 자동 감지 + 헬퍼 함수 |
| **Stripe** | X | O | - | - | 수동 설정 필수 |
| **Twilio** | O | O | - | - | 자동 감지, .env 권장 |
| **Firebase** | O | O | O | - | 다양한 방식 지원 |
| **korea_investment_stock** | **△** | O | - | - | 선택값만 자동 감지 |

### 3.3 패턴 분류

#### Type A - 환경변수 완전 자동 감지
**해당**: Twilio, OpenAI, boto3, Firebase

```python
# 생성자 파라미터 없이 호출하면 환경변수에서 자동 로드
client = Client()  # 환경 변수 자동 사용
```

**장점**:
- 사용자 코드 간결
- 보일러플레이트 코드 감소
- 환경별 설정 변경 용이

**단점**:
- 암묵적 동작으로 디버깅 어려울 수 있음
- 환경 변수 이름 규약 학습 필요

#### Type B - 수동 설정 필수
**해당**: Stripe, **현재 korea_investment_stock**

```python
# 사용자가 직접 환경변수를 읽어서 전달해야 함
api_key = os.getenv("STRIPE_API_KEY")
stripe.api_key = api_key
```

**장점**:
- 명시적이고 예측 가능한 동작
- 라이브러리가 환경에 대한 가정을 하지 않음
- 테스트 작성이 쉬움

**단점**:
- 사용자 코드에 보일러플레이트 증가
- 매번 환경 변수 읽는 코드 작성 필요

#### Type C - Hybrid 최적화
**해당**: boto3, Firebase

```python
# 다중 소스 지원 + 명확한 우선순위 체계
# 1) 생성자 파라미터 > 2) 환경변수 > 3) config 파일 > 4) 기본값
client = boto3.client('s3')  # 위 순서대로 설정 탐색
```

**장점**:
- 모든 사용 케이스 지원
- 유연성과 명시성 모두 확보

**단점**:
- 구현 복잡도 증가
- 설정 우선순위 학습 필요

---

## 4. Best Practice 평가

### 4.1 12-Factor App 원칙

[12-Factor App](https://12factor.net/config)의 설정 원칙:

> "환경 변수에 설정을 저장하라"

**평가**: 현재 방식은 12-Factor App 원칙을 준수함
- 환경 변수 사용 권장
- 코드와 설정 분리
- `.env` 파일이 아닌 OS 환경 변수 사용 (더 안전)

### 4.2 테스트 용이성

**Best Practice**: 라이브러리는 환경 변수를 직접 읽기보다 주입 패턴을 지원해야 함

```python
# Good: 테스트에서 mock 주입 가능
broker = KoreaInvestment(api_key, api_secret, acc_no, token_storage=mock_storage)

# Bad: 테스트에서 환경 변수를 조작해야 함
os.environ["KOREA_INVESTMENT_API_KEY"] = "test-key"
broker = KoreaInvestment()  # 환경 변수 자동 읽음
```

**평가**: 현재 방식은 테스트 용이성 측면에서 우수함
- 필수 값은 생성자로 주입
- `token_storage` 파라미터로 직접 객체 주입 가능

### 4.3 보안 고려사항

| 방식 | 보안 수준 | 설명 |
|-----|:--------:|------|
| OS 환경 변수 | 높음 | Git에 노출 위험 없음 |
| `.env` 파일 | 중간 | `.gitignore` 설정 필수 |
| 하드코딩 | 낮음 | 절대 금지 |
| Config 파일 | 중간 | 암호화 권장 |

**평가**: 현재 방식(OS 환경 변수만 사용)은 보안 측면에서 가장 안전한 선택

### 4.4 사용자 경험

**현재 방식의 사용자 코드**:
```python
import os
from korea_investment_stock import KoreaInvestment

api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
acc_no = os.getenv('KOREA_INVESTMENT_ACCOUNT_NO')

with KoreaInvestment(api_key, api_secret, acc_no) as broker:
    result = broker.fetch_price("005930", "KR")
```

**Twilio 스타일 사용자 코드**:
```python
from korea_investment_stock import KoreaInvestment

with KoreaInvestment() as broker:  # 환경 변수 자동 감지
    result = broker.fetch_price("005930", "KR")
```

**평가**: 현재 방식은 3줄의 보일러플레이트 코드가 필요함

---

## 5. 현재 방식 평가

### 5.1 장점

1. **명시적 동작**: 코드만 보고 어떤 값이 사용되는지 명확히 알 수 있음
2. **테스트 용이성**: 환경 변수 조작 없이 테스트 가능
3. **12-Factor App 준수**: OS 환경 변수 사용으로 보안 강화
4. **유연한 주입**: `token_storage` 파라미터로 커스텀 구현 가능
5. **Stripe과 동일한 패턴**: 업계에서 검증된 방식

### 5.2 단점/개선 가능 영역

1. **보일러플레이트 코드**: 매번 `os.getenv()` 호출 필요
2. **환경변수 이름 기억 필요**: 사용자가 정확한 변수명을 알아야 함
3. **일관성 부족**: 필수 값은 수동, 선택 값은 자동으로 혼재
4. **편의 기능 부재**: `set_default_*()` 같은 헬퍼 함수 없음

---

## 6. 개선 권장사항: Type C Hybrid 최적화

### 6.1 최종 목표

**목표**: boto3/Firebase 스타일 다중 설정 소스 + 우선순위 체계

```
우선순위: 생성자 파라미터 > 환경 변수 > Config 파일
```

### 6.2 최종 사용자 경험

```python
from korea_investment_stock import KoreaInvestment

# 방법 1: 생성자 파라미터 (최고 우선순위)
broker = KoreaInvestment(api_key="...", api_secret="...", acc_no="...")

# 방법 2: 환경 변수 자동 감지
broker = KoreaInvestment()  # KOREA_INVESTMENT_* 환경 변수 사용

# 방법 3: Config 파일에서 로드
broker = KoreaInvestment(config_file="~/.config/kis/config.yaml")

# 방법 4: 혼합 사용
broker = KoreaInvestment(api_key="override-key")  # 일부만 override
```

### 6.3 Config 파일 형식 (YAML)

```yaml
# ~/.config/kis/config.yaml
api_key: your-api-key
api_secret: your-api-secret
acc_no: "12345678-01"
token_storage_type: file
token_file: ~/.cache/kis/token.key
```

### 6.4 구현 로드맵

| Phase | 버전 | 내용 |
|:-----:|:----:|------|
| 1 | v0.9.0 | 환경변수 자동 감지 |
| 2 | v1.0.0 | Config 클래스 (YAML) |
| 3 | v1.1.0 | Hybrid 통합 |

> **상세 구현**: [1_var_implementation.md](./1_var_implementation.md)
>
> **TODO 체크리스트**: [1_var_todo.md](./1_var_todo.md)

---

## 7. 결론

### 7.1 현재 방식 평가

**현재**: Type B (수동 설정) 패턴 - Stripe SDK와 유사
- 12-Factor App 원칙 준수
- 테스트 용이성 확보
- 보안 측면에서 안전

**목표**: Type C (Hybrid 최적화) 패턴 - boto3/Firebase와 유사
- 다중 설정 소스 지원
- 명확한 우선순위 체계
- 사용자 편의성 극대화

### 7.2 기대 효과

1. **사용자 경험 개선**
   - 보일러플레이트 코드 제거 (3줄 → 0줄)
   - 다양한 설정 방식 선택 가능
   - boto3 사용자에게 친숙한 패턴

2. **유연성 확보**
   - 개발 환경: YAML config 파일 사용 (가독성, 주석 지원)
   - 프로덕션: 환경 변수 사용 (12-Factor App)
   - CI/CD: 환경 변수 또는 시크릿 관리 도구 연동

3. **하위 호환성 유지**
   - 기존 코드 변경 없이 동작
   - 새로운 기능은 opt-in 방식

---

## 참조 자료

- [Software Engineering SE - Library Config](https://softwareengineering.stackexchange.com/questions/438720/how-to-handle-config-env-vars-in-a-library-project)
- [Boto3 Configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)
- [OpenAI Agents SDK Config](https://openai.github.io/openai-agents-python/config/)
- [Stripe Python SDK](https://github.com/stripe/stripe-python)
- [Twilio Secure Credentials](https://www.twilio.com/docs/usage/secure-credentials)
- [Firebase Admin Setup](https://firebase.google.com/docs/admin/setup)
- [12-Factor App - Config](https://12factor.net/config)
- [Python Configuration Best Practices](https://tech.preferred.jp/en/blog/working-with-configuration-in-python/)
