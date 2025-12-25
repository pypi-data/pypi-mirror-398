# PRD: GitHub Actions 테스트 결과 가시성 개선

> **프로젝트**: Korea Investment Stock - Test Result Visibility Enhancement
> **작성일**: 2025-12-13
> **버전**: 1.0
> **관련 파일**: `.github/workflows/unit-tests.yml`

---

## 1. Executive Summary

### 문제 개요
현재 GitHub Actions에서 PR 코멘트로 표시되는 테스트 결과가 가독성이 낮아 테스트 상태를 빠르게 파악하기 어렵습니다.

**현재 출력 예시:**
```
## 🐳 Integration Test Results (Testcontainers)

```
=============== 11 passed, 215 deselected, 2 warnings in 10.93s ================
```
```

### 개선 목표
- 테스트 통과/실패 상태를 시각적으로 명확하게 표시
- 커버리지 정보 추가
- 실패한 테스트의 상세 정보 제공
- 단일 통합 코멘트로 가독성 향상

**개선 후 목표 출력:**
```
## 🧪 Test Results Summary

| 구분 | 결과 | 상세 |
|------|------|------|
| Unit Tests | ✅ **45 passed** | 0 failed, 2 skipped |
| Integration Tests | ✅ **11 passed** | 0 failed, 0 skipped |
| Coverage | 📊 **37.0%** | +2.1% vs main |

### ✅ All Tests Passed!
```

---

## 2. 현재 상황 분석

### 2.1 현재 워크플로우 구조

**파일**: `.github/workflows/unit-tests.yml`

```yaml
jobs:
  unit-tests:
    # pytest 출력을 파일로 저장
    - run: pytest ... > test-output.txt 2>&1

    # 단순 파싱으로 PR 코멘트 생성
    - uses: actions/github-script@v7
      with:
        script: |
          const summaryLine = lines.find(line => line.includes('passed'))
          # 마지막 15줄만 표시

  integration-tests:
    # 동일한 방식으로 별도 코멘트 생성
```

### 2.2 현재 문제점

| 문제 | 설명 | 영향 |
|------|------|------|
| **가독성 부족** | 단순 텍스트 출력만 표시 | 빠른 상태 파악 어려움 |
| **커버리지 없음** | pytest-cov 미사용 | 코드 품질 지표 부재 |
| **분리된 코멘트** | Unit/Integration 별도 코멘트 | PR 리뷰 혼란 |
| **실패 상세 없음** | 실패 시 구체적 정보 부족 | 디버깅 어려움 |
| **통계 부족** | 통과/실패/스킵 개수만 표시 | 트렌드 파악 불가 |

### 2.3 현재 의존성

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "fakeredis>=2.10.0",
    "testcontainers>=4.0.0",
]
# pytest-cov 없음!
```

---

## 3. 요구사항

### 3.1 기능 요구사항

#### FR-1: 통합 테스트 결과 코멘트
- **현재**: Unit/Integration 별도 2개 코멘트
- **목표**: 단일 통합 코멘트로 모든 결과 표시
- **방법**: 워크플로우 조정 또는 코멘트 업데이트 방식

#### FR-2: 시각적 상태 표시
- **통과**: ✅ 녹색 체크마크 + "passed" 강조
- **실패**: ❌ 빨간 X + "failed" 강조 + 상세 정보
- **스킵**: ⏭️ 스킵 아이콘 + 개수

#### FR-3: 테스트 통계 테이블
```markdown
| 구분 | Passed | Failed | Skipped | Total | 시간 |
|------|--------|--------|---------|-------|------|
| Unit | 45 | 0 | 2 | 47 | 3.2s |
| Integration | 11 | 0 | 0 | 11 | 10.9s |
```

#### FR-4: 커버리지 정보
- **현재**: 커버리지 측정 안 함
- **목표**: 전체 커버리지 퍼센트 표시
- **추가**: main 브랜치 대비 변화량 표시 (선택)

#### FR-5: 실패 테스트 상세 정보
실패 시 다음 정보 표시:
- 실패한 테스트 파일:라인
- 에러 메시지 요약
- 스택 트레이스 (접기/펼치기)

### 3.2 비기능 요구사항

#### NFR-1: 성능
- **목표**: 워크플로우 추가 시간 < 30초
- **방법**: 효율적인 파싱, 캐싱 활용

#### NFR-2: 유지보수성
- **요구**: 새로운 테스트 추가 시 자동 반영
- **방법**: 동적 파싱, 하드코딩 최소화

#### NFR-3: 확장성
- **요구**: Python 버전 매트릭스 지원
- **방법**: 버전별 결과 통합 표시

---

## 4. 기술 설계

### 4.1 아키텍처 옵션

#### Option A: JUnit XML + 커스텀 파싱 (권장)

```yaml
- name: Run tests with JUnit output
  run: |
    pytest korea_investment_stock/ \
      --junitxml=junit-report.xml \
      --cov=korea_investment_stock \
      --cov-report=xml \
      -v

- name: Parse and comment results
  uses: actions/github-script@v7
  with:
    script: |
      const xml = require('xml2js');
      // JUnit XML 파싱 후 마크다운 생성
```

**장점**:
- 표준화된 형식 (JUnit XML)
- 정확한 통계 추출
- 다른 도구와 호환 (CI 대시보드 등)

**단점**:
- XML 파싱 로직 필요
- 약간의 구현 복잡도

#### Option B: pytest-json-report 사용

```yaml
- name: Run tests with JSON output
  run: |
    pip install pytest-json-report
    pytest --json-report --json-report-file=report.json

- name: Parse JSON results
  uses: actions/github-script@v7
  with:
    script: |
      const report = require('./report.json');
      // JSON 직접 사용
```

**장점**:
- JSON 파싱 용이
- 상세한 정보 제공

**단점**:
- 추가 의존성
- 덜 표준화됨

#### Option C: 전용 GitHub Action 사용

```yaml
- name: Pytest coverage comment
  uses: MishaKav/pytest-coverage-comment@main
  with:
    pytest-xml-coverage-path: ./coverage.xml
    junitxml-path: ./junit-report.xml
```

**장점**:
- 구현 불필요
- 잘 만들어진 UI

**단점**:
- 외부 의존성
- 커스터마이징 제한

### 4.2 권장 설계: Option A + Option C 하이브리드

**Phase 1**: Option C 빠른 적용
- `MishaKav/pytest-coverage-comment` 또는 유사 액션 사용
- 즉시 개선된 가시성 확보

**Phase 2**: Option A 커스텀 개선
- 프로젝트 요구에 맞는 커스텀 파싱
- 통합 코멘트 구현

### 4.3 상세 설계

#### 4.3.1 의존성 추가

```toml
# pyproject.toml 수정
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "pytest-cov>=4.0.0",      # 추가!
    "fakeredis>=2.10.0",
    "testcontainers>=4.0.0",
]
```

#### 4.3.2 워크플로우 수정

```yaml
name: Tests

on:
  pull_request:
    branches: [main, master]
    types: [opened, synchronize, reopened]

jobs:
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

      - name: Upload coverage artifact
        uses: actions/upload-artifact@v4
        with:
          name: unit-test-results
          path: |
            junit-unit.xml
            coverage.xml
            test-output.txt

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

      - name: Upload integration results
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-results
          path: |
            junit-integration.xml
            integration-test-output.txt

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

            // Parse coverage (if available)
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
            const overallStatus = totalFailed === 0 ? '✅' : '❌';
            const statusMessage = totalFailed === 0
              ? '### ✅ All Tests Passed!'
              : `### ❌ ${totalFailed} Test(s) Failed`;

            // Build unit status
            const unitStatus = unitStats.failed === 0 ? '✅' : '❌';
            const unitDetail = `${unitStats.passed} passed` +
              (unitStats.failed > 0 ? `, ${unitStats.failed} failed` : '') +
              (unitStats.skipped > 0 ? `, ${unitStats.skipped} skipped` : '');

            // Build integration status
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

### 4.4 출력 예시

#### 모든 테스트 통과 시

```markdown
## 🧪 Test Results Summary

| 구분 | 상태 | 결과 | 시간 |
|------|:----:|------|------|
| **Unit Tests** | ✅ | 45 passed, 2 skipped | 3.2s |
| **Integration Tests** | ✅ | 11 passed | 10.9s |
| **Coverage** | 📊 | **37.0%** | - |

### ✅ All Tests Passed!

<details>
<summary>📋 Unit Test Details</summary>
...
</details>
```

#### 일부 테스트 실패 시

```markdown
## 🧪 Test Results Summary

| 구분 | 상태 | 결과 | 시간 |
|------|:----:|------|------|
| **Unit Tests** | ❌ | 43 passed, 2 failed, 2 skipped | 3.5s |
| **Integration Tests** | ✅ | 11 passed | 10.9s |
| **Coverage** | 📊 | **35.2%** | - |

### ❌ 2 Test(s) Failed

<details>
<summary>❌ Failed Tests</summary>

**test_cache_manager.py::TestCacheManager::test_cache_expiry**
```
AssertionError: Cache entry should have expired
```

**test_token_storage.py::TestFileStorage::test_save_token**
```
FileNotFoundError: [Errno 2] No such file or directory
```

</details>
```

---

## 5. 구현 계획

### 5.1 단계별 작업

#### Step 1: 의존성 추가 (10분)
- `pyproject.toml`에 `pytest-cov>=4.0.0` 추가
- 로컬에서 설치 확인

#### Step 2: 워크플로우 수정 (30분)
- `unit-tests.yml` 수정
- JUnit XML 및 커버리지 출력 추가
- 통합 리포트 job 추가

#### Step 3: 파싱 로직 구현 (30분)
- github-script 내 파싱 로직 작성
- 마크다운 템플릿 구현
- 에지 케이스 처리

#### Step 4: 테스트 및 검증 (20분)
- 테스트 PR 생성
- 정상 케이스 확인
- 실패 케이스 확인

### 5.2 체크리스트

```markdown
- [ ] pyproject.toml에 pytest-cov 추가
- [ ] unit-tests.yml 수정
  - [ ] pytest-cov 옵션 추가
  - [ ] JUnit XML 출력 추가
  - [ ] artifact 업로드 추가
  - [ ] 통합 리포트 job 추가
- [ ] 파싱 로직 구현
  - [ ] 단위 테스트 결과 파싱
  - [ ] 통합 테스트 결과 파싱
  - [ ] 커버리지 파싱
  - [ ] 실패 테스트 상세 정보 추출
- [ ] 마크다운 템플릿 구현
  - [ ] 통계 테이블
  - [ ] 상태 아이콘
  - [ ] 접기/펼치기 상세 정보
- [ ] 테스트 및 검증
  - [ ] 모든 테스트 통과 시 출력 확인
  - [ ] 일부 테스트 실패 시 출력 확인
  - [ ] 커버리지 표시 확인
```

---

## 6. 위험 요소 및 대응

### Risk 1: XML 파싱 실패
**위험도**: 🟡 중간
**설명**: JUnit XML 형식이 예상과 다를 경우

**대응**:
- 텍스트 파싱 fallback 구현
- 에러 발생 시 기존 방식으로 출력

### Risk 2: 워크플로우 시간 증가
**위험도**: 🟢 낮음
**설명**: 커버리지 측정으로 실행 시간 증가

**대응**:
- 병렬 실행 유지
- 캐싱 최적화
- 예상 증가: 10-20초

### Risk 3: 코멘트 중복
**위험도**: 🟡 중간
**설명**: 기존 코멘트 + 새 통합 코멘트 = 3개

**대응**:
- 기존 코멘트 로직 제거
- 통합 리포트 job만 코멘트 생성

---

## 7. 성공 지표

### 7.1 정량적 지표
- **코멘트 수**: 2개 → 1개
- **정보 항목**: 3개 → 8개 이상
- **커버리지 표시**: 없음 → 있음

### 7.2 정성적 지표
- PR에서 테스트 상태를 5초 내 파악 가능
- 실패 시 원인을 즉시 확인 가능
- 코드 품질 트렌드 추적 가능

---

## 8. 향후 확장 계획

### 8.1 커버리지 배지
```yaml
- name: Update coverage badge
  uses: schneegans/dynamic-badges-action@v1.6.0
  with:
    gistID: ${{ secrets.GIST_ID }}
    filename: coverage.json
    label: Coverage
    message: ${{ steps.coverage.outputs.total }}%
```

### 8.2 트렌드 차트
- 커버리지 히스토리 저장
- PR 코멘트에 트렌드 그래프 추가

### 8.3 Codecov 연동
```yaml
- name: Upload to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

---

## 9. 참고 자료

### 9.1 현재 워크플로우
- `.github/workflows/unit-tests.yml`

### 9.2 관련 GitHub Actions
- [pytest-coverage-comment](https://github.com/MishaKav/pytest-coverage-comment)
- [test-reporter](https://github.com/dorny/test-reporter)
- [codecov-action](https://github.com/codecov/codecov-action)

### 9.3 pytest 문서
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [JUnit XML 출력](https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files)

---

## 10. 결론

이 PRD는 GitHub Actions 테스트 결과의 가시성을 개선하기 위한 계획을 정의합니다.

**핵심 개선 사항**:
1. **통합 코멘트**: 2개 → 1개 통합 리포트
2. **시각적 상태**: ✅/❌ 아이콘으로 빠른 상태 파악
3. **커버리지 표시**: pytest-cov로 코드 커버리지 측정
4. **상세 정보**: 실패 테스트 상세 정보 제공
5. **테이블 형식**: 구조화된 통계 정보 표시

**예상 효과**:
- PR 리뷰 시간 단축 (테스트 결과 파악 5초 이내)
- 코드 품질 가시성 향상 (커버리지 추적)
- 디버깅 효율성 향상 (실패 상세 정보)

---

**작성일**: 2025-12-13
**버전**: 1.0
**상태**: Ready for Implementation
