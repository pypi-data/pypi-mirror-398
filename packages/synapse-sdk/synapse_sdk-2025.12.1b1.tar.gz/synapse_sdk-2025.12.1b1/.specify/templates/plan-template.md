# 구현 계획: [기능명]

**Branch**: `[###-feature-name]` | **작성일**: [DATE] | **명세서**: [link]
**입력**: `/specs/[###-feature-name]/spec.md`의 기능 명세서

**참고**: 이 템플릿은 `/speckit.plan` 명령으로 작성됩니다. 실행 워크플로우는 `.specify/templates/commands/plan.md`를 참조하세요.

## 요약

[기능 명세서에서 추출: 주요 요구사항 + 연구에서 도출된 기술적 접근 방식]

## 기술 컨텍스트

<!--
  작업 필요: 이 섹션의 내용을 프로젝트의 기술 세부사항으로 교체하세요.
  여기 구조는 반복 프로세스를 안내하기 위한 참고용입니다.
-->

**Language/Version**: [예: Python 3.11, Swift 5.9, Rust 1.75 또는 명확화 필요]
**Primary Dependencies**: [예: FastAPI, UIKit, LLVM 또는 명확화 필요]
**Storage**: [해당되는 경우, 예: PostgreSQL, CoreData, files 또는 해당 없음]
**Testing**: [예: pytest, XCTest, cargo test 또는 명확화 필요]
**Target Platform**: [예: Linux server, iOS 15+, WASM 또는 명확화 필요]
**Project Type**: [single/web/mobile - 소스 구조 결정]
**Performance Goals**: [도메인별, 예: 1000 req/s, 10k lines/sec, 60 fps 또는 명확화 필요]
**Constraints**: [도메인별, 예: <200ms p95, <100MB memory, 오프라인 지원 또는 명확화 필요]
**Scale/Scope**: [도메인별, 예: 10k 사용자, 1M LOC, 50 화면 또는 명확화 필요]

## 헌법 점검

*게이트: Phase 0 연구 전에 통과해야 함. Phase 1 설계 후 재점검.*

| 원칙 | 게이트 | 상태 |
|------|--------|------|
| I. TDD | 구현 작업 전에 테스트가 정의되었는가? | ☐ |
| II. Tidy First | 구조적 변경과 동작 변경이 분리되었는가? | ☐ |
| III. 코드 품질 | 설계가 DRY, 단일 책임을 따르는가? | ☐ |
| IV. 커밋 규율 | 커밋이 작고 논리적인 단위로 계획되었는가? | ☐ |
| V. 단순성 | 불필요한 추상화나 과도한 엔지니어링이 없는가? | ☐ |

*참조: [헌법](.specify/memory/constitution.md)*

## 프로젝트 구조

### 문서 (이 기능)

```text
specs/[###-feature]/
├── plan.md              # 이 파일 (/speckit.plan 명령 출력)
├── research.md          # Phase 0 출력 (/speckit.plan 명령)
├── data-model.md        # Phase 1 출력 (/speckit.plan 명령)
├── quickstart.md        # Phase 1 출력 (/speckit.plan 명령)
├── contracts/           # Phase 1 출력 (/speckit.plan 명령)
└── tasks.md             # Phase 2 출력 (/speckit.tasks 명령 - /speckit.plan으로 생성되지 않음)
```

### 소스 코드 (저장소 루트)
<!--
  작업 필요: 아래 플레이스홀더 트리를 이 기능의 구체적인 레이아웃으로 교체하세요.
  사용하지 않는 옵션은 삭제하고 선택한 구조를 실제 경로로 확장하세요
  (예: apps/admin, packages/something). 전달된 계획에는 Option 레이블이
  포함되지 않아야 합니다.
-->

```text
# [사용하지 않으면 삭제] 옵션 1: 단일 프로젝트 (기본)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [사용하지 않으면 삭제] 옵션 2: 웹 애플리케이션 ("frontend" + "backend" 감지 시)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [사용하지 않으면 삭제] 옵션 3: 모바일 + API ("iOS/Android" 감지 시)
api/
└── [위 backend와 동일]

ios/ 또는 android/
└── [플랫폼별 구조: 기능 모듈, UI 플로우, 플랫폼 테스트]
```

**구조 결정**: [선택한 구조를 문서화하고 위에서 캡처한 실제 디렉토리를 참조]

## 복잡성 추적

> **헌법 점검에서 정당화가 필요한 위반 사항이 있는 경우에만 작성**

| 위반 사항 | 필요한 이유 | 더 단순한 대안을 거부한 이유 |
|-----------|-------------|------------------------------|
| [예: 4번째 프로젝트] | [현재 필요] | [3개 프로젝트로 충분하지 않은 이유] |
| [예: Repository 패턴] | [특정 문제] | [직접 DB 접근으로 충분하지 않은 이유] |
