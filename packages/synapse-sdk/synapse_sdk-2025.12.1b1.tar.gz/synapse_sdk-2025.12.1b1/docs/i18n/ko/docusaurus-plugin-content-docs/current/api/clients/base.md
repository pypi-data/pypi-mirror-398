---
id: base
title: BaseClient
sidebar_position: 3
---

# BaseClient

핵심 HTTP 작업 및 페이지네이션 기능을 제공하는 모든 Synapse SDK 클라이언트의 기본 클래스입니다.

## 개요

`BaseClient`는 다른 모든 클라이언트에서 사용하는 HTTP 작업, 오류 처리, 요청 관리 및 페이지네이션을 위한 공통 기능을 제공합니다. 자동 파일 URL 변환 기능과 함께 효율적인 페이지네이션 처리를 구현합니다.

## 기능

- 재시도 로직이 있는 HTTP 요청 처리
- 자동 timeout 관리
- 제너레이터를 사용한 효율적인 페이지네이션
- 파일 URL을 로컬 경로로 자동 변환
- Pydantic 모델 유효성 검사
- 연결 풀링

## 핵심 HTTP 메서드

BaseClient는 모든 클라이언트 믹스인에서 내부적으로 사용하는 저수준 HTTP 메서드를 제공합니다:

- `_get()` - 선택적 응답 모델 검증을 포함한 GET 요청
- `_post()` - 요청/응답 검증을 포함한 POST 요청
- `_put()` - 모델 검증을 포함한 PUT 요청
- `_patch()` - 모델 검증을 포함한 PATCH 요청
- `_delete()` - 모델 검증을 포함한 DELETE 요청

이러한 메서드는 일반적으로 직접 호출되지 않습니다. 대신 클라이언트 믹스인에서 제공하는 상위 수준 메서드를 사용하세요.

## 페이지네이션 메서드

### `_list(path, url_conversion=None, list_all=False, params=None, **kwargs)`

선택적 자동 페이지네이션 및 파일 URL 변환 기능을 갖춘 페이지네이션 API 엔드포인트에서 리소스를 나열합니다.

**매개변수:**

- `path` (str): 요청할 URL 경로
- `url_conversion` (dict, optional): 파일 URL을 로컬 경로로 변환하기 위한 설정
 - 구조: `{'files_fields': ['field1', 'field2'], 'is_list': True}`
 - 자동으로 파일을 다운로드하고 URL을 로컬 경로로 대체
- `list_all` (bool): True인 경우 제너레이터를 사용하여 모든 페이지의 모든 결과 반환
- `params` (dict, optional): 쿼리 매개변수 (필터, 정렬 등)
- `**kwargs`: 추가 요청 인자

**반환값:**

- `list_all=False`인 경우: `results`, `count`, `next`, `previous`를 포함한 딕셔너리
- `list_all=True`인 경우: `(generator, total_count)` 튜플

**예제:**

```python
# 첫 페이지만 가져오기
response = client._list('api/tasks/')
tasks = response['results'] # 첫 페이지의 작업들
total = response['count'] # 전체 작업 수

# 제너레이터를 사용하여 모든 결과 가져오기 (메모리 효율적)
generator, total_count = client._list('api/tasks/', list_all=True)
all_tasks = list(generator) # 자동으로 모든 페이지 가져오기

# 필터와 함께 사용
params = {'status': 'pending', 'priority': 'high'}
response = client._list('api/tasks/', params=params)

# 파일 필드에 url_conversion 사용
url_conversion = {'files_fields': ['files'], 'is_list': True}
generator, count = client._list(
 'api/data_units/',
 url_conversion=url_conversion,
 list_all=True,
 params={'status': 'active'}
)
# 'files' 필드의 파일 URL이 자동으로 다운로드되어 로컬 경로로 변환됨
for unit in generator:
 print(unit['files']) # URL이 아닌 로컬 파일 경로
```

### `_list_all(path, url_conversion=None, params=None, **kwargs)`

페이지네이션된 API 엔드포인트에서 모든 결과를 생성하는 제너레이터입니다.

이 메서드는 `list_all=True`일 때 `_list()`에 의해 내부적으로 호출됩니다. `next` URL을 따라가며 자동으로 페이지네이션을 처리하고, 깊은 페이지네이션에서 스택 오버플로우를 방지하기 위해 재귀 대신 반복적 접근 방식(while 루프)을 사용합니다.

**주요 개선사항 (SYN-5757):**

1. **page_size 중복 제거**: `page_size` 매개변수는 첫 번째 요청에만 추가됩니다. 후속 요청은 이미 모든 필요한 매개변수를 포함하는 `next` URL을 직접 사용합니다.

2. **적절한 params 처리**: 사용자가 지정한 쿼리 매개변수가 첫 번째 요청에 올바르게 전달되고 `next` URL을 통해 페이지네이션 전체에 보존됩니다.

3. **모든 페이지에 url_conversion 적용**: URL 변환이 첫 번째 페이지뿐만 아니라 모든 페이지에 적용됩니다.

4. **재귀 대신 반복**: 더 나은 메모리 효율성과 대용량 데이터셋에서 스택 오버플로우 방지를 위해 재귀 대신 while 루프를 사용합니다.

**매개변수:**

- `path` (str): 초기 URL 경로
- `url_conversion` (dict, optional): 모든 페이지에 적용
- `params` (dict, optional): 첫 번째 요청에만 사용되는 쿼리 매개변수
- `**kwargs`: 추가 요청 인자

**생성:**

모든 페이지의 개별 결과 항목을 지연 방식으로 가져옵니다.

**예제:**

```python
# 기본: 모든 작업 반복
for task in client._list_all('api/tasks/'):
 process_task(task)

# 필터와 함께
params = {'status': 'pending'}
for task in client._list_all('api/tasks/', params=params):
 print(task['id'])

# 중첩된 파일 필드에 url_conversion 사용
url_conversion = {'files_fields': ['data.files', 'metadata.attachments'], 'is_list': True}
for item in client._list_all('api/items/', url_conversion=url_conversion):
 print(item['data']['files']) # 로컬 경로

# 모든 결과 수집 (대용량 데이터셋의 경우 메모리 집약적)
all_results = list(client._list_all('api/tasks/'))
```

## 파일 다운로드를 위한 URL 변환

`url_conversion` 매개변수는 API 응답에서 URL로 참조되는 파일의 자동 다운로드를 활성화합니다. 이는 파일 참조를 포함하는 데이터 유닛, 작업 또는 모든 리소스로 작업할 때 특히 유용합니다.

### URL 변환 구조

```python
url_conversion = {
 'files_fields': ['files', 'images', 'data.attachments'], # 필드 경로
 'is_list': True # 항목 목록을 처리하는지 여부
}
```

- `files_fields`: 필드 경로 목록 (중첩 필드를 위한 점 표기법 지원)
- `is_list`: 페이지네이션된 목록 응답의 경우 `True`로 설정

### 작동 방식

1. API가 파일 URL이 포함된 응답 반환
2. `url_conversion`이 URL을 포함하는 필드 식별
3. 파일이 임시 디렉토리에 자동으로 다운로드됨
4. URL이 로컬 파일 경로로 대체됨
5. 코드가 URL 대신 로컬 경로가 포함된 응답 수신

### 예제

```python
# 단순 파일 필드
url_conversion = {'files_fields': ['image_url'], 'is_list': True}
generator, count = client._list(
 'api/photos/',
 url_conversion=url_conversion,
 list_all=True
)
for photo in generator:
 # photo['image_url']은 이제 URL이 아닌 로컬 Path 객체
 with open(photo['image_url'], 'rb') as f:
 process_image(f)

# 여러 파일 필드
url_conversion = {
 'files_fields': ['thumbnail', 'full_image', 'raw_data'],
 'is_list': True
}

# 점 표기법을 사용한 중첩 필드
url_conversion = {
 'files_fields': ['data.files', 'metadata.preview', 'annotations.image'],
 'is_list': True
}

# 더 나은 성능을 위한 비동기 다운로드
from synapse_sdk.utils.file import files_url_to_path_from_objs

results = client._list('api/data_units/')['results']
files_url_to_path_from_objs(
 results,
 files_fields=['files'],
 is_list=True,
 is_async=True # 모든 파일 동시 다운로드
)
```

## 성능 고려사항

### 메모리 효율성

대용량 데이터셋으로 작업할 때는 모든 결과를 메모리에 로드하는 대신 제너레이터를 사용하세요:

```python
# 메모리 집약적 - 모든 결과 로드
all_tasks = list(client._list('api/tasks/', list_all=True)[0])

# 메모리 효율적 - 한 번에 하나씩 처리
generator, _ = client._list('api/tasks/', list_all=True)
for task in generator:
 process_task(task)
 # 작업이 처리되고 가비지 컬렉션될 수 있음
```

### 페이지네이션 모범 사례

1. **한 페이지보다 큰 데이터셋에는 list_all=True 사용**
2. **기본값(100)이 최적이 아닌 경우 params에서 적절한 page_size 설정**
3. **파일을 처리해야 할 때만 url_conversion 사용**
4. **항목당 여러 파일이 있는 경우 비동기 다운로드 고려**

```python
# 대용량 데이터셋을 위한 최적 페이지네이션
params = {'page_size': 50} # 더 빠른 첫 응답을 위한 작은 페이지
generator, total = client._list(
 'api/large_dataset/',
 list_all=True,
 params=params
)

# 진행 상황 추적과 함께 처리
from tqdm import tqdm
for item in tqdm(generator, total=total):
 process_item(item)
```

## 클라이언트 믹스인에서의 사용

BaseClient 페이지네이션 메서드는 모든 클라이언트 믹스인에서 내부적으로 사용됩니다:

```python
# DataCollectionClientMixin
def list_data_units(self, params=None, url_conversion=None, list_all=False):
 return self._list('data_units/', params=params,
 url_conversion=url_conversion, list_all=list_all)

# AnnotationClientMixin
def list_tasks(self, params=None, url_conversion=None, list_all=False):
 return self._list('sdk/tasks/', params=params,
 url_conversion=url_conversion, list_all=list_all)
```

## 참고

- [BackendClient](./backend.md) - 메인 클라이언트 구현
- [AgentClient](./agent.md) - Agent 전용 작업
- [DataCollectionClientMixin](./data-collection-mixin.md) - 데이터 및 파일 작업
- [AnnotationClientMixin](./annotation-mixin.md) - 작업 및 주석 관리
