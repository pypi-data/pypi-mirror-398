"""
Export / Import Guidelines
--------------------------

1. Do NOT import the top-level package directly.
   - All imports must start from at least two levels below the root package.
     (e.g., `project.module.submodule` is allowed,
            `project` 또는 `project.module` 단일 import는 금지)

2. Wildcard import (`from x import *`) is strictly prohibited.
   - 모든 외부 노출(export)은 명시적인 이름 기반으로 관리해야 한다.
   - `__all__` 리스트를 통해 공개할 API를 명확히 정의할 것.

3. Public API 를 구성할 때:
   - 하위 모듈에서 export할 항목만 `__all__`에 선언한다.
   - 내부 구현용 함수/클래스는 `_` prefix 를 사용하거나 `__all__`에 포함하지 않는다.

4. 모듈 간 의존성은 최단 경로만 허용한다.
   - 불필요한 상위/평행 패키지 import 경로는 금지하여 순환 의존성(circular dependency)을 방지한다.
"""

from synapse_sdk.shared import worker_process_setup_hook

__all__ = ['worker_process_setup_hook']
