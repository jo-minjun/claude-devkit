# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
