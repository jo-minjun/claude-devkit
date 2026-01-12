# 세션 컨텍스트 관리

오케스트레이터는 세션 파일을 통해 작업 진행 상태와 Contract를 관리한다.

## 세션 파일 위치

```
~/.claude/claude-devkit/sessions/
└── {project-hash}.yaml    # 프로젝트별 세션 파일
```

`project-hash`는 프로젝트 경로의 해시값 (충돌 방지).

## 세션 파일 구조

```yaml
# ~/.claude/claude-devkit/sessions/{hash}.yaml
session:
  # 메타데이터
  project_path: /Users/.../my-project
  reference_path: /Users/.../reference-project  # 참고 프로젝트 (있는 경우)
  created_at: 2024-01-15T10:00:00
  updated_at: 2024-01-15T14:30:00

  # 프로젝트 매니페스트 (Code Explore가 탐색)
  project_manifest:
    claude_md: /Users/.../my-project/CLAUDE.md  # 없으면 null
    agents_md: /Users/.../my-project/docs/AGENTS.md  # 없으면 null

  # 현재 진행 상태
  current_task: M2
  current_phase: implementation  # parallel_discovery | merge | design | test_first | implementation | verification | complete

  # 병렬 탐색 상태 (Parallel Discovery용)
  parallel_discovery:
    status: completed  # pending | running | completed
    code_explore:
      status: completed
      started_at: 2024-01-15T10:00:00
      completed_at: 2024-01-15T10:01:30
    planner:
      status: completed
      started_at: 2024-01-15T10:00:00
      completed_at: 2024-01-15T10:02:00

  # 작업 목록
  tasks:
    - id: M1
      name: Repository 인터페이스 생성
      status: completed
      completed_at: 2024-01-15T11:00:00

    - id: M2
      name: Service 레이어 구현
      status: in_progress
      started_at: 2024-01-15T11:00:00

    - id: M3
      name: Controller 구현
      status: pending

  # 탐색 결과 캐시
  explored_files:
    - path: src/main/.../Store.java
      summary: "상점 엔티티. 필드: id, name. 메서드: create, update"
      explored_at: M1

    - path: src/main/.../Customer.java
      summary: "고객 엔티티. 필드: id, email 등"
      explored_at: M1

  # Contract 저장소
  contracts:
    # 잠정 Design Brief (Planner가 코드탐색 없이 생성)
    preliminary_design_brief: |
      task_name: Service 레이어 구현
      objective: Store, Customer 서비스 구현
      assumptions:
        - "서비스 클래스는 src/main/service에 위치할 것"
        - "Repository 인터페이스가 이미 존재할 것"
      completion_criteria:
        - StoreService CRUD
      scope_in:
        - Service 클래스 구현 (추정)
      scope_out:
        - Controller 구현

    # 최종 Design Brief (Merge 후 생성)
    design_brief: |
      task_name: Service 레이어 구현
      objective: Store, Customer 서비스 구현
      completion_criteria:
        - StoreService CRUD
        - CustomerService CRUD
      scope_in:
        - src/main/java/com/example/service/StoreService.java
      scope_out:
        - Controller 구현

    design_contract: |
      task: Service 레이어 구현
      invariants:
        - Service는 Repository만 의존
        - Entity에 비즈니스 로직 위임
      interfaces:
        - name: StoreService
          methods: [list, create, get, update]

    test_contract: |
      task: Service 레이어 구현
      test_cases:
        - name: createStore_정상_생성
          target: StoreService.create
      test_file_path: src/test/.../StoreServiceTest.java

    test_result: null  # 테스트 실행 후 채워짐
```

## 세션 라이프사이클

### 1. 세션 생성 (오케스트레이터 시작 시)

```
조건: 세션 파일이 없거나 24시간 이상 경과
동작:
  1. 새 세션 파일 생성
  2. 프로젝트 경로, 참고 프로젝트 설정
  3. current_phase = "parallel_discovery"
  4. Parallel Discovery 페이즈 실행
```

### 1.5. Parallel Discovery (병렬 탐색)

```
동작:
  1. parallel_discovery.status = "running"
  2. 병렬로 두 Task 에이전트 호출:
     - Code Explore: 프로젝트 구조 탐색
     - Planner: 잠정 Design Brief 생성
  3. 각 Task 완료 시 상태 업데이트:
     - Code Explore 완료 → explored_files 저장
     - Planner 완료 → preliminary_design_brief 저장
  4. 두 Task 모두 완료 시:
     - parallel_discovery.status = "completed"
     - current_phase = "merge"
```

### 1.6. Merge (결과 병합)

```
동작:
  1. explored_files와 preliminary_design_brief 비교
  2. assumptions 검증:
     - 맞는 가정: scope_in 구체화 (실제 경로로 교체)
     - 틀린 가정: 실제 구조에 맞게 수정
  3. 최종 design_brief 생성 → contracts.design_brief
  4. current_phase = "design"
  5. 가정 50% 이상 불일치 시: Planner 재호출 (순차 모드)
```

### 2. 세션 업데이트 (매 페이즈 완료 후)

```
동작:
  1. current_phase 업데이트
  2. 해당 Contract 저장
  3. updated_at 갱신
```

### 3. 작업 완료 시

```
동작:
  1. 현재 작업 status: completed
  2. 다음 작업 status: in_progress
  3. contracts 초기화 (다음 작업용)
```

### 4. 세션 종료 조건

```
- 모든 작업 완료
- 사용자 명시적 종료 (/orchestrator stop)
- 24시간 비활성
```

## 세션 활용

### 서브에이전트 호출 시 컨텍스트 주입

오케스트레이터는 서브에이전트 호출 전 세션 파일에서 필요한 정보를 추출하여 주입한다.

```yaml
# 모든 에이전트 공통 주입
injected_context:
  project: "{{session.project_path}}"
  reference: "{{session.reference_path}}"
  task: "{{session.current_task}}"
  project_manifest: "{{session.project_manifest}}"  # CLAUDE.md, AGENTS.md 경로
  explored_files: "{{session.explored_files | summary}}"

# Architect, Implementer, QA Engineer 추가 주입
  design_contract: "{{session.contracts.design_contract}}"
  test_contract: "{{session.contracts.test_contract}}"
```

**project_manifest 활용:**
- 에이전트들은 `project_manifest.claude_md` 경로로 프로젝트 규칙 파일을 직접 읽을 수 있음
- CLAUDE.md가 없으면 null이므로 존재 여부 확인 후 사용

### 탐색 결과 재사용

```yaml
# 이미 탐색된 파일은 요약만 제공
explored_files_summary: |
  [이미 분석된 파일]
  - Store.java: 상점 엔티티. create, update 메서드 보유
  - Customer.java: 고객 엔티티. FK로 Store 참조

  상세 내용 필요 시 Read 도구로 직접 조회하세요.
```

## 명령어

### 세션 상태 확인

```
/orchestrator status
```

출력:
```
╔══════════════════════════════════════════════════════════╗
║  Orchestrator Session                                     ║
║  Project: my-project                                      ║
╠══════════════════════════════════════════════════════════╣
║                                                           ║
║  M1 Repository    ✅ completed                            ║
║  M2 Service       🔄 in_progress  ← current               ║
║  M3 Controller    ⏳ pending                              ║
║                                                           ║
║  Phase: Implementation                                    ║
║  Gate: GATE-1 ✅ GATE-3 ⏳ GATE-4 ⏳                       ║
║                                                           ║
╚══════════════════════════════════════════════════════════╝
```

### 세션 초기화

```
/orchestrator reset
```

### 세션 재개

```
/orchestrator resume
```