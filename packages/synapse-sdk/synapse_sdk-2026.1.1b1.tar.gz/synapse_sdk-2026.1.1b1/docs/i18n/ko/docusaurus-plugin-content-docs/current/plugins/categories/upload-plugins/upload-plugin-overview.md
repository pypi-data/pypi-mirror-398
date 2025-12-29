---
id: upload-plugin-overview
title: 업로드 플러그인 개요
sidebar_position: 1
---

# 업로드 플러그인 개요

업로드 플러그인은 메타데이터 지원, 보안 검증, 체계적인 데이터 단위 생성을 통해 Synapse 플랫폼으로 파일을 처리하는 포괄적인 파일 업로드 및 데이터 수집 작업을 제공합니다.

## 빠른 개요

**카테고리:** 업로드
**사용 가능한 작업:** `upload`
**실행 방법:** 작업 기반 실행

## 주요 특징

- **다중 경로 모드 지원**: 각 자산에 대한 개별 경로 설정으로 다른 위치에서 파일 업로드
- **Excel 메타데이터 통합**: Excel 파일에서 자동 메타데이터 주석 달기
- **유연한 파일 구성**: 다양한 사용 사례를 위한 단일 경로 또는 다중 경로 모드
- **배치 처리**: 대규모 업로드를 위한 최적화된 배치 처리
- **진행 상황 추적**: 워크플로우 단계 전반에 걸친 실시간 진행 상황 업데이트
- **보안 검증**: 포괄적인 파일 및 Excel 보안 검사

## 사용 사례

- 메타데이터 주석이 포함된 대량 파일 업로드
- Excel 기반 메타데이터 매핑 및 검증
- 재귀적 디렉토리 처리
- 유형 기반 파일 구성
- 배치 데이터 단위 생성
- 다중 소스 데이터셋 업로드 (다른 위치의 센서, 카메라, 주석)
- 크기 및 내용 검증을 통한 보안 파일 처리

## 지원되는 업로드 소스

- 로컬 파일 시스템 경로 (파일 및 디렉토리)
- 재귀적 디렉토리 스캔
- 향상된 파일 주석을 위한 Excel 메타데이터 파일
- 자동 구성 기능이 있는 혼합 파일 유형
- 자산별 경로 구성이 있는 분산 데이터 소스

## 구성 모드

### 모드 1: 단일 경로 모드 (기본값 - `use_single_path: true`)

모든 자산이 하나의 기본 디렉토리를 공유합니다. 시스템은 각 파일 사양에 대한 하위 디렉토리를 예상합니다.

```json
{
  "name": "표준 업로드",
  "use_single_path": true,
  "path": "/data/experiment",
  "is_recursive": true,
  "storage": 1,
  "data_collection": 5
}
```

**예상 디렉토리 구조:**

```
/data/experiment/
├── pcd_1/           # 포인트 클라우드
│   └── *.pcd
├── image_1/         # 이미지
│   └── *.jpg
└── json_meta_1/     # 메타데이터
    └── *.json
```

### 모드 2: 다중 경로 모드 (`use_single_path: false`)

각 자산에는 자체 경로 및 재귀 설정이 있습니다. 분산 데이터 소스에 적합합니다.

```json
{
  "name": "다중 소스 업로드",
  "use_single_path": false,
  "assets": {
    "pcd_1": {
      "path": "/sensors/lidar/scan_001",
      "is_recursive": false
    },
    "image_1": {
      "path": "/sensors/camera/front",
      "is_recursive": true
    },
    "json_meta_1": {
      "path": "/metadata/annotations",
      "is_recursive": false
    }
  },
  "storage": 1,
  "data_collection": 5
}
```

**선택적 파일 사양:**

다중 경로 모드에서는 데이터 컬렉션의 파일 사양 템플릿에서 파일 사양을 선택적으로 표시할 수 있습니다:

- **필수 사양** (`is_required: true`): `assets` 매개변수에 자산 경로가 반드시 있어야 합니다
- **선택적 사양** (`is_required: false`): `assets`에서 생략 가능 - 시스템이 건너뜁니다

선택적 사양이 생략된 예제:

```json
{
  "name": "다중 소스 업로드",
  "use_single_path": false,
  "assets": {
    "pcd_1": {"path": "/sensors/lidar", "is_recursive": false},
    "image_1": {"path": "/cameras/front", "is_recursive": true}
    // "json_meta_1"은 선택사항이며 생략됨
  },
  "storage": 1,
  "data_collection": 5
}
```

시스템 로그: `"Skipping optional spec json_meta_1: no asset path configured"`

## 기본 사용법

### CLI 사용법

```bash
# 단일 경로 모드 (전통적)
synapse plugin run upload '{
  "name": "데이터셋 업로드",
  "use_single_path": true,
  "path": "/data/training",
  "is_recursive": true,
  "storage": 1,
  "data_collection": 5
}'

# 다중 경로 모드 (고급)
synapse plugin run upload '{
  "name": "다중 센서 업로드",
  "use_single_path": false,
  "assets": {
    "lidar": {"path": "/sensors/lidar", "is_recursive": true},
    "camera": {"path": "/sensors/camera", "is_recursive": false}
  },
  "storage": 1,
  "data_collection": 5
}'
```

### Python API 사용법

```python
from synapse_sdk.plugins.categories.upload.actions.upload.action import UploadAction

# 업로드 매개변수 구성
params = {
    "name": "데이터셋 업로드",
    "use_single_path": true,
    "path": "/data/training_images",
    "is_recursive": True,
    "storage": 1,
    "data_collection": 5,
    "max_file_size_mb": 100
}

action = UploadAction(params=params, plugin_config=plugin_config)
result = action.start()

print(f"업로드된 파일 수: {result['uploaded_files_count']}")
print(f"생성된 데이터 단위 수: {result['generated_data_units_count']}")
```

## 구성 매개변수

### 필수 매개변수

| 매개변수          | 유형  | 설명               | 예시          |
| ----------------- | ----- | ------------------ | ------------- |
| `name`            | `str` | 업로드 이름        | `"내 업로드"` |
| `storage`         | `int` | 스토리지 ID        | `1`           |
| `data_collection` | `int` | 데이터 컬렉션 ID   | `5`           |

### 모드별 필수 매개변수

**단일 경로 모드** (`use_single_path: true`):

- `path` (str): 기본 디렉토리 경로

**다중 경로 모드** (`use_single_path: false`):

- `assets` (dict): 자산별 `path` 및 `is_recursive` 설정이 포함된 자산별 구성

### 선택적 매개변수

| 매개변수                        | 유형          | 기본값  | 설명                              |
| ------------------------------- | ------------- | ------- | --------------------------------- |
| `description`                   | `str \| None` | `None`  | 업로드 설명                       |
| `project`                       | `int \| None` | `None`  | 프로젝트 ID                       |
| `use_single_path`               | `bool`        | `true`  | 모드 전환                         |
| `is_recursive`                  | `bool`        | `true`  | 재귀적 스캔 (단일 경로 모드)      |
| `excel_metadata_path`           | `str \| None` | `None`  | Excel 메타데이터 파일 경로 |
| `max_file_size_mb`              | `int`         | `50`    | 최대 파일 크기 (MB)               |
| `creating_data_unit_batch_size` | `int`         | `100`   | 데이터 단위 생성을 위한 배치 크기 |

## Excel 메타데이터 지원

업로드 플러그인은 유연한 헤더 지원과 포괄적인 파일 이름 매칭 기능을 통해 고급 Excel 메타데이터 처리를 제공합니다.

### Excel 메타데이터 파일 지정

`excel_metadata_path` 매개변수를 사용하여 Excel 메타데이터 파일을 제공할 수 있습니다. 시스템은 다음과 같은 여러 경로 해석 전략을 지원합니다:

1. **절대 경로**: Excel 파일의 전체 파일 시스템 경로
2. **스토리지 상대 경로**: 스토리지 기본 디렉토리를 기준으로 한 경로
3. **작업 디렉토리 상대 경로**: 업로드 작업 디렉토리를 기준으로 한 경로 (단일 경로 모드만 해당)

**예시:**

```json
{
  "excel_metadata_path": "/data/metadata.xlsx"  // 절대 경로
}
```

```json
{
  "excel_metadata_path": "metadata.xlsx"  // 스토리지 기본 경로 기준
}
```

```json
{
  "excel_metadata_path": "metadata/dataset_info.xlsx"  // 스토리지 내 하위 디렉토리
}
```

### 경로 해석 순서

시스템은 다음 순서로 Excel 메타데이터 경로를 해석합니다:

1. **절대 경로**: 경로가 `/`로 시작하면 절대 파일 시스템 경로로 처리
2. **스토리지 상대 경로**: 스토리지의 기본 경로를 기준으로 경로 해석
3. **작업 디렉토리 상대 경로** (단일 경로 모드): 현재 작업 디렉토리를 기준으로 경로 해석

이러한 유연한 해석 방식을 통해 구성된 스토리지 위치에 데이터와 함께 메타데이터 파일을 저장할 수 있습니다.

### 기본 메타데이터 파일

`excel_metadata_path`를 지정하지 않으면 시스템이 작업 디렉토리에서 기본 메타데이터 파일을 자동으로 검색합니다 (단일 경로 모드만 해당):

- `meta.xlsx` (먼저 확인)
- `meta.xls` (대체)

**Python 예제:**

```python
# Excel 메타데이터에 대한 명시적 경로
upload_params = {
    "name": "메타데이터가 있는 업로드",
    "path": "/data/files",
    "storage": 1,
    "data_collection": 5,
    "excel_metadata_path": "metadata/dataset_info.xlsx"  // 스토리지 기준
}

# 기본 메타데이터 파일 사용 (작업 디렉토리의 meta.xlsx)
upload_params = {
    "name": "기본 메타데이터가 있는 업로드",
    "path": "/data/files",
    "storage": 1,
    "data_collection": 5
    // excel_metadata_path 미지정 - meta.xlsx가 있으면 사용
}
```

### Excel 형식

두 가지 헤더 형식이 모두 지원됩니다 (대소문자 구분 없음):

**옵션 1: "filename" 헤더**
| filename | category | description | custom_field |
|----------|----------|-------------|--------------|
| image1.jpg | nature | Mountain landscape | high_res |
| image2.png | urban | City skyline | processed |

**옵션 2: "filename" 헤더**
| file_name | category | description | custom_field |
|-----------|----------|-------------|--------------|
| image1.jpg | nature | Mountain landscape | high_res |
| image2.png | urban | City skyline | processed |

### 파일 이름 매칭

시스템은 5계층 우선순위 매칭 알고리즘을 사용합니다:

1. **정확한 스템 일치** (가장 높은 우선순위): `image1`이 `image1.jpg`와 일치
2. **정확한 파일 이름 일치**: `image1.jpg`가 `image1.jpg`와 일치
3. **메타데이터 키 스템 일치**: `path/image1.ext`의 스템이 `image1`과 일치
4. **부분 경로 일치**: `/uploads/image1.jpg`에 `image1`이 포함됨
5. **전체 경로 일치**: 복잡한 구조에 대한 전체 경로 일치

### 보안 검증

Excel 파일은 보안 검증을 거칩니다:

```python
# 기본 보안 제한
max_file_size_mb: 10      # 파일 크기 제한
max_rows: 100000          # 행 수 제한
max_columns: 50           # 열 수 제한
```

### 구성

`config.yaml`에서 Excel 보안을 구성합니다:

```yaml
actions:
  upload:
    excel_config:
      max_file_size_mb: 10
      max_rows: 100000
      max_columns: 50
```

## 진행 상황 추적

업로드 작업은 세 가지 주요 단계에 걸쳐 진행 상황을 추적합니다:

| 카테고리              | 비율 | 설명                                |
| --------------------- | ---- | ----------------------------------- |
| `analyze_collection`  | 2%   | 매개변수 검증 및 설정               |
| `upload_data_files`   | 38%  | 파일 업로드 처리                    |
| `generate_data_units` | 60%  | 데이터 단위 생성 및 최종화          |

## 일반적인 사용 사례

### 1. 간단한 데이터셋 업로드

```json
{
  "name": "학습 데이터셋",
  "use_single_path": true,
  "path": "/datasets/training",
  "is_recursive": true,
  "storage": 1,
  "data_collection": 2
}
```

### 2. 다중 소스 센서 데이터

```json
{
  "name": "다중 카메라 데이터셋",
  "use_single_path": false,
  "assets": {
    "front_camera": { "path": "/cameras/front", "is_recursive": true },
    "rear_camera": { "path": "/cameras/rear", "is_recursive": true },
    "lidar": { "path": "/sensors/lidar", "is_recursive": false }
  },
  "storage": 1,
  "data_collection": 2
}
```

### 3. 메타데이터가 포함된 데이터셋 (절대 경로)

```json
{
  "name": "주석이 달린 데이터셋",
  "use_single_path": true,
  "path": "/data/annotated",
  "is_recursive": true,
  "excel_metadata_path": "/data/metadata.xlsx",
  "storage": 1,
  "data_collection": 5
}
```

### 4. 메타데이터가 포함된 데이터셋 (스토리지 상대 경로)

```json
{
  "name": "스토리지 상대 메타데이터가 있는 업로드",
  "use_single_path": true,
  "path": "/data/uploads",
  "is_recursive": true,
  "excel_metadata_path": "metadata/dataset_info.xlsx",
  "storage": 1,
  "data_collection": 5
}
```

**Python 예제 - 다양한 경로 유형 사용:**

```python
# 예제 1: 절대 경로
params = {
    "name": "절대 경로 메타데이터가 있는 업로드",
    "path": "/data/uploads",
    "excel_metadata_path": "/data/metadata.xlsx",
    "storage": 1,
    "data_collection": 5
}

# 예제 2: 스토리지 상대 경로
params = {
    "name": "스토리지 상대 메타데이터가 있는 업로드",
    "path": "/data/uploads",
    "excel_metadata_path": "metadata/info.xlsx",  # 스토리지 기본 경로 기준
    "storage": 1,
    "data_collection": 5
}

# 예제 3: 기본 메타데이터 파일 사용
params = {
    "name": "기본 메타데이터가 있는 업로드",
    "path": "/data/uploads",
    # excel_metadata_path 미지정 - 작업 디렉토리의 meta.xlsx를 찾음
    "storage": 1,
    "data_collection": 5
}
```

## 이점

### 사용자용

- **유연성**: 단일 작업으로 여러 다른 위치에서 파일 업로드
- **세분화된 제어**: 전역이 아닌 자산별로 재귀 검색 설정
- **조직화**: 복잡한 파일 구조를 데이터 컬렉션 사양에 매핑
- **사용 사례 지원**: 다중 센서 데이터 수집, 분산 데이터셋, 이기종 소스

### 개발자용

- **하위 호환성**: 기존 코드가 변경 없이 계속 작동
- **타입 안전**: 명확한 오류 메시지가 포함된 전체 Pydantic 검증
- **유지보수성**: 단일 경로와 다중 경로 로직 간의 깔끔한 분리
- **확장성**: 향후 더 많은 자산별 구성 옵션을 쉽게 추가 가능

## 다음 단계

- **플러그인 개발자용**: 사용자 정의 업로드 플러그인을 파일 처리 로직과 함께 생성하려면 [BaseUploader 템플릿 가이드](./upload-plugin-template.md)를 참조하십시오.
- **SDK/액션 개발자용**: 아키텍처 세부 정보, 전략 패턴 및 액션 내부에 대해서는 [업로드 액션 개발](./upload-plugin-action.md)을 참조하십시오.

## 마이그레이션 가이드

### 레거시에서 현재 버전으로

업로드 작업은 100% 하위 호환성을 유지합니다. 기본 동작 (`use_single_path=true`)은 이전 버전과 동일하게 작동합니다.

#### 마이그레이션 필요 없음

기존 구성은 변경 없이 계속 작동합니다:

```python
# 이 레거시 사용법은 여전히 작동합니다
params = {
    "name": "내 업로드",
    "path": "/data/files",
    "storage": 1,
    "data_collection": 5
}
```

#### 다중 경로 모드 채택

새로운 다중 경로 기능을 사용하려면:

1. `use_single_path: false`로 설정
2. `path` 필드 제거 (무시됨)
3. 자산별 구성이 포함된 `assets` 사전을 추가

```python
# 새로운 다중 경로 모드
params = {
    "name": "다중 소스 업로드",
    "use_single_path": false,
    "assets": {
        "pcd_1": {"path": "/sensors/lidar", "is_recursive": false},
        "image_1": {"path": "/cameras/front", "is_recursive": true}
    },
    "storage": 1,
    "data_collection": 5
}
```

## 문제 해결

### 일반적인 문제

#### "파일을 찾을 수 없음" 오류

```bash
# 경로가 존재하고 읽을 수 있는지 확인
ls -la /path/to/data
test -r /path/to/data && echo "읽을 수 있음" || echo "읽을 수 없음"

# 파일이 존재하는지 확인
find /path/to/data -name "*.jpg" | head -10
```

#### Excel 처리 오류

```bash
# 파일 형식 및 크기 확인
file /path/to/metadata.xlsx
ls -lh /path/to/metadata.xlsx
```

#### 모드 검증 오류

- **단일 경로 모드**: `path`가 제공되었는지 확인
- **다중 경로 모드**: `assets`가 하나 이상의 자산 구성과 함께 제공되었는지 확인

## 모범 사례

### 디렉토리 구성

- 명확하고 설명적인 디렉토리 이름 사용
- 합리적인 디렉토리 크기 유지 (디렉토리당 10,000개 미만 파일)
- 안정성을 위해 절대 경로 사용

### 성능 최적화

- 필요할 때만 재귀 활성화
- 최상의 성능을 위해 Excel 파일을 5MB 미만으로 유지
- 균형 잡힌 디렉토리 구조로 파일 구성

### 보안 고려 사항

- 처리 전에 모든 경로 검증
- 소스 데이터에 읽기 전용 권한 사용
- 적절한 Excel 크기 제한 설정

## 지원 및 리소스

- **액션 개발 가이드**: [업로드 플러그인 액션 개발](./upload-plugin-action.md)
- **템플릿 개발 가이드**: [업로드 플러그인 템플릿 개발](./upload-plugin-template.md)
- **API 참조**: 자세한 API 참조는 액션 개발 설명서를 참조하십시오.
