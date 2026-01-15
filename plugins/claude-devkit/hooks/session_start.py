#!/usr/bin/env python3
"""
SessionStart Hook - 세션 시작 시 오케스트레이션 세션 관리

Claude 세션이 시작될 때 실행되어:
1. 기존 미완료 세션이 있으면 → 이어서 작업할지 선택 안내
2. 기존 세션이 없거나 완료 상태 → 새 세션 시작 준비
"""

import sys
import os
import uuid

# hooks 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hooks.common import (
    read_stdin_json,
    output_result,
    get_project_hash,
    load_state,
    load_knowledge,
    count_pending_subtasks,
    count_pending_tasks,
    get_current_work,
    format_progress_tree,
    format_knowledge_summary,
    initialize_session,
    save_current_session_id,
)


def generate_recovery_message(state: dict, current_work: dict, knowledge: dict) -> str:
    """기존 세션 복구 안내 메시지 생성"""
    pending_subtasks = count_pending_subtasks(state)
    pending_tasks = count_pending_tasks(state)

    lines = [
        "[Orchestrator Session Found]",
        "",
        "미완료 세션이 있습니다.",
        "",
        f"요청: {current_work.get('request', 'N/A')}",
    ]

    if current_work.get("task_id"):
        lines.append(f"현재 Task: {current_work.get('task_id')} ({current_work.get('task_name')})")

    if current_work.get("subtask_id"):
        phase = current_work.get("phase", "")
        phase_info = f" - {phase}" if phase else ""
        lines.append(f"현재 Subtask: {current_work.get('subtask_id')} ({current_work.get('subtask_name')}){phase_info}")

    lines.extend([
        f"남은 Tasks: {pending_tasks}",
        f"남은 Subtasks: {pending_subtasks}",
        "",
        "Progress:",
        format_progress_tree(state),
    ])

    # knowledge 정보 추가
    if knowledge:
        lines.extend([
            "",
            "Project Knowledge:",
            format_knowledge_summary(knowledge),
        ])

    lines.extend([
        "",
        "선택:",
        "- 이어서 작업하려면: '이어서 진행해줘' 또는 '/orchestrator resume'",
        "- 새로 시작하려면: '새 세션으로 시작해줘' 또는 키워드로 새 요청",
    ])

    return "\n".join(lines)


def generate_new_session_message() -> str:
    """새 세션 안내 메시지 생성"""
    lines = [
        "[Orchestrator Ready]",
        "",
        "TDD 오케스트레이션을 사용할 준비가 되었습니다.",
        "",
        "사용 방법:",
        "- '로그인 기능 구현해줘' 처럼 요청하면 자동으로 TDD 오케스트레이션이 시작됩니다.",
        "- 또는 '/orchestrator' 명령어를 사용할 수 있습니다.",
        "",
        "트리거 키워드: 구현해줘, 만들어줘, 추가해줘, 개발해줘, 변경해줘, 수정해줘",
    ]

    return "\n".join(lines)


def main():
    """SessionStart Hook 메인 함수"""
    # stdin에서 입력 읽기 (프로토콜 준수)
    input_data = read_stdin_json()

    # 새 Claude Code 세션 ID 생성 및 저장
    session_id = str(uuid.uuid4())[:8]
    save_current_session_id(session_id)

    project_hash = get_project_hash()

    # 1. state.json 확인
    state = load_state(project_hash)

    # 2. 기존 세션 상태 판단
    if state:
        request = state.get("request", {})
        request_status = request.get("status")

        # 미완료 세션 (active 상태)
        if request_status == "active":
            pending_subtasks = count_pending_subtasks(state)

            if pending_subtasks > 0:
                # 미완료 작업이 있는 세션 → 복구 안내
                current_work = get_current_work(state)
                knowledge = load_knowledge(project_hash)
                message = generate_recovery_message(state, current_work, knowledge)
                output_result(message, hook_event="SessionStart")
                return

    # 3. 기존 세션 없거나 완료 상태 → 새 세션 준비 안내
    message = generate_new_session_message()
    output_result(message, hook_event="SessionStart")


if __name__ == "__main__":
    main()
