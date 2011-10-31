from calendar import timegm

import datetime
import time

import flask
from flask import Flask, render_template

from firetower import category
from firetower import  redis_util

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS = redis_util.Redis(REDIS_HOST, REDIS_PORT)

app = Flask(__name__)


def timestamp(dttm):
        return timegm(dttm.utctimetuple())


@app.route("/")
def root():
    lines = []
    categories = REDIS.get_categories()
    for cat in categories:
        lines.append("<li>%s</li>" % cat)

    return "<ul>%s</ul>" % "\n".join(lines)


@app.route("/default/")
def default():
    cat_dict = REDIS.conn.hgetall("category_ids")

    end = datetime.datetime.now()
    start = end - datetime.timedelta(hours=1)

    results = []
    for cat_id in cat_dict:
        cat = cat_dict[cat_id]
        time_series = REDIS.get_timeseries(cat, timestamp(start), timestamp(end))
        items = [(int(x)*1000, int(y)) for x,y in time_series.items()]
        items.sort(lambda x,y: cmp(x[0], y[0]))
        results.append(
            (cat_id, cat, items)
        )

    return render_template(
        "last_5_index.html", categories = cat_dict.items(), results = results
    )


@app.route("/aggregate")
def aggregate():
    cat_dict = REDIS.conn.hgetall("category_ids")

    end = time.time()
    start = end - 300

    error_totals = {}
    for cat_id in cat_dict:
        cat = cat_dict[cat_id]
        time_series = REDIS.get_timeseries(cat, start, end)
        for time_point in time_series:
            error_totals[cat_id] = error_totals.get(cat_id, 0) + int(time_point[1])

    totals = []
    print error_totals
    for i in error_totals.items():
        totals.append((i[0], cat_dict[i[0]], i[1]))

    return render_template(
        "aggregate.html", totals = totals)

@app.route("/api/categories/")
def categories_api():
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    cats = category.Category.get_all_categories(redis.conn)
    end = flask.request.args.get('end', time.time())
    start = flask.request.args.get('start', end-300)
    time_series = {}
    for cat in cats:
        time_series[cat.cat_id] = cat.timeseries.range(start, end)

    return flask.jsonify(time_series)

@app.route("/api/categories/<category_id>")
def category_api(category_id):
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    cat = category.Category(redis.conn, cat_id=category_id)
    end = flask.request.args.get('end', time.time())
    start = flask.request.args.get('start', end-300)

    time_series = cat.timeseries.range(start, end)

    return flask.jsonify(time_series)


def main():
    app.run(debug=True, use_evalex=False, host='0.0.0.0')
