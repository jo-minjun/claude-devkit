---
name: orchestrator
description: TDD 기반 개발 오케스트레이터. 기능 추가, 기능 변경, 기능 구현 요청 시 자동 발동한다. "~해줘", "~만들어줘", "~추가해줘", "~구현해줘", "~개발해줘", "~변경해줘", "~수정해줘" 같은 코드 변경 요청에 트리거된다. Planner, Architect, QA Engineer, Implementer를 조율하여 테스트 우선 개발 루프를 실행하고, 작업 완료까지 자동으로 진행한다.
---

# TDD 오케스트레이터

서브에이전트를 작업 단위로 조율하여 TDD 기반 개발 루프를 실행한다.

## 핵심 원칙

1. **작업 단위**: 한 번에 하나의 작업만 처리
2. **계약 기반**: 페이즈 간 Contract로 정보 전달
3. **게이트 통제**: 조건 미충족 시 다음 단계 차단
4. **자동 루프**: 작업 완료까지 사용자 개입 없이 진행
5. **세션 유지**: 컨텍스트와 Contract를 세션 파일로 관리

## 오케스트레이션 루프

```
[Discovery] → Planning → Design → Test First → Implementation → Verification → Complete
                 ↑                                    │               │
                 └────────────────────────────────────┴───────────────┘
                             (테스트 실패 또는 게이트 위반 시 복귀)
```

## 세션 관리

오케스트레이터는 `~/.claude/claude-devkit/sessions/` 에 세션 파일을 관리한다.
세션 파일에는 프로젝트 정보, 작업 상태, Contract, 탐색 결과가 저장된다.

상세: [session.md](references/session.md)

### 세션 시작 시 (Discovery 페이즈)

오케스트레이터가 시작되면:

1. **세션 파일 확인/생성**
   ```yaml
   session:
     project_path: {{현재 작업 디렉토리}}
     reference_path: {{참고 프로젝트 경로, 있는 경우}}
     current_task: M1
     current_phase: discovery
   ```

2. **프로젝트 탐색** (code-explore 에이전트)
   - 디렉토리 구조 파악
   - 주요 파일 요약
   - 결과를 `explored_files`에 저장

3. **세션 컨텍스트 구성**
   - 이후 모든 서브에이전트에게 주입할 공통 정보 준비

## 에이전트 호출 순서

| 순서 | 에이전트 | 역할 | 입력 | 출력 |
|------|---------|------|------|------|
| 0 | Code Explore | 프로젝트 탐색 | 프로젝트 경로 | explored_files |
| 1 | Planner | 작업 정의 | 사용자 요청 + explored_files | Design Brief |
| 2 | Architect | 설계 확정 | Design Brief | Design Contract |
| 3 | QA Engineer | 테스트 작성 | Design Contract | Test Contract + 테스트 코드 |
| 4 | Implementer | 구현 | Design Contract + Test Contract | 구현 코드 |
| 5 | QA Engineer | 테스트 실행 | 구현 코드 + Test Contract | Test Result Report |

## Contract 체인

각 페이즈의 출력은 다음 페이즈의 입력으로 **자동 주입**된다.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Planner   │────▶│  Architect  │────▶│ QA Engineer │
│             │     │             │     │             │
│ Design Brief│     │Design Contract    │Test Contract│
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────┐            │
                    │ Implementer │◀───────────┘
                    │             │
                    │ 구현 코드    │──────▶ QA Engineer (Verification)
                    └─────────────┘
```

### 서브에이전트 호출 시 컨텍스트 주입 템플릿

**모든 에이전트 공통:**
```
[세션 컨텍스트]
- 프로젝트: {{session.project_path}}
- 참고: {{session.reference_path}}
- 현재 작업: {{session.current_task}}

[탐색된 파일 요약]
{{session.explored_files | summary}}
```

**Architect 호출 시 추가:**
```
[Design Brief]
{{session.contracts.design_brief}}
```

**QA Engineer (Test First) 호출 시 추가:**
```
[Design Contract]
{{session.contracts.design_contract}}
```

**Implementer 호출 시 추가:**
```
[Design Contract]
{{session.contracts.design_contract}}

[Test Contract]
{{session.contracts.test_contract}}

[테스트 코드]
{{test_file_content}}
```

## 상태 시각화

**매 페이즈 전환 시 자동 출력:**

```
╔══════════════════════════════════════════════════════════╗
║  TDD Orchestrator                                         ║
╠══════════════════════════════════════════════════════════╣
║                                                           ║
║  Discovery ✅ ─▶ Planning ✅ ─▶ Design ✅ ─▶ Test 🔄      ║
║                                            ↓              ║
║                              Verification ◀── Implementation
║                                                           ║
╠══════════════════════════════════════════════════════════╣
║  Tasks                                                    ║
║  ├─ M1 Repository      ✅ completed                       ║
║  ├─ M2 Service         🔄 in_progress  ← current          ║
║  └─ M3 Controller      ⏳ pending                         ║
║                                                           ║
║  Current Phase: Test First                                ║
║  Next Agent: QA Engineer                                  ║
║  Gates: GATE-1 ⏳                                         ║
╚══════════════════════════════════════════════════════════╝
```

### 상태 아이콘

| 아이콘 | 의미 |
|--------|------|
| ✅ | 완료 (completed) |
| 🔄 | 진행 중 (in_progress) |
| ⏳ | 대기 (pending) |
| ❌ | 실패 (failed) |
| ⚠️ | 경고 (warning) |

### 페이즈별 간략 상태 (한 줄)

```
[M2 Service] Planning ✅ → Design ✅ → Test 🔄 → Impl ⏳ → Verify ⏳
```

## 게이트 규칙 요약

| Gate | 조건 | 위반 시 |
|------|------|--------|
| GATE-1 | Test Contract 존재 | Implementation 차단 |
| GATE-2 | 테스트 결과 존재 | Complete 차단 |
| GATE-3 | 스코프 변경 없음 | Planning 복귀 |
| GATE-4 | 설계 불변 조건 유지 | Design 복귀 |

상세 규칙: [gate-rules.md](references/gate-rules.md)

## 참조 문서

| 문서 | 내용 |
|------|------|
| [session.md](references/session.md) | 세션 컨텍스트 관리 |
| [gate-rules.md](references/gate-rules.md) | 게이트 규칙 상세 |
| [contracts.md](references/contracts.md) | Contract 형식 (Design Brief, Design Contract, Test Contract) |
| [phases.md](references/phases.md) | 페이즈별 상세 절차 |
| [agent-contexts.md](references/agent-contexts.md) | 에이전트별 컨텍스트 주입 가이드 |

## 실행 흐름

### 1. Discovery (세션 초기화)

```
1. 세션 파일 생성/로드
2. Code Explore 호출:
   - prompt: "프로젝트 구조를 파악하고 주요 파일을 요약해줘"
   - subagent_type: "code-explore"
3. 결과를 session.explored_files에 저장
4. 상태 출력
```

### 2. Planning

```
1. 세션 컨텍스트 주입
2. Planner 호출:
   - prompt: "[세션 컨텍스트]\n[사용자 요청]\n분석하여 Design Brief 생성"
   - subagent_type: "planner"
3. Design Brief를 session.contracts.design_brief에 저장
4. 상태 출력
```

### 3. Design

```
1. 세션 컨텍스트 + Design Brief 주입
2. Architect 호출:
   - prompt: "[세션 컨텍스트]\n[Design Brief]\n기반으로 Design Contract 생성"
   - subagent_type: "architect"
3. Design Contract를 session.contracts.design_contract에 저장
4. 상태 출력
```

### 4. Test First

```
1. 세션 컨텍스트 + Design Contract 주입
2. QA Engineer 호출:
   - prompt: "[세션 컨텍스트]\n[Design Contract]\n기반으로 테스트 코드 작성"
   - subagent_type: "qa-engineer"
3. Test Contract를 session.contracts.test_contract에 저장
4. GATE-1 검증
5. 상태 출력
```

### 5. Implementation

```
1. 세션 컨텍스트 + Design Contract + Test Contract + 테스트 코드 주입
2. Implementer 호출:
   - prompt: "[세션 컨텍스트]\n[Design Contract]\n[Test Contract]\n[테스트 코드]\n테스트를 통과하는 최소 구현"
   - subagent_type: "implementer"
3. GATE-3, GATE-4 검증
4. 상태 출력
```

### 6. Verification

```
1. QA Engineer 호출:
   - prompt: "테스트 실행 및 결과 보고"
   - subagent_type: "qa-engineer"
2. Test Result를 session.contracts.test_result에 저장
3. GATE-2 검증
4. 결과에 따라:
   - PASS → Complete
   - FAIL (implementation_error) → Implementation 복귀
   - FAIL (design_violation) → Design 복귀
5. 상태 출력
```

### 7. Complete

```
1. 작업 완료 처리
2. 다음 작업 시작 또는 종료
3. 최종 상태 출력
```

## 명령어

| 명령 | 설명 |
|------|------|
| `/orchestrator` | 오케스트레이터 시작 |
| `/orchestrator status` | 현재 세션 상태 출력 |
| `/orchestrator resume` | 중단된 세션 재개 |
| `/orchestrator reset` | 세션 초기화 |

## 제약사항

- 한 번에 하나의 작업만 처리
- Contract 불완전 시 다음 단계 진행 금지
- 테스트 없이 구현 완료 불가
- 게이트 위반 시 이전 단계로 복귀
- 세션 파일은 `~/.claude/claude-devkit/sessions/`에 저장