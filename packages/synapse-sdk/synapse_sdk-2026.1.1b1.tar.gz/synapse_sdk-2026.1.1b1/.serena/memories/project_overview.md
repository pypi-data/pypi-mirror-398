# Synapse SDK v2 - Project Overview

## Purpose
Rewrite of legacy Synapse SDK with focus on enhanced code structure, architecture, developer experience, and plugin debugging. Breaking changes are acceptable as long as documented.

## Tech Stack
- **Python**: 3.12+ (uses modern type hints, PEP 585/604)
- **Package Manager**: `uv` (not pip directly)
- **Validation**: Pydantic v2
- **HTTP Clients**: `requests` (sync), `httpx` (async)
- **CLI**: Typer + Rich
- **Testing**: pytest with coverage, asyncio, mocking
- **Linting/Formatting**: Ruff
- **Build**: setuptools with setuptools-scm for versioning
- **Optional**: Ray for distributed execution, cloud storage (s3fs, gcsfs, sshfs)

## Codebase Structure
```
synapse_sdk/
  clients/       # HTTP clients (sync/async, agent client with mixins)
  plugins/       # Action framework, decorators, config, runner, executors
    executors/   # LocalExecutor, RayActorExecutor, RayJobExecutor
    context/     # RuntimeContext, PluginEnvironment
  utils/         # Storage, file utilities
  mcp/           # Model Context Protocol server
  cli/           # Command line interface (typer-based)
  integrations/  # External integrations
  shared/        # Shared utilities
  loggers.py     # BaseLogger, ConsoleLogger, BackendLogger
  enums.py       # Enums
  exceptions.py  # Exception hierarchy
```

## Key Concepts
- **BaseAction[P]**: Class-based actions with Pydantic params
- **@action decorator**: Function-based actions (simpler cases)
- **RuntimeContext**: Injected into actions (logger, env, job_id, progress/metrics setters)
- **Executors**: LocalExecutor (dev), RayActorExecutor (persistent), RayJobExecutor (async jobs)
- **PluginDiscovery**: Discover actions from config.yaml or Python modules
