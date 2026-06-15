from flask import Flask, request, jsonify
import urllib.request
import urllib.parse
import urllib.error
import json
import traceback


app = Flask(__name__)

STATIC = "https://static.jow.fr/"


@app.route("/", methods=["GET"])
def home():

    try:

        query = (
            request.args
            .get("q", "")
            .strip()
        )

        limit = int(
            request.args
            .get("limit", "12")
        )

        if not query:

            return jsonify({
                "error":
                "Missing ?q="
            }), 400

        recipes = search_jow(
            query,
            limit
        )

        return jsonify({
            "query":
            query,

            "recipes":
            recipes
        })

    except Exception:

        return jsonify({

            "error":
            traceback.format_exc()

        }), 500


def search_jow(query, limit):

    params = urllib.parse.urlencode({

        "query":
        query,

        "limit":
        limit,

        "start":
        0,

        "availabilityZoneId":
        "FR"
    })

    url = (
        "https://api.jow.fr/public/recipe/quicksearch?"
        + params
    )

    req = urllib.request.Request(

        url,

        method="POST",

        data=b"{}",

        headers={

            "Accept":
            "application/json",

            "Content-Type":
            "application/json",

            "Origin":
            "https://jow.fr",

            "Referer":
            "https://jow.fr/",

            "User-Agent":
            "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=20
    ) as r:

        raw = json.loads(
            r.read()
            .decode("utf-8")
        )

    recipes = (
        raw
        .get("data", {})
        .get("content", [])
    )

    result = []

    for recipe in recipes:

        result.append({

            "id":
            recipe.get("_id"),

            "name":
            recipe.get(
                "title"
            ),

            "description":
            recipe.get(
                "description"
            ),

            "slug":
            recipe.get(
                "slug"
            ),

            "imageUrl":
            build_static(
                recipe.get(
                    "editorialPictureUrl"
                )
                or
                recipe.get(
                    "imageUrl"
                )
            ),

            "videoUrl":
            build_static(
                recipe.get(
                    "videoUrl"
                )
            ),

            "ingredients": [
                x
                for x
                in recipe.get(
                    "constituents",
                    []
                )
            ],

            "steps": []
        })

    return result


def build_static(path):

    if not path:
        return None

    if path.startswith(
        "http"
    ):
        return path

    return STATIC + path
