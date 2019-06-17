import datetime
import logging.config
import math
import os

from binance.client import Client as BinanceClient

import api_keys

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), 'config/logging.cfg'))
log = logging.getLogger('ROOT')

ALL_QUOTE_CURRENCIES = ['BTC', 'BNB', 'ETH', 'XRP', 'USDT', 'TUSD', 'USDS', 'PAX', 'USDC']
QUOTE_GROUPS = {
    'BTC': ['BTC'],
    'BNB': ['BNB'],
    'ALTS': ['ETH', 'XRP'],
    'USD': ['USDT', 'TUSD', 'PAX', 'USDS', 'USDC']
}


def get_pair(symbol: str)->tuple:
    """
    Returns pair with base and quote currency

    Example: get_pair('BTCUSDT') = ('BTC','USDT')
    """
    if symbol[-4:] in ALL_QUOTE_CURRENCIES:
        return symbol[:-4], symbol[-4:]
    return symbol[:-3], symbol[-3:]


def get_pair_dict(symbol: str)->dict:
    """
    Returns dictionary with base and quote currency

    Example: get_pair_dict('BTCUSDT') = {'base': 'BTC', 'quote': 'USDT'}
    """
    return {"base": get_base_currency(symbol), "quote": get_quote_currency(symbol)}


def get_base_currency(symbol: str)->str:
    """
    Returns base currency of pair

    Example: get_base_currency('BTCUSDT') = 'BTC'
    """
    return get_pair(symbol)[0]


def get_quote_currency(symbol)->str:
    """
    Returns quote currency of pair

    Example: get_quote_currency('BTCUSDT') = 'USDT'
    """
    return get_pair(symbol)[1]


class OrderStatus:
    WAITING = 'Waiting'
    PLACED = 'Placed'
    CANCELED = 'Canceled'
    FILLED = 'Filled'
    FAILED = 'Failed'


class Side:
    BUY = 'BUY'
    SELL = 'SELL'


def get_precision_by_symbol_dict()->dict:
    """
    Returns dictionary: key - symbol, value - object that contains information
    about allowed step size, precision of price and quantity

    Example: get_precision_by_symbol_dict() = {
    'BTCUSDT':
    {'price_step':0.01, 'price_precision':2, 'quantity_step':0.0001, 'quantity_precision': 4},
    'TRXBTC':
    {'price_step':0.00000001, 'price_precision':8, 'quantity_step':1.0, 'quantity_precision': 0},
    ...
    }
    """
    res = {}
    for symbol_info in binance.get_exchange_info()['symbols']:
        precision = {}
        for symbol_filter in symbol_info['filters']:
            if symbol_filter['filterType'] == 'PRICE_FILTER':
                precision['price_step'] = symbol_filter['tickSize']
                precision['price_precision'] = -round(math.log10(float(precision['price_step'])))
            if symbol_filter['filterType'] == 'LOT_SIZE':
                precision['quantity_step'] = symbol_filter['stepSize']
                precision['quantity_precision'] = -round(math.log10(float(precision['quantity_step'])))
        res[symbol_info['symbol']] = precision
    return res


def get_tickers_by_quote_dict()->dict:
    """
    Returns dictionary: key - some currency, value - list of binance tickers with key as a quote currency

    Example: get_tickers_by_quote_dict() = {
    'BTC': [{'symbol': 'TRXBTC', 'lastPrice': '0.00000350', ...}, {'symbol': 'ETHBTC', 'lastPrice': '0.032', ...}]
    'USDT': [{'symbol': 'BTCUSDT', 'lastPrice': '20151.05', ...}, {'symbol': 'XLMUSDT', 'lastPrice': '0.277', ...}]
    ...
    }
    """
    tickers = {q: [] for q in ALL_QUOTE_CURRENCIES}
    for ticker in binance.get_ticker():
        ticker['base'] = get_base_currency(ticker['symbol'])
        ticker['quote'] = get_quote_currency(ticker['symbol'])
        tickers[ticker['quote']].append(ticker)
    return tickers


def get_current_time()->int:
    """
    Returns current timestamp in milliseconds
    """
    return int(datetime.datetime.now().timestamp() * 1000)


"""Global Binance client instance"""
binance = BinanceClient(api_keys.get_public(), api_keys.get_secret())

"""Global information about step sizes and precision"""
precision_by_symbol = get_precision_by_symbol_dict()
