import json

import numpy as np
import pandas as pd
from django.utils.dateparse import parse_date

BASE_MAPPING = {
    "instrument": "underlying_instrument__name",
    "ric": "underlying_instrument__refinitiv_identifier_code",
    "bbTicker": "underlying_instrument__ticker",
    "isin": "underlying_instrument__isin",
    "assetClass": "underlying_instrument__instrument_type",
    "direction": "transaction_subtype",
    "currency": "currency__key",
    "quantityTraded": "shares",
    "localPrice": "price",
    "fxMultiplier": "currency_fx_rate",
    "tradeDate": "book_date",
}


def parse(import_source):
    content = json.load(import_source.file)
    data = []
    if (rebalances := content.get("rebalances", None)) and (isin := content.get("isin", None)):
        for rebalance_data in rebalances:
            rebalancing_date = parse_date(rebalance_data["rebalanceDate"])
            df = pd.DataFrame(rebalance_data["items"]).replace([np.inf, -np.inf, np.nan], None)
            df = df.rename(columns=BASE_MAPPING)
            df = df.drop(columns=df.columns.difference(BASE_MAPPING.values()))
            df["underlying_instrument__instrument_type"] = df["underlying_instrument__instrument_type"].str.lower()
            df["transaction_date"] = rebalancing_date.strftime("%Y-%m-%d")
            df["portfolio__isin"] = isin
            df.loc[df["book_date"].isnull(), "book_date"] = df.loc[df["book_date"].isnull(), "transaction_date"]
            df["currency_fx_rate"] = 1 / df["currency_fx_rate"]
            df.loc[df["price"].isnull() & (df["underlying_instrument__instrument_type"] == "cash"), "price"] = 1.0
            df["underlying_instrument__currency__key"] = df["currency__key"]
            data.extend(df.to_dict(orient="records"))
    return {"data": data}
