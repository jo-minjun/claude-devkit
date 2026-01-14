---
name: orchestrator
description: TDD 기반 개발 오케스트레이터. 기능 추가, 기능 변경, 기능 구현 요청 시 자동 발동한다. "~해줘", "~만들어줘", "~추가해줘", "~구현해줘", "~개발해줘", "~변경해줘", "~수정해줘" 같은 코드 변경 요청에 트리거된다. Planner, Architect, QA Engineer, Implementer를 조율하여 테스트 우선 개발 루프를 실행하고, 작업 완료까지 자동으로 진행한다.
---

# TDD 오케스트레이터

서브에이전트를 3-tier 계층(Request → Task → Subtask)으로 조율하여 TDD 기반 개발 루프를 실행한다.

## 핵심 원칙

**중요**: 아래 원칙들은 **반드시** 지켜져야 한다. 위반시 다음 단계로 진행이 불가능하다.

1. **3-tier 계층**: Request → Task → Subtask 단위로 작업 분해
2. **Subtask 단위 TDD**: Mini TDD Loop은 Subtask 단위에서 적용
3. **계약 기반**: 페이즈 간 Contract로 정보 전달
4. **게이트 통제**: 조건 미충족 시 다음 단계 차단
5. **완료까지 자동 진행**: 모든 Task가 완료될 때까지 멈추지 않음
6. **파일 기반**: 세션 상태와 Contract는 **반드시** 파일 시스템에 저장

## 필수 파일 생성 규칙

**중요**: 아래 파일들은 각 단계에서 **반드시** 생성해야 한다. 파일 생성을 생략하고 다음 단계로 진행하면 안 된다.

| 단계 | 필수 생성 파일 | 생성 시점 |
|------|---------------|----------|
| 세션 시작 | session.json, state.json | `/orchestrator` 실행 직후 |
| Global Discovery | explored.yaml, task-breakdown.yaml | Agent 완료 직후 |
| Task Design | design-brief.yaml, design-contract.yaml | Architect 완료 직후 |
| Test First | test-contract.yaml | QA Engineer 완료 직후 |
| Verification | test-result.yaml | 테스트 실행 직후 |

**위반 시 동작**: 파일이 생성되지 않으면 다음 단계로 진행할 수 없다.

## Subtask 분해 규칙

**중요**: Subtask는 TDD 루프(Test First → Implementation → Verification)가 적용되는 단위이다.

### 올바른 분해
각 Subtask가 자체적으로 Mini TDD Loop을 실행한다:
```
T1-S1: UserService 구현
  └─ Test First → Implementation → Verification
T1-S2: UserController 구현
  └─ Test First → Implementation → Verification
```

### 잘못된 분해 (금지)
테스트를 별도 Subtask로 분리하면 안 된다:
```
T1-S1: UserService 구현      ← 테스트 없이 구현
T1-S2: UserController 구현   ← 테스트 없이 구현
T1-S3: 단위 테스트 작성      ← ❌ 잘못됨! 테스트가 별도 Subtask
```

**위반 시**: Planner에게 재분해 요청

## 3-tier 계층 모델

```
Request (요청) - R1
  ├── Task A (작업) - T1
  │   ├── Subtask 1 (하위작업) - T1-S1 → [Mini TDD 루프]
  │   ├── Subtask 2 (하위작업) - T1-S2 → [Mini TDD 루프]
  │   └── Subtask 3 (하위작업) - T1-S3 → [Mini TDD 루프]
  │
  └── Task B (작업) - T2
      ├── Subtask 1 - T2-S1 → [Mini TDD 루프]
      └── Subtask 2 - T2-S2 → [Mini TDD 루프]
```

### 각 계층의 역할

| 계층 | 식별자 | 역할 | 상태 |
|------|--------|------|------|
| **Request** | R1 | 사용자 원본 요청 | active/completed/stopped |
| **Task** | T1, T2 | 논리적 작업 단위 (설계 단위) | pending/in_progress/completed |
| **Subtask** | T1-S1 | TDD 루프 적용 단위 | pending/in_progress/completed/failed |

### 완료 조건

- **Subtask 완료**: Mini TDD Loop (Test → Impl → Verify) 통과
- **Task 완료**: 모든 Subtask 완료
- **Request 완료**: 모든 Task 완료

## 오케스트레이션 루프

```
┌────────────────────────────────────────────────────┐
│            GLOBAL DISCOVERY (한 번만)              │
│  Code Explore + Planner → task-breakdown.yaml      │
└────────────────────────┬───────────────────────────┘
                         ▼
         ┌───────────────────────────────┐
         │  For each Task (순차)          │
         │  ┌─────────────────────────┐  │
         │  │ Task Design (Architect) │  │
         │  └───────────┬─────────────┘  │
         │              ▼                 │
         │  ┌─────────────────────────┐  │
         │  │ For each Subtask        │  │
         │  │  ┌───────────────────┐  │  │
         │  │  │ Mini TDD Loop     │  │  │
         │  │  │ Test→Impl→Verify  │  │  │
         │  │  └───────────────────┘  │  │
         │  └─────────────────────────┘  │
         │              ▼                 │
         │        Task Complete           │
         └───────────────┬───────────────┘
                         ▼
                Request Complete
```

### Mini TDD Loop (Subtask 단위)

```
┌─────────────────────────────────────────┐
│           Mini TDD Loop                  │
│                                          │
│  Test First → Implementation → Verify    │
│       ↑                           │      │
│       └───────────────────────────┘      │
│              (실패 시 재시도)             │
└─────────────────────────────────────────┘
```

- Design은 Task 레벨에서 1회 수행
- 각 Subtask마다 Test → Impl → Verify 반복
- 실패 시 해당 Subtask만 재시도

## 세션 관리 (파일 기반)

오케스트레이터는 **파일 시스템**을 통해 세션 상태를 관리한다.
claude-mem은 자동 캡처된 이력 검색에만 보조적으로 사용한다.

### 저장소 구조

```
{project_root}/.claude/orchestrator/
├── sessions/{projectHash}/
│   ├── session.json                              # 세션 메타데이터
│   ├── state.json                                # 작업 상태 (3-tier)
│   └── contracts/
│       └── {requestId}/                          # Request 레벨
│           ├── explored.yaml                     # 프로젝트 탐색 결과
│           ├── task-breakdown.yaml               # Task/Subtask 분해
│           │
│           └── {taskId}/                         # Task 레벨
│               ├── design-brief.yaml             # 작업 정의서
│               ├── design-contract.yaml          # 설계 계약서
│               │
│               └── {subtaskId}/                  # Subtask 레벨
│                   ├── test-contract.yaml        # 테스트 계약서
│                   └── test-result.yaml          # 테스트 결과
│
└── knowledge/{projectHash}/
    └── knowledge.yaml                            # 프로젝트 지식
```

**예시 경로:**
```
contracts/R1/explored.yaml                        # Request 레벨
contracts/R1/task-breakdown.yaml
contracts/R1/T1/design-brief.yaml                 # Task 레벨
contracts/R1/T1/design-contract.yaml
contracts/R1/T1/T1-S1/test-contract.yaml          # Subtask 레벨
contracts/R1/T1/T1-S1/test-result.yaml
```

### 저장소 역할 분리

| 데이터 | 저장소 | 조회 방법 |
|--------|--------|----------|
| 세션 상태 | 파일 (session.json) | Read |
| 작업 상태 | 파일 (state.json) | Read |
| Contract | 파일 (*.yaml) | Read |
| 프로젝트 지식 | 파일 (knowledge.yaml) | Read |
| 과거 맥락 | claude-mem | search |

> 상세: [storage.md](references/storage.md), [session.md](references/session.md)

### 세션 정책

| 명령 | 동작 |
|------|------|
| `/orchestrator` | session.json 확인 → 새 세션 또는 재개 선택 |
| `/orchestrator resume` | 세션 디렉토리 스캔 → 목록 표시 → 선택 재개 |

### 세션 시작 (`/orchestrator`)

1. **세션 존재 확인**
   - `Read: .claude/orchestrator/sessions/{hash}/session.json`
   - 존재하고 status=active → 재개 여부 질문
   - 존재하지 않음 → 새 세션 생성

2. **프로젝트 지식 로드**
   - `Read: .claude/orchestrator/knowledge/{hash}/knowledge.yaml`
   - (보조) claude-mem search로 과거 맥락 검색

### claude-mem 검색 타이밍

오케스트레이터가 에이전트 호출 **전**에 트리거 조건을 확인하고 검색을 수행한다.

```
┌─────────────────────────────────────────────────────┐
│  에이전트 호출 전 (오케스트레이터 수행)               │
│                                                      │
│  1. 트리거 조건 확인                                 │
│     - 첫 세션 여부 (Architect)                       │
│     - 재시도 횟수 (Implementer: retry_count > 0)    │
│     - 테스트 실패 횟수 (QA: fail_count >= 2)        │
│                                                      │
│  2. 조건 충족 시 claude-mem search                   │
│     - 검색 결과를 mem_context에 저장                 │
│                                                      │
│  3. 프롬프트 템플릿에 주입                           │
│     - {{mem_context}} 변수 치환                      │
│                                                      │
│  4. 에이전트 호출                                    │
└─────────────────────────────────────────────────────┘
```

**트리거 조건:**
| 에이전트 | 조건 | 검색 쿼리 |
|----------|------|----------|
| Architect | 첫 세션 | `"{project_name} 설계 결정"` |
| Implementer | retry_count > 0 | `"{project_name} {subtask} 실패"` |
| QA Engineer | fail_count >= 2 | `"{project_name} 테스트 실패 패턴"` |

**Fallback:** claude-mem 미설치/검색 실패 시 경고 메시지 출력 후 파일 기반 지식만 사용

상세: [context-injection.md](references/context-injection.md)

### Global Discovery 페이즈 (Request 레벨, 1회)

1. **병렬 실행** (Code Explore + Planner 동시 실행)
   - **Agent A - Code Explore**: 프로젝트 구조 파악, 주요 파일 요약
   - **Agent B - Planner**: Task/Subtask 분해 (assumptions 포함)
   - 두 Agent 완료 대기

2. **결과 저장**
   - Code Explore 결과: `Write: contracts/{requestId}/explored.yaml`
   - Planner 결과: `Write: contracts/{requestId}/task-breakdown.yaml`
   - 상태 업데이트: `Write: state.json`

3. **Task 순회 시작**

## 에이전트 호출 순서

### Request 레벨 (1회)

| 순서 | 에이전트 | 역할 | 입력 | 출력 |
|------|---------|------|------|------|
| 0a | Code Explore | 프로젝트 탐색 | 프로젝트 경로 | explored.yaml |
| 0b | Planner | Task/Subtask 분해 | 사용자 요청 | task-breakdown.yaml |

### Task 레벨 (Task별 반복)

| 순서 | 에이전트 | 역할 | 입력 | 출력 |
|------|---------|------|------|------|
| 1 | Architect | Task 설계 | task-breakdown, explored | design-contract.yaml |

### Subtask 레벨 (Subtask별 반복 = Mini TDD Loop)

| 순서 | 에이전트 | 역할 | 입력 | 출력 |
|------|---------|------|------|------|
| 2 | QA Engineer | 테스트 작성 | design-contract | test-contract.yaml |
| 3 | Implementer | 구현 | design-contract + test-contract | 구현 코드 |
| 4 | QA Engineer | 테스트 실행 | test-contract + 구현 코드 | test-result.yaml |

> **Note**: 0a와 0b는 병렬로 실행됨. 순서 2-4는 각 Subtask마다 반복.

## Contract 체인

각 페이즈의 출력은 다음 페이즈의 입력으로 **자동 주입**된다.
Contract는 파일로 저장되며, 오케스트레이터가 Read로 조회하여 프롬프트에 주입한다.

```
┌──────────────────────────────────────────────────────────────────┐
│  REQUEST LEVEL (1회)                                              │
│  ┌─────────────┐           ┌─────────────┐                       │
│  │Code Explore │           │   Planner   │     ◀── 병렬 실행     │
│  │             │           │             │                       │
│  │explored.yaml│           │task-breakdown│                       │
│  │             │           │   .yaml      │                       │
│  └──────┬──────┘           └──────┬──────┘                       │
│         └───────────┬─────────────┘                              │
│                     ▼                                            │
│              contracts/{requestId}/                              │
└─────────────────────┬────────────────────────────────────────────┘
                      │
   ┌──────────────────┴──────────────────┐
   │  TASK LEVEL (Task별 반복)            │
   │                                      │
   │  ┌─────────────┐                     │
   │  │  Architect  │                     │
   │  │             │                     │
   │  │design-contract                    │
   │  │   .yaml     │                     │
   │  └──────┬──────┘                     │
   │         │ contracts/{requestId}/{taskId}/
   │         │                            │
   │  ┌──────┴───────────────────────┐    │
   │  │  SUBTASK LEVEL (Mini TDD)    │    │
   │  │                              │    │
   │  │  QA Engineer ──▶ Implementer │    │
   │  │  test-contract    구현 코드   │    │
   │  │       │              │       │    │
   │  │       └──────┬───────┘       │    │
   │  │              ▼               │    │
   │  │       QA Engineer            │    │
   │  │       test-result.yaml       │    │
   │  │                              │    │
   │  │  contracts/{requestId}/{taskId}/{subtaskId}/
   │  └──────────────────────────────┘    │
   │                                      │
   └──────────────────────────────────────┘
```

상세: [contracts.md](references/contracts.md), [agent-prompts.md](references/agent-prompts.md), [context-injection.md](references/context-injection.md)

## 상태 시각화

**매 페이즈 전환 시 자동 출력:**

```
╔══════════════════════════════════════════════════════════╗
║  TDD Orchestrator                                         ║
╠══════════════════════════════════════════════════════════╣
║  Request: XX컨트롤러 구현해줘                              ║
║  Global: Discovery ✅ ─▶ Merge ✅                         ║
╠══════════════════════════════════════════════════════════╣
║  Tasks                                                    ║
║  ├─ T1 a API 구현        🔄 in_progress                   ║
║  │   ├─ S1 API 스펙 확인     ✅ completed                 ║
║  │   ├─ S2 테스트 작성       🔄 in_progress  ← current    ║
║  │   │   └─ Test ✅ → Impl 🔄 → Verify ⏳                 ║
║  │   └─ S3 컨트롤러 구현     ⏳ pending                    ║
║  │                                                        ║
║  └─ T2 b API 구현        ⏳ pending                       ║
╠══════════════════════════════════════════════════════════╣
║  Progress: T1 [████░░░░] 1/3  │  Total [██░░░░░░] 1/6     ║
╚══════════════════════════════════════════════════════════╝
```

### 상태 아이콘

| 아이콘 | 의미 |
|--------|------|
| ✅ | 완료 (completed) |
| 🔄 | 진행 중 (in_progress) |
| ⏳ | 대기 (pending) |
| ❌ | 실패 (failed) |

### Subtask 진행 상태 (한 줄)

```
[T1-S2 테스트 작성] Test ✅ → Impl 🔄 → Verify ⏳
```

## 게이트 규칙 요약

| Gate | 조건 | 위반 시 |
|------|------|--------|
| GATE-1 | Test Contract 존재 | Implementation 차단 |
| GATE-2 | 테스트 결과 존재 | Complete 차단 |
| GATE-3 | 스코프 변경 없음 | Planning 복귀 |
| GATE-4 | 설계 불변 조건 유지 | Design 복귀 |

상세 규칙: [gate-rules.md](references/gate-rules.md)

## 명령어

| 명령 | 설명 |
|------|------|
| `/orchestrator` | 오케스트레이터 시작 |
| `/orchestrator status` | 현재 세션 상태 출력 |
| `/orchestrator resume` | 중단된 세션 재개 |
| `/orchestrator reset` | 세션 초기화 |
| `/orchestrator stop` | 세션 중지 |
| `/orchestrator learn` | 지식 축적 |

### /orchestrator learn

세션에서 학습한 내용을 프로젝트 지식으로 축적한다.

상세: [knowledge.md](references/knowledge.md)

## 실행 흐름

### 1. Global Discovery (Request 레벨)

```
1. 세션 파일 확인: Read .claude/orchestrator/sessions/{hash}/session.json
2. 새 세션이면:
   - session.json 생성
   - state.json 생성 (version: 2)
   - contracts/{requestId}/ 디렉토리 생성

3. 병렬로 두 Agent 호출:

   [Agent A: Code Explore]
   - prompt: "프로젝트 구조를 파악하고 주요 파일을 요약해줘"
   - subagent_type: "code-explore"

   [Agent B: Planner]
   - prompt: "[사용자 요청]\nTask/Subtask 분해 (assumptions 포함)"
   - subagent_type: "planner"

4. 결과 저장 (필수 - 생략 금지):
   - Write: contracts/{requestId}/explored.yaml ← 반드시 생성
   - Write: contracts/{requestId}/task-breakdown.yaml ← 반드시 생성

5. state.json 업데이트 (request.status=active, task_order 설정)
6. 첫 번째 Task 시작
```

### 2. Task Design (Task 레벨)

```
For each Task in task_order:

1. Read contracts/{requestId}/task-breakdown.yaml
2. Read contracts/{requestId}/explored.yaml
3. Read knowledge/{hash}/knowledge.yaml

4. Architect 호출 (해당 Task에 대한 설계)
5. Write contracts/{requestId}/{taskId}/design-brief.yaml ← 반드시 생성
6. Write contracts/{requestId}/{taskId}/design-contract.yaml ← 반드시 생성

7. state.json 업데이트:
   - tasks.{taskId}.status = "in_progress"
   - tasks.{taskId}.subtask_order 설정

8. 첫 번째 Subtask Mini TDD Loop 시작
```

### 3. Mini TDD Loop (Subtask 레벨)

```
For each Subtask in subtask_order:

  [Test First]
  1. Read contracts/{requestId}/{taskId}/design-contract.yaml
  2. QA Engineer 호출
  3. Write contracts/{requestId}/{taskId}/{subtaskId}/test-contract.yaml ← 반드시 생성
  4. GATE-1 검증 (test-contract.yaml 존재 확인)

  [Implementation]
  5. Read design-contract.yaml + test-contract.yaml
  6. Read knowledge/{hash}/knowledge.yaml (pitfalls)
  7. Implementer 호출
  8. GATE-3, GATE-4 검증

  [Verification]
  9. QA Engineer 호출 (테스트 실행)
  10. Write contracts/{requestId}/{taskId}/{subtaskId}/test-result.yaml ← 반드시 생성
  11. GATE-2 검증

  [결과 처리]
  12. PASS → 다음 Subtask로 진행
  13. FAIL (implementation_error) → Test First로 복귀
  14. FAIL (design_violation) → Task Design으로 복귀

  15. state.json 업데이트:
      - subtasks.{subtaskId}.status = "completed"
      - subtasks.{subtaskId}.phase = "complete"
```

### 4. Task Complete

```
모든 Subtask 완료 시:
1. state.json 업데이트:
   - tasks.{taskId}.status = "completed"
2. 다음 Task로 진행 (Task Design 단계로)
```

### 5. Request Complete

```
모든 Task 완료 시:
1. session.json 업데이트 (status=completed)
2. request.status = "completed"
3. 최종 상태 출력
4. (선택) /orchestrator learn 실행 제안
```

## 제약사항

- Request 완료 전까지 오케스트레이터는 멈추지 않음
- 한 번에 하나의 Subtask만 처리 (순차 실행)
- Contract 불완전 시 다음 단계 진행 금지
- 테스트 없이 구현 완료 불가 (각 Subtask마다 TDD 필수)
- 게이트 위반 시 해당 레벨로 복귀
- Task는 모든 Subtask 완료 시에만 완료 처리
- **세션/Contract 파일 생성은 필수** - 파일 생성 없이 구현만 진행하면 안 됨

## 참조 문서

| 문서 | 내용 |
|------|------|
| [storage.md](references/storage.md) | 파일 저장소 구조 및 스키마 |
| [session.md](references/session.md) | 세션 관리 (파일 기반) |
| [contracts.md](references/contracts.md) | Contract YAML 형식 |
| [agent-prompts.md](references/agent-prompts.md) | 에이전트별 프롬프트 템플릿 |
| [context-injection.md](references/context-injection.md) | 컨텍스트 조회 및 주입 로직 |
| [error-recovery.md](references/error-recovery.md) | 에러 처리 및 복구 전략 |
| [knowledge.md](references/knowledge.md) | 프로젝트 지식 관리, /orchestrator learn |
| [search-guide.md](references/search-guide.md) | claude-mem 검색 가이드 |
| [gate-rules.md](references/gate-rules.md) | 게이트 규칙 상세 |
| [phases.md](references/phases.md) | 페이즈별 상세 절차 |
