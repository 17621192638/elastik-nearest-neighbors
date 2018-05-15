from flask import Flask, request, render_template
from itertools import cycle
from pprint import pprint
import os
import pdb
import requests

# Get elasticsearch hosts from environment variable.
ESHOSTS = cycle(["http://localhost:9200"])
if "ESHOSTS" in os.environ:
    ESHOSTS = cycle(os.environ["ESHOSTS"].split(","))

DEMO_IDS = cycle([

    "988221425063530502",       # Mountain scenery
    "990013386929917953",       # Car
    "991780208138055681",       # Screenshot
    "989646964148133889",       # Male actors (DiCaprio)
    "988889393158115329",       # Male athlete (C. Ronaldo)
    "988487255877718017",       # Signs
    "991004064748978177",       # Female selfie
    "988237522810503168",       # Cartoon character
    "989808637773135873",       # North/south Korean politicians
    "989144784341229568",       # Leo Messi
    "989655776363921409",       # Dog
    "991484266415443968",       # Some kids playing with a racoon


    # "991422991845163009",
    # "988567576799272960",
    # "992424335796125697",
    # "990177895921344514",
    # "988992585619259392",
    # "990790859904794626",
    # "989815445132750849",
    # "991408722823000065",
    # "990656344377167872",
    # "988552330512687104",

])

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello, Internet"


@app.route("/<es_index>/<es_type>/<es_id>")
def images(es_index, es_type, es_id):

    # Fetch 10 random images for bottom carousel.
    body = {
        "_source": ["s3_url"],
        "size": 20,
        "query": {
            "function_score": {
                "query": {"match_all": {}},
                "boost": 5,
                "random_score": {},
                "boost_mode": "multiply"
            }
        }
    }
    req_url = "%s/%s/%s/_search" % (next(ESHOSTS), es_index, es_type)
    req = requests.get(req_url, json=body)
    random_imgs = req.json()["hits"]["hits"]

    if es_id.lower() == "random":
        es_id = random_imgs[0]["_id"]
    elif es_id.lower() == "demo":
        es_id = next(DEMO_IDS)

    # Get number of docs in corpus.
    req_url = "%s/%s/%s/_count" % (next(ESHOSTS), es_index, es_type)
    req = requests.get(req_url)
    count = req.json()["count"]

    # Get the nearest neighbors for the query image, which includes the image.
    image_id = request.args.get("image_id")
    req_url = "%s/%s/%s/%s/_aknn_search?k1=100&k2=10" % (
        next(ESHOSTS), es_index, es_type, es_id)
    req = requests.get(req_url)
    hits = req.json()["hits"]["hits"]
    took_ms = req.json()["took"]
    query_img, neighbor_imgs = hits[0], hits[1:]

    # Render template.
    return render_template(
        "index.html",
        es_index=es_index,
        es_type=es_type,
        took_ms=took_ms,
        count=count,
        query_img=query_img,
        neighbor_imgs=neighbor_imgs,
        random_imgs=random_imgs)