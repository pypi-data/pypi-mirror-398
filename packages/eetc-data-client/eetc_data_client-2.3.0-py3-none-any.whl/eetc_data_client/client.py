from typing import Union, List, Dict

import pandas as pd
import requests
from requests import Response


class EETCDataClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://eetc-data-hub-service-nb7ewdzv6q-ue.a.run.app/api"

    def _send_http_request(self, url: str, params: dict) -> Response:
        if params is None:
            params = {}

        response = requests.get(
            url,
            params=params,
            headers={"EETC-API-Key": self.api_key},
        )

        if response.status_code != 200:
            response.raise_for_status()

        return response

    def get_price_data(
        self,
        symbol: str,
        date: str = None,
        from_date: str = None,
        to_date: str = None,
        as_json=False,
    ) -> Union[pd.DataFrame, List[Dict]]:
        """
        Get historical Price data from EETC Data Hub via REST API.

        :param symbol: Symbol of the instrument.
        :param date: Specific date in string format "yyyy-mm-dd"
        :param from_date: Earliest date in string format "yyyy-mm-dd"
        :param to_date: Latest date in string format "yyyy-mm-dd"
        :param as_json: Indicates if caller wants data returned as JSON. False
        by default, if False, it will return the data as a pandas DataFrame.
        :return: Historical Price data as a pandas DataFrame.
        """

        url = f"{self.base_url}/price/?symbol={symbol}"
        params = {}

        # add optional query params
        if date:
            params["date"] = date

        if from_date:
            params["from_date"] = from_date

        if to_date:
            params["to_date"] = to_date

        # send the HTTP request to EETC Data Hub
        response = self._send_http_request(url, params)

        # process and return response data
        response_data = response.json()

        if as_json:
            return response_data

        df = pd.json_normalize(response_data)
        df = df.sort_values(by=["date"])

        return df

    def get_indicator_data(
        self,
        name: str,
        frequency: str = None,
        from_date: str = None,
        to_date: str = None,
        as_json=False,
    ) -> Union[pd.DataFrame, List[Dict]]:
        """
        Get historical Macroeconomic data from EETC Data Hub via REST API.

        :param name: Name of the macroeconomic data point.
        :param frequency: "Yearly", "Quarterly", "Monthly", "Weekly", "Daily".
        :param from_date: Earliest date in string format "yyyy-mm-dd"
        :param to_date: Latest date in string format "yyyy-mm-dd"
        :param as_json: Indicates if caller wants data returned as JSON. False
        by default, if False, it will return the data as a pandas DataFrame.
        :return: Historical Macroeconomic data as a pandas DataFrame.
        """

        url = f"{self.base_url}/indicators/?name={name}"
        params = {}

        # add optional query params
        if frequency:
            params["frequency"] = frequency

        if from_date:
            params["from_date"] = from_date

        if to_date:
            params["to_date"] = to_date

        # send the HTTP request to EETC Data Hub
        response = self._send_http_request(url, params)

        # process and return response data
        response_data = response.json()

        if as_json:
            return response_data

        df = pd.json_normalize(response_data)
        df = df.sort_values(by=["date"])

        return df

    def get_indicators(self) -> Dict[str, List[str]]:
        """
        Get supported indicators grouped by frequency from EETC Data Hub via
        REST API.

        :return: List of indicator names grouped by frequency.
        """

        url = f"{self.base_url}/indicators/names/"

        # send the HTTP request to EETC Data Hub
        response = self._send_http_request(url, {})

        # process and return response data
        response_data = response.json()

        return response_data

    def get_companies(self, index: str = None) -> Dict[str, List[str]]:
        """
        Get supported companies from EETC Data Hub via REST API.

        :param index: Index which contains the Company.
        :return: List of companies in the EETC Data Hub database.
        """

        url = f"{self.base_url}/companies/"
        params = {}

        # add optional query params
        if index:
            params["index"] = index

        # send the HTTP request to EETC Data Hub
        response = self._send_http_request(url, params)

        # process and return response data
        response_data = response.json()

        return response_data

    def get_orders(
        self,
        order_id: str = None,
        asset_type: str = None,
        action: str = None,
        symbol: str = None,
        strike: float = None,
        right: str = None,
        currency: str = None,
        exchange: str = None,
        strategy: str = None,
        broker: str = None,
        position_id: str = None,
        as_json: bool = False,
    ):
        """
        Retrieve order records from the EETC Data Hub via the `/orders` API.

        This endpoint returns trading order data with optional filtering.
        Filters can be combined to narrow down results (e.g., by symbol and action).

        :param order_id: Unique identifier of the order.
        :param asset_type: Type of asset, e.g. "EQUITY", "OPTION", "FUTURE".
        :param action: Action taken for the order, e.g. "BUY" or "SELL".
        :param symbol: Ticker symbol of the instrument, e.g. "AAPL".
        :param strike: Strike price (applicable for options).
        :param right: Option right, e.g. "CALL" or "PUT".
        :param currency: Currency of the trade, e.g. "USD".
        :param exchange: Exchange where the order was placed, e.g. "NASDAQ".
        :param strategy: Trading strategy associated with the order.
        :param broker: Broker handling the order, e.g. "IBKR".
        :param position_id: Identifier of the related position, if any.
        :param as_json: If True, returns raw JSON instead of a DataFrame.
        :return: List of order dictionaries or a pd.DataFrame.
        """

        url = f"{self.base_url}/orders/"
        params = {
            "order_id": order_id,
            "asset_type": asset_type,
            "action": action,
            "symbol": symbol,
            "strike": strike,
            "right": right,
            "currency": currency,
            "exchange": exchange,
            "strategy": strategy,
            "broker": broker,
            "position_id": position_id,
        }
        # Remove any None values (so only provided filters are sent)
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(
            url,
            params=params,
            headers={"EETC-API-Key": self.api_key},
        )

        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()

        return data if as_json else pd.json_normalize(data)


    def save_orders(self, orders: list[dict]) -> None:
        """
        Save one or multiple orders to the EETC Data Hub.

        :param orders: List of dicts with order data, e.g.
            [
                {
                    "order_id": "123",
                    "asset_type": "OPT",
                    "action": "BUY",
                    "symbol": "AAPL",
                    "strike": 150.0,
                    "right": "C",
                    "size": 10,
                    "price": 120.5,
                    "currency": "USD",
                    "exchange": "NASDAQ",
                    "strategy": "Long Call",
                    "broker": "IBKR",
                    "position_id": "pos_123"
                }
            ]
        """

        url = f"{self.base_url}/orders/"

        response = requests.post(
            url,
            json=orders,
            headers={
                "Content-Type": "application/json",
                "EETC-API-Key": self.api_key,
            },
        )

        if response.status_code not in [200, 201]:
            response.raise_for_status()

    def get_roguetrader_signals(
        self,
        date: str = None,
        symbol: str = None,
        as_json: bool = False,
    ):
        """
        Retrieve order records from the EETC Data Hub via the
        `/roguetrader-signals` API.

        This endpoint returns eetc-roguetrader generated signals
        data with optional filtering.
        Filters can be combined to narrow down results (e.g., by date).

        :param date: Signal generation date.
        :param symbol: Ticker symbol of the instrument, e.g. "AAPL".
        :param as_json: If True, returns raw JSON instead of a DataFrame.
        :return: List of order dictionaries or a pd.DataFrame.
        """

        url = f"{self.base_url}/roguetrader-signals/"
        params = {
            "date": date,
            "symbol": symbol,
        }
        # Remove any None values (so only provided filters are sent)
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(
            url,
            params=params,
            headers={"EETC-API-Key": self.api_key},
        )

        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()

        return data if as_json else pd.json_normalize(data)


    def save_roguetrader_signals(self, signals: list[dict]) -> None:
        """
        Save one or multiple eetc-roguetrader signals to the EETC Data Hub.

        :param signals: List of dicts with RogueTrader signal data, e.g.
        [
            {
                "date": "2024-01-15",
                "symbol": "SPY",
                "previous_close": 450.25,
                "open_price": 451.00,
                "open_gap": 0.17,
                "atm_strike": 450,
                "atm_iv": 0.15,
                "implied_daily_move_pct": 1.2,
                "atm_greeks": {"delta": 0.5, "gamma": 0.02},
                "vix_previous_close": 14.5,
                "vix_at_calculation": 15.2,
                "vix_change_pct": 4.83,
                "signals": [{"signal": 13.12}],
                "aggregate_gex": 1250000.0,
                "zero_gamma_level": 448.5,
                "gex_regime": "positive",
                "trading_allowed": True,
                "halt_reason": None
            }
        ]
        """

        url = f"{self.base_url}/roguetrader-signals/"

        response = requests.post(
            url,
            json=signals,
            headers={
                "Content-Type": "application/json",
                "EETC-API-Key": self.api_key,
            },
        )

        if response.status_code not in [200, 201]:
            response.raise_for_status()
