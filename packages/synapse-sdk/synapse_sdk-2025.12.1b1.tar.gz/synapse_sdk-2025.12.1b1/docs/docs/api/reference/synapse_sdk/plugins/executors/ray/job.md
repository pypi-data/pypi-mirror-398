---
sidebar_label: job
title: synapse_sdk.plugins.executors.ray.job
---

Ray Job executor for plugin actions.

## RayJobExecutor Objects

```python
class RayJobExecutor(BaseRayExecutor)
```

Ray Job Submission Client based asynchronous execution.

Submits actions as Ray jobs via the Job Submission API. Best for
heavy/long-running workloads. Jobs run asynchronously and can be
monitored via the Ray dashboard.

**Example**:

  >>> executor = RayJobExecutor(
  ...     dashboard_url='http://localhost:8265',
  ...     working_dir='/path/to/plugin',  # Auto-reads requirements.txt
  ... )
  >>> job_id = executor.submit('train', \{'epochs': 100\})
  >>> status = executor.get_status(job_id)
  >>> logs = executor.get_logs(job_id)

#### submit

```python
def submit(action_name: str,
           params: dict[str, Any],
           *,
           job_id: str | None = None,
           **kwargs: Any) -> str
```

Submit action as a Ray job.

Unlike execute(), this returns immediately with a job_id.
Use get_status() and get_logs() to monitor progress.

**Arguments**:

- `action_name` - Name of the action to execute.
- `params` - Parameters dict for the action.
- `job_id` - Optional submission ID. If None, Ray generates one.
- `**kwargs` - Additional options passed to submit_job().
  

**Returns**:

  Job submission ID for tracking.
  

**Raises**:

- `ExecutionError` - If job submission fails.

#### get\_status

```python
def get_status(job_id: str) -> str
```

Get job status.

**Arguments**:

- `job_id` - Job submission ID.
  

**Returns**:

  Job status string (PENDING, RUNNING, SUCCEEDED, FAILED, STOPPED).

#### get\_logs

```python
def get_logs(job_id: str) -> str
```

Get job logs.

**Arguments**:

- `job_id` - Job submission ID.
  

**Returns**:

  Job stdout/stderr logs as string.

#### stop

```python
def stop(job_id: str) -> bool
```

Stop a running job.

**Arguments**:

- `job_id` - Job submission ID.
  

**Returns**:

  True if stop was successful.

#### wait

```python
def wait(job_id: str, timeout_seconds: float = 300) -> str
```

Wait for job to complete.

**Arguments**:

- `job_id` - Job submission ID.
- `timeout_seconds` - Maximum time to wait.
  

**Returns**:

  Final job status.
  

**Raises**:

- `ExecutionError` - If job fails or times out.

