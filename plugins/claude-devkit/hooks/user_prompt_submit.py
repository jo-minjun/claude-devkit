#!/usr/bin/env python3
"""
UserPromptSubmit Hook - 키워드 감지 및 오케스트레이션 세션 관리

사용자 프롬프트 제출 시 실행되어:
1. 오케스트레이션 키워드 감지
2. 세션 생성/재개/새로시작 처리
3. 오케스트레이션 지시문 주입
"""

import sys
import os
import re

# hooks 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hooks.common import (
    read_stdin_json,
    output_result,
    get_project_hash,
    load_state,
    save_state,
    get_current_work,
    format_progress_tree,
    is_orchestration_enabled,
    is_orchestration_keyword,
    get_template,
    initialize_session,
    count_pending_subtasks,
    is_same_session,
)


# 세션 관리 키워드
RESUME_KEYWORDS = [
    r"이어서\s*진행",
    r"이어서\s*작업",
    r"계속\s*진행",
    r"resume",
    r"/orchestrator\s+resume",
]

NEW_SESSION_KEYWORDS = [
    r"새\s*세션",
    r"새로\s*시작",
    r"처음부터",
    r"reset",
    r"/orchestrator\s+reset",
]


def is_resume_keyword(prompt: str) -> bool:
    """세션 재개 키워드 감지"""
    for pattern in RESUME_KEYWORDS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False


def is_new_session_keyword(prompt: str) -> bool:
    """새 세션 시작 키워드 감지"""
    for pattern in NEW_SESSION_KEYWORDS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False


def generate_orchestration_start_message(request: str) -> str:
    """오케스트레이션 시작 메시지 생성"""
    template = get_template("orchestration_start")
    if template:
        return template

    return f"""[TDD Orchestration Mode - New Session]

요청: "{request}"

새 오케스트레이션 세션을 시작합니다.

## 진행 순서

1. **Global Discovery**
   - Code Explore 에이전트로 프로젝트 구조 탐색
   - Planner 에이전트로 Task/Subtask 분해
   (두 에이전트 병렬 호출)

2. **Task Loop** - 각 Task에 대해:
   - Architect 에이전트로 설계 (design-contract.yaml 생성)
   - Mini TDD Loop:
     a. QA Engineer로 테스트 먼저 작성 (test-contract.yaml)
     b. Implementer로 구현
     c. QA Engineer로 검증 (test-result.yaml)

3. **Complete** - 모든 Task 완료

## 게이트 규칙

- GATE-1: test-contract.yaml 없이 구현 불가
- GATE-2: test-result.yaml 없이 완료 불가

## 다음 단계

Code Explore 에이전트와 Planner 에이전트를 병렬로 호출하세요.
"""


def get_next_action_instruction(global_phase: str, phase: str, current_work: dict) -> str:
    """현재 상태에 따른 구체적인 다음 행동 지시"""
    task_name = current_work.get("task_name", "")
    subtask_name = current_work.get("subtask_name", "")
    task_id = current_work.get("task_id", "")
    subtask_id = current_work.get("subtask_id", "")

    # Global Discovery 단계
    if global_phase == "global_discovery":
        return """## 다음 행동 (필수)

**Global Discovery를 완료하세요:**

1. Code Explore 에이전트 호출:
   ```
   Task tool 사용, subagent_type: "claude-devkit:code-explore"
   프롬프트: "프로젝트 구조를 탐색하고 explored.yaml로 저장해줘"
   ```

2. Planner 에이전트 호출 (병렬):
   ```
   Task tool 사용, subagent_type: "claude-devkit:planner"
   프롬프트: "요청을 Task/Subtask로 분해하고 task-breakdown.yaml로 저장해줘"
   ```

두 에이전트를 **병렬**로 호출하세요."""

    # Task Loop - 설계 단계
    if global_phase == "task_loop" and not phase:
        return f"""## 다음 행동 (필수)

**Task 설계를 시작하세요:**

현재 Task: {task_id} ({task_name})

Architect 에이전트 호출:
```
Task tool 사용, subagent_type: "claude-devkit:architect"
프롬프트: "{task_name} 설계하고 design-contract.yaml로 저장해줘"
```"""

    # Test First 단계
    if phase == "test_first":
        return f"""## 다음 행동 (필수)

**테스트를 먼저 작성하세요 (Test First):**

현재 Subtask: {subtask_id} ({subtask_name})

QA Engineer 에이전트 호출:
```
Task tool 사용, subagent_type: "claude-devkit:qa-engineer"
프롬프트: "{subtask_name}에 대한 테스트 케이스를 작성하고 test-contract.yaml로 저장해줘"
```

⚠️ GATE-1: test-contract.yaml이 생성되어야 구현 단계로 진행 가능"""

    # Implementation 단계
    if phase == "implementation":
        return f"""## 다음 행동 (필수)

**구현을 진행하세요:**

현재 Subtask: {subtask_id} ({subtask_name})

Implementer 에이전트 호출:
```
Task tool 사용, subagent_type: "claude-devkit:implementer"
프롬프트: "{subtask_name}을 구현해줘. test-contract.yaml의 테스트를 통과하도록 작성해줘"
```"""

    # Verification 단계
    if phase == "verification":
        return f"""## 다음 행동 (필수)

**테스트 검증을 수행하세요:**

현재 Subtask: {subtask_id} ({subtask_name})

QA Engineer 에이전트 호출:
```
Task tool 사용, subagent_type: "claude-devkit:qa-engineer"
프롬프트: "{subtask_name} 구현을 검증하고 test-result.yaml로 결과를 저장해줘"
```

⚠️ GATE-2: test-result.yaml이 생성되고 테스트가 통과해야 완료 가능"""

    # Complete 단계
    if phase == "complete":
        return """## 다음 행동

**현재 Subtask가 완료되었습니다.**

다음 Subtask로 진행하거나, 모든 Subtask가 완료되었다면 다음 Task로 이동하세요."""

    return """## 다음 행동

현재 상태를 확인하고 적절한 에이전트를 호출하세요."""


def generate_resume_message(state: dict, current_work: dict) -> str:
    """세션 재개 메시지 생성"""
    global_phase = current_work.get("global_phase", "unknown")
    current_task = current_work.get("task_id", "없음")
    current_subtask = current_work.get("subtask_id", "없음")
    phase = current_work.get("phase", "")
    request = current_work.get("request", "")

    progress_tree = format_progress_tree(state)
    next_action = get_next_action_instruction(global_phase, phase, current_work)

    return f"""[TDD Orchestration Mode - Resume]

기존 세션을 재개합니다.

## 요청
{request}

## 현재 상태

| 항목 | 값 |
|------|-----|
| Global Phase | {global_phase} |
| Current Task | {current_task} |
| Current Subtask | {current_subtask} |
| Subtask Phase | {phase or "N/A"} |

## Progress

{progress_tree}

{next_action}
"""


def main():
    """UserPromptSubmit Hook 메인 함수"""
    input_data = read_stdin_json()

    # 사용자 프롬프트 추출
    prompt = input_data.get("prompt", "")
    if not prompt:
        return

    # 오케스트레이션 비활성화 확인
    if not is_orchestration_enabled():
        return

    project_hash = get_project_hash()
    state = load_state(project_hash)

    # 기존 미완료 세션 존재 여부
    has_active_session = False
    if state:
        request_status = state.get("request", {}).get("status")
        pending = count_pending_subtasks(state)
        has_active_session = (request_status == "active" and pending > 0)

    # 1. 세션 재개 키워드
    if is_resume_keyword(prompt):
        if has_active_session:
            current_work = get_current_work(state)
            message = generate_resume_message(state, current_work)
            output_result(message, hook_event="UserPromptSubmit")
        else:
            output_result("[Orchestrator] 재개할 세션이 없습니다. 새 요청을 입력하세요.", hook_event="UserPromptSubmit")
        return

    # 2. 새 세션 시작 키워드
    if is_new_session_keyword(prompt):
        # 기존 세션이 있으면 완료 처리
        if has_active_session:
            state["request"]["status"] = "cancelled"
            save_state(project_hash, state)

        output_result("[Orchestrator] 새 세션을 시작합니다. 요청을 입력하세요.", hook_event="UserPromptSubmit")
        return

    # 3. 오케스트레이션 키워드 감지
    if not is_orchestration_keyword(prompt):
        # active 세션이 있고, 같은 Claude Code 세션이면 컨텍스트 주입
        if has_active_session and is_same_session(state):
            current_work = get_current_work(state)
            message = generate_resume_message(state, current_work)
            output_result(message, hook_event="UserPromptSubmit")
        return

    # 4. 세션 처리
    if has_active_session:
        # 기존 미완료 세션이 있지만 새 키워드 요청 → 새 세션으로 덮어쓰기
        # (사용자가 새 요청을 했으니 이전 세션은 버림)
        pass

    # 5. 새 세션 생성
    initialize_session(project_hash, prompt)

    # 6. 시작 메시지 출력
    message = generate_orchestration_start_message(prompt)
    output_result(message, hook_event="UserPromptSubmit")


if __name__ == "__main__":
    main()
