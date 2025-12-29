---
description: 사용 가능한 설계 산출물을 기반으로 기존 작업을 의존성 순서가 지정된 실행 가능한 GitHub 이슈로 변환합니다.
tools: ['github/github-mcp-server/issue_write']
---

## 언어 설정

모든 출력과 사용자와의 대화는 **한국어**로 진행합니다.

## 사용자 입력

```text
$ARGUMENTS
```

입력이 비어있지 않다면 진행하기 전에 **반드시** 사용자 입력을 고려해야 합니다.

## 개요

1. 저장소 루트에서 `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`를 실행하고 FEATURE_DIR과 AVAILABLE_DOCS 목록을 파싱합니다. 모든 경로는 절대 경로여야 합니다. "I'm Groot"와 같이 인수에 작은따옴표가 있는 경우 이스케이프 구문 사용: 예: 'I'\\''m Groot' (또는 가능하면 큰따옴표: "I'm Groot").
1. 실행된 스크립트에서 **tasks** 경로를 추출합니다.
1. 다음을 실행하여 Git remote를 확인합니다:

```bash
git config --get remote.origin.url
```

**REMOTE가 GITHUB URL인 경우에만 다음 단계로 진행**

1. 목록의 각 작업에 대해, GitHub MCP 서버를 사용하여 Git remote를 나타내는 저장소에 새 이슈를 생성합니다.

**어떤 경우에도 REMOTE URL과 일치하지 않는 저장소에 이슈를 생성하지 마세요**
