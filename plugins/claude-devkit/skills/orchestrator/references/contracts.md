# Contract 형식

오케스트레이터가 페이즈 간 전달하는 계약 문서 형식이다.
Contract는 3-tier 계층(Request → Task → Subtask)에 따라 파일로 저장된다.
상세 스키마는 [storage.md](storage.md)를 참조한다.

---

## 파일 저장 경로 (3-tier 구조)

```
.claude/orchestrator/sessions/{projectHash}/contracts/
└── {requestId}/                          # Request 레벨
    ├── explored.yaml                     # Code Explore 결과
    ├── task-breakdown.yaml               # Planner 결과 (Task/Subtask 분해)
    │
    └── {taskId}/                         # Task 레벨
        ├── design-brief.yaml             # Task 설계 정의서
        ├── design-contract.yaml          # Architect 결과
        │
        └── {subtaskId}/                  # Subtask 레벨
            ├── test-contract.yaml        # QA Engineer (Test) 결과
            └── test-result.yaml          # QA Engineer (Verification) 결과
```

**예시 경로:**
```
contracts/R1/explored.yaml                     # Request 레벨
contracts/R1/task-breakdown.yaml
contracts/R1/T1/design-brief.yaml              # Task 레벨
contracts/R1/T1/design-contract.yaml
contracts/R1/T1/T1-S1/test-contract.yaml       # Subtask 레벨
contracts/R1/T1/T1-S1/test-result.yaml
```

---

## Task Breakdown (Request 레벨)

Planner 에이전트가 사용자 요청을 Task/Subtask로 분해한 결과.
저장 경로: `contracts/{requestId}/task-breakdown.yaml`

### 형식

```yaml
version: 1
request_id: R1
created_at: 2024-01-15T10:00:00
created_by: planner

original_request: "XX컨트롤러 구현해줘"
objective: "XX 기능 전체 구현"

tasks:
  - id: T1
    name: "a API 구현"
    objective: "a 기능 API 엔드포인트 구현"
    subtasks:
      - id: T1-S1
        name: "AController 구현"
        description: "a 기능 엔드포인트 (내부에서 TDD 적용)"
      - id: T1-S2
        name: "AService 구현"
        description: "a 비즈니스 로직 (내부에서 TDD 적용)"

  - id: T2
    name: "b API 구현"
    objective: "b 기능 API 엔드포인트 구현"
    subtasks:
      - id: T2-S1
        name: "BController 구현"
        description: "b 기능 엔드포인트 (내부에서 TDD 적용)"

assumptions:
  - "인증 관련 코드는 auth/ 디렉토리에 있을 것"
  - "Spring Security를 사용 중일 것"

task_order: ["T1", "T2"]
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| request_id | 요청 ID (R1, R2, ...) |
| original_request | 원본 사용자 요청 |
| objective | 전체 달성 목표 |
| tasks | Task 목록 |
| tasks[].id | Task ID (T1, T2, ...) |
| tasks[].subtasks | Subtask 목록 |
| tasks[].subtasks[].id | Subtask ID (T1-S1, T1-S2, ...) |
| **assumptions** | 코드 구조에 대한 가정 목록 (필수) |
| task_order | Task 실행 순서 |

---

## Design Brief (Task 레벨)

Task별 설계 정의서. task-breakdown + explored를 기반으로 생성.
저장 경로: `contracts/{requestId}/{taskId}/design-brief.yaml`

### 형식

```yaml
version: 1
request_id: R1
task_id: T1
created_at: 2024-01-15T10:05:00
created_by: orchestrator

task_name: "a API 구현"
objective: "a 기능 API 엔드포인트 구현"

subtasks:
  - id: T1-S1
    name: "API 스펙 확인"
  - id: T1-S2
    name: "테스트 작성"
  - id: T1-S3
    name: "컨트롤러 구현"

completion_criteria:
  - "API 엔드포인트 동작"
  - "테스트 통과"

scope_in:
  - "GET /api/a 엔드포인트"
  - "AController 클래스"

scope_out:
  - "인증 로직"

file_refs:
  - entity: "AController"
    path: "src/main/java/com/example/controller/AController.java"
    status: "to_create"

subtask_order: ["T1-S1", "T1-S2", "T1-S3"]
```

### file_refs status

| status | 설명 |
|--------|------|
| exists | 이미 존재하는 파일 |
| to_create | 새로 생성할 파일 |
| to_modify | 수정할 파일 |

---

## Design Contract (Task 레벨)

Architect → QA Engineer/Implementer로 전달되는 설계 명세서.
저장 경로: `contracts/{requestId}/{taskId}/design-contract.yaml`

### 형식

```yaml
version: 1
request_id: R1
task_id: T1
created_at: 2024-01-15T10:15:00
created_by: architect

task_name: "a API 구현"

invariants:
  - id: INV-1
    rule: "도메인 레이어는 인프라에 의존하지 않는다"
  - id: INV-2
    rule: "모든 비즈니스 로직은 Service를 통해 처리한다"

interfaces:
  - name: "AService.getData"
    input:
      type: "ARequest"
      fields:
        - name: "id"
          type: "string"
    output:
      type: "Result<AResponse, AError>"
    contract: "유효한 ID로 데이터 조회"

boundaries:
  - from: "AController"
    to: "AService"
    allowed: true
  - from: "AService"
    to: "ARepository"
    allowed: true
    note: "인터페이스만 의존"

layer_assignments:
  - component: "AController"
    layer: "presentation"
  - component: "AService"
    layer: "application"

file_refs:
  - entity: "AController"
    path: "src/main/java/com/example/controller/AController.java"
    status: "to_create"
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| request_id | 요청 ID |
| task_id | 작업 ID |
| invariants | 절대 위반 불가 규칙 |
| interfaces | 공개 인터페이스 계약 |
| boundaries | 의존성 경계 규칙 |
| file_refs | 관련 파일 참조 |

---

## Test Contract (Subtask 레벨)

QA Engineer → Implementer로 전달되는 테스트 명세서.
저장 경로: `contracts/{requestId}/{taskId}/{subtaskId}/test-contract.yaml`

### 형식

```yaml
version: 1
request_id: R1
task_id: T1
subtask_id: T1-S2
created_at: 2024-01-15T10:30:00
created_by: qa-engineer

subtask_name: "테스트 작성"

test_cases:
  - id: TC-1
    name: "유효한_ID로_데이터_조회_성공"
    target: "AService.getData"
    given: "존재하는 ID"
    when: "getData(ARequest) 호출"
    then: "AResponse 반환"
    category: "happy_path"

  - id: TC-2
    name: "존재하지_않는_ID로_조회_실패"
    target: "AService.getData"
    given: "존재하지 않는 ID"
    when: "getData(ARequest) 호출"
    then: "AError 반환"
    category: "error_case"

coverage_targets:
  - "AService.getData"
  - "AController.handleGet"

test_file_path: "src/test/java/com/example/service/AServiceTest.java"
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| request_id | 요청 ID |
| task_id | 작업 ID |
| subtask_id | 하위작업 ID |
| subtask_name | 하위작업명 |
| test_cases | 테스트 케이스 목록 |
| test_file_path | 테스트 파일 경로 |

### 테스트 카테고리

| 카테고리 | 설명 |
|----------|------|
| happy_path | 정상 흐름 |
| error_case | 예외/에러 흐름 |
| edge_case | 경계값, 특수 케이스 |

---

## Test Result (Subtask 레벨)

QA Engineer (Verification) → Orchestrator로 전달되는 테스트 결과.
저장 경로: `contracts/{requestId}/{taskId}/{subtaskId}/test-result.yaml`

### 형식

```yaml
version: 1
request_id: R1
task_id: T1
subtask_id: T1-S2
created_at: 2024-01-15T11:00:00
created_by: qa-engineer

execution:
  command: "./gradlew test"
  timestamp: "2024-01-15T11:00:00"
  result: "pass"  # pass | fail

summary:
  total: 2
  passed: 2
  failed: 0
  skipped: 0

failed_tests: []
# 실패 시:
# - id: TC-2
#   name: 존재하지_않는_ID로_조회_실패
#   reason: "Expected AError but got NullPointerException"
#   category: implementation_error

recommendation:
  action: "complete"  # complete | retry_implementation | retry_design
  reason: "모든 테스트 통과"
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| request_id | 요청 ID |
| task_id | 작업 ID |
| subtask_id | 하위작업 ID |
| execution | 실행 정보 |
| summary | 결과 요약 |
| recommendation | 다음 단계 권장 |

### recommendation.action

| 값 | 의미 | 조건 |
|----|------|------|
| complete | Subtask 완료 | 모든 테스트 통과 |
| retry_implementation | 구현 재시도 | implementation_error 발생 |
| retry_design | Task 설계 재검토 | design_violation 발생 |

---

## 관련 문서

- [storage.md](storage.md) - 파일 저장소 구조 및 스키마
- [agent-prompts.md](agent-prompts.md) - 프롬프트 템플릿
- [context-injection.md](context-injection.md) - 컨텍스트 조회 방법
- [error-recovery.md](error-recovery.md) - 테스트 실패 시 복구
