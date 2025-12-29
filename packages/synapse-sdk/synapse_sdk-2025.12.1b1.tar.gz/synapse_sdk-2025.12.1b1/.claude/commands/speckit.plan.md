---
description: 계획 템플릿을 사용하여 설계 산출물을 생성하는 구현 계획 워크플로우를 실행합니다.
handoffs:
  - label: 작업 생성
    agent: speckit.tasks
    prompt: 계획을 작업으로 분해해주세요
    send: true
  - label: 체크리스트 생성
    agent: speckit.checklist
    prompt: 다음 도메인에 대한 체크리스트를 생성해주세요...
---

## 언어 설정

모든 출력과 사용자와의 대화는 **한국어**로 진행합니다.

## 사용자 입력

```text
$ARGUMENTS
```

입력이 비어있지 않다면 진행하기 전에 **반드시** 사용자 입력을 고려해야 합니다.

## 개요

1. **설정**: 저장소 루트에서 `.specify/scripts/bash/setup-plan.sh --json`을 실행하고 JSON에서 FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH를 파싱합니다. "I'm Groot"와 같이 인수에 작은따옴표가 있는 경우 이스케이프 구문 사용: 예: 'I'\''m Groot' (또는 가능하면 큰따옴표: "I'm Groot").

2. **컨텍스트 로드**: FEATURE_SPEC과 `.specify/memory/constitution.md`를 읽습니다. IMPL_PLAN 템플릿을 로드합니다 (이미 복사됨).

3. **계획 워크플로우 실행**: IMPL_PLAN 템플릿의 구조를 따라:
   - 기술 컨텍스트 작성 (알 수 없는 부분은 "명확화 필요"로 표시)
   - 헌법에서 헌법 점검 섹션 작성
   - 게이트 평가 (정당화되지 않은 위반이 있으면 ERROR)
   - Phase 0: research.md 생성 (모든 명확화 필요 해결)
   - Phase 1: data-model.md, contracts/, quickstart.md 생성
   - Phase 1: 에이전트 스크립트를 실행하여 에이전트 컨텍스트 업데이트
   - 설계 후 헌법 점검 재평가

4. **중지 및 보고**: Phase 2 계획 후 명령 종료. 브랜치, IMPL_PLAN 경로, 생성된 산출물 보고.

## 단계

### Phase 0: 개요 및 연구

1. **위의 기술 컨텍스트에서 미지정 항목 추출**:
   - 각 명확화 필요 → 연구 작업
   - 각 의존성 → 모범 사례 작업
   - 각 통합 → 패턴 작업

2. **연구 에이전트 생성 및 디스패치**:

   ```text
   기술 컨텍스트의 각 미지정 항목에 대해:
     Task: "{기능 컨텍스트}에 대한 {미지정 항목} 연구"
   각 기술 선택에 대해:
     Task: "{도메인}에서 {기술}의 모범 사례 찾기"
   ```

3. **연구 결과 통합** - `research.md`에 다음 형식으로:
   - 결정: [선택된 것]
   - 근거: [선택 이유]
   - 고려된 대안: [평가된 다른 것들]

**출력**: 모든 명확화 필요가 해결된 research.md

### Phase 1: 설계 및 계약

**전제조건:** `research.md` 완료

1. **기능 명세서에서 엔티티 추출** → `data-model.md`:
   - 엔티티 이름, 필드, 관계
   - 요구사항의 유효성 검사 규칙
   - 해당되는 경우 상태 전환

2. **기능 요구사항에서 API 계약 생성**:
   - 각 사용자 동작 → 엔드포인트
   - 표준 REST/GraphQL 패턴 사용
   - OpenAPI/GraphQL 스키마를 `/contracts/`에 출력

3. **에이전트 컨텍스트 업데이트**:
   - `.specify/scripts/bash/update-agent-context.sh claude` 실행
   - 이 스크립트들은 사용 중인 AI 에이전트를 감지
   - 적절한 에이전트별 컨텍스트 파일 업데이트
   - 현재 계획의 새 기술만 추가
   - 마커 사이의 수동 추가 사항 보존

**출력**: data-model.md, /contracts/*, quickstart.md, 에이전트별 파일

## 핵심 규칙

- 절대 경로 사용
- 게이트 실패 또는 해결되지 않은 명확화에 대해 ERROR
