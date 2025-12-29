# Synapse SDK v2 Development Guide

Rewrite of legacy Synapse SDK (`/Users/juhohong/VSCodeProjects/synapse-sdk/`).
Ongoing.

**Important Note**
This project, as an ongoing rewrite of legacy Synapse SDK.
Architecture changes, pydantic modeling, and  changes according to PEP 585, 604, and other 3.9+ conventions.
Breaking changes are acceptable as longs as it is documented. Main focus is enhanced code structure, architecture,
developer experience, plugin debugging experience and other improvements for better `Synapse` usage.

- Project uses `uv` for python interpreter

## Architecture

```
synapse_sdk/
├── clients/           # HTTP clients
│   ├── base.py        # BaseClient (sync/requests), AsyncBaseClient (async/httpx)
│   ├── exceptions.py  # ClientError
│   └── agent/         # AgentClient with mixins (plugin, container, ray)
├── plugins/
│   ├── action.py      # BaseAction[P] - class-based actions
│   ├── decorators.py  # @action - function-based actions
│   ├── config.py      # PluginConfig, ActionConfig
│   ├── runner.py      # run_plugin() entry point
│   ├── types.py       # PluginCategory enum
│   ├── errors.py      # PluginError hierarchy
│   ├── context/
│   │   ├── __init__.py  # RuntimeContext (dataclass)
│   │   └── env.py       # PluginEnvironment (auto-load from os.environ/TOML)
│   └── executors/
│       ├── __init__.py  # ExecutorProtocol
│       ├── local.py     # LocalExecutor (sync, in-process)
│       └── ray/         # RayActorExecutor, RayJobExecutor
├── loggers.py         # BaseLogger, ConsoleLogger, BackendLogger
└── types.py           # FileField, common types
```

## Key Patterns

### HTTP Clients
- **Sync**: `BaseClient` uses `requests` with retry via `urllib3.Retry`
- **Async**: `AsyncBaseClient` uses `httpx.AsyncClient`
- Both validate with Pydantic models via `_validate_request/response()`

### Plugin Actions

**Class-based** (preferred for complex actions):
```python
class TrainAction(BaseAction[TrainParams]):
    action_name = 'train'
    category = 'neural_net'
    params_model = TrainParams

    def execute(self) -> dict:
        self.set_progress(1, self.params.epochs)
        return {'status': 'done'}
```

**Function-based** (simple actions):
```python
@action(params=TrainParams)
def train(params: TrainParams, context: RuntimeContext) -> dict:
    return {'status': 'done'}
```

### RuntimeContext & Environment
```python
# RuntimeContext injected into actions
ctx.logger        # BaseLogger instance
ctx.env           # dict[str, Any] from PluginEnvironment
ctx.job_id        # Optional tracking ID
ctx.set_progress(current, total)
ctx.set_metrics(value, category)

# PluginEnvironment auto-loads config
env = PluginEnvironment.from_environ(prefix='PLUGIN_')
env = PluginEnvironment.from_file('config.toml')
env.get_str('API_KEY')
env.get_int('BATCH_SIZE', default=32)
env.get_bool('DEBUG', default=False)
```

### Executors
```python
# LocalExecutor - sync, in-process (dev/testing)
executor = LocalExecutor(env={'DEBUG': 'true'}, job_id='job-123')
result = executor.execute(TrainAction, {'epochs': 10})

# RayActorExecutor - persistent actor, serial execution per actor
executor = RayActorExecutor(
    working_dir='/path/to/plugin',  # auto-reads requirements.txt
    num_gpus=1,
)
result = executor.execute(TrainAction, {'epochs': 10})
executor.shutdown()

# RayJobExecutor - async job submission via dashboard API
executor = RayJobExecutor(
    dashboard_url='http://localhost:8265',
    working_dir='/path/to/plugin',
)
job_id = executor.submit('train', {'epochs': 100})
status = executor.get_status(job_id)  # PENDING, RUNNING, SUCCEEDED, FAILED
logs = executor.get_logs(job_id)
executor.wait(job_id, timeout_seconds=300)

# run_plugin() - unified entry point (local mode only for now)
result = run_plugin('yolov8', 'train', {'epochs': 10}, action_cls=TrainAction)
```

### Conventions
- Python 3.12+, `from __future__ import annotations`
- Type hints: `dict[str, Any]` not `Dict`, `X | None` not `Optional[X]`
- Pydantic v2 for validation
- Ruff for linting/formatting (single quotes, 120 line length)

### Documentation Requirements
- **Always update `README.md`** when adding new features or making breaking changes
- **Always update `REFACTORING.md`** to track migration progress (check off completed items)
- Document migration paths for clients (e.g., synapse-backend) in README's Migration Guide section