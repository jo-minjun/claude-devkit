# 페이즈 상세

오케스트레이션 루프의 각 페이즈별 상세 절차.

---

## 페이즈 흐름도

```
[Planning] ─── Design Brief ───→ [Design]
     ↑                              │
     │                       Design Contract
     │                              ↓
     │                        [Test First]
     │                              │
     │ GATE-3,4 위반           Test Contract
     │                         + 테스트 코드
     │                              ↓
     └─────────────────────── [Implementation]
                                    │
                              GATE-1 통과 필수
                                    │
                               구현 코드
                                    ↓
                             [Verification]
                                    │
                              GATE-2 통과 필수
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              테스트 실패                      테스트 통과
                    │                               │
                    ↓                               ↓
             [Implementation]                 [Complete]
              또는 [Design]
```

---

## 1. Planning 페이즈

### 담당 에이전트
Planner

### 입력
- 사용자 원본 요청
- 프로젝트 컨텍스트 (CLAUDE.md, 디렉토리 구조)

### 절차
1. 사용자 요청 분석
2. 단일 작업으로 축소 (큰 요청은 분할)
3. 완료 조건 정의
4. 스코프 경계 설정 (scope_in / scope_out)
5. Design Brief 생성

### 출력
Design Brief

### 다음 페이즈
Design

### 실패 조건
- 요청이 모호하여 작업 정의 불가 → 사용자에게 명확화 요청

---

## 2. Design 페이즈

### 담당 에이전트
Architect

### 입력
- Design Brief
- 프로젝트 아키텍처 패턴 (DDD 레이어 등)
- 기존 인터페이스/타입 정의

### 절차
1. Design Brief 검토
2. 설계 불변 조건 정의
3. 인터페이스 계약 작성
4. 의존성 경계 설정
5. 레이어 할당
6. Design Contract 생성

### 출력
Design Contract

### 다음 페이즈
Test First

### 실패 조건
- 기존 아키텍처와 충돌 → Design Brief 수정 필요 (Planning 복귀)

---

## 3. Test First 페이즈

### 담당 에이전트
QA Engineer

### 입력
- Design Contract
- 프로젝트 테스트 프레임워크 (JUnit 5 등)
- 기존 테스트 패턴

### 절차
1. Design Contract의 인터페이스별 테스트 케이스 설계
2. Given-When-Then 형식으로 명세
3. 카테고리 분류 (happy_path, error_case, edge_case)
4. 테스트 코드 작성 (Red 상태 - 컴파일만 되고 실패)
5. Test Contract 생성

### 출력
- Test Contract
- 테스트 코드 파일

### 다음 페이즈
Implementation (GATE-1 통과 필수)

### 게이트 검증
**GATE-1**: Test Contract와 테스트 코드가 존재해야 함

---

## 4. Implementation 페이즈

### 담당 에이전트
Implementer

### 입력
- Design Contract (불변 조건)
- Test Contract (통과해야 할 테스트)
- 테스트 코드 (전문)

### 절차
1. 테스트 코드 분석
2. 테스트 통과를 위한 최소 구현
3. 설계 불변 조건 준수 확인
4. 스코프 확장 금지 (scope_out 구현 금지)
5. 빌드 성공 확인

### 출력
구현 코드

### 다음 페이즈
Verification

### 게이트 검증 (Verification 전)
- **GATE-3**: 스코프 변경 없음
- **GATE-4**: 설계 불변 조건 유지

### 주의사항
- 테스트가 요구하지 않는 기능 추가 금지
- 불필요한 추상화 금지
- 설계 위반 발견 시 즉시 중단하고 보고

---

## 5. Verification 페이즈

### 담당 에이전트
QA Engineer

### 입력
- 구현된 코드
- Test Contract
- 테스트 실행 명령

### 절차
1. 테스트 실행 (`./gradlew test`)
2. 결과 수집
3. 실패 시 원인 분석 및 분류
4. Test Result Report 생성
5. 다음 action 결정

### 출력
Test Result Report

### 다음 페이즈 결정

| 결과 | action | 다음 페이즈 |
|------|--------|------------|
| 모든 테스트 통과 | COMPLETE | Complete |
| 구현 오류 | RETRY_IMPLEMENTATION | Implementation |
| 설계 위반 | RETRY_DESIGN | Design |

### 게이트 검증
**GATE-2**: 테스트 실행 결과가 존재해야 함

---

## 6. Complete 페이즈

### 조건
- GATE-2 통과 (테스트 결과 존재)
- 모든 테스트 통과

### 절차
1. 최종 상태 출력
2. 작업 완료 선언
3. (선택) Doc Writer 에이전트 호출하여 문서화

### 출력
작업 완료 리포트

---

## 페이즈 전환 요약

| 현재 페이즈 | 성공 시 | 실패 시 |
|------------|--------|--------|
| Planning | → Design | 사용자 명확화 요청 |
| Design | → Test First | → Planning |
| Test First | → Implementation | - |
| Implementation | → Verification | → Planning (GATE-3) 또는 → Design (GATE-4) |
| Verification | → Complete | → Implementation 또는 → Design |
| Complete | 종료 | - |
