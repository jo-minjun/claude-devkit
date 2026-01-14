# 에이전트 프롬프트 템플릿

각 에이전트 호출 시 사용하는 프롬프트 템플릿을 정의한다.
컨텍스트 조회 및 주입 방법은 [context-injection.md](context-injection.md)를 참조한다.

---

## 공통 헤더

모든 에이전트에 주입되는 세션 컨텍스트:

```
═══════════════════════════════════════════════════════════════
[세션 컨텍스트]
- 프로젝트: {{project_path}}
- Request ID: {{request.id}}
- 현재 Task: {{current_task.id}} - {{current_task.name}}
{{#if current_subtask}}
- 현재 Subtask: {{current_subtask.id}} - {{current_subtask.name}}
{{/if}}
- 현재 페이즈: {{current_phase}}

[프로젝트 매니페스트]
- CLAUDE.md: {{project_manifest.claude_md}}
- AGENTS.md: {{project_manifest.agents_md}}
═══════════════════════════════════════════════════════════════

[탐색된 파일 요약]
{{#each explored_files}}
- {{path}}: {{summary}}
{{/each}}

상세 내용 필요 시 Read 도구로 직접 조회하세요.
프로젝트 규칙 확인 필요 시 CLAUDE.md를 읽으세요. (null이면 기존 코드 패턴만 따름)
═══════════════════════════════════════════════════════════════
```

---

## 0. Code Explore 에이전트

### 역할
프로젝트 구조 파악 및 주요 파일 요약 (Request 레벨)

### 프롬프트 템플릿

```
프로젝트 구조를 파악하고 주요 파일을 요약해줘.

[프로젝트 경로]
{{project_path}}

{{#if reference_path}}
[참고 프로젝트]
{{reference_path}}
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

---

## 1. Planner 에이전트 (Global Discovery용)

### 역할
사용자 요청을 Task/Subtask로 분해 (Request 레벨)

### 프롬프트 템플릿

```
[프로젝트 정보]
- 경로: {{project_path}}
{{#if claudemd_content}}
- 프로젝트 설정:
{{claudemd_content}}
{{/if}}

[사용자 요청]
{{user_request}}

[지시사항]
다음 작업을 수행하라:
1. 요청을 분석하여 Task와 Subtask로 분해
2. 각 Task의 목표와 완료 조건 정의
3. 각 Subtask의 범위와 설명 작성
4. **코드 구조를 모르므로 가정(assumptions)을 명시적으로 기록**
5. Task Breakdown을 다음 형식으로 출력

[분해 규칙 - 필수]
- 테스트를 별도 Subtask로 분리하지 말 것
- 각 Subtask는 자체적으로 Test First → Implementation → Verification을 실행
- "테스트 작성", "단위 테스트", "테스트 검증" 등의 Subtask 금지
- Subtask는 구현 단위(클래스, 모듈, 기능)로 분해

[출력 형식]
task_breakdown:
  request_id: "R1"
  original_request: "[사용자 원본 요청]"
  objective: "[전체 달성 목표]"

  tasks:
    - id: "T1"
      name: "[작업명]"
      objective: "[작업 목표]"
      subtasks:
        - id: "T1-S1"
          name: "[하위작업명]"
          description: "[하위작업 설명]"
        - id: "T1-S2"
          name: "[하위작업명]"
          description: "[하위작업 설명]"

    - id: "T2"
      name: "[작업명]"
      objective: "[작업 목표]"
      subtasks:
        - id: "T2-S1"
          name: "[하위작업명]"
          description: "[하위작업 설명]"

  assumptions:  # 필수 - 코드 구조에 대한 가정
    - "[가정 1: 예상되는 파일 위치, 기존 구조 등]"
    - "[가정 2: ...]"

  task_order: ["T1", "T2"]
```

---

## 2. Architect 에이전트

### 역할
Task 레벨에서 설계 확정 및 불변 조건 정의

### 프롬프트 템플릿

```
{{공통 헤더}}

[Design Brief]
경로: contracts/{{request_id}}/{{task_id}}/design-brief.yaml
{{design_brief 내용}}

[프로젝트 지식]
{{knowledge 내용}}

[과거 맥락 - claude-mem 검색 결과]
{{#if mem_context}}
다음은 이전 세션에서 검색된 관련 설계 결정입니다:

{{mem_context}}

위 내용을 참고하되, 현재 요구사항에 맞게 판단하세요.
{{else}}
(이전 설계 결정 없음 - 새로운 결정을 내려주세요)
{{/if}}

[지시사항]
다음 작업을 수행하라:
1. Design Brief를 바탕으로 설계 확정
2. 의존성 방향 규칙 준수 (도메인 → 외부 의존 금지)
3. 인터페이스 계약 정의
4. 설계 불변 조건 명시
5. Design Contract를 다음 형식으로 출력

[출력 형식]
design_contract:
  request_id: "{{request_id}}"
  task_id: "{{task_id}}"
  task_name: "[작업명]"
  invariants:
    - id: "INV-1"
      rule: "[불변 조건 1]"
    - id: "INV-2"
      rule: "[불변 조건 2]"
  interfaces:
    - name: "[인터페이스명]"
      input:
        type: "[입력 타입]"
        fields:
          - name: "[필드명]"
            type: "[타입]"
      output:
        type: "[출력 타입]"
      contract: "[계약 조건]"
  boundaries:
    - from: "[컴포넌트A]"
      to: "[컴포넌트B]"
      allowed: true|false
      note: "[설명]"
  layer_assignments:
    - component: "[컴포넌트명]"
      layer: [presentation|application|domain|infrastructure]
```

---

## 3. QA Engineer 에이전트 (Test First)

### 역할
Subtask 레벨에서 테스트 계약 작성 및 테스트 코드 생성

### 프롬프트 템플릿

```
{{공통 헤더}}

[Design Contract]
경로: contracts/{{request_id}}/{{task_id}}/design-contract.yaml
{{design_contract 내용}}

[현재 Subtask]
- ID: {{subtask_id}}
- 이름: {{subtask_name}}
- 설명: {{subtask_description}}

[지시사항]
다음 작업을 수행하라:
1. 현재 Subtask 범위 내에서 테스트 케이스 설계
2. Design Contract의 관련 인터페이스별 테스트 명세
3. Given-When-Then 형식으로 테스트 명세
4. 경계값, 예외 케이스 포함
5. 테스트 코드 먼저 작성 (Red 상태 - 컴파일만 되고 실패해야 함)
6. Test Contract + 테스트 코드 출력

[출력 형식]
test_contract:
  request_id: "{{request_id}}"
  task_id: "{{task_id}}"
  subtask_id: "{{subtask_id}}"
  subtask_name: "[하위작업명]"
  test_cases:
    - id: "TC-1"
      name: "[테스트명]"
      target: "[테스트 대상 인터페이스]"
      given: "[전제 조건]"
      when: "[실행 동작]"
      then: "[기대 결과]"
      category: [happy_path|edge_case|error_case]
  coverage_targets:
    - "[커버리지 대상]"
  test_file_path: "[테스트 파일 경로]"
```

---

## 4. Implementer 에이전트

### 역할
Subtask 레벨에서 테스트 통과를 위한 구현

### 프롬프트 템플릿

```
{{공통 헤더}}

[Design Contract - 설계 불변 조건]
경로: contracts/{{request_id}}/{{task_id}}/design-contract.yaml
{{design_contract 내용}}

[Test Contract - 통과해야 할 테스트]
경로: contracts/{{request_id}}/{{task_id}}/{{subtask_id}}/test-contract.yaml
{{test_contract 내용}}

[테스트 코드]
{{test_file_content}}

[프로젝트 주의사항]
{{pitfalls 내용}}

[과거 실패 기록 - claude-mem 검색 결과]
{{#if mem_context}}
다음은 이전 세션에서 발생한 관련 문제입니다:

{{mem_context}}

위 실패 패턴을 피해서 구현하세요.
{{else}}
(이전 실패 기록 없음)
{{/if}}

[현재 Subtask]
- ID: {{subtask_id}}
- 이름: {{subtask_name}}

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

[출력 형식]
implementation_result:
  request_id: "{{request_id}}"
  task_id: "{{task_id}}"
  subtask_id: "{{subtask_id}}"
  subtask_name: "[하위작업명]"
  files_changed:
    - path: "[파일 경로]"
      action: "created|modified"
      summary: "[변경 내용 요약]"
  build_status: "pass|fail"
```

---

## 5. QA Engineer 에이전트 (Verification)

### 역할
Subtask 레벨에서 테스트 실행 및 검증

### 프롬프트 템플릿

```
[Test Contract]
경로: contracts/{{request_id}}/{{task_id}}/{{subtask_id}}/test-contract.yaml
{{test_contract 내용}}

[Design Contract - 불변 조건]
경로: contracts/{{request_id}}/{{task_id}}/design-contract.yaml
{{design_contract.invariants}}

[현재 Subtask]
- ID: {{subtask_id}}
- 이름: {{subtask_name}}

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
  request_id: "{{request_id}}"
  task_id: "{{task_id}}"
  subtask_id: "{{subtask_id}}"
  subtask_name: "[하위작업명]"
  execution:
    command: "[실행 명령]"
    timestamp: "[실행 시각]"
    result: [pass|fail]
  summary:
    total: [총 테스트 수]
    passed: [통과 수]
    failed: [실패 수]
    skipped: [스킵 수]
  failed_tests:
    - id: "[TC-ID]"
      name: "[실패한 테스트명]"
      reason: "[실패 원인]"
      category: [implementation_error|design_violation|test_error]
  recommendation:
    action: [complete|retry_implementation|retry_design]
    reason: "[사유]"
```

---

## 관련 문서

- [context-injection.md](context-injection.md) - 컨텍스트 조회 및 주입 방법
- [contracts.md](contracts.md) - Contract YAML 형식
- [storage.md](storage.md) - 파일 저장소 구조
