#!/usr/bin/env python3
"""
PreCompact Hook - 컨텍스트 압축 전 세션 상태 주입

컨텍스트 압축(Compaction) 직전에 실행되어:
1. 현재 orchestrator 세션 상태 추출
2. 핵심 정보를 압축 결과에 주입
3. 압축 후에도 세션 컨텍스트 유지
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
    count_pending_subtasks,
    count_pending_tasks,
    get_current_work,
    format_knowledge_summary,
)


def main():
    """PreCompact Hook 메인 함수"""
    # stdin에서 입력 읽기
    _ = read_stdin_json()

    project_hash = get_project_hash()

    # state.json 확인
    state = load_state(project_hash)
    if not state:
        # 오케스트레이터 세션 없음
        return

    request = state.get("request", {})
    if request.get("status") != "active":
        # 활성 세션 아님
        return

    # 현재 작업 정보
    current_work = get_current_work(state)
    pending_subtasks = count_pending_subtasks(state)
    pending_tasks = count_pending_tasks(state)

    # 핵심 상태 요약 생성
    lines = [
        "[Orchestrator Context - Preserve after compaction]",
        "",
    ]

    if current_work.get("request"):
        lines.append(f"Request: {current_work.get('request')[:100]}")

    if current_work.get("task_id"):
        lines.append(f"Current Task: {current_work.get('task_id')} ({current_work.get('task_name')})")

    if current_work.get("subtask_id"):
        phase = current_work.get("phase", "")
        lines.append(f"Current Subtask: {current_work.get('subtask_id')} - {phase}")

    lines.extend([
        f"Remaining: {pending_tasks} tasks, {pending_subtasks} subtasks",
    ])

    # knowledge 핵심 정보
    knowledge = load_knowledge(project_hash)
    if knowledge:
        pitfalls = knowledge.get("pitfalls", [])
        if pitfalls:
            lines.append("")
            lines.append("Key Pitfalls:")
            for p in pitfalls[:3]:
                desc = p.get("description", "")[:60]
                lines.append(f"- {desc}")

    lines.extend([
        "",
        "To resume: '/orchestrator resume'",
    ])

    output_result("\n".join(lines), hook_event="PreCompact")


if __name__ == "__main__":
    main()
