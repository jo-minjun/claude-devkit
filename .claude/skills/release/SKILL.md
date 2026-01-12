---
name: release
description: 버전 릴리스 자동화. CHANGELOG.md 업데이트, 플러그인 버전 파일 수정, Git 커밋까지 일괄 처리한다. "릴리스", "release", "버전 업데이트", "version bump", "배포 준비" 요청 시 트리거된다.
---

# 버전 릴리스

CHANGELOG.md와 플러그인 버전 파일들을 일괄 업데이트하고 Git 커밋까지 자동화한다.

## 워크플로우

### 1. 현재 버전 확인

`plugins/claude-devkit/.claude-plugin/plugin.json`에서 현재 버전을 읽는다.

```bash
cat plugins/claude-devkit/.claude-plugin/plugin.json | grep '"version"'
```

### 2. 새 버전 결정

사용자에게 버전 유형을 질문한다:

| 유형 | 설명 | 예시 |
|------|------|------|
| major | 호환성 깨지는 변경 | 1.0.0 → 2.0.0 |
| minor | 새 기능 추가 | 1.0.0 → 1.1.0 |
| patch | 버그 수정/개선 | 1.0.0 → 1.0.1 |

또는 사용자가 직접 버전을 지정할 수 있다.

### 3. 변경사항 수집

다음 중 하나로 변경사항을 수집한다:

1. **사용자 입력**: 변경사항을 직접 설명
2. **최근 커밋**: `git log` 에서 추출

변경사항은 다음 카테고리로 분류:
- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Fixed**: 버그 수정
- **Removed**: 제거된 기능

### 4. 파일 업데이트

다음 파일들을 업데이트한다:

| 파일 | 수정 내용 |
|------|----------|
| `plugins/claude-devkit/CHANGELOG.md` | 새 버전 섹션 추가 |
| `.claude-plugin/marketplace.json` | `metadata.version` 업데이트 |
| `plugins/claude-devkit/.claude-plugin/plugin.json` | `version` 업데이트 |

### 5. Git 커밋

파일 업데이트 후 자동으로 커밋한다:

```bash
git add .

git commit -m "$(cat <<'EOF'
release: vX.Y.Z

- CHANGELOG.md 업데이트
- 플러그인 버전 업데이트 (X.Y.Z-1 → X.Y.Z)
EOF
)"
```

### 6. 결과 출력

```
## 릴리스 완료

버전: X.Y.Z-1 → X.Y.Z
날짜: YYYY-MM-DD

### 수정된 파일
- plugins/claude-devkit/CHANGELOG.md
- .claude-plugin/marketplace.json
- plugins/claude-devkit/.claude-plugin/plugin.json

### 변경사항 요약
- Added: ...
- Changed: ...

### Git
커밋 완료: release: vX.Y.Z
```

## CHANGELOG 형식

[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 형식을 따른다:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- 새로운 기능

### Changed
- 변경된 기능

### Fixed
- 버그 수정

### Removed
- 제거된 기능
```

## 제약사항

- [Semantic Versioning](https://semver.org/) 준수
- 날짜는 ISO 8601 형식 (YYYY-MM-DD)
- CHANGELOG는 최신 버전이 위에 오도록 정렬
