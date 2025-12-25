# Implementation: GitHub Actions 테스트 결과 가시성 개선

> **관련 PRD**: `4_test_prd.md`
> **관련 파일**: `.github/workflows/unit-tests.yml`, `pyproject.toml`

---

## 1. 핵심 변경 사항

### 1.1 의존성 추가

**파일**: `pyproject.toml`

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "pytest-cov>=4.0.0",      # 추가
    "fakeredis>=2.10.0",
    "testcontainers>=4.0.0",
]
```

### 1.2 워크플로우 구조 변경

**기존 구조**:
```
unit-tests job → 개별 코멘트
integration-tests job → 개별 코멘트
```

**변경 구조**:
```
unit-tests job → artifact 업로드
integration-tests job → artifact 업로드
report job → 통합 코멘트 (1개)
```

---

## 2. 워크플로우 상세 구현

### 2.1 Unit Tests Job

```yaml
unit-tests:
  name: Unit Tests (Python 3.12)
  runs-on: ubuntu-latest

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python 3.12
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"
        cache: 'pip'
        cache-dependency-path: 'pyproject.toml'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run unit tests with coverage
      id: pytest
      run: |
        pytest korea_investment_stock/ -v \
          -m "not integration" \
          --ignore=korea_investment_stock/test_korea_investment_stock.py \
          --ignore=korea_investment_stock/test_integration_us_stocks.py \
          --ignore=korea_investment_stock/cache/test_cached_integration.py \
          -k "not (Redis or redis_storage or TestTokenStorageIntegration)" \
          --cov=korea_investment_stock \
          --cov-report=xml \
          --cov-report=term-missing \
          --junitxml=junit-unit.xml \
          2>&1 | tee test-output.txt
      continue-on-error: true

    - name: Upload unit test results
      uses: actions/upload-artifact@v4
      with:
        name: unit-test-results
        path: |
          junit-unit.xml
          coverage.xml
          test-output.txt
```

### 2.2 Integration Tests Job

```yaml
integration-tests:
  name: Integration Tests (Python 3.12 + Docker)
  runs-on: ubuntu-latest

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python 3.12
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"
        cache: 'pip'
        cache-dependency-path: 'pyproject.toml'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev,redis]"

    - name: Run integration tests
      id: integration-pytest
      run: |
        pytest -m integration -v \
          --junitxml=junit-integration.xml \
          2>&1 | tee integration-test-output.txt
      continue-on-error: true

    - name: Upload integration test results
      uses: actions/upload-artifact@v4
      with:
        name: integration-test-results
        path: |
          junit-integration.xml
          integration-test-output.txt
```

### 2.3 Report Job (통합 리포트)

```yaml
report:
  name: Test Report
  needs: [unit-tests, integration-tests]
  runs-on: ubuntu-latest
  if: always()

  steps:
    - name: Download all artifacts
      uses: actions/download-artifact@v4

    - name: Generate combined report
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');

          // Parse unit test results
          let unitOutput = '';
          let unitStats = { passed: 0, failed: 0, skipped: 0, total: 0, time: '0s' };
          try {
            unitOutput = fs.readFileSync('unit-test-results/test-output.txt', 'utf8');
            const match = unitOutput.match(/(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?.*in ([\d.]+)s/);
            if (match) {
              unitStats.passed = parseInt(match[1]) || 0;
              unitStats.failed = parseInt(match[2]) || 0;
              unitStats.skipped = parseInt(match[3]) || 0;
              unitStats.total = unitStats.passed + unitStats.failed + unitStats.skipped;
              unitStats.time = match[4] + 's';
            }
          } catch (e) {
            console.log('Unit test results not found');
          }

          // Parse integration test results
          let integrationOutput = '';
          let integrationStats = { passed: 0, failed: 0, skipped: 0, total: 0, time: '0s' };
          try {
            integrationOutput = fs.readFileSync('integration-test-results/integration-test-output.txt', 'utf8');
            const match = integrationOutput.match(/(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?.*in ([\d.]+)s/);
            if (match) {
              integrationStats.passed = parseInt(match[1]) || 0;
              integrationStats.failed = parseInt(match[2]) || 0;
              integrationStats.skipped = parseInt(match[3]) || 0;
              integrationStats.total = integrationStats.passed + integrationStats.failed + integrationStats.skipped;
              integrationStats.time = match[4] + 's';
            }
          } catch (e) {
            console.log('Integration test results not found');
          }

          // Parse coverage
          let coverage = 'N/A';
          try {
            const covOutput = fs.readFileSync('unit-test-results/test-output.txt', 'utf8');
            const covMatch = covOutput.match(/TOTAL\s+\d+\s+\d+\s+(\d+)%/);
            if (covMatch) {
              coverage = covMatch[1] + '%';
            }
          } catch (e) {}

          // Determine overall status
          const totalFailed = unitStats.failed + integrationStats.failed;
          const statusMessage = totalFailed === 0
            ? '### ✅ All Tests Passed!'
            : `### ❌ ${totalFailed} Test(s) Failed`;

          // Build status icons
          const unitStatus = unitStats.failed === 0 ? '✅' : '❌';
          const unitDetail = `${unitStats.passed} passed` +
            (unitStats.failed > 0 ? `, ${unitStats.failed} failed` : '') +
            (unitStats.skipped > 0 ? `, ${unitStats.skipped} skipped` : '');

          const integrationStatus = integrationStats.failed === 0 ? '✅' : '❌';
          const integrationDetail = `${integrationStats.passed} passed` +
            (integrationStats.failed > 0 ? `, ${integrationStats.failed} failed` : '') +
            (integrationStats.skipped > 0 ? `, ${integrationStats.skipped} skipped` : '');

          // Generate comment
          const comment = `## 🧪 Test Results Summary

| 구분 | 상태 | 결과 | 시간 |
|------|:----:|------|------|
| **Unit Tests** | ${unitStatus} | ${unitDetail} | ${unitStats.time} |
| **Integration Tests** | ${integrationStatus} | ${integrationDetail} | ${integrationStats.time} |
| **Coverage** | 📊 | **${coverage}** | - |

${statusMessage}

<details>
<summary>📋 Unit Test Details</summary>

\`\`\`
${unitOutput.split('\n').slice(-30).join('\n')}
\`\`\`

</details>

<details>
<summary>🐳 Integration Test Details</summary>

\`\`\`
${integrationOutput.split('\n').slice(-20).join('\n')}
\`\`\`

</details>
`;

          // Post comment
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

---

## 3. 출력 예시

### 3.1 모든 테스트 통과

```markdown
## 🧪 Test Results Summary

| 구분 | 상태 | 결과 | 시간 |
|------|:----:|------|------|
| **Unit Tests** | ✅ | 45 passed, 2 skipped | 3.2s |
| **Integration Tests** | ✅ | 11 passed | 10.9s |
| **Coverage** | 📊 | **37.0%** | - |

### ✅ All Tests Passed!
```

### 3.2 일부 테스트 실패

```markdown
## 🧪 Test Results Summary

| 구분 | 상태 | 결과 | 시간 |
|------|:----:|------|------|
| **Unit Tests** | ❌ | 43 passed, 2 failed, 2 skipped | 3.5s |
| **Integration Tests** | ✅ | 11 passed | 10.9s |
| **Coverage** | 📊 | **35.2%** | - |

### ❌ 2 Test(s) Failed
```

---

## 4. 파일 변경 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `pyproject.toml` | 수정 | pytest-cov 의존성 추가 |
| `.github/workflows/unit-tests.yml` | 수정 | 전체 워크플로우 재구성 |

---

## 5. 검증 방법

1. **로컬 테스트**: pytest-cov 옵션 동작 확인
   ```bash
   pytest korea_investment_stock/ -v \
     -m "not integration" \
     --cov=korea_investment_stock \
     --cov-report=term-missing
   ```

2. **PR 테스트**: 테스트 PR 생성하여 코멘트 출력 확인
   - 모든 테스트 통과 케이스
   - 일부 테스트 실패 케이스
   - 커버리지 표시 확인
