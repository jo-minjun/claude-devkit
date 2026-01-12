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
  project_path: /Users/.../vroong-point-internal-api
  reference_path: /Users/.../vroong-hectofinancial-epm  # 참고 프로젝트 (있는 경우)
  created_at: 2024-01-15T10:00:00
  updated_at: 2024-01-15T14:30:00

  # 현재 진행 상태
  current_task: M2
  current_phase: implementation

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
    - path: src/main/.../HectoMpsStore.java
      summary: "상점 엔티티. 필드: mid, description. 메서드: create, update"
      explored_at: M1

    - path: src/main/.../HectoMpsCustomer.java
      summary: "회원 엔티티. 필드: pointAccountNo, customerId 등"
      explored_at: M1

  # Contract 저장소
  contracts:
    design_brief: |
      task_name: Service 레이어 구현
      objective: Store, Customer, Mtrdno 서비스 구현
      completion_criteria:
        - HectoMpsStoreService CRUD
        - HectoMpsCustomerService CRUD
      scope_in:
        - Service 클래스 구현
      scope_out:
        - Controller 구현

    design_contract: |
      task: Service 레이어 구현
      invariants:
        - Service는 Repository만 의존
        - Entity에 비즈니스 로직 위임
      interfaces:
        - name: HectoMpsStoreService
          methods: [listStores, createStore, getStore, updateStore]

    test_contract: |
      task: Service 레이어 구현
      test_cases:
        - name: createStore_정상_생성
          target: HectoMpsStoreService.createStore
      test_file_path: src/test/.../HectoMpsStoreServiceTest.java

    test_result: null  # 테스트 실행 후 채워짐
```

## 세션 라이프사이클

### 1. 세션 생성 (오케스트레이터 시작 시)

```
조건: 세션 파일이 없거나 24시간 이상 경과
동작:
  1. 새 세션 파일 생성
  2. 프로젝트 경로, 참고 프로젝트 설정
  3. Discovery 페이즈 실행
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
# Implementer 호출 시 자동 주입
injected_context:
  project: "{{session.project_path}}"
  reference: "{{session.reference_path}}"
  task: "{{session.current_task}}"
  design_contract: "{{session.contracts.design_contract}}"
  test_contract: "{{session.contracts.test_contract}}"
  explored_files: "{{session.explored_files | summary}}"
```

### 탐색 결과 재사용

```yaml
# 이미 탐색된 파일은 요약만 제공
explored_files_summary: |
  [이미 분석된 파일]
  - HectoMpsStore.java: 상점 엔티티. create, update 메서드 보유
  - HectoMpsCustomer.java: 회원 엔티티. FK로 Store 참조

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
║  Project: vroong-point-internal-api                       ║
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