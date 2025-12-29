---
id: to-task-template-development
title: ToTask 템플릿 개발 with AnnotationToTask
sidebar_position: 4
---

# ToTask 템플릿 개발 with AnnotationToTask

이 가이드는 `AnnotationToTask` 템플릿을 사용하여 커스텀 pre-annotation 플러그인을 만들고자 하는 플러그인 개발자를 위한 것입니다. AnnotationToTask 템플릿은 Synapse 프로젝트에서 데이터를 작업 주석으로 변환하는 간단한 인터페이스를 제공합니다.

## 개요

`AnnotationToTask` 템플릿(`synapse_sdk.plugins.categories.pre_annotation.templates.plugin.to_task`)은 pre-annotation 플러그인을 구축하는 구조화된 접근 방식을 제공합니다. 워크플로우 통합을 처리하는 동안 커스텀 데이터 변환 로직 구현에 집중할 수 있습니다.

### AnnotationToTask란?

`AnnotationToTask`는 두 가지 핵심 변환 메서드를 정의하는 템플릿 클래스입니다:
- **`convert_data_from_file()`**: 파일의 JSON 데이터를 작업 주석으로 변환
- **`convert_data_from_inference()`**: 모델 추론 결과를 작업 주석으로 변환

ToTaskAction 프레임워크는 주석 워크플로우 중에 이러한 메서드를 자동으로 호출하여 데이터가 작업 객체로 변환되는 방식을 사용자 정의할 수 있습니다.

### 이 템플릿을 사용해야 하는 경우

다음이 필요한 경우 AnnotationToTask 템플릿을 사용하세요:
- 외부 주석 데이터를 Synapse 작업 형식으로 변환
- 모델 예측을 작업 주석으로 변환
- 커스텀 데이터 검증 및 변환 로직 구현
- 재사용 가능한 주석 변환 플러그인 생성

## 시작하기

### 템플릿 구조

ToTask 템플릿을 사용하여 pre-annotation 플러그인을 생성하면 다음과 같은 구조를 얻습니다:

```
synapse-{plugin-code}-plugin/
├── config.yaml              # 플러그인 메타데이터 및 구성
├── plugin/                  # 소스 코드 디렉토리
│   ├── __init__.py
│   └── to_task.py          # AnnotationToTask 구현
├── requirements.txt         # Python 의존성
├── pyproject.toml          # 패키지 구성
└── README.md               # 플러그인 문서
```

### 기본 플러그인 구현

```python
# plugin/to_task.py
class AnnotationToTask:
    """커스텀 주석 변환 로직을 위한 템플릿."""

    def __init__(self, run, *args, **kwargs):
        """플러그인 작업 pre annotation 액션 클래스 초기화.

        Args:
            run: 로깅 및 컨텍스트를 제공하는 플러그인 run 객체.
        """
        self.run = run

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """파일의 데이터를 작업 객체로 변환.

        Args:
            primary_file_url: 주 파일(예: 주석이 추가되는 이미지)의 URL
            primary_file_original_name: 주 파일의 원본 이름
            data_file_url: 주석 데이터 파일(JSON)의 URL
            data_file_original_name: 주석 파일의 원본 이름

        Returns:
            dict: Synapse 형식의 주석이 있는 작업 객체
        """
        # 여기에 커스텀 구현
        converted_data = {}
        return converted_data

    def convert_data_from_inference(self, data: dict) -> dict:
        """추론 결과의 데이터를 작업 객체로 변환.

        Args:
            data: 전처리기의 원시 추론 결과

        Returns:
            dict: Synapse 형식의 주석이 있는 작업 객체
        """
        # 여기에 커스텀 구현
        return data
```

## AnnotationToTask 클래스 레퍼런스

### 생성자

```python
def __init__(self, run, *args, **kwargs):
```

**파라미터:**
- `run`: 로깅 및 컨텍스트 접근을 제공하는 플러그인 run 객체
  - 로깅에 `self.run.log_message(msg)` 사용
  - `self.run.params`를 통한 구성 접근

**사용법:**
```python
def __init__(self, run, *args, **kwargs):
    self.run = run
    # 커스텀 속성 초기화
    self.confidence_threshold = 0.8
    self.custom_mapping = {}
```

### 메서드: convert_data_from_file()

JSON 파일의 주석 데이터를 Synapse 작업 객체 형식으로 변환합니다.

```python
def convert_data_from_file(
    self,
    primary_file_url: str,
    primary_file_original_name: str,
    data_file_url: str,
    data_file_original_name: str,
) -> dict:
```

**파라미터:**
- `primary_file_url` (str): 주 파일(예: 주석이 추가되는 이미지)의 HTTP/HTTPS URL
- `primary_file_original_name` (str): 주 파일의 원본 파일명
- `data_file_url` (str): 주석 JSON 파일의 HTTP/HTTPS URL
- `data_file_original_name` (str): 주석 파일의 원본 파일명

**반환값:**
- `dict`: Synapse 형식의 주석을 포함하는 작업 객체

**호출자:**
- 파일 기반 주석 워크플로우 중 `FileAnnotationStrategy`

**워크플로우:**
1. `data_file_url`에서 JSON 데이터 다운로드
2. JSON 구조 파싱 및 검증
3. Synapse 작업 객체 스키마에 맞게 데이터 변환
4. 형식화된 작업 객체 반환

**예제 구현:**

```python
import requests
import json

def convert_data_from_file(
    self,
    primary_file_url: str,
    primary_file_original_name: str,
    data_file_url: str,
    data_file_original_name: str,
) -> dict:
    """COCO 형식 주석을 Synapse 작업 형식으로 변환."""

    # 주석 파일 다운로드
    response = requests.get(data_file_url, timeout=30)
    response.raise_for_status()
    coco_data = response.json()

    # 주석 추출
    annotations = coco_data.get('annotations', [])

    # Synapse 형식으로 변환
    task_objects = []
    for idx, ann in enumerate(annotations):
        task_object = {
            'id': f'obj_{idx}',
            'class_id': ann['category_id'],
            'type': 'bbox',
            'coordinates': {
                'x': ann['bbox'][0],
                'y': ann['bbox'][1],
                'width': ann['bbox'][2],
                'height': ann['bbox'][3]
            },
            'properties': {
                'area': ann.get('area', 0),
                'iscrowd': ann.get('iscrowd', 0)
            }
        }
        task_objects.append(task_object)

    # 변환 정보 로깅
    self.run.log_message(
        f'Converted {len(task_objects)} COCO annotations from {data_file_original_name}'
    )

    return {'objects': task_objects}
```

### 메서드: convert_data_from_inference()

모델 추론 결과를 Synapse 작업 객체 형식으로 변환합니다.

```python
def convert_data_from_inference(self, data: dict) -> dict:
```

**파라미터:**
- `data` (dict): 전처리기 플러그인의 원시 추론 결과

**반환값:**
- `dict`: Synapse 형식의 주석을 포함하는 작업 객체

**호출자:**
- 추론 기반 주석 워크플로우 중 `InferenceAnnotationStrategy`

**워크플로우:**
1. 전처리기로부터 추론 결과 수신
2. 예측, 경계 상자, 클래스 등 추출
3. Synapse 작업 객체 스키마로 변환
4. 필터링 또는 후처리 적용
5. 형식화된 작업 객체 반환

**예제 구현:**

```python
def convert_data_from_inference(self, data: dict) -> dict:
    """YOLOv8 탐지 결과를 Synapse 작업 형식으로 변환."""

    # 추론 결과에서 탐지 추출
    detections = data.get('detections', [])

    # 신뢰도 임계값으로 필터링
    confidence_threshold = 0.5
    task_objects = []

    for idx, det in enumerate(detections):
        confidence = det.get('confidence', 0)

        # 낮은 신뢰도 탐지 건너뛰기
        if confidence < confidence_threshold:
            continue

        # Synapse 형식으로 변환
        task_object = {
            'id': f'det_{idx}',
            'class_id': det['class_id'],
            'type': 'bbox',
            'coordinates': {
                'x': det['bbox']['x'],
                'y': det['bbox']['y'],
                'width': det['bbox']['width'],
                'height': det['bbox']['height']
            },
            'properties': {
                'confidence': confidence,
                'class_name': det.get('class_name', 'unknown')
            }
        }
        task_objects.append(task_object)

    # 변환 정보 로깅
    self.run.log_message(
        f'Converted {len(task_objects)} detections '
        f'(filtered from {len(detections)} total)'
    )

    return {'objects': task_objects}
```

## SDK 데이터 컨버터 사용하기

Synapse SDK는 일반적인 주석 형식(COCO, YOLO, Pascal VOC)을 처리하는 내장 데이터 컨버터를 제공합니다. 커스텀 파싱 로직을 작성하는 대신 템플릿에서 이러한 컨버터를 활용하여 더 빠른 개발과 더 나은 안정성을 얻을 수 있습니다.

### SDK 컨버터를 사용하는 이유?

- **검증 및 테스트 완료**: 컨버터는 SDK 팀이 유지관리하고 테스트합니다
- **표준 형식**: COCO, YOLO, Pascal VOC를 기본적으로 지원
- **코드 감소**: 형식 파서 재구현 방지
- **일관성**: 모든 플러그인에서 동일한 변환 로직
- **오류 처리**: 내장된 검증 및 오류 메시지

### 사용 가능한 컨버터

| 컨버터 | 형식 | 방향 | 모듈 경로 | 사용 사례 |
|--------|------|------|-----------|----------|
| `COCOToDMConverter` | COCO JSON | External → DM | `synapse_sdk.utils.converters.coco` | COCO 형식 주석 |
| `YOLOToDMConverter` | YOLO .txt | External → DM | `synapse_sdk.utils.converters.yolo` | YOLO 형식 레이블 |
| `PascalToDMConverter` | Pascal VOC XML | External → DM | `synapse_sdk.utils.converters.pascal` | Pascal VOC 주석 |
| `DMV2ToV1Converter` | DM v2 | DM v2 → DM v1 | `synapse_sdk.utils.converters.dm` | 버전 변환 |
| `DMV1ToV2Converter` | DM v1 | DM v1 → DM v2 | `synapse_sdk.utils.converters.dm` | 버전 변환 |

**DM 형식**: Synapse의 내부 Data Manager 형식(작업 객체가 사용하는 형식)

### 템플릿에서 컨버터 사용하기

모든 To-DM 컨버터는 템플릿 사용을 위해 특별히 설계된 `convert_single_file()` 메서드를 제공합니다.

#### convert_data_from_file()에서

```python
import requests
from synapse_sdk.utils.converters.coco import COCOToDMConverter

class AnnotationToTask:
    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """SDK 컨버터를 사용하여 COCO 주석 변환."""

        # 주석 파일 다운로드
        response = requests.get(data_file_url, timeout=30)
        response.raise_for_status()
        coco_data = response.json()

        # 단일 파일 모드로 컨버터 생성
        converter = COCOToDMConverter(is_single_conversion=True)

        # 이미지 경로로 모의 파일 객체 생성
        class FileObj:
            def __init__(self, name):
                self.name = name

        # SDK 컨버터를 사용하여 변환
        result = converter.convert_single_file(
            data=coco_data,
            original_file=FileObj(primary_file_url),
            original_image_name=primary_file_original_name
        )

        # DM 형식 데이터 반환
        return result['dm_json']
```

#### convert_data_from_inference()에서

```python
from synapse_sdk.utils.converters.dm import DMV2ToV1Converter

class AnnotationToTask:
    def convert_data_from_inference(self, data: dict) -> dict:
        """선택적 DM 버전 변환을 사용한 추론 결과 변환."""

        # 추론 결과 처리
        dm_v2_data = self._process_inference_results(data)

        # 필요시 DM v2를 v1로 변환
        if self._needs_v1_format():
            converter = DMV2ToV1Converter(new_dm_data=dm_v2_data)
            dm_v1_data = converter.convert()
            return dm_v1_data

        return dm_v2_data
```

### 컨버터 예제

#### 예제 1: COCO 컨버터

`COCOToDMConverter`를 사용한 완전한 구현:

```python
# plugin/to_task.py
import requests
from synapse_sdk.utils.converters.coco import COCOToDMConverter

class AnnotationToTask:
    """주석 변환을 위한 SDK COCO 컨버터 사용."""

    def __init__(self, run, *args, **kwargs):
        self.run = run

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """SDK 컨버터를 사용하여 COCO JSON을 Synapse 작업 형식으로 변환."""

        try:
            # COCO 주석 파일 다운로드
            self.run.log_message(f'Downloading COCO annotations: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            coco_data = response.json()

            # COCO 구조 검증
            if 'annotations' not in coco_data or 'images' not in coco_data:
                raise ValueError('Invalid COCO format: missing required fields')

            # 단일 파일 변환을 위한 컨버터 생성
            converter = COCOToDMConverter(is_single_conversion=True)

            # 파일 객체 생성
            class MockFile:
                def __init__(self, path):
                    self.name = path

            # SDK 컨버터를 사용하여 변환
            result = converter.convert_single_file(
                data=coco_data,
                original_file=MockFile(primary_file_url),
                original_image_name=primary_file_original_name
            )

            self.run.log_message(
                f'Successfully converted COCO data using SDK converter'
            )

            # DM 형식 반환
            return result['dm_json']

        except requests.RequestException as e:
            self.run.log_message(f'Failed to download annotations: {str(e)}')
            raise
        except ValueError as e:
            self.run.log_message(f'Invalid COCO data: {str(e)}')
            raise
        except Exception as e:
            self.run.log_message(f'Conversion failed: {str(e)}')
            raise

    def convert_data_from_inference(self, data: dict) -> dict:
        """이 플러그인에서는 사용하지 않음."""
        return data
```

**지원되는 COCO 기능:**
- 경계 상자 (Bounding boxes)
- 키포인트 (Keypoints)
- 그룹 (bbox + keypoints)
- 카테고리 매핑
- 속성 (Attributes)

#### 예제 2: YOLO 컨버터

`YOLOToDMConverter`를 사용한 완전한 구현:

```python
# plugin/to_task.py
import requests
from synapse_sdk.utils.converters.yolo import YOLOToDMConverter

class AnnotationToTask:
    """레이블 변환을 위한 SDK YOLO 컨버터 사용."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        # YOLO 클래스 이름 (모델과 일치해야 함)
        self.class_names = ['person', 'car', 'truck', 'bicycle']

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """SDK 컨버터를 사용하여 YOLO 레이블을 Synapse 작업 형식으로 변환."""

        try:
            # YOLO 레이블 파일 다운로드
            self.run.log_message(f'Downloading YOLO labels: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            label_text = response.text

            # 레이블 라인 파싱
            label_lines = [line.strip() for line in label_text.splitlines() if line.strip()]

            # 클래스 이름으로 컨버터 생성
            converter = YOLOToDMConverter(
                is_single_conversion=True,
                class_names=self.class_names
            )

            # 파일 객체 생성
            class MockFile:
                def __init__(self, path):
                    self.name = path

            # SDK 컨버터를 사용하여 변환
            result = converter.convert_single_file(
                data=label_lines,  # 레이블 문자열 리스트
                original_file=MockFile(primary_file_url)
            )

            self.run.log_message(
                f'Successfully converted {len(label_lines)} YOLO labels'
            )

            return result['dm_json']

        except Exception as e:
            self.run.log_message(f'YOLO conversion failed: {str(e)}')
            raise

    def convert_data_from_inference(self, data: dict) -> dict:
        """이 플러그인에서는 사용하지 않음."""
        return data
```

**지원되는 YOLO 기능:**
- 경계 상자 (표준 YOLO 형식)
- 폴리곤 (세그멘테이션 형식)
- 키포인트 (포즈 추정 형식)
- 자동 좌표 비정규화
- 클래스 이름 매핑

#### 예제 3: Pascal VOC 컨버터

`PascalToDMConverter`를 사용한 완전한 구현:

```python
# plugin/to_task.py
import requests
from synapse_sdk.utils.converters.pascal import PascalToDMConverter

class AnnotationToTask:
    """XML 주석 변환을 위한 SDK Pascal VOC 컨버터 사용."""

    def __init__(self, run, *args, **kwargs):
        self.run = run

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> dict:
        """SDK 컨버터를 사용하여 Pascal VOC XML을 Synapse 작업 형식으로 변환."""

        try:
            # Pascal VOC XML 파일 다운로드
            self.run.log_message(f'Downloading Pascal VOC XML: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            xml_content = response.text

            # 컨버터 생성
            converter = PascalToDMConverter(is_single_conversion=True)

            # 파일 객체 생성
            class MockFile:
                def __init__(self, path):
                    self.name = path

            # SDK 컨버터를 사용하여 변환
            result = converter.convert_single_file(
                data=xml_content,  # XML 문자열
                original_file=MockFile(primary_file_url)
            )

            self.run.log_message('Successfully converted Pascal VOC annotations')

            return result['dm_json']

        except Exception as e:
            self.run.log_message(f'Pascal VOC conversion failed: {str(e)}')
            raise

    def convert_data_from_inference(self, data: dict) -> dict:
        """이 플러그인에서는 사용하지 않음."""
        return data
```

**지원되는 Pascal VOC 기능:**
- 경계 상자 (xmin, ymin, xmax, ymax)
- 객체 이름/클래스
- 자동 너비/높이 계산
- XML 파싱 및 검증

### 컨버터 모범 사례

#### 1. 컨버터 사용 시기

**SDK 컨버터 사용:**
- 표준 형식(COCO, YOLO, Pascal VOC) 작업 시
- 신뢰할 수 있고 테스트된 변환 로직 필요 시
- 유지보수 부담 최소화 원할 때
- 복잡한 형식(키포인트가 있는 COCO, YOLO 세그멘테이션) 작업 시

**커스텀 코드 작성:**
- 형식이 비표준이거나 독점적인 경우
- 변환 전 특별한 전처리 필요 시
- 컨버터가 특정 변형을 지원하지 않는 경우
- 성능 최적화가 중요한 경우

#### 2. 컨버터 오류 처리

항상 try-except 블록으로 컨버터 호출을 감싸세요:

```python
def convert_data_from_file(self, *args) -> dict:
    try:
        converter = COCOToDMConverter(is_single_conversion=True)
        result = converter.convert_single_file(...)
        return result['dm_json']

    except ValueError as e:
        # 컨버터의 검증 오류
        self.run.log_message(f'Invalid data format: {str(e)}')
        raise

    except KeyError as e:
        # 필수 필드 누락
        self.run.log_message(f'Missing field in result: {str(e)}')
        raise

    except Exception as e:
        # 예상치 못한 오류
        self.run.log_message(f'Converter error: {str(e)}')
        raise
```

#### 3. 컨버터와 커스텀 로직 결합

컨버터 출력을 후처리할 수 있습니다:

```python
def convert_data_from_file(self, *args) -> dict:
    # 기본 변환에 컨버터 사용
    converter = YOLOToDMConverter(
        is_single_conversion=True,
        class_names=self.class_names
    )
    result = converter.convert_single_file(...)
    dm_data = result['dm_json']

    # 커스텀 후처리 추가
    for img in dm_data.get('images', []):
        for bbox in img.get('bounding_box', []):
            # 커스텀 속성 추가
            bbox['attrs'].append({
                'name': 'source',
                'value': 'yolo_model_v2'
            })

            # 크기로 필터링
            if bbox['data'][2] < 10 or bbox['data'][3] < 10:
                # 작은 박스 표시
                bbox['attrs'].append({
                    'name': 'too_small',
                    'value': True
                })

    return dm_data
```

#### 4. 성능 고려사항

**컨버터는 최적화되어 있지만:**
- 파일을 효율적으로 다운로드 (타임아웃, 큰 파일인 경우 스트리밍 사용)
- 여러 파일 처리 시 컨버터 인스턴스 캐싱
- 모니터링을 위한 변환 진행 로깅

```python
def __init__(self, run, *args, **kwargs):
    self.run = run
    # 컨버터 인스턴스 캐시
    self.coco_converter = COCOToDMConverter(is_single_conversion=True)

def convert_data_from_file(self, *args) -> dict:
    # 캐시된 컨버터 재사용
    result = self.coco_converter.convert_single_file(...)
    return result['dm_json']
```

#### 5. 컨버터 테스트

컨버터 통합과 엣지 케이스 모두 테스트:

```python
# test_to_task.py
import pytest
from plugin.to_task import AnnotationToTask

class MockRun:
    def log_message(self, msg):
        print(msg)

def test_coco_converter_integration():
    """COCO 컨버터 통합 테스트."""
    converter = AnnotationToTask(MockRun())

    # 유효한 COCO 데이터로 테스트
    coco_data = {
        'images': [{'id': 1, 'file_name': 'test.jpg'}],
        'annotations': [{
            'id': 1,
            'image_id': 1,
            'category_id': 1,
            'bbox': [10, 20, 100, 200]
        }],
        'categories': [{'id': 1, 'name': 'person'}]
    }

    result = converter._convert_with_coco_converter(coco_data, 'test.jpg')

    # DM 구조 검증
    assert 'images' in result
    assert len(result['images']) == 1
    assert 'bounding_box' in result['images'][0]

def test_invalid_format_handling():
    """잘못된 데이터에 대한 오류 처리 테스트."""
    converter = AnnotationToTask(MockRun())

    # 잘못된 COCO 데이터로 테스트
    invalid_data = {'invalid': 'data'}

    with pytest.raises(ValueError):
        converter._convert_with_coco_converter(invalid_data, 'test.jpg')
```

### 컨버터 API 레퍼런스

#### COCOToDMConverter.convert_single_file()

```python
def convert_single_file(
    data: Dict[str, Any],
    original_file: IO,
    original_image_name: str
) -> Dict[str, Any]:
```

**파라미터:**
- `data`: COCO 형식 딕셔너리 (JSON 내용)
- `original_file`: `.name` 속성이 있는 파일 객체
- `original_image_name`: 이미지 파일 이름

**반환값:**
```python
{
    'dm_json': {...},        # DM 형식 데이터
    'image_path': str,       # 파일 객체의 경로
    'image_name': str        # 이미지의 베이스네임
}
```

#### YOLOToDMConverter.convert_single_file()

```python
def convert_single_file(
    data: List[str],
    original_file: IO
) -> Dict[str, Any]:
```

**파라미터:**
- `data`: YOLO 레이블 라인 리스트 (.txt 파일의 문자열)
- `original_file`: `.name` 속성이 있는 파일 객체

**반환값:**
```python
{
    'dm_json': {...},        # DM 형식 데이터
    'image_path': str,       # 파일 객체의 경로
    'image_name': str        # 이미지의 베이스네임
}
```

#### PascalToDMConverter.convert_single_file()

```python
def convert_single_file(
    data: str,
    original_file: IO
) -> Dict[str, Any]:
```

**파라미터:**
- `data`: Pascal VOC XML 내용 (문자열)
- `original_file`: `.name` 속성이 있는 파일 객체

**반환값:**
```python
{
    'dm_json': {...},        # DM 형식 데이터
    'image_path': str,       # 파일 객체의 경로
    'image_name': str        # 이미지의 베이스네임
}
```

## 완전한 예제

### 예제 1: COCO 형식 주석 플러그인

COCO 형식 주석을 Synapse 작업으로 변환하는 완전한 플러그인입니다.

```python
# plugin/to_task.py
import requests
import json
from typing import Dict, List

class AnnotationToTask:
    """COCO 형식 주석을 Synapse 작업 객체로 변환."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        # COCO 카테고리 ID를 Synapse 클래스 ID로 매핑
        self.category_mapping = {
            1: 1,   # person
            2: 2,   # bicycle
            3: 3,   # car
            # 필요에 따라 더 많은 매핑 추가
        }

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> Dict:
        """COCO JSON 파일을 Synapse 작업 형식으로 변환."""

        try:
            # COCO 주석 파일 다운로드
            self.run.log_message(f'Downloading: {data_file_url}')
            response = requests.get(data_file_url, timeout=30)
            response.raise_for_status()
            coco_data = response.json()

            # COCO 구조 검증
            if 'annotations' not in coco_data:
                raise ValueError('Invalid COCO format: missing annotations')

            # 주석 변환
            task_objects = self._convert_coco_annotations(
                coco_data['annotations']
            )

            self.run.log_message(
                f'Successfully converted {len(task_objects)} annotations'
            )

            return {
                'objects': task_objects,
                'metadata': {
                    'source': 'coco',
                    'file': data_file_original_name
                }
            }

        except requests.RequestException as e:
            self.run.log_message(f'Failed to download file: {str(e)}')
            raise
        except json.JSONDecodeError as e:
            self.run.log_message(f'Invalid JSON format: {str(e)}')
            raise
        except Exception as e:
            self.run.log_message(f'Conversion failed: {str(e)}')
            raise

    def _convert_coco_annotations(self, annotations: List[Dict]) -> List[Dict]:
        """COCO 주석을 Synapse 작업 객체로 변환."""
        task_objects = []

        for idx, ann in enumerate(annotations):
            # COCO 카테고리를 Synapse 클래스로 매핑
            coco_category = ann.get('category_id')
            synapse_class = self.category_mapping.get(coco_category)

            if not synapse_class:
                self.run.log_message(
                    f'Warning: Unmapped category {coco_category}, skipping'
                )
                continue

            # bbox 형식 변환: [x, y, width, height]
            bbox = ann.get('bbox', [])
            if len(bbox) != 4:
                continue

            task_object = {
                'id': f'coco_{ann.get("id", idx)}',
                'class_id': synapse_class,
                'type': 'bbox',
                'coordinates': {
                    'x': float(bbox[0]),
                    'y': float(bbox[1]),
                    'width': float(bbox[2]),
                    'height': float(bbox[3])
                },
                'properties': {
                    'area': ann.get('area', 0),
                    'iscrowd': ann.get('iscrowd', 0),
                    'original_category': coco_category
                }
            }
            task_objects.append(task_object)

        return task_objects

    def convert_data_from_inference(self, data: Dict) -> Dict:
        """이 플러그인에서는 사용하지 않음 - 파일 기반만."""
        return data
```

### 예제 2: 객체 탐지 추론 플러그인

객체 탐지 모델 출력을 변환하는 완전한 플러그인입니다.

```python
# plugin/to_task.py
from typing import Dict, List

class AnnotationToTask:
    """객체 탐지 추론 결과를 Synapse 작업으로 변환."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        # 구성
        self.confidence_threshold = 0.7
        self.nms_threshold = 0.5
        self.max_detections = 100

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> Dict:
        """이 플러그인에서는 사용하지 않음 - 추론 기반만."""
        return {}

    def convert_data_from_inference(self, data: Dict) -> Dict:
        """YOLOv8 탐지 결과를 Synapse 형식으로 변환."""

        try:
            # 예측 추출
            predictions = data.get('predictions', [])

            if not predictions:
                self.run.log_message('No predictions found in inference results')
                return {'objects': []}

            # 탐지 필터링 및 변환
            task_objects = self._process_detections(predictions)

            # 필요시 NMS 적용
            if len(task_objects) > self.max_detections:
                task_objects = self._apply_nms(task_objects)

            self.run.log_message(
                f'Converted {len(task_objects)} detections '
                f'(threshold: {self.confidence_threshold})'
            )

            return {
                'objects': task_objects,
                'metadata': {
                    'model': data.get('model_name', 'unknown'),
                    'inference_time': data.get('inference_time_ms', 0),
                    'confidence_threshold': self.confidence_threshold
                }
            }

        except Exception as e:
            self.run.log_message(f'Inference conversion failed: {str(e)}')
            raise

    def _process_detections(self, predictions: List[Dict]) -> List[Dict]:
        """탐지 처리 및 필터링."""
        task_objects = []

        for idx, pred in enumerate(predictions):
            confidence = pred.get('confidence', 0.0)

            # 신뢰도로 필터링
            if confidence < self.confidence_threshold:
                continue

            # bbox 좌표 추출
            bbox = pred.get('bbox', {})

            task_object = {
                'id': f'det_{idx}',
                'class_id': pred.get('class_id', 0),
                'type': 'bbox',
                'coordinates': {
                    'x': float(bbox.get('x', 0)),
                    'y': float(bbox.get('y', 0)),
                    'width': float(bbox.get('width', 0)),
                    'height': float(bbox.get('height', 0))
                },
                'properties': {
                    'confidence': float(confidence),
                    'class_name': pred.get('class_name', 'unknown'),
                    'model_version': pred.get('model_version', '1.0')
                }
            }
            task_objects.append(task_object)

        return task_objects

    def _apply_nms(self, detections: List[Dict]) -> List[Dict]:
        """겹치는 박스를 줄이기 위해 Non-Maximum Suppression 적용."""
        # 신뢰도로 정렬
        sorted_dets = sorted(
            detections,
            key=lambda x: x['properties']['confidence'],
            reverse=True
        )

        # 상위 N개 탐지 반환
        return sorted_dets[:self.max_detections]
```

### 예제 3: 하이브리드 플러그인 (파일 + 추론)

두 가지 주석 방법을 모두 지원하는 플러그인입니다.

```python
# plugin/to_task.py
import requests
import json
from typing import Dict

class AnnotationToTask:
    """파일 및 추론 주석을 모두 지원하는 하이브리드 플러그인."""

    def __init__(self, run, *args, **kwargs):
        self.run = run
        self.default_confidence = 0.8

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_original_name: str,
        data_file_url: str,
        data_file_original_name: str,
    ) -> Dict:
        """커스텀 JSON 주석 형식 처리."""

        # 주석 파일 다운로드
        response = requests.get(data_file_url, timeout=30)
        response.raise_for_status()
        annotation_data = response.json()

        # 커스텀 형식에서 변환
        task_objects = []
        for obj in annotation_data.get('objects', []):
            task_object = {
                'id': obj['id'],
                'class_id': obj['class'],
                'type': obj.get('type', 'bbox'),
                'coordinates': obj['coords'],
                'properties': obj.get('props', {})
            }
            task_objects.append(task_object)

        return {'objects': task_objects}

    def convert_data_from_inference(self, data: Dict) -> Dict:
        """검증이 포함된 추론 결과 처리."""

        # 예측 추출 및 검증
        predictions = data.get('predictions', [])

        task_objects = []
        for idx, pred in enumerate(predictions):
            # 필수 필드 검증
            if not self._validate_prediction(pred):
                continue

            task_object = {
                'id': f'pred_{idx}',
                'class_id': pred['class_id'],
                'type': 'bbox',
                'coordinates': pred['bbox'],
                'properties': {
                    'confidence': pred.get('confidence', self.default_confidence),
                    'source': 'inference'
                }
            }
            task_objects.append(task_object)

        return {'objects': task_objects}

    def _validate_prediction(self, pred: Dict) -> bool:
        """예측에 필수 필드가 있는지 검증."""
        required_fields = ['class_id', 'bbox']
        return all(field in pred for field in required_fields)
```

## 모범 사례

### 1. 데이터 검증

변환 전에 항상 입력 데이터를 검증하세요:

```python
def convert_data_from_file(self, *args) -> dict:
    # JSON 구조 검증
    if 'required_field' not in data:
        raise ValueError('Missing required field in annotation data')

    # 데이터 타입 검증
    if not isinstance(data['objects'], list):
        raise TypeError('Objects must be a list')

    # 값 검증
    for obj in data['objects']:
        if obj.get('confidence', 0) < 0 or obj.get('confidence', 1) > 1:
            raise ValueError('Confidence must be between 0 and 1')
```

### 2. 오류 처리

포괄적인 오류 처리를 구현하세요:

```python
def convert_data_from_file(self, *args) -> dict:
    try:
        # 변환 로직
        return converted_data

    except requests.RequestException as e:
        self.run.log_message(f'Network error: {str(e)}')
        raise

    except json.JSONDecodeError as e:
        self.run.log_message(f'Invalid JSON: {str(e)}')
        raise

    except KeyError as e:
        self.run.log_message(f'Missing field: {str(e)}')
        raise

    except Exception as e:
        self.run.log_message(f'Unexpected error: {str(e)}')
        raise
```

### 3. 로깅

로깅을 사용하여 변환 진행 상황을 추적하세요:

```python
def convert_data_from_inference(self, data: dict) -> dict:
    # 시작 로그
    self.run.log_message('Starting inference data conversion')

    predictions = data.get('predictions', [])
    self.run.log_message(f'Processing {len(predictions)} predictions')

    # 데이터 처리
    filtered = [p for p in predictions if p['confidence'] > 0.5]
    self.run.log_message(f'Filtered to {len(filtered)} high-confidence predictions')

    # 완료 로그
    self.run.log_message('Conversion completed successfully')

    return converted_data
```

### 4. 구성

플러그인을 구성 가능하게 만드세요:

```python
class AnnotationToTask:
    def __init__(self, run, *args, **kwargs):
        self.run = run

        # 플러그인 params에서 구성 가져오기
        params = getattr(run, 'params', {})
        pre_processor_params = params.get('pre_processor_params', {})

        # 구성 설정
        self.confidence_threshold = pre_processor_params.get('confidence_threshold', 0.7)
        self.nms_threshold = pre_processor_params.get('nms_threshold', 0.5)
        self.max_detections = pre_processor_params.get('max_detections', 100)
```

### 5. 테스트

변환을 철저히 테스트하세요:

```python
# test_to_task.py
import pytest
from plugin.to_task import AnnotationToTask

class MockRun:
    def log_message(self, msg):
        print(msg)

def test_convert_coco_format():
    """COCO 형식 변환 테스트."""
    converter = AnnotationToTask(MockRun())

    # 모의 COCO 데이터
    coco_data = {
        'annotations': [
            {
                'id': 1,
                'category_id': 1,
                'bbox': [10, 20, 100, 200],
                'area': 20000
            }
        ]
    }

    result = converter._convert_coco_annotations(coco_data['annotations'])

    assert len(result) == 1
    assert result[0]['class_id'] == 1
    assert result[0]['coordinates']['x'] == 10

def test_confidence_filtering():
    """신뢰도 임계값 필터링 테스트."""
    converter = AnnotationToTask(MockRun())
    converter.confidence_threshold = 0.7

    predictions = [
        {'confidence': 0.9, 'class_id': 1, 'bbox': {}},
        {'confidence': 0.5, 'class_id': 2, 'bbox': {}},  # 임계값 미만
        {'confidence': 0.8, 'class_id': 3, 'bbox': {}},
    ]

    result = converter._process_detections(predictions)

    # 2개만 임계값 통과해야 함
    assert len(result) == 2
```

## ToTaskAction과의 통합

### 템플릿 메서드가 호출되는 방법

템플릿 메서드는 워크플로우 실행 중 ToTaskAction 프레임워크에 의해 호출됩니다:

**파일 기반 주석 흐름:**
```
1. ToTaskAction.start()
   ↓
2. ToTaskOrchestrator.execute_workflow()
   ↓
3. FileAnnotationStrategy.process_task()
   ↓
4. annotation_to_task = context.entrypoint(logger)
   ↓
5. converted_data = annotation_to_task.convert_data_from_file(...)
   ↓
6. client.annotate_task_data(task_id, data=converted_data)
```

**추론 기반 주석 흐름:**
```
1. ToTaskAction.start()
   ↓
2. ToTaskOrchestrator.execute_workflow()
   ↓
3. InferenceAnnotationStrategy.process_task()
   ↓
4. inference_result = preprocessor_api.predict(...)
   ↓
5. annotation_to_task = context.entrypoint(logger)
   ↓
6. converted_data = annotation_to_task.convert_data_from_inference(inference_result)
   ↓
7. client.annotate_task_data(task_id, data=converted_data)
```

### 템플릿 디버깅

템플릿을 디버깅할 때:

1. **로그 확인**: 로그 메시지에 대한 플러그인 실행 로그 검토
2. **반환 검증**: 반환 형식이 Synapse 작업 객체 스키마와 일치하는지 확인
3. **로컬 테스트**: 배포 전 변환 메서드를 독립적으로 테스트
4. **입력 검사**: 수신 중인 데이터를 확인하기 위해 입력 파라미터 로깅
5. **오류 처리**: 설명적인 메시지와 함께 예외 catch 및 로깅

```python
def convert_data_from_file(self, *args) -> dict:
    # 디버그 로깅
    self.run.log_message(f'Received URLs: primary={args[0]}, data={args[2]}')

    try:
        # 로직
        result = process_data()

        # 결과 검증
        self.run.log_message(f'Converted {len(result["objects"])} objects')

        return result

    except Exception as e:
        # 상세한 오류 로깅
        self.run.log_message(f'Conversion failed: {type(e).__name__}: {str(e)}')
        import traceback
        self.run.log_message(traceback.format_exc())
        raise
```

## 일반적인 함정

### 1. 잘못된 반환 형식

**잘못됨:**
```python
def convert_data_from_file(self, *args) -> dict:
    return [obj1, obj2, obj3]  # 리스트 반환, dict 아님
```

**올바름:**
```python
def convert_data_from_file(self, *args) -> dict:
    return {'objects': [obj1, obj2, obj3]}  # 'objects' 키가 있는 dict 반환
```

### 2. 오류 처리 누락

**잘못됨:**
```python
def convert_data_from_file(self, *args) -> dict:
    response = requests.get(url)  # 타임아웃 없음, 오류 처리 없음
    data = response.json()
    return data
```

**올바름:**
```python
def convert_data_from_file(self, *args) -> dict:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return self._transform_data(data)
    except Exception as e:
        self.run.log_message(f'Error: {str(e)}')
        raise
```

### 3. 로깅 사용 안 함

**잘못됨:**
```python
def convert_data_from_inference(self, data: dict) -> dict:
    # 조용한 변환 - 가시성 없음
    return process(data)
```

**올바름:**
```python
def convert_data_from_inference(self, data: dict) -> dict:
    self.run.log_message(f'Converting {len(data["predictions"])} predictions')
    result = process(data)
    self.run.log_message(f'Conversion complete: {len(result["objects"])} objects')
    return result
```

## 관련 문서

- [ToTask 개요](./to-task-overview.md) - ToTask 액션 사용자 가이드
- [ToTask 액션 개발](./to-task-action-development.md) - SDK 개발자 가이드
- [Pre-annotation 플러그인 개요](./pre-annotation-plugin-overview.md) - 카테고리 개요
- 플러그인 개발 가이드 - 일반 플러그인 개발

## 템플릿 소스 코드

- Template: `synapse_sdk/plugins/categories/pre_annotation/templates/plugin/to_task.py`
- Called by: `synapse_sdk/plugins/categories/pre_annotation/actions/to_task/strategies/annotation.py`
