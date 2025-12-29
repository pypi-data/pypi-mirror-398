---
id: upload-plugin-template
title: 업로드 플러그인 템플릿 개발
sidebar_position: 3
---

# BaseUploader를 사용한 업로드 플러그인 템플릿 개발

이 가이드는 BaseUploader 템플릿을 사용하여 사용자 정의 업로드 플러그인을 만들려는 플러그인 개발자를 위한 것입니다. BaseUploader는 업로드 플러그인 내에서 파일 처리 및 구성을 위한 워크플로우 기반의 기초를 제공합니다.

## 개요

BaseUploader 템플릿 (`synapse_sdk.plugins.categories.upload.templates.plugin`)은 업로드 플러그인 구축을 위한 구조화된 접근 방식을 제공합니다. 메서드 재정의를 통해 사용자 정의를 허용하면서 일반적인 업로드 워크플로우를 처리합니다.

### BaseUploader 워크플로우

BaseUploader는 6단계 워크플로우 파이프라인을 구현합니다:

```
1. setup_directories()    # 사용자 정의 디렉토리 구조 생성
2. organize_files()       # 파일 구성 및 구조화
3. before_process()       # 전처리 후크
4. process_files()        # 주요 처리 로직 (필수)
5. after_process()        # 후처리 후크
6. validate_files()       # 최종 검증
```

## 시작하기

### 템플릿 구조

업로드 플러그인을 생성하면 다음과 같은 구조를 갖게 됩니다:

```
synapse-{plugin-code}-plugin/
├── config.yaml              # 플러그인 메타데이터 및 구성
├── plugin/                  # 소스 코드 디렉토리
│   ├── __init__.py
│   └── upload.py           # BaseUploader를 사용한 주요 업로드 구현
├── requirements.txt         # 파이썬 의존성
├── pyproject.toml          # 패키지 구성
└── README.md               # 플러그인 문서
```

### 기본 플러그인 구현

```python
# plugin/__init__.py
from pathlib import Path
from typing import Any, Dict, List

class BaseUploader:
    """일반적인 업로드 기능을 가진 기본 클래스."""

    def __init__(self, run, path: Path, file_specification: List = None,
                 organized_files: List = None, extra_params: Dict = None):
        self.run = run
        self.path = path
        self.file_specification = file_specification or []
        self.organized_files = organized_files or []
        self.extra_params = extra_params or {}

    # 재정의 가능한 핵심 워크플로우 메서드
    def setup_directories(self) -> None:
        """사용자 정의 디렉토리 설정 - 필요에 따라 재정의."""
        pass

    def organize_files(self, files: List) -> List:
        """파일 구성 - 사용자 정의 로직을 위해 재정의."""
        return files

    def before_process(self, organized_files: List) -> List:
        """전처리 후크 - 필요에 따라 재정의."""
        return organized_files

    def process_files(self, organized_files: List) -> List:
        """주요 처리 - 반드시 재정의해야 함."""
        return organized_files

    def after_process(self, processed_files: List) -> List:
        """후처리 후크 - 필요에 따라 재정의."""
        return processed_files

    def validate_files(self, files: List) -> List:
        """검증 - 사용자 정의 검증을 위해 재정의."""
        return self._filter_valid_files(files)

    def handle_upload_files(self) -> List:
        """주요 진입점 - 워크플로우를 실행합니다."""
        self.setup_directories()
        current_files = self.organized_files
        current_files = self.organize_files(current_files)
        current_files = self.before_process(current_files)
        current_files = self.process_files(current_files)
        current_files = self.after_process(current_files)
        current_files = self.validate_files(current_files)
        return current_files

# plugin/upload.py
from . import BaseUploader

class Uploader(BaseUploader):
    """사용자 정의 업로드 플러그인 구현."""

    def process_files(self, organized_files: List) -> List:
        """필수: 파일 처리 로직을 구현하십시오."""
        # 여기에 사용자 정의 처리 로직
        return organized_files
```

## 핵심 메서드 참조

### 필수 메서드

#### `process_files(organized_files: List) -> List`

**목적**: 모든 플러그인에서 구현해야 하는 주요 처리 메서드.

**사용 시기**: 항상 - 플러그인의 핵심 로직이 여기에 들어갑니다.

**예시**:

```python
def process_files(self, organized_files: List) -> List:
    """TIFF 이미지를 JPEG 형식으로 변환합니다."""
    processed_files = []

    for file_group in organized_files:
        files_dict = file_group.get('files', {})
        converted_files = {}

        for spec_name, file_path in files_dict.items():
            if file_path.suffix.lower() in ['.tif', '.tiff']:
                # TIFF를 JPEG로 변환
                jpeg_path = self.convert_tiff_to_jpeg(file_path)
                converted_files[spec_name] = jpeg_path
                self.run.log_message(f"{file_path}를 {jpeg_path}로 변환했습니다.")
            else:
                converted_files[spec_name] = file_path

        file_group['files'] = converted_files
        processed_files.append(file_group)

    return processed_files
```

### 선택적 후크 메서드

#### `setup_directories() -> None`

**목적**: 처리가 시작되기 전에 사용자 정의 디렉토리 구조를 생성합니다.

**사용 시기**: 플러그인이 처리, 임시 파일 또는 출력을 위해 특정 디렉토리가 필요할 때.

**예시**:

```python
def setup_directories(self):
    """처리 디렉토리를 생성합니다."""
    (self.path / 'temp').mkdir(exist_ok=True)
    (self.path / 'processed').mkdir(exist_ok=True)
    (self.path / 'thumbnails').mkdir(exist_ok=True)
    self.run.log_message("처리 디렉토리를 생성했습니다.")
```

#### `organize_files(files: List) -> List`

**목적**: 주요 처리 전에 파일을 재구성하고 구조화합니다.

**사용 시기**: 파일을 다르게 그룹화하거나, 기준으로 필터링하거나, 데이터를 재구성해야 할 때.

**예시**:

```python
def organize_files(self, files: List) -> List:
    """최적화된 처리를 위해 크기별로 파일을 그룹화합니다."""
    large_files = []
    small_files = []

    for file_group in files:
        total_size = sum(f.stat().st_size for f in file_group.get('files', {}).values())
        if total_size > 100 * 1024 * 1024:  # 100MB
            large_files.append(file_group)
        else:
            small_files.append(file_group)

    # 큰 파일 먼저 처리
    return large_files + small_files
```

#### `before_process(organized_files: List) -> List`

**목적**: 주요 처리 전 설정 작업을 위한 전처리 후크.

**사용 시기**: 검증, 준비 또는 초기화 작업에 사용합니다.

**예시**:

```python
def before_process(self, organized_files: List) -> List:
    """처리를 위해 파일을 검증하고 준비합니다."""
    self.run.log_message(f"{len(organized_files)}개 파일 그룹의 처리를 시작합니다.")

    # 사용 가능한 디스크 공간 확인
    if not self.check_disk_space(organized_files):
        raise Exception("처리에 필요한 디스크 공간이 부족합니다.")

    return organized_files
```

#### `after_process(processed_files: List) -> List`

**목적**: 정리 및 최종화를 위한 후처리 후크.

**사용 시기**: 정리, 최종 변환 또는 리소스 할당 해제에 사용합니다.

**예시**:

```python
def after_process(self, processed_files: List) -> List:
    """임시 파일을 정리하고 요약을 생성합니다."""
    # 임시 파일 제거
    temp_dir = self.path / 'temp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    # 처리 요약 생성
    summary = {
        'total_processed': len(processed_files),
        'processing_time': time.time() - self.start_time
    }

    self.run.log_message(f"처리가 완료되었습니다: {summary}")
    return processed_files
```

#### `validate_files(files: List) -> List`

**목적**: 유형 검사를 넘어서는 사용자 정의 검증 로직.

**사용 시기**: 내장 파일 유형 검증 외에 추가적인 검증 규칙이 필요할 때.

**예시**:

```python
def validate_files(self, files: List) -> List:
    """크기 및 형식 검사를 포함한 사용자 정의 검증."""
    # 먼저 내장 검증 적용
    validated_files = super().validate_files(files)

    # 그런 다음 사용자 정의 검증 적용
    final_files = []
    for file_group in validated_files:
        if self.validate_file_group(file_group):
            final_files.append(file_group)
        else:
            self.run.log_message(f"파일 그룹이 검증에 실패했습니다: {file_group}")

    return final_files
```

#### `filter_files(organized_file: Dict[str, Any]) -> bool`

**목적**: 사용자 정의 기준에 따라 개별 파일을 필터링합니다.

**사용 시기**: 처리에서 특정 파일을 제외해야 할 때.

**예시**:

```python
def filter_files(self, organized_file: Dict[str, Any]) -> bool:
    """작은 파일을 필터링합니다."""
    files_dict = organized_file.get('files', {})
    total_size = sum(f.stat().st_size for f in files_dict.values())

    if total_size < 1024:  # 1KB보다 작은 파일 건너뛰기
        self.run.log_message(f"작은 파일 그룹 건너뛰기: {total_size} 바이트")
        return False

    return True
```

## 파일 확장자 필터링

BaseUploader에는 파일 타입에 따라 자동으로 파일을 필터링하는 내장 확장자 필터링 시스템이 포함되어 있습니다. 이 기능은 워크플로우에 통합되어 있으며 검증 단계에서 자동으로 실행됩니다.

### 작동 방식

1. **자동 통합**: 확장자 필터링은 업로드 워크플로우의 `ValidateFilesStep`에서 자동으로 적용됩니다
2. **대소문자 무시**: 확장자는 대소문자를 구분하지 않고 매칭됩니다 (`.mp4`는 `.MP4`, `.Mp4` 등과 매칭)
3. **타입별 필터링**: 파일 타입(video, image, audio 등)별로 필터링이 수행됩니다
4. **자동 로깅**: 필터링된 파일은 WARNING 레벨로 로깅되며 어떤 확장자가 필터링되었는지 표시됩니다

### 기본 백엔드 구성

시스템은 백엔드 파일 타입 제한과 일치하는 합리적인 기본값을 제공합니다:

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """허용되는 파일 확장자 구성을 반환합니다.

    파일 타입별로 확장자를 제한하려면 이 메서드를 재정의하세요.
    확장자는 대소문자를 구분하지 않으며 점(.) 접두사를 포함해야 합니다.
    """
    return {
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'],
        'image': ['.jpg', '.jpeg', '.png'],
        'pcd': ['.pcd'],
        'text': ['.txt', '.html'],
        'audio': ['.mp3', '.wav'],
        'data': ['.xml', '.bin', '.json', '.fbx'],
    }
```

### 확장자 필터링 커스터마이징

플러그인의 확장자를 제한하려면 플러그인 템플릿 파일(`plugin/__init__.py`)에서 `get_file_extensions_config()` 메서드를 수정하기만 하면 됩니다:

#### 예제 1: MP4 비디오만 허용

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """MP4 비디오만 허용합니다."""
    return {
        'video': ['.mp4'],  # MP4만 허용
        'image': ['.jpg', '.jpeg', '.png'],
        'pcd': ['.pcd'],
        'text': ['.txt', '.html'],
        'audio': ['.mp3', '.wav'],
        'data': ['.xml', '.bin', '.json', '.fbx'],
    }
```

**결과**: 업로드 시 `.avi`, `.mkv`, `.mov` 등의 확장자를 가진 파일은 자동으로 필터링되고 로그에 기록됩니다:

```
WARNING: Filtered 3 video files with unavailable extensions: .avi, .mkv, .mov (allowed: .mp4)
```

#### 예제 2: 추가 형식 지원

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """추가 비디오 및 이미지 형식을 지원합니다."""
    return {
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'],
        'image': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'],  # 형식 추가
        'pcd': ['.pcd'],
        'text': ['.txt', '.html', '.md', '.csv'],  # .md 및 .csv 추가
        'audio': ['.mp3', '.wav', '.flac', '.aac'],  # .flac 및 .aac 추가
        'data': ['.xml', '.bin', '.json', '.fbx', '.yaml'],  # .yaml 추가
    }
```

#### 예제 3: 완전 커스텀 구성

```python
def get_file_extensions_config(self) -> Dict[str, List[str]]:
    """특정 프로젝트 요구사항에 맞는 커스텀 구성."""
    return {
        'video': ['.mp4'],  # 엄격한 비디오 형식
        'image': ['.jpg'],  # 엄격한 이미지 형식
        'cad': ['.dwg', '.dxf', '.step'],  # 커스텀 CAD 타입
        'document': ['.pdf', '.docx'],  # 커스텀 문서 타입
    }
```

### 확장자 필터링 워크플로우

```
OrganizeFilesStep
  ↓
ValidateFilesStep
  ├─ Uploader.handle_upload_files()
  │   └─ validate_files()
  │       └─ validate_file_types()  ← 확장자 필터링이 여기서 발생
  │           ├─ get_file_extensions_config() 읽기
  │           ├─ 타입별로 파일 필터링
  │           └─ 필터링된 확장자 로깅
  └─ Strategy 검증
```

## 실제 예제

### 예제 1: 이미지 처리 플러그인

```python
from pathlib import Path
from typing import List
from plugin import BaseUploader

class ImageProcessingUploader(BaseUploader):
    """TIFF 이미지를 JPEG로 변환하고 썸네일을 생성합니다."""

    def setup_directories(self):
        """처리된 이미지를 위한 디렉토리를 생성합니다."""
        (self.path / 'processed').mkdir(exist_ok=True)
        (self.path / 'thumbnails').mkdir(exist_ok=True)

    def process_files(self, organized_files: List) -> List:
        """이미지를 변환하고 썸네일을 생성합니다."""
        processed_files = []

        for file_group in organized_files:
            files_dict = file_group.get('files', {})
            converted_files = {}

            for spec_name, file_path in files_dict.items():
                if file_path.suffix.lower() in ['.tif', '.tiff']:
                    # JPEG로 변환
                    jpeg_path = self.convert_to_jpeg(file_path)
                    converted_files[spec_name] = jpeg_path

                    # 썸네일 생성
                    thumbnail_path = self.generate_thumbnail(jpeg_path)
                    converted_files[f"{spec_name}_thumbnail"] = thumbnail_path

                    self.run.log_message(f"{file_path.name}을(를) 처리했습니다.")
                else:
                    converted_files[spec_name] = file_path

            file_group['files'] = converted_files
            processed_files.append(file_group)

        return processed_files

    def convert_to_jpeg(self, tiff_path: Path) -> Path:
        """PIL을 사용하여 TIFF를 JPEG로 변환합니다."""
        from PIL import Image

        output_path = self.path / 'processed' / f"{tiff_path.stem}.jpg"

        with Image.open(tiff_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=95)

        return output_path

    def generate_thumbnail(self, image_path: Path) -> Path:
        """썸네일을 생성합니다."""
        from PIL import Image

        thumbnail_path = self.path / 'thumbnails' / f"{image_path.stem}_thumb.jpg"

        with Image.open(image_path) as img:
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85)

        return thumbnail_path
```

### 예제 2: 데이터 검증 플러그인

```python
class DataValidationUploader(BaseUploader):
    """데이터 파일을 검증하고 품질 보고서를 생성합니다."""

    def __init__(self, run, path, file_specification=None,
                 organized_files=None, extra_params=None):
        super().__init__(run, path, file_specification, organized_files, extra_params)

        # extra_params에서 초기화
        self.validation_config = extra_params.get('validation_config', {})
        self.strict_mode = extra_params.get('strict_validation', False)

    def before_process(self, organized_files: List) -> List:
        """검증 엔진을 초기화합니다."""
        self.validation_results = []
        self.run.log_message(f"{len(organized_files)}개 파일 그룹의 검증을 시작합니다.")
        return organized_files

    def process_files(self, organized_files: List) -> List:
        """파일을 검증하고 품질 보고서를 생성합니다."""
        processed_files = []

        for file_group in organized_files:
            validation_result = self.validate_file_group(file_group)

            # 검증 메타데이터 추가
            file_group['validation'] = validation_result
            file_group['quality_score'] = validation_result['score']

            # 검증 결과에 따라 파일 그룹 포함
            if self.should_include_file_group(validation_result):
                processed_files.append(file_group)
                self.run.log_message(f"파일 그룹 통과: 점수 {validation_result['score']}")
            else:
                self.run.log_message(f"파일 그룹 실패: {validation_result['errors']}")

        return processed_files

    def validate_file_group(self, file_group: Dict) -> Dict:
        """파일 그룹의 포괄적인 검증."""
        files_dict = file_group.get('files', {})
        errors = []
        score = 100

        for spec_name, file_path in files_dict.items():
            # 파일 존재 여부
            if not file_path.exists():
                errors.append(f"파일을 찾을 수 없음: {file_path}")
                score -= 50
                continue

            # 파일 크기 검증
            file_size = file_path.stat().st_size
            if file_size == 0:
                errors.append(f"빈 파일: {file_path}")
                score -= 40
            elif file_size > 1024 * 1024 * 1024:  # 1GB
                score -= 10

        return {
            'score': max(0, score),
            'errors': errors,
            'validated_at': datetime.now().isoformat()
        }

    def should_include_file_group(self, validation_result: Dict) -> bool:
        """파일 그룹을 포함해야 하는지 결정합니다."""
        if validation_result['errors'] and self.strict_mode:
            return False

        min_score = self.validation_config.get('min_score', 50)
        return validation_result['score'] >= min_score
```

### 예제 3: 배치 처리 플러그인

```python
class BatchProcessingUploader(BaseUploader):
    """구성 가능한 배치로 파일을 처리합니다."""

    def __init__(self, run, path, file_specification=None,
                 organized_files=None, extra_params=None):
        super().__init__(run, path, file_specification, organized_files, extra_params)

        self.batch_size = extra_params.get('batch_size', 10)
        self.parallel_processing = extra_params.get('use_parallel', True)
        self.max_workers = extra_params.get('max_workers', 4)

    def organize_files(self, files: List) -> List:
        """파일을 처리 배치로 구성합니다."""
        batches = []
        current_batch = []

        for file_group in files:
            current_batch.append(file_group)

            if len(current_batch) >= self.batch_size:
                batches.append({
                    'batch_id': len(batches) + 1,
                    'files': current_batch,
                    'batch_size': len(current_batch)
                })
                current_batch = []

        # 남은 파일 추가
        if current_batch:
            batches.append({
                'batch_id': len(batches) + 1,
                'files': current_batch,
                'batch_size': len(current_batch)
            })

        self.run.log_message(f"{len(batches)}개의 배치로 구성되었습니다.")
        return batches

    def process_files(self, organized_files: List) -> List:
        """배치로 파일을 처리합니다."""
        all_processed_files = []

        if self.parallel_processing:
            all_processed_files = self.process_batches_parallel(organized_files)
        else:
            all_processed_files = self.process_batches_sequential(organized_files)

        return all_processed_files

    def process_batches_sequential(self, batches: List) -> List:
        """배치를 순차적으로 처리합니다."""
        all_files = []

        for i, batch in enumerate(batches, 1):
            self.run.log_message(f"{i}/{len(batches)} 배치 처리 중")
            processed_batch = self.process_single_batch(batch)
            all_files.extend(processed_batch)

        return all_files

    def process_batches_parallel(self, batches: List) -> List:
        """ThreadPoolExecutor를 사용하여 배치를 병렬로 처리합니다."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_files = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self.process_single_batch, batch): batch
                for batch in batches
            }

            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    processed_files = future.result()
                    all_files.extend(processed_files)
                    self.run.log_message(f"배치 {batch['batch_id']} 완료")
                except Exception as e:
                    self.run.log_message(f"배치 {batch['batch_id']} 실패: {e}")

        return all_files

    def process_single_batch(self, batch: Dict) -> List:
        """단일 파일 배치를 처리합니다."""
        batch_files = batch['files']
        processed_files = []

        for file_group in batch_files:
            # 배치 메타데이터 추가
            file_group['batch_processed'] = True
            file_group['batch_id'] = batch['batch_id']
            processed_files.append(file_group)

        return processed_files
```

## 모범 사례

### 1. 코드 구성

- `process_files()`를 핵심 로직에 집중
- 설정, 정리 및 검증을 위해 후크 메서드 사용
- 헬퍼 메서드를 사용하여 관심사 분리

### 2. 오류 처리

- 포괄적인 오류 처리 구현
- 컨텍스트 정보와 함께 오류 기록
- 가능하면 정상적으로 실패

### 3. 성능

- 처리 로직 프로파일링
- 적절한 데이터 구조 사용
- 큰 파일에 대한 메모리 사용량 고려
- I/O 집약적인 작업에 대한 비동기 처리 구현

### 4. 테스트

- 모든 메서드에 대한 단위 테스트 작성
- 실제 파일을 사용한 통합 테스트 포함
- 오류 조건 및 엣지 케이스 테스트

### 5. 로깅

- 중요한 작업 및 마일스톤 기록
- 타이밍 정보 포함
- 분석을 위한 구조화된 로깅 사용

### 6. 구성

- 플러그인 구성에 `extra_params` 사용
- 합리적인 기본값 제공
- 구성 매개변수 검증

## 업로드 액션과의 통합

BaseUploader 플러그인은 업로드 액션 워크플로우와 통합됩니다:

1. **파일 검색**: 업로드 액션이 파일을 검색하고 구성합니다.
2. **플러그인 호출**: 구성된 파일과 함께 `handle_upload_files()`가 호출됩니다.
3. **워크플로우 실행**: BaseUploader가 6단계 워크플로우를 실행합니다.
4. **결과 반환**: 처리된 파일이 업로드 액션으로 반환됩니다.
5. **업로드 및 데이터 단위 생성**: 업로드 액션이 업로드를 완료합니다.

### 데이터 흐름

```
업로드 액션 (OrganizeFilesStep)
    ↓ organized_files
BaseUploader.handle_upload_files()
    ↓ setup_directories()
    ↓ organize_files()
    ↓ before_process()
    ↓ process_files()      ← 사용자 정의 로직
    ↓ after_process()
    ↓ validate_files()
    ↓ processed_files
업로드 액션 (UploadFilesStep, GenerateDataUnitsStep)
```

## 구성

### 플러그인 구성 (config.yaml)

```yaml
code: "my-upload-plugin"
name: "내 업로드 플러그인"
version: "1.0.0"
category: "upload"

package_manager: "pip"

actions:
  upload:
    entrypoint: "plugin.upload.Uploader"
    method: "job"
```

### 의존성 (requirements.txt)

```txt
synapse-sdk>=1.0.0
pillow>=10.0.0  # 이미지 처리용
pandas>=2.0.0   # 데이터 처리용
```

## 플러그인 테스트

### 단위 테스트

```python
import pytest
from unittest.mock import Mock
from pathlib import Path
from plugin.upload import Uploader

class TestUploader:

    def setup_method(self):
        self.mock_run = Mock()
        self.test_path = Path('/tmp/test')
        self.file_spec = [{'name': 'image_1', 'file_type': 'image'}]

    def test_process_files(self):
        """파일 처리 테스트."""
        uploader = Uploader(
            run=self.mock_run,
            path=self.test_path,
            file_specification=self.file_spec,
            organized_files=[{'files': {}}]
        )

        result = uploader.process_files([{'files': {}}])
        assert isinstance(result, list)
```

### 통합 테스트

```bash
# 샘플 데이터로 테스트
synapse plugin run upload '{
  "name": "테스트 업로드",
  "use_single_path": true,
  "path": "/test/data",
  "storage": 1,
  "data_collection": 5
}' --plugin my-upload-plugin --debug
```

## 참조

- [업로드 플러그인 개요](./upload-plugin-overview.md) - 사용자 가이드 및 구성 참조
- [업로드 액션 개발](./upload-plugin-action.md) - 액션 아키텍처 및 내부에 대한 SDK 개발자 가이드
