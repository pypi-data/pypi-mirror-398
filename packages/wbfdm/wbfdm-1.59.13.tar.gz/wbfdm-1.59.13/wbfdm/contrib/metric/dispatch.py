from contextlib import suppress
from datetime import date
from typing import Any

from wbfdm.contrib.metric.signals import instrument_metric_updated


def compute_metrics(val_date: date, key: str | None = None, basket: Any | None = None, **kwargs):
    """
    Compute and process metrics for a given date using the MetricOrchestrator.

    Args:
        val_date (date): The validation date for the metrics computation.
        key (Optional[str]): The optional metric backend key to narrow down the set of backends to use. Defaults to None.
        basket (Optional[Any]): An optional basket to narrow down the backend queryset. Defaults to None.
        **kwargs: Additional keyword arguments to pass to the MetricOrchestrator.

    Returns:
        None
    """
    from wbfdm.contrib.metric.orchestrators import MetricOrchestrator

    with suppress(KeyError):
        orchestrator = MetricOrchestrator(val_date, key=key, basket=basket, **kwargs)
        orchestrator.process()
        instrument_metric_updated.send(sender=basket.__class__, basket=basket, key=key, val_date=val_date)
