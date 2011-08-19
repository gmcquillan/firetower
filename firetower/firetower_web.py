import time

from flask import Flask, render_template

import redis_util

REDIS_HOST = "localhost"
REDIS_PORT = 6379

end = 1313788090 + 300

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
    return render_template(
        "last_5_index.html", categories = cat_dict.items()
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


if __name__ == "__main__":
    app.run(debug=True, use_evalex=False)
