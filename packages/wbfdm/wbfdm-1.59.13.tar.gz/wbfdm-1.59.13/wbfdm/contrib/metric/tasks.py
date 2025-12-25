from datetime import date

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from wbcore.workers import Queue

from wbfdm.contrib.metric.dispatch import compute_metrics


@shared_task(queue=Queue.EXTENDED_BACKGROUND.value)
def compute_metrics_as_task(
    val_date: date | None = None,
    key: str | None = None,
    basket_content_type_id: int | None = None,
    basket_id: int | None = None,
    **kwargs,
):
    """
    Run the orchestrator as a async task periodically for all keys and baskets

    Args:
        val_date (date): Compute the metric for the given date (Default to None). If None, let the metric backends decide what is the last valide date to use

    """
    basket = None
    if basket_content_type_id and basket_id:
        basket = ContentType.objects.get(id=basket_content_type_id).get_object_for_this_type(pk=basket_id)
    compute_metrics(val_date=val_date, key=key, basket=basket, **kwargs)
