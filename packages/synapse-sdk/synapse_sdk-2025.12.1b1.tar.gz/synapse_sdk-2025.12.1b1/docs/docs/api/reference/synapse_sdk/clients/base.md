---
sidebar_label: base
title: synapse_sdk.clients.base
---

## BaseClient Objects

```python
class BaseClient()
```

#### requests\_session

```python
@property
def requests_session() -> requests.Session
```

Get or create the requests session.

#### exists

```python
def exists(api: str, *args, **kwargs) -> bool
```

Check if any results exist for the given API method.

## AsyncBaseClient Objects

```python
class AsyncBaseClient()
```

Async HTTP client base using httpx.

#### close

```python
async def close() -> None
```

Close the HTTP client.

