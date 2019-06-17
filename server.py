import time

import pymongo
import schedule

from order import *
from utils import *

# MONGODB
db = pymongo.MongoClient("mongodb://localhost:27017/")["ShaurmaBinanceTerminal"]
order_db = db["orders"]

JOB_INTERVAL = 10.0  # interval of updating
jobs_pool = {}


def worker(symbol):
    try:
        time_start = time.time()
        # get all active orders
        active_orders = order_db.find({
            '$and': [
                {'symbol': symbol},
                {'$or': [
                    {'status': OrderStatus.WAITING},
                    {'status': OrderStatus.PLACED}
                ]}
            ]
        })

        # update all active orders
        for json_order in active_orders:
            order = Order(json_order)
            order.update()
            order_db.update_one({"_id": order._id}, {"$set": order.to_json()})

        # adjust updating period
        time_elapsed = min(JOB_INTERVAL, time.time() - time_start)
        jobs_pool[symbol].interval = JOB_INTERVAL - time_elapsed
    except Exception as e:
        log.error('Worker %s error: %s', symbol, repr(e))


def jobs_maintainer():
    # get all active symbols
    cursor = order_db.find({
        '$or': [
            {'status': OrderStatus.WAITING},
            {'status': OrderStatus.PLACED}
        ]
    }).distinct('symbol')

    working = set()

    # run jobs for not working, but active symbols
    for symbol in cursor:
        if symbol not in jobs_pool:
            log.info('Worker started, symbol: %s', symbol)
            jobs_pool[symbol] = schedule.every(JOB_INTERVAL).seconds.do(worker, symbol=symbol)
            jobs_pool[symbol].run()
        working.add(symbol)

    # remove jobs for working, but not active symbols
    for k in list(jobs_pool.keys()):
        if k not in working:
            log.info('Worker stopped, symbol: %s', k)
            schedule.cancel_job(jobs_pool[k])
            jobs_pool.pop(k)


def initialize_test_db():
    order_db.drop()
    o = [
        create_limit('BTCUSDT', Side.BUY, Decimal('7400.00'), Decimal('0.0015')),
        create_limit('BTCUSDT', Side.BUY, Decimal('7103.65'), Decimal('0.0020')),
        create_limit('BTCUSDT', Side.SELL, Decimal('9500.00'), Decimal('0.0030')),
        create_limit('BTCUSDT', Side.SELL, Decimal('9600.00'), Decimal('0.0010')),
        create_market_stop('BTCUSDT', Side.SELL, Decimal('6675.50'), Decimal('0.0035')),
        create_trailing_market_stop('BTCUSDT', Side.SELL, Decimal('100.00'), Decimal('7600.00'), Decimal('0.0035')),
        create_market_stop('XLMUSDT', Side.SELL, Decimal('0.105'), Decimal('50.0')),
        create_trailing_market_stop('XLMUSDT', Side.SELL, Decimal('0.01'), Decimal('0.14'), Decimal('0.0015')),
        create_trailing_market_stop('XLMUSDT', Side.SELL, Decimal('0.01'), Decimal('0.14'), Decimal('0.0015'))
    ]
    for o in o:
        order_db.insert_one(o.to_json())
    print('Test DB initialized')


def run_server():
    maintainer = schedule.every(5).seconds.do(jobs_maintainer)
    maintainer.run()
    while True:
        schedule.run_pending()
        time.sleep(0.1)


if __name__ == '__main__':
    # initialize_test_db()
    run_server()
