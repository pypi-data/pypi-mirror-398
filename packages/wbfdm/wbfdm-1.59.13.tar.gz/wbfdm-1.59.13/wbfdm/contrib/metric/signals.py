from django.db.models.signals import ModelSignal

# this signal is triggered whenever all instruments metrics are updated. Temporary solution until we rework the framework for more dynamicity

instrument_metric_updated = ModelSignal(
    use_caching=True
)  # the sender model is the type model class being updated (e.g. Instrument), expect a "basket", "key" and "val_date" keyword argument (null if all are updated)
