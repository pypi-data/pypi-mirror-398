import operator
from contextlib import suppress
from datetime import datetime
from functools import reduce
from typing import Any, Dict, Optional

from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, models
from django.db.models import Exists, OuterRef, Q
from slugify import slugify
from wbcore.contrib.currency.import_export.handlers import CurrencyImportHandler
from wbcore.contrib.geography.models import Geography
from wbcore.contrib.io.exceptions import DeserializationError
from wbcore.contrib.io.imports import ImportExportHandler, ImportState

from wbfdm.models.exchanges import Exchange


class InstrumentLookup:
    ORDERED_KEYS = [
        "instrument_type",
        "isin",
        "refinitiv_identifier_code",
        "refinitiv_mnemonic_code",
        "identifier",
        "ticker",
        "currency",
    ]

    def __init__(self, model, trigram_similarity_min_score: float = 0.8):
        self.cache = {}
        self.model = model
        self.trigram_similarity_min_score = trigram_similarity_min_score

    @classmethod
    def _get_cache_key(cls, **data):
        return "-".join([f"{k}:{slugify(str(data[k]))}" for k in cls.ORDERED_KEYS if data.get(k, None) is not None])

    def _get_cache(self, **kwargs):
        cache_key = self._get_cache_key(**kwargs)
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]

    def _set_cache(self, instrument, **kwargs):
        cache_key = self._get_cache_key(**kwargs)
        self.cache[cache_key] = instrument

    def _get_instruments_from_identifiers(self, queryset, **identifiers):
        # Try exact lookup on the filtered out universe
        identifiers = {k: v for k, v in identifiers.items() if v is not None}
        for identifier_key in [
            "isin",
            "refinitiv_identifier_code",
            "refinitiv_mnemonic_code",
            "sedol",
            "cusip",
            "identifier",
        ]:
            if identifier := identifiers.get(identifier_key, None):
                with suppress(self.model.DoesNotExist, MultipleObjectsReturned):
                    identifier = str(identifier)
                    if (
                        identifier_key != "refinitiv_identifier_code"
                    ):  # RIC cannot be uppercased because its symbology implies meaning for lowercase characters
                        identifier = identifier.upper()
                    # we try to lookup the instrument with the unique identifier
                    instrument = queryset.get(**{identifier_key: identifier})
                    return self.model.objects.filter(id=instrument.id)
        return queryset

    def _filter_identifiers(self, queryset, **identifiers):
        lookup_fields = [
            "isin",
            "refinitiv_identifier_code",
            "refinitiv_mnemonic_code",
            "refinitiv_ticker",
            "identifier",
            "ticker",
        ]
        conditions = []
        for field in lookup_fields:
            if field_value := identifiers.get(field, None):
                conditions.append(Q(**{f"{field}": field_value}))
                if field == "isin":
                    conditions.append(Q(old_isins__contains=[field_value]))
                if field == "ticker":
                    conditions.append(
                        Q(ticker__regex=rf"^{field_value}(\.[A-Za-z])$")
                    )  # initial regex: ([A-Za-z]?|\.?[A-Za-z])$ This led to a false positive, I don't remember why we allow an extra random character to be consider for eval
                    conditions.append(Q(refinitiv_mnemonic_code=f"@{field_value}"))

        if conditions:
            return queryset.filter(reduce(operator.or_, conditions))
        return queryset

    def _filter_name(self, queryset, name):
        instruments = queryset.annotate(similarity_score=TrigramSimilarity("name", name))
        if (
            queryset.count() > 1
            and instruments.filter(similarity_score__gt=self.trigram_similarity_min_score).count() == 1
        ):
            return instruments.filter(similarity_score__gt=self.trigram_similarity_min_score)
        return queryset

    def _filter_currency(self, queryset, currency):
        qs = queryset.filter(currency=currency)
        if qs.exists():
            return qs
        return queryset

    def _filter_exchange(self, queryset, exchange):
        return queryset.filter(exchange=exchange)

    def _filter_instrument_type(self, queryset, instrument_type):
        if not isinstance(instrument_type, str):
            instrument_type = instrument_type.key
        if instrument_type == "equity":
            qs = queryset.filter(instrument_type__key__in=["equity", "american_depository_receipt"])
        else:
            qs = queryset.filter(instrument_type__key=instrument_type)
        if qs.exists():
            return qs
        return queryset

    def _get_queryset(self, only_investable_universe: bool = False):
        instruments = self.model.objects.filter(is_security=True)
        if only_investable_universe:
            instruments = instruments.annotate(
                has_children_in_investable_universe=Exists(
                    self.model.objects.filter(is_investable_universe=True, parent=OuterRef("id"))
                )
            ).filter(Q(is_investable_universe=True) | Q(has_children_in_investable_universe=True))
        return instruments

    def _get_security_candidates(  # noqa: C901
        self,
        queryset,
        instrument_type=None,
        currency=None,
        name=None,
        **identifiers,
    ):
        # We need to lookup ticker because some provider gives us ticker with or without space in it
        instruments = self._get_instruments_from_identifiers(queryset, **identifiers)
        if instrument_type:
            instruments = self._filter_instrument_type(instruments, instrument_type)

        if instruments.count() == 1:
            return instruments

        instruments = self._filter_identifiers(instruments, **identifiers)

        if currency:
            instruments = self._filter_currency(instruments, currency)
        if name:
            instruments = self._filter_name(instruments, name)
        return instruments

    def _lookup_quote(
        self,
        security,
        currency=None,
        exchange=None,
        refinitiv_identifier_code=None,
        refinitiv_mnemonic_code=None,
        **kwargs,
    ):
        quotes = security.children.all()
        if not quotes.exists():
            return security
        if quotes.count() == 1:
            return quotes.first()
        if exchange:
            quotes = self._filter_exchange(quotes, exchange)
        if currency:
            quotes = self._filter_currency(quotes, currency)
        if refinitiv_mnemonic_code or refinitiv_identifier_code:
            quotes = self._filter_identifiers(
                quotes,
                refinitiv_identifier_code=refinitiv_identifier_code,
                refinitiv_mnemonic_code=refinitiv_mnemonic_code,
            )
        if quotes.filter(is_investable_universe=True).count() == 1:
            quotes = quotes.filter(is_investable_universe=True)
        if quotes.count() == 1:
            return quotes.first()
        return security.children.filter(is_primary=True).first()

    def lookup_security(self, **kwargs):
        queryset = self._get_queryset(only_investable_universe=False)
        security_candidates = self._get_security_candidates(queryset, **kwargs)

        if security_candidates.count() == 1:
            return security_candidates.first()
        # queryset = self._get_queryset(only_investable_universe=False)
        # security_candidates = self._get_security_candidates(queryset, **kwargs)

        if security_candidates.exists() > 1:
            security_candidates = security_candidates.filter(delisted_date__isnull=True)
        if security_candidates.count() == 1:
            return security_candidates.first()

    def lookup(self, only_security: bool = False, **lookup_kwargs):
        # To speed up lookup process, we try to get the quote from the investable universe first
        if instrument := self._get_cache(**lookup_kwargs):
            return instrument
        instrument = self.lookup_security(**lookup_kwargs)
        if not only_security and instrument:
            instrument = self._lookup_quote(instrument, **lookup_kwargs)
        if instrument:
            self._set_cache(instrument, **lookup_kwargs)
        return instrument


class InstrumentImportHandler(ImportExportHandler):
    MODEL_APP_LABEL: str = "wbfdm.Instrument"
    allow_update_save_failure = True
    exclude_update_fields = ["name", "isin", "country"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instrument_lookup = InstrumentLookup(self.model)
        self.currency_handler = CurrencyImportHandler(self.import_source)

    def _deserialize(self, data: Dict[str, Any]):
        from wbfdm.models import Classification, InstrumentType

        if isinstance(data, int):
            data = dict(id=data)
        if data.get("currency", None):
            data["currency"] = self.currency_handler.process_object(
                data["currency"], read_only=True, raise_exception=False
            )[0]
        if instrument_type := data.get("instrument_type", None):
            if isinstance(instrument_type, str):
                data["instrument_type"] = InstrumentType.objects.get_or_create(
                    key=instrument_type,
                    defaults={"name": instrument_type.title(), "short_name": instrument_type.title()},
                )[0]
            elif isinstance(instrument_type, int):
                data["instrument_type"] = InstrumentType.objects.get(id=instrument_type)
        if data.get("country", None):
            data["country"] = Geography.dict_to_model(data["country"])
        if data.get("headquarter_city", None):
            data["headquarter_city"] = Geography.dict_to_model(data["headquarter_city"], level=Geography.Level.CITY)
        if inception_date := data.get("inception_date", None):
            data["inception_date"] = datetime.strptime(inception_date, "%Y-%m-%d").date()
        if classifications := data.pop("classifications", None):
            data["classifications"] = [Classification.dict_to_model(c) for c in classifications]
        if (exchange_data := data.pop("exchange", None)) and isinstance(exchange_data, dict):
            sanitized_dict = {k: v for k, v in exchange_data.items() if v is not None}
            if sanitized_dict:
                data["exchange"] = Exchange.dict_to_model(sanitized_dict)

    def _get_instance(
        self,
        data: Dict[str, Any],
        history: Optional[models.QuerySet] = None,
        only_security: bool = False,
        **kwargs,
    ) -> models.Model:
        if isinstance(data, self.model):
            return data
        if instrument_id := data.pop("id", None):
            try:
                return self.model.objects.get(id=instrument_id)
            except self.model.DoesNotExist as e:
                raise DeserializationError("Instrument id does not match an existing instrument") from e
        else:
            return self.instrument_lookup.lookup(only_security=only_security, **data)

    def _create_instance(self, data: Dict[str, Any], **kwargs) -> models.Model:
        from wbfdm.models.instruments.instruments import Instrument

        if not data.get("name", None):
            raise DeserializationError("Can't create an instrument without at least a name")
        classifications = data.pop("classifications", None)
        try:
            obj = Instrument.objects.create(
                **data,
                import_source=self.import_source,
            )
            if classifications:
                obj.classifications.set([c for c in classifications if c])
            return obj
        except IntegrityError:
            self.import_source.log += f"\nError while creating new instrument with data {data}"

        return None

    def process_object(self, underlying_instrument_data, **kwargs):
        if underlying_instrument_data:
            if isinstance(underlying_instrument_data, self.model):
                return underlying_instrument_data, ImportState.UNMODIFIED
            if isinstance(underlying_instrument_data, int):
                underlying_instrument_data = dict(id=underlying_instrument_data)
        return super().process_object(
            underlying_instrument_data,
            include_update_fields=[
                "isin",
                "ticker",
                "refinitiv_mnemonic_code",
                "refinitiv_identifier_code",
                "country",
                "exchange",
            ],
            **kwargs,
        )
