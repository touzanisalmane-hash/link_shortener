import string
import random

from flask import Flask, request, redirect, render_template, abort
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["link_shortener"]
links = db["links"]

# Ensure short_code lookups are unique and fast
links.create_index("short_code", unique=True)


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def code_exists(code):
    return links.find_one({"short_code": code}) is not None


@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    if request.method == "POST":
        original_url = request.form.get("url", "").strip()

        if original_url and not original_url.startswith(("http://", "https://")):
            original_url = "https://" + original_url

        if original_url:
            code = generate_short_code()
            while code_exists(code):
                code = generate_short_code()

            links.insert_one({
                "short_code": code,
                "original_url": original_url,
                "clicks": 0,
            })
            short_url = request.host_url + code

    all_links = list(links.find().sort("_id", -1))

    return render_template("index.html", short_url=short_url, links=all_links)


@app.route("/<code>")
def redirect_to_url(code):
    link = links.find_one({"short_code": code})

    if link is None:
        abort(404)

    links.update_one({"short_code": code}, {"$inc": {"clicks": 1}})

    return redirect(link["original_url"])


if __name__ == "__main__":
    app.run(debug=True)