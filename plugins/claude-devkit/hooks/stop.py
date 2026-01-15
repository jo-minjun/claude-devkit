#!/usr/bin/env python3
"""
Stop Hook - 미완료 작업 경고 및 연속 작업 유도

Claude 에이전트가 응답 생성을 마쳤을 때 실행되어:
1. 미완료 작업이 있으면 경고 메시지 출력
2. 작업 완료 시 knowledge.yaml 자동 업데이트
3. 세션 종료 전 최종 상태 알림
"""

import sys
import os

# hooks 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hooks.common import (
    read_stdin_json,
    output_result,
    get_project_hash,
    load_state,
    load_knowledge,
    save_knowledge,
    count_pending_subtasks,
    count_pending_tasks,
    get_current_work,
    format_progress_tree,
    get_timestamp,
)


# 무한 루프 방지용 환경변수
STOP_HOOK_ACTIVE_KEY = "CLAUDE_DEVKIT_STOP_HOOK_ACTIVE"


def auto_update_knowledge_on_complete(project_hash: str, state: dict) -> list:
    """
    완료된 작업에서 지식 추출하여 업데이트

    Returns:
        업데이트된 항목 목록
    """
    knowledge = load_knowledge(project_hash)
    if not knowledge:
        return []

    updates = []

    # 완료된 Task/Subtask에서 패턴 추출 (향후 확장)
    # 현재는 timestamp만 업데이트
    knowledge["updated_at"] = get_timestamp()
    save_knowledge(project_hash, knowledge)

    return updates


def main():
    """Stop Hook 메인 함수"""
    # 무한 루프 방지
    if os.environ.get(STOP_HOOK_ACTIVE_KEY) == "true":
        return

    os.environ[STOP_HOOK_ACTIVE_KEY] = "true"

    try:
        # stdin에서 입력 읽기
        input_data = read_stdin_json()

        project_hash = get_project_hash()

        # state.json 로드
        state = load_state(project_hash)
        if not state:
            # 오케스트레이터 세션 없음 - 조용히 종료
            return

        request = state.get("request", {})
        request_status = request.get("status")

        # 미완료 작업 확인
        pending_subtasks = count_pending_subtasks(state)
        pending_tasks = count_pending_tasks(state)

        if pending_subtasks > 0 and request_status == "active":
            # 미완료 경고 메시지
            current_work = get_current_work(state)

            lines = [
                "[Orchestrator] Incomplete tasks warning",
                "",
                "Progress:",
                format_progress_tree(state),
                "",
                f"Remaining Tasks: {pending_tasks}",
                f"Remaining Subtasks: {pending_subtasks}",
            ]

            if current_work.get("subtask_id"):
                phase = current_work.get("phase", "")
                lines.extend([
                    "",
                    f"Current: {current_work.get('task_id')} > {current_work.get('subtask_id')} ({phase})",
                ])

            lines.extend([
                "",
                "To continue work, keep going.",
                "To explicitly stop: '/orchestrator stop'",
            ])

            output_result("\n".join(lines), hook_event="Stop")

        elif request_status == "completed":
            # 완료 시 지식 자동 업데이트
            updates = auto_update_knowledge_on_complete(project_hash, state)

            if updates:
                message = f"Session completed. knowledge.yaml updated: {len(updates)} items added"
                output_result(message, hook_event="Stop")

    finally:
        # 환경변수 정리
        if STOP_HOOK_ACTIVE_KEY in os.environ:
            del os.environ[STOP_HOOK_ACTIVE_KEY]


if __name__ == "__main__":
    main()
