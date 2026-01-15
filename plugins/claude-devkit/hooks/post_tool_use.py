#!/usr/bin/env python3
"""
PostToolUse Hook - knowledge.yaml 자동 업데이트 및 코드 패턴 분석

도구 실행 완료 후 실행되어:
1. Contract 파일 변경 시 knowledge.yaml 자동 업데이트
2. 코드 파일 탐색(Read) 시 패턴 분석 및 지식 축적
"""

import sys
import os
from pathlib import Path

# hooks 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import yaml
except ImportError:
    yaml = None

from hooks.common import (
    read_stdin_json,
    output_result,
    output_json,
    get_project_hash,
    load_knowledge,
    save_knowledge,
    load_state,
    save_state,
    is_contract_file,
    detect_code_patterns,
    merge_patterns,
    get_timestamp,
    check_yaml_available,
    get_current_work,
    check_gate,
    get_gate_enforcement,
    get_phase_transition,
    update_state_phase,
    get_template,
    initialize_session,
)


def extract_decisions_from_design_contract(file_path: str) -> list:
    """design-contract.yaml에서 설계 결정 추출"""
    if not check_yaml_available():
        return []

    decisions = []
    try:
        content = yaml.safe_load(Path(file_path).read_text(encoding="utf-8"))

        # invariants를 decisions로 변환
        for inv in content.get("invariants", []):
            decisions.append({
                "id": inv.get("id", ""),
                "topic": inv.get("id", ""),
                "decision": inv.get("rule", ""),
                "rationale": "Design invariant",
                "refs": [file_path],
                "created_at": get_timestamp()[:10],  # YYYY-MM-DD
            })
    except Exception:
        pass

    return decisions


def extract_pitfalls_from_test_result(file_path: str) -> list:
    """test-result.yaml 실패 케이스에서 pitfalls 추출"""
    if not check_yaml_available():
        return []

    pitfalls = []
    try:
        content = yaml.safe_load(Path(file_path).read_text(encoding="utf-8"))

        if content.get("execution", {}).get("result") == "fail":
            subtask_id = content.get("subtask_id", "")
            for failed in content.get("failed_tests", []):
                pitfalls.append({
                    "id": f"P-{failed.get('name', 'unknown')[:20]}",
                    "description": f"{failed.get('name', '')}: {failed.get('reason', '')}",
                    "reason": failed.get("suggestion", "Test failure analysis needed"),
                    "learned_from": subtask_id,
                })
    except Exception:
        pass

    return pitfalls


def process_contract_file(file_path: str, project_hash: str) -> list:
    """Contract 파일 처리"""
    updates = []

    knowledge = load_knowledge(project_hash)
    if not knowledge:
        knowledge = {
            "version": 1,
            "project": {
                "path": os.getcwd(),
                "hash": project_hash,
            },
            "patterns": {},
            "decisions": [],
            "pitfalls": [],
        }

    # design-contract.yaml 처리
    if "design-contract.yaml" in file_path:
        new_decisions = extract_decisions_from_design_contract(file_path)
        for dec in new_decisions:
            # 중복 체크 (같은 id면 스킵)
            existing_ids = [d.get("id") for d in knowledge.get("decisions", [])]
            if dec.get("id") and dec.get("id") not in existing_ids:
                knowledge["decisions"].append(dec)
                updates.append(f"Decision added: {dec.get('id')}")

    # test-result.yaml 처리
    elif "test-result.yaml" in file_path:
        new_pitfalls = extract_pitfalls_from_test_result(file_path)
        for pit in new_pitfalls:
            knowledge["pitfalls"].append(pit)
            desc = pit.get("description", "")[:30]
            updates.append(f"Pitfall added: {desc}...")

    # 변경사항 저장
    if updates:
        knowledge["updated_at"] = get_timestamp()
        save_knowledge(project_hash, knowledge)

    return updates


def process_state_transition(file_path: str, project_hash: str) -> dict:
    """
    Contract 파일 저장에 따른 상태 전환 처리

    Returns:
        {"transition": str, "gate_result": (bool, str), "next_action": str}
    """
    result = {
        "transition": None,
        "gate_result": (True, ""),
        "next_action": None,
    }

    state = load_state(project_hash)
    if not state:
        return result

    request = state.get("request", {})
    if request.get("status") != "active":
        return result

    current_work = get_current_work(state)
    current_phase = current_work.get("phase", "")
    global_phase = current_work.get("global_phase", "")

    # Contract별 상태 전환 처리
    if "explored.yaml" in file_path or "task-breakdown.yaml" in file_path:
        # Global Discovery 단계
        result["transition"] = "Global Discovery progress"
        result["next_action"] = "Complete Global Discovery, then proceed to Task Loop"

    elif "design-contract.yaml" in file_path:
        # Task Design 완료 → test_first로 전환
        result["transition"] = "Task Design completed"
        update_state_phase(project_hash, "test_first", "subtask")
        result["next_action"] = "QA Engineer로 테스트 먼저 작성하세요 (test-contract.yaml)"

    elif "test-contract.yaml" in file_path:
        # GATE-1 검증
        passed, message = check_gate("GATE-1", project_hash, current_work)
        result["gate_result"] = (passed, message)

        if passed:
            result["transition"] = "GATE-1 passed: test_first → implementation"
            update_state_phase(project_hash, "implementation", "subtask")
            result["next_action"] = "Implementer로 구현을 진행하세요"
        else:
            result["transition"] = "GATE-1 blocked"
            result["next_action"] = message

    elif "test-result.yaml" in file_path:
        # 테스트 결과 분석
        try:
            content = yaml.safe_load(Path(file_path).read_text(encoding="utf-8"))
            test_passed = content.get("execution", {}).get("result") == "pass"

            if current_phase == "verification":
                # GATE-2 검증
                passed, message = check_gate("GATE-2", project_hash, current_work)
                result["gate_result"] = (passed, message)

                if passed and test_passed:
                    result["transition"] = "GATE-2 passed: verification → complete"
                    update_state_phase(project_hash, "complete", "subtask")
                    result["next_action"] = "Subtask 완료. 다음 Subtask로 진행하세요."
                elif not test_passed:
                    result["transition"] = "Verification failed"
                    result["next_action"] = "테스트 실패. 구현을 수정하세요."
            else:
                # test_first 단계에서 테스트 결과
                result["transition"] = "Test first result recorded"
                result["next_action"] = "테스트 결과가 기록되었습니다."

        except Exception:
            pass

    return result


def generate_gate_blocked_message(gate_id: str, message: str) -> str:
    """게이트 차단 메시지 생성"""
    template = get_template("gate_blocked")
    if template:
        return template.format(gate_id=gate_id, message=message)

    return f"""[GATE BLOCKED: {gate_id}]

{message}

이 게이트를 통과하려면 필요한 조건을 충족해야 합니다.
"""


def process_code_read(file_path: str, content: str, project_hash: str) -> list:
    """코드 파일 Read 시 패턴 분석"""
    if not content:
        return []

    # 패턴 감지
    new_patterns = detect_code_patterns(file_path, content)
    if not new_patterns:
        return []

    # knowledge.yaml 로드/생성
    knowledge = load_knowledge(project_hash)
    if not knowledge:
        knowledge = {
            "version": 1,
            "project": {
                "path": os.getcwd(),
                "hash": project_hash,
            },
            "patterns": {},
            "decisions": [],
            "pitfalls": [],
        }

    # 패턴 병합
    existing_patterns = knowledge.get("patterns", {})
    merged, added = merge_patterns(existing_patterns, new_patterns)

    if added:
        knowledge["patterns"] = merged
        knowledge["updated_at"] = get_timestamp()
        save_knowledge(project_hash, knowledge)

    return added


def main():
    """PostToolUse Hook 메인 함수"""
    input_data = read_stdin_json()

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # 지원하는 도구 확인
    if tool_name not in ["Write", "Edit", "Read"]:
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    project_hash = get_project_hash()
    updates = []
    messages = []

    # Write/Edit: Contract 파일 처리
    if tool_name in ["Write", "Edit"]:
        if is_contract_file(file_path):
            # 1. knowledge.yaml 업데이트
            updates = process_contract_file(file_path, project_hash)

            # 2. 상태 전환 처리
            transition_result = process_state_transition(file_path, project_hash)

            if transition_result["transition"]:
                messages.append(f"[State] {transition_result['transition']}")

            # 게이트 검증 결과
            gate_passed, gate_message = transition_result["gate_result"]
            enforcement = get_gate_enforcement()

            if not gate_passed:
                if enforcement == "block":
                    # 엄격 차단
                    gate_blocked_msg = generate_gate_blocked_message(
                        "GATE", gate_message
                    )
                    output_json({
                        "decision": "block",
                        "reason": gate_blocked_msg,
                    })
                    return
                else:
                    # 경고만
                    messages.append(f"[Warning] {gate_message}")

            if transition_result["next_action"]:
                messages.append(f"[Next] {transition_result['next_action']}")

    # Read: 코드 패턴 분석
    elif tool_name == "Read":
        # Read 도구의 경우 content가 tool_input에 없을 수 있음
        # 실제로 파일 내용을 읽어야 함
        if Path(file_path).exists():
            try:
                content = Path(file_path).read_text(encoding="utf-8")
                updates = process_code_read(file_path, content, project_hash)
            except Exception:
                pass

    # 결과 출력
    all_outputs = []
    if updates:
        all_outputs.append(f"knowledge.yaml updated: {', '.join(updates)}")
    if messages:
        all_outputs.extend(messages)

    if all_outputs:
        output_result("\n".join(all_outputs), hook_event="PostToolUse")


if __name__ == "__main__":
    main()
