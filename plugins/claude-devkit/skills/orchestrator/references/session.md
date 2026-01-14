# 세션 관리 (파일 기반)

오케스트레이터는 파일 시스템을 통해 세션 상태를 관리한다.
3-tier 계층 구조 (Request → Task → Subtask)를 기반으로 한다.
claude-mem은 자동 캡처된 이력 검색에만 보조적으로 사용한다.

---

## 저장소

| 항목 | 저장소 | 파일 |
|------|--------|------|
| 세션 메타데이터 | 파일 | session.json |
| 작업 상태 | 파일 | state.json (version 2) |
| Contract | 파일 | contracts/{requestId}/{taskId}/{subtaskId}/*.yaml |
| 프로젝트 지식 | 파일 | knowledge.yaml |
| 실행 이력 | claude-mem | 자동 캡처 |

**저장 경로**: `{project_root}/.claude/orchestrator/sessions/{project-hash}/`

상세: [storage.md](storage.md)

---

## 세션 라이프사이클

**중요**: 아래 세션 라이프사이클은 반드시 지켜야 한다.

### 1. 새 세션 시작 (`/orchestrator`)

```
동작:
  1. 세션 디렉토리 확인
     경로: .claude/orchestrator/sessions/{hash}/session.json

  2. session.json 존재 확인
     - 존재하고 status=active → 재개 여부 질문
     - 존재하지 않음 → 새 세션 생성

  3. 새 세션 생성
     - session.json 생성
     - state.json 생성 (version: 2, 빈 tasks)
     - contracts/ 디렉토리 생성

  4. Global Discovery 실행
     - Code Explore + Planner 병렬 실행
     - 결과를 contracts/{requestId}/ 에 저장
       - explored.yaml
       - task-breakdown.yaml

  5. Merge 실행
     - task-breakdown + explored 병합
     - Task별 design-brief.yaml 생성
     - state.json 초기화 (tasks, task_order)
```

**session.json 초기값:**
```json
{
  "version": 1,
  "project": {
    "path": "/absolute/path/to/project",
    "name": "my-project",
    "hash": "a1b2c3d4"
  },
  "status": "active",
  "current_task": "T1",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "manifest": {
    "claude_md": null,
    "agents_md": null
  }
}
```

**state.json 초기값 (version 2):**
```json
{
  "version": 2,
  "request": {
    "id": "R1",
    "original_request": "[사용자 요청]",
    "status": "active",
    "current_task": "T1",
    "global_phase": "task_loop"
  },
  "tasks": {
    "T1": {
      "name": "[작업명]",
      "status": "in_progress",
      "current_subtask": "T1-S1",
      "subtasks": {
        "T1-S1": {
          "name": "[하위작업명]",
          "status": "in_progress",
          "phase": "test_first",
          "gates": {}
        }
      },
      "subtask_order": ["T1-S1", "T1-S2"]
    }
  },
  "task_order": ["T1", "T2"]
}
```

---

### 2. 세션 재개 (`/orchestrator resume`)

```
동작:
  1. 세션 디렉토리 스캔
     경로: .claude/orchestrator/sessions/*/session.json

  2. 세션 목록 표시
     - 프로젝트 이름, 현재 Task/Subtask, 페이즈, 상태
     - 최근 업데이트 순 정렬

  3. 사용자 선택

  4. 선택된 세션 로드
     - session.json 읽기
     - state.json에서 현재 Task/Subtask/phase 확인
     - contracts/ 에서 이전 Contract 로드

  5. 중단된 Subtask의 phase부터 재개
```

**표시 형식:**
```
┌─────────────────────────────────────────────────────┐
│ 이전 세션 목록                                       │
├─────────────────────────────────────────────────────┤
│ [1] my-project                                       │
│     Request: XX컨트롤러 구현해줘                     │
│     T2 > S1 Service (implementation) 🔄             │
│     2024-01-15 10:30                                │
│                                                      │
│ [2] other-project                                    │
│     Request: 인증 기능 추가                          │
│     T1 > S3 Repository (complete) ✅                │
│     2024-01-14 15:00                                │
│                                                      │
│ 번호를 선택하세요:                                   │
└─────────────────────────────────────────────────────┘
```

---

### 3. 페이즈 전환

```
동작:
  1. 현재 페이즈 완료 조건 확인

  2. state.json 업데이트
     - Subtask phase 변경
     - gate 상태 업데이트
     - updated_at 갱신

  3. 다음 에이전트 호출에 필요한 Contract 파일 확인
     - 없으면 이전 페이즈로 롤백

  4. 다음 에이전트 호출
```

**state.json 업데이트 예시:**
```json
{
  "version": 2,
  "request": {
    "id": "R1",
    "current_task": "T1",
    "global_phase": "task_loop"
  },
  "tasks": {
    "T1": {
      "status": "in_progress",
      "current_subtask": "T1-S2",
      "subtasks": {
        "T1-S1": {
          "status": "completed",
          "phase": "complete",
          "gates": {
            "GATE-1": "passed",
            "GATE-2": "passed"
          }
        },
        "T1-S2": {
          "status": "in_progress",
          "phase": "implementation",
          "gates": {
            "GATE-1": "passed",
            "GATE-2": "pending"
          }
        }
      }
    }
  }
}
```

---

### 4. Contract 저장

```
동작:
  1. 에이전트가 Contract 내용 생성

  2. 파일로 저장 (3-tier 경로)
     - Request 레벨: contracts/{requestId}/explored.yaml
     - Task 레벨: contracts/{requestId}/{taskId}/design-contract.yaml
     - Subtask 레벨: contracts/{requestId}/{taskId}/{subtaskId}/test-contract.yaml

  3. state.json의 updated_at 갱신

예시:
  - Planner 결과 → contracts/R1/task-breakdown.yaml
  - Architect 결과 → contracts/R1/T1/design-contract.yaml
  - QA 결과 → contracts/R1/T1/T1-S1/test-contract.yaml
```

---

### 5. Task/Subtask 완료 전환

```
Subtask 완료:
  1. test-result.yaml의 action이 "complete"
  2. Subtask status → "completed", phase → "complete"
  3. 다음 Subtask가 있으면 current_subtask 변경
  4. 없으면 Task 완료 확인

Task 완료:
  1. 모든 Subtask가 "completed" 상태
  2. Task status → "completed"
  3. 다음 Task가 있으면 current_task 변경
  4. 없으면 Request 완료 확인

Request 완료:
  1. 모든 Task가 "completed" 상태
  2. request.status → "completed"
  3. session.json status → "completed"
```

---

### 6. 세션 종료

```
조건:
  - 모든 Task/Subtask 완료
  - 사용자 명시적 종료 (/orchestrator stop)

동작:
  1. session.json 업데이트
     - status: "completed" 또는 "stopped"
     - updated_at 갱신

  2. **자동 지식 축적** (세션 완료 시)
     - design-contract.yaml에서 설계 결정 추출 → knowledge.yaml decisions에 추가
     - test-result.yaml에서 실패 후 성공 패턴 추출 → pitfalls에 추가
     - updated_at 갱신
```

### 7. 지식 자동 업데이트

| 시점 | 동작                             |
|------|--------------------------------|
| Task 완료 | design-contract에서 decisions 추출 |
| Subtask 재시도 후 성공 | 실패 원인을 pitfalls에 추가            |
| 세션 종료 | 전체 Contract 스캔 후 누락된 지식 병합     |
| 세션 종료 | claude-mem 스캔 후 핵심 지식 병합       |

상세: [knowledge.md](knowledge.md)

---

## 명령어

| 명령 | 동작 |
|------|------|
| `/orchestrator` | session.json 확인 → 새 세션 또는 재개 |
| `/orchestrator status` | session.json + state.json 읽어서 상태 출력 |
| `/orchestrator resume` | 세션 디렉토리 스캔 → 목록 표시 → 선택 재개 |
| `/orchestrator reset` | session.json status를 completed로 변경 |
| `/orchestrator stop` | session.json status를 stopped로 변경 |

---

## 파일 조회 방법

### 세션 존재 확인
```
Read: .claude/orchestrator/sessions/{hash}/session.json

존재하면 → 세션 있음
존재하지 않으면 → 새 세션 필요
```

### 현재 상태 확인
```
Read: .claude/orchestrator/sessions/{hash}/state.json

request.current_task → 현재 Task
tasks.{taskId}.current_subtask → 현재 Subtask
tasks.{taskId}.subtasks.{subtaskId}.phase → 현재 페이즈
tasks.{taskId}.subtasks.{subtaskId}.gates → 게이트 상태
```

### Contract 조회
```
Request 레벨:
  Read: contracts/{requestId}/explored.yaml
  Read: contracts/{requestId}/task-breakdown.yaml

Task 레벨:
  Read: contracts/{requestId}/{taskId}/design-brief.yaml
  Read: contracts/{requestId}/{taskId}/design-contract.yaml

Subtask 레벨:
  Read: contracts/{requestId}/{taskId}/{subtaskId}/test-contract.yaml
  Read: contracts/{requestId}/{taskId}/{subtaskId}/test-result.yaml

파일 존재하면 → Contract 있음
파일 없으면 → 이전 에이전트 실패 또는 미완료
```

---

## claude-mem 보조 활용

파일 기반 저장이 primary이지만, claude-mem의 자동 캡처 기능은 다음 용도로 활용:

### 실행 맥락 검색
```
search: "my-project 인증 결정 이유"
→ 왜 이런 설계를 했는지 과거 맥락 확인
```

### 코드 탐색 이력
```
search: "my-project 파일 구조 탐색"
→ 이전 탐색에서 발견한 내용 참조
```

### 실패 패턴 검색
```
search: "my-project 테스트 실패"
→ 이전 세션에서 실패한 케이스 확인
```

---

## 예외 처리

### 파일 손상
```
session.json 또는 state.json 파싱 실패 시:
  1. 백업 파일 확인 (*.bak)
  2. 없으면 사용자에게 알림
  3. 새 세션으로 시작 제안
```

### Contract 누락
```
다음 페이즈에 필요한 Contract 파일 없음:
  1. 이전 페이즈로 롤백
  2. 해당 에이전트 재실행
```

### 중복 세션
```
같은 프로젝트에 active 세션이 여러 개:
  1. 가장 최근 세션 선택
  2. 나머지는 stopped로 변경
```

---

## 관련 문서

- [storage.md](storage.md) - 파일 저장소 구조 및 스키마
- [contracts.md](contracts.md) - Contract 형식
- [error-recovery.md](error-recovery.md) - 에러 복구 전략
- [context-injection.md](context-injection.md) - 컨텍스트 조회 방법
