---
sidebar_label: export
title: synapse_sdk.plugins.actions.export
---

Export action module with optional workflow step support.

Provides the export action base class:
    - BaseExportAction: Base class for export workflows
    - ExportContext: Export-specific context extending BaseStepContext
    - ExportProgressCategories: Standard progress category names

For step infrastructure (BaseStep, StepRegistry, Orchestrator),
use the generic pipeline module:
    from synapse_sdk.plugins.pipelines.steps import BaseStep, StepRegistry

Example (simple execute):
    >>> class MyExportAction(BaseExportAction[MyParams]):
    ...     def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
    ...         return self.client.get_assignments(filters)
    ...
    ...     def execute(self) -> dict[str, Any]:
    ...         results, count = self.get_filtered_results(self.params.filter)
    ...         # ... export items ...
    ...         return \{'exported': count\}

Example (step-based):
    >>> from synapse_sdk.plugins.pipelines.steps import BaseStep, StepResult
    >>>
    >>> class FetchResultsStep(BaseStep[ExportContext]):
    ...     @property
    ...     def name(self) -> str:
    ...         return 'fetch_results'
    ...
    ...     @property
    ...     def progress_weight(self) -> float:
    ...         return 0.2
    ...
    ...     def execute(self, context: ExportContext) -> StepResult:
    ...         context.results, context.total_count = fetch_data(context.params)
    ...         return StepResult(success=True)
    >>>
    >>> class MyExportAction(BaseExportAction[MyParams]):
    ...     def setup_steps(self, registry) -> None:
    ...         registry.register(FetchResultsStep())
    ...         registry.register(ProcessStep())
    ...         registry.register(FinalizeStep())

