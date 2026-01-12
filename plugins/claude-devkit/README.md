# claude-devkit

Claude Code 개발 도구 모음 플러그인입니다. TDD 오케스트레이션, 에이전트/스킬 생성, MCP 빌더, 프롬프트 생성 등 AI 개발에 필요한 도구들을 제공합니다.

## 설치

```bash
/plugin marketplace add jo-minjun/claude-devkit
/plugin install claude-devkit
```

## 포함된 에이전트

| 에이전트 | 설명 |
|---------|------|
| **architect** | 소프트웨어 설계 결정 에이전트. 경계, 인터페이스, 데이터 구조, 트랜잭션, 에러 처리 전략 설계 |
| **implementer** | 코드 구현 에이전트. 설계를 바탕으로 실제 코드를 작성하고 빌드 확인 |
| **planner** | 작업 계획 에이전트. 마일스톤 확인, 우선순위 정리, 태스크 분해, TODO 리스트 생성 |
| **qa-engineer** | QA 엔지니어 에이전트. 테스트 케이스, 시나리오, 경계값 설계 및 테스트 코드 작성 |
| **doc-writer** | 문서 작성 에이전트. README, API 문서, 사용자 가이드, CHANGELOG 작성 |
| **code-explore** | 코드베이스 탐색 에이전트. 구현 찾기, 파일 위치 확인, 코드 구조 이해 |
| **web-explore** | 웹 탐색 및 요약 에이전트. 웹 검색, 페이지 가져오기, 온라인 정보 요약 |

## 포함된 스킬

| 스킬 | 설명 |
|-----|------|
| **orchestrator** | TDD 기반 개발 오케스트레이터. Planner, Architect, QA Engineer, Implementer를 조율하여 테스트 우선 개발 루프 실행. 세션 컨텍스트 관리, Contract 체인, 상태 시각화 지원 |
| **agent-creator** | 커스텀 서브에이전트 생성. `.claude/agents` 또는 `~/.claude/agents`에 새 에이전트 생성 |
| **skill-creator** | 효과적인 스킬 생성 가이드. Claude의 기능을 전문 지식, 워크플로우, 도구 통합으로 확장 |
| **mcp-builder** | MCP(Model Context Protocol) 서버 생성 가이드. Python(FastMCP)이나 Node/TypeScript로 외부 서비스 통합 |
| **prompt-generator** | AI 에이전트를 위한 고품질 프롬프트 생성. 스킬/에이전트/MCP 서버/일반 코딩 작업용 |
| **hook-generator** | Claude Code Hooks 생성. 도구 실행 전후 검증, 코드 품질 관리, 알림 전송 자동화 |
| **agent-manifest-aligner** | AGENTS.md와 CLAUDE.md 파일 간 연결 및 충돌 해결 |

## 사용 예시

### 오케스트레이터로 기능 개발
```
사용자: 로그인 기능 추가해줘
→ orchestrator 스킬이 자동 발동
→ Planner → Architect → QA Engineer → Implementer 순으로 TDD 개발
```

### 에이전트 생성
```
사용자: 코드 리뷰 에이전트 만들어줘
→ /agent-creator 또는 agent-creator 스킬 사용
```

### MCP 서버 구축
```
사용자: GitHub API 연동 MCP 서버 만들어줘
→ /mcp-builder 스킬 사용
```

## 라이선스

MIT
