#!/usr/bin/env python3
"""
SubagentStop Hook - 서브에이전트 결과 수집 및 상태 업데이트

메인 에이전트가 생성한 서브에이전트가 종료될 때 실행되어:
1. 서브에이전트 유형 확인 (Planner, Architect, QA Engineer 등)
2. 에이전트별 출력 Contract 파일 확인 (config에서 로드)
3. state.json 자동 업데이트
4. 다음 단계 안내 메시지 반환
"""

import sys
import os
from pathlib import Path

# hooks 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hooks.common import (
    read_stdin_json,
    output_result,
    log_orchestrator,
    get_project_hash,
    load_state,
    save_state,
    get_current_work,
    get_sessions_path,
    get_agent_config,
    load_orchestrator_config,
    load_task_breakdown,
    convert_task_breakdown_to_state,
    check_global_discovery_complete,
    transition_to_task_loop,
    get_next_phase_for_agent,
    update_subtask_phase,
    complete_current_subtask,
    complete_current_task,
    complete_request,
)


def check_contract_exists(project_hash: str, current_work: dict, contract_name: str, level: str) -> bool:
    """Contract 파일 존재 여부 확인"""
    sessions_path = get_sessions_path(project_hash)
    request_id = current_work.get("request_id", "R1")
    task_id = current_work.get("task_id", "")
    subtask_id = current_work.get("subtask_id", "")

    if level == "request":
        contract_path = sessions_path / "contracts" / request_id / contract_name
    elif level == "task" and task_id:
        contract_path = sessions_path / "contracts" / request_id / task_id / contract_name
    elif level == "subtask" and task_id and subtask_id:
        contract_path = sessions_path / "contracts" / request_id / task_id / subtask_id / contract_name
    else:
        return False

    return contract_path.exists()


def handle_agent_completion(project_hash: str, agent_type: str, current_phase: str) -> str:
    """
    에이전트 완료 시 상태 업데이트 처리

    Args:
        project_hash: 프로젝트 해시
        agent_type: 완료된 에이전트 타입
        current_phase: 현재 subtask phase

    Returns:
        상태 변경 결과 메시지
    """
    # 1. 다음 phase 결정
    next_phase = get_next_phase_for_agent(agent_type, current_phase)
    if not next_phase:
        return ""

    # 2. Subtask phase 업데이트
    if next_phase == "complete":
        # Subtask 완료 처리
        success, next_subtask = complete_current_subtask(project_hash)
        if not success:
            return "Error: Failed to complete subtask"

        if next_subtask:
            # 다음 subtask로 이동
            return f"Subtask completed. Moving to next subtask: {next_subtask}"
        else:
            # 모든 subtask 완료 -> Task 완료 처리
            success, next_task = complete_current_task(project_hash)
            if not success:
                return "Error: Failed to complete task"

            if next_task:
                # 다음 task로 이동
                return f"Task completed. Moving to next task: {next_task}"
            else:
                # 모든 task 완료 -> Request 완료 처리
                if complete_request(project_hash):
                    return "All tasks completed! Request finished."
                else:
                    return "Error: Failed to complete request"
    else:
        # Phase만 업데이트
        if update_subtask_phase(project_hash, next_phase):
            return f"Phase updated to: {next_phase}"
        else:
            return "Error: Failed to update phase"


def get_next_phase_message(agent_type: str, current_phase: str) -> str:
    """에이전트 타입과 현재 phase에 따른 다음 단계 메시지"""
    agent_config = get_agent_config(agent_type)
    if not agent_config:
        return ""

    # QA Engineer의 경우 현재 phase에 따라 다음 단계가 다름
    next_phase_map = agent_config.get("next_phase_map")
    if next_phase_map and current_phase in next_phase_map:
        next_phase = next_phase_map[current_phase]
    else:
        next_phase = agent_config.get("next_phase", "")

    # 다음 단계에 대한 안내 메시지
    phase_messages = {
        "merge": "Merge 단계: explored.yaml과 task-breakdown.yaml을 검토하고 design-brief.yaml을 생성하세요.",
        "test_first": "Test First: QA Engineer 에이전트로 테스트를 먼저 작성하세요 (test-contract.yaml).",
        "implementation": "Implementation: Implementer 에이전트로 구현을 진행하세요.",
        "verification": "Verification: QA Engineer 에이전트로 테스트 검증을 수행하세요 (test-result.yaml).",
        "complete": "Complete: Subtask가 완료되었습니다. 다음 Subtask로 진행하세요.",
    }

    return phase_messages.get(next_phase, f"다음 Phase: {next_phase}")


def main():
    """SubagentStop Hook 메인 함수"""
    input_data = read_stdin_json()

    # 서브에이전트 정보 추출
    agent_type = input_data.get("agent_type", "").lower()
    agent_id = input_data.get("agent_id", "")

    # config에서 에이전트 설정 로드
    agent_config = get_agent_config(agent_type)
    if not agent_config:
        # orchestrator 관련 에이전트가 아님
        return

    project_hash = get_project_hash()

    # state.json 확인
    state = load_state(project_hash)
    if not state:
        return

    request = state.get("request", {})
    if request.get("status") != "active":
        return

    current_work = get_current_work(state)
    current_phase = current_work.get("phase", "")
    level = agent_config.get("level", "request")

    # Contract 파일 존재 확인
    contract_name = agent_config.get("output")
    contracts = agent_config.get("outputs", [contract_name] if contract_name else [])

    created_contracts = []
    for contract in contracts:
        if contract and check_contract_exists(project_hash, current_work, contract, level):
            created_contracts.append(contract)

    # ========== Global Discovery → Task Loop 전환 로직 ==========
    global_phase = request.get("global_phase", "")
    request_id = request.get("id", "R1")

    # planner 완료 시: task-breakdown.yaml → state.json 반영
    if agent_type == "planner" and "task-breakdown.yaml" in created_contracts:
        breakdown = load_task_breakdown(project_hash, request_id)
        if breakdown:
            converted = convert_task_breakdown_to_state(breakdown)
            state["task_order"] = converted["task_order"]
            state["tasks"] = converted["tasks"]
            save_state(project_hash, state)
            log_orchestrator("task-breakdown.yaml parsed and state.json updated")

    # Global Discovery 완료 조건 확인 및 phase 전환
    if global_phase == "global_discovery":
        complete, missing = check_global_discovery_complete(project_hash)
        if complete:
            if transition_to_task_loop(project_hash):
                log_orchestrator("Global Discovery completed -> Task Loop started")
                # state 다시 로드하여 최신 상태 반영
                state = load_state(project_hash)
                global_phase = state.get("request", {}).get("global_phase", "")
        else:
            log_orchestrator(f"Global Discovery incomplete. Missing: {', '.join(missing)}")
    # ========== Global Discovery 전환 로직 끝 ==========

    # ========== Task Loop 상태 업데이트 로직 ==========
    # Task Loop 단계에서만 동작
    if global_phase == "task_loop":
        agent_level = agent_config.get("level", "request")

        # subtask 레벨 에이전트: 상태 업데이트
        if agent_level == "subtask":
            status_message = handle_agent_completion(project_hash, agent_type, current_phase)
            if status_message:
                log_orchestrator(status_message)

        # architect 완료: 첫 subtask phase를 test_first로 설정
        elif agent_type == "architect" and agent_level == "task":
            if update_subtask_phase(project_hash, "test_first"):
                log_orchestrator("Architect completed. Subtask phase set to test_first")
    # ========== Task Loop 상태 업데이트 로직 끝 ==========

    # 다음 단계 메시지 생성
    next_message = get_next_phase_message(agent_type, current_phase)

    # 결과 메시지 생성
    lines = []

    if created_contracts:
        contracts_str = ", ".join(created_contracts)
        lines.append(f"[{agent_type.title()} completed] {contracts_str} created")
        log_orchestrator(f"{agent_type.title()} completed: {contracts_str}")
    else:
        lines.append(f"[{agent_type.title()} completed]")
        log_orchestrator(f"{agent_type.title()} completed")

    if next_message:
        lines.append(f"-> {next_message}")

    output_result("\n".join(lines), hook_event="SubagentStop")


if __name__ == "__main__":
    main()
