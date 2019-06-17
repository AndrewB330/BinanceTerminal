import json

import pymongo
import requests
from bson import json_util, ObjectId
from flask import Flask, render_template, jsonify, request

from order import Order, create_limit
from utils import *

# FLAKS
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# MONGODB
db = pymongo.MongoClient("mongodb://localhost:27017/")["ShaurmaBinanceTerminal"]
order_db = db["orders"]

BINANCE_KLINES_URL = 'https://www.binance.com/api/v1/klines?symbol={}&interval={}&limit=200'
BINANCE_DEPTH_URL = 'https://www.binance.com/api/v1/depth?limit=20&symbol={}'


@app.route("/<base>_<quote>")
@app.route("/")
def index(base='BTC', quote='USDT'):
    return render_template(
        "terminal.html",
        base=base,
        quote=quote,
        tickers_json=get_tickers_by_quote_dict(),
        precision_json=get_precision_by_symbol_dict(),
        base_asset_json=binance.get_asset_balance(base),
        quote_asset_json=binance.get_asset_balance(quote),
        base_asset_free=binance.get_asset_balance(base)['free'],
        quote_asset_free=binance.get_asset_balance(quote)['free'],
        active_json=get_active()
    )


@app.route("/klines_<base>_<quote>_<interval>")
def klines(base, quote, interval):
    return requests.get(
        BINANCE_KLINES_URL.format(base + quote, interval)
    ).text


@app.route("/depth_<base>_<quote>")
def depth(base, quote):
    symbol = base + quote
    return requests.get(
        BINANCE_DEPTH_URL.format(symbol)
    ).text


@app.route("/precision")
def precision():
    return jsonify(get_precision_by_symbol_dict())


@app.route("/balance_<currency>")
def balance(currency):
    return jsonify(binance.get_asset_balance(currency))


@app.route("/active_pairs")
def active():
    return jsonify(get_active())


@app.route("/active_orders_<base>_<quote>")
def active_orders_by_symbol(base, quote):
    return jsonify(json.loads(json_util.dumps(list(order_db.find({
        '$and': [
            {'symbol': base + quote},
            {'$or': [
                {'status': OrderStatus.WAITING},
                {'status': OrderStatus.PLACED}
            ]}
        ]
    })))))


@app.route("/active_orders")
def active_orders():
    return jsonify(json.loads(json_util.dumps(list(order_db.find({
        '$or': [
            {'status': OrderStatus.WAITING},
            {'status': OrderStatus.PLACED}
        ]
    })))))


@app.route("/cancel_order")
def cancel_order():
    _id = request.args.get('id')
    order = Order(order_db.find_one({"_id": ObjectId(_id)}))
    order.cancel()
    order_db.update_one({"_id": order._id}, {"$set": order.to_json()})
    return jsonify({"message": "ok"})


@app.route("/limit_order")
def limit_order():
    symbol = request.args.get('symbol')
    side = request.args.get('side')
    price = request.args.get('price')
    quantity = request.args.get('quantity')

    if side != Side.SELL and side != Side.BUY:
        return jsonify({"message": "failed"})

    order = create_limit(symbol, side, price, quantity)
    order_db.insert_one(order.to_json())
    return jsonify({"message": "ok"})


def get_active():
    symbols = list(order_db.find({
        '$or': [
            {'status': OrderStatus.WAITING},
            {'status': OrderStatus.PLACED}
        ]
    }).distinct('symbol'))
    if 'BTCUSDT' not in symbols:
        symbols.append('BTCUSDT')
    return list(map(get_pair_dict, symbols))


if __name__ == '__main__':
    app.run(port=8080, debug=True)
