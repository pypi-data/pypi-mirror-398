---
sidebar_label: registry
title: synapse_sdk.utils.storage.registry
---

Storage provider registry with lazy loading.

#### get\_provider\_class

```python
def get_provider_class(provider: str) -> type[StorageProtocol]
```

Get the storage provider class for the given provider name.

**Arguments**:

- `provider` - Provider name (e.g., 's3', 'gcs', 'local').
  

**Returns**:

  Storage provider class.
  

**Raises**:

- `StorageProviderNotFoundError` - If provider is not registered.

#### register\_provider

```python
def register_provider(name: str,
                      factory: Callable[[], type[StorageProtocol]]) -> None
```

Register a custom storage provider.

**Arguments**:

- `name` - Provider name to register.
- `factory` - Factory function that returns the provider class.
  

**Example**:

  >>> def custom_factory():
  ...     from my_module import CustomStorage
  ...     return CustomStorage
  >>> register_provider('custom', custom_factory)

#### get\_registered\_providers

```python
def get_registered_providers() -> list[str]
```

Get list of registered provider names.

**Returns**:

  List of registered provider names.

