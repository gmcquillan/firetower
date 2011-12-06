import time
import calendar

import flask
from flask import Flask
from flask import abort
from flask import render_template
from flask import request

from dateutil import parser

from firetower import category
from firetower import  redis_util

# These items should be picked up from the config.yaml
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1
REDIS = redis_util.Redis(REDIS_HOST, REDIS_PORT, REDIS_DB)

DEFAULT_TIME_SLICE = 300000

app = Flask(__name__)

@app.route("/aggregate")
def aggregate():
    return render_template("aggregate.html")


@app.route("/api/category/new", methods=["POST"])
def cat_new():
    """For creating new signature categories manually."""

    sig = request.form.get("sig", None)
    if not sig:
        abort(500)
    thresh = request.form.get("thresh")
    human = request.form.get("human")
    conn = REDIS.conn
    new_cat = category.Category.create(conn, sig)
    if thresh:
        new_cat._set_threshold(thresh)
    if human:
        new_cat._set_human(human)

    return flask.jsonify(new_cat.to_dict())


@app.route("/category/<cat_id>")
def cat_chart(cat_id=None):
    return render_template(
        "category-chart.html", cat_id=cat_id)


@app.route("/api/categories/")
def cat_route():
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT, REDIS_DB).conn

    ret = {}
    for cat in category.Category.get_all_categories(redis):
        ret[cat.cat_id] = cat.to_dict()

    return flask.jsonify(ret)


def base_timeseries(cat_id=None):
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT, REDIS_DB).conn
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
        if start and end:
            start = calendar.timegm(parser.parse(request.form["start"]))
            end = calendar.timegm(parser.parse(request.form["end"]))
        else:
            end = time.time()
            start = end-DEFAULT_TIME_SLICE

        if cat_id:
            return [
                (x.timestamp*1000, x.count) for x in
                category.Category(redis, cat_id=cat_id).timeseries.range(
                    start, end
                )
            ]
        else:
            time_series = {}
            for cat in category.Category.get_all_categories(redis):
                time_series[cat.cat_id] = [
                (x.timestamp*1000, x.count) for x in
                cat.timeseries.range(start, end)
            ]
            return time_series


@app.route("/api/categories/timeseries/")
def categories_api():
    return flask.jsonify(base_timeseries())


@app.route("/api/categories/<category_id>/timeseries/")
def category_api(category_id):
    return flask.jsonify(base_timeseries(category_id))


def main():
    app.run(debug=True, use_evalex=False, host='127.0.0.1')
