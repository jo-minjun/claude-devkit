# 에이전트별 컨텍스트 주입 가이드

각 에이전트 호출 시 역할에 맞는 컨텍스트를 세션에서 추출하여 주입한다.

## 세션 기반 컨텍스트 주입

오케스트레이터는 `~/.claude/claude-devkit/sessions/{hash}.yaml` 에서 컨텍스트를 읽어 서브에이전트 프롬프트에 주입한다.

### 공통 헤더 (모든 에이전트)

```
═══════════════════════════════════════════════════════════════
[세션 컨텍스트]
- 프로젝트: {{session.project_path}}
- 참고: {{session.reference_path}}
- 현재 작업: {{session.tasks[current].name}}
- 현재 페이즈: {{session.current_phase}}

[프로젝트 매니페스트]
- CLAUDE.md: {{session.project_manifest.claude_md}}
- AGENTS.md: {{session.project_manifest.agents_md}}
═══════════════════════════════════════════════════════════════

[탐색된 파일 요약]
{{#each session.explored_files}}
- {{path}}: {{summary}}
{{/each}}

상세 내용 필요 시 Read 도구로 직접 조회하세요.
프로젝트 규칙 확인 필요 시 CLAUDE.md를 읽으세요. (null이면 기존 코드 패턴만 따름)
═══════════════════════════════════════════════════════════════
```

---

## 0. Code Explore 에이전트 (Discovery)

### 역할
프로젝트 구조 파악 및 주요 파일 요약

### 주입할 컨텍스트
```yaml
context:
  project_path: "{{session.project_path}}"
  reference_path: "{{session.reference_path}}"  # 있는 경우
```

### 프롬프트 템플릿
```
프로젝트 구조를 파악하고 주요 파일을 요약해줘.

[프로젝트 경로]
{{session.project_path}}

{{#if session.reference_path}}
[참고 프로젝트]
{{session.reference_path}}
{{/if}}

[요청 사항]
1. 디렉토리 구조 파악
2. CLAUDE.md, AGENTS.md 위치 확인 (없으면 null로 보고)
3. 주요 소스 파일 요약 (각 파일당 1-2줄)
4. 결과를 다음 형식으로 출력:

project_manifest:
  claude_md: "/absolute/path/to/CLAUDE.md"  # 없으면 null
  agents_md: "/absolute/path/to/AGENTS.md"  # 없으면 null

explored_files:
  - path: "src/main/.../파일명.java"
    summary: "간단한 설명"
```

### 출력
- `project_manifest` → `session.project_manifest`에 저장
- `explored_files` 목록 → `session.explored_files`에 저장

---

## 1. Planner 에이전트 (Parallel Discovery용)

### 역할
코드 탐색 결과 없이 잠정 작업 정의

### 주입할 컨텍스트
```yaml
context:
  - 프로젝트 경로
  - CLAUDE.md 내용 (있는 경우)
  - 사용자 원본 요청
  # explored_files는 주입하지 않음 (병렬 실행)
```

### 프롬프트 템플릿
```
[프로젝트 정보]
- 경로: {{session.project_path}}
{{#if claudemd_content}}
- 프로젝트 설정:
{{claudemd_content}}
{{/if}}

[사용자 요청]
{{user_request}}

[지시사항]
다음 작업을 수행하라:
1. 요청을 분석하여 단일 작업으로 축소
2. 작업 완료 조건을 명확히 정의
3. 스코프 경계를 설정 (포함/미포함 항목 명시)
4. **코드 구조를 모르므로 가정(assumptions)을 명시적으로 기록**
5. Preliminary Design Brief를 다음 형식으로 출력

[출력 형식]
preliminary_design_brief:
  task_name: [작업명]
  objective: [목표]
  assumptions:  # 필수 - 코드 구조에 대한 가정
    - "[가정 1: 예상되는 파일 위치, 기존 구조 등]"
    - "[가정 2: ...]"
  completion_criteria:
    - [완료 조건 1]
    - [완료 조건 2]
  scope_in:
    - [포함 항목 - 일반적인 경로 사용]
  scope_out:
    - [미포함 항목]
  dependencies:
    - [의존성 - 추정]
```

### 출력
Preliminary Design Brief → `session.contracts.preliminary_design_brief`에 저장

---

## 1.5. Merge 로직 (오케스트레이터 직접 수행)

### 목적
병렬 실행된 Code Explore와 Planner 결과를 병합하여 최종 `design_brief` 생성

### 입력
- `session.explored_files` (Code Explore 결과)
- `session.contracts.preliminary_design_brief` (Planner 결과)

### 병합 알고리즘

```
1. assumptions 검증:
   for each assumption in preliminary_design_brief.assumptions:
     - explored_files에서 관련 파일 검색
     - 일치/불일치 판정
     - 불일치 시 correction 기록

2. scope_in 조정:
   for each item in preliminary_design_brief.scope_in:
     - explored_files에서 매칭 파일 찾기
     - 없으면: 유사 파일 검색, 또는 신규 생성 표시
     - 있으면: 정확한 경로로 교체

3. 의존성 보완:
   - explored_files의 import/dependency 정보 활용
   - preliminary_design_brief.dependencies 보강

4. 최종 design_brief 생성:
   - assumptions 제거 (검증 완료)
   - 조정된 scope_in, scope_out, dependencies 적용
   - completion_criteria 구체화
```

### 재실행 조건
- assumptions 중 50% 이상 불일치 → Planner 재호출 (explored_files 주입, 순차 모드)
- 사소한 불일치 → 오케스트레이터가 직접 조정

### 출력
최종 Design Brief → `session.contracts.design_brief`에 저장

---

## 2. Architect 에이전트

### 역할
설계 확정 및 불변 조건 정의

### 주입할 컨텍스트
```yaml
context:
  - 공통 헤더
  - session.contracts.design_brief (Planner 산출물)
```

### 프롬프트 템플릿
```
{{공통 헤더}}

[Design Brief]
{{session.contracts.design_brief}}

[지시사항]
다음 작업을 수행하라:
1. Design Brief를 바탕으로 설계 확정
2. 의존성 방향 규칙 준수 (도메인 → 외부 의존 금지)
3. 인터페이스 계약 정의
4. 설계 불변 조건 명시
5. Design Contract를 다음 형식으로 출력

[출력 형식]
design_contract:
  task: [작업명]
  invariants:
    - [불변 조건 1]
    - [불변 조건 2]
  interfaces:
    - name: [인터페이스명]
      input: [입력 타입]
      output: [출력 타입]
      contract: [계약 조건]
  boundaries:
    - [경계 조건]
  layer_assignments:
    - component: [컴포넌트명]
      layer: [presentation|application|domain|infrastructure]
```

### 출력
Design Contract → `session.contracts.design_contract`에 저장

---

## 3. QA Engineer 에이전트 (Test First)

### 역할
테스트 계약 작성 및 테스트 코드 생성

### 주입할 컨텍스트
```yaml
context:
  - 공통 헤더
  - session.contracts.design_contract (Architect 산출물)
```

### 프롬프트 템플릿
```
{{공통 헤더}}

[Design Contract]
{{session.contracts.design_contract}}

[지시사항]
다음 작업을 수행하라:
1. Design Contract의 인터페이스별 테스트 케이스 설계
2. Given-When-Then 형식으로 테스트 명세
3. 경계값, 예외 케이스 포함
4. 테스트 코드 먼저 작성 (Red 상태 - 컴파일만 되고 실패해야 함)
5. Test Contract + 테스트 코드 출력

[출력 형식]
test_contract:
  task: [작업명]
  test_cases:
    - name: [테스트명]
      target: [테스트 대상 인터페이스]
      given: [전제 조건]
      when: [실행 동작]
      then: [기대 결과]
      category: [happy_path|edge_case|error_case]
  coverage_targets:
    - [커버리지 대상]
  test_file_path: [테스트 파일 경로]
```

### 출력
Test Contract → `session.contracts.test_contract`에 저장

---

## 4. Implementer 에이전트

### 역할
테스트 통과를 위한 구현

### 주입할 컨텍스트
```yaml
context:
  - 공통 헤더
  - session.contracts.design_contract (설계 불변 조건)
  - session.contracts.test_contract (통과해야 할 테스트)
  - 테스트 코드 파일 전문
```

### 프롬프트 템플릿
```
{{공통 헤더}}

[Design Contract - 설계 불변 조건]
{{session.contracts.design_contract}}

[Test Contract - 통과해야 할 테스트]
{{session.contracts.test_contract}}

[테스트 코드]
{{test_file_content}}

[지시사항]
다음 작업을 수행하라:
1. 테스트 통과만을 목표로 최소 구현
2. 설계 불변 조건 준수
3. 스코프 확장 금지 (Design Brief의 scope_out 항목 구현 금지)
4. 구현 코드 출력

[구현 시 주의사항]
- 테스트가 요구하지 않는 기능 추가 금지
- 불필요한 추상화 금지
- 설계 불변 조건 위반 시 즉시 중단하고 보고
```

### 출력
구현 코드

---

## 5. QA Engineer 에이전트 (Verification)

### 역할
테스트 실행 및 검증

### 주입할 컨텍스트
```yaml
context:
  - session.contracts.test_contract
  - session.contracts.design_contract (설계 불변 조건 검증용)
```

### 프롬프트 템플릿
```
[Test Contract]
{{session.contracts.test_contract}}

[Design Contract - 불변 조건]
{{session.contracts.design_contract.invariants}}

[지시사항]
다음 작업을 수행하라:
1. 테스트 실행 (./gradlew test 또는 npm test 등)
2. 테스트 결과 분석
3. 실패 시 원인 분석 및 분류
   - implementation_error: 구현 버그
   - design_violation: 설계 불변 조건 위반
   - test_error: 테스트 자체 문제
4. 테스트 결과 리포트 출력

[출력 형식]
test_result:
  execution:
    command: [실행 명령]
    result: [PASS|FAIL]
  summary:
    total: [총 테스트 수]
    passed: [통과 수]
    failed: [실패 수]
  failed_tests:
    - name: [실패한 테스트명]
      reason: [실패 원인]
      category: [implementation_error|design_violation|test_error]
  recommendation:
    action: [COMPLETE|RETRY_IMPLEMENTATION|RETRY_DESIGN]
    reason: [사유]
```

### 출력
Test Result Report → `session.contracts.test_result`에 저장

---

## 컨텍스트 흐름 요약

```
┌──────────────────────────────────────────────────────────────────┐
│                         Session File                              │
│  ~/.claude/claude-devkit/sessions/{hash}.yaml                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐     ┌─────────────────────┐                 │
│  │  [Code Explore] │     │     [Planner]        │   ◀── 병렬 실행 │
│  │       │         │     │         │            │                 │
│  │       ▼         │     │         ▼            │                 │
│  │ explored_files  │     │ preliminary_design   │                 │
│  │     저장        │     │ _brief 저장          │                 │
│  └────────┬────────┘     └──────────┬───────────┘                 │
│           │                         │                             │
│           └────────────┬────────────┘                             │
│                        ▼                                          │
│              ┌─────────────────┐                                  │
│              │     [Merge]     │  ◀── 오케스트레이터 직접 수행   │
│              │        │        │                                  │
│              │        ▼        │                                  │
│              │  design_brief   │                                  │
│              │      저장       │                                  │
│              └────────┬────────┘                                  │
│                       │                                           │
│                       │ design_brief 주입                         │
│                       ▼                                           │
│              [Architect] ────▶ design_contract 저장              │
│                       │                                           │
│                       │ design_contract 주입                      │
│                       ▼                                           │
│              [QA Engineer] ──▶ test_contract 저장                │
│                       │                                           │
│                       │ design_contract + test_contract 주입      │
│                       ▼                                           │
│              [Implementer] ──▶ 구현 코드 작성                    │
│                       │                                           │
│                       │ test_contract 주입                        │
│                       ▼                                           │
│              [QA Engineer] ──▶ test_result 저장                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## 캐싱 전략

### 탐색 결과 캐싱
- Discovery 페이즈에서 탐색한 파일은 세션에 저장
- 이후 에이전트는 요약만 받고, 필요 시 직접 Read

### Contract 캐싱
- 각 페이즈 완료 후 Contract를 세션에 저장
- 다음 에이전트는 세션에서 이전 Contract를 읽어 사용

### 세션 만료
- 24시간 비활성 시 세션 만료
- `/orchestrator reset`으로 수동 초기화 가능