import datetime
import logging
import re

import numpy as np
import pandas as pd

from wbportfolio.import_export.utils import convert_string_to_number

logger = logging.getLogger("importers.parsers.jp_morgan.strategy")


def file_name_parse(file_name):
    dates = re.findall("([0-9]{8})", file_name)
    if dates:
        return {"valuation_date": datetime.datetime.strptime(dates[0], "%Y%m%d").date()}
    return {}


def parse(import_source):
    # Load file into a CSV DictReader

    df = pd.read_csv(import_source.file, encoding="utf-16", delimiter=",")

    # Parse the Parts of the filename into the different parts
    parts = file_name_parse(import_source.file.name)

    # Get the valuation date from the parts list
    report_date = parts.get("valuation_date")

    # Iterate through the CSV File and parse the data into a list
    data = list()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    df.replace([np.inf, -np.inf, np.nan], None, inplace=True)
    for strategy_data in df.to_dict("records"):
        valuation_date = strategy_data.get("Date", report_date)
        if valuation_date:
            bbg_tickers = strategy_data["BBG Ticker"].split(" ")
            exchange = None
            if len(bbg_tickers) == 2:
                ticker = bbg_tickers[0]
                instrument_type = bbg_tickers[1]
            elif len(bbg_tickers) == 3:
                ticker = bbg_tickers[0]
                exchange = bbg_tickers[1]
                instrument_type = bbg_tickers[2]

            strategy = strategy_data["Strategy Ticker"].replace("Index", "").strip()
            strategy_currency_key = strategy_data["Strategy CCY"]

            position_currency_key = strategy_data["Position CCY"]

            isin = strategy_data["Position ISIN"]
            name = strategy_data["Position Description"]
            initial_price = convert_string_to_number(strategy_data["Prices"])
            initial_currency_fx_rate = convert_string_to_number(strategy_data["Fx Rates"])
            if exchange:
                exchange = {"bbg_exchange_codes": exchange}
            try:
                weighting = convert_string_to_number(strategy_data["Weight In Percent"].replace("%", "")) / 100
            except Exception:
                weighting = 0.0
            underlying_quote = {
                "ticker": ticker,
                "exchange": exchange,
                "isin": isin,
                "name": name,
                "currency__key": position_currency_key,
                "instrument_type": instrument_type.lower(),
            }
            if isin:
                underlying_quote["isin"] = isin
            data.append(
                {
                    "underlying_quote": underlying_quote,
                    "portfolio": {
                        "instrument_type": "index",
                        "ticker": strategy,
                        "currency__key": strategy_currency_key,
                    },
                    "exchange": exchange,
                    "is_estimated": False,
                    "currency__key": position_currency_key,
                    "initial_currency_fx_rate": initial_currency_fx_rate,
                    "weighting": weighting,
                    "initial_price": initial_price,
                    "date": valuation_date.strftime("%Y-%m-%d"),
                }
            )
    return {"data": data}
