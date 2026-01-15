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
    get_project_hash,
    load_state,
    get_current_work,
    get_sessions_path,
    get_agent_config,
    load_orchestrator_config,
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

    # 다음 단계 메시지 생성
    next_message = get_next_phase_message(agent_type, current_phase)

    # 결과 메시지 생성
    lines = []

    if created_contracts:
        contracts_str = ", ".join(created_contracts)
        lines.append(f"[{agent_type.title()} completed] {contracts_str} created")
    else:
        lines.append(f"[{agent_type.title()} completed]")

    if next_message:
        lines.append(f"-> {next_message}")

    output_result("\n".join(lines), hook_event="SubagentStop")


if __name__ == "__main__":
    main()
