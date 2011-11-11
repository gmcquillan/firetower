from calendar import timegm

import time
import calendar

import flask
from flask import Flask
from flask import request

from dateutil import parser

from firetower import category
from firetower import  redis_util

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS = redis_util.Redis(REDIS_HOST, REDIS_PORT)

DEFAULT_TIME_SLICE = 300000

app = Flask(__name__)


@app.route("/api/categories")
def cat_route():
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)

    ret = {}
    for cat in category.Category.get_all_categories(redis.conn):
        ret[cat.cat_id] = cat.to_dict()

    return flask.jsonify(base_timeseries())


def base_timeseries(cat_id=None):
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    get_all = request.args.get("all")
    start = request.args.get("start")
    end = request.args.get("end")

    if get_all:
        if cat_id:
            return category.Category(redis, cat_id=cat_id).timeseries.all()
        else:
            time_series = {}
            for cat in category.Category.get_all_categories(redis):
                time_series[cat.cat_id] = cat.timeseries.all()
            return time_series
    else:
        if param_start and param_end:
            start = calendar.timegm(parser.parse(request.form["start"]))
            end = calendar.timegm(parser.parse(request.form["end"]))
        else:
            end = time.time()
            start = end-DEFAULT_TIME_SLICE

        if cat_id:
            return category.Category(redis, cat_id=cat_id).timeseries.range(
                start, end)
        else:
            time_series = {}
            for cat in category.Category.get_all_categories(redis):
                time_series[cat.cat_id] = cat.timeseries.range(
                    start, end)
            return time_series


@app.route("/api/categories/timeseries/")
def categories_api():
    return flask.jsonify(base_timeseries())


@app.route("/api/categories/<category_id>/timeseries/")
def category_api(category_id):
    return flask.jsonify(base_timeseries(category_id))


def main():
    app.run(debug=True, use_evalex=False, host='127.0.0.1')
