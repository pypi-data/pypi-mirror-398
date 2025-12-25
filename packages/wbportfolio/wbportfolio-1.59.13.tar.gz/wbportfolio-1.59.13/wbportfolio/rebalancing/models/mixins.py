from django.db.models import QuerySet
from wbfdm.models import Classification, Instrument, InstrumentListThroughModel


class InstrumentMixin:
    def get_instruments(self, **kwargs):
        return self._filter_instruments(self._get_instruments(**kwargs), **kwargs)

    def _get_instruments(
        self,
        classification_ids: list[int] | None = None,
        instrument_ids: list[int] | None = None,
        instrument_list_id: int | None = None,
        **kwargs,
    ) -> QuerySet[Instrument]:
        """
        Use the provided kwargs to return a list of instruments as universe.
        - If classifications are given, we returns all the instrument linked to these classifications
        - Or directly from a static list of instrument ids
        - fallback to the last effective portfolio underlying instruments list
        """
        if not instrument_ids:
            instrument_ids = []
        if classification_ids:
            for classification in Classification.objects.filter(id__in=classification_ids):
                for children in classification.get_descendants(include_self=True):
                    for company in children.instruments.all():
                        instrument_ids.append(company.get_primary_quote().id)
        if instrument_list_id:
            instrument_ids.extend(
                list(
                    InstrumentListThroughModel.objects.filter(instrument_list_id=instrument_list_id).values_list(
                        "instrument", flat=True
                    )
                )
            )

        if not instrument_ids:
            instrument_ids = list(self.effective_portfolio.positions_map.keys())

        return Instrument.objects.filter(id__in=instrument_ids)

    def _filter_instruments(
        self, instruments: QuerySet[Instrument], instrument_filter_kwargs: dict[str, str] | None = None, **kwargs
    ) -> QuerySet[Instrument]:
        instruments = instruments.filter(is_cash=False)
        if instrument_filter_kwargs:
            instruments = instruments.filter(**instrument_filter_kwargs)
        return instruments
