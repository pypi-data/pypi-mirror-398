from collections import defaultdict
from datetime import date, timedelta
from typing import Iterator

import pypika as pk
from django.db import connections
from pypika import Case
from pypika import functions as fn
from pypika.enums import Order, SqlTypes
from wbcore.contrib.dataloader.dataloaders import Dataloader
from wbcore.contrib.dataloader.utils import dictfetchall

from wbfdm.dataloaders.protocols import FXRateProtocol
from wbfdm.dataloaders.types import FXRateDict


class FXRateConverter:
    fx_rates: dict[str, dict[date, float]]
    target_currency: str

    def load_fx_rates(self, entities, target_currency: str, from_date: date, to_date: date):
        fx_rates = defaultdict(dict)
        self.target_currency = target_currency
        if from_date:
            for fx_rate in DatastreamFXRatesDataloader(entities).fx_rates(
                from_date, to_date if to_date else date.today(), target_currency
            ):
                fx_rates[fx_rate["currency_pair"]][fx_rate["fx_date"]] = fx_rate["fx_rate"]
        self.fx_rates = fx_rates

    def apply_fx_rate(self, row, currency_columns: list[str], apply: bool = True, date_label: str = "valuation_date"):
        if row["currency"]:
            fx_rate = None
            if self.target_currency == row["currency"]:
                fx_rate = 1.0
            else:
                currency_fx_rates = self.fx_rates[f'{row["currency"]}{self.target_currency}']
                if currency_fx_rates:
                    try:
                        fx_rate = currency_fx_rates[row[date_label]] or 1.0
                    except KeyError:
                        max_idx = max(currency_fx_rates.keys())
                        fx_rate = currency_fx_rates[max_idx]
            if apply and fx_rate is not None:
                for col in currency_columns:
                    if v := row.get(col):
                        row[col] = v * fx_rate
                row["currency"] = self.target_currency
            row["fx_rate"] = fx_rate
        return row


class DatastreamFXRatesDataloader(FXRateProtocol, Dataloader):
    def fx_rates(
        self,
        from_date: date,
        to_date: date,
        target_currency: str,
    ) -> Iterator[FXRateDict]:
        currencies = list(self.entities.values_list("currency__key", flat=True))
        # Define tables
        fx_rate = pk.Table("DS2FxRate")
        fx_code = pk.Table("DS2FxCode")

        # Base query to get data we always need unconditionally
        query = (
            pk.MSSQLQuery.from_(fx_rate)
            # We join on _codes, which removes all instruments not in _codes - implicit where
            .join(fx_code)
            .on(fx_rate.ExRateIntCode == fx_code.ExRateIntCode)
            .where((fx_rate.ExRateDate >= from_date) & (fx_rate.ExRateDate <= to_date + timedelta(days=1)))
            .where(
                (fx_code.ToCurrCode == target_currency)
                & (fx_code.FromCurrCode.isin(currencies))
                & (fx_code.RateTypeCode == "SPOT")
            )
            .orderby(fx_rate.ExRateDate, order=Order.desc)
            .select(
                fn.Cast(fx_rate.ExRateDate, SqlTypes.DATE).as_("fx_date"),
                fn.Concat(fx_code.FromCurrCode, fx_code.ToCurrCode).as_("currency_pair"),
                (Case().when(fx_code.FromCurrCode == target_currency, 1).else_(1 / fx_rate.midrate)).as_("fx_rate"),
            )
        )
        with connections["qa"].cursor() as cursor:
            cursor.execute(query.get_sql())
            yield from dictfetchall(cursor, FXRateDict)
