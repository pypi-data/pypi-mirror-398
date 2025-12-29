"""Ultralytics YOLO callback implementations for autolog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from synapse_sdk.integrations._context import get_autolog_context


def on_train_epoch_end(trainer: Any) -> None:
    """Log training metrics at end of each epoch.

    Logs:
        - Progress: epoch/total_epochs
        - Metrics: box_loss, cls_loss, dfl_loss (category='train')

    Args:
        trainer: Ultralytics trainer instance.
    """
    ctx = get_autolog_context()
    if ctx is None:
        return

    action = ctx.action
    epoch = trainer.epoch + 1
    total_epochs = ctx.total_epochs or getattr(trainer, 'epochs', 100)

    # Update progress
    action.set_progress(epoch, total_epochs, 'train')

    # Log loss metrics
    if hasattr(trainer, 'loss_items') and trainer.loss_items is not None:
        loss_items = trainer.loss_items
        if hasattr(loss_items, 'cpu'):
            loss_items = loss_items.cpu().numpy()

        action.set_metrics(
            {
                'epoch': epoch,
                'box_loss': float(loss_items[0]),
                'cls_loss': float(loss_items[1]),
                'dfl_loss': float(loss_items[2]),
            },
            category='train',
        )


def on_fit_epoch_end(trainer: Any) -> None:
    """Log validation metrics after validation pass.

    Logs:
        - Metrics: mAP50, mAP50_95 (category='validation')
        - Files: validation batch prediction images

    Args:
        trainer: Ultralytics trainer instance.
    """
    ctx = get_autolog_context()
    if ctx is None:
        return

    action = ctx.action
    epoch = trainer.epoch + 1
    metrics = trainer.metrics

    if metrics:
        action.set_metrics(
            {
                'epoch': epoch,
                'mAP50': metrics.get('metrics/mAP50(B)', 0),
                'mAP50_95': metrics.get('metrics/mAP50-95(B)', 0),
            },
            category='validation',
        )

        # Log validation sample images
        save_dir = Path(trainer.save_dir)
        for i in range(3):
            img_path = save_dir / f'val_batch{i}_pred.jpg'
            if img_path.exists():
                action.log(
                    'validation_samples',
                    {'group': epoch, 'index': i},
                    file=str(img_path),
                )

    # Ray Tune integration
    is_tune = action.ctx.env.get_bool('IS_TUNE', default=False)
    if is_tune and metrics:
        try:
            from ray import tune

            tune.report(**metrics)
        except ImportError:
            pass


def on_train_end(trainer: Any) -> None:
    """Log final artifacts when training completes.

    Logs:
        - Files: best.pt weights, results.csv

    Args:
        trainer: Ultralytics trainer instance.
    """
    ctx = get_autolog_context()
    if ctx is None:
        return

    action = ctx.action
    save_dir = Path(trainer.save_dir)

    # Log final model weights
    best_pt = save_dir / 'weights' / 'best.pt'
    if best_pt.exists():
        action.log('model_weights', {'type': 'best'}, file=str(best_pt))

    # Log training results CSV
    results_csv = save_dir / 'results.csv'
    if results_csv.exists():
        action.log('training_results', {}, file=str(results_csv))


__all__ = ['on_train_epoch_end', 'on_fit_epoch_end', 'on_train_end']
