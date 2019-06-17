import datetime

import pymongo
from flask import Flask, render_template

# FLAKS
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# MONGODB
db = pymongo.MongoClient("mongodb://localhost:27017/")["ShaurmaBinanceTerminal"]
order_db = db["orders"]


@app.route("/")
def hello():
    cursor = order_db.find({})
    return render_template(
        "orders_viewer.html",
        orders=list(cursor),
        to_time=lambda t: str(datetime.datetime.fromtimestamp(t)),
        to_short=lambda oid: str(oid)[-5:]
    )


if __name__ == '__main__':
    app.run(port=8088, debug=True)
