#!/usr/bin/env python3
"""
Claude DevKit Hooks - 공통 유틸리티

모든 Hook에서 공통으로 사용하는 함수들.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None


# =============================================================================
# Orchestrator Config 관련 함수
# =============================================================================

def load_orchestrator_config() -> Dict[str, Any]:
    """orchestrator-config.yaml 설정 로드"""
    config_path = Path(__file__).parent / "orchestrator-config.yaml"

    # YAML 로드 시도
    if yaml is not None and config_path.exists():
        try:
            return yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            pass

    # Fallback: 기본 설정 반환
    return get_default_orchestrator_config()


def get_default_orchestrator_config() -> Dict[str, Any]:
    """PyYAML 없을 경우 기본 설정"""
    return {
        "version": "1.0.0",
        "orchestration": {
            "enabled": True,
            "gate_enforcement": "block",
        },
        "keywords": {
            "trigger": [
                r"구현해\s*줘",
                r"만들어\s*줘",
                r"추가해\s*줘",
                r"개발해\s*줘",
                r"변경해\s*줘",
                r"수정해\s*줘",
                r"/orchestrator",
                r"/orchestrate",
            ],
            "skip": [
                r"설명해\s*줘",
                r"알려\s*줘",
                r"찾아\s*줘",
                r"검색해\s*줘",
                r"조사해\s*줘",
                r"분석해\s*줘",
            ],
        },
        "agents": {
            "code-explore": {"output": "explored.yaml", "next_phase": "merge", "level": "request"},
            "planner": {"output": "task-breakdown.yaml", "next_phase": "merge", "level": "request"},
            "architect": {"output": "design-contract.yaml", "next_phase": "test_first", "level": "task"},
            "qa-engineer": {
                "outputs": ["test-contract.yaml", "test-result.yaml"],
                "next_phase_map": {"test_first": "implementation", "verification": "complete"},
                "level": "subtask",
            },
            "implementer": {"output": None, "next_phase": "verification", "level": "subtask"},
        },
        "gates": {
            "GATE-1": {"condition": "test-contract.yaml exists", "blocks": "implementation", "message": "테스트 Contract가 없습니다."},
            "GATE-2": {"condition": "test-result.yaml exists", "blocks": "complete", "message": "테스트 결과가 없습니다."},
        },
    }


def is_orchestration_enabled() -> bool:
    """오케스트레이션 활성화 여부"""
    config = load_orchestrator_config()
    return config.get("orchestration", {}).get("enabled", True)


def is_orchestration_keyword(prompt: str) -> bool:
    """오케스트레이션 키워드 감지"""
    config = load_orchestrator_config()
    keywords = config.get("keywords", {})

    # Skip 키워드 확인 (먼저 체크)
    for pattern in keywords.get("skip", []):
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False
        except re.error:
            continue

    # Trigger 키워드 확인
    for pattern in keywords.get("trigger", []):
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True
        except re.error:
            continue

    return False


def get_gate_config(gate_id: str) -> Optional[Dict[str, Any]]:
    """게이트 설정 조회"""
    config = load_orchestrator_config()
    return config.get("gates", {}).get(gate_id)


def get_agent_config(agent_type: str) -> Optional[Dict[str, Any]]:
    """에이전트 설정 조회"""
    config = load_orchestrator_config()
    return config.get("agents", {}).get(agent_type)


def get_next_phase_for_agent(agent_type: str, current_phase: str) -> Optional[str]:
    """
    에이전트 완료 후 다음 phase 결정

    Args:
        agent_type: 에이전트 타입 (architect, qa-engineer, implementer)
        current_phase: 현재 subtask phase

    Returns:
        다음 phase 또는 None
    """
    agent_config = get_agent_config(agent_type)
    if not agent_config:
        return None

    # QA Engineer는 phase에 따라 다른 전환
    next_phase_map = agent_config.get("next_phase_map")
    if next_phase_map and current_phase in next_phase_map:
        return next_phase_map[current_phase]

    return agent_config.get("next_phase")


def get_phase_transition(phase: str) -> Optional[Dict[str, Any]]:
    """Phase 전환 설정 조회"""
    config = load_orchestrator_config()
    return config.get("phase_transitions", {}).get(phase)


def get_template(template_name: str) -> str:
    """오케스트레이션 템플릿 조회"""
    config = load_orchestrator_config()
    return config.get("templates", {}).get(template_name, "")


def get_gate_enforcement() -> str:
    """게이트 적용 방식 (block/warn)"""
    config = load_orchestrator_config()
    return config.get("orchestration", {}).get("gate_enforcement", "warn")


def get_project_hash() -> str:
    """현재 프로젝트 경로의 해시값 반환 (8자리)"""
    cwd = os.getcwd()
    return hashlib.md5(cwd.encode()).hexdigest()[:8]


# =============================================================================
# Claude Code 세션 ID 관련 함수
# =============================================================================

def get_session_id_file() -> Path:
    """현재 Claude Code 세션 ID 파일 경로"""
    return Path.home() / ".claude-devkit-session-id"


def get_current_session_id() -> Optional[str]:
    """현재 Claude Code 세션 ID 읽기"""
    session_file = get_session_id_file()
    if session_file.exists():
        try:
            return session_file.read_text(encoding="utf-8").strip()
        except IOError:
            pass
    return None


def save_current_session_id(session_id: str) -> None:
    """현재 Claude Code 세션 ID 저장"""
    try:
        get_session_id_file().write_text(session_id, encoding="utf-8")
    except IOError:
        pass


def is_same_session(state: Dict[str, Any]) -> bool:
    """state의 세션 ID와 현재 세션 ID 비교"""
    current_id = get_current_session_id()
    state_id = state.get("request", {}).get("claude_session_id")
    return bool(current_id and state_id and current_id == state_id)


def get_orchestrator_base_path() -> Path:
    """오케스트레이터 기본 경로 반환"""
    return Path(os.getcwd()) / ".claude" / "orchestrator"


def get_sessions_path(project_hash: str) -> Path:
    """세션 디렉토리 경로"""
    return get_orchestrator_base_path() / "sessions" / project_hash


def get_knowledge_path(project_hash: str) -> Path:
    """지식 파일 경로"""
    return get_orchestrator_base_path() / "knowledge" / project_hash / "knowledge.yaml"


def load_state(project_hash: str) -> Optional[Dict[str, Any]]:
    """state.json 로드"""
    state_path = get_sessions_path(project_hash) / "state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_state(project_hash: str, state: Dict[str, Any]) -> bool:
    """state.json 저장"""
    state_path = get_sessions_path(project_hash) / "state.json"
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except IOError:
        return False


def load_session(project_hash: str) -> Optional[Dict[str, Any]]:
    """session.json 로드"""
    session_path = get_sessions_path(project_hash) / "session.json"
    if session_path.exists():
        try:
            return json.loads(session_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return None


def load_knowledge(project_hash: str) -> Optional[Dict[str, Any]]:
    """knowledge.yaml 로드"""
    if yaml is None:
        return None

    knowledge_path = get_knowledge_path(project_hash)
    if knowledge_path.exists():
        try:
            return yaml.safe_load(knowledge_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, IOError):
            pass
    return None


def save_knowledge(project_hash: str, knowledge: Dict[str, Any]) -> bool:
    """knowledge.yaml 저장"""
    if yaml is None:
        return False

    knowledge_path = get_knowledge_path(project_hash)
    try:
        knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        knowledge_path.write_text(
            yaml.dump(knowledge, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8"
        )
        return True
    except IOError:
        return False


def count_pending_subtasks(state: Dict[str, Any]) -> int:
    """미완료 Subtask 개수 계산"""
    count = 0
    tasks = state.get("tasks", {})
    for task_data in tasks.values():
        for subtask_data in task_data.get("subtasks", {}).values():
            if subtask_data.get("status") != "completed":
                count += 1
    return count


def count_pending_tasks(state: Dict[str, Any]) -> int:
    """미완료 Task 개수 계산"""
    count = 0
    tasks = state.get("tasks", {})
    for task_data in tasks.values():
        if task_data.get("status") != "completed":
            count += 1
    return count


def get_current_work(state: Dict[str, Any]) -> Dict[str, str]:
    """현재 진행 중인 작업 정보 추출"""
    request = state.get("request", {})
    current_task_id = request.get("current_task")

    if not current_task_id:
        return {}

    task = state.get("tasks", {}).get(current_task_id, {})
    current_subtask_id = task.get("current_subtask")
    subtask = task.get("subtasks", {}).get(current_subtask_id, {}) if current_subtask_id else {}

    return {
        "request": request.get("original_request", ""),
        "request_id": request.get("id", ""),
        "global_phase": request.get("global_phase", ""),
        "task_id": current_task_id,
        "task_name": task.get("name", ""),
        "subtask_id": current_subtask_id or "",
        "subtask_name": subtask.get("name", ""),
        "phase": subtask.get("phase", ""),
    }


def is_contract_file(file_path: str) -> bool:
    """Contract 파일 여부 확인"""
    contract_patterns = [
        "explored.yaml",
        "task-breakdown.yaml",
        "design-brief.yaml",
        "design-contract.yaml",
        "test-contract.yaml",
        "test-result.yaml",
    ]
    return any(pattern in file_path for pattern in contract_patterns)


def get_status_icon(status: str) -> str:
    """상태에 따른 아이콘 반환"""
    icons = {
        "completed": "[v]",
        "in_progress": "[>]",
        "pending": "[ ]",
        "failed": "[x]",
        "active": "[>]",
    }
    return icons.get(status, "[ ]")


def format_progress_tree(state: Dict[str, Any]) -> str:
    """진행 상황 트리 형식으로 포맷"""
    lines = []
    task_order = state.get("task_order", [])
    tasks = state.get("tasks", {})
    current_task_id = state.get("request", {}).get("current_task")

    for i, task_id in enumerate(task_order):
        task = tasks.get(task_id, {})
        is_last_task = i == len(task_order) - 1
        prefix = "`-" if is_last_task else "|-"

        status_icon = get_status_icon(task.get("status"))
        current_marker = " <- current" if task_id == current_task_id else ""
        lines.append(f"{prefix} {task_id} {task.get('name', '')} {status_icon}{current_marker}")

        # Subtasks
        subtask_order = task.get("subtask_order", [])
        subtasks = task.get("subtasks", {})
        current_subtask_id = task.get("current_subtask")

        for j, subtask_id in enumerate(subtask_order):
            subtask = subtasks.get(subtask_id, {})
            is_last_subtask = j == len(subtask_order) - 1

            if is_last_task:
                sub_prefix = "   `-" if is_last_subtask else "   |-"
            else:
                sub_prefix = "|  `-" if is_last_subtask else "|  |-"

            sub_status = get_status_icon(subtask.get("status"))
            sub_current = " <- current" if subtask_id == current_subtask_id else ""
            phase_info = f" ({subtask.get('phase', '')})" if subtask.get("phase") else ""
            lines.append(f"{sub_prefix} {subtask_id} {subtask.get('name', '')} {sub_status}{phase_info}{sub_current}")

    return "\n".join(lines)


def format_knowledge_summary(knowledge: Dict[str, Any], max_items: int = 3) -> str:
    """knowledge.yaml 요약 포맷"""
    lines = []

    patterns = knowledge.get("patterns", {})
    if patterns:
        if patterns.get("architecture"):
            lines.append(f"- Architecture: {patterns['architecture']}")
        if patterns.get("testing"):
            lines.append(f"- Testing: {patterns['testing']}")
        if patterns.get("error_handling"):
            lines.append(f"- Error handling: {patterns['error_handling']}")

    pitfalls = knowledge.get("pitfalls", [])
    if pitfalls:
        lines.append(f"- Pitfalls: {len(pitfalls)} items")
        for p in pitfalls[:max_items]:
            desc = p.get("description", "")[:50]
            lines.append(f"  * {desc}")

    decisions = knowledge.get("decisions", [])
    if decisions:
        lines.append(f"- Decisions: {len(decisions)} items")

    return "\n".join(lines) if lines else "No knowledge recorded yet"


def read_stdin_json() -> Dict[str, Any]:
    """stdin에서 JSON 입력 읽기"""
    try:
        input_text = sys.stdin.read()
        if not input_text.strip():
            return {}
        return json.loads(input_text)
    except (json.JSONDecodeError, IOError):
        return {}


def output_json(data: Dict[str, Any]) -> None:
    """JSON 출력"""
    print(json.dumps(data, ensure_ascii=False))


def output_result(message: str, hook_event: str = "UserPromptSubmit") -> None:
    """Claude 컨텍스트에 메시지 주입 (Claude Code 공식 형식)"""
    output = {
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "additionalContext": message
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def log_orchestrator(message: str) -> None:
    """오케스트레이션 진행 상황을 stderr로 출력 (사용자에게 보임)"""
    print(f"[Orchestrator] {message}", file=sys.stderr)


def get_timestamp() -> str:
    """현재 시각 ISO 8601 형식"""
    return datetime.utcnow().isoformat() + "Z"


def check_yaml_available() -> bool:
    """PyYAML 사용 가능 여부"""
    return yaml is not None


# =============================================================================
# 게이트 검증 함수
# =============================================================================

def check_gate(gate_id: str, project_hash: str, current_work: Dict[str, Any]) -> Tuple[bool, str]:
    """
    게이트 검증 수행.

    Returns:
        (passed, message) - 통과 여부와 메시지
    """
    gate = get_gate_config(gate_id)
    if not gate:
        return True, ""

    condition = gate.get("condition", "")
    message = gate.get("message", f"Gate {gate_id} blocked")

    # Contract 파일 존재 여부 확인
    if "exists" in condition:
        contract_name = condition.replace(" exists", "").strip()
        if not check_contract_exists_for_gate(project_hash, current_work, contract_name):
            return False, message

    # GATE-3, GATE-4는 별도 로직 필요 (현재는 통과 처리)
    # TODO: 스코프 변경, 설계 불변 조건 검증 로직 구현

    return True, ""


def check_contract_exists_for_gate(project_hash: str, current_work: Dict[str, Any], contract_name: str) -> bool:
    """게이트 검증용 Contract 파일 존재 확인"""
    sessions_path = get_sessions_path(project_hash)
    request_id = current_work.get("request_id", "R1")
    task_id = current_work.get("task_id", "")
    subtask_id = current_work.get("subtask_id", "")

    # 가능한 경로들 확인
    possible_paths = [
        sessions_path / "contracts" / request_id / contract_name,
    ]

    if task_id:
        possible_paths.append(sessions_path / "contracts" / request_id / task_id / contract_name)

    if task_id and subtask_id:
        possible_paths.append(sessions_path / "contracts" / request_id / task_id / subtask_id / contract_name)

    return any(p.exists() for p in possible_paths)


def get_next_phase(current_phase: str, current_work: Dict[str, Any]) -> Optional[str]:
    """현재 phase에서 다음 phase 결정"""
    transition = get_phase_transition(current_phase)
    if not transition:
        return None

    return transition.get("next")


def update_state_phase(project_hash: str, new_phase: str, level: str = "subtask") -> bool:
    """state.json의 phase 업데이트"""
    state = load_state(project_hash)
    if not state:
        return False

    if level == "global":
        state["request"]["global_phase"] = new_phase
    elif level == "subtask":
        current_task_id = state.get("request", {}).get("current_task")
        if current_task_id:
            task = state.get("tasks", {}).get(current_task_id, {})
            current_subtask_id = task.get("current_subtask")
            if current_subtask_id:
                state["tasks"][current_task_id]["subtasks"][current_subtask_id]["phase"] = new_phase

    return save_state(project_hash, state)


# =============================================================================
# 세션 초기화 함수
# =============================================================================

def create_initial_state(project_hash: str, request: str) -> Dict[str, Any]:
    """새 오케스트레이션 세션 초기 상태 생성"""
    return {
        "version": 1,
        "request": {
            "id": "R1",
            "original_request": request,
            "status": "active",
            "global_phase": "global_discovery",
            "current_task": None,
            "created_at": get_timestamp(),
            "claude_session_id": get_current_session_id(),
        },
        "task_order": [],
        "tasks": {},
    }


def initialize_session(project_hash: str, request: str) -> bool:
    """새 세션 초기화"""
    state = create_initial_state(project_hash, request)
    return save_state(project_hash, state)


def detect_code_patterns(file_path: str, content: str) -> Dict[str, Any]:
    """
    파일 내용에서 코드 패턴 감지

    Returns:
        감지된 패턴 딕셔너리 또는 빈 딕셔너리
    """
    patterns = {}
    file_name = os.path.basename(file_path)

    # 빌드 도구 감지
    if file_name == "build.gradle" or file_name == "build.gradle.kts":
        patterns["build_tool"] = "Gradle"
        if "spring" in content.lower():
            patterns["framework"] = "Spring"
    elif file_name == "pom.xml":
        patterns["build_tool"] = "Maven"
        if "spring" in content.lower():
            patterns["framework"] = "Spring"
    elif file_name == "package.json":
        patterns["build_tool"] = "npm"
        if '"react"' in content:
            patterns["framework"] = "React"
        elif '"vue"' in content:
            patterns["framework"] = "Vue"
        elif '"@angular' in content:
            patterns["framework"] = "Angular"

    # 테스팅 프레임워크 감지
    if "Test" in file_name or ".spec." in file_name or ".test." in file_name:
        if "@Test" in content or "org.junit" in content:
            if "jupiter" in content or "junit5" in content.lower():
                patterns["testing"] = "JUnit 5"
            else:
                patterns["testing"] = "JUnit 4"
        if "mockito" in content.lower():
            patterns["mocking"] = "Mockito"
        if "describe(" in content or "it(" in content:
            if "jest" in content.lower():
                patterns["testing"] = "Jest"
            elif "vitest" in content.lower():
                patterns["testing"] = "Vitest"
            elif "mocha" in content.lower():
                patterns["testing"] = "Mocha"
        if "pytest" in content or "@pytest" in content:
            patterns["testing"] = "pytest"

    # 아키텍처 패턴 감지
    if "Controller" in file_name or "@Controller" in content or "@RestController" in content:
        patterns["architecture_hint"] = "MVC/Layered"
    if "Repository" in file_name or "@Repository" in content:
        patterns["data_layer"] = "Repository Pattern"
    if "Service" in file_name or "@Service" in content:
        patterns["service_layer"] = "Service Layer"

    # 언어 감지
    if file_path.endswith(".java"):
        patterns["language"] = "Java"
    elif file_path.endswith(".py"):
        patterns["language"] = "Python"
    elif file_path.endswith((".ts", ".tsx")):
        patterns["language"] = "TypeScript"
    elif file_path.endswith((".js", ".jsx")):
        patterns["language"] = "JavaScript"
    elif file_path.endswith(".go"):
        patterns["language"] = "Go"
    elif file_path.endswith(".rs"):
        patterns["language"] = "Rust"

    return patterns


def merge_patterns(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 패턴에 새 패턴 병합 (중복 방지)

    Returns:
        병합된 패턴과 새로 추가된 항목 목록
    """
    merged = existing.copy()
    added = []

    for key, value in new.items():
        if key not in merged:
            merged[key] = value
            added.append(f"{key}: {value}")
        elif merged[key] != value:
            # 기존 값과 다르면 리스트로 관리하거나 덮어쓰지 않음
            pass

    return merged, added


# =============================================================================
# Global Discovery → Task Loop 전환 함수
# =============================================================================

def load_task_breakdown(project_hash: str, request_id: str = "R1") -> Optional[Dict[str, Any]]:
    """
    task-breakdown.yaml 로드

    경로: .claude/orchestrator/sessions/{hash}/contracts/{requestId}/task-breakdown.yaml
    """
    if yaml is None:
        return None

    sessions_path = get_sessions_path(project_hash)
    breakdown_path = sessions_path / "contracts" / request_id / "task-breakdown.yaml"

    if not breakdown_path.exists():
        return None

    try:
        return yaml.safe_load(breakdown_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, IOError):
        return None


def convert_task_breakdown_to_state(breakdown: Dict[str, Any]) -> Dict[str, Any]:
    """
    task-breakdown.yaml의 tasks를 state.json의 tasks 형식으로 변환

    Input (task-breakdown.yaml):
        task_breakdown:
          tasks:
            - id: "T1"
              name: "..."
              objective: "..."
              subtasks:
                - id: "T1-S1"
                  name: "..."
                  description: "..."
          task_order: ["T1", "T2"]

    Output (state.json format):
        {
            "task_order": ["T1", "T2"],
            "tasks": {
                "T1": {
                    "name": "...",
                    "objective": "...",
                    "status": "pending",
                    "current_subtask": None,
                    "subtask_order": ["T1-S1", "T1-S2"],
                    "subtasks": {
                        "T1-S1": {"name": "...", "description": "...", "status": "pending", "phase": ""}
                    }
                }
            }
        }
    """
    result = {
        "task_order": [],
        "tasks": {}
    }

    task_breakdown = breakdown.get("task_breakdown", {})
    tasks_list = task_breakdown.get("tasks", [])
    task_order = task_breakdown.get("task_order", [])

    # task_order가 없으면 tasks 순서대로 생성
    if not task_order:
        task_order = [t.get("id") for t in tasks_list if t.get("id")]

    result["task_order"] = task_order

    for task in tasks_list:
        task_id = task.get("id", "")
        if not task_id:
            continue

        subtasks_list = task.get("subtasks", [])
        subtask_order = [st.get("id") for st in subtasks_list if st.get("id")]
        subtasks_dict = {}

        for subtask in subtasks_list:
            subtask_id = subtask.get("id", "")
            if subtask_id:
                subtasks_dict[subtask_id] = {
                    "name": subtask.get("name", ""),
                    "description": subtask.get("description", ""),
                    "status": "pending",
                    "phase": "",
                }

        result["tasks"][task_id] = {
            "name": task.get("name", ""),
            "objective": task.get("objective", ""),
            "status": "pending",
            "current_subtask": None,
            "subtask_order": subtask_order,
            "subtasks": subtasks_dict,
        }

    return result


def check_explored_exists(project_hash: str, request_id: str = "R1") -> bool:
    """explored.yaml 존재 여부 확인"""
    sessions_path = get_sessions_path(project_hash)
    explored_path = sessions_path / "contracts" / request_id / "explored.yaml"
    return explored_path.exists()


def check_global_discovery_complete(project_hash: str) -> Tuple[bool, List[str]]:
    """
    Global Discovery 완료 조건 확인

    Returns:
        (완료 여부, 누락된 Contract 목록)
    """
    state = load_state(project_hash)
    if not state:
        return False, ["state.json not found"]

    request_id = state.get("request", {}).get("id", "R1")
    missing = []

    # 설정에서 필수 Contract 확인
    transition = get_phase_transition("global_discovery")
    requires = transition.get("requires", ["explored.yaml", "task-breakdown.yaml"]) if transition else ["explored.yaml", "task-breakdown.yaml"]

    sessions_path = get_sessions_path(project_hash)
    contract_path = sessions_path / "contracts" / request_id

    for contract in requires:
        if not (contract_path / contract).exists():
            missing.append(contract)

    return len(missing) == 0, missing


def transition_to_task_loop(project_hash: str) -> bool:
    """
    global_discovery → task_loop 전환

    조건:
    - explored.yaml 존재
    - task-breakdown.yaml 존재

    동작:
    1. task-breakdown.yaml 파싱
    2. state.json에 tasks 반영
    3. global_phase를 task_loop으로 변경
    4. 첫 번째 task를 current_task로 설정
    5. 첫 번째 task의 첫 번째 subtask를 current_subtask로 설정

    Returns:
        성공 여부
    """
    state = load_state(project_hash)
    if not state:
        return False

    request_id = state.get("request", {}).get("id", "R1")

    # 조건 확인
    if not check_explored_exists(project_hash, request_id):
        return False

    breakdown = load_task_breakdown(project_hash, request_id)
    if not breakdown:
        return False

    # task-breakdown을 state 형식으로 변환
    converted = convert_task_breakdown_to_state(breakdown)

    # state 업데이트
    state["task_order"] = converted["task_order"]
    state["tasks"] = converted["tasks"]

    # global_phase 전환
    state["request"]["global_phase"] = "task_loop"

    # 첫 번째 task 설정
    if converted["task_order"]:
        first_task_id = converted["task_order"][0]
        state["request"]["current_task"] = first_task_id

        # 첫 번째 task의 상태를 in_progress로
        if first_task_id in state["tasks"]:
            state["tasks"][first_task_id]["status"] = "in_progress"

            # 첫 번째 subtask 설정
            subtask_order = state["tasks"][first_task_id].get("subtask_order", [])
            if subtask_order:
                first_subtask_id = subtask_order[0]
                state["tasks"][first_task_id]["current_subtask"] = first_subtask_id
                state["tasks"][first_task_id]["subtasks"][first_subtask_id]["status"] = "in_progress"

    return save_state(project_hash, state)


# =============================================================================
# Task/Subtask 상태 업데이트 함수
# =============================================================================

def update_subtask_phase(project_hash: str, new_phase: str) -> bool:
    """
    현재 subtask의 phase 업데이트

    Args:
        project_hash: 프로젝트 해시
        new_phase: 새로운 phase (test_first, implementation, verification, complete)

    Returns:
        성공 여부
    """
    state = load_state(project_hash)
    if not state:
        return False

    current_task_id = state.get("request", {}).get("current_task")
    if not current_task_id:
        return False

    task = state.get("tasks", {}).get(current_task_id)
    if not task:
        return False

    current_subtask_id = task.get("current_subtask")
    if not current_subtask_id:
        return False

    subtask = task.get("subtasks", {}).get(current_subtask_id)
    if not subtask:
        return False

    state["tasks"][current_task_id]["subtasks"][current_subtask_id]["phase"] = new_phase

    return save_state(project_hash, state)


def complete_current_subtask(project_hash: str) -> Tuple[bool, Optional[str]]:
    """
    현재 subtask 완료 처리 및 다음 subtask로 이동

    Returns:
        (성공 여부, 다음 subtask_id 또는 None)
        - (True, subtask_id): 다음 subtask로 이동 성공
        - (True, None): 모든 subtask 완료 (task 완료 필요)
        - (False, None): 오류
    """
    state = load_state(project_hash)
    if not state:
        return False, None

    current_task_id = state.get("request", {}).get("current_task")
    if not current_task_id:
        return False, None

    task = state.get("tasks", {}).get(current_task_id)
    if not task:
        return False, None

    current_subtask_id = task.get("current_subtask")
    if not current_subtask_id:
        return False, None

    # 현재 subtask 완료 처리
    state["tasks"][current_task_id]["subtasks"][current_subtask_id]["status"] = "completed"
    state["tasks"][current_task_id]["subtasks"][current_subtask_id]["phase"] = "complete"

    # 다음 subtask 찾기
    subtask_order = task.get("subtask_order", [])
    try:
        current_idx = subtask_order.index(current_subtask_id)
        next_idx = current_idx + 1
    except ValueError:
        save_state(project_hash, state)
        return True, None

    # 다음 subtask 있음
    if next_idx < len(subtask_order):
        next_subtask_id = subtask_order[next_idx]
        state["tasks"][current_task_id]["current_subtask"] = next_subtask_id
        state["tasks"][current_task_id]["subtasks"][next_subtask_id]["status"] = "in_progress"
        save_state(project_hash, state)
        return True, next_subtask_id

    # 모든 subtask 완료
    save_state(project_hash, state)
    return True, None


def complete_current_task(project_hash: str) -> Tuple[bool, Optional[str]]:
    """
    현재 task 완료 처리 및 다음 task로 이동

    Returns:
        (성공 여부, 다음 task_id 또는 None)
        - (True, task_id): 다음 task로 이동 성공
        - (True, None): 모든 task 완료 (request 완료 필요)
        - (False, None): 오류
    """
    state = load_state(project_hash)
    if not state:
        return False, None

    current_task_id = state.get("request", {}).get("current_task")
    if not current_task_id:
        return False, None

    task = state.get("tasks", {}).get(current_task_id)
    if not task:
        return False, None

    # 현재 task 완료 처리
    state["tasks"][current_task_id]["status"] = "completed"
    state["tasks"][current_task_id]["current_subtask"] = None

    # 다음 task 찾기
    task_order = state.get("task_order", [])
    try:
        current_idx = task_order.index(current_task_id)
        next_idx = current_idx + 1
    except ValueError:
        save_state(project_hash, state)
        return True, None

    # 다음 task 있음
    if next_idx < len(task_order):
        next_task_id = task_order[next_idx]
        state["request"]["current_task"] = next_task_id
        state["tasks"][next_task_id]["status"] = "in_progress"

        # 첫 번째 subtask 설정
        subtask_order = state["tasks"][next_task_id].get("subtask_order", [])
        if subtask_order:
            first_subtask_id = subtask_order[0]
            state["tasks"][next_task_id]["current_subtask"] = first_subtask_id
            state["tasks"][next_task_id]["subtasks"][first_subtask_id]["status"] = "in_progress"

        save_state(project_hash, state)
        return True, next_task_id

    # 모든 task 완료
    save_state(project_hash, state)
    return True, None


def complete_request(project_hash: str) -> bool:
    """
    Request 완료 처리

    모든 Task가 완료되었을 때 호출.
    - request.status = "completed"
    - request.global_phase = "complete"

    Returns:
        성공 여부
    """
    state = load_state(project_hash)
    if not state:
        return False

    state["request"]["status"] = "completed"
    state["request"]["global_phase"] = "complete"
    state["request"]["current_task"] = None

    return save_state(project_hash, state)
