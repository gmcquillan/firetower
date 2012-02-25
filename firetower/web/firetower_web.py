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
REDIS = redis_util.get_redis_conn(REDIS_HOST, REDIS_PORT, REDIS_DB)

DEFAULT_TIME_SLICE = 300000

app = Flask(__name__)

def get_time_slice_options():
    slices = category.TIME_SLICES.items()
    slices.sort(key=lambda x: x[1])
    return [x[0] for x in slices]

@app.route("/")
@app.route("/aggregate/")
def aggregate():
    slice = request.args.get("time_slice", None)
    kwargs = {"time_slice_options": get_time_slice_options()}
    if slice:
        kwargs["time_slice"] = slice
    return render_template("aggregate.html", **kwargs)


@app.route("/category/<cat_id>/")
def cat_chart(cat_id=None):
    kwargs = category.Category(REDIS, cat_id=cat_id).to_dict()
    slice = request.args.get("time_slice", None)
    if slice:
        kwargs["time_slice"] = slice

    return render_template(
        "category.html", cat_id=cat_id, **kwargs)


@app.route("/api/categories/")
def cat_route():
    ret = {}
    for cat in category.Category.get_all_categories(REDIS):
        ret[cat.cat_id] = cat.to_dict()

    return flask.jsonify(ret)


@app.route("/api/category/<cat_id>", methods=["POST"])
def cat_update():
    """Update data about an existing category.
    
    Updatable fields include: signature, threshold, human name.
    """

    sig = request.form.get("sig", None)
    # You cannot delete the signature.
    if not sig:
        abort(500)
    thresh = request.form.get("thresh", None)
    human = request.form.get("human", None)
    conn = REDIS.conn
    cat = category.Category(conn, cat_id=cat_id)
    if cat.signature is not sig:
        cat.signature = sig
    if thresh and cat.threshold is not thresh:
        cat._set_threshold(thresh)
    if human and cat.human is not human:
        cat._set_human(human)

    return flask.jsonify(new_cat.to_dict())



@app.route("/api/category/new/", methods=["POST"])
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


@app.route("/api/category/recategorize/<cat_id>/", methods=["POST"])
def cat_recategorize():
    """For recategorizing an existing category."""

    # Let's be certain we want to do this.
    if not request.form.get("certain"):
        abort(400)
    if not cat_id:
        abort(400)
    thresh = request.form.get("thresh", 0.5)
    cat = category.Category(cat_id=cat_id)
    cat.recategorise(thresh)


def base_timeseries(cat_id=None):
    get_all = request.args.get("all")
    start = request.args.get("start")
    end = request.args.get("end")

    slice = request.args.get("time_slice", None)

    if get_all:
        if cat_id:
            return category.Category(
                REDIS, cat_id=cat_id).timeseries.all(time_slice=slice)
        else:
            time_series = {}
            for cat in category.Category.get_all_categories(REDIS):
                time_series[cat.cat_id] = cat.timeseries.all(time_slice=slice)
            return time_series
    else:
        if start and end:
            start = calendar.timegm(parser.parse(start).timetuple())
            end = calendar.timegm(parser.parse(end).timetuple())
        else:
            end = time.time()
            start = end-DEFAULT_TIME_SLICE

        if cat_id:
            return [
                [x.timestamp*1000, x.count] for x in
                category.Category(REDIS, cat_id=cat_id).timeseries.range(
                    start, end, time_slice=slice
                )
            ]
        else:
            time_series = {}
            for cat in category.Category.get_all_categories(REDIS):
                data = [
                    (x.timestamp*1000, x.count) for x in
                    cat.timeseries.range(start, end, time_slice=slice)
                ]
                if data:
                    time_series[cat.cat_id] = data
            return time_series


@app.route("/api/categories/timeseries/")
def categories_api():
    return flask.jsonify(base_timeseries())


@app.route("/api/categories/<category_id>/timeseries/")
def category_api(category_id):
    return flask.jsonify({category_id: base_timeseries(category_id)})


def main():
    app.run(debug=True, use_evalex=False, host='0.0.0.0')
