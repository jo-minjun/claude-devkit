# 스킬 가이드

claude-devkit에 포함된 7개의 스킬에 대한 상세 가이드입니다.

## 목차

- [개요](#개요)
- [스킬 목록](#스킬-목록)
  - [orchestrator](#orchestrator)
  - [agent-creator](#agent-creator)
  - [skill-creator](#skill-creator)
  - [mcp-builder](#mcp-builder)
  - [prompt-generator](#prompt-generator)
  - [hook-generator](#hook-generator)
  - [agent-manifest-aligner](#agent-manifest-aligner)
- [스킬 사용법](#스킬-사용법)

---

## 개요

스킬은 Claude Code의 기능을 확장하는 재사용 가능한 워크플로우입니다. 자연어 요청이나 명시적 명령어로 트리거됩니다.

### 스킬의 특징

- **자동 선택**: Claude가 요청을 분석하여 적절한 스킬 자동 실행
- **명시적 호출**: `/skill-name` 형식으로 직접 호출 가능
- **재사용 가능**: 반복되는 워크플로우를 표준화

---

## 스킬 목록

### orchestrator

**TDD 기반 개발 오케스트레이터**

여러 에이전트를 조율하여 테스트 주도 개발 루프를 자동으로 실행합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "~해줘", "~만들어줘", "~추가해줘", "~구현해줘" |
| 명시적 호출 | `/orchestrator` |

#### 실행 흐름

```
Planning → Design → Test First → Implementation → Verification
    ↑                                                    │
    └────────────────────────────────────────────────────┘
                    (테스트 실패 시 복귀)
```

#### 에이전트 호출 순서

| 순서 | 에이전트 | 역할 | 출력 |
|------|---------|------|------|
| 1 | Planner | 작업 정의 | Design Brief |
| 2 | Architect | 설계 확정 | Design Contract |
| 3 | QA Engineer | 테스트 작성 | Test Contract + 테스트 코드 |
| 4 | Implementer | 구현 | 구현 코드 |
| 5 | QA Engineer | 테스트 실행 | Test Result Report |

#### 게이트 규칙

| Gate | 조건 | 위반 시 |
|------|------|--------|
| GATE-1 | Test Contract 존재 | Implementation 차단 |
| GATE-2 | 테스트 결과 존재 | Complete 차단 |
| GATE-3 | 스코프 변경 없음 | Planning 복귀 |

#### 사용 예시

```
사용자: 로그인 기능 추가해줘

→ orchestrator 자동 발동
→ [Planner] 작업 분해
→ [Architect] 설계 결정
→ [QA Engineer] 테스트 먼저 작성
→ [Implementer] 테스트 통과하는 코드 구현
→ [QA Engineer] 테스트 실행 및 검증
→ 완료
```

---

### agent-creator

**커스텀 에이전트 생성 스킬**

새로운 서브에이전트를 생성합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "에이전트 만들어줘", "서브에이전트 추가" |
| 명시적 호출 | `/agent-creator` |

#### 수집 정보

1. **이름**: 소문자와 하이픈 (예: `code-reviewer`)
2. **목적**: 에이전트가 하는 일
3. **도구**: 필요한 도구 목록
4. **모델**: sonnet, opus, haiku, inherit
5. **위치**: `.claude/agents/` 또는 `~/.claude/agents/`

#### 에이전트 템플릿

```markdown
---
name: my-agent
description: 목적과 사용 시점 설명
tools: Read, Edit, Bash
model: sonnet
---

에이전트의 역할과 동작 설명
```

#### 사용 예시

```
사용자: 코드 리뷰 에이전트 만들어줘

→ [agent-creator] 요구사항 수집
   - 이름: code-reviewer
   - 목적: 코드 품질 검토
   - 도구: Read, Grep, Glob
→ .claude/agents/code-reviewer.md 생성
→ 즉시 사용 가능
```

---

### skill-creator

**스킬 생성 가이드**

Claude의 기능을 확장하는 새로운 스킬을 생성합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "스킬 만들어줘", "스킬 생성" |
| 명시적 호출 | `/skill-creator` |

#### 스킬 구조

```
skills/my-skill/
├── SKILL.md          # 필수: 스킬 지시사항
├── scripts/          # 선택: 실행 스크립트
├── references/       # 선택: 참고 문서
└── assets/           # 선택: 템플릿, 설정 파일
```

#### 포함된 유틸리티

- `scripts/init_skill.py`: 스킬 초기화
- `scripts/package_skill.py`: 스킬 패키징
- `scripts/quick_validate.py`: 유효성 검사

---

### mcp-builder

**MCP 서버 생성 가이드**

외부 서비스와 통합하는 MCP(Model Context Protocol) 서버를 구축합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "MCP 서버 만들어줘", "API 연동" |
| 명시적 호출 | `/mcp-builder` |

#### 지원 언어/프레임워크

- **Python**: FastMCP
- **Node.js/TypeScript**: MCP SDK

#### 워크플로우

1. 심층 리서치 및 계획
2. API 문서 분석
3. 도구 설계 (명명, 설명, 파라미터)
4. 서버 구현
5. 테스트 및 검증

#### 참조 문서

- `reference/mcp_best_practices.md`: MCP 베스트 프랙티스
- `reference/python_mcp_server.md`: Python 서버 가이드
- `reference/node_mcp_server.md`: Node.js 서버 가이드
- `reference/evaluation.md`: 품질 평가 기준

---

### prompt-generator

**프롬프트 생성 스킬**

AI 에이전트를 위한 고품질 프롬프트를 생성합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "프롬프트 만들어줘", "프롬프트 생성" |
| 명시적 호출 | `/prompt-generator` |

#### 지원하는 프롬프트 유형

| 유형 | 참조 문서 |
|------|----------|
| 스킬용 | `references/skill-guide.md` |
| 에이전트용 | `references/agent-guide.md` |
| MCP 서버용 | `references/mcp-guide.md` |
| 일반 코딩용 | `references/coding-guide.md` |

#### 사용 예시

```
사용자: 코드 리뷰 스킬용 프롬프트 만들어줘

→ [prompt-generator] 목적 분석
→ 구조화된 프롬프트 생성
→ 클립보드에 복사 (선택)
```

---

### hook-generator

**Claude Code Hooks 생성 스킬**

도구 실행 전후 검증, 알림 전송을 자동화하는 훅을 생성합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "훅 만들어줘", "hook 생성" |
| 명시적 호출 | `/hook-generator` |

#### 훅 유형

| 유형 | 설명 | 사용 사례 |
|------|------|----------|
| PreToolUse | 도구 실행 전 검증 | 민감 파일 보호, 명령어 차단 |
| PostToolUse | 도구 실행 후 처리 | 린트, 포맷팅, 로깅 |
| Notification | 알림 전송 | Slack, 이메일, 시스템 알림 |
| Stop | 세션 종료 시 정리 | 리소스 정리, 보고서 생성 |

#### 생성 위치

- 스크립트: `.claude/hooks/`
- 설정: `.claude/settings.json`

#### 사용 예시

```
사용자: .env 파일 보호하는 훅 만들어줘

→ [hook-generator] PreToolUse 훅 생성
→ .claude/hooks/protect-env.sh 생성
→ settings.json에 훅 설정 추가
```

---

### agent-manifest-aligner

**AGENTS.md와 CLAUDE.md 정렬 스킬**

프로젝트의 에이전트 매니페스트 파일 간 연결 및 충돌을 해결합니다.

| 속성 | 값 |
|------|-----|
| 트리거 | "AGENTS.md 연결", "매니페스트 정렬" |
| 명시적 호출 | `/agent-manifest-aligner` |

#### 기능

1. **파일 존재 확인**: AGENTS.md, CLAUDE.md 존재 여부 체크
2. **심볼릭 링크 설정**: CLAUDE.md → AGENTS.md 링크 생성
3. **충돌 감지 및 해결**: 두 파일 내용이 다를 때 사용자에게 확인

#### 포함된 스크립트

- `scripts/check_files.sh`: 파일 존재 확인
- `scripts/create_symlink.sh`: 심볼릭 링크 생성
- `scripts/detect_conflicts.py`: 충돌 감지

---

## 스킬 사용법

### 자동 트리거

자연어로 요청하면 Claude가 적절한 스킬을 자동으로 선택합니다.

```
사용자: 로그인 기능 추가해줘
→ orchestrator 스킬 자동 발동

사용자: 코드 리뷰 에이전트 만들어줘
→ agent-creator 스킬 자동 발동
```

### 명시적 호출

슬래시 명령어로 직접 호출할 수 있습니다.

```
/orchestrator
/agent-creator
/mcp-builder
/prompt-generator
/hook-generator
```

### 스킬 조합

복잡한 작업에서 여러 스킬이 순차적으로 실행될 수 있습니다.

```
1. /agent-creator로 새 에이전트 생성
2. /hook-generator로 품질 검증 훅 추가
3. orchestrator가 실제 개발 작업 수행
```

---

## 참고

- [← README로 돌아가기](../README.md)
- [에이전트 가이드](./AGENTS.md)
