# claude-devkit

Claude Code 개발 도구 모음 플러그인입니다. TDD 오케스트레이션, 에이전트/스킬 생성, MCP 빌더, 프롬프트 생성 등 AI 개발에 필요한 도구들을 제공합니다.

## 설치

```bash
# 마켓플레이스 등록
/plugin marketplace add jo-minjun/claude-devkit

# 플러그인 설치
/plugin install claude-devkit@jo-minjun
```

## 포함된 구성요소

### 에이전트 (7개)

| 에이전트 | 설명 |
|---------|------|
| **architect** | 소프트웨어 설계 결정 에이전트. 경계, 인터페이스, 데이터 구조, 에러 처리 전략 설계 |
| **implementer** | 코드 구현 에이전트. 설계를 바탕으로 실제 코드를 작성하고 빌드 확인 |
| **planner** | 작업 계획 에이전트. 작업 확인, 우선순위 정리, 태스크 분해 |
| **qa-engineer** | QA 엔지니어 에이전트. 테스트 케이스, 시나리오, 경계값 설계 및 테스트 코드 작성 |
| **doc-writer** | 문서 작성 에이전트. README, API 문서, 사용자 가이드, CHANGELOG 작성 |
| **code-explore** | 코드베이스 탐색 에이전트. 구현 찾기, 파일 위치 확인, 코드 구조 이해 |
| **web-explore** | 웹 탐색 및 요약 에이전트. 웹 검색, 페이지 가져오기, 온라인 정보 요약 |

### 스킬 (7개)

| 스킬 | 설명 |
|-----|------|
| **orchestrator** | TDD 기반 개발 오케스트레이터. Planner → Architect → QA → Implementer 순으로 조율 |
| **agent-creator** | 커스텀 서브에이전트 생성. `.claude/agents`에 새 에이전트 생성 |
| **skill-creator** | 효과적인 스킬 생성 가이드. Claude 기능을 워크플로우로 확장 |
| **mcp-builder** | MCP 서버 생성 가이드. Python/Node.js로 외부 서비스 통합 |
| **prompt-generator** | AI 에이전트를 위한 고품질 프롬프트 생성 |
| **hook-generator** | Claude Code Hooks 생성. 도구 실행 전후 검증, 알림 자동화 |
| **agent-manifest-aligner** | AGENTS.md와 CLAUDE.md 파일 간 연결 및 충돌 해결 |

## 사용 예시

### 오케스트레이터로 TDD 개발

```
사용자: /orchestrator 로그인 기능 추가해줘

→ Planner: 작업 분해 및 계획
→ Architect: 설계 결정
→ QA Engineer: 테스트 먼저 작성
→ Implementer: 테스트 통과하는 코드 구현
```

### 에이전트 생성

```
사용자: 코드 리뷰 에이전트 만들어줘
→ /agent-creator 또는 "에이전트 만들어줘" 트리거
→ 요구사항 수집 후 에이전트 파일 생성
```

### MCP 서버 구축

```
사용자: GitHub API 연동 MCP 서버 만들어줘
→ /mcp-builder 스킬 사용
→ Python(FastMCP) 또는 Node.js(MCP SDK)로 구현 가이드
```

### 프롬프트 생성

```
사용자: 코드 리뷰 스킬용 프롬프트 만들어줘
→ /prompt-generator 스킬 사용
→ 목적에 맞는 구조화된 프롬프트 생성
```

## 문서

- [에이전트 가이드](./docs/AGENTS.md) - 포함된 에이전트 상세 설명 및 사용법
- [스킬 가이드](./docs/SKILLS.md) - 포함된 스킬 상세 설명 및 사용법

## 프로젝트 구조

```
claude-devkit/
├── .claude-plugin/
│   └── marketplace.json      # 마켓플레이스 설정
├── plugins/
│   └── claude-devkit/
│       ├── .claude-plugin/
│       │   └── plugin.json   # 플러그인 메타데이터
│       ├── agents/           # 7개 에이전트
│       ├── skills/           # 7개 스킬
│       └── README.md
├── docs/
│   ├── AGENTS.md             # 에이전트 가이드
│   └── SKILLS.md             # 스킬 가이드
└── README.md
```

## 라이선스

MIT
