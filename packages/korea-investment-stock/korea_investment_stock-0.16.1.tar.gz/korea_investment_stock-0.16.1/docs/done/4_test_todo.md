# TODO: GitHub Actions 테스트 결과 가시성 개선

> **관련 PRD**: `4_test_prd.md`
> **관련 구현**: `4_test_implementation.md`

---

## Step 1: 의존성 추가

- [x] `pyproject.toml`에 pytest-cov 추가
  ```toml
  "pytest-cov>=4.0.0",
  ```
- [x] 로컬에서 설치 확인
  ```bash
  pip install -e ".[dev]"
  ```

---

## Step 2: 워크플로우 수정 - Unit Tests

- [x] pytest 명령어에 coverage 옵션 추가
  - `--cov=korea_investment_stock`
  - `--cov-report=xml`
  - `--cov-report=term-missing`
  - `--junitxml=junit-unit.xml`
- [x] 출력 방식 변경: `> test-output.txt 2>&1` → `2>&1 | tee test-output.txt`
- [x] 기존 PR 코멘트 step 제거
- [x] artifact 업로드 step 추가
  ```yaml
  - name: Upload unit test results
    uses: actions/upload-artifact@v4
    with:
      name: unit-test-results
      path: |
        junit-unit.xml
        coverage.xml
        test-output.txt
  ```

---

## Step 3: 워크플로우 수정 - Integration Tests

- [x] pytest 명령어에 JUnit XML 옵션 추가
  - `--junitxml=junit-integration.xml`
- [x] 출력 방식 변경: `> integration-test-output.txt 2>&1` → `2>&1 | tee integration-test-output.txt`
- [x] 기존 PR 코멘트 step 제거
- [x] artifact 업로드 step 추가
  ```yaml
  - name: Upload integration test results
    uses: actions/upload-artifact@v4
    with:
      name: integration-test-results
      path: |
        junit-integration.xml
        integration-test-output.txt
  ```

---

## Step 4: Report Job 추가

- [x] report job 생성
  - `needs: [unit-tests, integration-tests]`
  - `if: always()`
- [x] artifact 다운로드 step 추가
- [x] 파싱 로직 구현
  - [x] Unit test 결과 파싱 (passed/failed/skipped/time)
  - [x] Integration test 결과 파싱
  - [x] Coverage 퍼센트 파싱
- [x] 마크다운 템플릿 구현
  - [x] 통계 테이블
  - [x] 상태 아이콘 (✅/❌)
  - [x] 접기/펼치기 상세 정보
- [x] PR 코멘트 생성

---

## Step 5: 테스트 및 검증

- [x] 로컬에서 pytest-cov 동작 확인 (168 passed, 67% coverage)
  ```bash
  pytest korea_investment_stock/ -v \
    -m "not integration" \
    --cov=korea_investment_stock \
    --cov-report=term-missing
  ```
- [ ] 테스트 PR 생성
- [ ] 모든 테스트 통과 시 출력 확인
  - [ ] 단일 통합 코멘트 생성 확인
  - [ ] 테이블 형식 확인
  - [ ] 커버리지 표시 확인
- [ ] 일부 테스트 실패 시 출력 확인 (선택)
  - [ ] 실패 상태 아이콘 확인
  - [ ] 실패 개수 표시 확인

---

## 완료 기준

- [ ] PR 코멘트가 2개 → 1개로 통합됨
- [ ] 테이블 형식으로 Unit/Integration/Coverage 결과 표시
- [ ] 상태 아이콘(✅/❌)으로 빠른 상태 파악 가능
- [ ] 접기/펼치기로 상세 정보 제공
