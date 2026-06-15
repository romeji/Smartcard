from flask import Flask, request, jsonify
import urllib.request
import urllib.parse
import json


app = Flask(__name__)

STATIC = "https://static.jow.fr/"


@app.route("/", methods=["GET"])
def index():

    query = request.args.get(
        "q",
        ""
    ).strip()

    limit = int(
        request.args.get(
            "limit",
            12
        )
    )

    if not query:
        return jsonify({
            "error":
            "Missing ?q="
        }), 400

    try:

        recipes = search_jow(
            query,
            limit
        )

        return jsonify({
            "query": query,
            "recipes": recipes
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


def search_jow(query, limit):

    url = (
        "https://api.jow.fr/public/recipe/quicksearch"
    )

    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "start": 0,
        "availabilityZoneId": "FR"
    })

    req = urllib.request.Request(
        f"{url}?{params}",
        method="POST",
        data=b"{}",
        headers={
            "Accept":
            "application/json",

            "Content-Type":
            "application/json",

            "x-jow-withmeta":
            "1",

            "Origin":
            "https://jow.fr",

            "Referer":
            "https://jow.fr/",

            "User-Agent":
            "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        req
    ) as r:

        raw = json.loads(
            r.read()
            .decode()
        )

    recipes = (
        raw
        .get(
            "data",
            {}
        )
        .get(
            "content",
            []
        )
    )

    result = []

    for recipe in recipes:

        result.append({

            "id":
            recipe.get(
                "_id"
            ),

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

            "url":
            (
                "https://jow.fr/recettes/"
                +
                recipe.get(
                    "slug",
                    ""
                )
            ),

            "imageUrl":
            build_static(
                recipe.get(
                    "editorialPictureUrl"
                )
            ),

            "videoUrl":
            build_static(
                recipe.get(
                    "videoUrl"
                )
            ),

            "prepTime":
            recipe.get(
                "preparationTime",
                0
            ),

            "cookTime":
            recipe.get(
                "cookingTime",
                0
            ),

            "steps": [],

            "ingredients": [

                {
                    "name":
                    c["ingredient"]["name"],

                    "qty":
                    str(
                        c["ingredient"]
                        .get(
                            "quantityPerCover",
                            ""
                        )
                    ),

                    "unit": "",

                    "isOptional":
                    c.get(
                        "isOptional",
                        False
                    )
                }

                for c in recipe.get(
                    "constituents",
                    []
                )

                if c.get(
                    "ingredient"
                )
            ]
        })

    return result


def build_static(path):

    if not path:
        return None

    if path.startswith(
        "http"
    ):
        return path

    return (
        STATIC
        +
        path
    )
