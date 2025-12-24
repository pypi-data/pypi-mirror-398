import requests
import os
from pprint import pprint
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import json
from time import sleep
import pandas as pd

### Define the URL and headers
### LIVE
# BASE_URL = "https://api-fxtrade.oanda.com"
# HEADERS = {  # Live API Key
#     "Authorization": f"Bearer"
#     + " e5dbaf9835cd17e9257d9eb23c8c465f"
#     + "-5e4fcb74691ea3bf76e6a8f87812297f",
#     "Content-Type": "application/json",
# }
# ACCT_NO = "001-003-13021835-004"

### Demo
BASE_URL = "https://api-fxpractice.oanda.com"
HEADERS = { # Demo api key
    "Authorization": f"Bearer "
    + "d4ab3135a03abc82184f57ee0138c1fb-"
    + "2241dd29b38206e85788ea8937b494ea",
    "Content-Type": "application/json",
}
ACCT_NO = "101-003-30292726-004"

MAX_RISK_PERCENTAGE = 0.01  # 1% of account value

INSTRUMENTS = {
    "AUD/CAD": "AUD_CAD",
    "AUD/CHF": "AUD_CHF",
    "AUD/HKD": "AUD_HKD",
    "AUD/JPY": "AUD_JPY",
    "AUD/NZD": "AUD_NZD",
    "AUD/SGD": "AUD_SGD",
    "AUD/USD": "AUD_USD",
    "Australia 200": "AU200_AUD",
    "Brent Crude Oil": "BCO_USD",
    "CAD/CHF": "CAD_CHF",
    "CAD/HKD": "CAD_HKD",
    "CAD/JPY": "CAD_JPY",
    "CAD/SGD": "CAD_SGD",
    "CHF/HKD": "CHF_HKD",
    "CHF/JPY": "CHF_JPY",
    "CHF/ZAR": "CHF_ZAR",
    "China A50": "CN50_USD",
    "Copper": "XCU_USD",
    "Corn": "CORN_USD",
    "EUR/AUD": "EUR_AUD",
    "EUR/CAD": "EUR_CAD",
    "EUR/CHF": "EUR_CHF",
    "EUR/CZK": "EUR_CZK",
    "EUR/DKK": "EUR_DKK",
    "EUR/GBP": "EUR_GBP",
    "EUR/HKD": "EUR_HKD",
    "EUR/HUF": "EUR_HUF",
    "EUR/JPY": "EUR_JPY",
    "EUR/NOK": "EUR_NOK",
    "EUR/NZD": "EUR_NZD",
    "EUR/PLN": "EUR_PLN",
    "EUR/SEK": "EUR_SEK",
    "EUR/SGD": "EUR_SGD",
    "EUR/TRY": "EUR_TRY",
    "EUR/USD": "EUR_USD",
    "EUR/ZAR": "EUR_ZAR",
    "Europe 50": "EU50_EUR",
    "France 40": "FR40_EUR",
    "GBP/AUD": "GBP_AUD",
    "GBP/CAD": "GBP_CAD",
    "GBP/CHF": "GBP_CHF",
    "GBP/HKD": "GBP_HKD",
    "GBP/JPY": "GBP_JPY",
    "GBP/NZD": "GBP_NZD",
    "GBP/PLN": "GBP_PLN",
    "GBP/SGD": "GBP_SGD",
    "GBP/USD": "GBP_USD",
    "GBP/ZAR": "GBP_ZAR",
    "Germany 30": "DE30_EUR",
    "Gold": "XAU_USD",
    "HKD/JPY": "HKD_JPY",
    "Hong Kong 33": "HK33_HKD",
    "Japan 225": "JP225_USD",
    "NZD/CAD": "NZD_CAD",
    "NZD/CHF": "NZD_CHF",
    "NZD/HKD": "NZD_HKD",
    "NZD/JPY": "NZD_JPY",
    "NZD/SGD": "NZD_SGD",
    "NZD/USD": "NZD_USD",
    "Natural Gas": "NATGAS_USD",
    "Netherlands 25": "NL25_EUR",
    "Palladium": "XPD_USD",
    "Platinum": "XPT_USD",
    "SGD/CHF": "SGD_CHF",
    "SGD/JPY": "SGD_JPY",
    "Silver": "XAG_USD",
    "Singapore 30": "SG30_SGD",
    "Soybeans": "SOYBN_USD",
    "Spain 35": "ESPIX_EUR",
    "Sugar": "SUGAR_USD",
    "Switzerland 20": "CH20_CHF",
    "TRY/JPY": "TRY_JPY",
    "UK 100": "UK100_GBP",
    "US Nas 100": "NAS100_USD",
    "US Russ 2000": "US2000_USD",
    "US SPX 500": "SPX500_USD",
    "US T-Bond": "USB30Y_USD",
    "US Wall St 30": "US30_USD",
    "USD/CAD": "USD_CAD",
    "USD/CHF": "USD_CHF",
    "USD/CNH": "USD_CNH",
    "USD/CZK": "USD_CZK",
    "USD/DKK": "USD_DKK",
    "USD/HKD": "USD_HKD",
    "USD/HUF": "USD_HUF",
    "USD/JPY": "USD_JPY",
    "USD/MXN": "USD_MXN",
    "USD/NOK": "USD_NOK",
    "USD/PLN": "USD_PLN",
    "USD/SEK": "USD_SEK",
    "USD/SGD": "USD_SGD",
    "USD/THB": "USD_THB",
    "USD/TRY": "USD_TRY",
    "USD/ZAR": "USD_ZAR",
    "West Texas Oil": "WTICO_USD",
    "Wheat": "WHEAT_USD",
    "ZAR/JPY": "ZAR_JPY",
}

### Account summary
def get_account_details():
    ACCT_SUMM = f"{BASE_URL}/v3/accounts/{ACCT_NO}/summary"
    response = requests.get(ACCT_SUMM, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()  # Parse JSON data
        return data
    else:
        print(f"Request failed with status code: {response.status_code}")


def get_current_balance():
    data = get_account_details()
    return float(data["account"]["balance"])


def get_accnt_currency():
    data = get_account_details()
    return str(data["account"]["currency"])


def get_all_current_running_positions():
    GET_TRADES = f"{BASE_URL}/v3/accounts/{ACCT_NO}/openPositions"
    response = requests.get(GET_TRADES, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Request failed with status code: {response.status_code}")


def get_all_current_running_trades():
    GET_TRADES = f"{BASE_URL}/v3/accounts/{ACCT_NO}/openTrades"
    response = requests.get(GET_TRADES, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Request failed with status code: {response.status_code}")


def get_all_pending_orders():
    GET_PENDING_ORDERS = f"{BASE_URL}/v3/accounts/{ACCT_NO}/pendingOrders"
    response = requests.get(GET_PENDING_ORDERS, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Request failed with status code: {response.status_code}")


def get_current_nav():
    return float(get_account_details()["account"]["NAV"])


### Dealing
def prevent_over_trading(instrument, signal_type):
    if signal_type == "SELL":
        signal_direction = "short"
    elif signal_type == "BUY":
        signal_direction = "long"
    else:
        raise ValueError("signal_type is invalid.")

    open_positions = get_all_current_running_positions()["positions"]
    for pos in open_positions:
        if (
            pos["instrument"] == instrument
            and "tradeIDs" in list(pos[signal_direction].keys())
            and len(pos[signal_direction]["tradeIDs"]) >= 7
        ):
            return 1
    return 0


def send_order(lots, instrument, signal_type, tp, sl, price=None):
    SEND_ORDER = f"{BASE_URL}/v3/accounts/{ACCT_NO}/orders"

    if not price:
        curr_price = get_curr_price(instrument)
    else:
        curr_price = price

    if instrument in [
        "XAU_USD", "BCO_USD", "CORN_USD", "NATGAS_USD", "XPD_USD", 
        "XPT_USD", "SOYBN_USD", "WTICO_USD", "WHEAT_USD"
        ] or instrument.endswith("JPY"):
        tp, sl, curr_price = round(tp, 3), round(sl, 3), round(curr_price, 3)
    else:
        tp, sl, curr_price = round(tp, 5), round(sl, 5), round(curr_price, 5)

    if str(signal_type).upper() == "SELL" or signal_type == -1:
        lots = -lots
        if not (tp < curr_price < sl):
            print("ERROR: Take profit should be less than stop loss for sell orders.")
            return 1

    if (str(signal_type).upper() == "BUY" or signal_type == 1) and not (
        tp > curr_price > sl
    ):
        print("ERROR: Take profit should be greater than stop loss for buy orders.")
        return 1

    if "_" not in instrument:
        instrument = str(instrument[:-3] + "_" + instrument[-3:]).upper()

    if str(instrument) in list(INSTRUMENTS.values()):
        data = {
            "order": {
                "units": lots,
                "instrument": instrument,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT",
                "takeProfitOnFill": {
                    "price": str(tp)
                },  # Specify the Take Profit details
                "stopLossOnFill": {"price": str(sl)},  # Specify the Stop Loss details
            }
        }

        if price:
            data["order"]["price"] = str(curr_price)
            data["order"]["type"] = "MARKET_IF_TOUCHED"
            data["order"]["timeInForce"] = "GTC"

        assert (
            "takeProfitOnFill" in data["order"]
        ), "TP not included in the order payload."
        assert (
            "stopLossOnFill" in data["order"]
        ), "SL not included in the order payload."

        response = requests.post(SEND_ORDER, headers=HEADERS, json=data)
        if response.status_code in [201]:
            print(
                f"Order {signal_type} {instrument} with tp {tp} and sl {sl} placed successfully."
            )
            return 0
        else:
            print(
                f"Request failed with status code: {response.status_code}, {response.json()}"
            )
            return 1

    print(f"ERROR: {instrument} is not a valid instrument.")
    return 1


def delete_old_pending_orders(hours_threshold=24):
    """
    Deletes all pending orders older than the specified threshold in hours.

    :param hours_threshold: The threshold in hours to determine old orders (default: 24 hours).
    """
    # Get all pending orders using your provided function
    pending_orders_data = get_all_pending_orders()

    if not pending_orders_data or "orders" not in pending_orders_data:
        print("No pending orders found or failed to retrieve orders.")
        return

    pending_orders = pending_orders_data["orders"]
    print(f"Found {len(pending_orders)} pending orders. Checking for old orders...")

    # Current time in UTC
    current_time_utc = datetime.now(pytz.utc)

    # Threshold datetime
    time_threshold = current_time_utc - timedelta(hours=hours_threshold)

    # Loop through pending orders and delete old ones
    deletion_count = 0
    DELETE_ORDER_URL = f"{BASE_URL}/v3/accounts/{ACCT_NO}/orders"
    for order in pending_orders:
        if order["type"] != "STOP_LOSS" and order["type"] != "TAKE_PROFIT":
            try:
                # Fix createTime by truncating fractional seconds to 6 digits
                truncated_time = order["createTime"].split(".")[0] + "Z"
                create_time = datetime.fromisoformat(
                    truncated_time.replace("Z", "+00:00")
                )

                # Check if the order is older than the threshold
                if create_time < time_threshold:
                    order_id = order["id"]
                    # Attempt to delete the order
                    delete_response = requests.put(
                        f"{DELETE_ORDER_URL}/{order_id}/cancel", headers=HEADERS
                    )
                    if delete_response.status_code == 200:
                        print(
                            f"Deleted pending order {order_id} created at {create_time}."
                        )
                        deletion_count += 1
                    else:
                        print(
                            f"Failed to delete order {order_id}: {delete_response.status_code}, {delete_response.text}"
                        )
                else:
                    print(
                        f"Order {order['id']} is not old enough to be deleted (created at {create_time})."
                    )
            except Exception as e:
                print(f"Error processing order {order.get('id', 'unknown')}: {e}")

    return deletion_count


def close_trades(instrument, type):
    if "_" not in instrument:
        instrument = str(instrument[:3] + "_" + instrument[3:])
    CLOSE_TRADES = f"{BASE_URL}/v3/accounts/{ACCT_NO}/positions/{instrument}/close"

    data = {}
    if str(type).upper() == "SELL" or type == -1:
        data["shortUnits"] = "ALL"
    elif str(type).upper() == "BUY" or type == 1:
        data["longUnits"] = "ALL"
    else:
        return "Invalid type"

    response = requests.put(CLOSE_TRADES, headers=HEADERS, json=data)

    if response.status_code == 200:
        print(f"All {type} trades closed successfully for {instrument}.")
    else:
        print(
            f"Request failed with status code {response.status_code}: {response.json()['errorCode']}"
        )


def close_all_trades_in_accnt():
    open_trades = get_all_current_running_positions()
    for trade in open_trades["positions"]:
        if "long" in trade and abs(float(trade["long"]["units"])) > 0:
            close_trades(trade["instrument"], "BUY")
        if "short" in trade and abs(float(trade["short"]["units"])) > 0:
            close_trades(trade["instrument"], "SELL")
    return


def delete_all_pending_orders():
    """
    Deletes all pending orders in account.
    """
    # Get all pending orders using your provided function
    pending_orders_data = get_all_pending_orders()

    if not pending_orders_data or "orders" not in pending_orders_data:
        print("No pending orders found or failed to retrieve orders.")
        return

    pending_orders = pending_orders_data["orders"]
    print(f"Found {len(pending_orders)} pending orders.")

    # Loop through pending orders and delete old ones
    deletion_count = 0
    DELETE_ORDER_URL = f"{BASE_URL}/v3/accounts/{ACCT_NO}/orders"
    for order in pending_orders:
        try:
            order_id = order["id"]
            # Attempt to delete the order
            delete_response = requests.put(
                f"{DELETE_ORDER_URL}/{order_id}/cancel", headers=HEADERS
            )
            if delete_response.status_code == 200:
                print(f"Deleted pending order {order_id}.")
                deletion_count += 1
            else:
                print(
                    f"Failed to delete order {order_id}: {delete_response.status_code}, {delete_response.text}"
                )
        except Exception as e:
            print(f"Error processing order {order.get('id', 'unknown')}: {e}")

    return deletion_count


def kill_switch():
    close_all_trades_in_accnt()
    delete_all_pending_orders()
    return


def get_curr_price(instrument):
    """
    Fetches the latest mid price for a given instrument.

    :param instrument: The currency pair or instrument (e.g., "EUR_USD").
    :return: The mid price (average of bid and ask prices) or None if the request fails.
    """
    # Define the endpoint and parameters
    endpoint = f"{BASE_URL}/v3/accounts/{ACCT_NO}/pricing"
    params = {"instruments": instrument}  # Specify the instrument to fetch pricing for

    try:
        # Send the GET request to the OANDA API
        response = requests.get(endpoint, headers=HEADERS, params=params)
        response.raise_for_status()  # Raise an error for HTTP codes >= 400

        # Parse the JSON response
        data = response.json()
        for price in data["prices"]:
            if price["instrument"] == instrument:
                # Extract the bid and ask prices
                bid = float(price["bids"][0]["price"])
                ask = float(price["asks"][0]["price"])
                # Calculate the mid price
                mid_price = (bid + ask) / 2

                if instrument in ["USD_JPY", "XAU_USD"]:
                    mid_price = round(mid_price, 3)
                else:
                    mid_price = round(mid_price, 5)
                return mid_price

        # If the instrument is not found in the response
        raise ValueError(f"Instrument {instrument} not found in the response.")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching mid price for {instrument}: {e}")

    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response structure for {instrument}: {e}")


def trigger_kill_switch():
    check_and_store_highest_balance()
    running_nav = get_current_nav()
    sleep(0.1)  # To ensure the highest balance is stored before fetching it

    max_possible_loss = 0.7 * get_highest_balance()
    bag_profits = 1.05 * get_current_balance()

    if running_nav <= max_possible_loss:
        kill_switch()
        return 1
    if running_nav >= bag_profits:
        kill_switch()
        return -1
    return 0


def delete_invalid_trades():
    """
    Deletes all active trades that do not have either a take profit (TP) or stop loss (SL) level.

    :return: A count of trades deleted.
    """
    open_trades = get_all_current_running_trades()["trades"]
    curr_balance = get_current_balance()

    deleted = 0
    for trade in open_trades:
        if (
            "takeProfitOrder" not in trade
            and float(trade["unrealizedPL"]) > MAX_RISK_PERCENTAGE * curr_balance
        ) or (
            float(trade["unrealizedPL"]) <= (-1 * MAX_RISK_PERCENTAGE * curr_balance)
        ):
            trade_id = trade["id"]
            endpoint = f"{BASE_URL}/v3/accounts/{ACCT_NO}/trades/{trade_id}/close"
            response = requests.put(endpoint, headers=HEADERS)
            if response.status_code == 200:
                print(f"Deleted trade {trade_id} with missing TP/SL.")
                deleted += 1
            else:
                print(f"Failed to delete trade {trade_id}: {response.status_code}")
    return deleted


### Helper functions
def get_all_tradable_instruments():
    """
    Fetches all tradable instruments for the account.

    :return: A list of tradable instruments (names and details) or None if the request fails.
    """
    endpoint = f"{BASE_URL}/v3/accounts/{ACCT_NO}/instruments"

    try:
        # Send the GET request to the OANDA API
        response = requests.get(endpoint, headers=HEADERS)
        response.raise_for_status()  # Raise an error for HTTP codes >= 400

        # Parse the response
        data = response.json()
        instruments = data.get("instruments", [])
        return {
            instrument["displayName"]: instrument["name"] for instrument in instruments
        }

    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching tradable instruments: {e}")
        return None


def get_conversion_rate(instrument):
    # Define base and counter currencies
    _, counter_currency = instrument.split("_")
    accnt_currency = get_accnt_currency()
    if accnt_currency == counter_currency:
        return 1.0

    resp = requests.get(
        f"https://api.frankfurter.dev/v1/latest?base={counter_currency}&symbols={accnt_currency}",
    ).json()
    rates = resp.get("rates", {})
    if accnt_currency in rates:
        return float(rates[accnt_currency])
    raise RuntimeError(f"Rate not found for {instrument}")


def get_highest_balance():
    """
    Retrieves the highest account balance from local file.
    """
    if os.path.exists("highest_balance.json"):
        with open("highest_balance.json", "r") as file:
            data = json.load(file)
            return float(data["highest_balance"])
    return 0


def check_and_store_highest_balance():
    """
    Stores the highest account balance in a file.
    """
    current_balance = get_current_balance()
    highest_balance = get_highest_balance()

    # Store the highest balance
    if current_balance > highest_balance:
        with open("highest_balance.json", "w") as file:
            json.dump({"highest_balance": current_balance}, file)
        print(f"New highest balance stored: {current_balance}")

    return


def calculate_trade_units(sl_price, instrument, price=None):
    """
    Calculates the number of units to trade based on risk management criteria.

    :param current_price: The current price of the instrument.
    :param curr_account_value: The current account value in SGD.
    :param sl_price: The stop-loss price.
    :param instrument: The instrument to trade (e.g., "EUR_USD").
    :return: The number of units to trade (integer).
    """
    if not price:
        current_price = get_curr_price(instrument)
    else:
        current_price = price
    # print(current_price)

    curr_account_value = get_current_balance()
    # curr_account_value = get_highest_balance()
    # print(curr_account_value)

    # Maximum risk allowed
    max_risk = curr_account_value * MAX_RISK_PERCENTAGE
    # print(max_risk)

    # Calculate the pip value or price difference per unit
    price_difference_per_unit = abs(current_price - sl_price)
    # print(price_difference_per_unit)

    # Get the conversion rate for the instrument currency to account currency
    conversion_rate = get_conversion_rate(instrument)
    # print(conversion_rate)

    # Calculate the value of the potential loss in Account Currency for one unit
    potential_loss_per_unit = price_difference_per_unit * conversion_rate
    # print(potential_loss_per_unit)

    # Calculate the maximum number of units that can be traded within the risk limit
    if potential_loss_per_unit > 0:
        units = int(max_risk / potential_loss_per_unit)
    else:
        raise ValueError("Invalid stop-loss price or conversion rate.")

    return units


def get_oanda_ohlc(instrument, timeframe):
    """
    Fetch OHLC candlestick data for the given instrument and timeframe from OANDA,
    including volume and, if available, VWAP. Returns a pandas DataFrame sorted
    by time in ascending order.

    Parameters:
        instrument (str): The instrument symbol (e.g. "EUR_USD").
        timeframe (str): Supported timeframes: "1min", "5min", "15min", "1h", "4h", "1d", "1w".

    Returns:
        pandas.DataFrame: DataFrame with columns: time, open, high, low, close, volume, vwap.
    """
    # Map input timeframe to OANDA granularity codes.
    granularity_mapping = {
        "1min": "M1",
        "5min": "M5",
        "15min": "M15",
        "30min": "M30",
        "1h": "H1",
        "4h": "H4",
        "1d": "D",
        "1w": "W",
    }

    if timeframe not in granularity_mapping:
        raise ValueError(
            f"Unsupported timeframe '{timeframe}'. Supported timeframes are: {list(granularity_mapping.keys())}"
        )

    granularity = granularity_mapping[timeframe]

    # Build the endpoint URL for candlestick data.
    url = f"{BASE_URL}/v3/instruments/{instrument}/candles"

    # Define query parameters; adjust 'count' as needed.
    params = {
        "granularity": granularity,
        "price": "B",  # using mid prices for OHLC values
        "count": 100,  # number of candles to retrieve
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print(f"Request failed with status code: {response.status_code}")
        return None

    data = response.json()
    candles = data.get("candles", [])

    # Process each candle and collect the data.
    records = []
    for candle in candles:
        record = {
            "date": candle["time"],
            "open": float(candle["bid"]["o"]),
            "high": float(candle["bid"]["h"]),
            "low": float(candle["bid"]["l"]),
            "close": float(candle["bid"]["c"]),
            "volume": candle.get("volume", None),  # volume is provided by OANDA
        }
        records.append(record)

    # Create a DataFrame from the records.
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["mean"] = (df["high"] + df["low"] + df["close"]) / 3

    # Sort DataFrame by time in ascending order.
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


### Func callings
# kill_switch()
# sleep(3)
# print(get_current_balance())