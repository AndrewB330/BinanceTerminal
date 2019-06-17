import json
from decimal import Decimal

from binance.exceptions import BinanceAPIException

from utils import *

CONTEXT_DEPENDENT_FUNCTIONS = [
    'HighPrice',
    'LowPrice',
    'AvgVol',
    'AvgLowPrice',
    'AvgHighPrice',
    'AvgPrice',
    'OrderPrice',
    'OrderTime',
    'CurrentTime'
]


def Market() -> Decimal:
    """
    Returns constant that means market price
    """
    return Decimal(0)  # todo: WARNING! If price function returns Decimal(0) it means that order is Market


def D(number: str) -> Decimal:
    """
    Transforms string representation of the number into Decimal
    """
    return Decimal(number)


def Seconds(n: int) -> int:
    """
    Returns number of milliseconds in n seconds
    """
    return 1000 * n


def Minutes(n: int) -> int:
    """
    Returns number of milliseconds in n minutes
    """
    return Seconds(60) * n


def Hours(n: int) -> int:
    """
    Returns number of milliseconds in n hours
    """
    return Minutes(60) * n


def CurrentTime() -> int:
    """
    Returns current timestamp in milliseconds
    """
    return get_current_time()


def replace_context_dependent_functions(expression: str):
    """
    Add "self." to all function calls that requires order context (e.g. symbol, price, time, side ...)
    """
    for function_name in CONTEXT_DEPENDENT_FUNCTIONS:
        expression = expression.replace(function_name, 'self.' + function_name)
    return expression


def get_current_price(symbol: str) -> Decimal:
    """
    Returns last price of a given symbol
    """
    return Decimal(binance.get_ticker(symbol=symbol)['lastPrice'])


class Order:
    def HighPrice(self) -> Decimal:
        """
        Returns the highest price since placing an order
        """
        return self.high_price

    def LowPrice(self) -> Decimal:
        """
        Returns the lowest price since placing an order
        """
        return self.low_price

    def AvgHigh(self, interval: str, number_of_bars: int) -> Decimal:
        """
        Returns average of high price over last 'number_of_bars' bars on chart with 'interval' time scale
        """
        bars = self.get_kline_cache(interval)[-number_of_bars:]
        return sum(map(lambda bar: Decimal(bar[2]), bars)) / len(bars)

    def AvgLow(self, interval: str, number_of_bars: int) -> Decimal:
        """
        Returns average of low price over last 'number_of_bars' bars on chart with 'interval' time scale
        """
        bars = self.get_kline_cache(interval)[-number_of_bars:]
        return sum(map(lambda bar: Decimal(bar[3]), bars)) / len(bars)

    def AvgPrice(self, interval: str, number_of_bars: int) -> Decimal:
        """
        Returns average price over last 'number_of_bars' bars on chart with 'interval' time scale
        """
        return (self.AvgHigh(interval, number_of_bars) + self.AvgLow(interval, number_of_bars)) / 2

    def PlacedPrice(self) -> Decimal:
        """
        Returns price of placed order. Works only if order has status PLACED
        """
        # todo: raise exception when not PLACED
        return self.placed_order_price

    def PlacedTime(self) -> int:
        """
        Returns time when order was placed. Works only if order has status PLACED
        """
        # todo: raise exception when not PLACED
        return self.placed_order_time

    def __init__(self, json_obj: dict):
        self._id = json_obj.get('_id', None)
        self.time = json_obj.get('time', get_current_time())
        self.symbol = json_obj['symbol']
        self.side = json_obj['side']
        self.status = json_obj.get('status', OrderStatus.WAITING)

        self.price = json_obj['price']
        self.price_formatted = replace_context_dependent_functions(self.price)
        self.price_func = lambda: eval(self.price_formatted)

        self.quantity = json_obj['quantity']
        self.quantity_formatted = replace_context_dependent_functions(self.quantity)
        self.quantity_func = lambda: eval(self.quantity_formatted)

        self.place_trigger = json_obj.get('place_trigger', 'True')
        self.place_trigger_formatted = replace_context_dependent_functions(self.place_trigger)
        self.place_trigger_func = lambda: eval(self.place_trigger_formatted)

        self.reset_trigger = json_obj.get('reset_trigger', 'False')
        self.reset_trigger_formatted = replace_context_dependent_functions(self.reset_trigger)
        self.reset_trigger_func = lambda: eval(self.reset_trigger_formatted)

        self.cancel_trigger = json_obj.get('cancel_trigger', 'False')
        self.cancel_trigger_formatted = replace_context_dependent_functions(self.cancel_trigger)
        self.cancel_trigger_func = lambda: eval(self.cancel_trigger_formatted)

        self.order_description = json_obj.get('order_description', None)
        self.last_update = json_obj.get('last_update', self.time)

        if 'high_price' not in json_obj:
            self.high_price = get_current_price(self.symbol)
        else:
            self.high_price = Decimal(json_obj.get('high_price'))

        self.low_price = Decimal(json_obj.get('low_price', self.high_price))

        self.placed_order_price = Decimal(json_obj.get('placed_order_price', 0))
        self.placed_order_id = json_obj.get('placed_order_id', None)
        self.placed_order_time = json_obj.get('placed_order_time', None)

        self.cancel_time = json_obj.get('cancel_time', None)

        self.cached_klines = {}

    def get_kline_cache(self, interval):
        if interval not in self.cached_klines:
            self.cached_klines[interval] = binance.get_klines(symbol=self.symbol, interval=interval)
        return self.cached_klines[interval]

    def is_active(self) -> bool:
        return self.status in [OrderStatus.WAITING, OrderStatus.PLACED]

    def cancel(self):
        """
        Cancel this order. If it is already placed on binance cancel it too.
        """
        if not self.is_active():
            return  # todo: raise an exception, trying to cancel inactive order
        if self.status == OrderStatus.PLACED:
            response = binance.cancel_order(symbol=self.symbol, orderId=self.placed_order_id)
            if response['orderId'] == self.placed_order_id and response['status'] == 'CANCELED':
                pass
            else:
                pass  # todo: error???
        self.status = OrderStatus.CANCELED
        self.cancel_time = get_current_time()

    def place(self):
        """
        Place this order. If it is already placed on binance cancel it too.
        """
        if self.status != OrderStatus.WAITING:
            return  # todo: raise an exception, trying to place inactive or already placed order

        price = self.price_func()  # compute price depending on current state of order
        quantity = self.quantity_func()  # compute quantity depending on current state of order

        if price == Market():
            quantity = quantity.quantize(Decimal(precision_by_symbol[self.symbol]['quantity_step']))

            response = binance.order_market(
                symbol=self.symbol,
                side=self.side,
                quantity=quantity
            )
        else:
            price = price.quantize(Decimal(precision_by_symbol[self.symbol]['price_step']))
            quantity = quantity.quantize(Decimal(precision_by_symbol[self.symbol]['quantity_step']))

            response = binance.order_limit(
                symbol=self.symbol,
                side=self.side,
                quantity=quantity,
                price=price
            )
        log.info(json.dumps(response))
        self.placed_order_id = response['orderId']
        self.placed_order_price = price
        self.placed_order_time = response['transactTime']
        self.status = OrderStatus.PLACED

    def reset(self):
        """
        Reset this order. Reset means to cancel order if it is already placed, and move to WAITING state again
        """
        response = binance.cancel_order(symbol=self.symbol, orderId=self.placed_order_id)
        if response['orderId'] == self.placed_order_id and response['status'] == 'CANCELED':
            self.status = OrderStatus.WAITING
        else:
            pass  # todo: error???

    def update_high_low_price(self):
        """
        Updates high and low price since the time that order was created
        """
        for kline in self.get_kline_cache('1m'):
            if kline[6] > self.time:
                self.high_price = max(self.high_price, D(kline[2]))
                self.low_price = min(self.low_price, D(kline[3]))
        self.last_update = get_current_time()

    def check_order(self):
        if self.status != OrderStatus.PLACED:
            return  # todo: raise an exception?
        order = binance.get_order(symbol=self.symbol, orderId=self.placed_order_id)
        if order['status'] in ['FILLED', 'PARTIALLY_FILLED']:
            self.status = OrderStatus.FILLED
        if order['status'] in ['CANCELED', 'REJECTED', 'EXPIRED']:
            try:
                self.cancel()
            except BinanceAPIException as e:
                if e.code != -2011:  # -2011 CANCEL_REJECTED, order was canceled from binance site
                    raise e

    def update(self):
        self.cached_klines = {}
        try:
            self.update_high_low_price()

            if self.status == OrderStatus.PLACED:
                self.check_order()

            if self.cancel_trigger_func():
                log.info('Cancel trigger. Symbol: %s, order: %s', self.symbol, str(self._id))
                self.cancel()
            if self.status == OrderStatus.WAITING and self.place_trigger_func():
                log.info('Place trigger. Symbol: %s, order: %s', self.symbol, str(self._id))
                self.place()
            if self.status == OrderStatus.PLACED and self.reset_trigger_func():
                log.info('Reset trigger. Symbol: %s, order: %s', self.symbol, str(self._id))
                self.reset()
        except BinanceAPIException as e:
            log.info('Failed. Symbol: %s, order: %s', self.symbol, str(self._id))
            log.error(e.code, e.message)
            self.status = OrderStatus.FAILED  # todo: work with exceptions

    def to_json(self):
        """
        Returns json representation of the order. Use it whe you want to insert order in MongoDB
        """
        return {
            "time": self.time,
            "symbol": self.symbol,
            "side": self.side,
            "status": self.status,
            "price": self.price,
            "quantity": self.quantity,
            "place_trigger": self.place_trigger,
            "reset_trigger": self.reset_trigger,
            "cancel_trigger": self.cancel_trigger,
            "order_description": self.order_description,
            "last_update": self.last_update,
            "high_price": str(self.high_price),
            "low_price": str(self.low_price),
            "placed_order_price": str(self.placed_order_price),
            "placed_order_time": self.placed_order_time,
            "placed_order_id": self.placed_order_id,
            "cancel_time": self.cancel_time
        }


# todo: side type
def create_limit(symbol: str, side: str, price: Decimal, quantity: Decimal) -> Order:
    """
    Creates standard limit order
    """
    return Order({
        "symbol": symbol,
        "side": side,
        "price": 'D(\'{}\')'.format(str(price)),
        "quantity": 'D(\'{}\')'.format(str(quantity)),
        "order_description": "[Limit] {} {} {}, price: {} {}"
            .format(side.lower(), quantity, get_base_currency(symbol), price, get_quote_currency(symbol))
    })


# todo: side type
def create_market_stop(symbol: str, side: str, stop_price: Decimal, quantity: Decimal) -> Order:
    """
    Creates market stop loss order. Execute order by market price when
    price rises above (for BUY) or drops below (for SELL) 'stop_price'
    """
    if side == Side.SELL:
        return Order({
            "symbol": symbol,
            "side": Side.SELL,
            "price": "Market()",
            "quantity": "D('{}')".format(quantity),
            "place_trigger": "LowPrice() < D('{}')".format(stop_price),
            "order_description":
                "[Stop loss] sell {} {} if lowest price drops below {} {}"
                    .format(quantity, get_base_currency(symbol), stop_price, get_quote_currency(symbol))
        })
    return Order({
        "symbol": symbol,
        "side": Side.BUY,
        "price": "Market()",
        "quantity": "D('{}')".format(quantity),
        "place_trigger": "HighPrice() > D('{}')".format(stop_price),
        "order_description":
            "[Stop loss] buy {} {} if highest price rises above {} {}"
                .format(quantity, get_base_currency(symbol), stop_price, get_quote_currency(symbol))
    })


# todo: side type
def create_take_profit(symbol: str, side: str, take_profit_price: Decimal, quantity: Decimal) -> Order:
    """
    Creates take profit order. Execute order by market price when
    price rises above (for SELL) or drops below (for BUY) 'take_profit_price'

    It allows you not to freeze your assets but still sell an asset when it rises to the desired price
    Use it when you want to place both take-profit and stop-loss, in other cases use limit orders
    """
    if side == Side.SELL:
        return Order({
            "symbol": symbol,
            "side": Side.SELL,
            "price": "Market()",
            "quantity": "D('{}')".format(quantity),
            "place_trigger": "HighPrice() > D('{}')".format(take_profit_price),
            "order_description":
                "[Take profit] sell {} {} if highest price rises above {} {}"
                    .format(quantity, get_base_currency(symbol), take_profit_price, get_quote_currency(symbol))
        })
    return Order({
        "symbol": symbol,
        "side": Side.SELL,
        "price": "Market()",
        "quantity": "D('{}')".format(quantity),
        "place_trigger": "LowPrice() < D('{}')".format(take_profit_price),
        "order_description":
            "[Take profit] buy {} {} if lowest price drops below {} {}"
                .format(quantity, get_base_currency(symbol), take_profit_price, get_quote_currency(symbol))
    })


# todo: side type
def create_trailing_market_stop(symbol: str, side: str, stop_delta: Decimal, target_price: Decimal, quantity) -> Order:
    """
    Creates a trailing market stop order. Execute order by market price when
    price drops (for SELL) for 'stop_delta' from last high or when price rises (for BUY) for 'stop_delta' from last low

    Use it when you do not know the exact take-profit price but you want to sell an asset when price begins to go down
    """
    # todo: describe target_price
    if side == Side.SELL:
        return Order({
            "symbol": symbol,
            "side": Side.SELL,
            "price": "Market()",
            "quantity": "D('{}')".format(quantity),
            "place_trigger": "AvgPrice('1m', 2) < HighPrice() - D('{}') and HighPrice() > D('{}')"
                .format(str(stop_delta), str(target_price)),
            "order_description":
                "[Trailing stop] sell {} {} if price drops more than {} {} from high, works if high price > {} {}"
                .format(quantity, get_base_currency(symbol), stop_delta, get_quote_currency(symbol), target_price,
                        get_quote_currency(symbol))
        })
    return Order({
        "symbol": symbol,
        "side": Side.BUY,
        "price": "Market()",
        "quantity": "D('{}')".format(quantity),
        "place_trigger": "AvgPrice('1m', 2) > LowPrice() - D('{}') and LowPrice() < D('{}')"
            .format(str(stop_delta), str(target_price)),
        "order_description":
            "[Trailing stop] buy {} {} if price rises more than {} {} from low, works if low price < {} {}"
            .format(quantity, get_base_currency(symbol), stop_delta, get_quote_currency(symbol), target_price,
                    get_quote_currency(symbol))
    })
