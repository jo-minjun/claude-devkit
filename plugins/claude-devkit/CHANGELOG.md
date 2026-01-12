# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-12

### Added

- **Orchestrator 세션 관리**: `~/.claude/claude-devkit/sessions/`에서 프로젝트별 세션 파일 관리
  - 프로젝트 컨텍스트, 마일스톤 상태, Contract 자동 저장
  - 세션 재개 지원 (`/orchestrator resume`)

- **Contract 체인**: 에이전트 간 산출물 자동 연결
  - Design Brief → Design Contract → Test Contract → Test Result
  - 이전 에이전트 결과가 다음 에이전트에 자동 주입

- **상태 시각화**: 오케스트레이션 진행 상황 실시간 표시
  - 페이즈 진행 상태 (✅🔄⏳❌⚠️)
  - 마일스톤 목록 및 현재 위치
  - 게이트 통과 상태

- **Discovery 페이즈**: 오케스트레이션 시작 시 프로젝트 구조 자동 탐색
  - code-explore 에이전트로 주요 파일 요약
  - 탐색 결과 세션에 캐싱하여 재사용

### Changed

- 서브에이전트 호출 시 세션 컨텍스트 공통 헤더 자동 주입
- 에이전트별 컨텍스트 주입 템플릿 표준화

## [1.0.0] - 2026-01-12

### Added

- 초기 릴리스
- **에이전트**: architect, implementer, planner, qa-engineer, doc-writer, code-explore, web-explore
- **스킬**: orchestrator, agent-creator, skill-creator, mcp-builder, prompt-generator, hook-generator, agent-manifest-aligner