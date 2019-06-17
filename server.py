import time

import pymongo
import schedule

from order import *
from utils import *

db = pymongo.MongoClient("mongodb://localhost:27017/")["ShaurmaBinanceTerminal"]
order_db = db["orders"]

JOB_INTERVAL = 20
jobs_pool = {}


def worker(symbol):
    try:
        cursor = order_db.find({
            '$and': [
                {'symbol': symbol},
                {'$or': [
                    {'status': OrderStatus.WAITING},
                    {'status': OrderStatus.PLACED}
                ]}
            ]
        })
        for json_order in cursor:
            order = Order(json_order)
            order.update()
            order_db.update_one({"_id": order._id}, {"$set": order.to_json()})
    except Exception as e:
        log.error('Worker %s error: %s', symbol, repr(e))


def jobs_maintainer():
    cursor = order_db.find({
        '$or': [
            {'status': OrderStatus.WAITING},
            {'status': OrderStatus.PLACED}
        ]
    }).distinct('symbol')
    working = set()
    for symbol in cursor:
        if symbol not in jobs_pool:
            log.info('Worker started, symbol: %s', symbol)
            jobs_pool[symbol] = schedule.every(JOB_INTERVAL).seconds.do(worker, symbol=symbol)
            jobs_pool[symbol].run()
        working.add(symbol)
    for k in list(jobs_pool.keys()):
        if k not in working:
            log.info('Worker stopped, symbol: %s', k)
            schedule.cancel_job(jobs_pool[k])
            jobs_pool.pop(k)


maintainer = schedule.every(5).seconds.do(jobs_maintainer)
maintainer.run()


def initialize_test_db():
    order_db.drop()
    o = [
        createLimitOrder('BTCUSDT', Side.BUY, Decimal('7400.00'), '0.0015'),
        createLimitOrder('BTCUSDT', Side.BUY, Decimal('7103.65'), '0.0020'),
        createLimitOrder('BTCUSDT', Side.SELL, Decimal('8900.00'), '0.0030'),
        createLimitOrder('BTCUSDT', Side.SELL, Decimal('9100.00'), '0.0010'),
        createMarketStop('BTCUSDT', Side.SELL, Decimal('6675.50'), '00.0035'),
        createTrailingMarketStop('BTCUSDT', Side.SELL, Decimal('100.00'), Decimal('7600.00'), '00.0035'),
        createMarketStop('XLMUSDT', Side.SELL, Decimal('0.105'), '50.0'),
        createTrailingMarketStop('XLMUSDT', Side.SELL, Decimal('0.01'), Decimal('0.14'), '0.0015'),
        createTrailingMarketStop('XLMUSDT', Side.SELL, Decimal('0.01'), Decimal('0.14'), '0.0015')
    ]
    for o in o:
        order_db.insert_one(o.to_json())


while True:
    schedule.run_pending()
    time.sleep(0.5)
