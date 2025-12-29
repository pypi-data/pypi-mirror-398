---
id: features
title: 기능
sidebar_position: 5
---

# 기능

이 섹션에서는 Synapse SDK에서 제공하는 주요 기능과 기능성을 다룹니다.

## [플러그인 시스템](../plugins/plugins.md)

ML 워크플로우 구축 및 관리를 위한 포괄적인 플러그인 프레임워크입니다.

- **[플러그인 카테고리](../plugins/plugins.md#플러그인-카테고리)** - 신경망, 내보내기, 업로드, 스마트 도구 및 검증 플러그인
- **[실행 방법](../plugins/plugins.md)** - Job, Task 및 REST API 실행 모드
- **[개발 가이드](../plugins/plugins.md)** - 커스텀 플러그인 생성, 테스트 및 배포

## [파이프라인 패턴](./pipelines/index.md)

복잡한 다단계 작업을 위한 강력한 워크플로우 오케스트레이션 패턴입니다.

- **[스텝 오케스트레이션](./pipelines/step-orchestration.md)** - 진행 상황 추적 및 롤백이 포함된 순차적 스텝 기반 워크플로우
- **유틸리티 스텝** - 내장된 로깅, 타이밍, 검증 스텝 래퍼
- **액션 통합** - Train, Export, Upload 액션과의 원활한 통합

## [데이터 변환기](./converters/index.md)

컴퓨터 비전 데이터셋을 위한 포괄적인 데이터 형식 변환 유틸리티입니다.

- **[형식 변환기](./converters/index.md)** - DM, COCO, Pascal VOC 및 YOLO 형식 간 변환
- **[버전 마이그레이션](./converters/index.md)** - 버전 간 DM 데이터셋 마이그레이션