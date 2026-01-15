# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.7] - 2026-01-15

### Fixed

- **Global Discovery → Task Loop 전환 시 state.json 미업데이트 버그 수정**
  - `subagent_stop.py`에서 planner 완료 시 `task-breakdown.yaml` 파싱하여 state.json 반영
  - `explored.yaml` + `task-breakdown.yaml` 둘 다 존재 시 `global_phase`를 "task_loop"으로 자동 전환
  - 첫 번째 task/subtask를 current_task/current_subtask로 자동 설정

### Added

- **Task/Subtask 상태 자동 업데이트 로직**
  - Architect 완료 → subtask.phase = "test_first"
  - QA Engineer (test_first) 완료 → subtask.phase = "implementation"
  - Implementer 완료 → subtask.phase = "verification"
  - QA Engineer (verification) 완료 → subtask 완료, 다음 subtask로 자동 이동
  - 모든 subtask 완료 → task 완료, 다음 task로 자동 이동
  - 모든 task 완료 → request 완료 처리
- **orchestrator 트리거 키워드 추가**: "리팩터링해줘"

## [1.6.6] - 2026-01-15

### Changed

- **planner 에이전트 모델 변경**: sonnet → opus로 업그레이드하여 계획 품질 향상

## [1.6.5] - 2026-01-15

### Added

- **오케스트레이션 진행 상황 stderr 출력**: 훅 실행 시 터미널에서 진행 상황 확인 가능
  - `log_orchestrator()` 함수로 `[Orchestrator]` 메시지를 stderr로 출력
  - 세션 시작/재개, 상태 전환, 에이전트 완료 시 로깅
  - stdout(JSON 응답)과 분리되어 Claude Code 파싱에 영향 없음

## [1.6.4] - 2026-01-15

### Fixed

- **훅 출력 hookEventName 버그 수정**: 각 훅이 올바른 이벤트 이름 반환하도록 수정
  - `output_result()` 호출 시 `hook_event` 인자를 명시적으로 전달
  - PostToolUse 훅이 "UserPromptSubmit" 대신 "PostToolUse" 반환
  - 모든 훅에서 hookEventName 불일치 오류 해결

## [1.6.3] - 2026-01-15

### Fixed

- **훅 출력 형식 수정**: Claude Code 공식 규격에 맞게 변경
  - `{"result": message}` → `{"hookSpecificOutput": {"additionalContext": message}}`
  - 오케스트레이션 지시문이 Claude 컨텍스트에 올바르게 주입됨
  - 참고: [sisyphus](https://github.com/Yeachan-Heo/oh-my-claude-sisyphus) 구현 분석

## [1.6.2] - 2026-01-15

### Added

- **세션 ID 기반 오케스트레이션 연속성**: reject 후에도 같은 Claude Code 세션이면 자동으로 컨텍스트 주입
  - SessionStart 훅에서 세션 시작 시 고유 ID 생성
  - UserPromptSubmit 훅에서 세션 ID 비교하여 연속성 판단
  - 트리거 키워드 없이도 같은 세션 내에서 오케스트레이션 지속

## [1.6.1] - 2026-01-15

### Fixed

- **hooks.json 경로 문제 수정**: 상대 경로를 `${CLAUDE_PLUGIN_ROOT}` 환경변수로 변경
  - 사용자의 작업 디렉토리와 무관하게 훅 스크립트를 올바르게 찾음
  - `python3 hooks/xxx.py` → `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/xxx.py`

## [1.6.0] - 2026-01-15

### Added

- **오케스트레이터 훅 기반 아키텍처**: 스킬 기반에서 훅 기반으로 전면 전환
  - `hooks/` 디렉토리에 8개 훅 이벤트 핸들러 구현
  - SessionStart: 세션 복구 및 새 세션 준비
  - UserPromptSubmit: 키워드 감지 및 오케스트레이션 시작
  - PostToolUse: Contract 파일 감지 및 자동 phase 전환
  - SubagentStop: 에이전트 완료 시 다음 단계 안내
  - Stop: 미완료 작업 경고
  - PreCompact: 컨텍스트 압축 시 세션 상태 보존
  - `orchestrator-config.yaml`로 선언적 설정 (에이전트, 게이트, phase 전환 규칙)
  - `common.py`에 공통 유틸리티 함수 집중

### Changed

- **README.md 사용자 친화적 재작성**
  - Quick Start 섹션을 최상단에 배치
  - claude-mem이 선택적 의존성임을 명시 (없어도 모든 기능 정상 작동)
  - 사용 예시 중심으로 간결하게 구성

### Removed

- **orchestrator 스킬 제거**: 훅 기반으로 전환되어 스킬 방식 삭제
  - SKILL.md 및 references/ 디렉토리 전체 (12개 파일)

## [1.5.2] - 2026-01-14

### Added

- **스키마 준수 원칙**: 모든 세션/Contract 파일이 storage.md에 정의된 스키마를 반드시 따르도록 강화
  - 정의되지 않은 필드 추가 금지
  - 정의된 필드의 타입/구조 변경 금지
  - 임의의 최상위 객체 생성 금지

- **global_phase 업데이트 시점 명시**: state.json의 global_phase 전환 시점을 명확히 문서화
  - 세션 시작: `global_discovery`
  - Merge 완료: `task_loop`
  - Request 완료: `complete`

### Changed

- **storage.md**: 스키마 준수 원칙 섹션 추가 (파일 상단)
- **SKILL.md**: 핵심 원칙 7번으로 "스키마 준수" 추가, 세션 시작/Global Discovery 후 상태 업데이트 명시
- **session.md**: state.json 초기값과 Merge 완료 후 상태 예시 분리, global_phase 업데이트 시점 표 추가
- **phases.md**: Merge 페이즈 출력에 state.json 업데이트 내용 추가

### Fixed

- 오케스트레이터가 state.json에 문서에 정의되지 않은 `global` 객체를 생성하는 문제 수정
- Global Discovery 후 global_phase가 갱신되지 않는 문제 수정

## [1.5.1] - 2026-01-14

### Added

- **필수 파일 생성 규칙**: 오케스트레이터가 각 단계에서 반드시 생성해야 하는 파일 명시
  - session.json, state.json은 `/orchestrator` 실행 직후 생성
  - Contract 파일들은 각 Agent 완료 직후 생성
  - 파일 미생성 시 다음 단계 진행 차단

- **Subtask 분해 규칙**: TDD가 올바르게 적용되도록 Planner 가이드라인 추가
  - 테스트를 별도 Subtask로 분리 금지
  - 각 Subtask는 자체적으로 Test First → Implementation → Verification 실행
  - "테스트 작성", "단위 테스트" 등의 Subtask 명시적 금지

### Changed

- **contracts.md 예시 수정**: 테스트를 별도 Subtask로 분리하는 잘못된 예시 → 올바른 TDD 구조로 수정
- **agent-prompts.md**: Planner 프롬프트에 `[분해 규칙 - 필수]` 섹션 추가
- **SKILL.md**: 핵심 원칙에 필수 요건 강조 문구 추가

### Fixed

- 오케스트레이터가 세션/Contract 파일을 생성하지 않고 구현만 진행하는 문제 수정
- Planner가 테스트를 별도 Subtask로 분리하여 TDD가 적용되지 않는 문제 수정

## [1.5.0] - 2026-01-14

### Added

- **claude-mem 트리거 조건 명확화**: 에이전트별 검색 시점과 쿼리 패턴 정의
  - Architect: 첫 세션에서 설계 결정 검색
  - Implementer: 재시도 시 (retry_count > 0) 실패 패턴 검색
  - QA Engineer: 테스트 2회 이상 실패 시 패턴 검색
  - Fallback: claude-mem 미설치 시 경고 메시지 출력 후 파일 기반 지식만 사용

- **knowledge.yaml 자동 업데이트**: 수동 `/orchestrator learn` 없이 자동 축적
  - Task 완료 시: design-contract에서 decisions 추출
  - Subtask 재시도 후 성공 시: 실패 원인을 pitfalls에 추가
  - 세션 종료 시: 전체 Contract 스캔 후 누락된 지식 병합

- **에이전트 프롬프트에 mem_context 섹션 추가**: Architect, Implementer 템플릿에 claude-mem 검색 결과 주입 영역 추가

### Changed

- **README.md 전면 재구성**: 개념 설명 → 사용법 위주로 변경
  - 빠른 시작 섹션 추가
  - 에이전트/스킬별 트리거 예시 명시
  - 알아두면 좋은 개념 섹션 간소화

- **SKILL.md에 claude-mem 검색 타이밍 다이어그램 추가**: 오케스트레이터가 에이전트 호출 전 검색하는 흐름 시각화

- **session.md 지식 축적 정책 변경**: "(선택) 지식 축적" → "자동 지식 축적"으로 변경

- **참조 문서 구조 개편**: agent-prompts.md, context-injection.md 분리 및 상세화

### Removed

- **agent-contexts.md 삭제**: context-injection.md와 agent-prompts.md로 분리
- **timeline.md 삭제**: session.md와 storage.md로 통합

## [1.4.0] - 2026-01-13

### Added

- **타임라인 시스템**: 오케스트레이션 전체 흐름을 시간순으로 추적하는 새 참조 문서
  - 페이즈별 시작/종료 타임스탬프
  - 에이전트 호출 이력 및 소요 시간
  - Contract 생성/검증 이벤트

- **Knowledge 관리**: 세션 중 발견한 정보를 체계적으로 관리하는 새 참조 문서
  - 프로젝트 구조, 코드 패턴, 의존성 정보 저장
  - 에이전트 간 지식 공유 메커니즘
  - 세션 재개 시 컨텍스트 복원 지원

### Changed

- **Orchestrator SKILL.md 구조 개선**: 207줄 정리로 가독성 향상
- **Contract 문서 확장**: 453줄→더 상세한 체인 설명 및 검증 규칙
- **Session 문서 개편**: 에이전트 컨텍스트 주입 방식 명확화
- **Agent Context 템플릿 정리**: 공통 헤더 간소화

### Removed

- **플러그인 내부 README.md 삭제**: 루트 README.md로 통합

## [1.3.0] - 2026-01-13

### Added

- **Project Manifest 자동 탐색**: CLAUDE.md, AGENTS.md 위치를 자동으로 탐색하여 세션에 저장
  - Code Explore가 프로젝트 탐색 시 매니페스트 파일 위치 보고
  - `session.project_manifest`에 저장되어 모든 에이전트가 참조 가능
  - null 처리 지침: 파일이 없으면 기존 코드 패턴만 따름

### Changed

- **Architect 워크플로우 개선**: 1단계에서 project_manifest.claude_md 확인 후 조건부로 규칙 적용
- **Code Explore 매니페스트 탐색**: 오케스트레이터 연동 여부와 무관하게 항상 탐색
- **에이전트 컨텍스트 주입 개선**: 공통 헤더에 프로젝트 매니페스트 정보 추가

## [1.2.2] - 2026-01-12

### Changed

- **Implementer 주석 최소화 원칙 추가**: 과도한 주석 방지를 위한 명확한 기준 수립
  - 금지: WHAT 설명, 형식적 문서화, 파일 헤더, 구분선, TODO/FIXME, 주석 처리된 코드
  - 허용: WHY 설명, 위험 경고, 외부 참조
  - 기준: "6개월 후 처음 보는 개발자가 '왜?'라고 물을 곳"

## [1.2.1] - 2026-01-12

### Changed

- **Planner 작업 크기 기준 추가**: XS/S/M/L/XL 라벨로 작업 및 하위 작업 크기 명시
  - 작업(Task): S(1-2파일) ~ XL(7개+, 분할 필요)
  - 하위작업(Subtask): XS(단일 함수) ~ M(기능 단위)
  - 분해 규칙: XL 작업 분할, M 초과 하위작업 재분해

- **Prompt Generator 문서 개선**: SKILL.md를 73줄에서 356줄로 확장
  - 좋은 프롬프트 vs 나쁜 프롬프트 비교 예시 (4가지 유형)
  - 품질 체크리스트에 구체적 기준 및 나쁜/좋은 예 추가
  - 유형별 빠른 템플릿 5종 추가

## [1.2.0] - 2026-01-12

### Added

- **Parallel Discovery**: Code Explore와 Planner를 병렬 실행하여 초기 탐색 시간 단축
  - Code Explore: 프로젝트 구조 파악
  - Planner: assumptions 포함한 잠정 계획 수립 (코드 탐색 없이)
  - 두 결과를 Merge 페이즈에서 병합

- **Merge 페이즈**: 오케스트레이터가 직접 수행하는 새 페이즈
  - assumptions 검증 및 실제 코드 구조와 비교
  - scope_in 경로 구체화
  - 가정 50% 이상 불일치 시 Planner 재호출

- **Preliminary Design Brief**: Planner가 생성하는 잠정 작업 정의서
  - assumptions 필드 필수 (코드 구조에 대한 가정 명시)
  - Merge 후 최종 Design Brief로 변환

### Changed

- 오케스트레이션 루프 다이어그램 개선 (병렬 실행 시각화)
- 세션 파일에 parallel_discovery 상태 추가
- Contract 체인 다이어그램 업데이트

## [1.1.1] - 2026-01-12

### Changed

- **Planner 용어 정리**: "태스크"→"하위 작업", "마일스톤"→"작업"으로 용어 통일
- **Planner 사용자 확인 단계 추가**: 작업 정의 후 사용자에게 확인받고 피드백 반영하는 4단계 추가

## [1.1.0] - 2026-01-12

### Added

- **Orchestrator 세션 관리**: `~/.claude/claude-devkit/sessions/`에서 프로젝트별 세션 파일 관리
  - 프로젝트 컨텍스트, 작업 상태, Contract 자동 저장
  - 세션 재개 지원 (`/orchestrator resume`)

- **Contract 체인**: 에이전트 간 산출물 자동 연결
  - Design Brief → Design Contract → Test Contract → Test Result
  - 이전 에이전트 결과가 다음 에이전트에 자동 주입

- **상태 시각화**: 오케스트레이션 진행 상황 실시간 표시
  - 페이즈 진행 상태 (✅🔄⏳❌⚠️)
  - 작업 목록 및 현재 위치
  - 게이트 통과 상태

- **Discovery 페이즈**: 오케스트레이션 시작 시 프로젝트 구조 자동 탐색
  - code-explore 에이전트로 주요 파일 요약
  - 탐색 결과 세션에 캐싱하여 재사용

### Changed

- 서브에이전트 호출 시 세션 컨텍스트 공통 헤더 자동 주입
- 에이전트별 컨텍스트 주입 템플릿 표준화

## [1.0.0] - 2026-01-11

### Added

- 초기 릴리스
- **에이전트**: architect, implementer, planner, qa-engineer, doc-writer, code-explore, web-explore
- **스킬**: orchestrator, agent-creator, skill-creator, mcp-builder, prompt-generator, hook-generator, agent-manifest-aligner
