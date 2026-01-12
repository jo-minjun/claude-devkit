# 게이트 규칙

오케스트레이터가 다음 단계로 진행하기 전 검증하는 규칙이다.

## 게이트 요약

| Gate | 검증 시점 | 조건 | 위반 시 동작 |
|------|----------|------|-------------|
| GATE-1 | Implementation 진입 전 | Test Contract 존재 | Implementation 진입 차단 |
| GATE-2 | Complete 선언 전 | 테스트 실행 결과 존재 | Complete 선언 차단 |
| GATE-3 | Implementation 완료 후 | 스코프 변경 없음 | Planning으로 복귀 |
| GATE-4 | Implementation 완료 후 | 설계 불변 조건 유지 | Design으로 복귀 |

---

## GATE-1: Test Contract 필수

### 목적
테스트 없이 구현을 시작하는 것을 방지한다.

### 검증 항목
```yaml
required:
  - Test Contract 문서 존재
  - 최소 1개 이상의 test_cases 정의
  - 테스트 파일 경로 명시 (test_file_path)
  - 테스트 코드 생성 완료
```

### 위반 시
- Implementation 페이즈 진입 차단
- "Test First 페이즈로 복귀" 메시지 출력
- QA Engineer 에이전트 재호출

---

## GATE-2: 테스트 결과 필수

### 목적
테스트 실행 없이 완료 선언하는 것을 방지한다.

### 검증 항목
```yaml
required:
  - 테스트 실행 명령 실행됨
  - 테스트 결과 리포트 존재
  - result 필드가 PASS 또는 FAIL
  - PASS인 경우에만 Complete 허용
```

### 위반 시
- Complete 선언 차단
- FAIL인 경우: Implementation 또는 Design으로 복귀
- 미실행인 경우: Verification 페이즈 재실행

---

## GATE-3: 스코프 확장 금지

### 목적
요청 범위를 벗어난 구현을 방지한다.

### 검증 항목
```yaml
compare:
  - Design Brief의 scope_in vs 실제 구현
  - Design Brief의 scope_out 항목이 구현되지 않았는지
  - 새로운 파일/클래스가 스코프 내인지
```

### 위반 사례
- scope_out에 명시된 기능 구현
- 요청하지 않은 리팩토링
- 불필요한 유틸리티 클래스 추가

### 위반 시
- Planning 페이즈로 즉시 복귀
- 스코프 재정의 필요
- 확장된 부분 제거 또는 별도 작업으로 분리

---

## GATE-4: 설계 불변 조건 유지

### 목적
아키텍트가 정의한 설계 원칙 위반을 방지한다.

### 검증 항목
```yaml
verify:
  - Design Contract의 invariants 모두 충족
  - interfaces 계약 준수
  - boundaries 위반 없음
  - layer_assignments 준수 (DDD 레이어 규칙)
```

### 위반 사례
- 도메인 레이어에서 인프라 의존성 추가
- 인터페이스 시그니처 임의 변경
- 불변 조건에 명시된 규칙 무시

### 위반 시
- Design 페이즈로 즉시 복귀
- Architect 에이전트 재호출
- 설계 재검토 또는 불변 조건 수정

---

## 게이트 검증 순서

```
Implementation 완료 후:
  1. GATE-3 검증 (스코프)
  2. GATE-4 검증 (설계 불변)
  3. 통과 시 → Verification 진행

Verification 완료 후:
  1. GATE-2 검증 (테스트 결과)
  2. 통과 시 → Complete

Implementation 진입 전:
  1. GATE-1 검증 (Test Contract)
  2. 통과 시 → Implementation 진행
```
