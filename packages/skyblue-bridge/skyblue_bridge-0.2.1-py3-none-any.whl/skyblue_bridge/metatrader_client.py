from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

import requests
import pandas as pd


class MTClient:
    """Python client for the SkyBlue MT4/5 bridge service."""

    def __init__(
        self,
        api_key: str,
        server_url: str = "https://bridge.skybluefin.tech",
        timeout: int = 10,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.headers = {"Content-Type": "application/json", "X-API-Key": api_key}
        self.timeout = timeout

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.server_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url, json=data, headers=self.headers, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(f"Request timeout after {self.timeout} seconds") from exc
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"Failed to connect to server at {self.server_url}"
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"HTTP error {response.status_code}: {response.text}"
            ) from exc
        except Exception as exc:  # pragma: no cover - fallthrough
            raise RuntimeError(f"Request failed: {exc}") from exc

    # ==================== SERVER STATUS ====================

    def get_server_status(self) -> Dict[str, Any]:
        return self._make_request("GET", "/")

    def is_connected(self) -> bool:
        try:
            self.get_server_status()
            return True
        except Exception:
            return False

    # ==================== TRADING ORDERS ====================

    def _send_order(
        self,
        symbol: str,
        side: str,
        lots: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        order_id = f"{side.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        data: Dict[str, Any] = {
            "id": order_id,
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "lots": lots,
        }

        if sl is not None:
            data["sl"] = sl
        if tp is not None:
            data["tp"] = tp
        if order_type.upper() in {"LIMIT", "STOP"} and price is not None:
            data["price"] = price
        if comment is not None:
            data["comment"] = comment
        if expiration is not None:
            if isinstance(expiration, datetime):
                data["expiration"] = int(expiration.timestamp())
            else:
                data["expiration"] = int(expiration)

        return self._make_request("POST", "/v1/order", data)

    def buy_market(
        self,
        symbol: str,
        lots: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._send_order(
            symbol, "BUY", lots, "MARKET", sl=sl, tp=tp, comment=comment
        )

    def sell_market(
        self,
        symbol: str,
        lots: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._send_order(
            symbol, "SELL", lots, "MARKET", sl=sl, tp=tp, comment=comment
        )

    def buy_limit(
        self,
        symbol: str,
        lots: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        return self._send_order(
            symbol,
            "BUY",
            lots,
            "LIMIT",
            price,
            sl,
            tp,
            comment=comment,
            expiration=expiration,
        )

    def sell_limit(
        self,
        symbol: str,
        lots: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        return self._send_order(
            symbol,
            "SELL",
            lots,
            "LIMIT",
            price,
            sl,
            tp,
            comment=comment,
            expiration=expiration,
        )

    def buy_stop(
        self,
        symbol: str,
        lots: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        return self._send_order(
            symbol,
            "BUY",
            lots,
            "STOP",
            price,
            sl,
            tp,
            comment=comment,
            expiration=expiration,
        )

    def sell_stop(
        self,
        symbol: str,
        lots: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        return self._send_order(
            symbol,
            "SELL",
            lots,
            "STOP",
            price,
            sl,
            tp,
            comment=comment,
            expiration=expiration,
        )

    def buy_conditional_entry(
        self,
        symbol: str,
        lots: float,
        price: float | None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        """Buy if touched order"""
        current_price = self.get_mid(symbol)
        if price is not None and price < current_price:
            return self.buy_limit(
                symbol,
                lots,
                price,
                sl=sl,
                tp=tp,
                comment=comment,
                expiration=expiration,
            )
        if price is not None and price > current_price:
            return self.buy_stop(
                symbol,
                lots,
                price,
                sl=sl,
                tp=tp,
                comment=comment,
                expiration=expiration,
            )
        return self.buy_market(symbol, lots, sl, tp, comment=comment)

    def sell_conditional_entry(
        self,
        symbol: str,
        lots: float,
        price: float | None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: Optional[str] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        """Sell if touched order"""
        current_price = self.get_mid(symbol)
        if price is not None and price > current_price:
            return self.sell_limit(
                symbol,
                lots,
                price,
                sl=sl,
                tp=tp,
                comment=comment,
                expiration=expiration,
            )
        if price is not None and price < current_price:
            return self.sell_stop(
                symbol,
                lots,
                price,
                sl=sl,
                tp=tp,
                comment=comment,
                expiration=expiration,
            )
        return self.sell_market(symbol, lots, sl, tp, comment=comment)

    # ==================== MARKET DATA ====================

    def _get_price(self, symbol: str) -> Dict[str, Any]:
        data = {"symbol": symbol.upper(), "type": "MID"}
        return self._make_request("POST", "/v1/data", data)

    def get_bid(self, symbol: str) -> float:
        return float(self._get_price(symbol)["bid"])

    def get_ask(self, symbol: str) -> float:
        return float(self._get_price(symbol)["ask"])

    def get_mid(self, symbol: str) -> float:
        return float(self._get_price(symbol)["mid"])

    def get_spread(self, symbol: str) -> float:
        prices = self._get_price(symbol)
        return float(prices["ask"] - prices["bid"])

    def get_symbol_specs(self, symbol: str) -> Dict[str, Any]:
        """Get symbol specifications including contract size, digits, spreads, etc."""
        data = {"symbol": symbol.upper()}
        return self._make_request("POST", "/v1/symbol_specs", data)

    def get_ohlc(
        self,
        symbol: str,
        timeframe: str = "1h",
        count: Optional[int] = None,
        start_date: Optional[Union[str, datetime, int]] = None,
        as_df: bool = False,
    ) -> Union[Dict[str, Any], "pd.DataFrame"]:
        """Fetch OHLC data by either explicit count or start date."""
        if (count is None and start_date is None) or (
            count is not None and start_date is not None
        ):
            raise ValueError("Provide exactly one of 'count' or 'start_date'")

        data: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
        }

        if count is not None:
            if count <= 0:
                raise ValueError("count must be positive")
            if count > 5000:
                raise ValueError("count cannot exceed 5000")
            data["count"] = count

        if start_date is not None:
            if isinstance(start_date, datetime):
                data["start_date"] = start_date.isoformat()
            else:
                data["start_date"] = str(start_date)

        response = self._make_request("POST", "/v1/ohlc", data)

        if as_df:
            if pd is None:
                raise ImportError(
                    "pandas is required for as_df=True (pip install skyblue-bridge[pandas])"
                )
            frame = pd.DataFrame(response.get("data", []))
            if not frame.empty:
                frame["time"] = pd.to_datetime(frame["time"], unit="s")
                frame.set_index("time", inplace=True)
                frame.sort_index(ascending=True, inplace=True)
            return frame

        return response

    # ==================== ACCOUNT INFO ====================

    def _get_account(self) -> Dict[str, Any]:
        return self._make_request("GET", "/v1/account")

    def get_balance(self) -> float:
        return float(self._get_account().get("balance", 0.0))

    def get_equity(self) -> float:
        return float(self._get_account().get("equity", 0.0))

    def get_floating_pnl(self) -> float:
        account = self._get_account()
        return float(account.get("equity", 0.0) - account.get("balance", 0.0))

    # ==================== RISK MANAGEMENT ====================

    def kill_switch(self) -> Dict[str, Any]:
        return self._make_request("POST", "/v1/kill_switch", {})

    def close_symbol(self, symbol: str) -> Dict[str, Any]:
        return self._make_request(
            "POST", "/v1/close_symbol", {"symbol": symbol.upper()}
        )

    def list_positions(self) -> Dict[str, Any]:
        return self._make_request("GET", "/v1/positions")

    def close_ticket(self, ticket: int) -> Dict[str, Any]:
        return self._make_request("POST", "/v1/close_ticket", {"ticket": int(ticket)})

    def close_magic(self, magic: int) -> Dict[str, Any]:
        return self._make_request("POST", "/v1/close_magic", {"magic": int(magic)})

    def get_order_details(self, ticket: int) -> Dict[str, Any]:
        return self._make_request("POST", "/v1/order_details", {"ticket": int(ticket)})

    def modify_order(
        self,
        ticket: int,
        *,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        expiration: Optional[Union[int, datetime]] = None,
    ) -> Dict[str, Any]:
        if price is None and sl is None and tp is None and expiration is None:
            raise ValueError("Provide at least one of price, sl, tp, or expiration")

        data: Dict[str, Any] = {"ticket": int(ticket)}

        if price is not None:
            if price <= 0:
                raise ValueError("price must be positive")
            data["price"] = float(price)
        if sl is not None:
            data["sl"] = float(sl)
        if tp is not None:
            data["tp"] = float(tp)
        if expiration is not None:
            if isinstance(expiration, datetime):
                data["expiration"] = int(expiration.timestamp())
            else:
                data["expiration"] = int(expiration)

        return self._make_request("POST", "/v1/modify_order", data)

    def get_history(
        self, start_date: Optional[Union[datetime, str, int]] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if start_date is not None:
            if isinstance(start_date, datetime):
                data["start_date"] = start_date.isoformat()
            else:
                data["start_date"] = str(start_date)
        return self._make_request("POST", "/v1/history", data or {})

    # ==================== UTILITY METHODS ====================

    def get_conversion_rate(self, symbol: str, accnt_currency: str = "USD") -> float:
        counter_currency = symbol[3:]
        if accnt_currency == counter_currency or symbol in {"GOLD", "SILVER"}:
            return 1.0

        resp = requests.get(
            f"https://api.frankfurter.dev/v1/latest?base={counter_currency}&symbols={accnt_currency}",
            timeout=self.timeout,
        ).json()
        rates = resp.get("rates", {})
        if accnt_currency in rates:
            return float(rates[accnt_currency])
        raise RuntimeError(f"Rate not found for {symbol}")
