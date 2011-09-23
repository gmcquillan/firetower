import time

from flask import Flask, render_template

import redis_util

REDIS_HOST = "localhost"
REDIS_PORT = 6379

end = 1313792842 + 300

app = Flask(__name__)

@app.route("/")
def root():
    lines = []
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    categories = redis.get_categories()
    for cat in categories:
        lines.append("<li>%s</li>" % cat)

    return "<ul>%s</ul>" % "\n".join(lines)

@app.route("/last_5/")
def last_5():
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    cat_dict = redis.conn.hgetall("category_ids")

    start = end - 300

    results = []
    for cat_id in cat_dict:
        cat = cat_dict[cat_id]
        time_series = redis.get_timeseries(cat, start, end)
        items = [(int(x)*1000, int(y)) for x,y in time_series.items()]
        items.sort(lambda x,y: cmp(x[0], y[0]))
        results.append(
            (cat_id, cat, items)
        )

    return render_template(
        "last_5_index.html", categories = cat_dict.items(), results = results
    )

@app.route("/last_5/<category_id>")
def cat_last_5(category_id):
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    cat_dict = redis.conn.hgetall("category_ids")
    cat = cat_dict[category_id]

    start = end - 300
    time_series = redis.get_timeseries(cat, start, end)
    items = [(int(x)*1000, int(y)) for x,y in time_series.items()]
    items.sort(lambda x,y: cmp(x[0], y[0]))
    return render_template(
        "last_5.html", time_series = items, cat_name = cat)

@app.route("/aggregate")
def aggregate():
    redis = redis_util.Redis(REDIS_HOST, REDIS_PORT)
    cat_dict = redis.conn.hgetall("category_ids")

    start = end - 300

    error_totals = {}
    for cat_id in cat_dict:
        cat = cat_dict[cat_id]
        time_series = redis.get_timeseries(cat, start, end)
        for time_point in time_series:
            error_totals[cat_id] = error_totals.get(cat_id, 0) + int(time_point[1])

    totals = []
    print error_totals
    for i in error_totals.items():
        totals.append((i[0], cat_dict[i[0]], i[1]))

    return render_template(
        "aggregate.html", totals = totals)

def main():
    app.run(debug=True, use_evalex=False)
