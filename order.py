import json
from decimal import Decimal

from binance.exceptions import BinanceAPIException

from utils import *

inner_functions = [
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


def Market():
    return 'Market'


def D(number):
    return Decimal(number)


def Seconds(n):
    return 1000 * n


def Minutes(n):
    return Seconds(60) * n


def Hours(n):
    return Minutes(60) * n


def replace_inner_functions(expression):
    for function_name in inner_functions:
        expression = expression.replace(function_name, 'self.' + function_name)
    return expression


def getCurrentPrice(symbol):
    return binance.get_ticker(symbol=symbol)['lastPrice']


class Order:
    def HighPrice(self):
        return self.highPrice

    def LowPrice(self):
        return self.lowPrice

    def AvgHigh(self, interval, number_of_bars):
        bars = binance.get_klines(symbol=self.symbol, interval=interval)[-number_of_bars:]
        return sum(map(lambda bar: Decimal(bar[2]), bars)) / len(bars)

    def AvgLow(self, interval, number_of_bars):
        bars = binance.get_klines(symbol=self.symbol, interval=interval)[-number_of_bars:]
        return sum(map(lambda bar: Decimal(bar[3]), bars)) / len(bars)

    def AvgPrice(self, interval, number_of_bars):
        return (self.AvgHigh(interval, number_of_bars) + self.AvgLow(interval, number_of_bars)) / 2

    def OrderPrice(self):
        return self.orderPrice

    def OrderTime(self):
        return self.orderTime

    @staticmethod
    def CurrentTime():
        return get_current_time()

    def __init__(self, json_obj):
        self._id = json_obj.get('_id', None)
        self.time = json_obj.get('time', get_current_time())
        self.symbol = json_obj['symbol']
        self.side = json_obj['side']
        self.status = json_obj.get('status', OrderStatus.WAITING)

        self.price = json_obj['price']
        self.price_formatted = replace_inner_functions(self.price)
        self.price_func = lambda: eval(self.price_formatted)

        self.quantity = json_obj['quantity']
        self.quantityFormatted = replace_inner_functions(self.quantity)
        self.quantityFunc = lambda: eval(self.quantityFormatted)

        self.placeTrigger = json_obj.get('place_trigger', 'True')
        self.placeTriggerFormatted = replace_inner_functions(self.placeTrigger)
        self.placeTriggerFunc = lambda: eval(self.placeTriggerFormatted)

        self.resetTrigger = json_obj.get('reset_trigger', 'False')
        self.resetTriggerFormatted = replace_inner_functions(self.resetTrigger)
        self.resetTriggerFunc = lambda: eval(self.resetTriggerFormatted)

        self.cancelTrigger = json_obj.get('cancel_trigger', 'False')
        self.cancelTriggerFormatted = replace_inner_functions(self.cancelTrigger)
        self.cancelTriggerFunc = lambda: eval(self.cancelTriggerFormatted)

        self.orderDescription = json_obj.get('order_description', None)
        self.lastUpdate = json_obj.get('last_update', self.time)
        self.highPrice = Decimal(json_obj.get('high_price', getCurrentPrice(self.symbol)))
        self.lowPrice = Decimal(json_obj.get('low_price', self.highPrice))

        self.placed = json_obj.get('placed', False)
        self.orderPrice = Decimal(json_obj.get('order_price', '0.0'))
        self.orderId = json_obj.get('order_id', None)
        self.orderTime = json_obj.get('order_time', None)

        self.cancelTime = json_obj.get('cancel_time', None)

    def cancel(self):
        if self.status == OrderStatus.PLACED and self.cancelTriggerFunc():
            response = binance.cancel_order(symbol=self.symbol, orderId=self.orderId)
            if response['orderId'] == self.orderId and response['status'] == 'CANCELED':
                self.placed = False
            else:
                pass  # todo: error???
        self.status = OrderStatus.CANCELED
        self.cancelTime = binance.get_server_time()['serverTime']

    def place(self):
        price = self.price_func()
        quantity = self.quantityFunc().quantize(Decimal(precision_by_symbol[self.symbol]['quantity_step']))
        if self.price_func() == 'Market':
            response = binance.order_market(
                symbol=self.symbol,
                side=self.side,
                quantity=quantity
            )
        else:
            price = price.quantize(Decimal(precision_by_symbol[self.symbol]['price_step']))
            response = binance.order_limit(
                symbol=self.symbol,
                side=self.side,
                quantity=quantity,
                price=price
            )
        log.info(json.dumps(response))
        self.placed = True
        self.orderId = response['orderId']
        self.orderPrice = price
        self.status = OrderStatus.PLACED
        self.orderTime = response['transactTime']

    def reset(self):
        response = binance.cancel_order(symbol=self.symbol, orderId=self.orderId)
        if response['orderId'] == self.orderId and response['status'] == 'CANCELED':
            self.placed = False
            self.status = OrderStatus.WAITING
        else:
            pass  # todo: error???

    def update_high_low(self):
        for kline in binance.get_klines(symbol=self.symbol, interval=BinanceClient.KLINE_INTERVAL_1MINUTE):
            if kline[6] > self.time:
                self.highPrice = max(self.highPrice, D(kline[2]))
                self.lowPrice = min(self.lowPrice, D(kline[3]))
        self.lastUpdate = get_current_time()

    def update(self):
        try:
            self.update_high_low()

            if self.cancelTriggerFunc():
                log.info('Cancel trigger. Symbol: %s, order: %s', self.symbol, str(self._id))
                self.cancel()
            if self.status == OrderStatus.WAITING and self.placeTriggerFunc():
                log.info('Place trigger. Symbol: %s, order: %s', self.symbol, str(self._id))
                self.place()
            if self.status == OrderStatus.PLACED and self.resetTriggerFunc():
                log.info('Reset trigger. Symbol: %s, order: %s', self.symbol, str(self._id))
                self.reset()
        except BinanceAPIException as e:
            log.info('Failed. Symbol: %s, order: %s', self.symbol, str(self._id))
            self.status = OrderStatus.FAILED

    def to_json(self):
        return {
            "time": self.time,
            "symbol": self.symbol,
            "side": self.side,
            "status": self.status,
            "price": self.price,
            "quantity": self.quantity,
            "place_trigger": self.placeTrigger,
            "reset_trigger": self.resetTrigger,
            "cancel_trigger": self.cancelTrigger,
            "order_description": self.orderDescription,
            "last_update": self.lastUpdate,
            "high_price": str(self.highPrice),
            "low_price": str(self.lowPrice),
            "placed": self.placed,
            "order_price": str(self.orderPrice),
            "order_id": self.orderId,
            "cancel_time": self.cancelTime
        }


def createLimitOrder(symbol, side, price, quantity):
    return Order({
        "symbol": symbol,
        "side": side,
        "price": 'D(\'{}\')'.format(str(price)),
        "quantity": 'D(\'{}\')'.format(str(quantity)),
        "order_description": "[Limit] {} {} {}, price: {} {}".
            format(side.lower(), quantity, get_base_currency(symbol), price, get_quote_currency(symbol))
    })


def createMarketStop(symbol, side, stop_price, quantity):
    if side == 'SELL':
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


def createTakeProfit(symbol, side, take_profit_price, quantity):
    if side == 'SELL':
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


def createTrailingMarketStop(symbol, side, stop_delta, target_price, quantity):
    if side == 'SELL':
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
