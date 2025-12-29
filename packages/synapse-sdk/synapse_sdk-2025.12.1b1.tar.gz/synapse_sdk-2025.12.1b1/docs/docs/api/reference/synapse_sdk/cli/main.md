---
sidebar_label: main
title: synapse_sdk.cli.main
---

Synapse SDK CLI main entry point.

#### version\_callback

```python
def version_callback(value: bool) -> None
```

Show version and exit.

#### main

```python
@cli.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option('--version',
                     '-v',
                     callback=version_callback,
                     is_eager=True,
                     help='Show version and exit.'),
    ] = None
) -> None
```

Synapse SDK CLI.

