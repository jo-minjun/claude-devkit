# Contract 형식

오케스트레이터가 페이즈 간 전달하는 계약 문서 형식이다.

---

## Design Brief

Planner → Architect로 전달되는 작업 정의서.

### 형식

```yaml
design_brief:
  task_name: 사용자 인증 기능
  objective: JWT 기반 로그인/로그아웃 구현

  completion_criteria:
    - 로그인 API 동작
    - JWT 토큰 발급
    - 토큰 검증 미들웨어 동작

  scope_in:
    - POST /auth/login 엔드포인트
    - POST /auth/logout 엔드포인트
    - JwtTokenProvider 클래스
    - JwtAuthenticationFilter

  scope_out:
    - 회원가입 기능
    - 소셜 로그인
    - 리프레시 토큰
    - 비밀번호 재설정

  dependencies:
    - Spring Security 설정
    - User 엔티티 (기존)
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| task_name | 작업 식별 이름 |
| objective | 달성 목표 (1-2문장) |
| completion_criteria | 완료 판단 기준 목록 |
| scope_in | 구현 범위 내 항목 |
| scope_out | 명시적 제외 항목 |

---

## Design Contract

Architect → QA Engineer로 전달되는 설계 명세서.

### 형식

```yaml
design_contract:
  task: 사용자 인증 기능

  invariants:
    - 도메인 레이어는 인프라에 의존하지 않는다
    - 모든 인증 로직은 AuthService를 통해 처리한다
    - 토큰 생성/검증은 JwtTokenProvider에 캡슐화한다

  interfaces:
    - name: AuthService
      input: LoginRequest(email, password)
      output: TokenResponse(accessToken, expiresIn)
      contract: 유효한 자격증명 시 토큰 반환, 실패 시 AuthenticationException

    - name: JwtTokenProvider
      input: Authentication
      output: String (JWT)
      contract: 표준 JWT 형식, 만료 시간 포함

  boundaries:
    - Controller는 AuthService만 의존
    - AuthService는 UserRepository 인터페이스만 의존
    - JwtTokenProvider는 순수 유틸리티 (외부 의존 없음)

  layer_assignments:
    - component: AuthController
      layer: presentation
    - component: AuthService
      layer: application
    - component: JwtTokenProvider
      layer: infrastructure
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| task | 대상 작업명 |
| invariants | 절대 위반 불가 규칙 |
| interfaces | 공개 인터페이스 계약 |
| boundaries | 의존성 경계 규칙 |

---

## Test Contract

QA Engineer → Implementer로 전달되는 테스트 명세서.

### 형식

```yaml
test_contract:
  task: 사용자 인증 기능

  test_cases:
    - name: 유효한_자격증명으로_로그인_성공
      target: AuthService.login
      given: 등록된 사용자 (email, password)
      when: login(LoginRequest) 호출
      then: TokenResponse 반환, accessToken 비어있지 않음
      category: happy_path

    - name: 잘못된_비밀번호로_로그인_실패
      target: AuthService.login
      given: 등록된 사용자, 틀린 비밀번호
      when: login(LoginRequest) 호출
      then: AuthenticationException 발생
      category: error_case

    - name: 존재하지_않는_사용자_로그인_실패
      target: AuthService.login
      given: 미등록 이메일
      when: login(LoginRequest) 호출
      then: AuthenticationException 발생
      category: error_case

    - name: 빈_이메일로_로그인_시_검증_실패
      target: AuthController.login
      given: 빈 문자열 이메일
      when: POST /auth/login 호출
      then: 400 Bad Request
      category: edge_case

  coverage_targets:
    - AuthService.login
    - AuthService.logout
    - JwtTokenProvider.createToken
    - JwtTokenProvider.validateToken

  test_file_path: src/test/java/me/minjun/auth/AuthServiceTest.java
```

### 필수 필드

| 필드 | 설명 |
|------|------|
| task | 대상 작업명 |
| test_cases | Given-When-Then 형식 테스트 목록 |
| coverage_targets | 커버리지 대상 메서드 |
| test_file_path | 테스트 파일 경로 |

### 테스트 카테고리

| 카테고리 | 설명 |
|----------|------|
| happy_path | 정상 흐름 |
| error_case | 예외/에러 흐름 |
| edge_case | 경계값, 특수 케이스 |

---

## Test Result Report

QA Engineer (Verification) → Orchestrator로 전달되는 테스트 결과.

### 형식

```yaml
test_result:
  execution:
    command: ./gradlew test
    timestamp: 2024-01-15T10:30:00
    result: PASS  # 또는 FAIL

  summary:
    total: 4
    passed: 4
    failed: 0
    skipped: 0

  failed_tests: []  # 실패 시 목록
  #  - name: 테스트명
  #    reason: 실패 원인
  #    category: implementation_error | design_violation | test_error

  recommendation:
    action: COMPLETE  # COMPLETE | RETRY_IMPLEMENTATION | RETRY_DESIGN
    reason: 모든 테스트 통과
```

### 실패 시 action 결정 기준

| 실패 유형 | action | 이유 |
|----------|--------|------|
| implementation_error | RETRY_IMPLEMENTATION | 구현 버그 수정 필요 |
| design_violation | RETRY_DESIGN | 설계 재검토 필요 |
| test_error | RETRY_IMPLEMENTATION | 테스트 또는 구현 수정 |
