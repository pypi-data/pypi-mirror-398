# 보안 규칙

## 민감 정보 처리

### 1. API 인증 정보
- **절대로** 소스코드에 하드코딩하지 않음
- 환경 변수로만 처리
- 로그에 출력 금지

### 2. 로깅 시 마스킹
```python
# API 키 마스킹
def mask_sensitive_data(data: str) -> str:
    if len(data) > 8:
        return data[:4] + '*' * (len(data) - 8) + data[-4:]
    return '*' * len(data)

# 로그 출력 시
logger.info(f"API Key: {mask_sensitive_data(api_key)}")
```

### 3. 에러 메시지
- 에러 메시지에 민감 정보 포함 금지
- 계좌번호, API 키 등이 노출되지 않도록 주의

### 4. Git 관리
- `.gitignore`에 다음 항목 필수 포함:
  - `.env`
  - `*.key`
  - `*.secret`
  - `config/credentials.json`

### 5. 응답 데이터 처리
- 계좌번호, 잔고 등 민감 정보는 로그에 전체 출력하지 않음
- 디버깅 시에도 마스킹 처리 