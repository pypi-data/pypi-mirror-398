"""Monkey patches for Ultralytics YOLO autolog."""

from __future__ import annotations

import functools
from typing import Any

from synapse_sdk.integrations._context import get_autolog_context
from synapse_sdk.integrations.ultralytics._callbacks import (
    on_fit_epoch_end,
    on_train_end,
    on_train_epoch_end,
)

# Store original methods to avoid re-patching
_original_yolo_init: Any = None
_original_yolo_train: Any = None
_patched = False


def patch_yolo() -> None:
    """Apply all YOLO patches.

    Patches:
        - YOLO.__init__: Auto-attach callbacks when model is created
        - YOLO.train: Capture epochs from kwargs

    This function is idempotent - calling it multiple times has no effect.
    """
    global _patched
    if _patched:
        return

    _patch_yolo_init()
    _patch_yolo_train()
    _patched = True


def _patch_yolo_init() -> None:
    """Patch YOLO.__init__ to auto-attach callbacks."""
    global _original_yolo_init

    from ultralytics import YOLO

    if _original_yolo_init is not None:
        return  # Already patched

    _original_yolo_init = YOLO.__init__

    @functools.wraps(_original_yolo_init)
    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        result = _original_yolo_init(self, *args, **kwargs)

        # Check if autolog is active
        ctx = get_autolog_context()
        if ctx is not None:
            # Attach Synapse callbacks
            self.add_callback('on_train_epoch_end', on_train_epoch_end)
            self.add_callback('on_fit_epoch_end', on_fit_epoch_end)
            self.add_callback('on_train_end', on_train_end)

        return result

    YOLO.__init__ = patched_init


def _patch_yolo_train() -> None:
    """Patch YOLO.train to capture epochs from kwargs."""
    global _original_yolo_train

    from ultralytics import YOLO

    if _original_yolo_train is not None:
        return  # Already patched

    _original_yolo_train = YOLO.train

    @functools.wraps(_original_yolo_train)
    def patched_train(self: Any, *args: Any, **kwargs: Any) -> Any:
        ctx = get_autolog_context()
        if ctx is not None:
            # Auto-detect epochs from train() kwargs
            epochs = kwargs.get('epochs')
            if epochs is None:
                # Check data config for epochs
                data = kwargs.get('data')
                if isinstance(data, dict):
                    epochs = data.get('epochs')

            # Fall back to ultralytics default
            if epochs is None:
                epochs = 100

            ctx.total_epochs = epochs

        return _original_yolo_train(self, *args, **kwargs)

    YOLO.train = patched_train


def unpatch_yolo() -> None:
    """Restore original YOLO methods.

    Used for testing or cleanup.
    """
    global _original_yolo_init, _original_yolo_train, _patched

    if not _patched:
        return

    from ultralytics import YOLO

    if _original_yolo_init is not None:
        YOLO.__init__ = _original_yolo_init
        _original_yolo_init = None

    if _original_yolo_train is not None:
        YOLO.train = _original_yolo_train
        _original_yolo_train = None

    _patched = False


__all__ = ['patch_yolo', 'unpatch_yolo']
